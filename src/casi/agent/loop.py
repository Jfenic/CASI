"""Bounded agent execution loop."""

from __future__ import annotations

from collections.abc import Callable

from casi.agent.conversation import ContextCompactNotifier, ContextCompactPrompt, Conversation
from casi.agent.intent import (
	RoutingMode,
	TaskIntent,
	build_task_context,
	classify_intent,
	extract_search_targets,
	intent_supports_pipeline,
	parse_routing_mode,
	should_defer_clarification,
	task_requests_code_change,
)
from casi.agent.nudges import (
	nudge_for_premature_clarification,
	nudge_for_read_file_instead_of_search,
	nudge_for_repeated_clarification,
)
from casi.agent.patch_verify import verify_patch_response
from casi.agent.pipelines import (
	nudge_after_fix_pipeline,
	nudge_after_pipeline_fallback,
	run_fix_pipeline,
	run_repository_pipeline,
)
from casi.agent.response_policy import ResponsePolicy, RetryBudget
from casi.agent.state import AgentResult, PatchVerification
from casi.config import settings
from casi.llm.base import ChatMessage, LLMClient, LLMResponse
from casi.tools.registry import ToolRegistry

_MISSING_PATCH_ERROR = (
	"The agent finished without a valid unified diff. "
	"Ask CASI again to provide a ```diff patch."
)


class AgentLoop:
	"""Coordinate model decisions, intent routing, and structured tool execution."""

	def __init__(
		self,
		client: LLMClient,
		registry: ToolRegistry,
		*,
		max_steps: int = 8,
		max_correction_attempts: int | None = None,
		messages: list[ChatMessage] | None = None,
		require_tool_confirmation: Callable[[str, dict[str, object]], bool] | None = None,
		on_context_compact: ContextCompactNotifier | None = None,
		on_context_compact_prompt: ContextCompactPrompt | None = None,
		routing_mode: str | RoutingMode | None = None,
		response_policy: ResponsePolicy | None = None,
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
		if routing_mode is None:
			self.routing_mode = parse_routing_mode(settings.agent_routing_mode)
		elif isinstance(routing_mode, RoutingMode):
			self.routing_mode = routing_mode
		else:
			self.routing_mode = parse_routing_mode(routing_mode)
		self.messages = messages if messages is not None else []
		self.require_tool_confirmation = require_tool_confirmation
		self.response_policy = response_policy or ResponsePolicy()
		self.conversation = Conversation(
			self.messages,
			self.registry,
			llm_client=client,
			on_context_compact=on_context_compact,
			on_context_compact_prompt=on_context_compact_prompt,
			require_tool_confirmation=require_tool_confirmation,
		)

	def run(self, task: str) -> AgentResult:
		"""Run the agent until it returns a final response or reaches the limit."""

		if not task.strip():
			raise ValueError("task must not be empty")

		self.conversation.append("user", task.strip())
		tools = self.registry.definitions(agent_safe=True)
		continuing_after_clarification = self.conversation.consume_clarification_continuation()

		task_context = build_task_context(task.strip(), self.messages)
		intent = classify_intent(task_context)
		retries = RetryBudget()
		correction_attempts = 0
		patch_verification: PatchVerification | None = None

		if continuing_after_clarification and intent_supports_pipeline(intent):
			self._run_pipeline(intent, task_context, retries)

		if self._should_prefetch_repository(intent, task_context, continuing_after_clarification):
			self._run_pipeline(intent, task_context, retries)

		step_limit = self._step_limit_for_intent(intent)
		for step in range(1, step_limit + 1):
			self.conversation.compact_if_needed()
			response = self.client.complete(self.messages, tools)

			if response.kind == "tool_call":
				self._handle_tool_call(
					response,
					intent=intent,
					task_context=task_context,
				)
				continue

			if response.kind == "clarification":
				result = self._handle_clarification(
					response,
					task_context=task_context,
					intent=intent,
					continuing_after_clarification=continuing_after_clarification,
					step=step,
				)
				if result is not None:
					return result
				continuing_after_clarification = True
				continue

			if response.kind != "final":
				return AgentResult(
					success=False,
					error=f"Unsupported LLM response kind: {response.kind}",
					steps=step,
					messages=self.messages,
				)

			nudge = self.response_policy.evaluate_nudge(
				response.content,
				task_context=task_context,
				intent=intent,
				retries=retries,
				repository_inspected=self.conversation.repository_inspected(),
				continuing_after_clarification=continuing_after_clarification,
			)
			if nudge is not None:
				self.conversation.append_nudge(response.content, nudge.user_message)
				continue

			if self._should_fallback_to_pipeline(intent, task_context, retries):
				self._run_pipeline(intent, task_context, retries)
				continue

			patch_verification, should_retry = verify_patch_response(
				self.conversation,
				response.content,
				correction_attempts=correction_attempts,
				max_correction_attempts=self.max_correction_attempts,
			)
			if should_retry:
				correction_attempts += 1
				retries.patch_nudges = 0
				continue

			if self.response_policy.missing_required_patch(
				response.content,
				task_context,
				repository_inspected=self.conversation.repository_inspected(),
			):
				return AgentResult(
					success=False,
					error=_MISSING_PATCH_ERROR,
					steps=step,
					messages=self.messages,
					patch_verification=patch_verification,
					requested_code_change=True,
				)

			self.conversation.append("assistant", response.content)
			return AgentResult(
				success=True,
				response=response.content,
				steps=step,
				messages=self.messages,
				patch_verification=patch_verification,
				requested_code_change=task_requests_code_change(task_context),
			)

		return AgentResult(
			success=False,
			error=f"Agent reached the maximum of {step_limit} steps",
			steps=step_limit,
			messages=self.messages,
			patch_verification=patch_verification,
		)

	def _step_limit_for_intent(self, intent: TaskIntent) -> int:
		if intent is TaskIntent.FIX:
			return max(self.max_steps, settings.fix_max_steps)
		return self.max_steps

	def _should_prefetch_repository(
		self,
		intent: TaskIntent,
		task_context: str,
		continuing_after_clarification: bool,
	) -> bool:
		if self.routing_mode is RoutingMode.OFF:
			return False
		if continuing_after_clarification:
			return False
		if intent is TaskIntent.FIX:
			return False
		if not intent_supports_pipeline(intent):
			return False
		if self.conversation.missing_named_file_reads(task_context):
			return True
		if self.routing_mode is RoutingMode.STRICT:
			return True
		return bool(extract_search_targets(task_context))

	def _should_fallback_to_pipeline(
		self,
		intent: TaskIntent,
		task_context: str,
		retries: RetryBudget,
	) -> bool:
		if self.routing_mode is RoutingMode.OFF:
			return False
		if not intent_supports_pipeline(intent):
			return False
		if intent is TaskIntent.FIX:
			if not self.conversation.tool_was_used("run_tests"):
				return False
			if self.conversation.read_file_paths():
				return False
			if retries.pipeline_fallbacks >= retries.max_pipeline:
				return False
			return True
		if self.conversation.missing_named_file_reads(task_context):
			if retries.pipeline_fallbacks >= retries.max_pipeline:
				return False
			return True
		if self.conversation.repository_inspected():
			return False
		if retries.pipeline_fallbacks >= retries.max_pipeline:
			return False
		return True

	def _run_pipeline(
		self,
		intent: TaskIntent,
		task_context: str,
		retries: RetryBudget,
		*,
		test_output: str | None = None,
	) -> None:
		if intent is TaskIntent.FIX:
			if test_output is None:
				last_tests = self.conversation.last_tool_result("run_tests")
				test_output = last_tests.output if last_tests is not None else None
			run_fix_pipeline(
				task_context,
				self.conversation.execute_tool,
				repository_path=self.registry.repository_path,
				test_output=test_output,
			)
			nudge = nudge_after_fix_pipeline()
		else:
			run_repository_pipeline(
				intent,
				task_context,
				self.conversation.execute_tool,
				repository_path=self.registry.repository_path,
			)
			nudge = nudge_after_pipeline_fallback(intent)
		retries.pipeline_fallbacks += 1
		self.conversation.append("user", nudge.user_message)

	def _handle_tool_call(
		self,
		response: LLMResponse,
		*,
		intent: TaskIntent,
		task_context: str,
	) -> None:
		"""Execute a tool call, optionally redirecting redundant searches."""

		tool_name = response.tool_name or ""
		if self._should_redirect_search_to_read(intent, tool_name):
			paths = self.conversation.unread_search_code_paths()
			nudge = nudge_for_read_file_instead_of_search(
				paths,
				sources_already_read=bool(self.conversation.read_file_paths()),
			)
			self.conversation.append_nudge(
				Conversation.format_tool_call(tool_name, response.arguments),
				nudge.user_message,
			)
			return

		result = self.conversation.execute_tool(tool_name, response.arguments)
		if tool_name == "run_tests" and not result.success and intent is TaskIntent.FIX:
			self._run_fix_pipeline(task_context, test_output=result.output)

	def _run_fix_pipeline(self, task_context: str, *, test_output: str | None) -> None:
		run_fix_pipeline(
			task_context,
			self.conversation.execute_tool,
			repository_path=self.registry.repository_path,
			test_output=test_output,
		)
		self.conversation.append("user", nudge_after_fix_pipeline().user_message)

	def _should_redirect_search_to_read(self, intent: TaskIntent, tool_name: str) -> bool:
		if intent is not TaskIntent.FIX or tool_name != "search_code":
			return False
		if not self.conversation.tool_was_used("run_tests"):
			return False
		search_calls = sum(
			1
			for message in self.messages
			if message.role == "assistant"
			and message.content.startswith("Called tool=search_code")
		)
		return search_calls >= 1

	def _handle_clarification(
		self,
		response: LLMResponse,
		*,
		task_context: str,
		intent: TaskIntent,
		continuing_after_clarification: bool,
		step: int,
	) -> AgentResult | None:
		if continuing_after_clarification:
			nudge = nudge_for_repeated_clarification()
			self.conversation.append_nudge(response.content, nudge.user_message)
			return None

		if should_defer_clarification(
			task_context,
			intent,
			repository_inspected=self.conversation.repository_inspected(),
		):
			nudge = nudge_for_premature_clarification()
			self.conversation.append_nudge(response.content, nudge.user_message)
			return None

		self.conversation.mark_clarification_pending()
		self.conversation.append("assistant", response.content)
		return AgentResult(
			success=True,
			clarification=response.content,
			plan=response.plan,
			steps=step,
			messages=self.messages,
		)
