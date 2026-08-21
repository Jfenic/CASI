"""Bounded agent execution loop."""

from __future__ import annotations

from casi.agent.executor import execute_tool
from casi.agent.state import AgentResult
from casi.llm.base import ChatMessage, LLMClient
from casi.tools.registry import ToolRegistry
from casi.tools.result import ToolResult


class AgentLoop:
	"""Coordinate model decisions and structured tool execution."""

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
		"""Run the agent until it returns a final response or reaches the limit."""

		if not task.strip():
			raise ValueError("task must not be empty")

		messages = [ChatMessage(role="user", content=task)]
		tools = self.registry.definitions()

		# Each iteration represents one model decision and keeps execution bounded.
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

			# Preserve the assistant decision before returning the tool result.
			messages.append(
				ChatMessage(
					role="assistant",
					content=self._format_tool_call(response.tool_name, response.arguments),
				)
			)

			# Tool output becomes the next piece of context for the model.
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
		"""Serialize a tool result into the model's conversation context."""

		return (
			f"tool={tool_name}\n"
			f"success={result.success}\n"
			f"output={result.output}\n"
			f"error={result.error}"
		)

	@staticmethod
	def _format_tool_call(tool_name: str | None, arguments: dict[str, object]) -> str:
		"""Serialize the assistant's tool decision for the next model request."""

		return f"Called tool={tool_name} with arguments={arguments}"
