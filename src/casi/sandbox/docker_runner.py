"""Docker-based sandbox runner."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from casi.config import settings
from casi.repository.security import resolve_repository
from casi.sandbox.base import TestResult
from casi.sandbox.project_environment import ignore_sandbox_files


class DockerRunner:
	"""Run commands inside an isolated Docker container on a repository copy."""

	def __init__(
		self,
		*,
		image: str | None = None,
		memory: str | None = None,
		cpus: str | None = None,
		max_output_chars: int | None = None,
	) -> None:
		self.image = image or settings.docker_image
		self.memory = memory or settings.docker_memory
		self.cpus = cpus or settings.docker_cpus
		self.max_output_chars = max_output_chars or settings.max_command_output_chars

	def is_available(self) -> bool:
		"""Return whether Docker is installed and reachable."""

		if shutil.which("docker") is None:
			return False
		result = subprocess.run(
			["docker", "info"],
			capture_output=True,
			text=True,
			check=False,
		)
		return result.returncode == 0

	def image_exists(self) -> bool:
		"""Return whether the configured sandbox image is present locally."""

		result = subprocess.run(
			["docker", "image", "inspect", self.image],
			capture_output=True,
			text=True,
			check=False,
		)
		return result.returncode == 0

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
		if not self.is_available():
			raise RuntimeError("Docker is not available")

		root = resolve_repository(repository)
		with tempfile.TemporaryDirectory(
			prefix="casi-sandbox-",
			ignore_cleanup_errors=True,
		) as temp_dir:
			workspace = Path(temp_dir) / "workspace"
			shutil.copytree(
				root,
				workspace,
				ignore=ignore_sandbox_files,
				dirs_exist_ok=True,
			)
			return self.run_in_workspace(
				workspace,
				command,
				timeout_seconds=timeout_seconds,
			)

	def run_in_workspace(
		self,
		workspace: str | Path,
		command: list[str],
		*,
		timeout_seconds: float = 120,
	) -> TestResult:
		"""Run a command inside Docker against an existing workspace directory."""

		if not command:
			raise ValueError("command must not be empty")
		if timeout_seconds <= 0:
			raise ValueError("timeout_seconds must be greater than 0")
		if not self.is_available():
			raise RuntimeError("Docker is not available")

		root = Path(workspace).expanduser().resolve()
		if not root.is_dir():
			raise ValueError(f"workspace does not exist: {root}")

		started_at = time.monotonic()
		docker_command = [
			"docker",
			"run",
			"--rm",
			"--network",
			"none",
			"--memory",
			self.memory,
			"--cpus",
			self.cpus,
			"--pids-limit",
			str(settings.docker_pids_limit),
			"--cap-drop",
			"ALL",
			"--security-opt",
			"no-new-privileges",
			*self._user_flags(),
			"-v",
			f"{root}:/workspace:rw",
			"-w",
			"/workspace",
			self.image,
			*command,
		]

		try:
			completed = subprocess.run(
				docker_command,
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

	def _user_flags(self) -> list[str]:
		"""Run the container as the current user so workspace files stay deletable."""

		if not hasattr(os, "getuid") or not hasattr(os, "getgid"):
			return []
		return ["--user", f"{os.getuid()}:{os.getgid()}"]

	def _limit_output(self, output: str | bytes | None) -> str:
		if output is None:
			return ""
		if isinstance(output, bytes):
			output = output.decode("utf-8", errors="replace")
		if len(output) <= self.max_output_chars:
			return output
		return output[: self.max_output_chars] + "\n[output truncated]"
