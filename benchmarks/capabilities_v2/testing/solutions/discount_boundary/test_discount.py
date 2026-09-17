import pytest
from pricing import discounted_total


@pytest.mark.parametrize(
    "amount,member,expected",
    [
        (0, True, 0),
        (99, True, 99),
        (100, True, 90),
        (101, True, 90.9),
        (100, False, 100),
        (150, False, 150),
    ],
)
def test_prices(amount, member, expected):
    assert discounted_total(amount, member) == pytest.approx(expected)


@pytest.mark.parametrize("member", [True, False])
def test_negative(member):
    with pytest.raises(ValueError):
        discounted_total(-1, member)
