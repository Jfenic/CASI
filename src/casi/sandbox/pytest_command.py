"""Shared pytest invocation for repository sandboxes."""

from __future__ import annotations

import sys
from pathlib import Path


def pytest_command(repository: str | Path) -> list[str]:
	"""Build a pytest command scoped to a single repository directory."""

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
