"""Conversation state and tool execution helpers."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from casi.agent.executor import execute_tool
from casi.agent.intent import extract_search_targets
from casi.config import settings
from casi.llm.base import ChatMessage, LLMClient, LLMResponse
from casi.agent.pipelines import paths_from_search_output
from casi.repository.explorer import resolve_named_paths
from casi.tools.registry import ToolRegistry
from casi.tools.result import ToolResult

ToolConfirmation = Callable[[str, dict[str, object]], bool]
ContextCompactNotifier = Callable[[str], None]

_SUMMARY_PREFIX = "[Resumen de conversación anterior]"
_SUMMARY_PROMPT = (
	"Resume la siguiente conversación entre usuario, asistente y herramientas.\n"
	"Conserva objetivos del usuario, decisiones tomadas, resultados de herramientas "
	"relevantes, archivos mencionados, errores y el estado actual de la tarea.\n"
	'Responde solo con JSON: {"type":"final","content":"..."}\n\n'
)


@dataclass(frozen=True)
class ContextCompactRequest:
	"""Details shown before compacting conversation history."""

	total_messages: int
	limit: int
	messages_to_summarize: int
	messages_to_keep: int
	preview: str


@dataclass(frozen=True)
class ContextCompactDecision:
	"""User choice for whether and how to compact history."""

	summarize: bool
	instructions: str = ""


ContextCompactPrompt = Callable[[ContextCompactRequest], ContextCompactDecision]

_READ_FILE_CALL_PATTERN = re.compile(
	r"Called tool=read_file with arguments=\{'path': '([^']+)'\}"
)


def _truncate_content(content: str, max_chars: int) -> str:
	compact = " ".join(content.split())
	if len(compact) <= max_chars:
		return compact
	return f"{compact[: max_chars - 3]}..."


def format_context_thread(
	messages: list[ChatMessage],
	*,
	max_content_chars: int = 240,
) -> str:
	"""Format the active conversation thread for terminal display."""

	if not messages:
		return "(sin mensajes en el hilo)"

	lines: list[str] = []
	for index, message in enumerate(messages, start=1):
		label = message.role
		if message.content.startswith(_SUMMARY_PREFIX):
			label = "resumen"
		content = _truncate_content(message.content, max_content_chars)
		lines.append(f"{index}. [{label}] {content}")
	return "\n".join(lines)


def _format_transcript(messages: list[ChatMessage]) -> str:
	lines = [f"{message.role}: {message.content}" for message in messages]
	return "\n\n".join(lines)


def _fallback_summary(messages: list[ChatMessage]) -> str:
	"""Build a terse summary when no LLM client is available."""

	parts: list[str] = []
	for message in messages:
		content = _truncate_content(message.content, 160)
		parts.append(f"{message.role}: {content}")
	return "\n".join(parts)


class Conversation:
	"""Manage agent messages and structured tool exchanges."""

	def __init__(
		self,
		messages: list[ChatMessage],
		registry: ToolRegistry,
		*,
		llm_client: LLMClient | None = None,
		on_context_compact: ContextCompactNotifier | None = None,
		on_context_compact_prompt: ContextCompactPrompt | None = None,
		require_tool_confirmation: ToolConfirmation | None = None,
	) -> None:
		self.messages = messages
		self.registry = registry
		self.llm_client = llm_client
		self.on_context_compact = on_context_compact
		self.on_context_compact_prompt = on_context_compact_prompt
		self.require_tool_confirmation = require_tool_confirmation
		self._clarification_pending = False

	def mark_clarification_pending(self) -> None:
		"""Remember that the next turn continues after a clarification answer."""

		self._clarification_pending = True

	def consume_clarification_continuation(self) -> bool:
		"""Return and clear whether the current turn follows a clarification."""

		pending = self._clarification_pending
		self._clarification_pending = False
		return pending

	def context_status(self) -> dict[str, int | bool]:
		"""Return counts and flags for the active conversation thread."""

		limit = settings.max_context_messages
		count = len(self.messages)
		warn_at = max(int(limit * settings.context_compact_warn_ratio), 1)
		return {
			"count": count,
			"limit": limit,
			"warn_at": warn_at,
			"needs_compact": count > limit,
			"approaching_limit": count >= warn_at,
			"has_summary": any(
				message.content.startswith(_SUMMARY_PREFIX) for message in self.messages
			),
		}

	def format_context_display(self, *, max_content_chars: int = 240) -> str:
		"""Render the thread currently used to preserve session context."""

		status = self.context_status()
		header = (
			f"Hilo activo: {status['count']}/{status['limit']} mensajes "
			f"(aviso desde {status['warn_at']})"
		)
		if status["has_summary"]:
			header += " · incluye resumen previo"
		if status["needs_compact"]:
			header += " · supera el límite"
		return f"{header}\n{format_context_thread(self.messages, max_content_chars=max_content_chars)}"

	def compact_if_needed(self) -> bool:
		"""Summarize older messages when the history exceeds configured limits."""

		limit = settings.max_context_messages
		keep_recent = max(limit - 1, 1)
		if len(self.messages) <= limit:
			return False

		to_summarize = self.messages[:-keep_recent]
		recent = self.messages[-keep_recent:]
		request = ContextCompactRequest(
			total_messages=len(self.messages),
			limit=limit,
			messages_to_summarize=len(to_summarize),
			messages_to_keep=len(recent),
			preview=self.format_context_display(),
		)

		decision = (
			self.on_context_compact_prompt(request)
			if self.on_context_compact_prompt is not None
			else ContextCompactDecision(summarize=True)
		)
		if not decision.summarize:
			if self.on_context_compact is not None:
				self.on_context_compact(
					f"Resumen omitido por el usuario "
					f"({request.total_messages} mensajes, límite {limit})."
				)
			return False

		return self._apply_compact(to_summarize, recent, instructions=decision.instructions)

	def compact(self, *, instructions: str = "", notify: bool = True) -> bool:
		"""Force summarization of older messages, optionally with user guidance."""

		limit = settings.max_context_messages
		keep_recent = max(limit - 1, 1)
		if len(self.messages) <= 1:
			return False

		to_summarize = self.messages[:-keep_recent] if len(self.messages) > keep_recent else self.messages[:-1]
		recent = self.messages[-keep_recent:] if len(self.messages) > keep_recent else self.messages[-1:]
		if not to_summarize:
			return False

		return self._apply_compact(
			to_summarize,
			recent,
			instructions=instructions,
			notify=notify,
		)

	def _apply_compact(
		self,
		to_summarize: list[ChatMessage],
		recent: list[ChatMessage],
		*,
		instructions: str,
		notify: bool = True,
	) -> bool:
		if notify and self.on_context_compact is not None:
			total_before = len(to_summarize) + len(recent)
			limit = settings.max_context_messages
			self.on_context_compact(
				f"Resumiendo {len(to_summarize)} mensajes antiguos "
				f"({total_before} en total, límite {limit})..."
			)

		summary_text = self._summarize_messages(to_summarize, instructions=instructions)
		summary_message = ChatMessage(
			role="user",
			content=f"{_SUMMARY_PREFIX}\n{summary_text}",
		)
		self.messages[:] = [summary_message] + recent
		return True

	def _summarize_messages(
		self,
		messages: list[ChatMessage],
		*,
		instructions: str = "",
	) -> str:
		if not messages:
			return ""

		if self.llm_client is None:
			return _fallback_summary(messages)

		prompt = _SUMMARY_PROMPT
		if instructions.strip():
			prompt += f"Instrucciones adicionales del usuario:\n{instructions.strip()}\n\n"
		prompt += _format_transcript(messages)
		response = self.llm_client.complete(
			[ChatMessage(role="user", content=prompt)],
			[],
		)
		content = response.content.strip()
		return content or _fallback_summary(messages)

	def append(self, role: str, content: str) -> None:
		self.messages.append(ChatMessage(role=role, content=content))

	def append_nudge(self, assistant_content: str, user_message: str) -> None:
		self.append("assistant", assistant_content)
		self.append("user", user_message)

	def execute_tool(
		self,
		tool_name: str,
		arguments: dict[str, object],
		*,
		require_confirmation: bool = True,
	) -> ToolResult:
		"""Run a repository tool and append the exchange to the conversation."""

		response = LLMResponse.tool_call(tool_name, arguments)
		result = execute_tool(
			self.registry,
			response,
			require_tool_confirmation=(
				self.require_tool_confirmation if require_confirmation else None
			),
		)
		self.append("assistant", self.format_tool_call(response.tool_name, response.arguments))
		self.append("tool", self.format_tool_result(response.tool_name, result))
		return result

	def tool_was_used(self, tool_name: str) -> bool:
		prefix = f"tool={tool_name}\n"
		return any(
			message.role == "tool" and message.content.startswith(prefix)
			for message in self.messages
		)

	def last_tool_result(self, tool_name: str) -> ToolResult | None:
		"""Return the most recent result for a repository tool."""

		prefix = f"tool={tool_name}\n"
		for message in reversed(self.messages):
			if message.role == "tool" and message.content.startswith(prefix):
				return self._parse_tool_message(message.content)
		return None

	def search_code_paths(self) -> list[str]:
		"""Return file paths discovered by search_code during this conversation."""

		paths: list[str] = []
		prefix = "tool=search_code\n"
		for message in self.messages:
			if message.role != "tool" or not message.content.startswith(prefix):
				continue
			result = self._parse_tool_message(message.content)
			if result is None:
				continue
			for path in paths_from_search_output(result.output):
				if path not in paths:
					paths.append(path)
		return paths

	def unread_search_code_paths(self) -> list[str]:
		"""Return search_code paths that have not been read with read_file yet."""

		read_paths = self.read_file_paths()
		return [path for path in self.search_code_paths() if path not in read_paths]

	@staticmethod
	def _parse_tool_message(content: str) -> ToolResult | None:
		if not content.startswith("tool="):
			return None
		lines = content.splitlines()
		if not lines:
			return None

		success = False
		output_lines: list[str] = []
		error: str | None = None
		in_output = False
		for line in lines[1:]:
			if line.startswith("success="):
				success = line.removeprefix("success=").strip() == "True"
				in_output = False
			elif line.startswith("output="):
				output_lines = [line.removeprefix("output=")]
				in_output = True
			elif line.startswith("error="):
				error_value = line.removeprefix("error=").strip()
				error = None if error_value in {"", "None"} else error_value
				in_output = False
			elif in_output:
				output_lines.append(line)

		output = "\n".join(output_lines).strip()
		return ToolResult(success=success, output=output, error=error)

	def repository_inspected(self) -> bool:
		tool_names = (
			"search_code",
			"read_file",
			"list_files",
			"git_diff",
			"run_tests",
		)
		return any(self.tool_was_used(name) for name in tool_names)

	def read_file_paths(self) -> set[str]:
		"""Return repository paths already read during this conversation."""

		paths: set[str] = set()
		for message in self.messages:
			if message.role != "assistant":
				continue
			match = _READ_FILE_CALL_PATTERN.search(message.content)
			if match:
				paths.add(match.group(1))
		return paths

	def missing_named_file_reads(self, context: str) -> list[str]:
		"""Return named files from context that have not been read yet."""

		expected = resolve_named_paths(
			self.registry.repository_path,
			extract_search_targets(context),
		)
		if not expected:
			return []
		read_paths = self.read_file_paths()
		return [path for path in expected if path not in read_paths]

	@staticmethod
	def format_tool_result(tool_name: str | None, result: ToolResult) -> str:
		return (
			f"tool={tool_name}\n"
			f"success={result.success}\n"
			f"output={result.output}\n"
			f"error={result.error}"
		)

	@staticmethod
	def format_tool_call(tool_name: str | None, arguments: dict[str, object]) -> str:
		return f"Called tool={tool_name} with arguments={arguments}"
