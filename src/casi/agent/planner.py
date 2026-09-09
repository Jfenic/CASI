"""Build multi-agent execution plans from user requests."""

from __future__ import annotations

from dataclasses import dataclass

from casi.agent.intent import TaskIntent, build_task_context, is_fast_path_intent, resolve_task_intent
from casi.agent.permissions import PermissionTier
from casi.agent.profiles import resolve_profile
from casi.llm.base import ChatMessage

_FAST_PATH_TOOLS_GOAL = {
	TaskIntent.CONVERSATION: "direct answer",
	TaskIntent.META: "direct answer",
	TaskIntent.RECALL_PLAN: "get_session_plan",
	TaskIntent.GIT_STATUS: "git_diff",
}


@dataclass(frozen=True)
class AgentPlanStep:
	"""One specialized agent invocation within a plan."""

	objective: TaskIntent
	task: str
	tier: PermissionTier
	agent_name: str
	agent_role: str
	tools_goal: str

	@classmethod
	def from_intent(
		cls,
		task: str,
		intent: TaskIntent,
	) -> AgentPlanStep:
		profile = resolve_profile(intent)
		return cls(
			objective=intent,
			task=task.strip(),
			tier=PermissionTier.READ,
			agent_name=profile.name,
			agent_role=profile.role,
			tools_goal=_FAST_PATH_TOOLS_GOAL.get(intent, "repository tools as needed"),
		)


@dataclass(frozen=True)
class PlanSegment:
	"""Consecutive plan steps that share the same approval tier."""

	tier: PermissionTier
	steps: tuple[AgentPlanStep, ...]


@dataclass(frozen=True)
class AgentPlan:
	"""Ordered list of agents ready to execute for one user request."""

	original_task: str
	segments: tuple[PlanSegment, ...]

	def step_count(self) -> int:
		return sum(len(segment.steps) for segment in self.segments)

	def summary_lines(self) -> list[str]:
		lines: list[str] = []
		index = 1
		for segment in self.segments:
			for step in segment.steps:
				lines.append(
					f"{index}. [{step.agent_name}|{step.tier.value}] "
					f"{step.task} — {step.tools_goal}"
				)
				index += 1
		return lines


def decompose_task(task: str) -> list[str]:
	"""Return one task per plan; compound work is handled inside the general agent."""

	stripped = task.strip()
	return [stripped] if stripped else []


def group_segments(steps: list[AgentPlanStep]) -> list[PlanSegment]:
	"""Group consecutive steps that share the same permission tier."""

	if not steps:
		return []

	segments: list[PlanSegment] = []
	current_tier = steps[0].tier
	current_steps: list[AgentPlanStep] = [steps[0]]
	for step in steps[1:]:
		if step.tier is current_tier:
			current_steps.append(step)
			continue
		segments.append(PlanSegment(tier=current_tier, steps=tuple(current_steps)))
		current_tier = step.tier
		current_steps = [step]
	segments.append(PlanSegment(tier=current_tier, steps=tuple(current_steps)))
	return segments


class TaskPlanner:
	"""Analyze a request and produce a dynamic multi-agent execution plan."""

	@staticmethod
	def create_plan(
		task: str,
		session_messages: list[ChatMessage] | None = None,
		*,
		category: str | None = None,
	) -> AgentPlan:
		session = session_messages if session_messages is not None else []
		stripped = task.strip()
		if not stripped:
			return AgentPlan(original_task="", segments=())

		context = build_task_context(stripped, session)
		intent = resolve_task_intent(context, category=category)
		if is_fast_path_intent(intent):
			steps = [AgentPlanStep.from_intent(stripped, intent)]
		else:
			steps = [AgentPlanStep.from_intent(stripped, intent)]

		return AgentPlan(
			original_task=stripped,
			segments=tuple(group_segments(steps)),
		)
