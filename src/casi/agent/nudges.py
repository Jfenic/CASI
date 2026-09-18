"""Centralized agent nudge messages and detection."""

from __future__ import annotations

import json
from dataclasses import dataclass

from casi.agent.failure_classification import FailureKind, failure_kind_label
from casi.agent.test_failures import (
    extract_assertion_mismatches,
    output_reports_failures,
    sanitize_and_compact_error,
    summarize_test_failures,
)

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
_PREFIX_LAYOUT_REQUIRED = "Repository layout is not loaded yet"
_PREFIX_DIAGNOSIS_FORMAT = "Your diagnosis does not satisfy the response contract"

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
    _PREFIX_LAYOUT_REQUIRED,
    _PREFIX_DIAGNOSIS_FORMAT,
)


@dataclass(frozen=True)
class ResponseNudge:
    """Instruction to retry the model after an invalid or incomplete final answer."""

    user_message: str


def nudge_for_diagnosis_format(error: str) -> ResponseNudge:
    return ResponseNudge(
        user_message=(
            f"{_PREFIX_DIAGNOSIS_FORMAT}: {error}. "
            'Reply with {"type":"final","content":{"file":"relative/path.py",'
            '"line":1,"cause":"root cause in the implementation",'
            '"evidence":"exact code expression"}}. '
            "Use the actual path, line number, and evidence from the loaded files. "
            "Do not replace the JSON object with prose or propose a patch."
        ),
    )


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


def nudge_for_missing_patch(
    *, remaining_test_output: str | None = None, task_context: str = ""
) -> ResponseNudge:
    detail = ""
    if remaining_test_output and output_reports_failures(remaining_test_output):
        summary = summarize_test_failures(remaining_test_output)
        detail = (
            f" Tests are still failing: {summary}. "
            "Fix every remaining failure, not only the requirement mentioned in "
            "the task."
        )
    return ResponseNudge(
        user_message=(
            f"{_PREFIX_MISSING_PATCH} or passing tests.{detail} "
            f"{_PROPOSE_FILE_INSTRUCTION} "
            "Use read_file or list_files only when you still need source context."
            + (
                "\nPreserve the complete task contract:\n" + task_context
                if task_context
                else ""
            )
        ),
    )


def nudge_for_unread_failure_sources(paths: list[str]) -> ResponseNudge:
    joined = ", ".join(paths[:4])
    return ResponseNudge(
        user_message=(
            f"{_PREFIX_FIX_WITHOUT_INSPECTION}. Tests already ran, but the failing "
            f"source file(s) are not loaded yet: {joined}. "
            f"Call read_file on each path, then {_PROPOSE_FILE_INSTRUCTION}"
        ),
    )


def nudge_for_repeated_read_file(path: str, *, reason: str) -> ResponseNudge:
    return ResponseNudge(
        user_message=(
            f"read_file on {path} is not needed again because {reason}. "
            f"The source is already in the conversation; "
            f"{_PROPOSE_FILE_INSTRUCTION}"
        ),
    )


def nudge_for_missing_local_modules(paths: list[str]) -> ResponseNudge:
    joined = ", ".join(paths[:3])
    return ResponseNudge(
        user_message=(
            f"The repository is missing local file(s): {joined}. "
            f"Create each missing file with {_PROPOSE_FILE_INSTRUCTION} "
            "Use the failing tests as the contract for required behavior."
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
    compact_output = sanitize_and_compact_error(output)
    return ResponseNudge(
        user_message=(
            f"{_PREFIX_CORRUPT_PATCH}.\n"
            f"Output:\n{compact_output}\n"
            f"Do not hand-write a unified diff. {_PROPOSE_FILE_INSTRUCTION} "
            f"{_PREFIX_PATCH_CORRECTION} that fixes the failures."
        ),
    )


def nudge_for_fix_without_inspection() -> ResponseNudge:
    return ResponseNudge(
        user_message=(
            f"{_PREFIX_FIX_WITHOUT_INSPECTION}. "
            "Inspect the repository with list_files, search_code, or read_file as "
            "needed, then call propose_file when you know the target path and content."
        ),
    )


def nudge_for_layout_required() -> ResponseNudge:
    return ResponseNudge(
        user_message=(
            f"{_PREFIX_LAYOUT_REQUIRED}. Call list_files to see which directories "
            "and files exist before propose_file. Do not assume conventional layouts "
            f"such as tests/ or src/. Then {_PROPOSE_FILE_INSTRUCTION}"
        ),
    )


def nudge_after_layout_loaded() -> ResponseNudge:
    return ResponseNudge(
        user_message=(
            f"{PIPELINE_FALLBACK_PREFIX} list_files loaded the repository layout. "
            "Choose a repository-relative path that matches the listing. Do not "
            "assume directories such as tests/ or src/ exist unless they appear "
            f"there. Then {_PROPOSE_FILE_INSTRUCTION}"
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
            "from the request, then choose the next repository tool yourself or "
            'return {"type":"final","content":"..."}. '
            "Do not ask the user for paths or details you can discover with tools."
        ),
    )


def _assertion_correction_hints(output: str) -> str:
    hints: list[str] = []
    for actual, expected in extract_assertion_mismatches(output):
        hints.append(f"expected {expected!r}, but the code returned {actual!r}")
        if expected.endswith(".") and not actual.endswith("."):
            hints.append(
                "the expected value ends with a trailing period that is missing "
                f"from {actual!r}"
            )
        elif len(expected) > len(actual) and expected.startswith(actual):
            suffix = expected[len(actual) :]
            hints.append(f"the expected value adds {suffix!r} after {actual!r}")
    if not hints:
        return ""
    return " Assertion hints: " + " ".join(hints[:3]) + "."


def nudge_for_patch_correction(
    reason: str,
    output: str,
    *,
    failure_kind: FailureKind | None = None,
) -> ResponseNudge:
    compact_output = sanitize_and_compact_error(output)
    if failure_kind is not None:
        return nudge_for_failure_kind(failure_kind, reason, compact_output)
    if "corrupt patch" in output.lower():
        return nudge_for_corrupt_patch(compact_output)
    assertion_hints = _assertion_correction_hints(output)
    return ResponseNudge(
        user_message=(
            f"{reason}\n"
            f"Output:\n{compact_output}\n"
            f"{_PREFIX_PATCH_CORRECTION} that fixes the failures.{assertion_hints} "
            "Do not repeat the same change. Read the failed assertion carefully, "
            f"work out the expected value, and {_PROPOSE_FILE_INSTRUCTION}"
        ),
    )


def nudge_for_failure_kind(
    kind: FailureKind,
    reason: str,
    output: str,
) -> ResponseNudge:
    """Return a recovery nudge tailored to the classified failure kind."""

    compact_output = sanitize_and_compact_error(output)
    label = failure_kind_label(kind)
    guidance = _FAILURE_GUIDANCE[kind]
    assertion_hints = ""
    if kind is FailureKind.CODE:
        assertion_hints = _assertion_correction_hints(output)
    return ResponseNudge(
        user_message=(
            f"{reason}\n"
            f"Failure kind: {kind.value} ({label}).\n"
            f"Output:\n{compact_output}\n"
            f"{guidance}{assertion_hints} {_PROPOSE_FILE_INSTRUCTION}"
        ),
    )


_FAILURE_GUIDANCE = {
    FailureKind.CODE: (
        "Inspect the failing assertion and test output carefully, then provide "
        "corrected file content."
    ),
    FailureKind.DEPENDENCY: (
        "The failure looks like a missing import. If a local module or file is "
        "missing, create it with propose_file. Otherwise verify imports against "
        "the loaded source files before proposing changes."
    ),
    FailureKind.DOCKER: (
        "The Docker sandbox failed before tests could run. Retry only after the "
        "environment issue is resolved or use an approved local fallback."
    ),
    FailureKind.TIMEOUT: (
        "The test command timed out. Propose a smaller, focused fix rather than "
        "adding expensive work."
    ),
    FailureKind.PATCH_INVALID: (
        "The patch format or paths were rejected. Do not hand-write a diff;"
    ),
    FailureKind.PATCH_APPLY: (
        "The patch could not be applied to the current file contents. Re-read the "
        "target file and"
    ),
    FailureKind.MODEL_FORMAT: (
        "The diff format was invalid. Do not hand-write a unified diff;"
    ),
    FailureKind.UNKNOWN: _PREFIX_PATCH_CORRECTION + " that fixes the failures.",
}


def nudge_for_propose_file_failure(error: str, *, path: object = None) -> ResponseNudge:
    example = json.dumps(
        {
            "name": "propose_file",
            "arguments": {
                "path": path if isinstance(path, str) else "relative/path.py",
                "content": "<complete replacement file text>",
            },
        },
        ensure_ascii=False,
    )
    layout_hint = ""
    if "parent directory does not exist" in error.lower():
        layout_hint = (
            " Call list_files if the layout is not already in the conversation, "
            "then choose a path under an existing directory or the repository root."
        )
    return ResponseNudge(
        user_message=(
            f"{_PREFIX_PROPOSE_FILE_FAILURE}: {error} "
            "No valid proposal was produced by this call. "
            f"Fix the issue and {_PROPOSE_FILE_INSTRUCTION}{layout_hint}\n"
            f"Next response shape: {example}\n"
            "Replace the content placeholder with the entire corrected file, "
            "encoded as a JSON string. Put both path and content inside arguments. "
            "Do not send a final explanation or omit unchanged parts of the file."
        ),
    )
