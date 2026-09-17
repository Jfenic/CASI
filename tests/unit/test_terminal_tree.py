from __future__ import annotations

from casi.terminal.theme import Theme
from casi.terminal.tree import TreeNode, render_tree


def test_render_single_node() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    node = TreeNode(label="Single task")
    rendered = render_tree([node], theme=theme)

    assert rendered == "└─ Single task"


def test_render_multiple_nodes() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    nodes = [
        TreeNode(label="Step 1"),
        TreeNode(label="Step 2"),
        TreeNode(label="Step 3"),
    ]
    rendered = render_tree(nodes, theme=theme)
    lines = rendered.splitlines()

    assert len(lines) == 3
    assert lines[0] == "├─ Step 1"
    assert lines[1] == "├─ Step 2"
    assert lines[2] == "└─ Step 3"


def test_render_nested_children() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    root = TreeNode(label="Parent")
    root.add_child("Child 1", badge="42 lines")
    root.add_child("Child 2")

    rendered = render_tree([root], theme=theme)
    lines = rendered.splitlines()

    assert lines[0] == "└─ Parent"
    assert lines[1] == "   ├─ Child 1 42 lines"
    assert lines[2] == "   └─ Child 2"


def test_render_node_with_status() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    node_ok = TreeNode(label="Passing step", status="ok")
    node_err = TreeNode(label="Failing step", status="error")

    rendered = render_tree([node_ok, node_err], theme=theme)
    assert "✓ Passing step" in rendered
    assert "✗ Failing step" in rendered
