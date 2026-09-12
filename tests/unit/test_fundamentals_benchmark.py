"""Validate fundamentals suite baseline failures and reference solutions."""

from __future__ import annotations

from pathlib import Path

import pytest

from casi.evaluation.benchmark import load_tasks
from casi.evaluation.grading import grade_task
from casi.sandbox.local_runner import LocalRunner

SUITE = Path(__file__).resolve().parents[2] / "benchmarks" / "fundamentals"
TASKS = load_tasks(SUITE / "tasks")


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.task_id)
def test_fundamentals_task_rejects_baseline_and_accepts_reference(task):
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
