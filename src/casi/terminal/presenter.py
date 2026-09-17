"""Terminal presenter coordinating themes, trees, diffs, and output formatting."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from typing import Protocol

from casi.terminal.diff_view import FileDiffStat, format_compact_diff
from casi.terminal.fold import fold_output
from casi.terminal.review import review_patch
from casi.terminal.spinner import Spinner
from casi.terminal.test_summary import format_test_summary
from casi.terminal.theme import Theme
from casi.terminal.tree import TreeNode, render_tree


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
