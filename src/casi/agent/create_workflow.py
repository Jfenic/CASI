"""Create-task helpers for bootstrap and tool selection."""

from __future__ import annotations

from pathlib import Path


def repository_has_test_files(repository_path: str | Path) -> bool:
    """Return whether the repository already contains runnable tests."""

    repository = Path(repository_path).resolve()
    patterns = (
        "test_*.py",
        "tests/test_*.py",
        "tests/**/test_*.py",
    )
    for pattern in patterns:
        if any(repository.glob(pattern)):
            return True
    for marker in ("pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"):
        if (repository / marker).is_file():
            return True
    return False
