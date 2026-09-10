"""Run repository test commands with runner selection and fallback."""

from __future__ import annotations

from pathlib import Path

from casi.agent.failure_classification import (
    FailureKind,
    TestExecutionError,
    failure_kind_label,
    is_docker_infrastructure_failure,
)
from casi.config import settings
from casi.sandbox.base import TestResult
from casi.sandbox.docker_runner import DockerRunner
from casi.sandbox.local_runner import LocalRunner
from casi.sandbox.runner_factory import RunnerKind, resolve_test_runner
from casi.sandbox.test_command import detect_test_command


def run_repository_tests(
    repository: str | Path,
    *,
    timeout_seconds: float,
    prefer_docker: bool | None = None,
    workspace: str | Path | None = None,
) -> tuple[TestResult, RunnerKind]:
    """Run the repository test command, preferring Docker with optional fallback."""

    target = workspace if workspace is not None else repository
    runner, runner_kind = resolve_test_runner(
        repository=repository,
        prefer_docker=prefer_docker,
    )
    command = detect_test_command(target, runner=runner_kind)

    if workspace is not None and isinstance(runner, DockerRunner):
        result = runner.run_in_workspace(
            workspace,
            command,
            timeout_seconds=timeout_seconds,
        )
    else:
        result = runner.run(target, command, timeout_seconds=timeout_seconds)

    if runner_kind == "docker" and is_docker_infrastructure_failure(result):
        if not settings.allow_local_test_fallback:
            kind = FailureKind.DOCKER
            raise TestExecutionError(
                (
                    f"Docker sandbox failed ({failure_kind_label(kind)}). "
                    "Local fallback is disabled; fix Docker or set "
                    "LOCALCODE_AGENT_ALLOW_LOCAL_FALLBACK=true."
                ),
                failure_kind=kind,
            )
        local_runner = LocalRunner(max_output_chars=settings.max_command_output_chars)
        local_command = detect_test_command(target, runner="local")
        result = local_runner.run(
            target, local_command, timeout_seconds=timeout_seconds
        )
        runner_kind = "local"

    return result, runner_kind


def run_repository_pytest(
    repository: str | Path,
    *,
    timeout_seconds: float,
    prefer_docker: bool | None = None,
    workspace: str | Path | None = None,
) -> tuple[TestResult, RunnerKind]:
    """Backward-compatible alias for repository test execution."""

    return run_repository_tests(
        repository,
        timeout_seconds=timeout_seconds,
        prefer_docker=prefer_docker,
        workspace=workspace,
    )
