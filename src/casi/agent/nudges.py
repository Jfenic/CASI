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
_PREFIX_PATCH_CORRECTION = "Provide a corrected unified diff"
_PREFIX_READ_INSTEAD_OF_SEARCH = "search_code results are already available"
_PREFIX_CORRUPT_PATCH = "The diff format was invalid for git apply"

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
			"loaded them yet, then reply with a complete unified diff only, starting "
			"with --- a/ and +++ b/, preferably inside a ```diff block. "
			"Do not describe the fix without the diff."
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
				"Do not call search_code again; reply with a complete unified diff "
				"inside a ```diff block."
			),
		)

	joined = ", ".join(paths[:3])
	return ResponseNudge(
		user_message=(
			f"{_PREFIX_READ_INSTEAD_OF_SEARCH} for {joined}. "
			"Call read_file on those paths to load the full source, then reply with "
			"a complete unified diff inside a ```diff block."
		),
	)


def nudge_for_corrupt_patch(output: str) -> ResponseNudge:
	return ResponseNudge(
		user_message=(
			f"{_PREFIX_CORRUPT_PATCH}.\n"
			f"Output:\n{output}\n"
			"Reply with a valid unified diff inside a ```diff block. Requirements:\n"
			"- Start with --- a/path and +++ b/path on their own lines\n"
			"- Include a hunk header like @@ -1,3 +1,3 @@ on its own line\n"
			"- Prefix every content line with space (context), + (added), or - (removed)\n"
			"- Do not put code on the same line as the hunk header\n"
			f"{_PREFIX_PATCH_CORRECTION} that fixes the failures."
		),
	)


def nudge_for_fix_without_inspection() -> ResponseNudge:
	return ResponseNudge(
		user_message=(
			f"{_PREFIX_FIX_WITHOUT_INSPECTION}. "
			"Call run_tests first, inspect failures with read_file or search_code, "
			"then reply with a complete unified diff inside a ```diff block."
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
			f"{_PREFIX_PATCH_CORRECTION} that fixes the failures."
		),
	)
