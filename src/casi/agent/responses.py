"""Final-response validation helpers."""

from __future__ import annotations

import json

from casi.agent.intent import task_requests_code_change
from casi.patching.extract import extract_patch

_FINAL_JSON_KEYS = ("content", "response", "message", "answer", "text", "assistant")
_PATCH_JSON_KEYS = ("patch", "diff", "unified_diff", "unifiedDiff")


def is_malformed_json(content: str) -> bool:
    """Detect final replies that are JSON objects without usable answer text."""

    text = content.strip()
    if not text.startswith("{"):
        return False
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return False
    if not isinstance(payload, dict):
        return False
    if payload.get("type") in {"final", "clarification", "tool_call"}:
        return False
    if isinstance(payload.get("name"), str) and isinstance(
        payload.get("arguments"), dict
    ):
        return False
    for key in (*_FINAL_JSON_KEYS, *_PATCH_JSON_KEYS):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return False
    return True


def response_missing_required_patch(
    content: str,
    context: str,
    *,
    repository_inspected: bool,
    mutation_workflow: bool = False,
) -> bool:
    """Detect fix requests that ended without a unified diff."""

    if not mutation_workflow and not task_requests_code_change(context):
        return False
    if not repository_inspected:
        return False
    return extract_patch(content) is None
