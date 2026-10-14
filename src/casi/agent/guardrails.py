"""Loop guardrails against repetitive or excessive repository reads."""

from __future__ import annotations

from casi.llm.base import ChatMessage


def read_file_usage(messages: list[ChatMessage]) -> dict[str, int]:
    """Count how many times each path was read via read_file."""

    counts: dict[str, int] = {}
    for message in messages:
        call = message.tool_call
        if call is None or call.name != "read_file":
            continue
        path = str(call.arguments.get("path", ""))
        if not path:
            continue
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
