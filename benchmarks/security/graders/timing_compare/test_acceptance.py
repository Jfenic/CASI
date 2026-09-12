import inspect

from auth import verify_token


def test_rejects_mismatch() -> None:
    assert verify_token("abc", "abd") is False
    assert verify_token("", "x") is False


def test_accepts_match() -> None:
    assert verify_token("session-token", "session-token") is True


def test_uses_constant_time_helper() -> None:
    source = inspect.getsource(verify_token)
    assert "compare_digest" in source
