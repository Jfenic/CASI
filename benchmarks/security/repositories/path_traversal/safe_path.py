"""Safe path resolution — prevent directory traversal (path traversal / LFI classic)."""

from pathlib import Path


def safe_join(base_dir: str, user_path: str) -> str:
    return str(Path(base_dir) / user_path)
