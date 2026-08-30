from __future__ import annotations

from casi.agent.nudges import nudge_for_corrupt_patch, nudge_for_patch_correction


def test_patch_correction_nudge_explains_corrupt_diff_format() -> None:
    nudge = nudge_for_patch_correction(
        "The proposed patch is invalid.",
        "error: corrupt patch at line 4",
    )

    assert "diff format was invalid" in nudge.user_message
    assert "Prefix every content line with space" in nudge.user_message


def test_corrupt_patch_nudge_includes_git_output() -> None:
    nudge = nudge_for_corrupt_patch("error: corrupt patch at line 4")

    assert "error: corrupt patch at line 4" in nudge.user_message
    assert "Provide a corrected unified diff" in nudge.user_message
