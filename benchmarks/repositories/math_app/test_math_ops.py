from math_ops import add, divide


def test_addition() -> None:
	assert add(2, 3) == 5


def test_divide_by_zero() -> None:
	assert divide(1, 0) == 0
