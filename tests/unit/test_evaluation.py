from __future__ import annotations

import sys
from pathlib import Path

import pytest

from casi.agent.state import AgentResult
from casi.cli import main
from casi.evaluation.benchmark import (
    BenchmarkTask,
    BenchmarkTaskResult,
    load_tasks,
    run_benchmark,
)
from casi.evaluation.metrics import summarize_results
from casi.evaluation.report import render_report
from casi.sandbox.docker_runner import DockerRunner


def test_cli_test_runs_pytest(tmp_path: Path, capsys) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_passes():\n    assert True\n",
        encoding="utf-8",
    )

    exit_code = main(["test", "--repo", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "exit_code=0" in output


def test_cli_test_reports_failure(tmp_path: Path, capsys) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_fails():\n    assert False\n",
        encoding="utf-8",
    )

    exit_code = main(["test", "--repo", str(tmp_path)])

    assert exit_code == 1


def test_load_benchmark_tasks() -> None:
    tasks = load_tasks(Path("benchmarks/tasks"))

    assert len(tasks) >= 26
    categories = {task.category for task in tasks}
    assert "create" in categories
    assert tasks[0].task_id
    assert tasks[0].instruction
    assert tasks[0].repository
    assert tasks[0].category


def test_benchmark_runner_collects_results() -> None:
    tasks = [
        BenchmarkTask(task_id="t1", name="One", instruction="Inspect"),
        BenchmarkTask(task_id="t2", name="Two", instruction="Search"),
    ]

    def run_task(task: BenchmarkTask) -> AgentResult:
        return AgentResult(
            success=task.task_id == "t1",
            response="ok",
            steps=2,
        )

    results = run_benchmark(tasks, run_task)

    assert len(results) == 2
    assert results[0].agent_success is True
    assert results[1].agent_success is False
    assert summarize_results(results)["tasks"] == 2
    assert "t1 [general]: ok" in render_report(results)


def test_benchmark_report_json_payload() -> None:
    results = [
        BenchmarkTaskResult(
            task_id="t1",
            name="One",
            repository="healthy_lib",
            category="read",
            model="mock",
            agent_success=True,
            task_success=True,
            steps=3,
            duration_seconds=1.5,
        )
    ]

    from casi.evaluation.report import build_report_payload, render_markdown_report

    payload = build_report_payload(results, model="mock")
    assert payload["model"] == "mock"
    assert payload["metrics"]["tasks"] == 1
    assert "task_success_rate" in payload["metrics"]
    assert render_markdown_report(results, model="mock").startswith("# CASI Benchmark")


def test_benchmark_runner_uses_isolated_repository(tmp_path: Path, monkeypatch) -> None:
    from casi.agent.orchestrator import OrchestratorResult
    from casi.evaluation.benchmark import BenchmarkTask
    from casi.evaluation.runner import BenchmarkRunOptions, run_task

    repos_root = Path("benchmarks/repositories")
    task = BenchmarkTask(
        task_id="read_only",
        name="Read healthy lib",
        instruction="Explain the repository",
        repository="healthy_lib",
        category="read",
        success_command=["python3", "-m", "pytest", "-q"],
        max_steps=4,
    )

    monkeypatch.setattr(
        "casi.evaluation.runner.AgentOrchestrator.run",
        lambda self, instruction, category=None: OrchestratorResult(
            success=True,
            response=f"done: {instruction[:20]}",
        ),
    )

    class FakeClient:
        model = "mock-model"

        def complete(self, messages, tools):
            raise AssertionError("complete should not be called in this test")

    result = run_task(
        task,
        repositories_root=repos_root,
        client=FakeClient(),
        options=BenchmarkRunOptions(repositories_root=repos_root),
    )

    assert result.agent_success is True
    assert result.task_success is True
    assert result.model == "mock-model"
    assert result.command_success is True


def test_benchmark_progress_output(tmp_path: Path, capsys, monkeypatch) -> None:
    from casi.agent.orchestrator import OrchestratorResult
    from casi.evaluation.runner import BenchmarkRunOptions, run_model_benchmark

    tasks = load_tasks(Path("benchmarks/tasks"))[:1]

    monkeypatch.setattr(
        "casi.evaluation.runner.AgentOrchestrator.run",
        lambda self, instruction, category=None: OrchestratorResult(
            success=True,
            response="done",
        ),
    )

    class FakeClient:
        model = "mock-model"

        def complete(self, messages, tools):
            raise AssertionError("not used")

    run_model_benchmark(
        tasks,
        client=FakeClient(),
        options=BenchmarkRunOptions(
            repositories_root=Path("benchmarks/repositories"),
            show_progress=True,
        ),
    )
    captured = capsys.readouterr()
    assert "[benchmark] Task 1/1:" in captured.err
    assert "task_001" in captured.err
    assert "result: PASS" in captured.err


def test_resolve_benchmark_max_steps_by_category() -> None:
    from casi.evaluation.runner import resolve_benchmark_max_steps

    create = BenchmarkTask(
        task_id="t1",
        name="create",
        instruction="Create module",
        repository="stats_app",
        category="create",
        max_steps=12,
    )
    fix = BenchmarkTask(
        task_id="t2",
        name="fix",
        instruction="Fix module",
        repository="stats_app",
        category="fix",
        max_steps=8,
    )
    read = BenchmarkTask(
        task_id="t3",
        name="read",
        instruction="Read module",
        repository="stats_app",
        category="read",
        max_steps=8,
    )

    assert resolve_benchmark_max_steps(create) >= 18
    assert resolve_benchmark_max_steps(fix) >= 12
    assert resolve_benchmark_max_steps(read) == 8


def test_evaluate_task_success_ignores_pytest_for_read_only() -> None:
    from casi.evaluation.runner import evaluate_task_success

    task = BenchmarkTask(
        task_id="t1",
        name="read",
        instruction="Explain",
        repository="math_app",
        category="read",
    )
    assert (
        evaluate_task_success(task, agent_success=True, command_success=False) is True
    )
    assert (
        evaluate_task_success(task, agent_success=False, command_success=True) is False
    )

    fix = BenchmarkTask(
        task_id="t2",
        name="fix",
        instruction="Fix",
        repository="email_app",
        category="fix",
    )
    assert (
        evaluate_task_success(fix, agent_success=True, command_success=False) is False
    )
    assert evaluate_task_success(fix, agent_success=True, command_success=True) is True

    create = BenchmarkTask(
        task_id="t3",
        name="create",
        instruction="Create module",
        repository="stats_app",
        category="create",
    )
    assert (
        evaluate_task_success(create, agent_success=True, command_success=False)
        is False
    )
    assert (
        evaluate_task_success(create, agent_success=True, command_success=True) is True
    )


def test_cli_benchmark_lists_tasks(capsys) -> None:
    exit_code = main(["benchmark", "--list"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "task_001" in output
    assert "healthy_lib" in output


def test_docker_runner_reports_unavailable_without_docker() -> None:
    runner = DockerRunner(image="casi-sandbox:missing")
    if runner.is_available():
        pytest.skip("Docker is available; skipping unavailable-path test")

    with pytest.raises(RuntimeError, match="Docker is not available"):
        runner.run(Path("."), [sys.executable, "-c", "print('hi')"])
