from bst import Node, contains


def _sample_tree() -> Node:
    return Node(
        8,
        Node(3, Node(1), Node(6)),
        Node(10, None, Node(14)),
    )


def test_contains_existing_values() -> None:
    root = _sample_tree()
    for value in (1, 3, 6, 8, 10, 14):
        assert contains(root, value) is True


def test_missing_values() -> None:
    root = _sample_tree()
    for value in (0, 4, 7, 13, 20):
        assert contains(root, value) is False
