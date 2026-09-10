import random


def train_test_split(items, *, test_fraction=0.2, seed=0):
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    shuffled = list(items)
    rng = random.Random(seed)
    rng.shuffle(shuffled)
    test_size = int(len(shuffled) * test_fraction)
    test = shuffled[:test_size]
    train = shuffled[test_size:]
    return train, test
