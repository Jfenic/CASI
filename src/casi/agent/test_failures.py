"""Helpers for extracting repository paths from pytest output."""

from __future__ import annotations

import re

_FAILURE_PATH_PATTERNS = (
	re.compile(r"^([^\s:]+\.py):\d+:", re.MULTILINE),
	re.compile(r'File "([^"]+\.py)", line \d+'),
	re.compile(r"\bFAILED ([\w./-]+\.py)::"),
	re.compile(r"\bin ([\w./-]+\.py):\d+\b"),
)


def extract_failure_paths(test_output: str) -> list[str]:
	"""Return repository-relative paths mentioned in a pytest failure report."""

	paths: list[str] = []
	for pattern in _FAILURE_PATH_PATTERNS:
		for match in pattern.finditer(test_output):
			path = match.group(1).strip().lstrip("./")
			if path and path not in paths:
				paths.append(path)
	return paths
