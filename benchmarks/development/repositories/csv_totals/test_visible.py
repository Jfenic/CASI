from sales import totals


def test_duplicate_products():
    assert totals("product,quantity\npen,2\npen,3\n") == {"pen": 5}
