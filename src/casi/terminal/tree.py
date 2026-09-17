"""Tree formatting for hierarchical agent steps and tool execution."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from casi.terminal.theme import Theme


@dataclass(slots=True)
class TreeNode:
    """A node in an execution or activity tree."""

    label: str
    children: list[TreeNode] = field(default_factory=list)
    badge: str | None = None
    status: str | None = None  # "ok", "error", "running", or custom symbol

    def add_child(
        self,
        label: str,
        *,
        badge: str | None = None,
        status: str | None = None,
    ) -> TreeNode:
        child = TreeNode(label=label, badge=badge, status=status)
        self.children.append(child)
        return child


def render_tree(
    nodes: Sequence[TreeNode],
    *,
    theme: Theme | None = None,
    indent: str = "",
) -> str:
    """Render a sequence of tree nodes into a clean terminal string."""
    t = theme or Theme()
    lines: list[str] = []

    for index, node in enumerate(nodes):
        is_last = index == len(nodes) - 1
        branch = t.glyphs.tree_last if is_last else t.glyphs.tree_branch
        branch_colored = t.branch(branch)

        # Status badge if present
        status_str = ""
        if node.status == "ok":
            status_str = f" {t.success('')}".strip() + " "
        elif node.status == "error":
            status_str = f" {t.error('')}".strip() + " "
        elif node.status:
            status_str = f"[{node.status}] "

        badge_str = f" {t.dim(node.badge)}" if node.badge else ""
        line = f"{indent}{branch_colored} {status_str}{node.label}{badge_str}"
        lines.append(line)

        # Recurse children with proper continuation indent
        if node.children:
            next_indent = indent + (
                "   " if is_last else f"{t.branch(t.glyphs.tree_pipe)} "
            )
            child_text = render_tree(
                node.children,
                theme=t,
                indent=next_indent,
            )
            if child_text:
                lines.append(child_text)

    return "\n".join(lines)
