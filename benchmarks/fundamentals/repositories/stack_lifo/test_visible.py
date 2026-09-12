from stack import Stack


def test_push_then_pop_returns_last_pushed() -> None:
    stack = Stack()
    stack.push(1)
    stack.push(2)
    assert stack.pop() == 2
