from cart import Cart
from receipt import build_receipt


def test_empty_cart() -> None:
    receipt = build_receipt(Cart())
    assert receipt == {"subtotal": 0.0, "tax": 0.0, "total": 0.0}


def test_single_unit_line() -> None:
    cart = Cart()
    cart.add("gizmo", 1)
    receipt = build_receipt(cart)
    assert receipt["subtotal"] == 7.5
    assert receipt["tax"] == 0.75
    assert receipt["total"] == 8.25


def test_mixed_quantities_and_skus() -> None:
    cart = Cart()
    cart.add("widget", 4)
    cart.add("gadget", 1)
    cart.add("gizmo", 2)
    receipt = build_receipt(cart)
    assert receipt["subtotal"] == 60.0
    assert receipt["tax"] == 6.0
    assert receipt["total"] == 66.0


def test_repeated_additions_accumulate_quantity() -> None:
    cart = Cart()
    cart.add("widget", 1)
    cart.add("widget", 2)
    receipt = build_receipt(cart)
    assert receipt["subtotal"] == 30.0
