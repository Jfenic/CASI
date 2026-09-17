"""Parsing and collapsed formatting of test runner outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass

from casi.terminal.fold import fold_output
from casi.terminal.theme import Theme

# Matches pytest footer: e.g. "=== 12 passed in 0.45s ==="
# or "=== 1 failed, 11 passed in 0.8s ==="
_PYTEST_FOOTER_RE = re.compile(
    r"=+\s+([0-9]+\s+(?:passed|failed|skipped|error|xfailed|xpassed)[^=]*?)=+",
    re.IGNORECASE,
)
_FAILED_LINE_RE = re.compile(r"^FAILED\s+(.*)$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class ParsedTestResult:
    """Structured extraction from test runner output."""

    passed: bool
    summary: str
    failure_details: str
    raw_output: str


def parse_test_output(raw_output: str, *, default_passed: bool) -> ParsedTestResult:
    """Extract summary line and failure snippets from pytest/unittest output."""
    if not raw_output or not raw_output.strip():
        summary = "passed" if default_passed else "failed"
        return ParsedTestResult(
            passed=default_passed,
            summary=summary,
            failure_details="",
            raw_output=raw_output,
        )

    lines = raw_output.splitlines()

    # Look for pytest footer from bottom to top
    summary = ""
    for line in reversed(lines):
        match = _PYTEST_FOOTER_RE.search(line)
        if match:
            summary = match.group(1).strip()
            break

    if not summary:
        summary = "all tests passed" if default_passed else "tests failed"

    # Extract failure block if failed
    failure_details = ""
    if not default_passed:
        # Check for short test summary info or FAILURES block
        in_failures = False
        failure_lines: list[str] = []
        for line in lines:
            if "=== FAILURES ===" in line or "=== short test summary info ===" in line:
                in_failures = True
                failure_lines.append(line)
                continue
            if in_failures:
                # Stop at the final footer line
                if line.startswith("===") and ("passed" in line or "failed" in line):
                    break
                failure_lines.append(line)

        if failure_lines:
            failure_details = "\n".join(failure_lines).strip()
        else:
            # Fallback to lines matching FAILED ...
            failed_matches = _FAILED_LINE_RE.findall(raw_output)
            if failed_matches:
                failure_details = "\n".join(
                    f"FAILED {m.strip()}" for m in failed_matches
                )
            else:
                failure_details = raw_output.strip()

    return ParsedTestResult(
        passed=default_passed,
        summary=summary,
        failure_details=failure_details,
        raw_output=raw_output,
    )


def format_test_summary(
    raw_output: str,
    *,
    passed: bool,
    runner: str,
    theme: Theme | None = None,
    max_failure_lines: int = 15,
) -> str:
    """Render a clean test result summary, showing only failure trace when failed."""
    t = theme or Theme()
    parsed = parse_test_output(raw_output, default_passed=passed)

    if parsed.passed:
        return t.success(f"Tests passed via {runner} ({parsed.summary})")

    # If failed, show failure title and folded details
    lines: list[str] = [t.error(f"Tests failed via {runner} ({parsed.summary})")]
    if parsed.failure_details:
        folded = fold_output(
            parsed.failure_details,
            max_lines=max_failure_lines,
            head_lines=7,
            tail_lines=4,
            theme=t,
        )
        lines.append(folded)

    return "\n".join(lines)
