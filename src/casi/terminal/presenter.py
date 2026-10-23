"""Terminal presenter coordinating themes, trees, diffs, and output formatting."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol

from casi.config import settings
from casi.terminal.diff_view import FileDiffStat, format_compact_diff
from casi.terminal.fold import fold_output
from casi.terminal.panel import render_panel
from casi.terminal.review import review_patch
from casi.terminal.session_metrics import SessionMetrics
from casi.terminal.spinner import Spinner
from casi.terminal.test_summary import format_test_summary
from casi.terminal.theme import Theme
from casi.terminal.tree import TreeNode, render_tree


def _detect_git_branch(repository: str | Path) -> str | None:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repository),
            capture_output=True,
            text=True,
            timeout=1.0,
        )
        if res.returncode == 0:
            branch = res.stdout.strip()
            if branch and branch != "HEAD":
                return branch
    except Exception:
        pass
    return None


class PresenterProtocol(Protocol):
    """Structural protocol for terminal presenters."""

    def user(self, text: str) -> None: ...
    def agent(self, text: str) -> None: ...
    def success(self, text: str) -> None: ...
    def error(self, text: str, *, hint: str | None = None) -> None: ...
    def warning(self, text: str) -> None: ...
    def hint(self, text: str) -> None: ...
    def diff(self, diff_text: str, *, max_lines: int | None = 60) -> None: ...
    def tree(self, nodes: Sequence[TreeNode]) -> None: ...
    def session_summary(self, metrics: SessionMetrics) -> None: ...
    def panel(
        self,
        lines: Sequence[str],
        *,
        title: str | None = None,
        subtitle: str | None = None,
        width: int | None = None,
    ) -> None: ...
    def prompt(self, status: str | None = None) -> str: ...


class TerminalPresenter:
    """Coordinates clean visual hierarchy, semantic coloring, and compact views."""

    def __init__(
        self,
        *,
        output_fn: Callable[[str], None] = print,
        theme: Theme | None = None,
        use_color: bool | None = None,
        use_unicode: bool | None = None,
    ) -> None:
        self.output_fn = output_fn
        self.theme = theme or Theme(use_color=use_color, use_unicode=use_unicode)

    def _emit(self, text: str) -> None:
        self.output_fn(text)
        if hasattr(sys.stdout, "flush"):
            sys.stdout.flush()

    def user(self, text: str) -> None:
        """Render user input prompt."""
        self._emit(self.theme.user(text))

    def agent(self, text: str) -> None:
        """Render agent message or final response."""
        self._emit(self.theme.agent(text))

    def success(self, text: str) -> None:
        """Render success checkmark."""
        self._emit(self.theme.success(text))

    def error(self, text: str, *, hint: str | None = None) -> None:
        """Render error message with optional actionable hint."""
        self._emit(self.theme.error(text))
        if hint:
            self._emit(self.theme.hint(hint))

    def warning(self, text: str) -> None:
        """Render warning message."""
        self._emit(self.theme.warning(text))

    def hint(self, text: str) -> None:
        """Render actionable hint."""
        self._emit(self.theme.hint(text))

    def plan(self, original_task: str, steps: Sequence[str]) -> None:
        """Render an execution plan hierarchically."""
        self._emit(f"{self.theme.agent('Plan')} {self.theme.dim(f'({original_task})')}")
        nodes = [TreeNode(label=step) for step in steps]
        if nodes:
            self._emit(render_tree(nodes, theme=self.theme))

    def step_start(
        self,
        step_number: int,
        total_steps: int,
        agent_name: str,
        role: str,
    ) -> None:
        """Render the start of an execution phase."""
        prefix = self.theme.agent(f"Step {step_number}/{total_steps}:")
        self._emit(f"{prefix} {agent_name} {self.theme.dim(f'({role})')}")

    def tool_call(
        self,
        name: str,
        summary: str = "",
        *,
        status: str | None = "ok",
    ) -> None:
        """Render a single tool execution line in tree style."""
        badge = f"({summary})" if summary else None
        node = TreeNode(label=name, badge=badge, status=status)
        self._emit(render_tree([node], theme=self.theme))

    def tree(self, nodes: Sequence[TreeNode]) -> None:
        """Render an arbitrary tree of operations."""
        self._emit(render_tree(nodes, theme=self.theme))

    def diff(self, diff_text: str, *, max_lines: int | None = 60) -> None:
        """Render a compact, highlighted unified diff."""
        formatted = format_compact_diff(
            diff_text,
            theme=self.theme,
            max_lines=max_lines,
        )
        if formatted:
            self._emit(formatted)

    def folded(
        self,
        text: str,
        *,
        max_lines: int = 15,
        head_lines: int = 6,
        tail_lines: int = 4,
    ) -> None:
        """Render folded output if text exceeds max_lines."""
        self._emit(
            fold_output(
                text,
                max_lines=max_lines,
                head_lines=head_lines,
                tail_lines=tail_lines,
                theme=self.theme,
            )
        )

    def confirm(
        self,
        prompt: str,
        *,
        default: bool = False,
        input_fn: Callable[[str], str] = input,
    ) -> bool:
        """Ask a yes/no confirmation prompt."""
        suffix = " [Y/n] " if default else " [y/N] "
        formatted_prompt = f"{self.theme.glyphs.prompt}{suffix}{prompt}"
        answer = input_fn(formatted_prompt).strip().lower()
        if not answer:
            return default
        return answer in {"y", "yes", "s", "si", "sí"}

    def test_result(
        self,
        *,
        passed: bool,
        runner: str,
        output: str,
        max_failure_lines: int = 15,
    ) -> None:
        """Render parsed and formatted test results."""
        summary = format_test_summary(
            output,
            passed=passed,
            runner=runner,
            theme=self.theme,
            max_failure_lines=max_failure_lines,
        )
        self._emit(summary)

    def review_patch(
        self,
        patch: str,
        stats: list[FileDiffStat],
        *,
        input_fn: Callable[[str], str] = input,
    ) -> tuple[bool, str | None]:
        """Run interactive review for a proposed patch."""
        return review_patch(
            patch,
            stats,
            input_fn=input_fn,
            presenter=self,
        )

    @contextmanager
    def status(self, message: str):
        """Show immediate progress spinner during long-running operations."""
        spinner = Spinner(message, theme=self.theme)
        spinner.start()
        try:
            yield spinner
        finally:
            spinner.stop()

    def session_summary(self, metrics: SessionMetrics) -> None:
        """Render session summary metrics tree."""
        self._emit(metrics.format_summary(theme=self.theme))

    def panel(
        self,
        lines: Sequence[str],
        *,
        title: str | None = None,
        subtitle: str | None = None,
        width: int | None = None,
    ) -> None:
        """Render a bordered terminal panel."""
        self._emit(
            render_panel(
                lines,
                title=title,
                subtitle=subtitle,
                width=width,
                theme=self.theme,
            )
        )

    def prompt(self, status: str | None = None) -> str:
        """Render a clean, modern input prompt (e.g. 'casi ❯ ')."""
        t = self.theme
        if not t.color_enabled and t.glyphs.prompt == ">":
            return f"casi [{status}]> " if status else "casi> "

        if status:
            return (
                f"\001{t.BRIGHT_CYAN}{t.BOLD}\002casi\001{t.RESET}\002 "
                f"\001{t.YELLOW}\002[{status}]\001{t.RESET}\002 "
                f"\001{t.CYAN}\002❯\001{t.RESET}\002 "
            )
        return (
            f"\001{t.BRIGHT_CYAN}{t.BOLD}\002casi\001{t.RESET}\002 "
            f"\001{t.CYAN}\002❯\001{t.RESET}\002 "
        )

    def welcome_banner(
        self,
        *,
        repository: str | Path,
        model: str | None = None,
        provider: str | None = None,
        routing_mode: str = "assist",
    ) -> None:
        """Render welcoming header card for interactive mode."""
        repo_name = Path(repository).resolve().name
        branch = _detect_git_branch(repository)
        branch_str = f" [git: {branch}]" if branch else ""
        model_str = model or settings.ollama_model
        provider_str = provider or settings.llm_provider
        sandbox_str = (
            f"Docker isolated ({settings.docker_image})"
            if settings.use_docker_sandbox
            else "Local fallback (unisolated)"
        )

        t = self.theme
        cyan = t.BRIGHT_CYAN if t.color_enabled else ""
        reset = t.RESET if t.color_enabled else ""
        bold = t.BOLD if t.color_enabled else ""
        dim = t.DIM if t.color_enabled else ""

        lines = [
            f"{cyan}{bold}  ____ ___    _____ ____ {reset}",
            (
                f"{cyan}{bold} / __//   |  / ___//  _/ {reset}  "
                f"{bold}CASI • Local AI Software Engineer{reset}"
            ),
            (
                f"{cyan}{bold}/ /  / /| |  \\__ \\ / /   {reset}  "
                f"{dim}Model   :{reset} {bold}{model_str}{reset} "
                f"{dim}({provider_str} • {routing_mode}){reset}"
            ),
            (
                f"{cyan}{bold}/ /__/ ___ | ___/ // /   {reset}  "
                f"{dim}Sandbox :{reset} {sandbox_str}"
            ),
            (
                f"{cyan}{bold}\\___/_/  |_|/____//___/  {reset}  "
                f"{dim}Repo    :{reset} {bold}{repo_name}{reset}"
                f"{dim}{branch_str}{reset}"
            ),
            "",
            (
                f" {dim}Guard   :{reset} "
                f"apply_patch requires human confirmation [y/N/v/save/?]"
            ),
            (
                f" {dim}Commands:{reset} {bold}/help{reset} • {bold}/status{reset} • "
                f"{bold}/explain{reset} • {bold}/diff{reset} • "
                f"{bold}/undo{reset} • {bold}/exit{reset}"
            ),
            (
                f" {dim}Hint    :{reset} "
                f"Type {bold}@file{reset} to autocomplete paths with Tab"
            ),
        ]
        self.panel(lines, title="CASI", subtitle="v0.1.0")

    def status_card(
        self,
        items: dict[str, str],
        *,
        title: str = "System Status",
    ) -> None:
        """Render key-value system status information."""
        lines = [
            f"• {key.ljust(13)}: {self.theme.bold(val)}" for key, val in items.items()
        ]
        self.panel(lines, title=title)
