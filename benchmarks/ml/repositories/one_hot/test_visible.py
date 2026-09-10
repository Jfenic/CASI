from encode import one_hot_encode


def test_basic_encoding():
    assert one_hot_encode([0, 2, 1]) == [
        [1, 0, 0],
        [0, 0, 1],
        [0, 1, 0],
    ]
