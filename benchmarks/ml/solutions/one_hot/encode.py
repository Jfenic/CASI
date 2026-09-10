def one_hot_encode(labels):
    if not labels:
        return []
    num_classes = max(labels) + 1
    rows = []
    for label in labels:
        row = [0] * num_classes
        row[label] = 1
        rows.append(row)
    return rows
