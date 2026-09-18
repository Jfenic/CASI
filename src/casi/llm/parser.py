"""Parsing helpers for the structured LLM response format."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from casi.llm.base import LLMResponse, ToolDefinition

_FINAL_CONTENT_KEYS = ("content", "response", "message", "answer", "text", "assistant")
_PATCH_CONTENT_KEYS = ("patch", "diff", "unified_diff", "unifiedDiff")


def _extract_final_content(payload: dict[str, Any]) -> str | None:
    """Extract human-readable text and embedded diffs from common JSON shapes."""

    parts: list[str] = []
    for key in _FINAL_CONTENT_KEYS:
        value = payload.get(key)
        if key == "content" and isinstance(value, dict) and value:
            parts.append(json.dumps(value, ensure_ascii=False))
            break
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
        payload: Any = json.loads(raw_response, strict=False)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM response must be valid JSON") from exc

    if not isinstance(payload, dict):
        raise ValueError("LLM response must be a JSON object")

    response_type = payload.get("type")
    if response_type == "final":
        content = _extract_final_content(payload)
        if content is None:
            raise ValueError(
                "Final response requires non-empty string or object content"
            )
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


def _strip_json_fences(text: str) -> str:
    content = text.strip()
    if content.startswith("```") and content.endswith("```"):
        content = content[3:-3].strip()
        if content.startswith("json"):
            content = content[4:].strip()
    return content


def _tool_call_from_dict(payload: dict[str, Any]) -> dict[str, object] | None:
    name = payload.get("name")
    arguments = payload.get("arguments")
    if isinstance(name, str) and name.strip() and isinstance(arguments, dict):
        return {"name": name, "arguments": arguments}
    return None


def extract_tool_call_payload(text: str) -> dict[str, object] | None:
    """Return a single tool-call-shaped dict embedded in text, if present."""

    content = _strip_json_fences(text)
    if not content:
        return None

    try:
        payload: Any = json.loads(content, strict=False)
    except json.JSONDecodeError:
        return None

    if isinstance(payload, list):
        if len(payload) != 1 or not isinstance(payload[0], dict):
            return None
        payload = payload[0]

    if not isinstance(payload, dict):
        return None

    response_type = payload.get("type")
    if response_type in {"final", "tool_call"}:
        inner = payload.get("content")
        if isinstance(inner, str):
            return extract_tool_call_payload(inner)
        if isinstance(inner, dict):
            return _tool_call_from_dict(inner)
        if response_type == "tool_call":
            return _tool_call_from_dict(payload)
        return None

    return _tool_call_from_dict(payload)


def _tool_definition(
    allowed_tools: Sequence[ToolDefinition], name: str
) -> ToolDefinition | None:
    for tool in allowed_tools:
        if tool.name == name:
            return tool
    return None


def _arguments_match_schema(tool: ToolDefinition, arguments: dict[str, object]) -> bool:
    for argument_name, spec in tool.arguments.items():
        if not isinstance(spec, dict):
            continue
        required = bool(spec.get("required"))
        if required and argument_name not in arguments:
            return False
        if argument_name not in arguments:
            continue
        value = arguments[argument_name]
        expected_type = str(spec.get("type", "string"))
        if expected_type == "string" and not isinstance(value, str):
            return False
        if expected_type == "integer" and not isinstance(value, int):
            return False
        if expected_type == "boolean" and not isinstance(value, bool):
            return False

    unexpected = sorted(set(arguments) - set(tool.arguments))
    return not unexpected


def tool_call_allowed(
    name: str,
    arguments: dict[str, object],
    allowed_tools: Sequence[ToolDefinition],
) -> bool:
    """Return whether a tool call matches a known tool schema."""

    tool = _tool_definition(allowed_tools, name)
    if tool is None:
        return False
    return _arguments_match_schema(tool, arguments)


def normalize_response(
    response: LLMResponse,
    *,
    allowed_tools: Sequence[ToolDefinition] | None = None,
) -> LLMResponse:
    """Coerce embedded tool JSON inside a final envelope to a tool call.

    When ``allowed_tools`` is provided, recovery is strict: the tool name must be
    known, arguments must match the tool schema, and exactly one action may be
    embedded. When omitted, any single embedded tool call is recovered.
    """

    if response.kind != "final":
        return response
    payload = extract_tool_call_payload(response.content)
    if payload is None:
        return response
    name = payload["name"]
    arguments = payload["arguments"]
    if not isinstance(name, str) or not isinstance(arguments, dict):
        return response
    if allowed_tools is not None and not tool_call_allowed(
        name, arguments, allowed_tools
    ):
        return response
    return LLMResponse.tool_call(name, arguments)
