"""Unit tests for repository test-command detection."""

from __future__ import annotations

from pathlib import Path

from casi.sandbox.test_command import detect_test_command


def test_detect_test_command_defaults_to_pytest(tmp_path: Path) -> None:
    command = detect_test_command(tmp_path, runner="local")

    assert command[1:3] == ["-m", "pytest"]


def test_detect_test_command_reads_casi_override(tmp_path: Path) -> None:
    override_dir = tmp_path / ".casi"
    override_dir.mkdir()
    (override_dir / "test-command").write_text(
        "python -m pytest -q tests/\n", encoding="utf-8"
    )

    command = detect_test_command(tmp_path, runner="local")

    assert command[-1] == "tests/"


def test_detect_test_command_uses_makefile_test_target(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(
        "test:\n\tpython -m pytest -q\n", encoding="utf-8"
    )

    command = detect_test_command(tmp_path, runner="local")

    assert command[:2] == ["make", "test"]
