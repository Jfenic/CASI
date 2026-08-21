"""Action execution helpers for the agent."""

from casi.llm.base import LLMResponse
from casi.tools.registry import ToolRegistry
from casi.tools.result import ToolResult


def execute_tool(registry: ToolRegistry, response: LLMResponse) -> ToolResult:
	if response.kind != "tool_call" or response.tool_name is None:
		raise ValueError("Expected a tool-call response")
	return registry.execute(response.tool_name, response.arguments)
