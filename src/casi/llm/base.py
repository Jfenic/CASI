"""Provider-independent LLM client abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence


@dataclass(frozen=True)
class ChatMessage:
	role: str
	content: str


@dataclass(frozen=True)
class ToolDefinition:
	name: str
	description: str
	arguments: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
	kind: str
	content: str = ""
	tool_name: str | None = None
	arguments: dict[str, Any] = field(default_factory=dict)

	@classmethod
	def final(cls, content: str) -> "LLMResponse":
		return cls(kind="final", content=content)

	@classmethod
	def tool_call(cls, name: str, arguments: dict[str, Any]) -> "LLMResponse":
		return cls(kind="tool_call", tool_name=name, arguments=arguments)


class LLMClient(Protocol):
	def complete(
		self,
		messages: Sequence[ChatMessage],
		tools: Sequence[ToolDefinition],
	) -> LLMResponse:
		"""Return the model's next final response or tool call."""
