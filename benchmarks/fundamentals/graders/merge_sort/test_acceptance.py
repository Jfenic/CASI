import pytest

from merge_sort import merge, merge_sort


def test_merge_handles_leftovers() -> None:
    assert merge([1, 3], [2, 4, 5]) == [1, 2, 3, 4, 5]


@pytest.mark.parametrize(
    "items,expected",
    [
        ([], []),
        ([1], [1]),
        ([5, 4, 3, 2, 1], [1, 2, 3, 4, 5]),
        ([3, 1, 4, 1, 5, 9, 2, 6], [1, 1, 2, 3, 4, 5, 6, 9]),
    ],
)
def test_merge_sort(items, expected) -> None:
    assert merge_sort(items) == expected
