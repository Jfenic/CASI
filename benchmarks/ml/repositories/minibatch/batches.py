def iterate_minibatches(items, batch_size):
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    batches = []
    for start in range(0, len(items), batch_size):
        end = start + batch_size
        if end <= len(items):
            batches.append(items[start:end])
    return batches
