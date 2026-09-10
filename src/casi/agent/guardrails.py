"""Loop guardrails against repetitive or excessive repository reads."""

from __future__ import annotations

import re

_READ_FILE_CALL = re.compile(
    r"Called tool=read_file with arguments=\{'path': '([^']+)'\}"
)


def read_file_usage(messages: list[object]) -> dict[str, int]:
    """Count how many times each path was read via read_file."""

    counts: dict[str, int] = {}
    for message in messages:
        role = getattr(message, "role", None)
        content = getattr(message, "content", "")
        if role != "assistant" or not isinstance(content, str):
            continue
        match = _READ_FILE_CALL.search(content)
        if match is None:
            continue
        path = match.group(1)
        counts[path] = counts.get(path, 0) + 1
    return counts


def should_block_read_file(
    path: str,
    usage: dict[str, int],
    *,
    max_reads_per_file: int,
    max_total_reads: int,
) -> str | None:
    """Return a short reason when a read_file call should be redirected."""

    if max_reads_per_file > 0 and usage.get(path, 0) >= max_reads_per_file:
        return f"{path} was already read {usage[path]} time(s)"
    total = sum(usage.values())
    if max_total_reads > 0 and total >= max_total_reads:
        return f"the task already loaded {total} file(s)"
    return None
