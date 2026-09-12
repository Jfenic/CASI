"""Grade bounded diagnosis responses against withheld rubrics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from casi.llm.diagnosis import extract_diagnosis_payload


@dataclass(frozen=True)
class DiagnosisRubric:
    """Expected elements for a bounded failure-analysis response."""

    file: str
    line_min: int | None
    line_max: int | None
    cause_terms_any: tuple[str, ...]
    cause_terms_all: tuple[str, ...]
    evidence_terms_any: tuple[str, ...]
    evidence_terms_all: tuple[str, ...]
    required_fields: tuple[str, ...]
    forbidden_patterns: tuple[str, ...]


@dataclass(frozen=True)
class DiagnosisGrade:
    """Outcome of grading one diagnosis response."""

    passed: bool
    reasons: tuple[str, ...]
    payload: dict[str, object] | None = None


def load_diagnosis_rubric(path: Path) -> DiagnosisRubric:
    """Load a rubric YAML file from a response grader directory."""

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid diagnosis rubric: {path}")

    line = data.get("line") or {}
    if not isinstance(line, dict):
        raise ValueError(f"line must be a mapping in {path}")

    def terms(key: str, *, default_any: list[str] | None = None) -> tuple[str, ...]:
        block = data.get(key) or {}
        if not isinstance(block, dict):
            raise ValueError(f"{key} must be a mapping in {path}")
        any_terms = block.get("any") or default_any or []
        all_terms = block.get("all") or []
        if not isinstance(any_terms, list) or not isinstance(all_terms, list):
            raise ValueError(f"{key}.any/all must be lists in {path}")
        return tuple(str(term).lower() for term in any_terms), tuple(
            str(term).lower() for term in all_terms
        )

    cause_any, cause_all = terms("cause")
    evidence_any, evidence_all = terms("evidence")

    forbidden = data.get("forbidden") or []
    if not isinstance(forbidden, list):
        raise ValueError(f"forbidden must be a list in {path}")

    required_fields = data.get("required_fields") or [
        "file",
        "line",
        "cause",
        "evidence",
    ]
    if not isinstance(required_fields, list):
        raise ValueError(f"required_fields must be a list in {path}")

    file_name = str(data.get("file") or "")
    if not file_name:
        raise ValueError(f"file is required in {path}")

    return DiagnosisRubric(
        file=file_name,
        line_min=int(line["min"]) if "min" in line else None,
        line_max=int(line["max"]) if "max" in line else None,
        cause_terms_any=cause_any,
        cause_terms_all=cause_all,
        evidence_terms_any=evidence_any,
        evidence_terms_all=evidence_all,
        required_fields=tuple(str(field) for field in required_fields),
        forbidden_patterns=tuple(str(pattern) for pattern in forbidden),
    )


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    if not terms:
        return True
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _contains_all(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return all(term in lowered for term in terms)


def grade_diagnosis_response(
    response: str,
    *,
    rubric: DiagnosisRubric,
) -> DiagnosisGrade:
    """Return whether a bounded diagnosis response satisfies the rubric."""

    reasons: list[str] = []
    lowered_response = response.lower()
    for pattern in rubric.forbidden_patterns:
        if pattern.lower() in lowered_response:
            reasons.append(f"forbidden pattern present: {pattern}")

    payload = extract_diagnosis_payload(response)
    if payload is None:
        reasons.append("missing or invalid diagnosis JSON payload")
        return DiagnosisGrade(passed=False, reasons=tuple(reasons))

    for field in rubric.required_fields:
        if field not in payload:
            reasons.append(f"missing required field: {field}")

    file_value = str(payload.get("file", "")).strip()
    if Path(file_value).name != Path(rubric.file).name:
        reasons.append(f"expected file {rubric.file!r}, got {file_value!r}")

    line_value = payload.get("line")
    if rubric.line_min is not None or rubric.line_max is not None:
        if not isinstance(line_value, int):
            reasons.append("line must be an integer")
        else:
            if rubric.line_min is not None and line_value < rubric.line_min:
                reasons.append(f"line {line_value} below minimum {rubric.line_min}")
            if rubric.line_max is not None and line_value > rubric.line_max:
                reasons.append(f"line {line_value} above maximum {rubric.line_max}")

    cause = str(payload.get("cause", ""))
    evidence = str(payload.get("evidence", ""))

    if not _contains_any(cause, rubric.cause_terms_any):
        reasons.append("cause missing expected failure description")
    if not _contains_all(cause, rubric.cause_terms_all):
        reasons.append("cause missing required terms")

    if not _contains_any(evidence, rubric.evidence_terms_any):
        reasons.append("evidence missing expected symbol or expression")
    if not _contains_all(evidence, rubric.evidence_terms_all):
        reasons.append("evidence missing required terms")

    return DiagnosisGrade(
        passed=not reasons,
        reasons=tuple(reasons),
        payload=payload,
    )


def grade_diagnosis_task(
    response: str,
    *,
    grader_directory: Path,
) -> DiagnosisGrade:
    """Grade a diagnosis response using rubric.yaml in a grader directory."""

    rubric_path = grader_directory / "rubric.yaml"
    if not rubric_path.is_file():
        raise ValueError(f"Diagnosis rubric not found: {rubric_path}")
    rubric = load_diagnosis_rubric(rubric_path)
    return grade_diagnosis_response(response, rubric=rubric)
