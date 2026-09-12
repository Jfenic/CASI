"""Safe path resolution — prevent directory traversal (path traversal / LFI classic)."""

from pathlib import Path


def safe_join(base_dir: str, user_path: str) -> str:
    base = Path(base_dir).resolve()
    target = (base / user_path).resolve()
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise ValueError("path escapes base directory") from exc
    return str(target)
