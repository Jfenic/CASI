from features import rolling_features


def test_final_window():
    assert rolling_features([1, 3], 2) == [(2, 1, 3)]
