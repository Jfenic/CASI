def standardize(rows):
    if not rows:
        return []
    width = len(rows[0])
    means = []
    stds = []
    for col in range(width):
        values = [row[col] for row in rows]
        mean = sum(values) / len(values)
        if len(values) == 1:
            std = 0.0
        else:
            variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
            std = variance**0.5
        means.append(mean)
        stds.append(std)
    result = []
    for row in rows:
        standardized = []
        for col, value in enumerate(row):
            if stds[col] == 0:
                standardized.append(0.0)
            else:
                standardized.append((value - means[col]) / stds[col])
        result.append(standardized)
    return result
