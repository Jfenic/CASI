from encode import one_hot_encode


def test_single_class_zero():
    assert one_hot_encode([0, 0, 0]) == [[1], [1], [1]]


def test_empty():
    assert one_hot_encode([]) == []


def test_does_not_mutate_input():
    labels = [1, 0]
    original = labels[:]
    _ = one_hot_encode(labels)
    assert labels == original
