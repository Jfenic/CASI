"""LLM-backed task evaluation and agent personality assignment."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from casi.agent.intent import TaskIntent, resolve_task_intent
from casi.agent.profiles import AgentProfile, resolve_profile
from casi.llm.base import ChatMessage, LLMClient

logger = logging.getLogger(__name__)

EVALUATOR_SYSTEM_PROMPT = """You are the CASI Orchestrator Evaluator.
Analyze the user request and repository context, and assign the task to
the most appropriate specialized agent from this CLOSED CATALOG:

1. 'explain' (Code Explanation & Architecture Specialist):
   - For explaining repository files, code structure, architecture, modules, or flows.
   - Strictly read-only.
   - Enforces a 5-section technical explanation:
     ### 1. Propósito General
     ### 2. Componentes Clave (Clases y Funciones)
     ### 3. Dependencias e Interacciones
     ### 4. Flujo de Datos y Ejecución
     ### 5. Puntos Clave para el Proyecto

2. 'diagnose' (Root Cause Diagnosis Specialist):
   - For analyzing failing tests, bugs, or unexpected runtime behavior.
   - Strictly read-only / test execution. Never proposes patches.
   - Identifies the root cause statement and provides evidence in JSON.

3. 'fix' (Bug Fix & Patch Specialist):
   - For repairing code bugs, satisfying failing tests, and generating unified diffs.

4. 'test_engineer' (Test Engineering & QA Specialist):
   - For writing new unit/integration tests without modifying production code.

5. 'refactor' (Refactoring & Code Quality Specialist):
   - For refactoring code modularity/typing while keeping all existing tests passing.

6. 'security' (Security & Defensive Audit Specialist):
   - For auditing security risks, secret leaks, and traversal vulnerabilities.

7. 'overview' (Repository Overview Specialist):
   - For general repository onboarding, README explanation, and project entry points.

8. 'conversation' (Conversation Assistant):
   - For greetings and casual messages that do not require inspecting the repository.

Return ONLY a valid JSON object with these exact keys:
{
  "objective": "explain" | "diagnose" | "fix" | "test_engineer" |
               "refactor" | "security" | "overview" | "conversation",
  "agent_role": "concise role description",
  "tools_needed": ["read_file", "search_code"],
  "plan_instructions": "Step-by-step instructions for the agent to resolve the task.",
  "reasoning": "Brief explanation of why this agent was selected."
}
"""


@dataclass(frozen=True)
class TaskEvaluation:
    """Outcome of an LLM task evaluation."""

    objective: TaskIntent
    agent_name: str
    agent_role: str
    tools_needed: list[str] = field(default_factory=list)
    plan_instructions: str = ""
    reasoning: str = ""


def default_tools_for_intent(intent: TaskIntent) -> list[str]:
    """Return standard tools for a given intent."""

    if intent in {TaskIntent.EXPLAIN, TaskIntent.SECURITY, TaskIntent.OVERVIEW}:
        return ["read_file", "search_code", "list_files"]
    if intent is TaskIntent.DIAGNOSE:
        return ["run_tests", "read_file", "search_code"]
    if intent in {
        TaskIntent.FIX,
        TaskIntent.CREATE,
        TaskIntent.TEST_ENGINEER,
        TaskIntent.REFACTOR,
        TaskIntent.ML,
    }:
        return ["read_file", "search_code", "run_tests", "propose_file"]
    if intent is TaskIntent.GIT_STATUS:
        return ["git_diff"]
    return ["read_file", "search_code", "list_files"]


def _extract_json_payload(text: str) -> dict[str, Any]:
    """Extract a dictionary from JSON or markdown fenced blocks."""

    stripped = text.strip()
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    if match:
        data = json.loads(match.group(1))
        if isinstance(data, dict):
            return data

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        data = json.loads(stripped[start : end + 1])
        if isinstance(data, dict):
            return data

    raise ValueError(f"Could not extract JSON from text: {text[:100]}")


class LLMTaskEvaluator:
    """Evaluate user requests using LLM to pick specialized agent and plan."""

    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def _can_evaluate_with_llm(self) -> bool:
        from casi.llm.ollama_client import OllamaClient

        return isinstance(self.client, OllamaClient) or bool(
            getattr(self.client, "is_evaluator", False)
            or getattr(self.client, "supports_evaluation", False)
        )

    def evaluate(
        self,
        task: str,
        session_messages: list[ChatMessage] | None = None,
        *,
        category: str | None = None,
    ) -> TaskEvaluation:
        """Evaluate a task using the LLM, with deterministic fallback if needed."""

        # 1. If explicit category is provided, honor it directly
        if category:
            intent = resolve_task_intent(task, category=category)
            profile = resolve_profile(intent)
            return self._build_evaluation_from_profile(intent, profile, task)

        # 2. Try LLM evaluation if client supports it
        if self._can_evaluate_with_llm():
            try:
                return self._evaluate_with_llm(task, session_messages)
            except Exception as exc:
                logger.debug(
                    "LLM evaluation failed, falling back to base classification: %s",
                    exc,
                )

        fallback_intent = resolve_task_intent(task, category=category)
        fallback_profile = resolve_profile(fallback_intent)
        return self._build_evaluation_from_profile(
            fallback_intent, fallback_profile, task
        )

    def _evaluate_with_llm(
        self,
        task: str,
        session_messages: list[ChatMessage] | None,
    ) -> TaskEvaluation:
        messages = [
            ChatMessage(role="system", content=EVALUATOR_SYSTEM_PROMPT),
        ]
        if session_messages:
            for msg in session_messages[-3:]:
                messages.append(msg)
        messages.append(
            ChatMessage(
                role="user",
                content=f"Evaluate this user request:\n\n{task.strip()}",
            )
        )
        response = self.client.complete(messages, tools=[])
        raw_text = response.content.strip()
        if not raw_text:
            raise ValueError("Empty evaluator response")

        payload = _extract_json_payload(raw_text)
        raw_objective = payload.get("objective", "").strip().lower()
        if not raw_objective:
            raise ValueError("No objective in evaluator payload")

        # Map to TaskIntent
        intent: TaskIntent = TaskIntent.UNKNOWN
        for candidate in TaskIntent:
            if candidate.value == raw_objective:
                intent = candidate
                break

        profile = resolve_profile(intent)
        role = payload.get("agent_role") or profile.role
        instructions = payload.get("plan_instructions") or ""
        tools = payload.get("tools_needed") or default_tools_for_intent(intent)
        reasoning = payload.get("reasoning") or ""

        return TaskEvaluation(
            objective=intent,
            agent_name=profile.name,
            agent_role=role,
            tools_needed=tools,
            plan_instructions=instructions,
            reasoning=reasoning,
        )

    def _build_evaluation_from_profile(
        self,
        intent: TaskIntent,
        profile: AgentProfile,
        task: str,
    ) -> TaskEvaluation:
        instructions = ""
        if intent is TaskIntent.EXPLAIN:
            instructions = (
                "1. Locate and read the target files or symbols with search_code "
                "and read_file.\n"
                "2. Identify the key components, functions, classes, and imported "
                "dependencies.\n"
                "3. Synthesize your final explanation under the 5 technical sections:\n"
                "   1. Propósito General\n"
                "   2. Componentes Clave (Clases y Funciones)\n"
                "   3. Dependencias e Interacciones\n"
                "   4. Flujo de Datos y Ejecución\n"
                "   5. Puntos Clave para el Proyecto."
            )
        elif intent is TaskIntent.DIAGNOSE:
            instructions = (
                "1. Run tests to reproduce the failure.\n"
                "2. Trace the failure traceback to the implementation statements.\n"
                "3. Report root cause with file, line, cause, and evidence in JSON."
            )
        elif intent is TaskIntent.TEST_ENGINEER:
            instructions = (
                "1. Inspect existing tests and target implementation.\n"
                "2. Run existing tests to ensure baseline passes.\n"
                "3. Propose comprehensive deterministic tests without modifying "
                "production code."
            )
        elif intent is TaskIntent.REFACTOR:
            instructions = (
                "1. Run tests to establish baseline.\n"
                "2. Apply clean refactoring with propose_file.\n"
                "3. Ensure all tests pass with zero behavior alteration."
            )
        elif intent is TaskIntent.SECURITY:
            instructions = (
                "1. Audit target code for input validation, sanitization, and "
                "secret leaks.\n"
                "2. Detail vulnerabilities, risk severity, and defensive mitigations."
            )

        return TaskEvaluation(
            objective=intent,
            agent_name=profile.name,
            agent_role=profile.role,
            tools_needed=default_tools_for_intent(intent),
            plan_instructions=instructions,
            reasoning=f"Assigned to {profile.name} based on intent {intent.value}.",
        )
