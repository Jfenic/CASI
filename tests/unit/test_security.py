from pathlib import Path

import pytest

from casi_code_agent.exceptions import RepositoryError, SecurityError
from casi_code_agent.repository.explorer import list_files
from casi_code_agent.repository.security import resolve_repository, safe_path


def test_repository_does_not_exist(tmp_path: Path) -> None:
    with pytest.raises(RepositoryError):
        resolve_repository(tmp_path / "missing")


def test_repository_is_not_directory(tmp_path: Path) -> None:
    target = tmp_path / "repo.txt"
    target.write_text("content", encoding="utf-8")

    with pytest.raises(RepositoryError):
        resolve_repository(target)


def test_path_traversal_is_blocked(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()

    with pytest.raises(SecurityError):
        safe_path(repository, "../outside.txt")


def test_sensitive_file_is_blocked(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / ".env").write_text("SECRET=1", encoding="utf-8")

    with pytest.raises(SecurityError):
        safe_path(repository, ".env")


def test_symbolic_link_outside_repository_is_blocked(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    (repository / "linked.txt").symlink_to(outside)

    with pytest.raises(SecurityError):
        safe_path(repository, "linked.txt")


def test_git_directory_is_ignored(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    git_dir = repository / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("ignored", encoding="utf-8")
    (repository / "visible.txt").write_text("visible", encoding="utf-8")

    assert list_files(repository) == [Path("visible.txt")]


def test_file_limit_is_respected(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()

    for index in range(5):
        (repository / f"file_{index}.txt").write_text(str(index), encoding="utf-8")

    results = list_files(repository, max_files=2)

    assert len(results) == 2
    assert all(result.name.startswith("file_") for result in results)
