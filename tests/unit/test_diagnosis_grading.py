"""Unit tests for diagnosis response parsing and grading."""

from __future__ import annotations

import json
from pathlib import Path

from casi.evaluation.diagnosis import grade_diagnosis_response, load_diagnosis_rubric
from casi.llm.diagnosis import extract_diagnosis_payload

RUBRIC = load_diagnosis_rubric(
    Path(__file__).resolve().parents[2]
    / "benchmarks"
    / "diagnosis"
    / "rubrics"
    / "diag_001"
    / "rubric.yaml"
)


def test_extract_diagnosis_payload_from_final_json():
    payload = {
        "file": "counter.py",
        "line": 9,
        "cause": "zero increment",
        "evidence": "+= 0",
    }
    response = json.dumps({"type": "final", "content": json.dumps(payload)})
    assert extract_diagnosis_payload(response) == payload


def test_grade_diagnosis_response_checks_line_and_terms():
    response = json.dumps(
        {
            "type": "final",
            "content": json.dumps(
                {
                    "file": "counter.py",
                    "line": 9,
                    "cause": "increment adds zero",
                    "evidence": "self._value += 0",
                }
            ),
        }
    )
    grade = grade_diagnosis_response(response, rubric=RUBRIC)
    assert grade.passed


def test_verbose_diagnosis_passes_when_factually_correct():
    response = json.dumps(
        {
            "type": "final",
            "content": json.dumps(
                {
                    "file": "counter.py",
                    "line": 9,
                    "cause": (
                        "The increment method adds 0 instead of 1 to self._value, "
                        "so repeated increments never change the stored counter."
                    ),
                    "evidence": (
                        "Line 9 shows self._value += 0, which leaves the counter "
                        "at zero after any number of increment calls."
                    ),
                }
            ),
        }
    )
    grade = grade_diagnosis_response(response, rubric=RUBRIC)
    assert grade.passed, grade.reasons
