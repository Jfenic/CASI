from stats import mean


def test_mean_of_three_values() -> None:
    assert mean([1.0, 2.0, 3.0]) == 2.0
