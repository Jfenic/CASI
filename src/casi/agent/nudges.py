"""Centralized agent nudge messages and detection."""

from __future__ import annotations

from dataclasses import dataclass

_PREFIX_MALFORMED_JSON = "Your last reply was not a valid CASI"
_PREFIX_MISSING_PATCH = "The user requested a code change"
_PREFIX_REPOSITORY_DEFERRAL = "The repository is available through tools"
_PREFIX_REPEATED_CLARIFICATION = "The user already answered a clarification"
_PREFIX_PREMATURE_CLARIFICATION = "Do not ask the user for more details yet"
PIPELINE_FALLBACK_PREFIX = "Repository context for intent"
_PREFIX_FIX_WITHOUT_INSPECTION = "The user asked to fix code or pass tests"
_PREFIX_PATCH_INVALID = "The proposed patch is invalid"
_PREFIX_PATCH_NOT_APPLIED = "The proposed patch could not be applied"
_PREFIX_PATCH_FAILED_TESTS = "The proposed patch failed tests"
_PREFIX_PATCH_CORRECTION = "Provide corrected file content via propose_file"
_PREFIX_READ_INSTEAD_OF_SEARCH = "search_code results are already available"
_PREFIX_CORRUPT_PATCH = "The diff format was invalid for git apply"
_PREFIX_PROPOSE_FILE_FAILURE = "propose_file could not build the patch"

_PROPOSE_FILE_INSTRUCTION = (
	"Call propose_file with the repository-relative path and the complete "
	"file content. CASI will build the unified diff; do not write the diff yourself."
)

AGENT_NUDGE_PREFIXES = (
	_PREFIX_MALFORMED_JSON,
	_PREFIX_MISSING_PATCH,
	_PREFIX_REPOSITORY_DEFERRAL,
	_PREFIX_REPEATED_CLARIFICATION,
	_PREFIX_PREMATURE_CLARIFICATION,
	PIPELINE_FALLBACK_PREFIX,
	_PREFIX_FIX_WITHOUT_INSPECTION,
	_PREFIX_PATCH_INVALID,
	_PREFIX_PATCH_NOT_APPLIED,
	_PREFIX_PATCH_FAILED_TESTS,
	_PREFIX_PATCH_CORRECTION,
	_PREFIX_READ_INSTEAD_OF_SEARCH,
	_PREFIX_CORRUPT_PATCH,
	_PREFIX_PROPOSE_FILE_FAILURE,
)


@dataclass(frozen=True)
class ResponseNudge:
	"""Instruction to retry the model after an invalid or incomplete final answer."""

	user_message: str


def is_agent_nudge(content: str) -> bool:
	"""Return whether a user message was injected by CASI to steer the model."""

	return content.strip().startswith(AGENT_NUDGE_PREFIXES)


def nudge_for_malformed_json() -> ResponseNudge:
	return ResponseNudge(
		user_message=(
			f"{_PREFIX_MALFORMED_JSON} final answer. "
			"Use the repository tool results already in the conversation "
			'and reply with {"type":"final","content":"your answer"} only.'
		),
	)


def nudge_for_repository_deferral() -> ResponseNudge:
	return ResponseNudge(
		user_message=(
			f"{_PREFIX_REPOSITORY_DEFERRAL}. "
			"Inspect it with search_code, read_file, or run_tests, "
			"then answer from tool results."
		),
	)


def nudge_for_missing_patch() -> ResponseNudge:
	return ResponseNudge(
		user_message=(
			f"{_PREFIX_MISSING_PATCH} or passing tests. "
			"Call read_file on the failing source and test files if you have not "
			f"loaded them yet, then {_PROPOSE_FILE_INSTRUCTION} "
			"Do not describe the fix without calling propose_file."
		),
	)


def nudge_for_read_file_instead_of_search(
	paths: list[str],
	*,
	sources_already_read: bool = False,
) -> ResponseNudge:
	if sources_already_read:
		return ResponseNudge(
			user_message=(
				f"{_PREFIX_READ_INSTEAD_OF_SEARCH}. "
				"Source files are already loaded with read_file. "
				f"Do not call search_code again; {_PROPOSE_FILE_INSTRUCTION}"
			),
		)

	joined = ", ".join(paths[:3])
	return ResponseNudge(
		user_message=(
			f"{_PREFIX_READ_INSTEAD_OF_SEARCH} for {joined}. "
			f"Call read_file on those paths to load the full source, then "
			f"{_PROPOSE_FILE_INSTRUCTION}"
		),
	)


def nudge_for_corrupt_patch(output: str) -> ResponseNudge:
	return ResponseNudge(
		user_message=(
			f"{_PREFIX_CORRUPT_PATCH}.\n"
			f"Output:\n{output}\n"
			f"Do not hand-write a unified diff. {_PROPOSE_FILE_INSTRUCTION} "
			f"{_PREFIX_PATCH_CORRECTION} that fixes the failures."
		),
	)


def nudge_for_fix_without_inspection() -> ResponseNudge:
	return ResponseNudge(
		user_message=(
			f"{_PREFIX_FIX_WITHOUT_INSPECTION}. "
			"Call run_tests first, inspect failures with read_file or search_code, "
			f"then {_PROPOSE_FILE_INSTRUCTION}"
		),
	)


def nudge_for_repeated_clarification() -> ResponseNudge:
	return ResponseNudge(
		user_message=(
			f"{_PREFIX_REPEATED_CLARIFICATION}. State what you understood, "
			"inspect the repository with tools, and continue without asking again."
		),
	)


def nudge_for_premature_clarification() -> ResponseNudge:
	return ResponseNudge(
		user_message=(
			f"{_PREFIX_PREMATURE_CLARIFICATION}. Briefly state what you understood "
			"from the request, then call the first relevant repository tool or return "
			'a final answer with {"type":"final","content":"..."}. Do not ask the user '
			"to specify files, areas, or details you can infer or discover with tools."
		),
	)


def nudge_for_patch_correction(reason: str, output: str) -> ResponseNudge:
	if "corrupt patch" in output.lower():
		return nudge_for_corrupt_patch(output)
	return ResponseNudge(
		user_message=(
			f"{reason}\n"
			f"Output:\n{output}\n"
			f"{_PREFIX_PATCH_CORRECTION} that fixes the failures. "
			"Do not repeat the same change. Read the failed assertion carefully, "
			f"work out the expected value, and {_PROPOSE_FILE_INSTRUCTION}"
		),
	)


def nudge_for_propose_file_failure(error: str) -> ResponseNudge:
	return ResponseNudge(
		user_message=(
			f"{_PREFIX_PROPOSE_FILE_FAILURE}: {error} "
			f"Fix the issue and {_PROPOSE_FILE_INSTRUCTION}"
		),
	)
