"""Structured tool execution results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolResult:
    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)
