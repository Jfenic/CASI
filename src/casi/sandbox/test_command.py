"""Detect how a repository expects its test suite to be executed."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

from casi.sandbox.pytest_command import DOCKER_WORKSPACE, pytest_command
from casi.sandbox.runner_factory import RunnerKind


def _adapt_command_for_runner(
    command: list[str], runner: RunnerKind, *, repository: Path | None = None
) -> list[str]:
    """Return a docker-friendly command when the runner executes inside a container."""

    if runner != "docker":
        return command
    if repository is not None:
        command = [
            _adapt_repository_argument(argument, repository) for argument in command
        ]
    if command and Path(command[0]).name == "pytest":
        return ["python3", "-m", "pytest", *command[1:]]
    if (
        len(command) >= 3
        and re.fullmatch(r"python(?:\d+(?:\.\d+)*)?", Path(command[0]).name)
        and command[1:3] == ["-m", "pytest"]
    ):
        return ["python3", *command[1:]]
    return command


def _adapt_repository_argument(argument: str, repository: Path) -> str:
    """Map absolute repository paths while retaining flags and pytest node IDs."""

    flag, separator, value = argument.partition("=")
    value = value if separator else argument
    path, node_separator, node_id = value.partition("::")
    if not Path(path).is_absolute():
        return argument
    try:
        relative = Path(path).relative_to(repository)
    except ValueError:
        return argument
    mapped = (Path(DOCKER_WORKSPACE) / relative).as_posix()
    if node_separator:
        mapped += node_separator + node_id
    return flag + separator + mapped if separator else mapped


def detect_test_command(
    repository: str | Path,
    *,
    runner: RunnerKind = "local",
) -> list[str]:
    """Detect the preferred test command for a repository."""

    root = Path(repository).expanduser().resolve()
    override = root / ".casi" / "test-command"
    if override.is_file():
        for line in override.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return _adapt_command_for_runner(
                    shlex.split(stripped), runner, repository=root
                )

    makefile = root / "Makefile"
    if makefile.is_file() and _makefile_has_test_target(
        makefile.read_text(encoding="utf-8")
    ):
        return _adapt_command_for_runner(["make", "test"], runner, repository=root)

    return pytest_command(root, runner=runner)


def _makefile_has_test_target(content: str) -> bool:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("test:") or stripped == "test":
            return True
    return False
