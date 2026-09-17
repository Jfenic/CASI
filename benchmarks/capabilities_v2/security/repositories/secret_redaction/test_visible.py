from redaction import redact


def test_password():
    assert redact({"password": "hidden"}) == {"password": "[REDACTED]"}
