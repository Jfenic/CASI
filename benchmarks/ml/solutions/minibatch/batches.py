def iterate_minibatches(items, batch_size):
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    batches = []
    for start in range(0, len(items), batch_size):
        batches.append(list(items[start : start + batch_size]))
    return batches
