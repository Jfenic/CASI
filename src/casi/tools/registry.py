"""Registry for structured tools."""

from __future__ import annotations

from collections.abc import Callable

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from casi.agent.policies import AGENT_TOOL_NAMES, is_mutation_tool
from casi.agent.planner import AgentPlan
from casi.llm.base import ToolDefinition
from casi.tools.base import Tool
from casi.tools.file_tools import ListFilesTool, ReadFileTool
from casi.tools.git_tools import GitDiffTool
from casi.tools.result import ToolResult
from casi.tools.search_tools import SearchCodeTool
from casi.tools.session_tools import GetSessionPlanTool
from casi.tools.test_tools import RunTestsTool
from casi.tools.patch_tools import ProposeFileTool, ValidatePatchTool
from casi.tools.patch_tools import ApplyPatchTool


@dataclass
class ToolRegistry:
    repository_path: str | Path
    plan_provider: Callable[[], AgentPlan | None] | None = None
    _tools: dict[str, Tool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self._tools:
            self.register(ListFilesTool(self.repository_path))
            self.register(ReadFileTool(self.repository_path))
            self.register(SearchCodeTool(self.repository_path))
            self.register(RunTestsTool(self.repository_path))
            self.register(GitDiffTool(self.repository_path))
            self.register(ValidatePatchTool(self.repository_path))
            self.register(ProposeFileTool(self.repository_path))
            self.register(ApplyPatchTool(self.repository_path))
            if self.plan_provider is not None:
                self.register(GetSessionPlanTool(self.plan_provider))

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def definitions(self, *, agent_safe: bool = False) -> list[ToolDefinition]:
        tools = self._tools.values()
        if agent_safe:
            tools = [tool for tool in tools if tool.name in AGENT_TOOL_NAMES]

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
            for tool in tools
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

        if is_mutation_tool(name):
            return ToolResult(
                success=False,
                output="",
                error=(
                    "Mutation tools cannot be executed through the agent. "
                    "Propose a unified diff in the final response instead."
                ),
                metadata={"tool_name": name, "blocked": True},
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
