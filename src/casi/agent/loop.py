"""Bounded agent execution loop."""

from __future__ import annotations

from collections.abc import Callable

from casi.agent.executor import execute_tool
from casi.agent.state import AgentResult
from casi.config import settings
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
		messages: list[ChatMessage] | None = None,
		require_tool_confirmation: Callable[[str, dict[str, object]], bool] | None = None,
	) -> None:
		if max_steps < 1:
			raise ValueError("max_steps must be greater than or equal to 1")
		self.client = client
		self.registry = registry
		self.max_steps = max_steps
		# Reuse the same list to preserve context across interactive tasks.
		self.messages = messages if messages is not None else []
		# The callback is the permission boundary for tools that can modify state.
		self.require_tool_confirmation = require_tool_confirmation

	def run(self, task: str) -> AgentResult:
		"""Run the agent until it returns a final response or reaches the limit."""

		if not task.strip():
			raise ValueError("task must not be empty")

		self.messages.append(ChatMessage(role="user", content=task.strip()))
		self._trim_messages()
		# Only tools marked safe for autonomous execution are exposed to the model.
		tools = self.registry.definitions(agent_safe=True)

		for step in range(1, self.max_steps + 1):
			response = self.client.complete(self.messages, tools)

			if response.kind == "final":
				# Store the final answer so the next task can use this conversation turn.
				self.messages.append(
					ChatMessage(role="assistant", content=response.content),
				)
				self._trim_messages()
				return AgentResult(
					success=True,
					response=response.content,
					steps=step,
					messages=self.messages,
				)

			if response.kind == "clarification":
				self.messages.append(
					ChatMessage(role="assistant", content=response.content),
				)
				self._trim_messages()
				return AgentResult(
					success=True,
					clarification=response.content,
					plan=response.plan,
					steps=step,
					messages=self.messages,
				)

			if response.kind != "tool_call":
				# Unknown response types cannot be executed safely.
				return AgentResult(
					success=False,
					error=f"Unsupported LLM response kind: {response.kind}",
					steps=step,
					messages=self.messages,
				)

			# Execution delegates permission checks to the centralized executor.
			result = execute_tool(
				self.registry,
				response,
				require_tool_confirmation=self.require_tool_confirmation,
			)

			self.messages.append(
				ChatMessage(
					role="assistant",
					content=self._format_tool_call(response.tool_name, response.arguments),
				)
			)
			self.messages.append(
				ChatMessage(
					role="tool",
					content=self._format_tool_result(response.tool_name, result),
				)
			)
			self._trim_messages()

		return AgentResult(
			success=False,
			error=f"Agent reached the maximum of {self.max_steps} steps",
			steps=self.max_steps,
			messages=self.messages,
		)

	def _trim_messages(self) -> None:
		"""Keep the most recent conversation messages within configured limits."""

		limit = settings.max_context_messages
		if len(self.messages) <= limit:
			return
		self.messages[:] = self.messages[-limit:]

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
