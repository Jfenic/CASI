"""Ephemeral Git worktrees and isolated workspace management."""

from __future__ import annotations

import difflib
import logging
import re
import shutil
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from casi.config import settings
from casi.patching.applier import PatchApplicationError, apply_patch
from casi.patching.validator import validate_patch
from casi.repository.security import is_sensitive_path, resolve_repository
from casi.sandbox.base import TestResult
from casi.sandbox.docker_runner import DockerRunner
from casi.sandbox.project_environment import ignore_sandbox_files
from casi.sandbox.runner_factory import RunnerKind
from casi.sandbox.test_execution import run_repository_tests
from casi.terminal.diff_view import FileDiffStat, calculate_diff_stats
from casi.terminal.review import review_patch

if TYPE_CHECKING:
    from casi.terminal.presenter import TerminalPresenter

logger = logging.getLogger(__name__)

_TASK_ID_PATTERN = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9_\.-]*[a-zA-Z0-9])?$")
_EXCLUDE_DIR_NAMES = {
    ".git",
    ".casi",
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


class WorktreeError(Exception):
    """Base exception for worktree operations."""


class WorktreeCreationError(WorktreeError):
    """Raised when an ephemeral worktree cannot be created."""


class WorktreeNotFoundError(WorktreeError):
    """Raised when a requested worktree does not exist or is not tracked."""


class WorktreeMutationError(WorktreeError):
    """Raised when a mutation or patch application inside a worktree fails."""


def _validate_task_id(task_id: str) -> None:
    if not task_id or not isinstance(task_id, str):
        raise ValueError("task_id must be a non-empty string")
    if not _TASK_ID_PATTERN.match(task_id) or ".." in task_id:
        raise ValueError(
            f"Invalid task_id: {task_id!r}. "
            "Must start and end with alphanumeric character, allowed characters: "
            "alphanumeric, '_', '-', '.' and no '..'"
        )


def _resolve_safe_path(root: Path, relative_path: str | Path) -> Path:
    if not str(relative_path).strip():
        raise ValueError("Path must be a non-empty relative path")
    rel = Path(relative_path)
    if rel.is_absolute():
        raise ValueError(f"Path must be relative, got: {relative_path}")
    target = (root / rel).resolve()
    if root not in target.parents:
        raise ValueError(f"Path traversal detected: {relative_path}")
    if is_sensitive_path(rel):
        raise ValueError(f"Sensitive path not allowed: {relative_path}")
    return target


def _make_copy_ignore(
    worktree_base: Path | None = None,
) -> Callable[[str, list[str]], set[str]]:
    """Return an ignore callback that excludes .casi and worktrees from copytree."""

    def _ignore(directory: str, names: list[str]) -> set[str]:
        ignored = set(ignore_sandbox_files(directory, names))
        ignored.add(".casi")
        if worktree_base is not None:
            dir_path = Path(directory).resolve()
            wt_base = worktree_base.resolve()
            if wt_base == dir_path:
                ignored.update(names)
            else:
                for name in names:
                    if (dir_path / name).resolve() == wt_base:
                        ignored.add(name)
        return ignored

    return _ignore


def _collect_relative_files(
    directory: Path,
    base_exclude: Path | None = None,
) -> set[str]:
    """Collect repository-relative paths, ignoring VCS, builds, and symlink escapes."""
    paths: set[str] = set()
    if not directory.is_dir():
        return paths

    dir_resolved = directory.resolve()
    exclude_resolved = base_exclude.resolve() if base_exclude is not None else None

    for item in directory.rglob("*"):
        if not item.is_file():
            continue
        try:
            item_resolved = item.resolve()
            if (
                dir_resolved not in item_resolved.parents
                and item_resolved != dir_resolved
            ):
                continue
        except OSError:
            continue

        if exclude_resolved is not None and (
            item_resolved == exclude_resolved
            or exclude_resolved in item_resolved.parents
        ):
            continue

        rel = item.relative_to(directory)
        if any(part in _EXCLUDE_DIR_NAMES for part in rel.parts):
            continue
        if is_sensitive_path(rel):
            continue
        paths.add(rel.as_posix())
    return paths


def _format_file_diff(
    orig_content: str,
    mod_content: str,
    fromfile: str,
    tofile: str,
) -> str:
    """Format unified diff chunk with proper EOF newline indicators."""
    orig_has_nl = orig_content.endswith("\n") or not orig_content
    mod_has_nl = mod_content.endswith("\n") or not mod_content

    orig_lines = orig_content.splitlines(keepends=True)
    mod_lines = mod_content.splitlines(keepends=True)

    orig_norm = [line if line.endswith("\n") else line + "\n" for line in orig_lines]
    mod_norm = [line if line.endswith("\n") else line + "\n" for line in mod_lines]

    raw_diff = list(
        difflib.unified_diff(
            orig_norm,
            mod_norm,
            fromfile=fromfile,
            tofile=tofile,
        )
    )
    if not raw_diff:
        return ""

    result: list[str] = []
    n = len(raw_diff)
    for i, line in enumerate(raw_diff):
        result.append(line)
        if not orig_has_nl and line.startswith("-") and not line.startswith("---"):
            has_subsequent_minus = any(
                raw_diff[j].startswith("-") and not raw_diff[j].startswith("---")
                for j in range(i + 1, min(i + 50, n))
            )
            if not has_subsequent_minus:
                result.append("\\ No newline at end of file\n")
        if not mod_has_nl and line.startswith("+") and not line.startswith("+++"):
            has_subsequent_plus = any(
                raw_diff[j].startswith("+") and not raw_diff[j].startswith("+++")
                for j in range(i + 1, min(i + 50, n))
            )
            if not has_subsequent_plus:
                result.append("\\ No newline at end of file\n")

    return "".join(result)


def _generate_non_git_diff(
    repo_root: Path,
    worktree_path: Path,
    *,
    worktree_base: Path | None = None,
) -> str:
    """Generate a multi-file unified diff between repo_root and worktree_path."""
    repo_files = _collect_relative_files(repo_root, base_exclude=worktree_base)
    wt_files = _collect_relative_files(worktree_path, base_exclude=None)
    all_files = sorted(repo_files | wt_files)

    diff_chunks: list[str] = []
    for rel_path in all_files:
        original = repo_root / rel_path
        modified = worktree_path / rel_path

        orig_exists = original.is_file()
        mod_exists = modified.is_file()

        if orig_exists and mod_exists:
            orig_text = original.read_text(encoding="utf-8", errors="replace")
            mod_text = modified.read_text(encoding="utf-8", errors="replace")
            if orig_text != mod_text:
                chunk = _format_file_diff(
                    orig_text, mod_text, f"a/{rel_path}", f"b/{rel_path}"
                )
                if chunk:
                    diff_chunks.append(
                        f"diff --git a/{rel_path} b/{rel_path}\n" + chunk
                    )
        elif not orig_exists and mod_exists:
            mod_text = modified.read_text(encoding="utf-8", errors="replace")
            chunk = _format_file_diff("", mod_text, "/dev/null", f"b/{rel_path}")
            if chunk:
                diff_chunks.append(
                    f"diff --git a/{rel_path} b/{rel_path}\nnew file mode 100644\n"
                    + chunk
                )
        elif orig_exists and not mod_exists:
            orig_text = original.read_text(encoding="utf-8", errors="replace")
            chunk = _format_file_diff(orig_text, "", f"a/{rel_path}", "/dev/null")
            if chunk:
                diff_chunks.append(
                    f"diff --git a/{rel_path} b/{rel_path}\ndeleted file mode 100644\n"
                    + chunk
                )

    return "".join(diff_chunks)


class WorktreeSession:
    """An active ephemeral worktree session isolated from the user's workspace."""

    def __init__(
        self,
        task_id: str,
        path: Path,
        repo_path: Path,
        *,
        is_git: bool,
        base_commit: str | None = None,
        branch_name: str | None = None,
        is_ephemeral_branch: bool = False,
        manager: WorktreeManager | None = None,
        auto_cleanup: bool = False,
    ) -> None:
        self.task_id = task_id
        self.path = path.resolve()
        self.repo_path = repo_path.resolve()
        self.is_git = is_git
        self.base_commit = base_commit
        self.branch_name = branch_name
        self.is_ephemeral_branch = is_ephemeral_branch
        self.created_at = time.time()
        self.active = True
        self._manager = manager
        self._auto_cleanup = auto_cleanup

    def write_file(
        self,
        relative_path: str | Path,
        content: str | bytes,
        *,
        stage: bool = False,
    ) -> Path:
        """Write content to a file in the worktree without touching main repo."""
        if not self.active:
            raise WorktreeMutationError(
                f"Worktree session {self.task_id} is no longer active"
            )

        target = _resolve_safe_path(self.path, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, str):
            target.write_text(content, encoding="utf-8")
        else:
            target.write_bytes(content)

        if stage and self.is_git:
            rel = target.relative_to(self.path).as_posix()
            self._run_git(["add", "-A", "--", rel])

        return target

    def read_file(self, relative_path: str | Path) -> str:
        """Read text from a file inside the worktree."""
        target = _resolve_safe_path(self.path, relative_path)
        if not target.is_file():
            raise FileNotFoundError(f"File not found in worktree: {relative_path}")
        return target.read_text(encoding="utf-8")

    def delete_file(
        self,
        relative_path: str | Path,
        *,
        stage: bool = False,
        missing_ok: bool = False,
    ) -> None:
        """Delete a file or directory inside the worktree."""
        if not self.active:
            raise WorktreeMutationError(
                f"Worktree session {self.task_id} is no longer active"
            )

        target = _resolve_safe_path(self.path, relative_path)
        if not target.exists():
            if missing_ok:
                return
            raise FileNotFoundError(f"File not found in worktree: {relative_path}")

        if target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)

        if stage and self.is_git:
            rel = target.relative_to(self.path).as_posix()
            self._run_git(["add", "-A", "--", rel])

    def file_exists(self, relative_path: str | Path) -> bool:
        """Return whether a file exists in this worktree."""
        try:
            target = _resolve_safe_path(self.path, relative_path)
            return target.exists()
        except ValueError:
            return False

    def stage_file(
        self,
        relative_path: str | Path,
        content: str | bytes | None = None,
    ) -> None:
        """Write (if content provided) and stage a file inside the worktree."""
        if not self.active:
            raise WorktreeMutationError(
                f"Worktree session {self.task_id} is no longer active"
            )
        if content is not None:
            self.write_file(relative_path, content, stage=True)
        elif self.is_git:
            target = _resolve_safe_path(self.path, relative_path)
            rel = target.relative_to(self.path).as_posix()
            self._run_git(["add", "-A", "--", rel])

    def stage_files(self, files: dict[str | Path, str | bytes]) -> None:
        """Write and stage multiple files inside the worktree."""
        for rel_path, content in files.items():
            self.write_file(rel_path, content, stage=False)
        if self.is_git and self.active:
            self._run_git(["add", "-A"])

    def apply_patch(self, patch: str) -> list[str]:
        """Apply a unified diff directly inside the isolated worktree."""
        if not self.active:
            raise WorktreeMutationError(
                f"Worktree session {self.task_id} is no longer active"
            )

        validation = validate_patch(self.path, patch)
        if not validation.valid:
            raise WorktreeMutationError(validation.error or "Patch is invalid")

        if self.is_git:
            result = self._run_git(
                ["apply", "--recount", "--whitespace=error-all", "-"],
                input=patch,
            )
            if result.returncode != 0:
                raise WorktreeMutationError(
                    result.stderr.strip() or "Patch application failed"
                )
            self._run_git(["add", "-A"])
            return validation.files

        try:
            return apply_patch(self.path, patch, approved=True, dry_run=False)
        except PatchApplicationError as exc:
            raise WorktreeMutationError(str(exc)) from exc

    def get_diff(self) -> str:
        """Extract a clean unified multi-file diff against the base commit."""
        if not self.active:
            return ""

        if self.is_git:
            # Stage all untracked and modified files so they appear in diff
            self._run_git(["add", "-A"])
            base = self.base_commit or "HEAD"
            result = self._run_git(
                ["diff", "--cached", "--no-ext-diff", "-U3", base],
            )
            if result.returncode == 0:
                return result.stdout
            # Fallback to non-cached diff against base
            result_uncached = self._run_git(
                ["diff", "--no-ext-diff", "-U3", base],
            )
            return result_uncached.stdout if result_uncached.returncode == 0 else ""

        manager_base = self._manager.worktree_base if self._manager else None
        return _generate_non_git_diff(
            self.repo_path, self.path, worktree_base=manager_base
        )

    def get_diff_stats(self) -> list[FileDiffStat]:
        """Compute line insertions and deletions per file for the worktree changes."""
        return calculate_diff_stats(self.get_diff())

    def get_changed_files(self) -> list[str]:
        """Return list of modified/added/deleted relative file paths."""
        return [stat.path for stat in self.get_diff_stats()]

    def review(
        self,
        *,
        input_fn: Callable[[str], str] = input,
        presenter: TerminalPresenter | None = None,
        output_fn: Callable[[str], None] = print,
    ) -> tuple[bool, str | None]:
        """Run interactive review prompt [y/N/v/save/?] on worktree changes."""
        diff = self.get_diff()
        stats = self.get_diff_stats()
        return review_patch(
            diff,
            stats,
            input_fn=input_fn,
            presenter=presenter,
            output_fn=output_fn,
        )

    def apply_to_main_repo(self, *, approved: bool = False) -> list[str]:
        """Apply approved worktree changes to the user's main working tree.

        Safety invariant: Changes are NEVER applied without approved=True.
        """
        if not approved:
            raise WorktreeMutationError(
                "Applying changes to main repository requires explicit human approval."
            )

        diff = self.get_diff()
        if not diff.strip():
            return []

        try:
            return apply_patch(self.repo_path, diff, approved=True, dry_run=False)
        except PatchApplicationError as exc:
            raise WorktreeMutationError(str(exc)) from exc

    def run_tests(
        self,
        command: list[str] | None = None,
        *,
        timeout_seconds: float = 120,
        prefer_docker: bool | None = None,
        runner: DockerRunner | None = None,
    ) -> tuple[TestResult, RunnerKind]:
        """Execute test suites against the worktree path without touching main repo."""
        if not self.active:
            raise WorktreeMutationError("Cannot run tests on an inactive worktree")

        if runner is not None and isinstance(runner, DockerRunner):
            if command is None:
                from casi.sandbox.test_command import detect_test_command

                command = detect_test_command(self.path, runner="docker")
            result = runner.run_in_workspace(
                self.path,
                command,
                timeout_seconds=timeout_seconds,
            )
            return result, "docker"

        return run_repository_tests(
            self.repo_path,
            timeout_seconds=timeout_seconds,
            prefer_docker=prefer_docker,
            workspace=self.path,
        )

    def reset(self) -> None:
        """Reset worktree back to base state, discarding staged mutations."""
        if not self.active:
            return

        if self.is_git:
            base = self.base_commit or "HEAD"
            self._run_git(["reset", "--hard", base])
            self._run_git(["clean", "-fdx"])
        else:
            shutil.rmtree(self.path, ignore_errors=True)
            self.path.mkdir(parents=True, exist_ok=True)
            shutil.copytree(
                self.repo_path,
                self.path,
                ignore=_make_copy_ignore(self.path.parent),
                dirs_exist_ok=True,
            )

    def cleanup(self) -> None:
        """Remove worktree and prune associated temporary git branch/metadata."""
        if not self.active:
            return

        self.active = False
        if self._manager is not None:
            self._manager._on_session_cleaned(self.task_id)

        if self.is_git:
            try:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(self.path)],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=settings.git_timeout_seconds,
                )
                subprocess.run(
                    ["git", "worktree", "prune"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=settings.git_timeout_seconds,
                )
                if self.branch_name and self.is_ephemeral_branch:
                    subprocess.run(
                        ["git", "branch", "-D", self.branch_name],
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=settings.git_timeout_seconds,
                    )
            except Exception as exc:
                logger.warning(
                    "Error during git worktree cleanup for %s: %s", self.task_id, exc
                )

        if self.path.exists():
            shutil.rmtree(self.path, ignore_errors=True)

    def _run_git(
        self,
        args: list[str],
        *,
        input: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.path,
            input=input,
            capture_output=True,
            text=True,
            check=False,
            timeout=settings.git_timeout_seconds,
        )

    def __enter__(self) -> WorktreeSession:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._auto_cleanup or exc_type is not None:
            self.cleanup()


class WorktreeManager:
    """Manages creation, tracking, and clean rollback of ephemeral git worktrees."""

    def __init__(
        self,
        repository: str | Path,
        *,
        worktree_dir: str | Path | None = None,
    ) -> None:
        self.repository_path = resolve_repository(repository)
        self.worktree_base = (
            Path(worktree_dir).resolve()
            if worktree_dir is not None
            else (self.repository_path / ".casi" / "worktrees").resolve()
        )
        self._sessions: dict[str, WorktreeSession] = {}
        self._ensure_git_exclude()

    def is_git_repository(self) -> bool:
        """Return True if repository is a valid git repository with commits."""
        try:
            check_top = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=self.repository_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=settings.git_timeout_seconds,
            )
            if check_top.returncode != 0 or not check_top.stdout.strip():
                return False
            discovered = Path(check_top.stdout.strip()).resolve()
            if discovered != self.repository_path.resolve():
                return False

            check_head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repository_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=settings.git_timeout_seconds,
            )
            return check_head.returncode == 0 and bool(check_head.stdout.strip())
        except (OSError, subprocess.SubprocessError):
            return False

    def is_detached_head(self) -> bool:
        """Return True if the repository HEAD is detached."""
        if not self.is_git_repository():
            return False
        try:
            res = subprocess.run(
                ["git", "symbolic-ref", "-q", "HEAD"],
                cwd=self.repository_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=settings.git_timeout_seconds,
            )
            return res.returncode != 0
        except (OSError, subprocess.SubprocessError):
            return False

    def get_head_commit(self) -> str | None:
        """Return current commit SHA of the repository, or None."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repository_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=settings.git_timeout_seconds,
            )
            return res.stdout.strip() if res.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None

    def create_worktree(
        self,
        task_id: str,
        *,
        base_ref: str | None = None,
        branch: str | None = None,
        create_branch: bool = False,
        detach: bool = True,
        auto_cleanup: bool = False,
    ) -> WorktreeSession:
        """Create and track an ephemeral worktree under `.casi/worktrees/<task_id>`."""
        _validate_task_id(task_id)

        # Clean up existing session for task_id if present
        if task_id in self._sessions:
            self._sessions[task_id].cleanup()

        target_path = self.worktree_base / task_id

        self.worktree_base.mkdir(parents=True, exist_ok=True)
        self._ensure_git_exclude()

        is_git = self.is_git_repository()
        if is_git:
            # Clean up any stale git worktree registration before creating
            try:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(target_path)],
                    cwd=self.repository_path,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=settings.git_timeout_seconds,
                )
                subprocess.run(
                    ["git", "worktree", "prune"],
                    cwd=self.repository_path,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=settings.git_timeout_seconds,
                )
            except Exception:
                pass

        if target_path.exists():
            shutil.rmtree(target_path, ignore_errors=True)

        if is_git:
            session = self._create_git_worktree(
                task_id,
                target_path,
                base_ref=base_ref,
                branch=branch,
                create_branch=create_branch,
                detach=detach,
                auto_cleanup=auto_cleanup,
            )
            if session is not None:
                self._sessions[task_id] = session
                return session
            logger.info(
                "Git worktree creation failed for %s, falling back to copy workspace.",
                task_id,
            )

        # Fallback for non-git repository or when git worktree creation fails
        session = self._create_fallback_workspace(
            task_id, target_path, auto_cleanup=auto_cleanup
        )
        self._sessions[task_id] = session
        return session

    def get_worktree(self, task_id: str) -> WorktreeSession | None:
        """Retrieve an active worktree session by task_id."""
        return self._sessions.get(task_id)

    def list_worktrees(self) -> list[WorktreeSession]:
        """Return all tracked active worktree sessions."""
        return [s for s in self._sessions.values() if s.active]

    def remove_worktree(self, task_id: str) -> None:
        """Cleanly remove a worktree session."""
        session = self._sessions.pop(task_id, None)
        if session is not None:
            session.cleanup()
        else:
            target_path = self.worktree_base / task_id
            if self.is_git_repository():
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", "--force", str(target_path)],
                        cwd=self.repository_path,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=settings.git_timeout_seconds,
                    )
                    subprocess.run(
                        ["git", "branch", "-D", f"casi/wt-{task_id}"],
                        cwd=self.repository_path,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=settings.git_timeout_seconds,
                    )
                except Exception:
                    pass
            if target_path.exists():
                shutil.rmtree(target_path, ignore_errors=True)
            self.prune()

    def cleanup_all(self) -> None:
        """Remove all active worktrees and prune stale metadata."""
        for session in list(self._sessions.values()):
            session.cleanup()
        self._sessions.clear()
        self.prune()

    def prune(self) -> None:
        """Prune git worktree metadata and clean empty worktree directories."""
        if self.is_git_repository():
            try:
                subprocess.run(
                    ["git", "worktree", "prune"],
                    cwd=self.repository_path,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=settings.git_timeout_seconds,
                )
                res = subprocess.run(
                    ["git", "branch", "--list", "casi/wt-*"],
                    cwd=self.repository_path,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=settings.git_timeout_seconds,
                )
                if res.returncode == 0:
                    active_branches = {
                        s.branch_name
                        for s in self._sessions.values()
                        if s.active and s.branch_name
                    }
                    for line in res.stdout.splitlines():
                        br = line.strip().lstrip("* ").strip()
                        if (
                            br
                            and br.startswith("casi/wt-")
                            and br not in active_branches
                        ):
                            subprocess.run(
                                ["git", "branch", "-D", br],
                                cwd=self.repository_path,
                                capture_output=True,
                                text=True,
                                check=False,
                                timeout=settings.git_timeout_seconds,
                            )
            except Exception:
                pass

        if self.worktree_base.exists() and not any(self.worktree_base.iterdir()):
            try:
                self.worktree_base.rmdir()
            except OSError:
                pass

    def _create_git_worktree(
        self,
        task_id: str,
        target_path: Path,
        *,
        base_ref: str | None = None,
        branch: str | None = None,
        create_branch: bool = False,
        detach: bool = True,
        auto_cleanup: bool = False,
    ) -> WorktreeSession | None:
        base_commit = self.get_head_commit() if base_ref is None else base_ref
        if not base_commit:
            return None

        branch_name: str | None = None
        is_ephemeral_branch = False

        cmd = ["git", "worktree", "add"]
        if create_branch:
            branch_name = branch or f"casi/wt-{task_id}"
            is_ephemeral_branch = True
            cmd.extend(["-B", branch_name, str(target_path), base_commit])
        elif branch:
            branch_name = branch
            is_ephemeral_branch = False
            cmd.extend([str(target_path), branch_name])
        elif detach:
            cmd.extend(["--detach", str(target_path), base_commit])
        else:
            cmd.extend([str(target_path), base_commit])

        result = subprocess.run(
            cmd,
            cwd=self.repository_path,
            capture_output=True,
            text=True,
            check=False,
            timeout=settings.git_timeout_seconds,
        )

        if result.returncode != 0:
            logger.warning(
                "git worktree add failed with code %d: %s",
                result.returncode,
                result.stderr,
            )
            return None

        return WorktreeSession(
            task_id=task_id,
            path=target_path,
            repo_path=self.repository_path,
            is_git=True,
            base_commit=base_commit,
            branch_name=branch_name,
            is_ephemeral_branch=is_ephemeral_branch,
            manager=self,
            auto_cleanup=auto_cleanup,
        )

    def _create_fallback_workspace(
        self,
        task_id: str,
        target_path: Path,
        *,
        auto_cleanup: bool = False,
    ) -> WorktreeSession:
        target_path.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            self.repository_path,
            target_path,
            ignore=_make_copy_ignore(self.worktree_base),
            dirs_exist_ok=True,
        )
        return WorktreeSession(
            task_id=task_id,
            path=target_path,
            repo_path=self.repository_path,
            is_git=False,
            base_commit=None,
            branch_name=None,
            manager=self,
            auto_cleanup=auto_cleanup,
        )

    def _ensure_git_exclude(self) -> None:
        """Ensure .casi/ is excluded in .git/info/exclude."""
        if not self.is_git_repository():
            return
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repository_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=settings.git_timeout_seconds,
            )
            if res.returncode == 0 and res.stdout.strip():
                git_dir = Path(res.stdout.strip())
                if not git_dir.is_absolute():
                    git_dir = (self.repository_path / git_dir).resolve()
                exclude_file = git_dir / "info" / "exclude"
                exclude_file.parent.mkdir(parents=True, exist_ok=True)
                existing = (
                    exclude_file.read_text(encoding="utf-8")
                    if exclude_file.exists()
                    else ""
                )
                if ".casi" not in existing:
                    with exclude_file.open("a", encoding="utf-8") as f:
                        if existing and not existing.endswith("\n"):
                            f.write("\n")
                        f.write(".casi/\n")
        except Exception:
            pass

    def _on_session_cleaned(self, task_id: str) -> None:
        self._sessions.pop(task_id, None)

    def __enter__(self) -> WorktreeManager:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.cleanup_all()
