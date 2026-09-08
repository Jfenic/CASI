from validators import validate_email


def test_rejects_missing_at_symbol() -> None:
    assert validate_email("bad") is False
