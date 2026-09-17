from __future__ import annotations

from casi.terminal.presenter import TerminalPresenter
from casi.terminal.theme import Theme


def test_presenter_user_and_agent() -> None:
    output: list[str] = []
    theme = Theme(use_color=False, use_unicode=True)
    presenter = TerminalPresenter(output_fn=output.append, theme=theme)

    presenter.user("Hello agent")
    presenter.agent("Hello user")

    assert output[0] == "› Hello agent"
    assert output[1] == "◆ Hello user"


def test_presenter_success_and_error_with_hint() -> None:
    output: list[str] = []
    theme = Theme(use_color=False, use_unicode=True)
    presenter = TerminalPresenter(output_fn=output.append, theme=theme)

    presenter.success("All tests passed")
    presenter.error("Command failed", hint="Check dependencies in pyproject.toml")

    assert output[0] == "✓ All tests passed"
    assert output[1] == "✗ Command failed"
    assert "[💡]" in output[2]
    assert "Check dependencies" in output[2]


def test_presenter_plan_and_step() -> None:
    output: list[str] = []
    theme = Theme(use_color=False, use_unicode=True)
    presenter = TerminalPresenter(output_fn=output.append, theme=theme)

    presenter.plan("Fix bug", ["Read files", "Apply patch", "Run tests"])
    presenter.step_start(1, 3, "explorer", "inspect code")

    assert any("Fix bug" in line for line in output)
    assert any("├─ Read files" in line for line in output)
    assert any("└─ Run tests" in line for line in output)
    assert any("Step 1/3: explorer (inspect code)" in line for line in output)


def test_presenter_tool_call() -> None:
    output: list[str] = []
    theme = Theme(use_color=False, use_unicode=True)
    presenter = TerminalPresenter(output_fn=output.append, theme=theme)

    presenter.tool_call("read_file", summary="src/main.py (50 lines)")
    assert any(
        "read_file" in line and "(src/main.py (50 lines))" in line for line in output
    )


def test_presenter_confirm() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    presenter = TerminalPresenter(theme=theme)

    assert presenter.confirm("Apply?", input_fn=lambda _: "y") is True
    assert presenter.confirm("Apply?", input_fn=lambda _: "n") is False
    assert presenter.confirm("Apply?", default=True, input_fn=lambda _: "") is True
    assert presenter.confirm("Apply?", default=False, input_fn=lambda _: "") is False
