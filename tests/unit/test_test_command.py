"""Unit tests for repository test-command detection."""

from __future__ import annotations

from pathlib import Path

import pytest

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


@pytest.mark.parametrize(
    "executable", ["pytest", "python", "python3", ".venv/bin/python3.12"]
)
def test_docker_override_preserves_selection_and_options(
    tmp_path: Path, executable: str
) -> None:
    override = tmp_path / ".casi"
    override.mkdir()
    prefix = executable if executable == "pytest" else f"{executable} -m pytest"
    (override / "test-command").write_text(
        f"{prefix} -q -k regression tests/unit --maxfail=2\n"
    )

    assert detect_test_command(tmp_path, runner="docker") == [
        "python3",
        "-m",
        "pytest",
        "-q",
        "-k",
        "regression",
        "tests/unit",
        "--maxfail=2",
    ]


def test_docker_override_maps_absolute_repository_paths(tmp_path: Path) -> None:
    override = tmp_path / ".casi"
    override.mkdir()
    (override / "test-command").write_text(
        f"python3 -m pytest --rootdir={tmp_path} "
        f"{tmp_path}/checks/cart_test.py::test_total\n"
    )
    assert detect_test_command(tmp_path, runner="docker") == [
        "python3",
        "-m",
        "pytest",
        "--rootdir=/workspace",
        "/workspace/checks/cart_test.py::test_total",
    ]
