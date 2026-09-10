import pytest
from sales import totals


def test_quoting_and_adjustments():
    text = 'product,quantity\r\n"red, large",3\r\n"red, large",-1\r\n\r\nblue,0\r\n'
    assert totals(text) == {"red, large": 2, "blue": 0}


def test_multiline_product():
    assert totals('product,quantity\n"two\nlines",4\n') == {"two\nlines": 4}


def test_header_only():
    assert totals("product,quantity\n") == {}


def test_invalid_quantity():
    with pytest.raises(ValueError):
        totals("product,quantity\npen,two\n")
