"""Interactive terminal session for CASI."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

from casi.agent.conversation import ContextCompactDecision, ContextCompactRequest, Conversation
from casi.agent.orchestrator import (
	AgentOrchestrator,
	OrchestratorResult,
	PendingOrchestration,
	format_segment_approval_prompt,
)
from casi.agent.planner import AgentPlan, AgentPlanStep, PlanSegment
from casi.agent.state import AgentResult
from casi.agent.trace import AgentTraceRecorder
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
		routing_mode: str = "assist",
		max_steps: int | None = None,
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
		self._session_conversation = Conversation(
			self.messages,
			self._registry,
			llm_client=self.client,
			on_context_compact=lambda message: self._emit(f"[context] {message}"),
			on_context_compact_prompt=self._prompt_context_compact,
		)
		self._awaiting_clarification = False
		self._pending_orchestration: PendingOrchestration | None = None
		self._last_plan: AgentPlan | None = None
		self._trace_enabled = False
		self._last_trace: list[str] = []
		self._trace = AgentTraceRecorder(
			on_event=lambda message: self._emit(f"[trace] {message}"),
			live=False,
		)
		self._orchestrator = AgentOrchestrator(
			self.client,
			self.repository,
			session_messages=self.messages,
			max_steps=self.max_steps,
			routing_mode=self.routing_mode,
			require_tool_confirmation=self._confirm_tool,
			approve_segment=self._approve_plan_segment,
			on_context_compact=lambda message: self._emit(f"[context] {message}"),
			on_context_compact_prompt=self._prompt_context_compact,
			on_plan=self._emit_plan,
			on_step_start=self._emit_step_start,
			on_activity=self._emit_activity,
			trace=self._trace,
		)

	def _emit_activity(self, message: str) -> None:
		self._emit(f"[working] {message}")

	def _emit_step_start(self, step: AgentPlanStep, step_number: int, total_steps: int) -> None:
		self._emit(
			f"[working] Step {step_number}/{total_steps}: "
			f"{step.agent_name} ({step.agent_role})"
		)

	def _emit_plan(self, plan: AgentPlan) -> None:
		self._last_plan = plan
		self._emit("[plan]")
		for line in plan.summary_lines():
			self._emit(line)
		self._emit(
			"[working] Executing plan… please wait. "
			"Read phases start automatically; do not type at CASI> until a response appears."
		)

	def run(self) -> int:
		"""Start the session and return a process-style exit code."""

		self._emit("CASI interactive mode. Type /help for commands.")

		while True:
			try:
				prompt = (
					"Answer (/plan, /cancel)> "
					if self._awaiting_clarification
					else "CASI> "
				)
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
			if self._awaiting_clarification and self._is_plan_request(task):
				self._show_plan()
				continue

			if self._awaiting_clarification:
				result = self._continue_clarification(task)
			else:
				self.history.append(task)
				result = self._start_turn(task)

			if result is None:
				return 0
			agent_result = self._as_agent_result(result)
			if agent_result.success and not self._awaiting_clarification:
				self._display_response(agent_result)
				self._maybe_warn_context_usage()
			elif not agent_result.success and not result.cancelled:
				self._emit(self._format_error(agent_result.error))
				self._emit_trace_summary(result.trace)

	def _format_error(self, error: str | None) -> str:
		message = error or "Agent failed."
		if "timed out" in message.lower():
			timeout = int(settings.ollama_timeout_seconds)
			return (
				f"[error] {message}\n"
				f"[hint] Ollama did not respond within {timeout}s. "
				"Check `ollama serve`, try a faster model, or raise "
				"LOCALCODE_AGENT_OLLAMA_TIMEOUT."
			)
		if "maximum of" in message.lower() and "steps" in message.lower():
			return (
				f"[error] {message}\n"
				f"[hint] Use /trace on before the next run, or /last-trace to review. "
				f"For fixes, try LOCALCODE_AGENT_FIX_MAX_STEPS=20 or --max-steps 20."
			)
		if "without a valid unified diff" in message.lower():
			return (
				f"[error] {message}\n"
				"[hint] Run /last-trace to inspect rejected tools and the exact patch "
				"validation error. Use /save-trace PATH.json to export diagnostics."
			)
		return f"[error] {message}"

	def _emit_trace_summary(self, trace: list[str]) -> None:
		if not trace:
			return
		self._last_trace = list(trace)
		self._emit("[trace] Run summary:")
		for line in trace:
			self._emit(f"[trace] {line}")

	def _set_trace_enabled(self, enabled: bool) -> None:
		self._trace_enabled = enabled
		self._trace.set_live(enabled)
		state = "on" if enabled else "off"
		self._emit(f"[trace] Live trace {state}.")

	def _show_last_trace(self) -> None:
		if not self._last_trace:
			self._emit("[trace] No trace captured yet. Failures store one automatically.")
			return
		self._emit("[trace] Last run:")
		for line in self._last_trace:
			self._emit(f"[trace] {line}")

	@staticmethod
	def _is_plan_request(message: str) -> bool:
		normalized = " ".join(message.lower().strip(" ¿?¡!").split())
		return normalized in {
			"dime el plan",
			"muestra el plan",
			"muéstrame el plan",
			"ver el plan",
			"cual es el plan",
			"cuál es el plan",
		}

	def _show_plan(self) -> None:
		plan = (
			self._pending_orchestration.plan
			if self._pending_orchestration is not None
			else self._last_plan
		)
		if plan is None:
			self._emit("[plan] No plan is available for this session.")
			return
		self._emit("[plan] Current plan:")
		for line in plan.summary_lines():
			self._emit(line)
		if self._awaiting_clarification:
			self._emit("[pending] Answer the question to continue, or use /cancel.")

	def _cancel_pending(self) -> None:
		if not self._awaiting_clarification and self._pending_orchestration is None:
			self._emit("[pending] There is no pending task to cancel.")
			return
		self._awaiting_clarification = False
		self._pending_orchestration = None
		self._emit("[pending] Pending task cancelled. You can enter a new request.")

	def _save_last_trace(self, path: str) -> None:
		if not path:
			self._emit("[trace] Usage: /save-trace PATH.json")
			return
		if not self._last_trace:
			self._emit("[trace] No trace captured yet.")
			return
		try:
			target = self._trace.save(path, events=self._last_trace)
		except OSError as exc:
			self._emit(f"[error] Could not save trace: {exc}")
			return
		self._emit(f"[trace] Saved diagnostic trace to {target}")

	def _start_turn(self, task: str) -> OrchestratorResult | None:
		"""Begin a new user task using the multi-agent orchestrator."""

		self._trace.clear()
		self._emit("[working] Planning your request...")
		result = self._handle_orchestrator_result(self._orchestrator.run(task))
		if result is not None and result.trace:
			self._last_trace = list(result.trace)
		return result

	def _continue_clarification(self, answer: str) -> OrchestratorResult | None:
		"""Resume the current turn after the user answers a model question."""

		if answer.lower() in {"/exit", "/quit"}:
			self._awaiting_clarification = False
			self._pending_orchestration = None
			self._emit("Session ended.")
			return None

		self._emit("[working] Continuing with your answer...")
		if self._pending_orchestration is None:
			return self._handle_orchestrator_result(self._orchestrator.run(answer))
		return self._handle_orchestrator_result(
			self._orchestrator.run(answer, pending=self._pending_orchestration)
		)

	def _approve_plan_segment(self, segment: PlanSegment) -> bool:
		"""Ask once before running a non-read plan phase."""

		self._emit(format_segment_approval_prompt(segment))
		answer = self.input_fn("Approve phase> ").strip().lower()
		return answer in {"y", "yes", "s", "si", "sí"}

	def _handle_orchestrator_result(
		self,
		result: OrchestratorResult,
	) -> OrchestratorResult | None:
		if result.cancelled:
			self._awaiting_clarification = False
			self._pending_orchestration = None
			self._emit(result.error or "Execution cancelled.")
			return result

		if result.clarification is not None:
			self._awaiting_clarification = True
			self._pending_orchestration = result.pending
			self._emit(f"[question] {result.clarification}")
			self._emit(
				"[pending] Reply to continue. Use /plan to review the current plan, "
				"/cancel to discard it, or /exit to leave."
			)
			return result

		self._awaiting_clarification = False
		self._pending_orchestration = None
		if result.step_results:
			last = result.step_results[-1]
			self._emit(f"[agent:{last.step.agent_name}] {last.step.agent_role}")
		return result

	@staticmethod
	def _as_agent_result(result: OrchestratorResult) -> AgentResult:
		return AgentResult(
			success=result.success,
			response=result.response,
			error=result.error,
			clarification=result.clarification,
			plan=result.plan,
			patch_verification=result.patch_verification,
			requested_code_change=result.requested_code_change,
			trace=result.trace,
		)

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

		for line in self._session_conversation.format_context_display().splitlines():
			self._emit(f"[context] {line}")

	def _run_manual_compact(self, instructions: str) -> None:
		"""Summarize older messages on demand."""

		if not self.messages:
			self._emit("[context] No hay mensajes que resumir.")
			return

		self._emit("[context] Hilo activo antes del resumen:")
		self._show_context_thread()
		compacted = self._session_conversation.compact(instructions=instructions)
		if not compacted:
			self._emit("[context] No había suficiente historial para resumir.")
			return

		self._emit("[context] Resumen aplicado. Hilo actual:")
		self._show_context_thread()

	def _maybe_warn_context_usage(self) -> None:
		"""Notify when the session thread is approaching the configured limit."""

		status = self._session_conversation.context_status()
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
		if result.patch_verification is not None and not result.patch_verification.passed:
			self._emit(
				"[error] Patch was not applied because its sandbox tests failed. "
				"No repository files were changed."
			)
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
				"/trace [on|off]  Show or toggle live decision trace\n"
				"/last-trace  Show trace from the last run\n"
				"/save-trace PATH.json  Save the last trace as structured JSON\n"
				"/plan  Show the current or last generated plan\n"
				"/cancel  Cancel a task waiting for clarification\n"
				"/exit  Leave interactive mode\n"
				"\n"
				"While CASI works, watch for [working] status lines. "
				"Use /trace on to see each tool call and nudge live. "
				"Do not type at CASI> until you see [agent] or [question]."
			)
			return False
		if name == "/trace":
			argument = remainder.strip().lower()
			if argument in {"on", "off"}:
				self._set_trace_enabled(argument == "on")
			elif self._trace_enabled:
				self._emit("[trace] Live trace is on.")
			else:
				self._emit("[trace] Live trace is off. Use /trace on to enable.")
			return False
		if name == "/last-trace":
			self._show_last_trace()
			return False
		if name == "/save-trace":
			self._save_last_trace(remainder.strip())
			return False
		if name == "/plan":
			self._show_plan()
			return False
		if name == "/cancel":
			self._cancel_pending()
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
			self._pending_orchestration = None
			self._last_plan = None
			self._emit("Session history and conversation context cleared.")
			return False

		self._emit(f"Unknown command: {name}. Type /help for commands.")
		return False
