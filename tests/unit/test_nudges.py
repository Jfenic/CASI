from __future__ import annotations

from casi.agent.failure_classification import FailureKind
from casi.agent.nudges import (
    nudge_for_corrupt_patch,
    nudge_for_missing_patch,
    nudge_for_patch_correction,
)


def test_patch_correction_nudge_explains_corrupt_diff_format() -> None:
    nudge = nudge_for_patch_correction(
        "The proposed patch is invalid.",
        "error: corrupt patch at line 4",
    )

    assert "diff format was invalid" in nudge.user_message
    assert "propose_file" in nudge.user_message
    assert "Do not hand-write a unified diff" in nudge.user_message


def test_corrupt_patch_nudge_includes_git_output() -> None:
    nudge = nudge_for_corrupt_patch("error: corrupt patch at line 4")

    assert "error: corrupt patch at line 4" in nudge.user_message
    assert "Provide corrected file content via propose_file" in nudge.user_message


def test_patch_correction_nudge_highlights_trailing_period_mismatch() -> None:
    output = "E    AssertionError: assert 'A.L' == 'A.L.'\n"
    nudge = nudge_for_patch_correction(
        "The proposed patch failed tests in the local sandbox.",
        output,
        failure_kind=FailureKind.CODE,
    )

    assert "expected 'A.L.'" in nudge.user_message
    assert "trailing period" in nudge.user_message


def test_missing_patch_nudge_lists_remaining_failures() -> None:
    output = (
        "FAILED test_validator.py::test_rejects_missing_at_symbol - AssertionError\n"
    )
    nudge = nudge_for_missing_patch(remaining_test_output=output)

    assert "Tests are still failing" in nudge.user_message
    assert "test_rejects_missing_at_symbol" in nudge.user_message
    assert "Fix every remaining failure" in nudge.user_message
