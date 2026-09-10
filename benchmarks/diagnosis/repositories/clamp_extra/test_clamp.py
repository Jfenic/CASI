from clamp import clamp


def test_keeps_in_range_value() -> None:
    assert clamp(7, 0, 10) == 7
