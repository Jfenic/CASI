from stats import mean


def test_mean_of_three_values() -> None:
	assert mean([1, 2, 3]) == 2.0


def test_mean_of_empty_list() -> None:
	assert mean([]) == 0.0
