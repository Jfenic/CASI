"""Patch memento capturing and restoring file state for patch undo."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from casi.patching.validator import validate_patch


@dataclass(frozen=True, slots=True)
class PatchMemento:
    """Snapshot of file states prior to patch application."""

    patch: str
    files: tuple[str, ...]
    snapshots: dict[str, bytes | None]
    timestamp: float = field(default_factory=time.time)
    description: str = ""

    @classmethod
    def capture(
        cls,
        repository: str | Path,
        patch: str,
        *,
        files: Sequence[str] | None = None,
        description: str = "",
    ) -> PatchMemento:
        """Capture the current state of files that will be affected by a patch."""
        repo_path = Path(repository).expanduser().resolve()
        if files is None:
            validation = validate_patch(repository, patch)
            target_files = tuple(validation.files)
        else:
            target_files = tuple(files)

        snapshots: dict[str, bytes | None] = {}
        for rel_path in target_files:
            file_path = (repo_path / rel_path).resolve()
            if file_path.is_file():
                snapshots[rel_path] = file_path.read_bytes()
            else:
                snapshots[rel_path] = None

        return cls(
            patch=patch,
            files=target_files,
            snapshots=snapshots,
            description=description,
        )

    def restore(self, repository: str | Path) -> list[str]:
        """Restore all captured files to their exact pre-patch state."""
        repo_path = Path(repository).expanduser().resolve()
        restored: list[str] = []

        for rel_path, snapshot in self.snapshots.items():
            file_path = (repo_path / rel_path).resolve()
            if snapshot is None:
                if file_path.is_file():
                    file_path.unlink()
                    restored.append(rel_path)
            else:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(snapshot)
                restored.append(rel_path)

        return restored


class PatchMementoStack:
    """LIFO stack of patch mementos for rollback and undo operations."""

    def __init__(self) -> None:
        self._stack: list[PatchMemento] = []

    def push(self, memento: PatchMemento) -> None:
        """Add a patch memento onto the undo stack."""
        self._stack.append(memento)

    def pop(self) -> PatchMemento | None:
        """Remove and return the topmost memento, or None if empty."""
        if not self._stack:
            return None
        return self._stack.pop()

    def peek(self) -> PatchMemento | None:
        """Inspect the topmost memento without removing it."""
        if not self._stack:
            return None
        return self._stack[-1]

    def is_empty(self) -> bool:
        """Return True if no mementos are currently stored."""
        return len(self._stack) == 0

    def __len__(self) -> int:
        return len(self._stack)

    def undo(self, repository: str | Path) -> tuple[PatchMemento, list[str]]:
        """Pop the most recent memento and restore its pre-patch file snapshots."""
        if not self._stack:
            raise ValueError("No patch memento available to undo.")
        memento = self._stack.pop()
        restored = memento.restore(repository)
        return memento, restored

    def clear(self) -> None:
        """Clear all stored mementos."""
        self._stack.clear()
