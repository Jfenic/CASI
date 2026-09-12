import pytest

from gcd import gcd


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (48, 18, 6),
        (14, 15, 1),
        (0, 7, 7),
        (12, 0, 12),
        (270, 192, 6),
        (-12, 8, 4),
    ],
)
def test_gcd(a, b, expected) -> None:
    assert gcd(a, b) == expected
