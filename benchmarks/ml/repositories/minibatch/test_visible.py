from batches import iterate_minibatches


def test_even_batches():
    assert iterate_minibatches([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]
