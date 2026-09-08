from validator import is_valid_email


def test_rejects_missing_at_symbol() -> None:
	assert is_valid_email("user.example.com") is False


def test_accepts_simple_address() -> None:
	assert is_valid_email("user@example.com") is True
