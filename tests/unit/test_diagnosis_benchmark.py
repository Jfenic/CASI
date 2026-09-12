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
        "line": 9,
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
    "diag_006": {
        "file": "normalize.py",
        "line": 7,
        "cause": "off-by-one divisor uses len(values) - 1 instead of len(values)",
        "evidence": "len(values) - 1",
    },
    "diag_007": {
        "file": "discount.py",
        "line": 5,
        "cause": "gold discount uses exclusive greater-than at the 100 threshold",
        "evidence": "total > 100",
    },
    "diag_008": {
        "file": "totals.py",
        "line": 10,
        "cause": "subtotal adds unit price without multiplying by line quantity",
        "evidence": "catalog.get_price(sku)",
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


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.task_id)
def test_rubric_line_range_matches_reference_bug_line(task):
    """The reference line must fall inside the rubric range and grade as pass."""

    assert task.response_grader_directory is not None
    rubric = load_diagnosis_rubric(task.response_grader_directory / "rubric.yaml")
    reference = REFERENCE_RESPONSES[task.task_id]
    line = reference["line"]
    if rubric.line_min is not None:
        assert line >= rubric.line_min, (
            f"{task.task_id}: reference line {line} is below rubric minimum "
            f"{rubric.line_min}"
        )
    if rubric.line_max is not None:
        assert line <= rubric.line_max, (
            f"{task.task_id}: reference line {line} is above rubric maximum "
            f"{rubric.line_max}"
        )


def test_diag_002_rubric_accepts_correct_source_line():
    """Regression: line 9 is the buggy statement in clamp.py, not line 10+."""

    grader = SUITE / "rubrics" / "diag_002"
    response = _final_response(REFERENCE_RESPONSES["diag_002"])
    grade = grade_diagnosis_task(response, grader_directory=grader)
    assert grade.passed, grade.reasons

    wrong_line = _final_response({**REFERENCE_RESPONSES["diag_002"], "line": 10})
    wrong_grade = grade_diagnosis_task(wrong_line, grader_directory=grader)
    assert not wrong_grade.passed
    assert any("line 10" in reason for reason in wrong_grade.reasons)


def test_patch_like_response_fails_rubric():
    task = TASKS[0]
    assert task.response_grader_directory is not None
    patched = (
        _final_response(REFERENCE_RESPONSES[task.task_id]) + "\n```diff\n--- a/x\n"
    )
    grade = grade_diagnosis_task(
        patched, grader_directory=task.response_grader_directory
    )
    assert not grade.passed
    assert any("forbidden" in reason for reason in grade.reasons)
