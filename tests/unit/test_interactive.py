from __future__ import annotations

import json
from pathlib import Path

from casi.config import settings
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
                LLMResponse.final("## Plan\n\nI will inspect the email validator."),
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
    assert any("[working] Planning your request..." in line for line in output)
    assert any("[plan]" in line for line in output)
    assert any("Executing plan" in line for line in output)
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

    session = InteractiveSession(
        tmp_path,
        client,
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    )
    session.run()

    assert len(client.seen_lengths) >= 2
    assert [message.role for message in session.messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert session.messages[0].content == "First task"
    assert session.messages[2].content == "Second task"
    assert session.messages[1].content.startswith("messages=")
    assert session.messages[3].content.startswith("messages=")


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
    commands = iter(["Run tests", "y", "/exit"])
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

    assert any("Approve phase>" in prompt for prompt in prompts)
    assert not any("Run run_tests? [y/N]" in prompt for prompt in prompts)
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
    commands = iter(["Improve things please", "Focus on readability", "/exit"])
    output: list[str] = []

    InteractiveSession(
        tmp_path,
        ClarifyingClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    ).run()

    assert "[plan]" in output
    assert any("Which email validation behavior" in message for message in output)
    assert any("I will inspect the email validator." in message for message in output)


def test_interactive_session_uses_answer_prompt_during_clarification(tmp_path: Path) -> None:
    prompts: list[str] = []
    commands = iter(["Improve things please", "Focus on readability", "/exit"])
    output: list[str] = []

    InteractiveSession(
        tmp_path,
        ClarifyingClient(),
        input_fn=lambda prompt: prompts.append(prompt) or next(commands),
        output_fn=output.append,
    ).run()

    assert prompts[0] == "CASI> "
    assert prompts[1] == "Answer (/plan, /cancel)> "
    assert prompts[2] == "CASI> "
    assert any("[pending] Reply to continue" in message for message in output)


def test_interactive_session_skips_clarification_for_fix_requests(tmp_path: Path) -> None:
    commands = iter(["Fix email validation", "y", "/exit"])
    output: list[str] = []

    InteractiveSession(
        tmp_path,
        ClarifyingClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    ).run()

    assert not any("Reply at Answer>" in message for message in output)
    assert "[agent] I will inspect the email validator." in output


def test_interactive_session_can_exit_during_clarification(tmp_path: Path) -> None:
    commands = iter(["Improve things please", "/exit"])
    output: list[str] = []

    InteractiveSession(
        tmp_path,
        ClarifyingClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    ).run()

    assert "Session ended." in output


def test_interactive_plan_request_does_not_consume_pending_answer(tmp_path: Path) -> None:
    prompts: list[str] = []
    commands = iter([
        "Improve things please",
        "dime el plan",
        "Focus on readability",
        "/exit",
    ])
    output: list[str] = []

    InteractiveSession(
        tmp_path,
        ClarifyingClient(),
        input_fn=lambda prompt: prompts.append(prompt) or next(commands),
        output_fn=output.append,
    ).run()

    assert prompts.count("Answer (/plan, /cancel)> ") == 2
    assert "[plan] Current plan:" in output
    assert any("I will inspect the email validator." in message for message in output)


def test_interactive_cancel_discards_pending_clarification(tmp_path: Path) -> None:
    commands = iter(["Improve things please", "/cancel", "/exit"])
    output: list[str] = []

    InteractiveSession(
        tmp_path,
        ClarifyingClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    ).run()

    assert "[pending] Pending task cancelled. You can enter a new request." in output


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
            "-value = False\n"
            "+value = True\n"
            "```"
        )


def test_interactive_session_rejects_patch_without_changes(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "app.py").write_text("value = False\n", encoding="utf-8")
    (repository / "test_app.py").write_text(
        "from app import value\n\ndef test_value():\n    assert value is True\n",
        encoding="utf-8",
    )
    commands = iter(["Fix app.py", "y", "n", "/exit"])
    output: list[str] = []

    InteractiveSession(
        repository,
        PatchClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    ).run()

    assert (repository / "app.py").read_text(encoding="utf-8") == "value = False\n"
    assert "Patch rejected; no files were changed." in output


def test_interactive_session_shows_context_command(tmp_path: Path) -> None:
	commands = iter(["First task", "/context", "/exit"])
	output: list[str] = []

	InteractiveSession(
		tmp_path,
		FakeClient(),
		input_fn=lambda prompt: next(commands),
		output_fn=output.append,
	).run()

	assert any("Hilo activo:" in message for message in output)
	assert any("[user] First task" in message for message in output)


def test_interactive_session_runs_manual_compact(tmp_path: Path) -> None:
	class SummarizeClient:
		def __init__(self) -> None:
			self.calls = 0

		def complete(self, messages, tools):
			self.calls += 1
			if self.calls == 1:
				return LLMResponse.final("Task completed")
			return LLMResponse.final("Resumen manual.")

	commands = iter(["First task", "/compact Conserva errores de tests", "/exit"])
	output: list[str] = []

	InteractiveSession(
		tmp_path,
		SummarizeClient(),
		input_fn=lambda prompt: next(commands),
		output_fn=output.append,
	).run()

	assert any("Resumen aplicado" in message for message in output)
	assert any("[resumen]" in message for message in output)


def test_interactive_session_warns_when_context_is_large(tmp_path: Path) -> None:
	class ManyTurnClient:
		def __init__(self) -> None:
			self.turn = 0

		def complete(self, messages, tools):
			self.turn += 1
			return LLMResponse.final(f"done-{self.turn}")

	commands = iter(["Task one", "Task two", "/exit"])
	output: list[str] = []

	original_limit = settings.max_context_messages
	original_ratio = settings.context_compact_warn_ratio
	try:
		object.__setattr__(settings, "max_context_messages", 100)
		object.__setattr__(settings, "context_compact_warn_ratio", 0.02)
		InteractiveSession(
			tmp_path,
			ManyTurnClient(),
			input_fn=lambda prompt: next(commands),
			output_fn=output.append,
		).run()
	finally:
		object.__setattr__(settings, "max_context_messages", original_limit)
		object.__setattr__(settings, "context_compact_warn_ratio", original_ratio)

	assert any("/context para revisarlo" in message for message in output)


def test_interactive_session_applies_approved_patch(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "app.py").write_text("value = False\n", encoding="utf-8")
    (repository / "test_app.py").write_text(
        "from app import value\n\ndef test_value():\n    assert value is True\n",
        encoding="utf-8",
    )
    commands = iter(["Fix app.py", "y", "y", "/exit"])
    output: list[str] = []

    InteractiveSession(
        repository,
        PatchClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
    ).run()

    assert (repository / "app.py").read_text(encoding="utf-8") == "value = True\n"
    assert any("Patch applied to" in message for message in output)


def test_interactive_session_saves_last_trace(tmp_path: Path) -> None:
    output: list[str] = []
    session = InteractiveSession(tmp_path, FakeClient(), output_fn=output.append)
    session._last_trace = ["decision 1/2: tool run_tests", "  -> run_tests failed"]
    target = tmp_path / "diagnostics" / "trace.json"

    should_exit = session._handle_command(f"/save-trace {target}")
    payload = json.loads(target.read_text(encoding="utf-8"))

    assert should_exit is False
    assert [event["message"] for event in payload["events"]] == session._last_trace
    assert any("Saved diagnostic trace" in message for message in output)
