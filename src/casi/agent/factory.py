"""Factory for specialized, task-scoped agent instances."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from casi.agent.conversation import ContextCompactNotifier, ContextCompactPrompt
from casi.agent.intent import RoutingMode, TaskIntent, build_task_context, classify_intent
from casi.agent.loop import AgentLoop
from casi.agent.profiles import AgentProfile, resolve_profile
from casi.agent.response_policy import ResponsePolicy
from casi.agent.state import AgentResult
from casi.llm.base import ChatMessage, LLMClient
from casi.llm.ollama_client import OllamaClient
from casi.tools.registry import ToolRegistry

ToolConfirmation = Callable[[str, dict[str, object]], bool]


@dataclass(frozen=True)
class SpecializedAgent:
	"""Configured agent for one objective with an isolated task context per run."""

	profile: AgentProfile
	loop: AgentLoop

	def run(self, task: str) -> AgentResult:
		"""Execute one task with the profile's role and isolated working memory."""

		return self.loop.run(task)

	@property
	def session_messages(self) -> list[ChatMessage]:
		"""Return the lightweight session thread shared across tasks."""

		return self.loop.messages


def _client_for_profile(client: LLMClient, profile: AgentProfile) -> LLMClient:
	if not profile.prompt_instructions.strip():
		return client
	if isinstance(client, OllamaClient):
		return OllamaClient(
			base_url=client.base_url,
			model=client.model,
			timeout_seconds=client.timeout_seconds,
			role_instructions=profile.prompt_instructions,
		)
	return client


class AgentFactory:
	"""Create specialized agents with clear objectives and isolated task scope."""

	@staticmethod
	def create(
		objective: TaskIntent | str,
		*,
		client: LLMClient,
		repository: str | Path,
		max_steps: int | None = None,
		max_correction_attempts: int | None = None,
		session_messages: list[ChatMessage] | None = None,
		require_tool_confirmation: ToolConfirmation | None = None,
		on_context_compact: ContextCompactNotifier | None = None,
		on_context_compact_prompt: ContextCompactPrompt | None = None,
		routing_mode: str | RoutingMode | None = None,
		response_policy: ResponsePolicy | None = None,
	) -> SpecializedAgent:
		"""Instantiate an agent for a known objective."""

		profile = resolve_profile(objective)
		profiled_client = _client_for_profile(client, profile)
		registry = ToolRegistry(repository)
		loop = AgentLoop(
			profiled_client,
			registry,
			profile=profile,
			max_steps=max_steps if max_steps is not None else (profile.max_steps or 8),
			max_correction_attempts=max_correction_attempts,
			messages=session_messages if session_messages is not None else [],
			require_tool_confirmation=require_tool_confirmation,
			on_context_compact=on_context_compact,
			on_context_compact_prompt=on_context_compact_prompt,
			routing_mode=routing_mode,
			response_policy=response_policy,
		)
		return SpecializedAgent(profile=profile, loop=loop)

	@staticmethod
	def for_task(
		task: str,
		*,
		client: LLMClient,
		repository: str | Path,
		max_steps: int | None = None,
		max_correction_attempts: int | None = None,
		session_messages: list[ChatMessage] | None = None,
		require_tool_confirmation: ToolConfirmation | None = None,
		on_context_compact: ContextCompactNotifier | None = None,
		on_context_compact_prompt: ContextCompactPrompt | None = None,
		routing_mode: str | RoutingMode | None = None,
		response_policy: ResponsePolicy | None = None,
	) -> SpecializedAgent:
		"""Classify the task and return the matching specialized agent."""

		session = session_messages if session_messages is not None else []
		context = build_task_context(task.strip(), session)
		intent = classify_intent(context)
		return AgentFactory.create(
			intent,
			client=client,
			repository=repository,
			max_steps=max_steps,
			max_correction_attempts=max_correction_attempts,
			session_messages=session,
			require_tool_confirmation=require_tool_confirmation,
			on_context_compact=on_context_compact,
			on_context_compact_prompt=on_context_compact_prompt,
			routing_mode=routing_mode,
			response_policy=response_policy,
		)
