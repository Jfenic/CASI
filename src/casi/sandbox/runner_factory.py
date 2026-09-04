"""Select the sandbox runner used for test execution."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from casi.config import settings
from casi.sandbox.docker_runner import DockerRunner
from casi.sandbox.local_runner import LocalRunner
from casi.sandbox.project_environment import project_image_if_available

RunnerKind = Literal["docker", "local"]


def resolve_test_runner(
	*,
	repository: str | Path | None = None,
	prefer_docker: bool | None = None,
) -> tuple[LocalRunner | DockerRunner, RunnerKind]:
	"""Return a sandbox runner, preferring Docker when configured and available."""

	use_docker = settings.use_docker_sandbox if prefer_docker is None else prefer_docker
	if use_docker:
		project_image = (
			project_image_if_available(repository) if repository is not None else None
		)
		docker_runner = DockerRunner(
			image=project_image or settings.docker_image,
			max_output_chars=settings.max_command_output_chars,
		)
		if docker_runner.is_available() and docker_runner.image_exists():
			return docker_runner, "docker"

	return LocalRunner(max_output_chars=settings.max_command_output_chars), "local"
