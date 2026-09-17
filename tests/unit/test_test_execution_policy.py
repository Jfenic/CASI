"""Additional tests for repository test execution policy."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from casi.agent.failure_classification import FailureKind, TestExecutionError
from casi.config import settings
from casi.sandbox.base import TestResult
from casi.sandbox.test_execution import run_repository_tests


@pytest.mark.parametrize("available,image_exists", [(False, True), (True, False)])
@pytest.mark.parametrize("allow_fallback", [False, True])
def test_unavailable_sandbox_respects_explicit_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    available: bool,
    image_exists: bool,
    allow_fallback: bool,
) -> None:
    monkeypatch.setattr(
        "casi.sandbox.runner_factory.settings",
        replace(
            settings, use_docker_sandbox=True, allow_local_test_fallback=allow_fallback
        ),
    )
    monkeypatch.setattr(
        "casi.sandbox.runner_factory.project_image_if_available", lambda _: None
    )
    monkeypatch.setattr(
        "casi.sandbox.runner_factory.DockerRunner.is_available",
        lambda _: available,
    )
    monkeypatch.setattr(
        "casi.sandbox.runner_factory.DockerRunner.image_exists",
        lambda _: image_exists,
    )
    calls = []

    def local_run(self, repository, command, **kwargs):
        calls.append(command)
        return TestResult(command, 0, "passed", "", 0.1)

    monkeypatch.setattr("casi.sandbox.local_runner.LocalRunner.run", local_run)
    if allow_fallback:
        result, kind = run_repository_tests(tmp_path, timeout_seconds=5)
        assert kind == "local"
        assert result.exit_code == 0
        assert len(calls) == 1
    else:
        with pytest.raises(TestExecutionError) as exc_info:
            run_repository_tests(tmp_path, timeout_seconds=5)
        assert exc_info.value.failure_kind is FailureKind.DOCKER
        assert calls == []


def test_explicit_local_execution_works_with_fallback_disabled(monkeypatch) -> None:
    from casi.sandbox.runner_factory import resolve_test_runner

    monkeypatch.setattr(
        "casi.sandbox.runner_factory.settings",
        replace(settings, allow_local_test_fallback=False),
    )
    _, kind = resolve_test_runner(prefer_docker=False)
    assert kind == "local"


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
