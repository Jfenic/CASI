"""Helpers for extracting repository paths from pytest output."""

from __future__ import annotations

import re

_FAILURE_PATH_PATTERNS = (
    re.compile(r"^([^\s:]+\.py):\d+:", re.MULTILINE),
    re.compile(r'File "([^"]+\.py)", line \d+'),
    re.compile(r"\bFAILED ([\w./-]+\.py)::"),
    re.compile(r"\bin ([\w./-]+\.py):\d+\b"),
)
_ASSERTION_MISMATCH = re.compile(
    r"AssertionError: assert (.+) == (.+)",
)
_FAILED_TEST_LINE = re.compile(r"^FAILED ([\w./-]+\.py::[\w_]+)", re.MULTILINE)


def extract_failure_paths(test_output: str) -> list[str]:
    """Return repository-relative paths mentioned in a pytest failure report."""

    paths: list[str] = []
    for pattern in _FAILURE_PATH_PATTERNS:
        for match in pattern.finditer(test_output):
            path = match.group(1).strip().lstrip("./")
            if path and path not in paths:
                paths.append(path)
    return paths


def extract_assertion_mismatches(test_output: str) -> list[tuple[str, str]]:
    """Return actual/expected pairs from pytest assertion failures."""

    mismatches: list[tuple[str, str]] = []
    for match in _ASSERTION_MISMATCH.finditer(test_output):
        actual = match.group(1).strip().strip("'\"")
        expected = match.group(2).strip().strip("'\"")
        pair = (actual, expected)
        if pair not in mismatches:
            mismatches.append(pair)
    return mismatches


def summarize_test_failures(test_output: str, *, max_items: int = 3) -> str:
    """Build a short human-readable summary of remaining pytest failures."""

    lines: list[str] = []
    for path in extract_failure_paths(test_output)[:max_items]:
        lines.append(path)
    for test_name in _FAILED_TEST_LINE.findall(test_output)[:max_items]:
        label = test_name.split("::", 1)[-1]
        if label not in lines:
            lines.append(label)
    for actual, expected in extract_assertion_mismatches(test_output)[:max_items]:
        hint = f"expected {expected!r}, got {actual!r}"
        if hint not in lines:
            lines.append(hint)
    if not lines:
        compact = " ".join(test_output.split())
        if len(compact) > 240:
            compact = f"{compact[:237]}..."
        return compact or "tests are still failing"
    return "; ".join(lines[:max_items])


def output_reports_failures(test_output: str) -> bool:
    """Return whether pytest output indicates failing tests."""

    if not test_output.strip():
        return False
    lowered = test_output.lower()
    if "== fail" in lowered or " failed" in lowered:
        return True
    if extract_failure_paths(test_output) or _FAILED_TEST_LINE.search(test_output):
        return True
    return "errors" in lowered
