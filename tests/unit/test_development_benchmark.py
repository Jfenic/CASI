"""Validate scoring against broken fixtures, reference repairs and weak tests."""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from casi.agent.orchestrator import OrchestratorResult
from casi.evaluation.benchmark import load_tasks
from casi.evaluation.grading import grade_task
from casi.evaluation.runner import BenchmarkRunOptions, run_task
from casi.sandbox.local_runner import LocalRunner

SUITE = Path(__file__).resolve().parents[2] / "benchmarks" / "development"
TASKS = load_tasks(SUITE / "tasks")


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.task_id)
def test_development_task_rejects_baseline_and_accepts_reference(task):
    original = SUITE / "repositories" / task.repository
    baseline, _ = grade_task(
        task, original=original, candidate=original, runner=LocalRunner()
    )
    assert not baseline.timed_out, baseline.stderr
    assert baseline.exit_code in {1, 2}, baseline.stdout + baseline.stderr
    reference, _ = grade_task(
        task,
        original=original,
        candidate=SUITE / "solutions" / task.repository,
        runner=LocalRunner(),
    )
    assert reference.exit_code == 0, reference.stdout + reference.stderr
    assert not reference.timed_out


def test_test_writing_grader_rejects_happy_path_only(tmp_path):
    task = next(task for task in TASKS if task.repository == "retry_tests")
    (tmp_path / "test_retry.py").write_text(
        "from retrying import retry\n"
        "def test_happy():\n"
        "    assert retry(lambda: 42) == 42\n"
    )
    result, _ = grade_task(
        task,
        original=SUITE / "repositories" / task.repository,
        candidate=tmp_path,
        runner=LocalRunner(),
    )
    assert result.exit_code == 1
    assert "no_retry" in result.stdout


def test_grader_restores_tests_and_withholds_checks_from_agent(tmp_path, monkeypatch):
    task = TASKS[0]
    original = SUITE / "repositories" / task.repository
    shutil.copytree(original, tmp_path / "candidate")
    candidate = tmp_path / "candidate"
    (candidate / "test_visible.py").write_text("def test_fake(): assert True\n")
    result, _ = grade_task(
        task, original=original, candidate=candidate, runner=LocalRunner()
    )
    assert result.exit_code == 1
    assert "test_first_page" in result.stdout
    assert not (candidate / "_benchmark_checks").exists()


def test_runner_rejects_patch_to_protected_tests(tmp_path, monkeypatch):
    task = TASKS[0]
    patch = (
        "--- a/test_visible.py\n"
        "+++ b/test_visible.py\n"
        "@@ -1 +1 @@\n"
        "-assert False\n"
        "+assert True\n"
    )
    root = tmp_path / task.repository
    root.mkdir()
    (root / "pagination.py").write_text("def paginate(*args): return []\n")
    (root / "test_visible.py").write_text("assert False\n")

    def fake_run(self, instruction, category=None):
        assert not (Path(self.repository) / "_benchmark_checks").exists()
        return OrchestratorResult(success=True, response=f"```diff\n{patch}```")

    monkeypatch.setattr("casi.evaluation.runner.AgentOrchestrator.run", fake_run)
    from casi.sandbox.base import TestResult

    monkeypatch.setattr(
        "casi.evaluation.runner.grade_task",
        lambda *args, **kwargs: (TestResult([], 0, "", "", 0), "mock"),
    )
    result = run_task(
        task,
        repositories_root=tmp_path,
        client=object(),
        options=BenchmarkRunOptions(
            repositories_root=tmp_path,
            show_progress=False,
            artifacts_dir=tmp_path / "artifacts",
        ),
    )
    assert not result.task_success
    assert not result.patch_applied
    assert "disallowed files" in result.agent_error
    assert (root / "test_visible.py").read_text() == "assert False\n"
    artifacts = tmp_path / "artifacts" / "unknown" / task.task_id
    recorded = json.loads((artifacts / "result.json").read_text())
    assert recorded["task_success"] is False
    assert "disallowed files" in recorded["agent_error"]
    assert (artifacts / "trace.json").is_file()


def test_grader_refuses_traversal_even_for_programmatic_task(tmp_path):
    task = replace(TASKS[0], allowed_files=("../outside.py",))
    with pytest.raises(ValueError):
        grade_task(
            task,
            original=SUITE / "repositories" / task.repository,
            candidate=tmp_path,
            runner=LocalRunner(),
        )


def test_independent_checks_are_required_even_for_read_category():
    from casi.evaluation.runner import evaluate_task_success

    task = replace(TASKS[0], category="read")
    assert not evaluate_task_success(task, agent_success=True, command_success=False)
    assert not evaluate_task_success(task, agent_success=True, command_success=None)


def test_report_retains_verification_and_capability():
    from casi.evaluation.benchmark import BenchmarkTaskResult
    from casi.evaluation.report import build_report_payload, render_markdown_report

    result = BenchmarkTaskResult(
        task_id="dev_example",
        capability="test_design",
        difficulty="intermediate",
        agent_success=True,
        task_success=False,
        command_success=False,
        verification_output="no_retry survived",
        verification_runner="docker",
    )
    payload = build_report_payload([result])
    assert payload["by_capability"] == {"test_design": {"tasks": 1, "passed": 0}}
    assert payload["tasks"][0]["verification_output"] == "no_retry survived"
    assert payload["tasks"][0]["verification_runner"] == "docker"
    assert "| test_design | 0 / 1 |" in render_markdown_report([result])


def test_loader_resolves_grader_relative_to_yaml_and_rejects_escape(tmp_path):
    import yaml

    (tmp_path / "tasks").mkdir()
    (tmp_path / "checks").mkdir()
    specification = {
        "id": "example",
        "repository": "example",
        "instruction": "Fix",
        "grader": "../checks",
        "allowed_files": ["module.py"],
    }
    path = tmp_path / "tasks" / "example.yaml"
    path.write_text(yaml.safe_dump(specification))
    task = load_tasks(tmp_path / "tasks")[0]
    assert task.grader_directory == tmp_path / "checks"
    specification["allowed_files"] = ["../outside.py"]
    path.write_text(yaml.safe_dump(specification))
    with pytest.raises(ValueError, match="allowed_files"):
        load_tasks(tmp_path / "tasks")


def test_model_failure_does_not_abort_remaining_tasks(tmp_path, monkeypatch):
    from casi.evaluation.runner import run_model_benchmark
    from casi.exceptions import LLMError
    from casi.sandbox.base import TestResult

    tasks = [replace(TASKS[0], task_id="first"), replace(TASKS[0], task_id="second")]
    calls = []

    def fake_run(self, instruction, category=None):
        calls.append(instruction)
        if len(calls) == 1:
            raise LLMError("model timeout")
        return OrchestratorResult(success=True, response="done")

    monkeypatch.setattr("casi.evaluation.runner.AgentOrchestrator.run", fake_run)
    monkeypatch.setattr(
        "casi.evaluation.runner.grade_task",
        lambda *args, **kwargs: (TestResult([], 1, "baseline fails", "", 0), "mock"),
    )
    first_dir = tmp_path / "artifacts" / "unknown" / "first"
    first_dir.mkdir(parents=True)
    (first_dir / "proposal.diff").write_text("stale proposal")
    results = run_model_benchmark(
        tasks,
        client=object(),
        options=BenchmarkRunOptions(
            repositories_root=SUITE / "repositories",
            show_progress=False,
            artifacts_dir=tmp_path / "artifacts",
        ),
    ).results
    assert len(calls) == 2
    assert not (first_dir / "proposal.diff").exists()
    assert (first_dir / "result.json").is_file()
    assert results[0].agent_error == "model timeout"
    assert not results[0].task_success
    assert results[1].agent_success
    assert not results[1].task_success


@pytest.mark.parametrize(
    ("task_id", "filename", "original_expression", "broken_expression", "failure"),
    [
        (
            "dev_006",
            "settings.py",
            "result[key] = deepcopy(value)",
            "result[key] = value",
            "test_no_aliases_or_mutations",
        ),
        (
            "dev_007",
            "reader.py",
            "enumerate(text.splitlines(), 1)",
            "enumerate((line for line in text.splitlines() if line.strip()), 1)",
            "test_physical_line_number",
        ),
    ],
)
def test_grader_rejects_observed_repairs_that_pass_visible_tests(
    tmp_path, task_id, filename, original_expression, broken_expression, failure
):
    """Preserve the false-positive boundary observed in September 12 model runs."""
    task = next(task for task in TASKS if task.task_id == task_id)
    original = SUITE / "repositories" / task.repository
    candidate = tmp_path / "candidate"
    shutil.copytree(original, candidate)
    reference = (SUITE / "solutions" / task.repository / filename).read_text()
    assert original_expression in reference
    (candidate / filename).write_text(
        reference.replace(original_expression, broken_expression)
    )
    runner = LocalRunner()
    visible = runner.run(candidate, [sys.executable, "-m", "pytest", "-q"])
    assert visible.exit_code == 0, visible.stdout + visible.stderr
    graded, _ = grade_task(task, original=original, candidate=candidate, runner=runner)
    assert graded.exit_code == 1, graded.stdout + graded.stderr
    assert failure in graded.stdout
    assert not graded.timed_out
