from bst import Node, contains


def test_finds_value_in_left_subtree() -> None:
    root = Node(8, Node(3), Node(10))
    assert contains(root, 3) is True
