"""Interactive terminal session for CASI."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from casi.agent.loop import AgentLoop
from casi.llm.base import ChatMessage, LLMClient
from casi.patching.applier import PatchApplicationError, apply_patch
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
		input_fn: Callable[[str], str] = input,
		output_fn: Callable[[str], None] = print,
	) -> None:
		self.repository = repository
		self.client = client
		self.max_steps = max_steps
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
		)

	def run(self) -> int:
		"""Start the session and return a process-style exit code."""

		self.output_fn("CASI interactive mode. Type /help for commands.")

		while True:
			try:
				task = self.input_fn("CASI> ").strip()
			except (EOFError, KeyboardInterrupt):
				self.output_fn("\nSession ended.")
				return 0

			if not task:
				continue
			if task.startswith("/"):
				if self._handle_command(task):
					return 0
				continue

			self.history.append(task)
			result = self._agent.run(task)
			if result.success:
				self._display_response(result.response)
			else:
				self.output_fn(f"[error] {result.error or 'Agent failed.'}")

	def _confirm_tool(self, tool_name: str, arguments: dict[str, object]) -> bool:
		"""Ask the user before executing tools that run commands."""

		answer = self.input_fn(f"Run {tool_name}? [y/N] ").strip().lower()
		return answer in {"y", "yes"}

	def _display_response(self, response: str) -> None:
		"""Display a response and offer approval when it contains a valid diff."""

		patch = self._extract_patch(response)
		if patch is None:
			self.output_fn(f"[agent] {response}")
			return

		validation = validate_patch(self.repository, patch)
		self.output_fn(f"[patch] {validation.error or 'Patch is valid'}")
		self.output_fn(patch)
		if not validation.valid:
			return

		approval = self.input_fn("Apply patch? [y/N] ").strip().lower()
		if approval not in {"y", "yes"}:
			self.output_fn("Patch rejected; no files were changed.")
			return

		try:
			files = apply_patch(
				self.repository,
				patch,
				approved=True,
				dry_run=False,
			)
		except PatchApplicationError as exc:
			self.output_fn(f"[error] {exc}")
			return
		self.output_fn(f"Patch applied to: {', '.join(files)}")

	@staticmethod
	def _extract_patch(response: str) -> str | None:
		"""Extract a fenced or raw unified diff from model output."""

		marker = "```diff"
		if marker in response:
			patch = response.split(marker, 1)[1].split("```", 1)[0].strip()
			if patch.startswith("--- ") and "+++ " in patch:
				return patch + "\n"

		start = response.find("--- a/")
		if start >= 0:
			patch = response[start:].strip()
			if "+++ b/" in patch:
				return patch + "\n"
		return None

	def _handle_command(self, command: str) -> bool:
		name = command.split(maxsplit=1)[0].lower()
		if name in {"/exit", "/quit"}:
			self.output_fn("Session ended.")
			return True
		if name == "/help":
			self.output_fn(
				"/help  Show available commands\n"
				"/history  Show tasks from this session\n"
				"/clear  Clear session task history and conversation context\n"
				"/exit  Leave interactive mode"
			)
			return False
		if name == "/history":
			if not self.history:
				self.output_fn("No tasks in this session.")
			else:
				for index, task in enumerate(self.history, start=1):
					self.output_fn(f"{index}. {task}")
			return False
		if name == "/clear":
			self.history.clear()
			self.messages.clear()
			self.output_fn("Session history and conversation context cleared.")
			return False

		self.output_fn(f"Unknown command: {name}. Type /help for commands.")
		return False
