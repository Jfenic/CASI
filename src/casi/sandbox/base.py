"""Process runner abstractions and structured results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TestResult:
	command: list[str]
	exit_code: int
	stdout: str
	stderr: str
	duration_seconds: float
	timed_out: bool = False
