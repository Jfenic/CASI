def train_test_split(items, *, test_fraction=0.2, seed=0):
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    test_size = int(len(items) * test_fraction)
    test = list(items[:test_size])
    train = list(items[test_size:])
    return train, test
