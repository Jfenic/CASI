from billing import invoice_total


def test_half_up():
    assert invoice_total([("1.005", 1)]) == "1.01"
