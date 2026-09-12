"""In-memory shopping cart."""


class Cart:
    def __init__(self) -> None:
        self._lines: list[tuple[str, int]] = []

    def add(self, sku: str, qty: int) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        self._lines.append((sku, qty))

    @property
    def lines(self) -> list[tuple[str, int]]:
        return list(self._lines)
