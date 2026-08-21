"""Repository tree exploration helpers."""

import os
from pathlib import Path

from casi_code_agent.config import settings

from .security import SecurityError, resolve_repository, safe_path

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
}

def list_files(
    repository_path: str | Path,
    max_files: int | None = None,
) -> list[Path]:
    """Lista archivos permitidos dentro del repositorio."""

    repository = resolve_repository(repository_path)
    max_files = settings.max_files if max_files is None else max_files
    results: list[Path] = []

    for current_directory, directories, filenames in os.walk(repository):
        directories[:] = [
            directory
            for directory in directories
            if directory not in IGNORED_DIRECTORIES
        ]

        current_path = Path(current_directory)

        for filename in filenames:
            absolute_path = current_path / filename
            relative_path = absolute_path.relative_to(repository)

            try:
                safe_path(repository, relative_path)
            except SecurityError:
                continue

            results.append(relative_path)

            if len(results) >= max_files:
                return sorted(results)

    return sorted(results)