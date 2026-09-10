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
            (
                "Do not call repository tools unless the user clearly "
                "shifts to a repo task."
            ),
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
            "Call run_tests first and inspect failing files.",
            (
                "After files are loaded, you MUST call propose_file with "
                "the path and complete corrected file content."
            ),
            (
                "Do not hand-write a diff when propose_file is available "
                "and never call apply_patch."
            ),
        ),
        max_steps=12,
    ),
    TaskIntent.CREATE: AgentProfile(
        objective=TaskIntent.CREATE,
        name="create",
        role="Module Creation Specialist",
        mission="Create missing local modules that satisfy the repository tests.",
        prompt_instructions=_instructions(
            "You are the module creation specialist.",
            (
                "The tests define the required API; read them first and "
                "treat them as the specification."
            ),
            "The target module or file does not exist yet, so do not search for it.",
            (
                "Create the missing file with propose_file using the "
                "repository-relative path and complete file content."
            ),
            (
                "Implement only the behavior required by the tests; keep "
                "the solution minimal."
            ),
            (
                "Do not hand-write a diff when propose_file is available "
                "and never call apply_patch."
            ),
        ),
        max_steps=18,
    ),
    TaskIntent.RECALL_PLAN: AgentProfile(
        objective=TaskIntent.RECALL_PLAN,
        name="recall_plan",
        role="Session Plan Assistant",
        mission="Explain the stored CASI plan for the current session.",
        prompt_instructions=_instructions(
            "You are the session plan specialist.",
            (
                "When the user asks for the plan, next steps, or what "
                "CASI will do, call get_session_plan first."
            ),
            (
                "Answer from get_session_plan output only; do not read "
                "README.md or search the repository for a plan."
            ),
            "If no plan is stored, say so clearly and suggest starting a task first.",
            "Use a final JSON response after you have the tool result.",
        ),
        max_steps=3,
    ),
    TaskIntent.PRESENT: AgentProfile(
        objective=TaskIntent.PRESENT,
        name="presenter",
        role="Output Formatting Specialist",
        mission=(
            "Turn raw specialist answers into clear, structured markdown for the user."
        ),
        prompt_instructions=_instructions(
            "You are the presenter specialist.",
            (
                "You receive another agent's draft answer in the "
                "conversation; do not call repository tools."
            ),
            (
                "Rewrite it as polished markdown: a short title, "
                "sections, bullet lists, and `path` references."
            ),
            (
                "Preserve every factual claim from the draft; do not "
                "invent files, symbols, or behavior."
            ),
            "Use the user's language. Reply with one final JSON response only.",
            (
                "Suggested sections when relevant: Resumen, Estructura, "
                "Puntos clave, Archivos relevantes, Próximos pasos."
            ),
        ),
        max_steps=2,
    ),
    TaskIntent.UNKNOWN: AgentProfile(
        objective=TaskIntent.UNKNOWN,
        name="general",
        role="General Repository Agent",
        mission=(
            "Inspect the repository and complete the user request "
            "with tools when needed."
        ),
        prompt_instructions=_instructions(
            "You are the general repository agent.",
            "Prefer tools over assumptions and act on reasonably clear requests.",
            "Use list_files, search_code, and read_file to inspect before answering.",
            (
                "When the user asks to add or change code or tests, "
                "inspect first, then call run_tests if verification is "
                "needed."
            ),
            (
                "When files must change, call propose_file with the "
                "repository-relative path and complete file content."
            ),
            (
                "Do not ask the user for source code, file paths, or "
                "test output you can read with tools."
            ),
            "Keep answers concise and tied to repository evidence.",
        ),
        max_steps=12,
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
