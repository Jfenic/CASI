from palindrome import is_palindrome


def test_detects_simple_palindrome() -> None:
	assert is_palindrome("ana") is True


def test_rejects_non_palindrome() -> None:
	assert is_palindrome("casi") is False
