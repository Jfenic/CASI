"""Parsing helpers for the structured LLM response format."""

from __future__ import annotations

import json
from typing import Any

from casi.llm.base import LLMResponse

_FINAL_CONTENT_KEYS = ("content", "response", "message", "answer", "text", "assistant")
_PATCH_CONTENT_KEYS = ("patch", "diff", "unified_diff", "unifiedDiff")


def _extract_final_content(payload: dict[str, Any]) -> str | None:
    """Extract human-readable text and embedded diffs from common JSON shapes."""

    parts: list[str] = []
    for key in _FINAL_CONTENT_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
            break
    for key in _PATCH_CONTENT_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
            break
    if not parts:
        return None
    return "\n\n".join(parts)


def parse_response(raw_response: str) -> LLMResponse:
    """Parse a JSON response containing a final answer or tool call."""

    try:
        payload: Any = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM response must be valid JSON") from exc

    if not isinstance(payload, dict):
        raise ValueError("LLM response must be a JSON object")

    response_type = payload.get("type")
    if response_type == "final":
        content = _extract_final_content(payload)
        if content is None:
            raise ValueError("Final response requires non-empty string content")
        return LLMResponse.final(content)

    if response_type == "tool_call":
        name = payload.get("name")
        arguments = payload.get("arguments", {})
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Tool call requires a non-empty string name")
        if not isinstance(arguments, dict):
            raise ValueError("Tool call arguments must be a JSON object")
        return LLMResponse.tool_call(name, arguments)

    name = payload.get("name")
    if isinstance(name, str) and name.strip():
        arguments = payload.get("arguments", {})
        if not isinstance(arguments, dict):
            raise ValueError("Tool call arguments must be a JSON object")
        return LLMResponse.tool_call(name, arguments)

    alternate_content = _extract_final_content(payload)
    if alternate_content is not None:
        return LLMResponse.final(alternate_content)

    if response_type == "clarification":
        question = payload.get("question")
        plan = payload.get("plan", [])
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Clarification requires a non-empty question")
        if not isinstance(plan, list) or not all(
            isinstance(item, str) for item in plan
        ):
            raise ValueError("Clarification plan must be a list of strings")
        return LLMResponse.clarification(question, plan)

    raise ValueError(
        "LLM response type must be 'final', 'tool_call', or 'clarification'"
    )
