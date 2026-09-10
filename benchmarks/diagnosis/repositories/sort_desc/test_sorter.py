from sorter import sort_asc


def test_sorts_ascending() -> None:
    assert sort_asc([3, 1, 2]) == [1, 2, 3]
