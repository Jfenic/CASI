"""Panel and box-drawing utilities for terminal framing in CASI."""

from __future__ import annotations

import re
from collections.abc import Sequence

from casi.terminal.theme import Theme

_ANSI_STRIP_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\001|\002")


def strip_ansi(text: str) -> str:
    """Return text stripped of ANSI escape sequences and readline markers."""
    return _ANSI_STRIP_RE.sub("", text)


def render_panel(
    lines: Sequence[str],
    *,
    title: str | None = None,
    subtitle: str | None = None,
    width: int | None = None,
    theme: Theme | None = None,
) -> str:
    """Render text lines inside a bordered terminal box with title and subtitle."""
    t = theme or Theme()
    unicode_mode = t.glyphs.tree_branch == "├─"

    top_left = "╭" if unicode_mode else "+"
    top_right = "╮" if unicode_mode else "+"
    bottom_left = "╰" if unicode_mode else "+"
    bottom_right = "╯" if unicode_mode else "+"
    horiz = "─" if unicode_mode else "-"
    vert = "│" if unicode_mode else "|"

    visible_lengths = [len(strip_ansi(line)) for line in lines]
    title_len = len(strip_ansi(title)) + 4 if title else 0
    subtitle_len = len(strip_ansi(subtitle)) + 4 if subtitle else 0
    max_content_len = max(visible_lengths, default=20)
    target_width = width or max(max_content_len + 4, title_len + subtitle_len + 6, 70)

    inner_width = target_width - 2

    if title and subtitle:
        title_part = f"{horiz} {title} "
        subtitle_part = f" {subtitle} {horiz}"
        fill_count = max(
            inner_width - len(strip_ansi(title_part)) - len(strip_ansi(subtitle_part)),
            1,
        )
        top_border = (
            f"{top_left}{title_part}{horiz * fill_count}{subtitle_part}{top_right}"
        )
    elif title:
        title_part = f"{horiz} {title} "
        fill_count = max(inner_width - len(strip_ansi(title_part)), 1)
        top_border = f"{top_left}{title_part}{horiz * fill_count}{top_right}"
    else:
        top_border = f"{top_left}{horiz * inner_width}{top_right}"

    rendered = [t.dim(top_border)]

    for line in lines:
        vlen = len(strip_ansi(line))
        pad = " " * max(inner_width - vlen - 2, 0)
        row = f"{t.dim(vert)} {line}{pad} {t.dim(vert)}"
        rendered.append(row)

    bottom_border = f"{bottom_left}{horiz * inner_width}{bottom_right}"
    rendered.append(t.dim(bottom_border))

    return "\n".join(rendered)
