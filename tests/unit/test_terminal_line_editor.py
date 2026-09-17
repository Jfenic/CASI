from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from casi.terminal.line_editor import setup_line_editing


def test_setup_line_editing_returns_none_in_non_tty(tmp_path: Path) -> None:
    with patch.object(sys.stdin, "isatty", return_value=False):
        completer = setup_line_editing(tmp_path)
        assert completer is None


def test_setup_line_editing_initializes_with_history(tmp_path: Path) -> None:
    history_file = tmp_path / ".history"
    history_file.write_text("/help\n/history\n", encoding="utf-8")

    with patch.object(sys.stdin, "isatty", return_value=True):
        completer = setup_line_editing(tmp_path, history_file=history_file)
        assert completer is not None
