"""Decimal to binary conversion — computer systems / number bases classic."""


def to_binary(n: int) -> str:
    if n == 0:
        return "0"
    if n < 0:
        raise ValueError("n must be non-negative")
    bits: list[str] = []
    while n:
        bits.append(str(n % 2))
        n //= 2
    return "".join(reversed(bits))
