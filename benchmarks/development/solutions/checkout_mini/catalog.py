"""Product catalog with fixed unit prices."""

_PRICES = {
    "widget": 10.0,
    "gadget": 5.0,
    "gizmo": 7.5,
}


def get_price(sku: str) -> float:
    if sku not in _PRICES:
        raise KeyError(f"unknown sku: {sku}")
    return _PRICES[sku]
