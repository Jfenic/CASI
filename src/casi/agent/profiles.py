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

    def with_instructions(self, extra_instructions: str) -> AgentProfile:
        """Derive a profile with additional instructions from the orchestrator."""
        if not extra_instructions.strip():
            return self
        combined = (
            f"{self.prompt_instructions}\n\n"
            f"Orchestrator plan instructions:\n{extra_instructions.strip()}"
        )
        return AgentProfile(
            objective=self.objective,
            name=self.name,
            role=self.role,
            mission=self.mission,
            prompt_instructions=combined,
            max_steps=self.max_steps,
        )

    def with_personality(
        self,
        *,
        role: str | None = None,
        mission: str | None = None,
        prompt_instructions: str | None = None,
        max_steps: int | None = None,
    ) -> AgentProfile:
        """Derive a profile with a customized personality set by the orchestrator."""
        return AgentProfile(
            objective=self.objective,
            name=self.name,
            role=role if role is not None else self.role,
            mission=mission if mission is not None else self.mission,
            prompt_instructions=prompt_instructions
            if prompt_instructions is not None
            else self.prompt_instructions,
            max_steps=max_steps if max_steps is not None else self.max_steps,
        )


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
    TaskIntent.EXPLAIN: AgentProfile(
        objective=TaskIntent.EXPLAIN,
        name="explain",
        role="Code Explanation & Architecture Specialist",
        mission=(
            "Inspect repository files and provide structured, technical explanations "
            "that aid project understanding."
        ),
        prompt_instructions=_instructions(
            "You are the code explanation and architecture specialist.",
            (
                "Use search_code and read_file to inspect the target files, "
                "functions, or modules."
            ),
            (
                "Do not call propose_file, run_tests, or apply_patch; "
                "this is a read-only explanatory task."
            ),
            "Ground every claim in real code inspected from the repository.",
            (
                "Structure your final answer clearly using the following "
                "technical markdown sections:"
            ),
            "  ### 1. Propósito General",
            (
                "  Explain what the file/component does and its role within "
                "the repository architecture."
            ),
            "  ### 2. Componentes Clave (Clases y Funciones)",
            (
                "  Break down the key classes, functions, and data structures "
                "with their responsibilities."
            ),
            "  ### 3. Dependencias e Interacciones",
            (
                "  Identify project imports, external dependencies, and how "
                "other modules interact with it."
            ),
            "  ### 4. Flujo de Datos y Ejecución",
            (
                "  Trace how data flows through the component or the invocation "
                "lifecycle."
            ),
            "  ### 5. Puntos Clave para el Proyecto",
            (
                "  Highlight critical considerations, invariants, error "
                "handling, or extension points."
            ),
            "Cite concrete paths and symbols in your explanation.",
        ),
        max_steps=8,
    ),
    TaskIntent.DIAGNOSE: AgentProfile(
        objective=TaskIntent.DIAGNOSE,
        name="diagnose",
        role="Failure Diagnosis Specialist",
        mission=(
            "Find the root cause of failing tests and report it in bounded JSON "
            "without modifying the repository."
        ),
        prompt_instructions=_instructions(
            "You are the failure diagnosis specialist.",
            "Call run_tests first, then read_file on failing source and test files.",
            ("Do not call propose_file or apply_patch; diagnosis tasks are read-only."),
            (
                "Reply with one final JSON response. Put a JSON object in content "
                "with keys file, line, cause, and evidence."
            ),
            (
                "Ground cause and evidence in code you inspected "
                "(symbol, expression, or operator). Be precise; length is fine."
            ),
            (
                "Trace the failed assertion back to the responsible implementation "
                "statement. Report the cause of the wrong value, not merely "
                "AssertionError or the test assertion. Only blame a test when its "
                "expectation contradicts the stated behavior contract."
            ),
        ),
        max_steps=10,
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
    TaskIntent.ML: AgentProfile(
        objective=TaskIntent.ML,
        name="ml",
        role="Machine Learning Fix Specialist",
        mission=(
            "Repair ML utilities (metrics, splits, preprocessing, batching, "
            "encoding) so tests pass with correct numerical behavior."
        ),
        prompt_instructions=_instructions(
            "You are the machine learning fix specialist.",
            "Call run_tests first and read failing source and test files.",
            (
                "Check metric formulas (precision/recall denominators, empty "
                "classes), data leakage in splits, seed reproducibility, "
                "sample vs population std (ddof=1), zero-variance features, "
                "batch remainder handling, and one-hot column counts."
            ),
            "Never mutate input lists or datasets; return new structures.",
            (
                "After inspection, you MUST call propose_file with the "
                "repository-relative path and complete corrected file content."
            ),
            (
                "Do not hand-write a diff when propose_file is available "
                "and never call apply_patch."
            ),
        ),
        max_steps=18,
    ),
    TaskIntent.CREATE: AgentProfile(
        objective=TaskIntent.CREATE,
        name="create",
        role="Module Creation Specialist",
        mission="Create requested source or test files satisfying the full task.",
        prompt_instructions=_instructions(
            "You are the module creation specialist.",
            (
                "Read the task requirements and tests to identify the required API. "
                "Visible tests may cover only part of the requested behavior."
            ),
            "Inspect existing target files before replacing them; create missing ones.",
            (
                "Call list_files when you have not seen the repository layout yet; "
                "choose paths that match the listing instead of assuming tests/ or "
                "src/ directories exist."
            ),
            (
                "For test-writing tasks, leave implementation unchanged and propose "
                "the requested test file. Passing existing tests does not complete "
                "a request to add tests. Cover the full behavior contract."
            ),
            (
                "Create the missing file with propose_file using the "
                "repository-relative path and complete file content."
            ),
            (
                "Implement every explicit task requirement, including validation "
                "and edge cases absent from visible tests. Keep the solution minimal."
            ),
            (
                "Do not hand-write a diff when propose_file is available "
                "and never call apply_patch."
            ),
        ),
        max_steps=18,
    ),
    TaskIntent.TEST_ENGINEER: AgentProfile(
        objective=TaskIntent.TEST_ENGINEER,
        name="test_engineer",
        role="Test Engineering & QA Specialist",
        mission=(
            "Design and write comprehensive unit and integration tests covering "
            "edge cases and regressions without modifying production code."
        ),
        prompt_instructions=_instructions(
            "You are the test engineering and QA specialist.",
            (
                "Inspect existing tests and target implementation files with "
                "read_file and search_code."
            ),
            "Call run_tests to verify existing test status before proposing new tests.",
            (
                "Propose test files using propose_file, strictly targeted to test "
                "directories (such as tests/)."
            ),
            "Do not modify production code in src/ or the main package.",
            (
                "Write deterministic assertions covering boundary conditions, "
                "type contracts, and exception handling."
            ),
            (
                "Do not hand-write a diff when propose_file is available "
                "and never call apply_patch."
            ),
        ),
        max_steps=14,
    ),
    TaskIntent.REFACTOR: AgentProfile(
        objective=TaskIntent.REFACTOR,
        name="refactor",
        role="Refactoring & Code Quality Specialist",
        mission=(
            "Improve code structure, modularity, readability, and typing while "
            "strictly preserving external behavior and passing all existing tests."
        ),
        prompt_instructions=_instructions(
            "You are the refactoring specialist.",
            (
                "Call run_tests first to verify that all existing tests pass "
                "before refactoring."
            ),
            (
                "Inspect the code to identify duplication, high cyclomatic "
                "complexity, or naming issues."
            ),
            (
                "Apply focused refactorings with propose_file, keeping changes "
                "minimal and disciplined."
            ),
            (
                "Behavior invariant: all existing tests must continue to pass "
                "100% after the refactoring."
            ),
            "Never weaken existing tests to accommodate refactored code.",
        ),
        max_steps=14,
    ),
    TaskIntent.SECURITY: AgentProfile(
        objective=TaskIntent.SECURITY,
        name="security",
        role="Security & Defensive Audit Specialist",
        mission=(
            "Audit repository code for vulnerabilities, injection risks, secret leaks, "
            "and insecure defaults without modifying the repository."
        ),
        prompt_instructions=_instructions(
            "You are the security and defensive audit specialist.",
            (
                "Use search_code, read_file, and list_files to audit code "
                "paths and configurations."
            ),
            (
                "Do not call propose_file or apply_patch; security audits are "
                "strictly read-only."
            ),
            (
                "Look for input validation gaps, path traversal, shell injection, "
                "hardcoded secrets, and unsafe deserialization."
            ),
            (
                "Report findings with: Vulnerability description, Affected file "
                "& line, Risk severity, and Recommended defensive mitigation."
            ),
        ),
        max_steps=8,
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
