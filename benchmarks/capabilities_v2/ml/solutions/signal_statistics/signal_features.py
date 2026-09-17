import math


def describe_signal(values):
    if not values:
        raise ValueError("empty signal")
    count = len(values)
    mean = sum(values) / count
    rms = math.sqrt(sum(value * value for value in values) / count)
    variance = sum((value - mean) ** 2 for value in values) / count
    crossings = sum(
        left * right < 0 for left, right in zip(values, values[1:], strict=False)
    )
    rate = crossings / (count - 1) if count > 1 else 0.0
    return {"mean": mean, "rms": rms, "variance": variance, "zero_crossing_rate": rate}
