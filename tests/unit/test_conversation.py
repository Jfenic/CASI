from __future__ import annotations

from casi.agent.conversation import (
    ContextCompactDecision,
    ContextCompactRequest,
    Conversation,
    format_context_thread,
)
from casi.config import settings
from casi.llm.base import ChatMessage, LLMResponse
from casi.tools.registry import ToolRegistry


class FakeSummarizeClient:
    def __init__(self, summary: str) -> None:
        self.summary = summary
        self.calls: list[list[ChatMessage]] = []

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[object],
    ) -> LLMResponse:
        self.calls.append(messages[:])
        return LLMResponse.final(self.summary)


def test_compact_if_needed_keeps_recent_messages_within_limit(tmp_path) -> None:
    messages = [
        ChatMessage(role="user", content=f"message {index}") for index in range(5)
    ]
    conversation = Conversation(
        messages,
        ToolRegistry(tmp_path),
        llm_client=FakeSummarizeClient("Resumen breve."),
    )

    original_limit = settings.max_context_messages
    try:
        object.__setattr__(settings, "max_context_messages", 3)
        compacted = conversation.compact_if_needed()
    finally:
        object.__setattr__(settings, "max_context_messages", original_limit)

    assert compacted is True
    assert len(conversation.messages) == 3
    assert conversation.messages[0].content.startswith(
        "[Resumen de conversación anterior]"
    )
    assert "Resumen breve." in conversation.messages[0].content
    assert conversation.messages[-1].content == "message 4"
    assert conversation.messages[-2].content == "message 3"


def test_compact_if_needed_notifies_before_summarizing(tmp_path) -> None:
    messages = [
        ChatMessage(role="user", content=f"message {index}") for index in range(5)
    ]
    notifications: list[str] = []
    client = FakeSummarizeClient("Resumen.")
    conversation = Conversation(
        messages,
        ToolRegistry(tmp_path),
        llm_client=client,
        on_context_compact=notifications.append,
    )

    original_limit = settings.max_context_messages
    try:
        object.__setattr__(settings, "max_context_messages", 3)
        conversation.compact_if_needed()
    finally:
        object.__setattr__(settings, "max_context_messages", original_limit)

    assert len(notifications) == 1
    assert "Resumiendo 3 mensajes antiguos" in notifications[0]
    assert "(5 en total, límite 3)" in notifications[0]
    assert len(client.calls) == 1


def test_compact_if_needed_skips_when_under_limit(tmp_path) -> None:
    messages = [ChatMessage(role="user", content="only one")]
    notifications: list[str] = []
    client = FakeSummarizeClient("unused")
    conversation = Conversation(
        messages,
        ToolRegistry(tmp_path),
        llm_client=client,
        on_context_compact=notifications.append,
    )

    assert conversation.compact_if_needed() is False
    assert notifications == []
    assert client.calls == []
    assert conversation.messages == messages


def test_compact_if_needed_uses_fallback_without_llm_client(tmp_path) -> None:
    messages = [
        ChatMessage(role="user", content="first question"),
        ChatMessage(role="assistant", content="first answer"),
        ChatMessage(role="user", content="second question"),
        ChatMessage(role="assistant", content="second answer"),
    ]
    conversation = Conversation(messages, ToolRegistry(tmp_path))

    original_limit = settings.max_context_messages
    try:
        object.__setattr__(settings, "max_context_messages", 3)
        compacted = conversation.compact_if_needed()
    finally:
        object.__setattr__(settings, "max_context_messages", original_limit)

    assert compacted is True
    assert "first question" in conversation.messages[0].content
    assert conversation.messages[-1].content == "second answer"


def test_format_context_thread_marks_summary_messages() -> None:
    messages = [
        ChatMessage(role="user", content="[Resumen de conversación anterior]\nAntiguo"),
        ChatMessage(role="user", content="Nueva pregunta"),
    ]

    display = format_context_thread(messages)

    assert "[resumen]" in display
    assert "[user] Nueva pregunta" in display


def test_compact_if_needed_honors_prompt_skip(tmp_path) -> None:
    messages = [
        ChatMessage(role="user", content=f"message {index}") for index in range(5)
    ]
    client = FakeSummarizeClient("unused")

    def reject(_request: ContextCompactRequest) -> ContextCompactDecision:
        return ContextCompactDecision(summarize=False)

    conversation = Conversation(
        messages,
        ToolRegistry(tmp_path),
        llm_client=client,
        on_context_compact_prompt=reject,
    )

    original_limit = settings.max_context_messages
    try:
        object.__setattr__(settings, "max_context_messages", 3)
        compacted = conversation.compact_if_needed()
    finally:
        object.__setattr__(settings, "max_context_messages", original_limit)

    assert compacted is False
    assert len(conversation.messages) == 5
    assert client.calls == []


def test_compact_passes_user_instructions_to_summarizer(tmp_path) -> None:
    messages = [
        ChatMessage(role="user", content=f"message {index}") for index in range(5)
    ]
    client = FakeSummarizeClient("Resumen con archivos.")
    conversation = Conversation(
        messages,
        ToolRegistry(tmp_path),
        llm_client=client,
    )

    original_limit = settings.max_context_messages
    try:
        object.__setattr__(settings, "max_context_messages", 3)
        conversation.compact(instructions="Conserva los nombres de archivos.")
    finally:
        object.__setattr__(settings, "max_context_messages", original_limit)

    assert len(client.calls) == 1
    assert "Conserva los nombres de archivos." in client.calls[0][0].content
