import pytest
from pagination import paginate


@pytest.mark.parametrize(
    "items,page,size,expected",
    [
        ([1, 2, 3, 4, 5], 2, 2, [3, 4]),
        ([1, 2, 3], 2, 2, [3]),
        ([1], 3, 2, []),
        ([], 1, 3, []),
        ([1, 2], 1, 10, [1, 2]),
    ],
)
def test_pages(items, page, size, expected):
    before = items.copy()
    result = paginate(items, page, size)
    assert result == expected
    assert items == before
    assert result is not items


@pytest.mark.parametrize("page,size", [(0, 2), (-1, 2), (1, 0), (1, -1)])
def test_invalid(page, size):
    with pytest.raises(ValueError):
        paginate([], page, size)
