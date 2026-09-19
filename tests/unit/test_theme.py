from __future__ import annotations

from casi.terminal.theme import Theme


def test_theme_user_prompt_wraps_ansi_codes_in_readline_markers() -> None:
    theme = Theme(use_color=True, use_unicode=True)
    prompt = theme.user("CASI> ")

    # Readline requires \001 (start ignore) and \002 (end ignore) around ANSI codes
    assert "\001" in prompt
    assert "\002" in prompt
    assert prompt.endswith("CASI> ")


def test_theme_user_prompt_without_color_has_no_ansi() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    prompt = theme.user("CASI> ")

    assert "\001" not in prompt
    assert "\002" not in prompt
    assert "CASI> " in prompt
