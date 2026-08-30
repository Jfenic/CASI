"""Build multi-agent execution plans from user requests."""

from __future__ import annotations

import re
from dataclasses import dataclass

from casi.agent.intent import (
	TaskIntent,
	build_task_context,
	classify_intent,
	task_requests_code_change,
	task_requests_test_execution,
)
from casi.agent.permissions import PermissionTier, resolve_permission_tier
from casi.agent.profiles import resolve_profile
from casi.llm.base import ChatMessage

_COMPOUND_SPLIT = re.compile(
	r"\s+(?:,\s*)?(?:y luego|después|despues|and then|then|y después|y despues)\s+",
	re.IGNORECASE,
)

_READ_THEN_EXECUTE = re.compile(
	r"\b(?:revisa|review|explica|explain|inspect|analiza|analyze|mira|lee|read)\b",
	re.IGNORECASE,
)


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
	def from_task(cls, task: str, *, session_messages: list[ChatMessage]) -> AgentPlanStep:
		context = build_task_context(task.strip(), session_messages)
		intent = classify_intent(context)
		profile = resolve_profile(intent)
		tier = resolve_permission_tier(task, intent)
		return cls(
			objective=intent,
			task=task.strip(),
			tier=tier,
			agent_name=profile.name,
			agent_role=profile.role,
			tools_goal=_tools_goal(intent, tier),
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


def _tools_goal(intent: TaskIntent, tier: PermissionTier) -> str:
	if tier is PermissionTier.MUTATE:
		return "run_tests, read_file, propose unified diff"
	if tier is PermissionTier.EXECUTE:
		return "run_tests"
	if intent is TaskIntent.GIT_STATUS:
		return "git_diff"
	if intent in {TaskIntent.OVERVIEW, TaskIntent.INSPECT}:
		return "list_files, search_code, read_file"
	if intent in {TaskIntent.CONVERSATION, TaskIntent.META}:
		return "direct answer"
	return "repository tools as needed"


def decompose_task(task: str) -> list[str]:
	"""Split compound requests into independent subtasks when appropriate."""

	stripped = task.strip()
	if not stripped:
		return []

	if task_requests_code_change(stripped):
		return [stripped]

	parts = [part.strip() for part in _COMPOUND_SPLIT.split(stripped) if part.strip()]
	if len(parts) > 1:
		return parts

	if task_requests_test_execution(stripped) and _READ_THEN_EXECUTE.search(stripped):
		for separator in (" y ", " and ", ", "):
			if separator in stripped.lower():
				left, _, right = stripped.lower().partition(separator.strip())
				if _READ_THEN_EXECUTE.search(left) and task_requests_test_execution(right):
					origin_left, _, origin_right = stripped.partition(separator)
					if origin_left.strip() and origin_right.strip():
						return [origin_left.strip(), origin_right.strip()]

	return [stripped]


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
	) -> AgentPlan:
		session = session_messages if session_messages is not None else []
		subtasks = decompose_task(task)
		steps = [
			AgentPlanStep.from_task(subtask, session_messages=session)
			for subtask in subtasks
		]
		return AgentPlan(
			original_task=task.strip(),
			segments=tuple(group_segments(steps)),
		)
