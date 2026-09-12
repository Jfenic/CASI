import pytest

from conversion import to_binary


@pytest.mark.parametrize(
    "n,expected",
    [
        (0, "0"),
        (1, "1"),
        (2, "10"),
        (5, "101"),
        (8, "1000"),
        (255, "11111111"),
    ],
)
def test_to_binary(n, expected) -> None:
    assert to_binary(n) == expected


def test_negative_raises() -> None:
    with pytest.raises(ValueError):
        to_binary(-1)
