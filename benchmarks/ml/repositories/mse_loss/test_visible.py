import pytest

from loss import mse


def test_perfect_prediction() -> None:
    assert mse([1.0, 2.0], [1.0, 2.0]) == 0.0


def test_known_error() -> None:
    assert mse([0.0, 0.0], [1.0, 3.0]) == 5.0
