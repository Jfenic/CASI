from linked_list import Node, reverse, to_list


def test_reverse_empty() -> None:
    assert reverse(None) is None


def test_reverse_single() -> None:
    head = Node(7)
    assert to_list(reverse(head)) == [7]


def test_reverse_longer_list() -> None:
    head = Node(1, Node(2, Node(3, Node(4))))
    assert to_list(reverse(head)) == [4, 3, 2, 1]
