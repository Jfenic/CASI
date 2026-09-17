"""Terminal styling, color palettes, and glyph definitions for CASI."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass


def _should_use_color(force_color: bool | None = None) -> bool:
    if force_color is not None:
        return force_color
    if os.environ.get("NO_COLOR", "").strip() != "":
        return False
    if os.environ.get("TERM", "").lower() == "dumb":
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _should_use_unicode(force_unicode: bool | None = None) -> bool:
    if force_unicode is not None:
        return force_unicode
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        "›◆✓✗─".encode(encoding)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


@dataclass(frozen=True, slots=True)
class Glyphs:
    """Symbols and branch characters for terminal output."""

    prompt: str
    agent: str
    success: str
    error: str
    warning: str
    hint: str
    tree_branch: str
    tree_last: str
    tree_pipe: str
    tree_dash: str
    bullet: str
    ellipsis: str

    @classmethod
    def unicode(cls) -> Glyphs:
        return cls(
            prompt="›",
            agent="◆",
            success="✓",
            error="✗",
            warning="!",
            hint="💡",
            tree_branch="├─",
            tree_last="└─",
            tree_pipe="│ ",
            tree_dash="──",
            bullet="•",
            ellipsis="…",
        )

    @classmethod
    def ascii(cls) -> Glyphs:
        return cls(
            prompt=">",
            agent="*",
            success="+",
            error="x",
            warning="!",
            hint="*",
            tree_branch="|-",
            tree_last=r"\-",
            tree_pipe="| ",
            tree_dash="--",
            bullet="-",
            ellipsis="...",
        )


class Theme:
    """ANSI color scheme and formatting with graceful plain-text fallback."""

    # ANSI Escape sequences
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Semantic 4-5 Color Palette
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    GRAY = "\033[90m"

    # Bright variants for headers
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_WHITE = "\033[97m"

    def __init__(
        self,
        *,
        use_color: bool | None = None,
        use_unicode: bool | None = None,
    ) -> None:
        self.color_enabled = _should_use_color(use_color)
        self.glyphs = (
            Glyphs.unicode() if _should_use_unicode(use_unicode) else Glyphs.ascii()
        )

    def _apply(self, text: str, code: str) -> str:
        if not self.color_enabled or not text:
            return text
        return f"{code}{text}{self.RESET}"

    # Text style helpers
    def bold(self, text: str) -> str:
        return self._apply(text, self.BOLD)

    def dim(self, text: str) -> str:
        return self._apply(text, self.DIM)

    def muted(self, text: str) -> str:
        return self._apply(text, self.GRAY)

    # Semantic roles
    def user(self, text: str) -> str:
        """User input role: bold cyan prompt icon + crisp text."""
        icon = self._apply(self.glyphs.prompt, self.BRIGHT_CYAN + self.BOLD)
        return f"{icon} {text}"

    def agent(self, text: str) -> str:
        """Agent role: distinct magenta/cyan symbol."""
        icon = self._apply(self.glyphs.agent, self.BRIGHT_CYAN + self.BOLD)
        return f"{icon} {text}"

    def success(self, text: str) -> str:
        """Success role: green check."""
        icon = self._apply(self.glyphs.success, self.BRIGHT_GREEN + self.BOLD)
        return f"{icon} {text}"

    def error(self, text: str) -> str:
        """Error role: red cross."""
        icon = self._apply(self.glyphs.error, self.BRIGHT_RED + self.BOLD)
        return f"{icon} {text}"

    def warning(self, text: str) -> str:
        """Warning role: yellow mark."""
        icon = self._apply(self.glyphs.warning, self.YELLOW + self.BOLD)
        return f"{icon} {text}"

    def hint(self, text: str) -> str:
        """Hint or suggestion role."""
        prefix = self._apply(f"[{self.glyphs.hint}]", self.YELLOW)
        return f"{prefix} {text}"

    def branch(self, text: str) -> str:
        """Tree branch decoration: muted/gray."""
        return self._apply(text, self.GRAY)

    def diff_add(self, text: str) -> str:
        """Diff line addition: green."""
        return self._apply(text, self.GREEN)

    def diff_remove(self, text: str) -> str:
        """Diff line removal: red."""
        return self._apply(text, self.RED)

    def diff_header(self, text: str) -> str:
        """Diff chunk header: cyan/bold."""
        return self._apply(text, self.CYAN)
