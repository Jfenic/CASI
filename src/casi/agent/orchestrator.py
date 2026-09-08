"""Execute multi-agent plans with tier-based user approval."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from casi.agent.conversation import ContextCompactNotifier, ContextCompactPrompt
from casi.agent.factory import AgentFactory, SpecializedAgent, ToolConfirmation
from casi.agent.intent import RoutingMode, TaskIntent
from casi.agent.permissions import (
	tier_label,
	tier_requires_approval,
	tool_covered_by_approved_tier,
)
from casi.agent.planner import AgentPlan, AgentPlanStep, PlanSegment, TaskPlanner
from casi.agent.response_policy import ResponsePolicy
from casi.agent.state import AgentResult, PatchVerification
from casi.agent.trace import AgentTraceRecorder
from casi.llm.base import ChatMessage
from casi.tools.registry import ToolRegistry

SegmentApproval = Callable[[PlanSegment], bool]
StepStartNotifier = Callable[[AgentPlanStep, int, int], None]
ActivityNotifier = Callable[[str], None]


@dataclass(frozen=True)
class AgentStepResult:
	"""Outcome for one executed plan step."""

	step: AgentPlanStep
	result: AgentResult


@dataclass
class PendingOrchestration:
	"""Resume a plan after clarification or partial execution."""

	plan: AgentPlan
	segment_index: int
	step_index: int
	step_results: list[AgentStepResult] = field(default_factory=list)
	agent: SpecializedAgent | None = None


@dataclass
class OrchestratorResult:
	"""Combined outcome for a full or partial orchestrated request."""

	success: bool
	response: str = ""
	error: str | None = None
	clarification: str | None = None
	plan: list[str] = field(default_factory=list)
	patch_verification: PatchVerification | None = None
	requested_code_change: bool = False
	cancelled: bool = False
	executed_plan: AgentPlan | None = None
	step_results: list[AgentStepResult] = field(default_factory=list)
	pending: PendingOrchestration | None = None
	trace: list[str] = field(default_factory=list)


class AgentOrchestrator:
	"""Plan, approve, and run specialized agents for one user request."""

	def __init__(
		self,
		client: LLMClient,
		repository: str | Path,
		*,
		session_messages: list[ChatMessage] | None = None,
		max_steps: int | None = None,
		max_correction_attempts: int | None = None,
		routing_mode: str | RoutingMode | None = None,
		require_tool_confirmation: ToolConfirmation | None = None,
		approve_segment: SegmentApproval | None = None,
		on_context_compact: ContextCompactNotifier | None = None,
		on_context_compact_prompt: ContextCompactPrompt | None = None,
		on_plan: Callable[[AgentPlan], None] | None = None,
		on_step_start: StepStartNotifier | None = None,
		on_activity: ActivityNotifier | None = None,
		trace: AgentTraceRecorder | None = None,
		response_policy: ResponsePolicy | None = None,
		registry: ToolRegistry | None = None,
	) -> None:
		self.client = client
		self.repository = repository
		self.session_messages = session_messages if session_messages is not None else []
		self.max_steps = max_steps
		self.max_correction_attempts = max_correction_attempts
		self.routing_mode = routing_mode
		self.require_tool_confirmation = require_tool_confirmation
		self.approve_segment = approve_segment
		self.on_context_compact = on_context_compact
		self.on_context_compact_prompt = on_context_compact_prompt
		self.on_plan = on_plan
		self.on_step_start = on_step_start
		self.on_activity = on_activity
		self.trace = trace
		self.response_policy = response_policy
		self.registry = registry

	def run(
		self,
		task: str,
		*,
		pending: PendingOrchestration | None = None,
	) -> OrchestratorResult:
		if pending is not None:
			return self._continue_pending(task, pending)

		if self.trace is not None:
			self.trace.clear()
			self.trace.set_context(
				repository=str(self.repository),
				task=task.strip(),
				model=getattr(self.client, "model", None)
				if isinstance(getattr(self.client, "model", None), str)
				else None,
			)
			self.trace.mark_started()

		plan = TaskPlanner.create_plan(task, self.session_messages)
		if plan.step_count() == 0:
			return OrchestratorResult(success=False, error="Task must not be empty")
		if self.on_plan is not None:
			self.on_plan(plan)
		return self._execute_plan(plan, start_segment=0, start_step=0, prior_results=[])

	def _continue_pending(self, answer: str, pending: PendingOrchestration) -> OrchestratorResult:
		segment = pending.plan.segments[pending.segment_index]
		step = segment.steps[pending.step_index]

		if step.objective is TaskIntent.PRESENT and pending.step_index > 0:
			worker_index = pending.step_index - 1
			worker_step = segment.steps[worker_index]
			worker_agent = self._create_agent(worker_step.objective, segment)
			merged_task = (
				f"{worker_step.task}\n\n"
				f"Additional user context: {answer.strip()}"
			)
			result = worker_agent.run(merged_task)
			if result.clarification is not None:
				worker_pending = PendingOrchestration(
					plan=pending.plan,
					segment_index=pending.segment_index,
					step_index=worker_index,
					step_results=pending.step_results,
					agent=worker_agent,
				)
				return OrchestratorResult(
					success=True,
					clarification=result.clarification,
					plan=result.plan,
					step_results=pending.step_results,
					executed_plan=pending.plan,
					pending=worker_pending,
				)
			if not result.success:
				failed_results = [
					*pending.step_results,
					AgentStepResult(step=worker_step, result=result),
				]
				return OrchestratorResult(
					success=False,
					error=result.error,
					step_results=failed_results,
					executed_plan=pending.plan,
					trace=_collect_trace(failed_results),
				)
			step_results = [
				*pending.step_results,
				AgentStepResult(step=worker_step, result=result),
			]
			return self._execute_plan(
				pending.plan,
				start_segment=pending.segment_index,
				start_step=pending.step_index,
				prior_results=step_results,
			)

		agent = pending.agent or self._create_agent(step.objective, segment)
		pending.agent = agent
		result = agent.run(answer.strip())

		if result.clarification is not None:
			return OrchestratorResult(
				success=True,
				clarification=result.clarification,
				plan=result.plan,
				step_results=pending.step_results,
				executed_plan=pending.plan,
				pending=pending,
			)

		if not result.success:
			failed_results = [*pending.step_results, AgentStepResult(step=step, result=result)]
			return OrchestratorResult(
				success=False,
				error=result.error,
				step_results=failed_results,
				executed_plan=pending.plan,
				trace=_collect_trace(failed_results),
			)

		step_results = [*pending.step_results, AgentStepResult(step=step, result=result)]
		next_step = pending.step_index + 1
		next_segment = pending.segment_index
		if next_step >= len(segment.steps):
			next_segment += 1
			next_step = 0
		return self._execute_plan(
			pending.plan,
			start_segment=next_segment,
			start_step=next_step,
			prior_results=step_results,
		)

	def _execute_plan(
		self,
		plan: AgentPlan,
		*,
		start_segment: int,
		start_step: int,
		prior_results: list[AgentStepResult],
	) -> OrchestratorResult:
		step_results = list(prior_results)
		total_steps = plan.step_count()
		step_number = len(step_results)

		for segment_index in range(start_segment, len(plan.segments)):
			segment = plan.segments[segment_index]
			first_step = start_step if segment_index == start_segment else 0
			if first_step == 0 and not self._segment_allowed(segment):
				return OrchestratorResult(
					success=False,
					cancelled=True,
					error="Execution cancelled by the user.",
					executed_plan=plan,
					step_results=step_results,
					plan=plan.summary_lines(),
				)
			for step_index in range(first_step, len(segment.steps)):
				step = segment.steps[step_index]
				step_number += 1
				if self.on_step_start is not None:
					self.on_step_start(step, step_number, total_steps)
				step_task = self._build_step_task(step, step_results)
				agent = self._create_agent(step.objective, segment)
				pending = PendingOrchestration(
					plan=plan,
					segment_index=segment_index,
					step_index=step_index,
					step_results=step_results,
					agent=agent,
				)
				result = agent.run(step_task)

				if result.clarification is not None:
					return OrchestratorResult(
						success=True,
						clarification=result.clarification,
						plan=result.plan or plan.summary_lines(),
						step_results=step_results,
						executed_plan=plan,
						pending=pending,
					)

				if not result.success:
					failed_results = [
						*step_results,
						AgentStepResult(step=step, result=result),
					]
					return OrchestratorResult(
						success=False,
						error=result.error,
						step_results=failed_results,
						executed_plan=plan,
						plan=plan.summary_lines(),
						trace=_collect_trace(failed_results),
					)

				step_results.append(AgentStepResult(step=step, result=result))
				if (
					step.objective is TaskIntent.PRESENT
					and result.success
					and result.response.strip()
				):
					_replace_last_assistant_message(
						self.session_messages,
						result.response.strip(),
					)

			start_step = 0

		last = step_results[-1].result if step_results else None
		return OrchestratorResult(
			success=True,
			response=last.response if last is not None else "",
			patch_verification=last.patch_verification if last is not None else None,
			requested_code_change=any(
				item.result.requested_code_change for item in step_results
			),
			executed_plan=plan,
			step_results=step_results,
			plan=plan.summary_lines(),
			trace=_collect_trace(step_results),
		)

	def _segment_allowed(self, segment: PlanSegment) -> bool:
		if not tier_requires_approval(segment.tier):
			return True
		if self.approve_segment is None:
			return False
		return self.approve_segment(segment)

	def _create_agent(
		self,
		objective: TaskIntent | str,
		segment: PlanSegment,
	) -> SpecializedAgent:
		return AgentFactory.create(
			objective,
			client=self.client,
			repository=self.repository,
			max_steps=self.max_steps,
			max_correction_attempts=self.max_correction_attempts,
			session_messages=self.session_messages,
			require_tool_confirmation=self._confirmation_for_segment(segment),
			on_context_compact=self.on_context_compact,
			on_context_compact_prompt=self.on_context_compact_prompt,
			on_activity=self.on_activity,
			trace=self.trace,
			routing_mode=self.routing_mode,
			response_policy=self.response_policy,
			registry=self.registry,
		)

	def _confirmation_for_segment(self, segment: PlanSegment) -> ToolConfirmation | None:
		callback = self.require_tool_confirmation
		if callback is None:
			return None
		if not tier_requires_approval(segment.tier):
			return callback

		def confirm(tool_name: str, arguments: dict[str, object]) -> bool:
			if tool_covered_by_approved_tier(tool_name, segment.tier):
				return True
			return callback(tool_name, arguments)

		return confirm

	@staticmethod
	def _build_step_task(step: AgentPlanStep, prior_results: list[AgentStepResult]) -> str:
		if not prior_results:
			return step.task
		summary = prior_results[-1].result.response.strip()
		if not summary:
			return step.task
		compact = summary if len(summary) <= 800 else f"{summary[:797]}..."
		return (
			f"{step.task}\n\n"
			f"Context from previous agent ({prior_results[-1].step.agent_name}):\n"
			f"{compact}"
		)


def _collect_trace(step_results: list[AgentStepResult]) -> list[str]:
	lines: list[str] = []
	for item in step_results:
		if not item.result.trace:
			continue
		lines.append(f"[{item.step.agent_name}]")
		lines.extend(f"  {event}" for event in item.result.trace)
	return lines


def format_segment_approval_prompt(segment: PlanSegment) -> str:
	"""Build a concise approval question for a non-read plan phase."""

	agents = ", ".join(f"{step.agent_name} ({step.agent_role})" for step in segment.steps)
	goals = "; ".join(step.tools_goal for step in segment.steps)
	return (
		f"Fase de {tier_label(segment.tier)}: {agents}. "
		f"Herramientas/objetivo: {goals}. ¿Continuar? [y/N]"
	)


def _replace_last_assistant_message(
	session_messages: list[ChatMessage],
	content: str,
) -> None:
	for index in range(len(session_messages) - 1, -1, -1):
		if session_messages[index].role == "assistant":
			session_messages[index] = ChatMessage(role="assistant", content=content)
			return
