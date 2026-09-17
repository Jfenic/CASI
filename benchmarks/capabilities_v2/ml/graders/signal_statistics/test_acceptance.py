import pytest
from signal_features import describe_signal


@pytest.mark.parametrize(
    "values,expected",
    [
        ([-1, 1, -1, 1], {"mean": 0, "rms": 1, "variance": 1, "zero_crossing_rate": 1}),
        ([3, 3], {"mean": 3, "rms": 3, "variance": 0, "zero_crossing_rate": 0}),
        ([-3], {"mean": -3, "rms": 3, "variance": 0, "zero_crossing_rate": 0}),
        (
            [-1, 0, 1],
            {
                "mean": 0,
                "rms": (2 / 3) ** 0.5,
                "variance": 2 / 3,
                "zero_crossing_rate": 0,
            },
        ),
        (
            [1, -1, -1],
            {"mean": -1 / 3, "rms": 1, "variance": 8 / 9, "zero_crossing_rate": 0.5},
        ),
    ],
)
def test_statistics(values, expected):
    before = values.copy()
    result = describe_signal(values)
    assert result == pytest.approx(expected)
    assert values == before


def test_empty():
    with pytest.raises(ValueError):
        describe_signal([])
