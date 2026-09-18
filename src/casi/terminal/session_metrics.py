"""Session metrics tracking and summary presentation for CASI interactive mode."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field

from casi.terminal.theme import Theme
from casi.terminal.tree import TreeNode, render_tree


@dataclass
class SessionMetrics:
    """Tracks metrics and activity during an interactive session."""

    start_time: float = field(default_factory=time.monotonic)
    turns_completed: int = 0
    total_steps: int = 0
    patches_proposed: int = 0
    patches_applied: int = 0
    patches_undone: int = 0
    modified_files: set[str] = field(default_factory=set)
    tool_counts: dict[str, int] = field(default_factory=dict)

    def record_turn(self) -> None:
        """Record the start or completion of a user turn."""
        self.turns_completed += 1

    def record_step(self) -> None:
        """Record an agent execution step."""
        self.total_steps += 1

    def record_tool_call(self, name: str) -> None:
        """Record execution of a specific tool."""
        self.tool_counts[name] = self.tool_counts.get(name, 0) + 1

    def record_patch_proposed(self) -> None:
        """Record that a model response contained a patch."""
        self.patches_proposed += 1

    def record_patch_applied(self, files: Sequence[str]) -> None:
        """Record that a patch was applied to repository files."""
        self.patches_applied += 1
        self.modified_files.update(files)

    def record_patch_undone(
        self,
        files: Sequence[str],
        *,
        still_modified: Sequence[str] | None = None,
    ) -> None:
        """Record that a patch was undone and adjust modified files."""
        self.patches_undone += 1
        if still_modified is not None:
            self.modified_files = set(still_modified)
        else:
            for f in files:
                self.modified_files.discard(f)

    @property
    def duration_seconds(self) -> float:
        """Elapsed time in seconds since session creation."""
        return max(0.0, time.monotonic() - self.start_time)

    def format_duration(self) -> str:
        """Format elapsed time in a clean human-readable string."""
        total_seconds = int(self.duration_seconds)
        if total_seconds < 1:
            return "< 1s"
        if total_seconds < 60:
            return f"{total_seconds}s"
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        if minutes < 60:
            return f"{minutes}m {seconds:02d}s"
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours}h {remaining_minutes:02d}m"

    def format_summary(self, theme: Theme | None = None) -> str:
        """Render a formatted summary of session metrics using tree formatting."""
        t = theme or Theme()

        nodes: list[TreeNode] = [
            TreeNode(label=f"Duration: {self.format_duration()}"),
            TreeNode(label=f"Tasks completed: {self.turns_completed}"),
        ]

        if self.total_steps > 0:
            nodes.append(TreeNode(label=f"Agent steps: {self.total_steps}"))

        patches_label = (
            f"Patches: {self.patches_proposed} proposed, "
            f"{self.patches_applied} applied, "
            f"{self.patches_undone} undone"
        )
        nodes.append(TreeNode(label=patches_label))

        files_str = (
            ", ".join(sorted(self.modified_files)) if self.modified_files else "none"
        )
        nodes.append(TreeNode(label=f"Files modified: {files_str}"))

        total_tools = sum(self.tool_counts.values())
        if total_tools > 0:
            breakdown = ", ".join(
                f"{k}: {v}" for k, v in sorted(self.tool_counts.items())
            )
            tools_label = f"Tools executed: {total_tools} ({breakdown})"
        else:
            tools_label = "Tools executed: 0"
        nodes.append(TreeNode(label=tools_label))

        tree_output = render_tree(nodes, theme=t)
        header = t.agent("Session summary:")
        return f"{header}\n{tree_output}"


def format_session_summary(
    metrics: SessionMetrics,
    theme: Theme | None = None,
) -> str:
    """Format session metrics into a display string."""
    return metrics.format_summary(theme=theme)
