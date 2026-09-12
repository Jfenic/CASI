import pytest

from binary_search import binary_search


@pytest.mark.parametrize(
    "items,target,expected",
    [
        ([], 1, -1),
        ([5], 5, 0),
        ([1, 3, 5, 7, 9], 1, 0),
        ([1, 3, 5, 7, 9], 9, 4),
        ([1, 3, 5, 7, 9], 4, -1),
        ([2, 4, 6, 8, 10, 12, 14], 12, 5),
    ],
)
def test_binary_search(items, target, expected) -> None:
    assert binary_search(items, target) == expected
