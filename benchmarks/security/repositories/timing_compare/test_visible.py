from auth import verify_token


def test_matching_tokens() -> None:
    assert verify_token("abc123", "abc123") is True
