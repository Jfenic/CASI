"""Binary search tree lookup — trees unit classic."""

from __future__ import annotations


class Node:
    def __init__(
        self, value: int, left: Node | None = None, right: Node | None = None
    ) -> None:
        self.value = value
        self.left = left
        self.right = right


def contains(root: Node | None, target: int) -> bool:
    if root is None:
        return False
    if target == root.value:
        return True
    if target < root.value:
        return contains(root.left, target)
    return contains(root.right, target)
