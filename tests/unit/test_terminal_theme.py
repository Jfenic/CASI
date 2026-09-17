from __future__ import annotations

import os
from unittest.mock import patch

from casi.terminal.theme import Glyphs, Theme, _should_use_color


def test_theme_respects_no_color_env() -> None:
    with patch.dict(os.environ, {"NO_COLOR": "1"}):
        assert _should_use_color() is False


def test_theme_respects_dumb_term() -> None:
    with patch.dict(os.environ, {"TERM": "dumb", "NO_COLOR": ""}):
        assert _should_use_color() is False


def test_theme_force_color_overrides_env() -> None:
    with patch.dict(os.environ, {"NO_COLOR": "1"}):
        assert _should_use_color(force_color=True) is True
        assert _should_use_color(force_color=False) is False


def test_glyphs_unicode_and_ascii() -> None:
    u = Glyphs.unicode()
    a = Glyphs.ascii()

    assert u.prompt == "›"
    assert u.agent == "◆"
    assert u.success == "✓"
    assert u.tree_branch == "├─"

    assert a.prompt == ">"
    assert a.agent == "*"
    assert a.success == "+"
    assert a.tree_branch == "|-"


def test_theme_formatting_when_colors_disabled() -> None:
    theme = Theme(use_color=False, use_unicode=True)

    assert theme.user("my input") == "› my input"
    assert theme.agent("thinking") == "◆ thinking"
    assert theme.success("done") == "✓ done"
    assert theme.error("failed") == "✗ failed"
    assert theme.warning("watch out") == "! watch out"
    assert "[💡]" in theme.hint("try this")


def test_theme_formatting_when_colors_enabled() -> None:
    theme = Theme(use_color=True, use_unicode=True)

    formatted_user = theme.user("hello")
    assert "\033[" in formatted_user
    assert "hello" in formatted_user

    formatted_error = theme.error("bad error")
    assert "\033[" in formatted_error
    assert "bad error" in formatted_error
