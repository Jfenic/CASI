"""Subtotal calculations for checkout."""

import catalog
from cart import Cart


def subtotal(cart: Cart) -> float:
    total = 0.0
    for sku, qty in cart.lines:
        total += catalog.get_price(sku) * qty
    return total
