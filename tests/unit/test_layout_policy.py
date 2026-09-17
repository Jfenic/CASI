from __future__ import annotations

from pathlib import Path

from casi.agent.conversation import Conversation
from casi.agent.intent import TaskIntent
from casi.agent.loop import AgentLoop
from casi.agent.nudges import is_agent_nudge, nudge_for_propose_file_failure
from casi.agent.response_policy import ResponsePolicy, RetryBudget
from casi.llm.base import LLMResponse
from casi.tools.registry import ToolRegistry


class FakeClient:
    def __init__(self, responses: list[LLMResponse]) -> None:
        self.responses = iter(responses)
        self.calls: list[tuple[list[object], list[object]]] = []

    def complete(self, messages, tools):
        self.calls.append((messages[:], tools[:]))
        return next(self.responses)


def test_layout_known_requires_list_files(tmp_path: Path) -> None:
    conversation = Conversation([], ToolRegistry(tmp_path))

    assert conversation.layout_known() is False

    conversation.execute_tool(
        "read_file",
        {"path": "module.py"},
        require_confirmation=False,
    )
    assert conversation.repository_inspected() is True
    assert conversation.layout_known() is False

    conversation.execute_tool("list_files", {}, require_confirmation=False)
    assert conversation.layout_known() is True


def test_response_policy_requires_layout_before_create_patch() -> None:
    policy = ResponsePolicy()
    retries = RetryBudget()

    nudge = policy.evaluate_nudge(
        "Voy a crear main.py.",
        task_context="crea el archivo main.py",
        intent=TaskIntent.CREATE,
        retries=retries,
        repository_inspected=False,
        layout_known=False,
        continuing_after_clarification=False,
    )

    assert nudge is not None
    assert "Repository layout is not loaded yet" in nudge.user_message
    assert retries.deferral_nudges == 1


def test_response_policy_skips_layout_nudge_when_listing_exists() -> None:
    task = "Create only test_retry.py. Do not change implementation."
    nudge = ResponsePolicy().evaluate_nudge(
        "I will add tests.",
        task_context=task,
        intent=TaskIntent.CREATE,
        retries=RetryBudget(),
        repository_inspected=True,
        layout_known=True,
        continuing_after_clarification=False,
        mutation_workflow=True,
        remaining_test_output=". [100%]\n1 passed in 0.00s",
    )

    assert nudge is not None
    assert "Repository layout is not loaded yet" not in nudge.user_message
    assert "propose_file" in nudge.user_message


def test_propose_file_failure_nudge_mentions_layout_for_missing_parent() -> None:
    nudge = nudge_for_propose_file_failure(
        "Parent directory does not exist for tests/test_slug.py. "
        "Choose a path inside an existing directory."
    )

    assert "list_files" in nudge.user_message


def test_ensure_layout_context_runs_list_files_once(tmp_path: Path) -> None:
    (tmp_path / "slug.py").write_text(
        "def slugify(text):\n    return text\n",
        encoding="utf-8",
    )
    loop = AgentLoop(FakeClient([]), ToolRegistry(tmp_path), routing_mode="off")
    loop.conversation = loop._build_conversation([])

    loop._ensure_layout_context()
    loop._ensure_layout_context()

    list_file_messages = [
        message
        for message in loop.conversation.messages
        if message.role == "tool" and message.content.startswith("tool=list_files\n")
    ]
    assert len(list_file_messages) == 1
    assert "slug.py" in list_file_messages[0].content


def test_redirect_propose_file_without_layout_loads_listing(tmp_path: Path) -> None:
    (tmp_path / "module.py").write_text("value = 1\n", encoding="utf-8")
    loop = AgentLoop(
        FakeClient([]),
        ToolRegistry(tmp_path),
        routing_mode="off",
    )
    loop.conversation = loop._build_conversation([])
    loop._redirect_propose_file_without_layout(
        LLMResponse.tool_call(
            "propose_file",
            {"path": "tests/test_module.py", "content": "value = 2\n"},
        ),
        step=1,
        step_limit=8,
    )

    assert loop.conversation.layout_known() is True
    assert any(
        message.role == "user"
        and is_agent_nudge(message.content)
        and "list_files loaded the repository layout" in message.content
        for message in loop.conversation.messages
    )
