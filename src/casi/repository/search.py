"""Repository search helpers."""

from dataclasses import dataclass
from pathlib import Path

from casi.config import settings
from casi.repository.reader import is_probably_binary
from casi.repository.explorer import list_files
from casi.repository.security import resolve_repository, safe_path


@dataclass(frozen=True)
class SearchResult:
    path: str
    line_number: int
    line: str


def search_code(
    repository_path: str | Path,
    query: str,
    max_results: int | None = None,
) -> list[SearchResult]:
    """Busca texto dentro de los archivos del repositorio."""

    if not query.strip():
        raise ValueError("El texto de búsqueda no puede estar vacío.")

    repository = resolve_repository(repository_path)
    max_results = settings.max_search_results if max_results is None else max_results
    results: list[SearchResult] = []

    for relative_path in list_files(
        repository,
        max_files=settings.max_files,
    ):
        target = safe_path(repository, relative_path)

        if is_probably_binary(target):
            continue

        try:
            content = target.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            continue

        for line_number, line in enumerate(
            content.splitlines(),
            start=1,
        ):
            if query.lower() in line.lower():
                results.append(
                    SearchResult(
                        path=relative_path.as_posix(),
                        line_number=line_number,
                        line=line,
                    )
                )

                if len(results) >= max_results:
                    return results

    return results
