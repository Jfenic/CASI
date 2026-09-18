from __future__ import annotations

from casi.agent.test_failures import (
    extract_assertion_mismatches,
    extract_failure_paths,
    output_reports_failures,
    sanitize_and_compact_error,
    summarize_test_failures,
    truncate_by_strategy,
)


def test_extract_failure_paths_from_pytest_traceback() -> None:
    output = (
        "FAILED "
        "tests/test_sorter.py::test_bubble_sort_orders_ascending "
        "- AssertionError\n"
        "_______________________ "
        "test_bubble_sort_orders_ascending "
        "_______________________\n"
        "    def test_bubble_sort_orders_ascending():\n"
        ">       assert bubble_sort([2, 1]) == [1, 2]\n"
        "tests/test_sorter.py:6: AssertionError\n"
        "sorter.py:10: in bubble_sort\n"
        '  File "sorter.py", line 10, in bubble_sort\n'
    )

    assert extract_failure_paths(output) == [
        "tests/test_sorter.py",
        "sorter.py",
    ]


def test_extract_assertion_mismatches_from_pytest_output() -> None:
    output = (
        "E    AssertionError: assert 'A.L' == 'A.L.'\n"
        "E      \n"
        "E      - A.L.\n"
        "E      + A.L\n"
    )

    assert extract_assertion_mismatches(output) == [("A.L", "A.L.")]


def test_summarize_test_failures_includes_expected_and_actual() -> None:
    output = (
        "FAILED test_initials.py::test_builds_initials_from_names - AssertionError\n"
        "E    AssertionError: assert 'G' == 'G.'\n"
    )

    summary = summarize_test_failures(output)

    assert "test_initials.py" in summary
    assert "expected 'G.'" in summary
    assert "got 'G'" in summary


def test_output_reports_failures_detects_pytest_summary() -> None:
    assert output_reports_failures("1 failed, 1 passed in 0.01s") is True
    assert output_reports_failures("3 passed in 0.01s") is False


def test_truncate_by_strategy_noop_when_under_limit() -> None:
    text = "line 1\nline 2"
    assert truncate_by_strategy(text, max_chars=100) == text


def test_truncate_by_strategy_tail_keeps_last_lines() -> None:
    text = "first part of text\nsecond part of text\nfinal line of error"
    truncated = truncate_by_strategy(text, max_chars=35, strategy="tail")
    assert "salida truncada" in truncated
    assert "final line of error" in truncated


def test_truncate_by_strategy_head_tail() -> None:
    text = "HEAD line here\n" + ("middle line\n" * 20) + "TAIL line here"
    truncated = truncate_by_strategy(text, max_chars=60, strategy="head_tail")
    assert "HEAD line" in truncated
    assert "TAIL line" in truncated
    assert "omitido" in truncated


def test_truncate_by_strategy_head() -> None:
    text = "HEAD line here\n" + ("middle line\n" * 20)
    truncated = truncate_by_strategy(text, max_chars=40, strategy="head")
    assert "HEAD line here" in truncated
    assert "salida truncada" in truncated


def test_sanitize_and_compact_error_auto_extracts_failures() -> None:
    long_prefix = "platform linux -- python 3.11\ncollected 20 items\n" + (
        "passing test line\n" * 50
    )
    failure_block = (
        "= FAILURES =\n"
        "___ test_foo ___\n"
        "assert False\n"
        "= short test summary info =\n"
        "FAILED test_foo\n"
    )
    full_output = long_prefix + failure_block
    compacted = sanitize_and_compact_error(full_output, max_chars=300, strategy="auto")
    assert "= FAILURES =" in compacted or "FAILED test_foo" in compacted
    assert "platform linux" not in compacted


def test_sanitize_and_compact_error_summary_strategy() -> None:
    output = (
        "FAILED test_math.py::test_add - AssertionError\n"
        "E    AssertionError: assert 3 == 4\n"
        "lots of noise...\n" * 20
    )
    compacted = sanitize_and_compact_error(output, max_chars=50, strategy="summary")
    assert "Resumen de fallos:" in compacted
    assert "test_math.py" in compacted
    assert "Aserciones fallidas:" in compacted
