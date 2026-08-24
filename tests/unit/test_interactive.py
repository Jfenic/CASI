from __future__ import annotations

from pathlib import Path

from casi.interactive import InteractiveSession
from casi.llm.base import ChatMessage, LLMResponse, ToolDefinition


class FakeClient:
    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        return LLMResponse.final("Task completed")


class ClarifyingClient:
    def __init__(self) -> None:
        self.responses = iter(
            [
                LLMResponse.clarification(
                    "Which email validation behavior should change?",
                    ["Locate the validator", "Propose a focused change"],
                ),
                LLMResponse.final("I will inspect the email validator."),
            ]
        )

    def complete(self, messages, tools):
        return next(self.responses)


def test_interactive_session_runs_task_and_exits(tmp_path: Path) -> None:
    commands = iter(["Inspect the repository", "/exit"])
    output: list[str] = []

    session = InteractiveSession(
        tmp_path,
        FakeClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    )

    assert session.run() == 0
    assert "[agent] Task completed" in output
    assert session.history == ["Inspect the repository"]


def test_interactive_session_handles_help_history_and_clear(tmp_path: Path) -> None:
    commands = iter(["First task", "/help", "/history", "/clear", "/history", "/exit"])
    output: list[str] = []

    session = InteractiveSession(
        tmp_path,
        FakeClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    )

    session.run()

    assert any("/help" in message for message in output)
    assert "1. First task" in output
    assert "Session history and conversation context cleared." in output
    assert "No tasks in this session." in output
    assert session.history == []
    assert session.messages == []


class ContextClient:
    def __init__(self) -> None:
        self.seen_lengths: list[int] = []

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        self.seen_lengths.append(len(messages))
        return LLMResponse.final(f"messages={len(messages)}")


def test_interactive_session_preserves_conversation_context(tmp_path: Path) -> None:
    client = ContextClient()
    commands = iter(["First task", "Second task", "/exit"])
    output: list[str] = []

    InteractiveSession(
        tmp_path,
        client,
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    ).run()

    assert client.seen_lengths[1] > client.seen_lengths[0]
    assert "[agent] messages=3" in output


class RunTestsClient:
    def __init__(self) -> None:
        self.calls = 0

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        if self.calls == 0:
            self.calls += 1
            return LLMResponse.tool_call("run_tests", {})
        return LLMResponse.final("Done")


def test_interactive_session_prompts_before_run_tests(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n",
        encoding="utf-8",
    )
    commands = iter(["Run tests", "n", "/exit"])
    output: list[str] = []
    prompts: list[str] = []

    def input_fn(prompt: str) -> str:
        prompts.append(prompt)
        return next(commands)

    InteractiveSession(
        tmp_path,
        RunTestsClient(),
        input_fn=input_fn,
        output_fn=output.append,
    ).run()

    assert any("Run run_tests? [y/N]" in prompt for prompt in prompts)
    assert "[agent] Done" in output


def test_interactive_session_reports_unknown_command(tmp_path: Path) -> None:
    commands = iter(["/unknown", "/exit"])
    output: list[str] = []

    InteractiveSession(
        tmp_path,
        FakeClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    ).run()

    assert any("Unknown command: /unknown." in message for message in output)


def test_interactive_session_resolves_clarification_before_final_response(
    tmp_path: Path,
) -> None:
    commands = iter(["Fix email validation", "Reject addresses without @", "/exit"])
    output: list[str] = []

    InteractiveSession(
        tmp_path,
        ClarifyingClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    ).run()

    assert "[plan]" in output
    assert any("Which email validation behavior" in message for message in output)
    assert "[agent] I will inspect the email validator." in output


def test_interactive_session_can_exit_during_clarification(tmp_path: Path) -> None:
    commands = iter(["Fix the issue", "/exit"])
    output: list[str] = []

    InteractiveSession(
        tmp_path,
        ClarifyingClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    ).run()

    assert "Session ended." in output


class PatchClient:
    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        return LLMResponse.final(
            "```diff\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -1 +1 @@\n"
            "-return False\n"
            "+return True\n"
            "```"
        )


def test_interactive_session_rejects_patch_without_changes(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "app.py").write_text("return False\n", encoding="utf-8")
    commands = iter(["Fix app.py", "n", "/exit"])
    output: list[str] = []

    InteractiveSession(
        repository,
        PatchClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    ).run()

    assert (repository / "app.py").read_text(encoding="utf-8") == "return False\n"
    assert "Patch rejected; no files were changed." in output


def test_interactive_session_applies_approved_patch(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "app.py").write_text("return False\n", encoding="utf-8")
    commands = iter(["Fix app.py", "y", "/exit"])
    output: list[str] = []

    InteractiveSession(
        repository,
        PatchClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    ).run()

    assert (repository / "app.py").read_text(encoding="utf-8") == "return True\n"
    assert any("Patch applied to" in message for message in output)