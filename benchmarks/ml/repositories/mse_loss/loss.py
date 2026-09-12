"""Mean squared error for regression targets."""

import math


def mse(y_true: list[float], y_pred: list[float]) -> float:
    if len(y_true) != len(y_pred):
        raise ValueError("length mismatch")
    if not y_true:
        return 0.0
    total = sum((truth - pred) ** 2 for truth, pred in zip(y_true, y_pred, strict=True))
    return math.sqrt(total / len(y_true))
