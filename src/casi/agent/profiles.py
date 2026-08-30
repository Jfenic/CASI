"""Predefined agent profiles for specialized repository tasks."""

from __future__ import annotations

from dataclasses import dataclass

from casi.agent.intent import TaskIntent


@dataclass(frozen=True)
class AgentProfile:
	"""Role, objective, and runtime limits for a specialized agent."""

	objective: TaskIntent
	name: str
	role: str
	mission: str
	prompt_instructions: str
	max_steps: int | None = None

	def display_name(self) -> str:
		"""Return a concise label for logs and interactive output."""

		return f"{self.name} ({self.role})"


def _instructions(*lines: str) -> str:
	return "\n".join(f"- {line}" for line in lines)


PROFILES: dict[TaskIntent, AgentProfile] = {
	TaskIntent.CONVERSATION: AgentProfile(
		objective=TaskIntent.CONVERSATION,
		name="conversation",
		role="Conversation Assistant",
		mission="Answer greetings and casual messages without repository tools.",
		prompt_instructions=_instructions(
			"You are the conversation specialist.",
			"Answer directly with a final JSON response.",
			"Do not call repository tools unless the user clearly shifts to a repo task.",
		),
		max_steps=2,
	),
	TaskIntent.META: AgentProfile(
		objective=TaskIntent.META,
		name="meta",
		role="CASI Meta Assistant",
		mission="Explain CASI capabilities, model, and available tools.",
		prompt_instructions=_instructions(
			"You are the meta specialist.",
			"Answer questions about CASI, the active model, and registered tools.",
			"Use a final JSON response; repository tools are usually unnecessary.",
		),
		max_steps=2,
	),
	TaskIntent.OVERVIEW: AgentProfile(
		objective=TaskIntent.OVERVIEW,
		name="overview",
		role="Repository Overview Specialist",
		mission="Explain project purpose, layout, and entry points from real files.",
		prompt_instructions=_instructions(
			"You are the overview specialist.",
			"Start with list_files, then read README.md or the most relevant docs.",
			"Summarize purpose, structure, and where to begin reading the code.",
		),
		max_steps=6,
	),
	TaskIntent.INSPECT: AgentProfile(
		objective=TaskIntent.INSPECT,
		name="inspect",
		role="Code Inspection Specialist",
		mission="Locate and explain concrete symbols, files, tests, or behavior.",
		prompt_instructions=_instructions(
			"You are the inspection specialist.",
			"Use search_code and read_file to inspect the exact target the user named.",
			"Ground every claim in tool output; cite paths and symbols you inspected.",
		),
		max_steps=8,
	),
	TaskIntent.GIT_STATUS: AgentProfile(
		objective=TaskIntent.GIT_STATUS,
		name="git_status",
		role="Git Status Specialist",
		mission="Report working-tree and staged changes accurately.",
		prompt_instructions=_instructions(
			"You are the git status specialist.",
			"Use git_diff before answering.",
			"Describe changed files and the nature of modifications.",
		),
		max_steps=4,
	),
	TaskIntent.FIX: AgentProfile(
		objective=TaskIntent.FIX,
		name="fix",
		role="Fix and Patch Specialist",
		mission="Run tests, inspect failures, and produce a valid unified diff.",
		prompt_instructions=_instructions(
			"You are the fix specialist.",
			"Call run_tests first, inspect failing files, then reply with a complete unified diff.",
			"Never claim the repository changed without including --- a/ and +++ b/ headers.",
		),
		max_steps=12,
	),
	TaskIntent.UNKNOWN: AgentProfile(
		objective=TaskIntent.UNKNOWN,
		name="general",
		role="General Repository Agent",
		mission="Inspect the repository and answer the user request with tools when needed.",
		prompt_instructions=_instructions(
			"You are the general repository agent.",
			"Prefer tools over assumptions.",
			"Keep answers concise and tied to repository evidence.",
		),
		max_steps=8,
	),
}

DEFAULT_PROFILE = PROFILES[TaskIntent.UNKNOWN]


def resolve_profile(objective: TaskIntent | str) -> AgentProfile:
	"""Return the profile for an objective name or intent enum."""

	if isinstance(objective, TaskIntent):
		return PROFILES.get(objective, DEFAULT_PROFILE)

	normalized = objective.strip().lower()
	for profile in PROFILES.values():
		if profile.name == normalized or profile.objective.value == normalized:
			return profile

	raise ValueError(
		f"Unknown agent objective {objective!r}. "
		f"Expected one of: {', '.join(profile.name for profile in PROFILES.values())}"
	)
