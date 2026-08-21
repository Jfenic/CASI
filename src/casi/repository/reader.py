"""Repository file reading helpers."""

from pathlib import Path

from casi.config import settings
from casi.exceptions import BinaryFileError, FileTooLargeError
from casi.repository.security import resolve_repository, safe_path


def is_probably_binary(path: Path) -> bool:
    """Detecta de forma sencilla si un archivo parece binario."""

    sample = path.read_bytes()[:1024]
    return b"\x00" in sample


def read_file(
    repository_path: str | Path,
    file_path: str | Path,
    start_line: int = 1,
    end_line: int = 300,
) -> str:
    """Lee un rango de líneas de un archivo seguro."""

    repository = resolve_repository(repository_path)
    target = safe_path(repository, file_path)

    if not target.exists():
        raise FileNotFoundError(f"El archivo no existe: {file_path}")

    if not target.is_file():
        raise IsADirectoryError(f"La ruta no es un archivo: {file_path}")

    if target.stat().st_size > settings.max_file_size_bytes:
        raise FileTooLargeError(f"El archivo supera {settings.max_file_size_bytes} bytes.")

    if is_probably_binary(target):
        raise BinaryFileError(f"El archivo parece ser binario: {file_path}")

    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()

    start = max(start_line, 1)
    end = min(max(end_line, start), len(lines))

    selected_lines = []

    for line_number in range(start, end + 1):
        content = lines[line_number - 1]
        selected_lines.append(f"{line_number}: {content}")

    return "\n".join(selected_lines)
