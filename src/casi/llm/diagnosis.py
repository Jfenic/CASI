"""Diagnosis response contract shared by runtime validation and evaluation."""

from __future__ import annotations

import json
import re

_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def extract_diagnosis_payload(response: str) -> dict[str, object] | None:
    """Accept a diagnosis object, optionally inside a final envelope or fence."""

    text = response.strip()
    for _ in range(3):
        block = _JSON_BLOCK.fullmatch(text)
        if block is not None:
            text = block.group(1)
        try:
            payload = json.loads(text, strict=False)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        if payload.get("type") != "final":
            return payload
        content = payload.get("content")
        if isinstance(content, dict):
            return content
        if not isinstance(content, str):
            return None
        text = content.strip()
    return None


def diagnosis_response_error(response: str) -> str | None:
    """Validate structure only; factual correctness requires repository evidence."""

    payload = extract_diagnosis_payload(response)
    if payload is None:
        return "Expected a diagnosis JSON object with file, line, cause, and evidence"
    for field in ("file", "cause", "evidence"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            return f"Diagnosis field {field!r} must be a non-empty string"
    line = payload.get("line")
    if type(line) is not int or line < 1:
        return "Diagnosis field 'line' must be a positive integer"
    if any(marker in response for marker in ("```diff", "--- a/", "+++ b/")):
        return "Diagnosis must not include a patch"
    return None
