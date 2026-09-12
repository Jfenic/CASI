from linked_list import Node, reverse, to_list


def test_reverse_two_nodes() -> None:
    head = Node(1, Node(2))
    assert to_list(reverse(head)) == [2, 1]
