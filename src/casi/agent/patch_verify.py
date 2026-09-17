"""Patch verification helpers for final agent responses."""

from __future__ import annotations

from collections.abc import Callable

from casi.agent.conversation import Conversation
from casi.agent.create_workflow import repository_has_test_files
from casi.agent.failure_classification import (
    FailureKind,
    classify_patch_validation_error,
    classify_test_result,
)
from casi.agent.nudges import nudge_for_patch_correction
from casi.agent.state import PatchVerification
from casi.patching.applier import PatchApplicationError
from casi.patching.extract import extract_patch
from casi.patching.validator import validate_patch
from casi.sandbox.patched_tests import run_patched_tests


def _request_patch_correction(
    conversation: Conversation,
    content: str,
    *,
    reason: str,
    correction_attempts: int,
    max_correction_attempts: int,
    runner: str,
    output: str,
    passed: bool,
    failure_kind: FailureKind | None = None,
    on_retry: Callable[[str], None] | None = None,
) -> tuple[PatchVerification | None, bool]:
    verification = PatchVerification(
        passed=passed,
        output=output,
        runner=runner,
        correction_attempts=correction_attempts,
        failure_kind=failure_kind,
    )
    if passed or correction_attempts >= max_correction_attempts:
        return verification, False

    nudge = nudge_for_patch_correction(reason, output, failure_kind=failure_kind)
    if on_retry is not None:
        detail = " ".join(output.split())
        if len(detail) > 240:
            detail = f"{detail[:237]}..."
        kind_label = failure_kind.value if failure_kind is not None else "unknown"
        on_retry(f"patch retry ({kind_label}): {reason} Detail: {detail}")
    conversation.append_nudge(content, nudge.user_message)
    return verification, True


def verify_patch_response(
    conversation: Conversation,
    content: str,
    *,
    correction_attempts: int,
    max_correction_attempts: int,
    intent: object | None = None,
    on_retry: Callable[[str], None] | None = None,
) -> tuple[PatchVerification | None, bool]:
    """Run patched tests on a final response or ask the model to retry."""

    patch = extract_patch(content)
    if patch is None:
        return None, False

    validation = validate_patch(conversation.registry.repository_path, patch)
    if not validation.valid:
        error = validation.error or "Patch is invalid"
        return _request_patch_correction(
            conversation,
            content,
            reason="The proposed patch is invalid.",
            correction_attempts=correction_attempts,
            max_correction_attempts=max_correction_attempts,
            runner="validation",
            output=error,
            passed=False,
            failure_kind=classify_patch_validation_error(error),
            on_retry=on_retry,
        )

    try:
        test_result, runner = run_patched_tests(
            conversation.registry.repository_path,
            patch,
        )
    except (ValueError, PatchApplicationError) as exc:
        error = str(exc)
        return _request_patch_correction(
            conversation,
            content,
            reason="The proposed patch could not be applied.",
            correction_attempts=correction_attempts,
            max_correction_attempts=max_correction_attempts,
            runner="validation",
            output=error,
            passed=False,
            failure_kind=classify_patch_validation_error(error),
            on_retry=on_retry,
        )

    output = test_result.stdout
    if test_result.stderr:
        output = f"{output}\n{test_result.stderr}".strip()
    has_test_suite = repository_has_test_files(conversation.registry.repository_path)
    no_tests_collected = test_result.exit_code == 5 and (
        "no tests ran" in output.lower() or "collected 0 items" in output.lower()
    )
    is_create = getattr(intent, "value", intent) == "create"
    if (
        is_create
        and not has_test_suite
        and no_tests_collected
        and not test_result.timed_out
    ):
        passed = True
        failure_kind = None
    else:
        passed = test_result.exit_code == 0 and not test_result.timed_out
        failure_kind = None if passed else classify_test_result(test_result, runner)
    return _request_patch_correction(
        conversation,
        content,
        reason=f"The proposed patch failed tests in the {runner} sandbox.",
        correction_attempts=correction_attempts,
        max_correction_attempts=max_correction_attempts,
        runner=runner,
        output=output,
        passed=passed,
        failure_kind=failure_kind,
        on_retry=on_retry,
    )
