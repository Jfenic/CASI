from copy import deepcopy

import pytest
from preprocessing import Centerer


def test_training_only_and_missing():
    train = [[1, None, 2], [3, None, None]]
    test = [[100, 4, None], [None, None, 6]]
    before = deepcopy((train, test))
    model = Centerer()
    assert model.fit(train) is model
    result = model.transform(test)
    assert result == [[98, 4, 0], [0, 0, 4]]
    assert model.transform([[2, None, 2]]) == [[0, 0, 0]]
    assert (train, test) == before
    result[0][0] = -1
    assert result[1][0] == 0
    assert model.transform(test)[0][0] == 98
    assert model.transform([]) == []


def test_refit_and_width():
    model = Centerer().fit([[0], [2]])
    model.fit([[8], [12]])
    assert model.transform([[12]]) == [[2]]
    with pytest.raises(ValueError):
        model.transform([[1, 2]])


@pytest.mark.parametrize("rows", [[], [[]], [[1], [1, 2]]])
def test_invalid_fit(rows):
    with pytest.raises(ValueError):
        Centerer().fit(rows)


def test_unfitted():
    with pytest.raises(ValueError):
        Centerer().transform([])
