"""Greatest common divisor — Euclid's algorithm (discrete math classic)."""


def gcd(a: int, b: int) -> int:
    a = abs(a)
    b = abs(b)
    while b:
        a, b = b, a % b
    return a
