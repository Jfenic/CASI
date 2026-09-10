"""Validate diagnosis task rubrics and reference responses."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from casi.evaluation.benchmark import load_tasks
from casi.evaluation.diagnosis import grade_diagnosis_task, load_diagnosis_rubric

SUITE = Path(__file__).resolve().parents[2] / "benchmarks" / "diagnosis"
TASKS = load_tasks(SUITE / "tasks")

REFERENCE_RESPONSES = {
    "diag_001": {
        "file": "counter.py",
        "line": 9,
        "cause": "increment adds zero so the counter never changes",
        "evidence": "self._value += 0",
    },
    "diag_002": {
        "file": "clamp.py",
        "line": 11,
        "cause": "in-range values return value plus one",
        "evidence": "return value + 1",
    },
    "diag_003": {
        "file": "sorter.py",
        "line": 5,
        "cause": "sort_asc uses reverse so order is descending",
        "evidence": "sorted(values, reverse=True)",
    },
    "diag_004": {
        "file": "stats.py",
        "line": 7,
        "cause": "mean subtracts one after dividing the sum",
        "evidence": "sum(values) / len(values) - 1.0",
    },
    "diag_005": {
        "file": "validator.py",
        "line": 7,
        "cause": "validation only checks for a dot, not an at sign",
        "evidence": '"." in email',
    },
}


def _final_response(payload: dict[str, object]) -> str:
    return json.dumps(
        {"type": "final", "content": json.dumps(payload, ensure_ascii=False)},
        ensure_ascii=False,
    )


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.task_id)
def test_reference_diagnosis_passes_rubric(task):
    assert task.response_grader_directory is not None
    response = _final_response(REFERENCE_RESPONSES[task.task_id])
    grade = grade_diagnosis_task(
        response,
        grader_directory=task.response_grader_directory,
    )
    assert grade.passed, grade.reasons


def test_diagnosis_tasks_use_diagnose_category():
    assert TASKS
    assert all(task.category == "diagnose" for task in TASKS)
    assert all(task.response_grader_directory is not None for task in TASKS)


def test_vague_diagnosis_fails_rubric():
    task = TASKS[0]
    assert task.response_grader_directory is not None
    vague = _final_response(
        {
            "file": "counter.py",
            "line": 9,
            "cause": "tests fail",
            "evidence": "unknown",
        }
    )
    grade = grade_diagnosis_task(
        vague,
        grader_directory=task.response_grader_directory,
    )
    assert not grade.passed


def test_patch_like_response_fails_rubric():
    task = TASKS[0]
    assert task.response_grader_directory is not None
    rubric = load_diagnosis_rubric(task.response_grader_directory / "rubric.yaml")
    patched = _final_response(REFERENCE_RESPONSES[task.task_id]) + "\n```diff\n--- a/x\n"
    grade = grade_diagnosis_task(patched, grader_directory=task.response_grader_directory)
    assert not grade.passed
    assert any("forbidden" in reason for reason in grade.reasons)
