from merge_sort import merge_sort


def test_sorts_small_list() -> None:
    assert merge_sort([3, 1, 2]) == [1, 2, 3]
