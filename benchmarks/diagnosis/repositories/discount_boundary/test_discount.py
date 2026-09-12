from discount import apply_discount


def test_gold_discount_at_exact_threshold() -> None:
    assert apply_discount(100, "gold") == 80.0
