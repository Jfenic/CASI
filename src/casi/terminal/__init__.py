"""Terminal presentation, styling, and interactive UI utilities for CASI."""

from __future__ import annotations

from casi.terminal.completion import (
    DEFAULT_SLASH_COMMANDS,
    InteractiveCompleter,
    extract_file_mentions,
)
from casi.terminal.diff_view import (
    FileDiffStat,
    calculate_diff_stats,
    format_compact_diff,
)
from casi.terminal.fold import fold_output
from casi.terminal.line_editor import setup_line_editing
from casi.terminal.memento import PatchMemento, PatchMementoStack
from casi.terminal.presenter import PresenterProtocol, TerminalPresenter
from casi.terminal.review import PatchAction, parse_patch_action, review_patch
from casi.terminal.session_metrics import SessionMetrics, format_session_summary
from casi.terminal.spinner import Spinner, status
from casi.terminal.test_summary import (
    ParsedTestResult,
    format_test_summary,
    parse_test_output,
)
from casi.terminal.theme import Glyphs, Theme
from casi.terminal.tree import TreeNode, render_tree

__all__ = [
    "DEFAULT_SLASH_COMMANDS",
    "FileDiffStat",
    "Glyphs",
    "InteractiveCompleter",
    "ParsedTestResult",
    "PatchAction",
    "PatchMemento",
    "PatchMementoStack",
    "PresenterProtocol",
    "SessionMetrics",
    "Spinner",
    "TerminalPresenter",
    "Theme",
    "TreeNode",
    "calculate_diff_stats",
    "extract_file_mentions",
    "fold_output",
    "format_compact_diff",
    "format_session_summary",
    "format_test_summary",
    "parse_patch_action",
    "parse_test_output",
    "render_tree",
    "review_patch",
    "setup_line_editing",
    "status",
]
