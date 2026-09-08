"""Detect how a repository expects its test suite to be executed."""

from __future__ import annotations

import shlex
from pathlib import Path

from casi.sandbox.pytest_command import DOCKER_WORKSPACE, pytest_command
from casi.sandbox.runner_factory import RunnerKind


def _adapt_command_for_runner(command: list[str], runner: RunnerKind) -> list[str]:
	"""Return a docker-friendly command when the runner executes inside a container."""

	if runner != "docker":
		return command
	if command[:3] == ["python3", "-m", "pytest"] or command[:2] == ["pytest"]:
		return pytest_command(DOCKER_WORKSPACE, runner="docker")
	return command


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
				return _adapt_command_for_runner(shlex.split(stripped), runner)

	makefile = root / "Makefile"
	if makefile.is_file() and _makefile_has_test_target(makefile.read_text(encoding="utf-8")):
		return _adapt_command_for_runner(["make", "test"], runner)

	return pytest_command(root, runner=runner)


def _makefile_has_test_target(content: str) -> bool:
	for line in content.splitlines():
		stripped = line.strip()
		if stripped.startswith("test:") or stripped == "test":
			return True
	return False
