from __future__ import annotations

from pathlib import Path

from casi.terminal.diff_view import FileDiffStat
from casi.terminal.presenter import TerminalPresenter
from casi.terminal.review import PatchAction, parse_patch_action, review_patch
from casi.terminal.theme import Theme

_SAMPLE_PATCH = """--- a/src/calc.py
+++ b/src/calc.py
@@ -1,2 +1,3 @@
 def add(a, b):
-    return 0
+    return a + b
"""


def test_parse_patch_action() -> None:
    assert parse_patch_action("y") == PatchAction.APPLY
    assert parse_patch_action("yes") == PatchAction.APPLY
    assert parse_patch_action("si") == PatchAction.APPLY
    assert parse_patch_action("n") == PatchAction.REJECT
    assert parse_patch_action("no") == PatchAction.REJECT
    assert parse_patch_action("") == PatchAction.REJECT
    assert parse_patch_action("v") == PatchAction.VIEW_FULL
    assert parse_patch_action("view") == PatchAction.VIEW_FULL
    assert parse_patch_action("save") == PatchAction.SAVE
    assert parse_patch_action("?") == PatchAction.HELP


def test_review_patch_immediate_apply() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    presenter = TerminalPresenter(theme=theme)
    stats = [FileDiffStat(path="src/calc.py", insertions=1, deletions=1)]

    applied, path = review_patch(
        _SAMPLE_PATCH,
        stats,
        input_fn=lambda _: "y",
        presenter=presenter,
    )
    assert applied is True
    assert path is None


def test_review_patch_immediate_reject() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    presenter = TerminalPresenter(theme=theme)
    stats = [FileDiffStat(path="src/calc.py", insertions=1, deletions=1)]

    applied, path = review_patch(
        _SAMPLE_PATCH,
        stats,
        input_fn=lambda _: "n",
        presenter=presenter,
    )
    assert applied is False
    assert path is None


def test_review_patch_view_full_then_apply() -> None:
    output: list[str] = []
    theme = Theme(use_color=False, use_unicode=True)
    presenter = TerminalPresenter(output_fn=output.append, theme=theme)
    stats = [FileDiffStat(path="src/calc.py", insertions=1, deletions=1)]
    answers = iter(["v", "y"])

    applied, path = review_patch(
        _SAMPLE_PATCH,
        stats,
        input_fn=lambda _: next(answers),
        presenter=presenter,
    )
    assert applied is True
    assert path is None
    assert any("Full Patch Diff:" in line for line in output)
    assert any("+    return a + b" in line for line in output)


def test_review_patch_save_then_apply(tmp_path: Path) -> None:
    output: list[str] = []
    theme = Theme(use_color=False, use_unicode=True)
    presenter = TerminalPresenter(output_fn=output.append, theme=theme)
    stats = [FileDiffStat(path="src/calc.py", insertions=1, deletions=1)]

    target_file = tmp_path / "patch.diff"
    answers = iter(["save", str(target_file), "y"])

    applied, saved_path = review_patch(
        _SAMPLE_PATCH,
        stats,
        input_fn=lambda _: next(answers),
        presenter=presenter,
    )
    assert applied is True
    assert saved_path == str(target_file.resolve())
    assert target_file.exists()
    assert "return a + b" in target_file.read_text(encoding="utf-8")
    assert any("Patch saved to:" in line for line in output)
