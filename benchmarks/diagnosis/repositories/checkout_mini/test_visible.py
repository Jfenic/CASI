from cart import Cart
from receipt import build_receipt


def test_multi_quantity_lines() -> None:
    cart = Cart()
    cart.add("widget", 2)
    cart.add("gadget", 3)
    receipt = build_receipt(cart)
    assert receipt["subtotal"] == 35.0
    assert receipt["tax"] == 3.5
    assert receipt["total"] == 38.5
