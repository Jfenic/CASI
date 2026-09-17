"""Readline configuration, tab-completion bindings, and persistent command history."""

from __future__ import annotations

import atexit
import sys
from collections.abc import Sequence
from pathlib import Path

from casi.terminal.completion import InteractiveCompleter

_DEFAULT_HISTORY_FILE = Path.home() / ".casi_history"
_HISTORY_LIMIT = 1000
_READLINE_DELIMS = " \t\n`~!#$%^&*()=+[{]}\\|;:'\",<>?"


def setup_line_editing(
    repository: str | Path,
    *,
    history_file: Path | None = None,
    commands: Sequence[str] | None = None,
) -> InteractiveCompleter | None:
    """Configure readline for tab completion and persistent session history."""
    if not (hasattr(sys.stdin, "isatty") and sys.stdin.isatty()):
        return None

    try:
        import readline
    except ImportError:
        return None

    completer = InteractiveCompleter(repository, commands=commands)
    readline.set_completer(completer.complete)
    readline.set_completer_delims(_READLINE_DELIMS)

    # Enable tab completion
    if sys.platform == "darwin":
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

    # Load persistent history
    target_history = history_file or _DEFAULT_HISTORY_FILE
    try:
        if target_history.exists():
            readline.read_history_file(str(target_history))
    except (OSError, UnicodeDecodeError):
        pass

    readline.set_history_length(_HISTORY_LIMIT)

    def _persist_history() -> None:
        try:
            target_history.parent.mkdir(parents=True, exist_ok=True)
            readline.write_history_file(str(target_history))
        except OSError:
            pass

    atexit.register(_persist_history)
    return completer
