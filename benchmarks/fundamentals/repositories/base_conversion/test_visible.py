from conversion import to_binary


def test_zero() -> None:
    assert to_binary(0) == "0"
