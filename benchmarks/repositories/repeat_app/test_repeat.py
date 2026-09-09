from repeat import repeat


def test_repeats_twice() -> None:
	assert repeat("ab", 2) == "abab"


def test_repeats_zero_times() -> None:
	assert repeat("ab", 0) == ""
