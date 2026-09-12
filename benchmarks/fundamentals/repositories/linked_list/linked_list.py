"""Singly linked list — classic pointer-manipulation exercise."""

from __future__ import annotations


class Node:
    def __init__(self, value: int, next: Node | None = None) -> None:
        self.value = value
        self.next = next


def to_list(head: Node | None) -> list[int]:
    values: list[int] = []
    current = head
    while current is not None:
        values.append(current.value)
        current = current.next
    return values


def reverse(head: Node | None) -> Node | None:
    prev: Node | None = None
    current = head
    while current is not None:
        nxt = current.next
        current.next = prev
        prev = current
        current = nxt
    return head
