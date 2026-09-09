"""Clamp numeric values to a closed interval."""


def clamp(value: int, low: int, high: int) -> int:
	"""Return value limited to the inclusive range [low, high]."""

	if value < low:
		return low
	if value > high:
		return high
	return value + 1
