"""Local process runner with timeout and output limits."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from casi.repository.security import resolve_repository
from casi.sandbox.base import TestResult


class LocalRunner:
    """Run an explicit command inside a resolved repository directory."""

    def __init__(self, *, max_output_chars: int = 20_000) -> None:
        if max_output_chars < 1:
            raise ValueError("max_output_chars must be greater than or equal to 1")
        self.max_output_chars = max_output_chars

    def run(
        self,
        repository: str | Path,
        command: list[str],
        *,
        timeout_seconds: float = 120,
    ) -> TestResult:
        if not command:
            raise ValueError("command must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0")

        root = resolve_repository(repository)
        started_at = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return TestResult(
                command=command,
                exit_code=-1,
                stdout=self._limit_output(exc.stdout),
                stderr=self._limit_output(exc.stderr),
                duration_seconds=time.monotonic() - started_at,
                timed_out=True,
            )

        return TestResult(
            command=command,
            exit_code=completed.returncode,
            stdout=self._limit_output(completed.stdout),
            stderr=self._limit_output(completed.stderr),
            duration_seconds=time.monotonic() - started_at,
        )

    def _limit_output(self, output: str | bytes | None) -> str:
        if output is None:
            return ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        if len(output) <= self.max_output_chars:
            return output
        return output[: self.max_output_chars] + "\n[output truncated]"
