from __future__ import annotations

from casi.terminal.diff_view import calculate_diff_stats, format_compact_diff
from casi.terminal.theme import Theme

_SAMPLE_DIFF = """diff --git a/src/auth.py b/src/auth.py
index e69de29..b3a4a12 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,3 +1,4 @@
 def check_token(token: str) -> bool:
-    return False
+    if not token:
+        return False
+    return True
"""


def test_calculate_diff_stats() -> None:
    stats = calculate_diff_stats(_SAMPLE_DIFF)
    assert len(stats) == 1
    assert stats[0].path == "src/auth.py"
    assert stats[0].insertions == 3
    assert stats[0].deletions == 1


def test_format_compact_diff_header_and_lines() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    formatted = format_compact_diff(_SAMPLE_DIFF, theme=theme)

    lines = formatted.splitlines()
    assert lines[0] == "Diff [+3 / -1]: src/auth.py (+3, -1)"
    assert "@@ -1,3 +1,4 @@" in formatted
    assert "+    return True" in formatted
    assert "-    return False" in formatted
    # Git header noise should be omitted
    assert "diff --git" not in formatted
    assert "index " not in formatted


def test_format_compact_diff_empty() -> None:
    assert format_compact_diff("") == ""
    assert format_compact_diff("   \n") == ""


def test_format_compact_diff_truncated() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    # Long diff with 20 lines
    diff_text = """diff --git a/file.txt b/file.txt
--- a/file.txt
+++ b/file.txt
@@ -1,20 +1,20 @@
""" + "\n".join(f"+line {i}" for i in range(20))

    formatted = format_compact_diff(diff_text, theme=theme, max_lines=5)
    assert "more diff lines folded" in formatted
