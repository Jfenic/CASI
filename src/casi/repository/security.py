"""Repository safety checks and path guards."""

from pathlib import Path

from casi.exceptions import RepositoryError, SecurityError

BLOCKED_NAMES = {
    ".env",
    ".git",
    ".ssh",
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
}

BLOCKED_SUFFIXES = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
}


def resolve_repository(path: str | Path) -> Path:
    """Resolve the repository root path."""

    repository = Path(path).expanduser().resolve()
    if not repository.exists():
        raise RepositoryError(f"Repository path does not exist: {repository}")
    if not repository.is_dir():
        raise RepositoryError(f"Repository path is not a directory: {repository}")
    return repository


def is_sensitive_path(relative_path: Path) -> bool:
    """Check if the relative path contains any sensitive names or suffixes"""

    lowered_parts = {part.lower() for part in relative_path.parts}
    return (
        bool(lowered_parts & BLOCKED_NAMES)
        or relative_path.suffix.lower() in BLOCKED_SUFFIXES
    )


def safe_path(
    repository: Path,
    requested_path: str | Path,
) -> Path:
    """Check that a path remains within the repository and is not sensitive."""

    repository = repository.resolve()
    candidate = (repository / requested_path).resolve()

    try:
        relative_path = candidate.relative_to(repository)
    except ValueError as exc:
        raise SecurityError(
            f"Requested path is outside the repository: {requested_path}"
        ) from exc

    if is_sensitive_path(relative_path):
        raise SecurityError(f"Requested path is sensitive: {requested_path}")

    return candidate
