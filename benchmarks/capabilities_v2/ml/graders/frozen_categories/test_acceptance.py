import pytest
from encoding import Encoder


def test_vocabulary_and_unknown():
    train = ["z", "a", "z", "b"]
    model = Encoder()
    assert model.fit(train) is model
    values = ["unknown", "a", "z", "a"]
    result = model.transform(values)
    assert result == [[0, 0, 0], [0, 1, 0], [1, 0, 0], [0, 1, 0]]
    result[1][1] = 9
    assert result[3] == [0, 1, 0]
    assert model.transform(["unknown", "b"]) == [[0, 0, 0], [0, 0, 1]]
    assert train == ["z", "a", "z", "b"]
    assert values == ["unknown", "a", "z", "a"]


def test_empty_refit_and_unfitted():
    with pytest.raises(ValueError):
        Encoder().transform([])
    model = Encoder().fit(["a"])
    model.fit(["b"])
    assert model.transform(["a", "b"]) == [[0], [1]]
    model.fit([])
    result = model.transform(["x", "y"])
    assert result == [[], []]
    result[0].append(1)
    assert result[1] == []
    assert model.transform([]) == []
