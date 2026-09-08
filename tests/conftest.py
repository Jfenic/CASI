"""Shared pytest configuration and opt-in Ollama E2E helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(PROJECT_ROOT / ".pytest-tmp"))
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SRC_DIR))


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "ollama: requires a running Ollama server and OLLAMA_E2E=1",
    )


def pytest_ignore_collect(collection_path, config):  # noqa: ARG001
    return "fixtures" in collection_path.parts


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def invalid_email_repo(tmp_path: Path) -> Path:
    """Copy the invalid-email repair fixture into an initialized git repo."""

    source = Path(__file__).parent / "fixtures" / "repair" / "invalid_email"
    repository = tmp_path / "invalid_email_repo"
    shutil.copytree(source, repository)
    _git(repository, "init", "--initial-branch", "main")
    _git(repository, "config", "user.email", "tests@example.com")
    _git(repository, "config", "user.name", "CASI Tests")
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "initial")
    return repository


@pytest.fixture
def ollama_e2e_enabled() -> None:
    """Skip Ollama E2E tests unless explicitly enabled."""

    if os.getenv("OLLAMA_E2E", "").lower() not in {"1", "true", "yes"}:
        pytest.skip("Set OLLAMA_E2E=1 to run Ollama end-to-end tests")


@pytest.fixture
def ollama_available(ollama_e2e_enabled: None) -> None:
    """Skip when Ollama is not reachable."""

    from casi.config import settings

    try:
        import urllib.error
        import urllib.request

        urllib.request.urlopen(
            f"{settings.ollama_base_url.rstrip('/')}/api/tags",
            timeout=3,
        )
    except (OSError, urllib.error.URLError):
        pytest.skip("Ollama server is not reachable")
