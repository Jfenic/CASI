from __future__ import annotations

from casi.terminal.fold import fold_output
from casi.terminal.theme import Theme


def test_fold_output_short_text_unchanged() -> None:
    text = "line 1\nline 2\nline 3"
    assert fold_output(text, max_lines=5) == text


def test_fold_output_collapses_when_exceeding_max_lines() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    lines = [f"line {i}" for i in range(1, 21)]
    text = "\n".join(lines)

    folded = fold_output(
        text,
        max_lines=10,
        head_lines=3,
        tail_lines=2,
        theme=theme,
    )
    result_lines = folded.splitlines()

    assert len(result_lines) == 6  # 3 head + 1 fold marker + 2 tail
    assert result_lines[0] == "line 1"
    assert result_lines[1] == "line 2"
    assert result_lines[2] == "line 3"
    assert "[15 lines collapsed]" in result_lines[3]
    assert result_lines[4] == "line 19"
    assert result_lines[5] == "line 20"
