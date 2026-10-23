from __future__ import annotations

from pathlib import Path

from casi.interactive import InteractiveSession
from casi.llm.base import ChatMessage, LLMResponse, ToolDefinition
from casi.terminal import TerminalPresenter, Theme, render_panel, strip_ansi


class DummyClient:
    model = "test-model"
    provider_name = "test-provider"

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        return LLMResponse.final("Ok")


def test_strip_ansi() -> None:
    assert strip_ansi("\033[96mHello\033[0m") == "Hello"
    assert strip_ansi("\001\033[1m\002Title\001\033[0m\002") == "Title"
    assert strip_ansi("Plain text") == "Plain text"


def test_render_panel_unicode() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    lines = ["Line 1", "Line 2 is longer"]
    panel = render_panel(lines, title="Test", subtitle="v1.0", theme=theme)

    assert "╭─ Test" in panel
    assert "v1.0 ─╮" in panel
    assert "│ Line 1" in panel
    assert "│ Line 2 is longer" in panel
    assert panel.endswith("╯")


def test_render_panel_ascii() -> None:
    theme = Theme(use_color=False, use_unicode=False)
    lines = ["Alpha", "Beta"]
    panel = render_panel(lines, title="Box", theme=theme)

    assert "+- Box" in panel
    assert "| Alpha" in panel
    assert panel.endswith("+")


def test_presenter_welcome_banner_and_status_card() -> None:
    output: list[str] = []
    theme = Theme(use_color=False, use_unicode=True)
    presenter = TerminalPresenter(output_fn=output.append, theme=theme)

    presenter.welcome_banner(
        repository="/tmp/dummy",
        model="qwen-test",
        provider="ollama",
        routing_mode="assist",
    )
    assert any("CASI" in line for line in output)
    assert any("dummy" in line for line in output)
    assert any("qwen-test" in line for line in output)

    presenter.status_card({"Model": "qwen-test", "Sandbox": "Docker"})
    assert any("System Status" in line for line in output)
    assert any("qwen-test" in line for line in output)


def test_interactive_status_command(tmp_path: Path) -> None:
    commands = iter(["/status", "/exit"])
    output: list[str] = []
    theme = Theme(use_color=False, use_unicode=True)
    presenter = TerminalPresenter(output_fn=output.append, theme=theme)

    session = InteractiveSession(
        tmp_path,
        DummyClient(),
        input_fn=lambda prompt: next(commands),
        output_fn=output.append,
        presenter=presenter,
    )

    exit_code = session.run()
    assert exit_code == 0
    assert any("System Status" in line for line in output)
    assert any("test-model" in line for line in output)
    assert any("test-provider" in line for line in output)


def test_presenter_prompt() -> None:
    theme_colored = Theme(use_color=True, use_unicode=True)
    presenter_colored = TerminalPresenter(theme=theme_colored)
    p_colored = presenter_colored.prompt()
    assert "casi" in p_colored
    assert "❯" in p_colored

    p_clarify = presenter_colored.prompt(status="clarify")
    assert "clarify" in p_clarify

    theme_ascii = Theme(use_color=False, use_unicode=False)
    presenter_ascii = TerminalPresenter(theme=theme_ascii)
    assert presenter_ascii.prompt() == "casi> "
    assert presenter_ascii.prompt(status="clarify") == "casi [clarify]> "
