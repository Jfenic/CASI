"""Simple tax helper."""


def compute_tax(amount: float, rate: float = 0.1) -> float:
    return round(amount * rate, 2)
