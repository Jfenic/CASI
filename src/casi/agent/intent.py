"""Task intent classification for agent routing."""

from __future__ import annotations

import re
from enum import Enum

from casi.agent.nudges import is_agent_nudge
from casi.llm.base import ChatMessage

SEARCH_STOP_WORDS = frozenset(
	{
		"the",
		"and",
		"for",
		"with",
		"from",
		"that",
		"this",
		"what",
		"why",
		"how",
		"por",
		"que",
		"qué",
		"con",
		"para",
		"como",
		"cómo",
		"los",
		"las",
		"una",
		"uno",
	}
)

IDENTIFIER_PATTERN = re.compile(
	r"`([^`]+)`"
	r"|\b(?:test_[a-z0-9_]+|[a-z][a-z0-9_]*_[a-z0-9_]+)\b"
	r"|\b[A-Z][a-z0-9_]*[A-Z][a-zA-Z0-9_]*\b"
	r"|\b[\w.-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|md|toml|yaml|yml|json|txt)\b",
)

_CONVERSATION_PATTERN = re.compile(
	r"^(?:hola|hi|hello|hey|gracias|thanks|buenos días|buenas tardes)[!.?\s]*$",
	re.IGNORECASE,
)

_META_PATTERN = re.compile(
	r"\b(?:modelo|model|tools?|herramientas?|quién eres|quien eres|"
	r"what model|which tools|qué tool|que tool)\b",
	re.IGNORECASE,
)

_GIT_STATUS_PATTERN = re.compile(
	r"\b(?:git_diff|git diff|git status|estado actual|current changes|"
	r"cambios actuales|working tree)\b",
	re.IGNORECASE,
)

_OVERVIEW_PATTERN = re.compile(
	r"\b(?:about|overview|describe|descripción|descripcion|"
	r"de qué trata|que trata|qué trata|"
	r"purpose|propósito|proposito|estructura|structure|lista|listar|list|"
	r"qué es este|que es este|what is this|proyecto|project)\b",
	re.IGNORECASE,
)

_REPOSITORY_KEYWORDS = re.compile(
	r"\b(?:test|tests|bug|error|fail|falla|function|función|class|module|"
	r"file|archivo|repo|repository|repositorio|código|code|"
	r"explain|explica|prueba|pruebas)\b",
	re.IGNORECASE,
)

_RUN_TESTS_PATTERN = re.compile(
	r"\b(?:run tests|run_tests|ejecuta(?:r)?(?: los| las)? tests|"
	r"ejecuta(?:r)?(?: las)? pruebas|correr tests)\b",
	re.IGNORECASE,
)

_APPLY_PATCH_PATTERN = re.compile(
	r"\bapply[_ ]patch\b",
	re.IGNORECASE,
)

_CHANGE_REQUEST_PATTERN = re.compile(
	r"\b(?:fix|fixes|corrige(?:lo|la|los|las)?|corrígelo|corrígela|corregir|"
	r"arregla(?:lo|la|los|las)?|arréglalo|arréglala|repara(?:lo|la)?|repáralo|"
	r"repair|actualiza|update|modifica|cambia)\b"
	r"|\b(?:pass|pasa|pasan|pasen|make|haz)\b.{0,40}\b(?:test|tests|prueba|pruebas)\b"
	r"|\b(?:test|tests|prueba|pruebas)\b.{0,40}\b(?:pass|pasa|pasan|pasen|fix|corrige)\b",
	re.IGNORECASE | re.DOTALL,
)

_PATCH_REQUEST_PATTERN = re.compile(
	r"\b(?:genera|generar|create|crea|provide|proporciona|envia|envía)\b"
	r".{0,40}\b(?:parche|patch|diff)\b"
	r"|\b(?:parche|patch|diff)\b.{0,20}\b(?:valido|válido|valid)\b",
	re.IGNORECASE | re.DOTALL,
)

_PLAN_RECALL_PATTERN = re.compile(
	r"\b(?:dime|muestra|muéstrame|muestrame|ver|recuerda|recuerdame|recuérdame|"
	r"cual|cuál|que|qué|what)\b.{0,40}\b(?:plan|planes|pasos|estrategia|"
	r"ibas a hacer|vas a hacer|next steps)\b"
	r"|\b(?:what(?:'s| is) the plan|show me the plan)\b",
	re.IGNORECASE | re.DOTALL,
)

USER_DEFERRAL_PATTERN = re.compile(
	r"\b(?:provide|proporciona|proporcioname|proporción|share|comparte|"
	r"paste|pega|send|envia|envía|give me|dame|need)\b"
	r".{0,80}\b(?:code|código|source|file|archivo|test|error|output|"
	r"salida|function|función|implementation|implementación)\b",
	re.IGNORECASE | re.DOTALL,
)


class RoutingMode(str, Enum):
	"""How aggressively CASI applies deterministic repository pipelines."""

	ASSIST = "assist"
	STRICT = "strict"
	OFF = "off"


class TaskIntent(str, Enum):
	"""High-level user goal detected from the current task."""

	CONVERSATION = "conversation"
	META = "meta"
	OVERVIEW = "overview"
	INSPECT = "inspect"
	GIT_STATUS = "git_status"
	FIX = "fix"
	RECALL_PLAN = "recall_plan"
	PRESENT = "present"
	UNKNOWN = "unknown"


def parse_routing_mode(value: str) -> RoutingMode:
	"""Parse a routing mode from CLI or environment configuration."""

	try:
		return RoutingMode(value.lower())
	except ValueError as exc:
		allowed = ", ".join(mode.value for mode in RoutingMode)
		raise ValueError(f"routing mode must be one of: {allowed}") from exc


def build_task_context(
	task: str,
	messages: list[ChatMessage],
	*,
	max_prior: int = 4,
) -> str:
	"""Combine the current task with recent user requests when helpful."""

	parts = [task.strip()]
	prior_users: list[str] = []
	for message in reversed(messages):
		if message.role != "user":
			continue
		previous = message.content.strip()
		if not previous or previous == task.strip() or is_agent_nudge(previous):
			continue
		prior_users.append(previous)
		if len(prior_users) >= max_prior:
			break
	parts.extend(prior_users)
	return " ".join(parts)


def extract_search_targets(text: str) -> list[str]:
	"""Extract likely repository identifiers, symbols, and paths from user text."""

	targets: list[str] = []
	for match in IDENTIFIER_PATTERN.finditer(text):
		candidate = match.group(1) or match.group(0)
		candidate = candidate.strip().strip("'\"")
		if candidate and candidate not in targets:
			targets.append(candidate)
	return targets


def derive_search_queries(task: str) -> list[str]:
	"""Build repository search queries from user context."""

	queries = extract_search_targets(task)
	if queries:
		return queries

	tokens = re.findall(r"\w+", task, flags=re.UNICODE)
	meaningful = [
		token
		for token in tokens
		if len(token) > 2 and token.lower() not in SEARCH_STOP_WORDS
	]
	return meaningful or [task]


def task_requests_code_change(context: str) -> bool:
	"""Return whether the user is asking CASI to modify code or pass tests."""

	return (
		_CHANGE_REQUEST_PATTERN.search(context) is not None
		or _PATCH_REQUEST_PATTERN.search(context) is not None
	)


def task_requests_test_execution(context: str) -> bool:
	"""Return whether the user asks to run tests without necessarily changing code."""

	return _RUN_TESTS_PATTERN.search(context) is not None


def task_requests_patch_application(context: str) -> bool:
	"""Return whether the user explicitly asks to apply a patch."""

	return _APPLY_PATCH_PATTERN.search(context) is not None


def classify_intent(context: str) -> TaskIntent:
	"""Return fast-path intents only; everything else uses the general agent."""

	if _CONVERSATION_PATTERN.match(context.strip()):
		return TaskIntent.CONVERSATION
	if _PLAN_RECALL_PATTERN.search(context):
		return TaskIntent.RECALL_PLAN
	if _META_PATTERN.search(context):
		return TaskIntent.META
	if _GIT_STATUS_PATTERN.search(context):
		return TaskIntent.GIT_STATUS
	return TaskIntent.UNKNOWN


def is_fast_path_intent(intent: TaskIntent) -> bool:
	"""Return whether the intent bypasses the general repository agent."""

	return intent in {
		TaskIntent.CONVERSATION,
		TaskIntent.META,
		TaskIntent.RECALL_PLAN,
		TaskIntent.GIT_STATUS,
	}


def intent_supports_pipeline(intent: TaskIntent) -> bool:
	"""Return whether a deterministic repository pipeline exists for the intent."""

	return intent in {
		TaskIntent.UNKNOWN,
		TaskIntent.OVERVIEW,
		TaskIntent.INSPECT,
		TaskIntent.GIT_STATUS,
		TaskIntent.FIX,
	}


def response_defers_repository_work(content: str, intent: TaskIntent) -> bool:
	"""Detect answers that push repository inspection back to the user."""

	if intent not in {TaskIntent.OVERVIEW, TaskIntent.INSPECT, TaskIntent.UNKNOWN}:
		return False
	return USER_DEFERRAL_PATTERN.search(content) is not None


def should_defer_clarification(
	context: str,
	intent: TaskIntent,
	*,
	repository_inspected: bool,
) -> bool:
	"""Return whether the model should act instead of asking the user."""

	if task_requests_code_change(context):
		return True
	if intent in {
		TaskIntent.INSPECT,
		TaskIntent.OVERVIEW,
		TaskIntent.GIT_STATUS,
		TaskIntent.FIX,
		TaskIntent.RECALL_PLAN,
		TaskIntent.PRESENT,
	}:
		return True
	if intent is TaskIntent.UNKNOWN and repository_inspected:
		return True
	if extract_search_targets(context):
		return True
	if repository_inspected:
		return True
	return False
