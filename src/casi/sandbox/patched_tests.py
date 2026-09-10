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
from casi.sandbox.project_environment import ignore_sandbox_files
from casi.sandbox.runner_factory import RunnerKind
from casi.sandbox.test_execution import run_repository_pytest


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

    with tempfile.TemporaryDirectory(prefix="casi-patched-") as temp_dir:
        workspace = Path(temp_dir) / "workspace"
        shutil.copytree(
            root, workspace, ignore=ignore_sandbox_files, dirs_exist_ok=True
        )

        apply_result = subprocess.run(
            ["git", "apply", "--recount", "--whitespace=error-all", "-"],
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

        result, runner_kind = run_repository_pytest(
            root,
            timeout_seconds=timeout,
            prefer_docker=prefer_docker,
            workspace=workspace,
        )
        return result, runner_kind
