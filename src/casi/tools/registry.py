"""Registry for structured tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from casi.llm.base import ToolDefinition
from casi.tools.base import Tool
from casi.tools.file_tools import ListFilesTool, ReadFileTool
from casi.tools.result import ToolResult
from casi.tools.search_tools import SearchCodeTool


@dataclass
class ToolRegistry:
    repository_path: str | Path
    _tools: dict[str, Tool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self._tools:
            self.register(ListFilesTool(self.repository_path))
            self.register(ReadFileTool(self.repository_path))
            self.register(SearchCodeTool(self.repository_path))

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def definitions(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name=tool.name,
                description=tool.description,
                arguments={
                    name: {
                        "type": self._type_name(spec.type),
                        "required": spec.required,
                    }
                    for name, spec in tool.argument_schema.items()
                },
            )
            for tool in self._tools.values()
        ]

    @staticmethod
    def _type_name(expected_type: type | tuple[type, ...]) -> str:
        if isinstance(expected_type, tuple):
            return " | ".join(type_.__name__ for type_ in expected_type)
        return expected_type.__name__

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {name}",
                metadata={"tool_name": name},
            )

        try:
            result = tool.execute(arguments)
        except (TypeError, ValueError, FileNotFoundError, IsADirectoryError) as exc:
            return ToolResult(
                success=False,
                output="",
                error=str(exc),
                metadata={"tool_name": name},
            )

        return result


tool_registry = ToolRegistry(Path("."))