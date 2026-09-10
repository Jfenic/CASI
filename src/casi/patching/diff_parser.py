"""Unified diff parsing helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath


class PatchFormatError(ValueError):
    """Raised when a patch does not contain valid file headers."""


@dataclass(frozen=True)
class PatchFile:
    old_path: str | None
    new_path: str | None

    @property
    def path(self) -> str:
        return self.new_path or self.old_path or ""


_HEADER = re.compile(r"^(---|\+\+\+) (.+?)(?:\t.*)?$")


def parse_patch_files(patch: str) -> list[PatchFile]:
    """Extract file paths from a unified diff."""

    if not patch.strip():
        raise PatchFormatError("Patch must not be empty")

    headers: list[tuple[str, str]] = []
    for line in patch.splitlines():
        match = _HEADER.match(line)
        if match:
            path = match.group(2).split("\t", 1)[0]
            headers.append((match.group(1), path))

    if not headers or len(headers) % 2:
        raise PatchFormatError("Patch must contain paired --- and +++ file headers")

    files: list[PatchFile] = []
    for index in range(0, len(headers), 2):
        old_marker, old_path = headers[index]
        new_marker, new_path = headers[index + 1]
        if old_marker != "---" or new_marker != "+++":
            raise PatchFormatError(
                "Patch file headers must appear as --- followed by +++"
            )
        files.append(
            PatchFile(
                old_path=_normalize_diff_path(old_path),
                new_path=_normalize_diff_path(new_path),
            )
        )

    return files


def _normalize_diff_path(path: str) -> str | None:
    if path == "/dev/null":
        return None
    if path.startswith(("a/", "b/")):
        return path[2:]
    return path


def is_relative_safe_path(path: str) -> bool:
    """Return whether a patch path is relative and traversal-free."""

    path_object = PurePosixPath(path)
    return not path_object.is_absolute() and ".." not in path_object.parts
