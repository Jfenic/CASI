def standardize(rows):
    if not rows:
        return []
    width = len(rows[0])
    means = []
    for col in range(width):
        values = [row[col] for row in rows]
        means.append(sum(values) / len(values))
    result = []
    for row in rows:
        standardized = []
        for col, value in enumerate(row):
            values = [candidate[col] for candidate in rows]
            mean = means[col]
            variance = sum((item - mean) ** 2 for item in values) / len(values)
            std = variance**0.5
            standardized.append((value - mean) / std)
        result.append(standardized)
    return result
