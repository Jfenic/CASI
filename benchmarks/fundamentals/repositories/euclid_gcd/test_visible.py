from gcd import gcd


def test_gcd_of_coprime_numbers() -> None:
    assert gcd(14, 15) == 1
