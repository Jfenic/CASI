from copy import deepcopy

import pytest
from orders import checkout


@pytest.mark.parametrize("quantity", [1, 2, 3])
def test_success(quantity):
    stock = {"a": 3, "b": 8}
    prices = {"a": 2.5, "b": 4}
    assert checkout(stock, prices, "a", quantity) == pytest.approx(2.5 * quantity)
    assert stock == {"a": 3 - quantity, "b": 8}
    assert prices == {"a": 2.5, "b": 4}


@pytest.mark.parametrize("quantity", [0, -1, 4])
def test_rejected_quantity(quantity):
    stock = {"a": 3}
    with pytest.raises(ValueError):
        checkout(stock, {"a": 2}, "a", quantity)
    assert stock == {"a": 3}


@pytest.mark.parametrize("stock,prices", [({"b": 3}, {"a": 2}), ({"a": 3}, {"b": 2})])
def test_unknown(stock, prices):
    before = deepcopy(stock)
    with pytest.raises(KeyError):
        checkout(stock, prices, "a", 1)
    assert stock == before
