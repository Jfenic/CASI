"""Check the versioned capability extension without an Ollama server."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from casi.evaluation.benchmark import load_tasks
from casi.evaluation.grading import grade_task
from casi.sandbox.local_runner import LocalRunner

SUITE = Path(__file__).resolve().parents[2] / "benchmarks" / "capabilities_v2"
CASES = [
    (area, task)
    for area in ("testing", "security", "ml")
    for task in load_tasks(SUITE / area / "tasks")
]


@pytest.mark.parametrize("area,task", CASES, ids=[t.task_id for _, t in CASES])
def test_extension_rejects_baseline_and_accepts_reference(area, task):
    root = SUITE / area
    original = root / "repositories" / task.repository
    baseline, _ = grade_task(
        task, original=original, candidate=original, runner=LocalRunner()
    )
    # All fixtures import successfully: baseline rejection is an assertion failure.
    assert baseline.exit_code == 1, baseline.stdout + baseline.stderr
    assert not baseline.timed_out
    reference, _ = grade_task(
        task,
        original=original,
        candidate=root / "solutions" / task.repository,
        runner=LocalRunner(),
    )
    assert reference.exit_code == 0, reference.stdout + reference.stderr
    assert not reference.timed_out


@pytest.mark.parametrize(
    "task", [t for area, t in CASES if area == "testing"], ids=lambda t: t.task_id
)
def test_generated_suite_that_asserts_true_does_not_detect_mutations(task, tmp_path):
    (tmp_path / task.allowed_files[0]).write_text(
        "def test_empty():\n    assert True\n"
    )
    result, _ = grade_task(
        task,
        original=SUITE / "testing" / "repositories" / task.repository,
        candidate=tmp_path,
        runner=LocalRunner(),
    )
    assert result.exit_code == 1, result.stdout + result.stderr
    assert not result.timed_out
    mutants = json.loads((task.grader_directory / "mutants.json").read_text())
    # Every mutation is evaluated, even after the first survivor.
    for name in mutants:
        assert f"test_detects_mutation[{name}]" in result.stdout


@pytest.mark.parametrize(
    "content",
    [
        "def test_always_fails():\n    assert False\n",
        "import nonexistent_candidate_dependency\n",
        "# No tests delivered\n",
    ],
    ids=["always_fails", "import_error", "no_tests"],
)
def test_invalid_control_cannot_score_as_mutation_detection(content, tmp_path):
    task = next(t for area, t in CASES if t.task_id == "test_001")
    (tmp_path / "test_retry.py").write_text(content)
    result, _ = grade_task(
        task,
        original=SUITE / "testing" / "repositories" / task.repository,
        candidate=tmp_path,
        runner=LocalRunner(),
    )
    assert result.exit_code != 0
    assert not result.timed_out
    # Import errors may stop the outer collection before the control runs.
    if "nonexistent_candidate_dependency" not in content:
        assert "CORRECT_IMPLEMENTATION" in result.stdout
        assert "skipped" in result.stdout


@pytest.mark.parametrize(
    "task_id,legacy_repo,missing_mutant",
    [
        ("test_001", "retry_tests", "wrong_default"),
        ("test_002", "slug_tests", "accepts_non_ascii"),
    ],
)
def test_extension_rejects_legacy_coverage_gaps(
    task_id, legacy_repo, missing_mutant, tmp_path
):
    task = next(t for _, t in CASES if t.task_id == task_id)
    filename = task.allowed_files[0]
    legacy = SUITE.parent / "development" / "solutions" / legacy_repo / filename
    (tmp_path / filename).write_text(legacy.read_text())
    result, _ = grade_task(
        task,
        original=SUITE / "testing" / "repositories" / task.repository,
        candidate=tmp_path,
        runner=LocalRunner(),
    )
    assert result.exit_code == 1, result.stdout + result.stderr
    assert not result.timed_out
    assert f"test_detects_mutation[{missing_mutant}]" in result.stdout
