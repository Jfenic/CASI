"""Bounded agent execution loop."""

from __future__ import annotations

import re
from collections.abc import Callable

from casi.agent.executor import execute_tool
from casi.agent.state import AgentResult, PatchVerification
from casi.config import settings
from casi.llm.base import ChatMessage, LLMClient, LLMResponse
from casi.patching.applier import PatchApplicationError
from casi.patching.extract import extract_patch
from casi.patching.validator import validate_patch
from casi.sandbox.patched_tests import run_patched_tests
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
		max_correction_attempts: int | None = None,
		messages: list[ChatMessage] | None = None,
		require_tool_confirmation: Callable[[str, dict[str, object]], bool] | None = None,
	) -> None:
		if max_steps < 1:
			raise ValueError("max_steps must be greater than or equal to 1")
		self.client = client
		self.registry = registry
		self.max_steps = max_steps
		self.max_correction_attempts = (
			settings.max_correction_attempts
			if max_correction_attempts is None
			else max_correction_attempts
		)
		if self.max_correction_attempts < 0:
			raise ValueError("max_correction_attempts must be greater than or equal to 0")
		# Reuse the same list to preserve context across interactive tasks.
		self.messages = messages if messages is not None else []
		self._clarification_pending = False
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
		clarification_seen = self._clarification_pending
		self._clarification_pending = False

		if clarification_seen:
			self._run_post_clarification_search(task.strip())

		correction_attempts = 0
		patch_verification: PatchVerification | None = None

		for step in range(1, self.max_steps + 1):
			response = self.client.complete(self.messages, tools)

			if response.kind == "final":
				patch_verification, should_retry = self._verify_patch_response(
					response.content,
					correction_attempts=correction_attempts,
				)
				if should_retry:
					correction_attempts += 1
					continue

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
					patch_verification=patch_verification,
				)

			if response.kind == "clarification":
				if clarification_seen:
					self.messages.append(
						ChatMessage(
							role="user",
							content=(
								"The user has already clarified the request. Do not ask another "
								"scope or location question; use the repository tools now."
							),
						)
					)
					self._trim_messages()
					continue
				clarification_seen = True
				self._clarification_pending = True
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
			patch_verification=patch_verification,
		)

	def _verify_patch_response(
		self,
		content: str,
		*,
		correction_attempts: int,
	) -> tuple[PatchVerification | None, bool]:
		"""Run patched tests on a final response or ask the model to retry."""

		patch = extract_patch(content)
		if patch is None:
			return None, False

		validation = validate_patch(self.registry.repository_path, patch)
		if not validation.valid:
			return None, False

		try:
			test_result, runner = run_patched_tests(
				self.registry.repository_path,
				patch,
			)
		except (ValueError, PatchApplicationError):
			return None, False

		output = test_result.stdout
		if test_result.stderr:
			output = f"{output}\n{test_result.stderr}".strip()
		passed = test_result.exit_code == 0 and not test_result.timed_out
		verification = PatchVerification(
			passed=passed,
			output=output,
			runner=runner,
			correction_attempts=correction_attempts,
		)

		if passed or correction_attempts >= self.max_correction_attempts:
			return verification, False

		self.messages.append(ChatMessage(role="assistant", content=content))
		self.messages.append(
			ChatMessage(
				role="user",
				content=(
					f"The proposed patch failed tests in the {runner} sandbox.\n"
					f"Output:\n{output}\n"
					"Provide a corrected unified diff that fixes the failures."
				),
			)
		)
		self._trim_messages()
		return None, True

	def _trim_messages(self) -> None:
		"""Keep the most recent conversation messages within configured limits."""

		limit = settings.max_context_messages
		if len(self.messages) <= limit:
			return
		self.messages[:] = self.messages[-limit:]

	_SEARCH_STOP_WORDS = frozenset(
		{
			"a",
			"add",
			"agrega",
			"añade",
			"and",
			"arregla",
			"bad",
			"corrige",
			"corregir",
			"de",
			"el",
			"fix",
			"la",
			"las",
			"los",
			"por",
			"please",
			"pruebas",
			"reject",
			"test",
			"tests",
			"the",
			"un",
			"una",
			"without",
			"y",
		}
	)

	def _run_post_clarification_search(self, task: str) -> None:
		"""Inspect the repository immediately after the user clarifies scope."""

		response: LLMResponse | None = None
		result: ToolResult | None = None
		for query in self._derive_search_queries(task):
			candidate = LLMResponse.tool_call("search_code", {"query": query})
			candidate_result = execute_tool(
				self.registry,
				candidate,
				require_tool_confirmation=self.require_tool_confirmation,
			)
			response = candidate
			result = candidate_result
			if candidate_result.output.strip():
				break

		if response is None or result is None:
			return

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

	@classmethod
	def _derive_search_queries(cls, task: str) -> list[str]:
		"""Build repository search queries from a clarified task."""

		tokens = re.findall(r"\w+", task, flags=re.UNICODE)
		meaningful = [
			token
			for token in tokens
			if len(token) > 2 and token.lower() not in cls._SEARCH_STOP_WORDS
		]
		if not meaningful:
			return [task]

		queries: list[str] = []
		for token in meaningful:
			if "_" in token and token not in queries:
				queries.append(token)
		for token in sorted(meaningful, key=len, reverse=True):
			if token not in queries:
				queries.append(token)
		return queries

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
