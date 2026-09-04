"""Prepare reproducible Docker environments for Python repositories."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from casi.repository.security import resolve_repository
from casi.repository.security import BLOCKED_NAMES, BLOCKED_SUFFIXES

_DEPENDENCY_FILES = (
	"uv.lock",
	"poetry.lock",
	"requirements.txt",
	"requirements-dev.txt",
	"pyproject.toml",
	"setup.cfg",
	"setup.py",
)
_COPY_EXCLUDES = {
	".git",
	".hg",
	".svn",
	".venv",
	"venv",
	"env",
	"__pycache__",
	".pytest_cache",
	".mypy_cache",
	".ruff_cache",
	"node_modules",
	"dist",
	"build",
}


@dataclass(frozen=True)
class ProjectEnvironment:
	"""Detected dependency strategy and its content-addressed image name."""

	manager: str
	dependency_files: tuple[str, ...]
	image: str


@dataclass(frozen=True)
class EnvironmentBuildResult:
	"""Result of building a project environment image."""

	success: bool
	image: str
	manager: str
	command: tuple[str, ...]
	stdout: str
	stderr: str
	returncode: int


def detect_project_environment(repository: str | Path) -> ProjectEnvironment | None:
	"""Detect supported Python dependency metadata and derive an image tag."""

	root = resolve_repository(repository)
	present = tuple(name for name in _DEPENDENCY_FILES if (root / name).is_file())
	if not present:
		return None

	if "uv.lock" in present and "pyproject.toml" in present:
		manager = "uv"
		selected = ("pyproject.toml", "uv.lock")
	elif "poetry.lock" in present and "pyproject.toml" in present:
		manager = "poetry"
		selected = ("pyproject.toml", "poetry.lock")
	elif "requirements.txt" in present:
		manager = "pip-requirements"
		selected = tuple(
			name
			for name in ("requirements.txt", "requirements-dev.txt")
			if name in present
		)
	elif "pyproject.toml" in present:
		manager = "pip-project"
		selected = tuple(
			name for name in ("pyproject.toml", "setup.cfg", "setup.py") if name in present
		)
	elif "setup.py" in present or "setup.cfg" in present:
		manager = "pip-project"
		selected = tuple(name for name in ("setup.cfg", "setup.py") if name in present)
	else:
		return None

	digest = hashlib.sha256()
	digest.update(b"casi-python-3.11-v1\0")
	digest.update(manager.encode())
	for name in selected:
		digest.update(b"\0")
		digest.update(name.encode())
		digest.update(b"\0")
		digest.update((root / name).read_bytes())

	return ProjectEnvironment(
		manager=manager,
		dependency_files=selected,
		image=f"casi-project-env:{digest.hexdigest()[:16]}",
	)


def project_image_if_available(repository: str | Path) -> str | None:
	"""Return the content-addressed image when it already exists locally."""

	environment = detect_project_environment(repository)
	if environment is None or shutil.which("docker") is None:
		return None
	result = subprocess.run(
		["docker", "image", "inspect", environment.image],
		capture_output=True,
		text=True,
		check=False,
	)
	return environment.image if result.returncode == 0 else None


def prepare_project_environment(repository: str | Path) -> EnvironmentBuildResult:
	"""Build a dependency image. The caller must obtain explicit user approval."""

	root = resolve_repository(repository)
	environment = detect_project_environment(root)
	if environment is None:
		raise ValueError("No supported Python dependency files were found")
	if shutil.which("docker") is None:
		raise RuntimeError("Docker is not installed")

	with tempfile.TemporaryDirectory(prefix="casi-env-build-") as temp_dir:
		context = Path(temp_dir) / "context"
		shutil.copytree(root, context, ignore=ignore_sandbox_files)
		(context / "Dockerfile.casi").write_text(
			_dockerfile_for(environment.manager),
			encoding="utf-8",
		)
		command = (
			"docker",
			"build",
			"--tag",
			environment.image,
			"--file",
			"Dockerfile.casi",
			".",
		)
		result = subprocess.run(
			command,
			cwd=context,
			capture_output=True,
			text=True,
			check=False,
		)

	return EnvironmentBuildResult(
		success=result.returncode == 0,
		image=environment.image,
		manager=environment.manager,
		command=command,
		stdout=result.stdout,
		stderr=result.stderr,
		returncode=result.returncode,
	)


def ignore_sandbox_files(directory: str, names: list[str]) -> set[str]:
	"""Exclude local state, caches, VCS data, and common secret files."""

	ignored = {name for name in names if name in _COPY_EXCLUDES}
	for name in names:
		lower = name.lower()
		if lower in BLOCKED_NAMES or lower.startswith(".env."):
			ignored.add(name)
		if Path(lower).suffix in BLOCKED_SUFFIXES:
			ignored.add(name)
	return ignored


def _dockerfile_for(manager: str) -> str:
	lines = [
		"FROM python:3.11-slim",
		"WORKDIR /opt/casi-project",
		"ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1",
		"COPY . /opt/casi-project",
	]
	if manager == "uv":
		lines.extend(
			[
				"RUN python -m pip install uv pytest",
				"ENV UV_PROJECT_ENVIRONMENT=/opt/casi-venv",
				"RUN uv sync --locked --all-groups --no-install-project",
				"ENV PATH=/opt/casi-venv/bin:$PATH",
			]
		)
	elif manager == "poetry":
		lines.extend(
			[
				"RUN python -m pip install poetry pytest",
				"RUN poetry config virtualenvs.create false && poetry install --no-root",
			]
		)
	elif manager == "pip-requirements":
		lines.append("RUN python -m pip install pytest -r requirements.txt")
		lines.append(
			"RUN if [ -f requirements-dev.txt ]; then "
			"python -m pip install -r requirements-dev.txt; fi"
		)
	else:
		lines.append("RUN python -m pip install pytest .")
	lines.extend(["WORKDIR /workspace", "CMD [\"python3\", \"-m\", \"pytest\", \"-q\"]"])
	return "\n".join(lines) + "\n"
