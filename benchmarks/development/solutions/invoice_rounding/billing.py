from decimal import ROUND_HALF_UP, Decimal


def invoice_total(lines):
    total = Decimal("0.00")
    for price, quantity in lines:
        if quantity < 0:
            raise ValueError("negative quantity")
        total += (Decimal(price) * quantity).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    return f"{total:.2f}"
