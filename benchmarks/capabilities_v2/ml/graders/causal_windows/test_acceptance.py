import pytest
from features import rolling_features


def test_windows_and_future_independence():
    values = [1, 3, 5, 100]
    result = rolling_features(values, 2)
    assert result == [(2, 1, 3), (4, 3, 5), (52.5, 5, 100)]
    assert rolling_features(values + [-1000], 2)[:3] == result
    assert values == [1, 3, 5, 100]
    assert all(isinstance(row, tuple) for row in result)


def test_boundaries():
    assert rolling_features([-2, 4], 1) == [(-2, -2, -2), (4, 4, 4)]
    assert rolling_features([1], 2) == []
    assert rolling_features([], 2) == []
    mean, low, high = rolling_features([0, 1, 1], 3)[0]
    assert mean == pytest.approx(2 / 3)
    assert (low, high) == (0, 1)


@pytest.mark.parametrize("window", [0, -1, True, 1.5, "2"])
def test_invalid(window):
    with pytest.raises(ValueError):
        rolling_features([], window)
