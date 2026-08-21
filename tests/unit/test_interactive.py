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
    assert "Session task history cleared." in output
    assert "No tasks in this session." in output
    assert session.history == []


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