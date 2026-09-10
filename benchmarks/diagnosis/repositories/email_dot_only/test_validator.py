from validator import is_valid_email


def test_rejects_missing_at_sign() -> None:
    assert is_valid_email("user.example.com") is False
