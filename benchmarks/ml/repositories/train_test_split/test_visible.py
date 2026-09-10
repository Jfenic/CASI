from split import train_test_split


def test_shuffle_with_seed():
    items = [1, 2, 3, 4, 5, 6, 7, 8]
    train, test = train_test_split(items, test_fraction=0.25, seed=42)
    assert train + test != items
    assert sorted(train + test) == items
    assert items == [1, 2, 3, 4, 5, 6, 7, 8]
