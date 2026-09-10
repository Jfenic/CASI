"""Isolated task context and session merge helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from casi.agent.state import AgentResult
from casi.llm.base import ChatMessage


@dataclass
class TaskScope:
    """Task-local message history with optional merge into a session thread."""

    task_messages: list[ChatMessage] = field(default_factory=list)
    session_messages: list[ChatMessage] | None = None

    def merge_result(self, task: str, result: AgentResult) -> None:
        """Persist only the user turn and assistant outcome in the session thread."""

        if self.session_messages is None:
            return

        self.session_messages.append(ChatMessage(role="user", content=task.strip()))
        if result.clarification is not None:
            self.session_messages.append(
                ChatMessage(role="assistant", content=result.clarification)
            )
            return

        if result.success and result.response.strip():
            self.session_messages.append(
                ChatMessage(role="assistant", content=result.response.strip())
            )
            return

        if result.error:
            self.session_messages.append(
                ChatMessage(role="assistant", content=f"[error] {result.error}")
            )
