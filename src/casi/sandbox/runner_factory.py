"""Select the sandbox runner used for test execution."""

from __future__ import annotations

from typing import Literal

from casi.config import settings
from casi.sandbox.docker_runner import DockerRunner
from casi.sandbox.local_runner import LocalRunner

RunnerKind = Literal["docker", "local"]


def resolve_test_runner(
	*,
	prefer_docker: bool | None = None,
) -> tuple[LocalRunner | DockerRunner, RunnerKind]:
	"""Return a sandbox runner, preferring Docker when configured and available."""

	use_docker = settings.use_docker_sandbox if prefer_docker is None else prefer_docker
	if use_docker:
		docker_runner = DockerRunner(max_output_chars=settings.max_command_output_chars)
		if docker_runner.is_available() and docker_runner.image_exists():
			return docker_runner, "docker"

	return LocalRunner(max_output_chars=settings.max_command_output_chars), "local"
