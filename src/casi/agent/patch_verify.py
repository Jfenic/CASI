"""Patch verification helpers for final agent responses."""

from __future__ import annotations

from casi.agent.conversation import Conversation
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
) -> tuple[PatchVerification | None, bool]:
	verification = PatchVerification(
		passed=passed,
		output=output,
		runner=runner,
		correction_attempts=correction_attempts,
	)
	if passed or correction_attempts >= max_correction_attempts:
		return verification, False

	nudge = nudge_for_patch_correction(reason, output)
	conversation.append_nudge(content, nudge.user_message)
	return None, True


def verify_patch_response(
	conversation: Conversation,
	content: str,
	*,
	correction_attempts: int,
	max_correction_attempts: int,
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
		)

	try:
		test_result, runner = run_patched_tests(
			conversation.registry.repository_path,
			patch,
		)
	except (ValueError, PatchApplicationError) as exc:
		return _request_patch_correction(
			conversation,
			content,
			reason="The proposed patch could not be applied.",
			correction_attempts=correction_attempts,
			max_correction_attempts=max_correction_attempts,
			runner="validation",
			output=str(exc),
			passed=False,
		)

	output = test_result.stdout
	if test_result.stderr:
		output = f"{output}\n{test_result.stderr}".strip()
	passed = test_result.exit_code == 0 and not test_result.timed_out
	return _request_patch_correction(
		conversation,
		content,
		reason=f"The proposed patch failed tests in the {runner} sandbox.",
		correction_attempts=correction_attempts,
		max_correction_attempts=max_correction_attempts,
		runner=runner,
		output=output,
		passed=passed,
	)
