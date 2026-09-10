"""Repository tree exploration helpers."""

import os
from pathlib import Path

from casi.config import settings

from .security import SecurityError, resolve_repository, safe_path

SOURCE_FILE_SUFFIXES = frozenset(
    {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".go",
        ".rs",
        ".java",
        ".md",
        ".toml",
        ".yaml",
        ".yml",
        ".json",
        ".txt",
    }
)

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".pytest-tmp",
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


def looks_like_filename(text: str) -> bool:
    """Return whether text looks like a repository file reference."""

    return Path(text.strip()).suffix.lower() in SOURCE_FILE_SUFFIXES


def resolve_named_paths(
    repository_path: str | Path,
    targets: list[str],
) -> list[str]:
    """Resolve bare filenames or repository paths to readable file paths."""

    repository = resolve_repository(repository_path)
    resolved: list[str] = []
    known_files = list_files(repository)

    for target in targets:
        candidate = target.strip().strip("'\"")
        if not candidate:
            continue

        path = Path(candidate)
        if "/" in candidate or candidate.startswith("."):
            try:
                safe_path(repository, path)
            except SecurityError:
                continue
            if (repository / path).is_file():
                normalized = path.as_posix()
                if normalized not in resolved:
                    resolved.append(normalized)
            continue

        if not looks_like_filename(candidate):
            continue

        matches = sorted(
            (
                relative_path
                for relative_path in known_files
                if relative_path.name == path.name
            ),
            key=lambda relative_path: (
                len(relative_path.parts),
                relative_path.as_posix(),
            ),
        )
        for match in matches[:3]:
            normalized = match.as_posix()
            if normalized not in resolved:
                resolved.append(normalized)

    return resolved
