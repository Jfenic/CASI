"""Map Python tool argument types to JSON Schema types for Ollama."""

from __future__ import annotations

from pathlib import Path

_JSON_SCHEMA_TYPES = {
    int: "integer",
    float: "number",
    bool: "boolean",
    str: "string",
    Path: "string",
}


def json_schema_type(expected_type: type | tuple[type, ...]) -> str:
    """Return a JSON Schema type string accepted by Ollama structured output."""

    if isinstance(expected_type, tuple):
        mapped = {json_schema_type(type_) for type_ in expected_type}
        if mapped == {"integer"}:
            return "integer"
        if mapped <= {"integer", "number"}:
            return "number"
        return "string"

    return _JSON_SCHEMA_TYPES.get(expected_type, "string")


def normalize_json_schema_type(type_name: str) -> str:
    """Normalize legacy Python type names stored on tool definitions."""

    cleaned = type_name.replace(" ", "")
    if cleaned in {"int", "integer"}:
        return "integer"
    if cleaned in {"float", "number"}:
        return "number"
    if cleaned in {"bool", "boolean"}:
        return "boolean"
    if cleaned in {"str", "string", "Path"}:
        return "string"
    if "|" in cleaned:
        parts = cleaned.split("|")
        return normalize_json_schema_type(parts[0])
    return "string"
