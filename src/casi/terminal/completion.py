"""Interactive readline completer for slash commands and @file references."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from casi.repository.explorer import list_files

DEFAULT_SLASH_COMMANDS = [
    "/help",
    "/explain",
    "/plan",
    "/diff",
    "/undo",
    "/history",
    "/stats",
    "/metrics",
    "/context",
    "/compact",
    "/clear",
    "/trace",
    "/last-trace",
    "/save-trace",
    "/cancel",
    "/exit",
    "/quit",
]

_FILE_MENTION_RE = re.compile(r"@([a-zA-Z0-9_\-./]+)")


def extract_file_mentions(text: str, repository: str | Path) -> list[str]:
    """Find and verify all @path references in a text string against the repository."""
    repo_path = Path(repository).resolve()
    mentions = _FILE_MENTION_RE.findall(text)
    verified: list[str] = []

    for match in mentions:
        cleaned = match.strip().lstrip("/")
        candidate = (repo_path / cleaned).resolve()
        try:
            candidate.relative_to(repo_path)
        except ValueError:
            continue
        if candidate.is_file():
            verified.append(cleaned)

    # Return deduplicated while preserving order
    return list(dict.fromkeys(verified))


class InteractiveCompleter:
    """Readline-compatible completion for slash commands and @repository files."""

    def __init__(
        self,
        repository: str | Path,
        commands: Sequence[str] | None = None,
    ) -> None:
        self.repository = Path(repository)
        self.commands = list(commands or DEFAULT_SLASH_COMMANDS)
        self._file_cache: list[str] | None = None
        self._last_matches: list[str] = []

    def get_files(self) -> list[str]:
        """Return list of relative file paths in repository."""
        if self._file_cache is None:
            try:
                self._file_cache = [str(p) for p in list_files(self.repository)]
            except Exception:
                self._file_cache = []
        return self._file_cache

    def refresh_files(self) -> None:
        """Clear cached files list."""
        self._file_cache = None

    def get_matches(self, text: str) -> list[str]:
        """Compute matching completions for given input text."""
        if text.startswith("/"):
            query = text.lower()
            return [cmd for cmd in self.commands if cmd.startswith(query)]

        if text.startswith("@"):
            query = text[1:]
            return [f"@{f}" for f in self.get_files() if f.startswith(query)]

        return []

    def complete(self, text: str, state: int) -> str | None:
        """Readline callback returning the match corresponding to state."""
        if state == 0:
            self._last_matches = self.get_matches(text)

        if state < len(self._last_matches):
            return self._last_matches[state]
        return None
