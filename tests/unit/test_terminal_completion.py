from __future__ import annotations

from pathlib import Path

from casi.terminal.completion import (
    DEFAULT_SLASH_COMMANDS,
    InteractiveCompleter,
    extract_file_mentions,
)


def test_default_commands_present() -> None:
    assert "/help" in DEFAULT_SLASH_COMMANDS
    assert "/diff" in DEFAULT_SLASH_COMMANDS
    assert "/plan" in DEFAULT_SLASH_COMMANDS
    assert "/exit" in DEFAULT_SLASH_COMMANDS


def test_command_completion(tmp_path: Path) -> None:
    completer = InteractiveCompleter(tmp_path)

    # First match
    first = completer.complete("/h", 0)
    assert first in {"/help", "/history"}

    # Exhaustion
    state = 0
    matches = []
    while True:
        m = completer.complete("/di", state)
        if m is None:
            break
        matches.append(m)
        state += 1

    assert matches == ["/diff"]


def test_file_mention_completion(tmp_path: Path) -> None:
    # Create fake repository structure
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("# auth\n", encoding="utf-8")
    (src / "login.py").write_text("# login\n", encoding="utf-8")

    completer = InteractiveCompleter(tmp_path)

    matches = completer.get_matches("@src/")
    assert "@src/auth.py" in matches
    assert "@src/login.py" in matches


def test_extract_file_mentions(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')\n", encoding="utf-8")

    text = "Please inspect @src/main.py and also @src/nonexistent.py"
    mentions = extract_file_mentions(text, tmp_path)

    assert mentions == ["src/main.py"]
