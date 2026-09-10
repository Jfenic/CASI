"""Grade development tasks using checks withheld from the agent workspace."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from casi.evaluation.benchmark import BenchmarkTask
from casi.sandbox.base import TestResult
from casi.sandbox.docker_runner import DockerRunner
from casi.sandbox.local_runner import LocalRunner
from casi.sandbox.project_environment import ignore_sandbox_files


def grade_task(
    task: BenchmarkTask,
    *,
    original: Path,
    candidate: Path,
    runner: DockerRunner | LocalRunner | None = None,
    timeout_seconds: float = 60,
) -> tuple[TestResult, str]:
    """Restore the baseline, overlay allowed files, then add independent checks.

    Production grading requires Docker. LocalRunner is explicitly injected only
    for deterministic validation of our authored fixtures and reference solutions.
    """

    if task.grader_directory is None or not task.allowed_files:
        raise ValueError("Independent grading requires checks and allowed_files")
    selected = runner if runner is not None else DockerRunner()
    runner_name = "docker" if isinstance(selected, DockerRunner) else "local"
    if runner_name == "docker":
        if not selected.is_available() or not selected.image_exists():
            raise RuntimeError("Independent grading requires the Docker sandbox image")
    with tempfile.TemporaryDirectory(prefix="casi-grading-") as temp_dir:
        workspace = Path(temp_dir) / "workspace"
        shutil.copytree(original, workspace, ignore=ignore_sandbox_files)
        for name in task.allowed_files:
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts or name in {"", "."}:
                raise ValueError(f"Invalid allowed file: {name}")
            source = candidate / name
            destination = workspace / name
            if source.is_symlink() or not source.resolve().is_relative_to(
                candidate.resolve()
            ):
                raise ValueError(f"Candidate file escapes repository: {name}")
            if source.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            elif source.exists():
                raise ValueError(f"Candidate is not a regular file: {name}")
            else:
                destination.unlink(missing_ok=True)
        shutil.copytree(
            task.grader_directory,
            workspace / "_benchmark_checks",
            ignore=ignore_sandbox_files,
        )
        python = "python3" if runner_name == "docker" else sys.executable
        result = selected.run(
            workspace,
            [python, "-m", "pytest", "-q", "."],
            timeout_seconds=timeout_seconds,
        )
        return result, runner_name
