from __future__ import annotations

from pathlib import Path

from casi.agent.loop import AgentLoop
from casi.llm.base import ChatMessage, LLMResponse, ToolDefinition
from casi.tools.registry import ToolRegistry


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


def test_agent_loop_executes_tool_then_returns_final_response(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")
    client = FakeClient(
        [
            LLMResponse.tool_call("read_file", {"path": "README.md"}),
            LLMResponse.final("The file contains hello."),
        ]
    )

    result = AgentLoop(client, ToolRegistry(tmp_path)).run("Inspect README.md")

    assert result.success is True
    assert result.response == "The file contains hello."
    assert result.steps == 2
    assert client.calls[0][1][1].name == "read_file"
    assert "hello" in client.calls[1][0][-1].content


def test_agent_loop_stops_at_step_limit(tmp_path: Path) -> None:
    client = FakeClient([LLMResponse.tool_call("list_files", {})] * 2)

    result = AgentLoop(client, ToolRegistry(tmp_path), max_steps=2).run("Inspect")

    assert result.success is False
    assert result.steps == 2
    assert result.error == "Agent reached the maximum of 2 steps"


def test_agent_loop_excludes_mutation_tools_from_definitions(tmp_path: Path) -> None:
    client = FakeClient([LLMResponse.final("done")])
    registry = ToolRegistry(tmp_path)

    AgentLoop(client, registry).run("Inspect")

    tool_names = {tool.name for tool in client.calls[0][1]}
    assert "apply_patch" not in tool_names
    assert "read_file" in tool_names


def test_agent_loop_blocks_apply_patch_tool_call(tmp_path: Path) -> None:
    client = FakeClient(
        [
            LLMResponse.tool_call(
                "apply_patch",
                {"patch": "--- a/x\n+++ b/x\n", "approved": True, "dry_run": False},
            ),
            LLMResponse.final("Stopped"),
        ]
    )

    result = AgentLoop(client, ToolRegistry(tmp_path)).run("Apply patch")

    assert result.success is True
    tool_message = client.calls[1][0][-1].content
    assert "success=False" in tool_message
    assert "Mutation tools cannot be executed" in tool_message


def test_agent_loop_requires_confirmation_for_run_tests(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n",
        encoding="utf-8",
    )
    client = FakeClient(
        [
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.final("Tests finished"),
        ]
    )
    confirmations: list[tuple[str, dict[str, object]]] = []

    def confirm(tool_name: str, arguments: dict[str, object]) -> bool:
        confirmations.append((tool_name, arguments))
        return False

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        require_tool_confirmation=confirm,
    ).run("Run tests")

    assert confirmations == [("run_tests", {})]
    assert result.success is True
    assert "Tool execution denied by user" in client.calls[1][0][-1].content


def test_agent_loop_runs_search_code_after_clarification(tmp_path: Path) -> None:
    (tmp_path / "validators.py").write_text(
        "def validate_email():\n    pass\n",
        encoding="utf-8",
    )
    client = FakeClient([LLMResponse.clarification("Which behavior should change?")])
    loop = AgentLoop(client, ToolRegistry(tmp_path))

    clarification = loop.run("Fix email validation")
    assert clarification.clarification == "Which behavior should change?"

    client.responses = iter([LLMResponse.final("Found validate_email in validators.py.")])
    result = loop.run("Tighten validate_email to reject bad addresses")

    assert result.success is True
    assert result.response == "Found validate_email in validators.py."
    tool_messages = [message for message in loop.messages if message.role == "tool"]
    assert any("validate_email" in message.content for message in tool_messages)
    assert "validate_email" in client.calls[1][0][-1].content


def test_agent_loop_derives_search_queries_from_clarified_task() -> None:
    assert AgentLoop._derive_search_queries(
        "corrige la validación de email y agrega tests"
    ) == ["validación", "email"]
    assert AgentLoop._derive_search_queries(
        "Tighten validate_email to reject bad addresses"
    ) == ["validate_email", "addresses", "Tighten"]