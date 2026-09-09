from __future__ import annotations

from pathlib import Path

import pytest

from casi.agent.factory import AgentFactory
from casi.agent.intent import TaskIntent
from casi.agent.profiles import resolve_profile
from casi.llm.base import ChatMessage, LLMResponse, ToolDefinition


class FakeClient:
    def __init__(self, responses: list[LLMResponse]) -> None:
        self.responses = iter(responses)
        self.calls: list[tuple[list[ChatMessage], list[ToolDefinition]]] = []

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        self.calls.append((messages[:], tools[:]))
        return next(self.responses)


def test_resolve_profile_accepts_intent_and_name() -> None:
    assert resolve_profile(TaskIntent.FIX).name == "fix"
    assert resolve_profile(TaskIntent.CREATE).name == "create"
    assert resolve_profile("inspect").objective is TaskIntent.INSPECT


def test_resolve_profile_rejects_unknown_objective() -> None:
    with pytest.raises(ValueError, match="Unknown agent objective"):
        resolve_profile("not-a-profile")


def test_factory_create_assigns_profile_and_role_instructions(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")
    client = FakeClient(
        [
            LLMResponse.final("Es un proyecto demo."),
            LLMResponse.final("Es un proyecto demo."),
        ]
    )

    agent = AgentFactory.create(
        TaskIntent.OVERVIEW,
        client=client,
        repository=tmp_path,
    )

    assert agent.profile.name == "overview"
    assert agent.profile.role == "Repository Overview Specialist"
    result = agent.run("dime que trata este proyecto")
    assert result.success is True


def test_factory_for_task_uses_fix_agent(tmp_path: Path) -> None:
    client = FakeClient([LLMResponse.final("done")])

    agent = AgentFactory.for_task(
        "corrige los tests",
        client=client,
        repository=tmp_path,
        require_tool_confirmation=lambda *_args: True,
        routing_mode="off",
    )

    assert agent.profile.objective is TaskIntent.FIX
    assert agent.profile.name == "fix"
    assert agent.loop.max_steps == 12


def test_factory_uses_profile_max_steps_when_unspecified(tmp_path: Path) -> None:
    agent = AgentFactory.create(TaskIntent.INSPECT, client=FakeClient([]), repository=tmp_path)
    assert agent.loop.max_steps == 8


def test_presenter_agent_does_not_receive_repository_tools(tmp_path: Path) -> None:
    client = FakeClient([LLMResponse.final("## Resumen\n\nFormatted.")])
    agent = AgentFactory.create(
        TaskIntent.PRESENT,
        client=client,
        repository=tmp_path,
    )

    result = agent.run(
        "Format and structure the final answer for this user request: explain repo\n\n"
        "Context from previous agent (overview):\nRaw draft."
    )

    assert result.success is True
    assert client.calls[0][1] == []
    assert "## Resumen" in result.response


def test_task_scope_keeps_tool_output_out_of_session_thread(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")
    session: list[ChatMessage] = []
    client = FakeClient(
        [
            LLMResponse.tool_call("read_file", {"path": "README.md"}),
            LLMResponse.final("First answer."),
            LLMResponse.final("Second answer."),
        ]
    )

    first = AgentFactory.for_task(
        "Inspect README.md",
        client=client,
        repository=tmp_path,
        session_messages=session,
    ).run("Inspect README.md")
    second = AgentFactory.for_task(
        "hola",
        client=client,
        repository=tmp_path,
        session_messages=session,
    ).run("hola")

    assert first.success is True
    assert second.success is True
    assert any(message.role == "tool" for message in first.messages)
    assert not any(message.role == "tool" for message in session)
    assert [message.content for message in session] == [
        "Inspect README.md",
        "First answer.",
        "hola",
        "Second answer.",
    ]
