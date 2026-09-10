"""Basic statistics helpers."""


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values) - 1.0
