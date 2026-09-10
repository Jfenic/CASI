"""Finalize one-shot CLI agent runs: patches, exit codes, and verbose output."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

from casi.agent.orchestrator import OrchestratorResult
from casi.agent.run_outcome import resolve_agent_run_outcome
from casi.patching.applier import PatchApplicationError, apply_patch

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_PATCH_PENDING = 2


def finalize_agent_run(
    repository: str | Path,
    result: OrchestratorResult,
    *,
    save_patch: str | None = None,
    yes: bool = False,
    verbose: bool = False,
    input_fn: Callable[[str], str] = input,
) -> int:
    """Print agent output and optionally save or apply a proposed patch."""

    outcome = resolve_agent_run_outcome(repository, result)

    if not outcome.success:
        print(
            outcome.error or "Agent failed without an error message.", file=sys.stderr
        )
        _emit_verbose_trace(outcome.plan, outcome.trace, verbose=verbose)
        return EXIT_ERROR

    _emit_verbose_trace(outcome.plan, outcome.trace, verbose=verbose)

    if outcome.test_runner is not None:
        status = "passed" if outcome.tests_passed else "failed"
        print(
            f"[tests:{status} via {outcome.test_runner}] "
            f"{outcome.test_output or 'No test output.'}",
            file=sys.stderr,
        )

    if outcome.patch is None:
        if outcome.requested_code_change:
            print(
                "[hint] No valid unified diff was returned. "
                "Ask CASI again to provide a ```diff patch.",
                file=sys.stderr,
            )
        print(outcome.response)
        return EXIT_SUCCESS

    print(f"[patch] {outcome.patch_error or 'Patch is valid'}", file=sys.stderr)
    print(outcome.patch)

    if not outcome.patch_valid:
        return EXIT_ERROR

    if outcome.tests_passed is False:
        print(
            "[error] Patch was not applied because its sandbox tests failed. "
            "No repository files were changed.",
            file=sys.stderr,
        )
        return EXIT_ERROR

    saved = False
    if save_patch is not None:
        path = Path(save_patch)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(outcome.patch, encoding="utf-8")
        print(f"Patch saved to: {path.resolve()}", file=sys.stderr)
        saved = True

    should_apply = yes
    if not yes:
        answer = input_fn("Apply patch? [y/N] ").strip().lower()
        should_apply = answer in {"y", "yes"}

    if not should_apply:
        print("Patch rejected; no files were changed.", file=sys.stderr)
        return EXIT_SUCCESS if saved else EXIT_PATCH_PENDING

    try:
        files = apply_patch(
            repository,
            outcome.patch,
            approved=True,
            dry_run=False,
        )
    except PatchApplicationError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return EXIT_ERROR

    print(f"Patch applied to: {', '.join(files)}", file=sys.stderr)
    return EXIT_SUCCESS


def _emit_verbose_trace(
    plan: tuple[str, ...],
    trace: tuple[str, ...],
    *,
    verbose: bool,
) -> None:
    if not verbose:
        return
    if plan:
        print("[plan]", file=sys.stderr)
        for line in plan:
            print(line, file=sys.stderr)
    if trace:
        print("[trace]", file=sys.stderr)
        for line in trace:
            print(line, file=sys.stderr)
