from __future__ import annotations

from dataclasses import replace

import pytest

from casi.agent.failure_classification import FailureKind
from casi.agent.nudges import (
    nudge_for_corrupt_patch,
    nudge_for_missing_patch,
    nudge_for_patch_correction,
    nudge_for_read_file_instead_of_search,
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


def test_patch_correction_nudge_reports_actual_and_expected_values() -> None:
    output = "E    AssertionError: assert 'A.L' == 'A.L.'\n"
    nudge = nudge_for_patch_correction(
        "The proposed patch failed tests in the local sandbox.",
        output,
        failure_kind=FailureKind.CODE,
    )

    assert "expected 'A.L.'" in nudge.user_message
    assert "code returned 'A.L'" in nudge.user_message


def test_missing_patch_nudge_lists_remaining_failures() -> None:
    output = (
        "FAILED test_validator.py::test_rejects_missing_at_symbol - AssertionError\n"
    )
    nudge = nudge_for_missing_patch(remaining_test_output=output)

    assert "Tests are still failing" in nudge.user_message
    assert "test_rejects_missing_at_symbol" in nudge.user_message
    assert "within the requested scope" in nudge.user_message
    assert "unrelated pre-existing failures" in nudge.user_message


@pytest.mark.parametrize("failure_kind", [None, FailureKind.CODE])
def test_missing_exception_guidance_survives_output_truncation(
    monkeypatch: pytest.MonkeyPatch, failure_kind: FailureKind | None
) -> None:
    from casi.config import settings

    monkeypatch.setattr(
        "casi.config.settings",
        replace(settings, max_error_output_chars=200),
    )
    output = (
        "E Failed: DID NOT RAISE <class 'RuntimeError'>\n"
        + "irrelevant log line\n" * 100
        + "FAILED tests/test_inputs.py::test_validation\n1 failed\n"
    )
    nudge = nudge_for_patch_correction(
        "The proposed patch failed tests.", output, failure_kind=failure_kind
    )

    assert "expected exception was not raised" in nudge.user_message
    assert "invalid input" not in nudge.user_message
    assert "restore any removed or weakened guards" not in nudge.user_message
    assert "isinstance(True, int)" not in nudge.user_message
    assert "type(value) is int" not in nudge.user_message
    assert "salida truncada" in nudge.user_message


def test_repeated_search_guidance_respects_read_only_role() -> None:
    nudge = nudge_for_read_file_instead_of_search(
        [], sources_already_read=True, allow_patch=False
    )
    assert "propose_file" not in nudge.user_message
    assert "Search a different target" in nudge.user_message
