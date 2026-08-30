"""Interactive terminal session for CASI."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

from casi.agent.conversation import ContextCompactDecision, ContextCompactRequest
from casi.agent.loop import AgentLoop
from casi.agent.state import AgentResult
from casi.config import settings
from casi.llm.base import ChatMessage, LLMClient
from casi.patching.applier import PatchApplicationError, apply_patch
from casi.patching.extract import extract_patch
from casi.patching.validator import validate_patch
from casi.tools.registry import ToolRegistry


class InteractiveSession:
	"""Run repeated repository tasks from an interactive terminal prompt."""

	def __init__(
		self,
		repository: str | Path,
		client: LLMClient,
		*,
		max_steps: int = 8,
		routing_mode: str = "assist",
		input_fn: Callable[[str], str] = input,
		output_fn: Callable[[str], None] = print,
	) -> None:
		self.repository = repository
		self.client = client
		self.max_steps = max_steps
		self.routing_mode = routing_mode
		self.input_fn = input_fn
		self.output_fn = output_fn
		self.history: list[str] = []
		self.messages: list[ChatMessage] = []
		self._registry = ToolRegistry(self.repository)
		self._agent = AgentLoop(
			self.client,
			self._registry,
			max_steps=self.max_steps,
			messages=self.messages,
			require_tool_confirmation=self._confirm_tool,
			on_context_compact=lambda message: self._emit(f"[context] {message}"),
			on_context_compact_prompt=self._prompt_context_compact,
			routing_mode=self.routing_mode,
		)
		self._awaiting_clarification = False

	def run(self) -> int:
		"""Start the session and return a process-style exit code."""

		self._emit("CASI interactive mode. Type /help for commands.")

		while True:
			try:
				prompt = "Answer> " if self._awaiting_clarification else "CASI> "
				task = self.input_fn(prompt).strip()
			except (EOFError, KeyboardInterrupt):
				self._emit("\nSession ended.")
				return 0

			if not task:
				continue
			if task.startswith("/"):
				if self._handle_command(task):
					return 0
				continue

			if self._awaiting_clarification:
				result = self._continue_clarification(task)
			else:
				self.history.append(task)
				result = self._start_turn(task)

			if result is None:
				return 0
			if result.success and not self._awaiting_clarification:
				self._display_response(result)
				self._maybe_warn_context_usage()
			elif not result.success:
				self._emit(f"[error] {result.error or 'Agent failed.'}")

	def _start_turn(self, task: str) -> AgentResult | None:
		"""Begin a new user task and surface clarifications before the next prompt."""

		self._emit("[working] Processing your request...")
		result = self._agent.run(task)
		return self._handle_agent_result(result)

	def _continue_clarification(self, answer: str) -> AgentResult | None:
		"""Resume the current turn after the user answers a model question."""

		if answer.lower() in {"/exit", "/quit"}:
			self._awaiting_clarification = False
			self._emit("Session ended.")
			return None

		self._emit("[working] Continuing with your answer...")
		result = self._agent.run(answer)
		return self._handle_agent_result(result)

	def _handle_agent_result(self, result: AgentResult) -> AgentResult | None:
		"""Show clarifications immediately and keep the turn open until resolved."""

		if result.clarification is not None:
			self._awaiting_clarification = True
			if result.plan:
				self._emit("[plan]")
				for index, step in enumerate(result.plan, start=1):
					self._emit(f"{index}. {step}")
			self._emit(f"[question] {result.clarification}")
			self._emit("Reply at Answer> (or /exit to leave).")
			return result

		self._awaiting_clarification = False
		return result

	def _prompt_context_compact(
		self,
		request: ContextCompactRequest,
	) -> ContextCompactDecision:
		"""Ask whether to summarize old context and accept optional guidance."""

		self._emit(
			f"[context] Límite alcanzado: {request.total_messages}/{request.limit} mensajes."
		)
		self._emit(
			f"[context] Se resumirían {request.messages_to_summarize} mensajes antiguos "
			f"y se conservarían {request.messages_to_keep} recientes."
		)
		self._emit("[context] Hilo activo:")
		for line in request.preview.splitlines():
			self._emit(f"[context] {line}")

		answer = self.input_fn(
			"Resumir contexto? [y/N/instrucciones] "
			"(y=sí, n=omitir, o escribe qué conservar): "
		).strip()
		lowered = answer.lower()
		if not answer or lowered in {"n", "no"}:
			return ContextCompactDecision(summarize=False)
		if lowered in {"y", "yes", "s", "si", "sí"}:
			return ContextCompactDecision(summarize=True)
		return ContextCompactDecision(summarize=True, instructions=answer)

	def _show_context_thread(self) -> None:
		"""Display the conversation thread currently sent to the model."""

		for line in self._agent.conversation.format_context_display().splitlines():
			self._emit(f"[context] {line}")

	def _run_manual_compact(self, instructions: str) -> None:
		"""Summarize older messages on demand."""

		if not self.messages:
			self._emit("[context] No hay mensajes que resumir.")
			return

		self._emit("[context] Hilo activo antes del resumen:")
		self._show_context_thread()
		compacted = self._agent.conversation.compact(instructions=instructions)
		if not compacted:
			self._emit("[context] No había suficiente historial para resumir.")
			return

		self._emit("[context] Resumen aplicado. Hilo actual:")
		self._show_context_thread()

	def _maybe_warn_context_usage(self) -> None:
		"""Notify when the session thread is approaching the configured limit."""

		status = self._agent.conversation.context_status()
		if not status["approaching_limit"]:
			return
		if status["needs_compact"]:
			return

		self._emit(
			f"[context] {status['count']}/{status['limit']} mensajes en el hilo. "
			"Usa /context para revisarlo o /compact para resumir."
		)

	def _confirm_tool(self, tool_name: str, arguments: dict[str, object]) -> bool:
		"""Ask the user before executing tools that run commands."""

		self._emit(f"[confirm] The agent wants to run `{tool_name}`.")
		answer = self.input_fn(f"Run {tool_name}? [y/N] ").strip().lower()
		return answer in {"y", "yes"}

	def _display_response(self, result: AgentResult) -> None:
		"""Display a response and offer approval when it contains a valid diff."""

		response = result.response
		if result.patch_verification is not None:
			status = "passed" if result.patch_verification.passed else "failed"
			self._emit(
				f"[tests:{status} via {result.patch_verification.runner}] "
				f"{result.patch_verification.output or 'No test output.'}"
			)

		patch = extract_patch(response)
		if patch is None:
			if result.requested_code_change:
				self._emit(
					"[hint] No valid unified diff was returned. "
					"Ask CASI again to provide a ```diff patch."
				)
			self._emit(f"[agent] {response}")
			return

		validation = validate_patch(self.repository, patch)
		self._emit(f"[patch] {validation.error or 'Patch is valid'}")
		self._emit(patch)
		if not validation.valid:
			return

		approval = self.input_fn("Apply patch? [y/N] ").strip().lower()
		if approval not in {"y", "yes"}:
			self._emit("Patch rejected; no files were changed.")
			return

		try:
			files = apply_patch(
				self.repository,
				patch,
				approved=True,
				dry_run=False,
			)
		except PatchApplicationError as exc:
			self._emit(f"[error] {exc}")
			return
		self._emit(f"Patch applied to: {', '.join(files)}")

	def _emit(self, message: str) -> None:
		"""Write session output and flush so prompts do not appear out of order."""

		self.output_fn(message)
		sys.stdout.flush()

	def _handle_command(self, command: str) -> bool:
		name, _, remainder = command.partition(" ")
		name = name.lower()
		if name in {"/exit", "/quit"}:
			self._emit("Session ended.")
			return True
		if name == "/help":
			warn_at = max(int(settings.max_context_messages * settings.context_compact_warn_ratio), 1)
			self._emit(
				"/help  Show available commands\n"
				"/history  Show tasks from this session\n"
				"/context  Show the conversation thread sent to the model\n"
				f"/compact [instrucciones]  Summarize older context (warn from {warn_at} msgs)\n"
				"/clear  Clear session task history and conversation context\n"
				"/exit  Leave interactive mode"
			)
			return False
		if name == "/history":
			if not self.history:
				self._emit("No tasks in this session.")
			else:
				for index, task in enumerate(self.history, start=1):
					self._emit(f"{index}. {task}")
			return False
		if name == "/context":
			if not self.messages:
				self._emit("[context] No hay mensajes en el hilo.")
			else:
				self._show_context_thread()
			return False
		if name == "/compact":
			self._run_manual_compact(remainder.strip())
			return False
		if name == "/clear":
			self.history.clear()
			self.messages.clear()
			self._awaiting_clarification = False
			self._emit("Session history and conversation context cleared.")
			return False

		self._emit(f"Unknown command: {name}. Type /help for commands.")
		return False
