"""Additional tests for repository test execution policy."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from casi.agent.failure_classification import FailureKind, TestExecutionError
from casi.config import settings
from casi.sandbox.base import TestResult
from casi.sandbox.test_execution import run_repository_tests


def test_run_repository_tests_raises_when_docker_fails_without_fallback(
	tmp_path: Path,
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	(tmp_path / "test_sample.py").write_text(
		"def test_ok():\n    assert True\n",
		encoding="utf-8",
	)

	class FailingDockerRunner:
		def run(self, repository, command, *, timeout_seconds):
			return TestResult(
				command=command,
				exit_code=127,
				stdout="",
				stderr="python3: not found",
				duration_seconds=0.1,
			)

	monkeypatch.setattr(
		"casi.sandbox.test_execution.resolve_test_runner",
		lambda **kwargs: (FailingDockerRunner(), "docker"),
	)
	monkeypatch.setattr(
		"casi.sandbox.test_execution.settings",
		replace(settings, allow_local_test_fallback=False),
	)

	with pytest.raises(TestExecutionError) as exc_info:
		run_repository_tests(tmp_path, timeout_seconds=5)

	assert exc_info.value.failure_kind is FailureKind.DOCKER
