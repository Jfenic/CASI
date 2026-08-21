"""Bounded agent execution loop."""

from __future__ import annotations

from casi_code_agent.agent.executor import execute_tool
from casi_code_agent.agent.state import AgentResult
from casi_code_agent.llm.base import ChatMessage, LLMClient
from casi_code_agent.tools.registry import ToolRegistry
from casi_code_agent.tools.result import ToolResult


class AgentLoop:
	def __init__(
		self,
		client: LLMClient,
		registry: ToolRegistry,
		*,
		max_steps: int = 8,
	) -> None:
		if max_steps < 1:
			raise ValueError("max_steps must be greater than or equal to 1")
		self.client = client
		self.registry = registry
		self.max_steps = max_steps

	def run(self, task: str) -> AgentResult:
		if not task.strip():
			raise ValueError("task must not be empty")

		messages = [ChatMessage(role="user", content=task)]
		tools = self.registry.definitions()

		for step in range(1, self.max_steps + 1):
			response = self.client.complete(messages, tools)
			if response.kind == "final":
				return AgentResult(
					success=True,
					response=response.content,
					steps=step,
					messages=messages,
				)

			if response.kind != "tool_call":
				return AgentResult(
					success=False,
					error=f"Unsupported LLM response kind: {response.kind}",
					steps=step,
					messages=messages,
				)

			result = execute_tool(self.registry, response)
			messages.append(
				ChatMessage(
					role="tool",
					content=self._format_tool_result(response.tool_name, result),
				)
			)

		return AgentResult(
			success=False,
			error=f"Agent reached the maximum of {self.max_steps} steps",
			steps=self.max_steps,
			messages=messages,
		)

	@staticmethod
	def _format_tool_result(tool_name: str | None, result: ToolResult) -> str:
		return f"tool={tool_name}\nsuccess={result.success}\noutput={result.output}\nerror={result.error}"
