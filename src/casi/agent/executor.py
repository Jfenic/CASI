"""Action execution helpers for the agent."""

from __future__ import annotations

from collections.abc import Callable

from casi.agent.policies import requires_confirmation
from casi.llm.base import LLMResponse
from casi.tools.registry import ToolRegistry
from casi.tools.result import ToolResult


def execute_tool(
	registry: ToolRegistry,
	response: LLMResponse,
	*,
	require_tool_confirmation: Callable[[str, dict[str, object]], bool] | None = None,
) -> ToolResult:
	if response.kind != "tool_call" or response.tool_name is None:
		raise ValueError("Expected a tool-call response")

	tool_name = response.tool_name
	arguments = response.arguments

	if require_tool_confirmation and requires_confirmation(tool_name):
		if not require_tool_confirmation(tool_name, arguments):
			return ToolResult(
				success=False,
				output="",
				error=f"Tool execution denied by user: {tool_name}",
				metadata={"tool_name": tool_name, "denied": True},
			)

	return registry.execute(tool_name, arguments)
