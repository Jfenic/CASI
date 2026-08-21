"""State returned by an agent execution."""

from __future__ import annotations

from dataclasses import dataclass, field

from casi.llm.base import ChatMessage


@dataclass(frozen=True)
class AgentResult:
	success: bool
	response: str = ""
	clarification: str | None = None
	plan: list[str] = field(default_factory=list)
	error: str | None = None
	steps: int = 0
	messages: list[ChatMessage] = field(default_factory=list)
