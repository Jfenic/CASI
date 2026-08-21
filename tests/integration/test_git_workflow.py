from __future__ import annotations

import subprocess
from pathlib import Path

from casi.tools.registry import ToolRegistry


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


def _create_git_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repo"
    repository.mkdir()
    _git(repository, "init", "--initial-branch", "main")
    _git(repository, "config", "user.email", "tests@example.com")
    _git(repository, "config", "user.name", "CASI Tests")
    (repository / "README.md").write_text("initial\n", encoding="utf-8")
    _git(repository, "add", "README.md")
    _git(repository, "commit", "-m", "initial")
    return repository


def test_git_diff_reports_clean_working_tree(tmp_path: Path) -> None:
    repository = _create_git_repository(tmp_path)

    result = ToolRegistry(repository).execute("git_diff", {})

    assert result.success is True
    assert result.output == ""
    assert result.metadata["changed"] is False


def test_git_diff_reports_modified_file(tmp_path: Path) -> None:
    repository = _create_git_repository(tmp_path)
    (repository / "README.md").write_text("updated\n", encoding="utf-8")

    result = ToolRegistry(repository).execute("git_diff", {})

    assert result.success is True
    assert "-initial" in result.output
    assert "+updated" in result.output
    assert result.metadata["changed"] is True


def test_git_diff_reports_staged_changes(tmp_path: Path) -> None:
    repository = _create_git_repository(tmp_path)
    (repository / "README.md").write_text("staged\n", encoding="utf-8")
    _git(repository, "add", "README.md")

    result = ToolRegistry(repository).execute("git_diff", {"staged": True})

    assert result.success is True
    assert "+staged" in result.output
    assert result.metadata["staged"] is True


def test_git_diff_rejects_non_git_directory(tmp_path: Path) -> None:
    repository = tmp_path / "not-a-repository"
    repository.mkdir()

    result = ToolRegistry(repository).execute("git_diff", {})

    assert result.success is False
    assert result.error is not None
    assert result.metadata["exit_code"] != 0
