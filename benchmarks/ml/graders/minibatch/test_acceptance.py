import pytest

from batches import iterate_minibatches


def test_partial_final_batch():
    assert iterate_minibatches([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_single_item_batch():
    assert iterate_minibatches(["a", "b", "c"], 1) == [["a"], ["b"], ["c"]]


def test_empty_input():
    assert iterate_minibatches([], 3) == []


@pytest.mark.parametrize("size", [0, -1])
def test_invalid_batch_size(size):
    with pytest.raises(ValueError):
        iterate_minibatches([1], size)


def test_does_not_mutate_input():
    items = [1, 2, 3]
    original = items[:]
    _ = iterate_minibatches(items, 2)
    assert items == original
