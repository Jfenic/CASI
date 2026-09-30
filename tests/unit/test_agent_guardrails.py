from __future__ import annotations

from casi.agent.guardrails import read_file_usage, should_block_read_file
from casi.llm.base import ChatMessage, ToolCallRecord


def test_read_file_usage_counts_paths() -> None:
    messages = [
        ChatMessage(
            role="assistant",
            content="Called tool=read_file with arguments={'path': 'a.py'}",
            tool_call=ToolCallRecord("read_file", {"path": "a.py"}, True),
        ),
        ChatMessage(
            role="assistant",
            content="Called tool=read_file with arguments={'path': 'a.py'}",
            tool_call=ToolCallRecord(
                "read_file", {"path": "a.py", "start_line": 20}, True
            ),
        ),
        ChatMessage(
            role="assistant",
            content="Called tool=read_file with arguments={'path': 'b.py'}",
            tool_call=ToolCallRecord(
                "read_file", {"end_line": 40, "path": "b.py"}, True
            ),
        ),
    ]

    assert read_file_usage(messages) == {"a.py": 2, "b.py": 1}


def test_read_claims_without_execution_do_not_consume_read_budget() -> None:
    messages = [
        ChatMessage(
            role="assistant",
            content="Called tool=read_file with arguments={'path': 'a.py'}",
        )
    ]
    assert read_file_usage(messages) == {}


def test_should_block_read_file_when_path_repeats() -> None:
    usage = {"sorter.py": 2}

    reason = should_block_read_file(
        "sorter.py",
        usage,
        max_reads_per_file=2,
        max_total_reads=12,
    )

    assert reason is not None
    assert "sorter.py" in reason


def test_should_block_read_file_when_total_limit_reached() -> None:
    usage = {f"file{i}.py": 1 for i in range(12)}

    reason = should_block_read_file(
        "new.py",
        usage,
        max_reads_per_file=2,
        max_total_reads=12,
    )

    assert reason is not None
    assert "12 file(s)" in reason
