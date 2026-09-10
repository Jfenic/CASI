from __future__ import annotations

from casi.agent.test_failures import (
    extract_assertion_mismatches,
    extract_failure_paths,
    output_reports_failures,
    summarize_test_failures,
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
