"""State returned by an agent execution."""

from __future__ import annotations

from dataclasses import dataclass, field

from casi_code_agent.llm.base import ChatMessage


@dataclass(frozen=True)
class AgentResult:
	success: bool
	response: str = ""
	error: str | None = None
	steps: int = 0
	messages: list[ChatMessage] = field(default_factory=list)
