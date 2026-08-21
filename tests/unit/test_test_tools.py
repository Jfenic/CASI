from __future__ import annotations

import sys
from pathlib import Path

from casi.sandbox.local_runner import LocalRunner
from casi.tools.registry import ToolRegistry


def test_run_tests_tool_reports_passing_tests(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_passes():\n    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )

    result = ToolRegistry(tmp_path).execute("run_tests", {})

    assert result.success is True
    assert result.metadata["exit_code"] == 0
    assert result.metadata["timed_out"] is False


def test_run_tests_tool_reports_failing_tests(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_fails():\n    assert False\n",
        encoding="utf-8",
    )

    result = ToolRegistry(tmp_path).execute("run_tests", {})

    assert result.success is False
    assert result.metadata["exit_code"] != 0
    assert "failed" in result.output.lower()


def test_local_runner_handles_timeout(tmp_path: Path) -> None:
    result = LocalRunner().run(
        tmp_path,
        [sys.executable, "-c", "import time; time.sleep(1)"],
        timeout_seconds=0.05,
    )

    assert result.timed_out is True
    assert result.exit_code == -1


def test_local_runner_truncates_output(tmp_path: Path) -> None:
    result = LocalRunner(max_output_chars=10).run(
        tmp_path,
        [sys.executable, "-c", "print('a' * 100)"],
    )

    assert result.stdout.endswith("[output truncated]")
    assert len(result.stdout) > 10