"""ModelProvider protocol and abstract base class for CASI."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from casi.llm.actions import ProposeFileAction
from casi.llm.base import ChatMessage, LLMResponse, ToolDefinition


@runtime_checkable
class ModelProvider(Protocol):
    """Protocol satisfied by all LLM model providers in CASI."""

    @property
    def provider_name(self) -> str:
        """The identifier of this provider (e.g. 'ollama', 'openai')."""
        ...

    @property
    def model_name(self) -> str:
        """The active model name (e.g. 'qwen2.5-coder:7b', 'gpt-4o')."""
        ...

    @property
    def supports_evaluation(self) -> bool:
        """Whether this provider can be used by LLMTaskEvaluator."""
        ...

    def complete(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition],
    ) -> LLMResponse:
        """Return the next model decision or tool call."""
        ...

    def complete_action(
        self,
        messages: Sequence[ChatMessage],
        action: type[ProposeFileAction] = ProposeFileAction,
    ) -> LLMResponse:
        """Constrain a mutation turn to the action schema."""
        ...

    def complete_tool_call(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition],
    ) -> LLMResponse:
        """Constrain a decision to a tool call."""
        ...

    def with_role_instructions(self, role_instructions: str) -> ModelProvider:
        """Return a copy of the provider with specific specialist role instructions."""
        ...
