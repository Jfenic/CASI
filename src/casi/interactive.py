"""Interactive terminal session for CASI."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from casi.agent.loop import AgentLoop
from casi.llm.base import LLMClient
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
            result = AgentLoop(
                self.client,
                ToolRegistry(self.repository),
                max_steps=self.max_steps,
            ).run(task)
            if result.success:
                self.output_fn(f"[agent] {result.response}")
            else:
                self.output_fn(f"[error] {result.error or 'Agent failed.'}")

    def _handle_command(self, command: str) -> bool:
        name = command.split(maxsplit=1)[0].lower()
        if name in {"/exit", "/quit"}:
            self.output_fn("Session ended.")
            return True
        if name == "/help":
            self.output_fn(
                "/help  Show available commands\n"
                "/history  Show tasks from this session\n"
                "/clear  Clear the session task history\n"
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
            self.output_fn("Session task history cleared.")
            return False

        self.output_fn(f"Unknown command: {name}. Type /help for commands.")
        return False