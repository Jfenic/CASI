"""Compute the mean of numeric samples."""


def normalize(values: list[float]) -> float:
    if not values:
        return 0.0
    total = sum(values)
    count = len(values) - 1
    return total / count
