"""Provider-independent LLM client abstractions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class ToolCallRecord:
    """Internal execution evidence; never inferred from model response text."""

    name: str
    arguments: dict[str, object]
    success: bool
    call_id: str | None = None


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str
    tool_call: ToolCallRecord | None = None


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
    plan: list[str] = field(default_factory=list)
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    call_id: str | None = None

    @classmethod
    def final(cls, content: str) -> LLMResponse:
        return cls(kind="final", content=content)

    @classmethod
    def tool_call(
        cls,
        name: str,
        arguments: dict[str, Any],
        call_id: str | None = None,
    ) -> LLMResponse:
        return cls(
            kind="tool_call",
            tool_name=name,
            arguments=arguments,
            call_id=call_id,
        )

    @classmethod
    def clarification(cls, question: str, plan: list[str] | None = None) -> LLMResponse:
        return cls(kind="clarification", content=question, plan=plan or [])


@runtime_checkable
class LLMClient(Protocol):
    def complete(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition],
    ) -> LLMResponse:
        """Return the model's next final response or tool call."""
