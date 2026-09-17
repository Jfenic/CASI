"""Build a checkout receipt from a cart."""

import tax as tax_module
import totals
from cart import Cart


def build_receipt(cart: Cart) -> dict[str, float]:
    sub = totals.subtotal(cart)
    tax_amount = tax_module.compute_tax(sub)
    return {
        "subtotal": sub,
        "tax": tax_amount,
        "total": round(sub + tax_amount, 2),
    }
