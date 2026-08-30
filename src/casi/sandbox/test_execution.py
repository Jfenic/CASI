"""Run repository pytest commands with runner selection and fallback."""

from __future__ import annotations

from pathlib import Path

from casi.config import settings
from casi.sandbox.base import TestResult
from casi.sandbox.docker_runner import DockerRunner
from casi.sandbox.local_runner import LocalRunner
from casi.sandbox.pytest_command import pytest_command
from casi.sandbox.runner_factory import RunnerKind, resolve_test_runner


def is_docker_infrastructure_failure(result: TestResult) -> bool:
	"""Return whether Docker failed before pytest could run meaningfully."""

	if result.exit_code == 127:
		return True
	combined = f"{result.stdout}\n{result.stderr}"
	return "No module named pytest" in combined


def run_repository_pytest(
	repository: str | Path,
	*,
	timeout_seconds: float,
	prefer_docker: bool | None = None,
	workspace: str | Path | None = None,
) -> tuple[TestResult, RunnerKind]:
	"""Run pytest in a repository, preferring Docker with local fallback."""

	runner, runner_kind = resolve_test_runner(prefer_docker=prefer_docker)
	target = workspace if workspace is not None else repository
	command = pytest_command(target, runner=runner_kind)

	if workspace is not None and isinstance(runner, DockerRunner):
		result = runner.run_in_workspace(
			workspace,
			command,
			timeout_seconds=timeout_seconds,
		)
	else:
		result = runner.run(target, command, timeout_seconds=timeout_seconds)

	if runner_kind == "docker" and is_docker_infrastructure_failure(result):
		local_runner = LocalRunner(max_output_chars=settings.max_command_output_chars)
		local_command = pytest_command(target, runner="local")
		result = local_runner.run(target, local_command, timeout_seconds=timeout_seconds)
		runner_kind = "local"

	return result, runner_kind
