"""Compact and syntax-highlighted diff rendering for the terminal."""

from __future__ import annotations

import re
from dataclasses import dataclass

from casi.terminal.theme import Theme

_FILE_DIFF_RE = re.compile(r"^diff --git a/(.*) b/(.*)$", re.MULTILINE)
_CHUNK_HEADER_RE = re.compile(r"^@@\s+-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?\s+@@")


@dataclass(frozen=True, slots=True)
class FileDiffStat:
    """Line change statistics for a single file."""

    path: str
    insertions: int
    deletions: int


def calculate_diff_stats(diff_text: str) -> list[FileDiffStat]:
    """Calculate additions and deletions per file in a unified diff."""
    stats: list[FileDiffStat] = []
    current_file: str | None = None
    insertions = 0
    deletions = 0

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            if current_file is not None:
                stats.append(
                    FileDiffStat(
                        path=current_file,
                        insertions=insertions,
                        deletions=deletions,
                    )
                )
            match = _FILE_DIFF_RE.match(line)
            current_file = match.group(2) if match else "unknown"
            insertions = 0
            deletions = 0
        elif line.startswith("+++ b/"):
            if current_file is None:
                current_file = line[6:].strip()
                insertions = 0
                deletions = 0
        elif line.startswith("+") and not line.startswith("+++"):
            insertions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    if current_file is not None:
        stats.append(
            FileDiffStat(
                path=current_file,
                insertions=insertions,
                deletions=deletions,
            )
        )

    return stats


def format_compact_diff(
    diff_text: str,
    *,
    theme: Theme | None = None,
    max_lines: int | None = 60,
) -> str:
    """Format a unified diff with compact syntax highlighting and line counts."""
    t = theme or Theme()
    if not diff_text.strip():
        return ""

    stats = calculate_diff_stats(diff_text)
    total_ins = sum(s.insertions for s in stats)
    total_del = sum(s.deletions for s in stats)

    # Build header summary
    file_summaries: list[str] = []
    for s in stats:
        ins = t.diff_add(f"+{s.insertions}")
        dels = t.diff_remove(f"-{s.deletions}")
        file_summaries.append(f"{s.path} ({ins}, {dels})")

    header = (
        f"{t.bold('Diff')} "
        f"[{t.diff_add(f'+{total_ins}')} / {t.diff_remove(f'-{total_del}')}]"
    )
    if file_summaries:
        header += f": {', '.join(file_summaries)}"

    raw_lines = diff_text.splitlines()
    formatted_lines: list[str] = [header]

    lines_to_render = raw_lines
    truncated = False
    if max_lines is not None and len(raw_lines) > max_lines:
        lines_to_render = raw_lines[:max_lines]
        truncated = True

    for line in lines_to_render:
        if line.startswith("diff --git ") or line.startswith("index "):
            continue
        elif line.startswith("--- ") or line.startswith("+++ "):
            formatted_lines.append(t.muted(line))
        elif _CHUNK_HEADER_RE.match(line):
            formatted_lines.append(t.diff_header(line))
        elif line.startswith("+"):
            formatted_lines.append(t.diff_add(line))
        elif line.startswith("-"):
            formatted_lines.append(t.diff_remove(line))
        else:
            formatted_lines.append(line)

    if truncated:
        remaining = len(raw_lines) - max_lines  # type: ignore[operator]
        ell = t.glyphs.ellipsis
        formatted_lines.append(
            t.muted(f"   {ell} [{remaining} more diff lines folded] {ell}")
        )

    return "\n".join(formatted_lines)
