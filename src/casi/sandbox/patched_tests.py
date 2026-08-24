"""Run tests against a temporary copy of the repository with a patch applied."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from casi.config import settings
from casi.patching.applier import PatchApplicationError
from casi.patching.validator import validate_patch
from casi.repository.security import resolve_repository
from casi.sandbox.base import TestResult
from casi.sandbox.docker_runner import DockerRunner
from casi.sandbox.pytest_command import pytest_command
from casi.sandbox.runner_factory import RunnerKind, resolve_test_runner

_COPY_IGNORE = shutil.ignore_patterns(".git", ".venv", "__pycache__")


def run_patched_tests(
	repository: str | Path,
	patch: str,
	*,
	timeout_seconds: float | None = None,
	prefer_docker: bool | None = None,
) -> tuple[TestResult, RunnerKind]:
	"""Apply a patch to a repository copy and run pytest in an isolated workspace."""

	validation = validate_patch(repository, patch)
	if not validation.valid:
		raise ValueError(validation.error or "Patch is invalid")

	timeout = timeout_seconds or settings.test_timeout_seconds
	root = resolve_repository(repository)
	command = pytest_command(root)

	with tempfile.TemporaryDirectory(prefix="casi-patched-") as temp_dir:
		workspace = Path(temp_dir) / "workspace"
		shutil.copytree(root, workspace, ignore=_COPY_IGNORE, dirs_exist_ok=True)

		apply_result = subprocess.run(
			["git", "apply", "--whitespace=error-all", "-"],
			cwd=workspace,
			input=patch,
			capture_output=True,
			text=True,
			check=False,
		)
		if apply_result.returncode != 0:
			raise PatchApplicationError(
				apply_result.stderr.strip() or "Patch application failed"
			)

		runner, runner_kind = resolve_test_runner(prefer_docker=prefer_docker)
		if isinstance(runner, DockerRunner):
			result = runner.run_in_workspace(
				workspace,
				command,
				timeout_seconds=timeout,
			)
		else:
			result = runner.run(workspace, command, timeout_seconds=timeout)
		return result, runner_kind
