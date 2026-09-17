def rolling_features(values, window):
    if isinstance(window, bool) or not isinstance(window, int) or window < 1:
        raise ValueError("positive integer window required")
    result = []
    for end in range(window, len(values)):
        segment = values[end - window : end]
        result.append((sum(segment) / window, min(segment), max(segment)))
    return result
