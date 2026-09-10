import pytest
from billing import invoice_total


def test_round_lines_before_sum():
    assert invoice_total([("0.005", 1), ("0.005", 1)]) == "0.02"


def test_quantity_before_rounding():
    assert invoice_total([("0.335", 3)]) == "1.01"


def test_empty_and_zero():
    assert invoice_total([]) == "0.00"
    assert invoice_total([("123.455", 0)]) == "0.00"


def test_precision_and_input():
    lines = [("9007199254740993.01", 1), ("0.10", 3)]
    before = list(lines)
    assert invoice_total(lines) == "9007199254740993.31"
    assert lines == before


def test_negative_quantity():
    with pytest.raises(ValueError):
        invoice_total([("2.00", -1)])
