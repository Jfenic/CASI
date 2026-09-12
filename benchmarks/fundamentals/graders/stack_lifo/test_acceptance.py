import pytest

from stack import Stack


def test_lifo_pop_order() -> None:
    stack = Stack()
    for value in (1, 2, 3):
        stack.push(value)
    assert stack.pop() == 3
    assert stack.pop() == 2
    assert stack.pop() == 1


def test_peek_does_not_remove() -> None:
    stack = Stack()
    stack.push(42)
    assert stack.peek() == 42
    assert stack.pop() == 42


def test_empty_stack_errors() -> None:
    stack = Stack()
    assert stack.is_empty()
    with pytest.raises(IndexError):
        stack.pop()
    with pytest.raises(IndexError):
        stack.peek()
