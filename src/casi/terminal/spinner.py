"""Lightweight, non-blocking terminal spinner for immediate activity feedback."""

from __future__ import annotations

import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager

from casi.terminal.theme import Theme

_UNICODE_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
_ASCII_FRAMES = ("|", "/", "-", "\\")


class Spinner:
    """Threaded terminal spinner providing visual activity in <200ms."""

    def __init__(
        self,
        message: str,
        *,
        theme: Theme | None = None,
        interval: float = 0.08,
    ) -> None:
        self.message = message
        self.theme = theme or Theme()
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._frames = (
            _UNICODE_FRAMES if self.theme.glyphs.ellipsis == "…" else _ASCII_FRAMES
        )
        self._is_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    def start(self) -> Spinner:
        """Start the background animation thread if in a TTY."""
        if not self._is_tty or not self.theme.color_enabled:
            return self

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def _spin(self) -> None:
        idx = 0
        while not self._stop_event.is_set():
            frame = self._frames[idx % len(self._frames)]
            icon = self.theme.muted(frame)
            msg = self.theme.muted(self.message)
            line = f"\r\033[2K{icon} {msg}"
            sys.stdout.write(line)
            sys.stdout.flush()
            idx += 1
            time.sleep(self.interval)

    def update(self, new_message: str) -> None:
        """Change the displayed spinner text while running."""
        self.message = new_message

    def stop(self, *, clear: bool = True) -> None:
        """Stop the background spinner."""
        if self._thread is not None and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=0.3)
            if clear and self._is_tty and self.theme.color_enabled:
                sys.stdout.write("\r\033[2K")
                sys.stdout.flush()
        self._thread = None

    def __enter__(self) -> Spinner:
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


@contextmanager
def status(
    message: str,
    *,
    theme: Theme | None = None,
) -> Iterator[Spinner]:
    """Context manager for showing spinner activity during long-running tasks."""
    spinner = Spinner(message, theme=theme)
    spinner.start()
    try:
        yield spinner
    finally:
        spinner.stop()
