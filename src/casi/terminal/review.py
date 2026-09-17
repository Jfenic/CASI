"""Interactive patch review and confirmation workflow."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from casi.terminal.diff_view import FileDiffStat, format_compact_diff

if TYPE_CHECKING:
    from casi.terminal.presenter import TerminalPresenter


class PatchAction(StrEnum):
    """User choice when reviewing a proposed patch."""

    APPLY = "apply"
    REJECT = "reject"
    VIEW_FULL = "view_full"
    SAVE = "save"
    HELP = "help"


def parse_patch_action(answer: str) -> PatchAction:
    """Normalize user confirmation input to a PatchAction."""
    normalized = answer.strip().lower()
    if not normalized or normalized in {"n", "no"}:
        return PatchAction.REJECT
    if normalized in {"y", "yes", "s", "si", "sí"}:
        return PatchAction.APPLY
    if normalized in {"v", "view", "ver", "diff"}:
        return PatchAction.VIEW_FULL
    if normalized in {"save", "guardar"}:
        return PatchAction.SAVE
    if normalized in {"?", "h", "help", "ayuda"}:
        return PatchAction.HELP
    # Single letter 's' might collide with Spanish 'sí', handled above if exact
    return PatchAction.REJECT


def review_patch(
    patch: str,
    stats: list[FileDiffStat],
    *,
    input_fn: Callable[[str], str] = input,
    presenter: TerminalPresenter | None = None,
    output_fn: Callable[[str], None] = print,
) -> tuple[bool, str | None]:
    """Run an interactive prompt allowing full diff review, saving, or approval.

    Returns:
        tuple of (should_apply, saved_path)
    """
    if presenter is None:
        from casi.terminal.presenter import TerminalPresenter

        p = TerminalPresenter(output_fn=output_fn)
    else:
        p = presenter
    t = p.theme
    saved_path: str | None = None

    # Summary of target files
    files_str = ", ".join(s.path for s in stats) if stats else "files"

    prompt_label = (
        f"Apply patch to {files_str}? [y/N/v/save/?] "
        f"{t.dim('(y=apply, n=reject, v=view full diff, save=save to file)')}: "
    )

    while True:
        prompt_text = t.user(prompt_label)
        try:
            answer = input_fn(prompt_text).strip()
        except (EOFError, KeyboardInterrupt):
            p.warning("Patch rejected.")
            return False, saved_path

        action = parse_patch_action(answer)

        if action == PatchAction.APPLY:
            return True, saved_path

        if action == PatchAction.REJECT:
            return False, saved_path

        if action == PatchAction.VIEW_FULL:
            p._emit(t.bold("Full Patch Diff:"))
            p._emit(format_compact_diff(patch, theme=t, max_lines=None))
            prompt_label = f"Apply patch to {files_str}? [y/N/save]: "
            continue

        if action == PatchAction.SAVE:
            save_prompt = t.user("Save patch to path: ")
            try:
                dest = input_fn(save_prompt).strip()
            except (EOFError, KeyboardInterrupt):
                p.warning("Save cancelled.")
                continue

            if not dest:
                p.warning("No file path specified; patch not saved.")
                continue

            try:
                target = Path(dest)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(patch, encoding="utf-8")
                saved_path = str(target.resolve())
                p.success(f"Patch saved to: {saved_path}")
            except OSError as exc:
                p.error(f"Could not save patch: {exc}")

            prompt_label = f"Apply patch to {files_str}? [y/N]: "
            continue

        if action == PatchAction.HELP:
            help_lines = [
                t.bold("Available actions:"),
                f"  {t.bold('y')}    - Apply patch to the repository",
                f"  {t.bold('n')}    - Reject patch without changing files (default)",
                f"  {t.bold('v')}    - View entire diff without folding",
                f"  {t.bold('save')} - Save patch to a local .diff / .patch file",
                f"  {t.bold('?')}    - Show this help message",
            ]
            for line in help_lines:
                p._emit(line)
            continue
