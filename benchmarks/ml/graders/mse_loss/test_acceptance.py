import pytest

from loss import mse


def test_perfect_prediction() -> None:
    assert mse([2.0, 4.0, 6.0], [2.0, 4.0, 6.0]) == 0.0


def test_single_pair() -> None:
    assert mse([3.0], [1.0]) == 4.0


def test_empty_inputs() -> None:
    assert mse([], []) == 0.0


def test_length_mismatch_raises() -> None:
    with pytest.raises(ValueError):
        mse([1.0], [1.0, 2.0])
