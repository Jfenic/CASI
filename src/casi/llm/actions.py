"""Structured action schemas for constrained Ollama mutation turns."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProposeFileAction:
    """Required CREATE mutation payload: repository path and complete file content."""

    path: str
    content: str

    tool_name: str = "propose_file"

    @classmethod
    def json_schema(cls) -> dict[str, Any]:
        """Return the Ollama structured-output schema for this action."""

        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        }

    @classmethod
    def from_json(cls, text: str) -> ProposeFileAction:
        """Parse and validate model output for a propose_file action."""

        payload: Any = json.loads(text.strip())
        if not isinstance(payload, dict):
            raise ValueError("Action payload must be a JSON object")

        path = payload.get("path")
        content = payload.get("content")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("path must be a non-empty string")
        if not isinstance(content, str):
            raise ValueError("content must be a string")
        return cls(path=path, content=content)

    def as_tool_arguments(self) -> dict[str, str]:
        """Return ToolRegistry arguments for propose_file."""

        return {"path": self.path, "content": self.content}


def action_validation_error(error: str) -> str:
    """Return a structural retry message for invalid action schema output."""

    return (
        "Protocol violation: response does not match ProposeFileAction schema. "
        f"Validation error: {error}. "
        'Return only JSON with "path" and "content" keys. '
        "No final answer, no tool wrapper, no markdown fences."
    )
