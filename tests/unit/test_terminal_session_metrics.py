from __future__ import annotations

from casi.terminal.session_metrics import SessionMetrics, format_session_summary
from casi.terminal.theme import Theme


def test_session_metrics_recording() -> None:
    metrics = SessionMetrics()
    metrics.record_turn()
    metrics.record_step()
    metrics.record_step()
    metrics.record_tool_call("read_file")
    metrics.record_tool_call("read_file")
    metrics.record_tool_call("run_tests")
    metrics.record_patch_proposed()
    metrics.record_patch_applied(["app.py", "models.py"])

    assert metrics.turns_completed == 1
    assert metrics.total_steps == 2
    assert metrics.patches_proposed == 1
    assert metrics.patches_applied == 1
    assert metrics.patches_undone == 0
    assert metrics.tool_counts == {"read_file": 2, "run_tests": 1}
    assert metrics.modified_files == {"app.py", "models.py"}


def test_session_metrics_undo_tracking() -> None:
    metrics = SessionMetrics()
    metrics.record_patch_applied(["app.py", "models.py"])
    assert metrics.modified_files == {"app.py", "models.py"}

    metrics.record_patch_undone(["models.py"])
    assert metrics.patches_undone == 1
    assert metrics.modified_files == {"app.py"}


def test_session_metrics_duration_formatting() -> None:
    metrics = SessionMetrics()
    metrics.start_time = 100.0

    formatted = metrics.format_duration()
    assert isinstance(formatted, str)


def test_session_metrics_format_summary() -> None:
    metrics = SessionMetrics()
    metrics.record_turn()
    metrics.record_step()
    metrics.record_tool_call("search_code")
    metrics.record_patch_proposed()
    metrics.record_patch_applied(["main.py"])

    theme = Theme(use_color=False, use_unicode=True)
    summary = format_session_summary(metrics, theme=theme)

    assert "Session summary" in summary
    assert "Tasks completed: 1" in summary
    assert "Agent steps: 1" in summary
    assert "Patches: 1 proposed, 1 applied, 0 undone" in summary
    assert "Files modified: main.py" in summary
    assert "Tools executed: 1 (search_code: 1)" in summary


def test_session_metrics_empty_format() -> None:
    metrics = SessionMetrics()
    theme = Theme(use_color=False, use_unicode=False)
    summary = metrics.format_summary(theme=theme)

    assert "Session summary" in summary
    assert "Tasks completed: 0" in summary
    assert "Files modified: none" in summary
    assert "Tools executed: 0" in summary
