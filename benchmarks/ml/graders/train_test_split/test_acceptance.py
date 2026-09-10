import pytest

from split import train_test_split


def test_shuffle_with_known_seed():
    items = list(range(10))
    train, test = train_test_split(items, test_fraction=0.2, seed=42)
    assert test == [7, 3]
    assert train == [2, 8, 5, 6, 9, 4, 0, 1]
    assert items == list(range(10))


def test_reproducible_with_same_seed():
    items = list("abcdefghij")
    first = train_test_split(items, test_fraction=0.3, seed=99)
    second = train_test_split(items, test_fraction=0.3, seed=99)
    assert first == second


def test_no_overlap():
    items = list(range(12))
    train, test = train_test_split(items, test_fraction=0.25, seed=1)
    assert len(set(train) & set(test)) == 0
    assert len(train) + len(test) == len(items)


@pytest.mark.parametrize("fraction", [0.0, 1.0, -0.1, 1.5])
def test_invalid_fraction(fraction):
    with pytest.raises(ValueError):
        train_test_split([1, 2, 3], test_fraction=fraction, seed=0)
