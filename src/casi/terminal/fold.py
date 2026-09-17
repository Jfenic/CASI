"""Intelligent output folding and truncation for long terminal text."""

from __future__ import annotations

from casi.terminal.theme import Theme


def fold_output(
    text: str,
    *,
    max_lines: int = 15,
    head_lines: int = 6,
    tail_lines: int = 4,
    theme: Theme | None = None,
) -> str:
    """Fold long multi-line text by showing top and bottom lines with a
    summary fold marker.
    """
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text

    t = theme or Theme()
    head = lines[:head_lines]
    tail = lines[-tail_lines:] if tail_lines > 0 else []
    collapsed_count = len(lines) - (len(head) + len(tail))

    ell = t.glyphs.ellipsis
    marker = t.muted(f"   {ell} [{collapsed_count} lines collapsed] {ell}")
    result = [*head, marker, *tail]
    return "\n".join(result)
