from __future__ import annotations

from casi.terminal.test_summary import (
    format_test_summary,
    parse_test_output,
)
from casi.terminal.theme import Theme

_SAMPLE_PASSING_PYTEST = """=== test session starts ===
rootdir: /repo
collected 5 items

test_app.py .....                                                        [100%]

============================== 5 passed in 0.12s ===============================
"""

_SAMPLE_FAILING_PYTEST = """=== test session starts ===
rootdir: /repo
collected 2 items

test_app.py .F                                                           [100%]

=================================== FAILURES ===================================
__________________________________ test_fail ___________________________________
    def test_fail():
>       assert False is True
E       AssertionError: assert False is True

test_app.py:5: AssertionError
=========================== short test summary info ============================
FAILED test_app.py::test_fail - AssertionError: assert False is True
========================= 1 failed, 1 passed in 0.18s ==========================
"""


def test_parse_passing_pytest() -> None:
    parsed = parse_test_output(_SAMPLE_PASSING_PYTEST, default_passed=True)
    assert parsed.passed is True
    assert parsed.summary == "5 passed in 0.12s"
    assert parsed.failure_details == ""


def test_parse_failing_pytest() -> None:
    parsed = parse_test_output(_SAMPLE_FAILING_PYTEST, default_passed=False)
    assert parsed.passed is False
    assert parsed.summary == "1 failed, 1 passed in 0.18s"
    assert "FAILED test_app.py::test_fail" in parsed.failure_details
    assert "AssertionError" in parsed.failure_details


def test_format_test_summary_passing() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    rendered = format_test_summary(
        _SAMPLE_PASSING_PYTEST,
        passed=True,
        runner="docker pytest",
        theme=theme,
    )
    assert rendered == "✓ Tests passed via docker pytest (5 passed in 0.12s)"


def test_format_test_summary_failing() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    rendered = format_test_summary(
        _SAMPLE_FAILING_PYTEST,
        passed=False,
        runner="pytest",
        theme=theme,
    )
    assert "✗ Tests failed via pytest (1 failed, 1 passed in 0.18s)" in rendered
    assert "FAILED test_app.py::test_fail" in rendered


def test_format_test_summary_empty() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    rendered_pass = format_test_summary("", passed=True, runner="pytest", theme=theme)
    assert "✓ Tests passed via pytest (passed)" in rendered_pass

    rendered_fail = format_test_summary("", passed=False, runner="pytest", theme=theme)
    assert "✗ Tests failed via pytest (failed)" in rendered_fail
