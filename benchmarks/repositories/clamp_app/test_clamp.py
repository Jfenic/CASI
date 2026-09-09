from clamp import clamp


def test_clamps_low() -> None:
	assert clamp(-5, 0, 10) == 0


def test_clamps_high() -> None:
	assert clamp(25, 0, 10) == 10


def test_keeps_in_range_value() -> None:
	assert clamp(7, 0, 10) == 7
