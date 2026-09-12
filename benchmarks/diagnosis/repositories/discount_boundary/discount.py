"""Apply tiered discounts to order totals."""


def apply_discount(total: float, tier: str) -> float:
    if tier == "gold" and total > 100:
        return total * 0.8
    if tier == "silver" and total > 50:
        return total * 0.9
    return total
