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


def truncate_by_strategy(
    text: str,
    max_chars: int,
    strategy: str = "tail",
) -> str:
    """Truncate text according to the given strategy when exceeding max_chars.

    Strategies:
    - 'tail': Preserve the end of the text (ideal for tracebacks and logs).
    - 'head_tail': Preserve both beginning and end with an omission marker.
    - 'head': Preserve the beginning of the text.
    """
    if len(text) <= max_chars:
        return text

    if strategy == "head":
        marker = "\n[... salida truncada ...]"
        budget = max(max_chars - len(marker), 10)
        return text[:budget] + marker

    if strategy == "head_tail":
        marker = "\n[... omitido ...]\n"
        available = max_chars - len(marker)
        if available <= 10:
            return text[-max_chars:]
        head_len = max(available // 3, 5)
        tail_len = max(available - head_len, 5)
        head = text[:head_len]
        tail = text[-tail_len:]
        first_nl = tail.find("\n")
        if first_nl != -1 and first_nl < tail_len // 3:
            tail = tail[first_nl + 1 :]
        return f"{head}{marker}{tail}"

    # Default: 'tail' (quedarse con lo último)
    marker = "[... salida truncada ...]\n"
    budget = max(max_chars - len(marker), 20)
    tail = text[-budget:]
    first_nl = tail.find("\n")
    if first_nl != -1 and first_nl < budget // 3:
        tail = tail[first_nl + 1 :]
    return f"{marker}{tail}"


def sanitize_and_compact_error(
    output: str,
    *,
    max_chars: int | None = None,
    strategy: str | None = None,
) -> str:
    """Sanitize and compact test/command error output based on length and strategy."""
    from casi.config import settings

    limit = max_chars if max_chars is not None else settings.max_error_output_chars
    strat = strategy if strategy is not None else settings.error_truncation_strategy

    cleaned = output.strip()
    if len(cleaned) <= limit:
        return cleaned

    if strat == "summary":
        summary = summarize_test_failures(cleaned)
        mismatches = extract_assertion_mismatches(cleaned)
        parts = [f"Resumen de fallos: {summary}"]
        if mismatches:
            hints = [
                f"esperado {exp!r}, pero obtuvo {act!r}" for act, exp in mismatches
            ]
            parts.append(f"Aserciones fallidas: {'; '.join(hints)}")
        return "\n".join(parts)

    if strat == "auto":
        failures_idx = cleaned.find("= FAILURES =")
        short_summary_idx = cleaned.find("= short test summary info =")

        if failures_idx != -1:
            extracted = cleaned[failures_idx:].strip()
            if len(extracted) <= limit:
                return extracted
            return truncate_by_strategy(extracted, limit, strategy="tail")
        if short_summary_idx != -1:
            extracted = cleaned[short_summary_idx:].strip()
            if len(extracted) <= limit:
                return extracted
            return truncate_by_strategy(extracted, limit, strategy="tail")
        return truncate_by_strategy(cleaned, limit, strategy="tail")

    return truncate_by_strategy(cleaned, limit, strategy=strat)
