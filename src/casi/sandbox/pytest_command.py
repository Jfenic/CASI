"""Shared pytest invocation for repository sandboxes."""

from __future__ import annotations

import sys
from pathlib import Path

from casi.sandbox.runner_factory import RunnerKind

DOCKER_WORKSPACE = "/workspace"


def pytest_command(repository: str | Path, *, runner: RunnerKind = "local") -> list[str]:
	"""Build a pytest command scoped to a repository directory."""

	if runner == "docker":
		return [
			"python3",
			"-m",
			"pytest",
			"-q",
			"--rootdir",
			DOCKER_WORKSPACE,
			DOCKER_WORKSPACE,
		]

	root = Path(repository).expanduser().resolve()
	return [
		sys.executable,
		"-m",
		"pytest",
		"-q",
		"--rootdir",
		str(root),
		str(root),
	]
