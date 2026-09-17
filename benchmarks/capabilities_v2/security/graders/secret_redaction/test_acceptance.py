from copy import deepcopy

import pytest
from redaction import redact


@pytest.mark.parametrize("key", ["password", "TOKEN", "Secret", "Authorization"])
def test_sensitive_keys(key):
    assert redact({key: {"nested": ["sensitive"]}}) == {key: "[REDACTED]"}


def test_nested_and_safe_data():
    value = {
        "users": [{"Token": "abc", "name": "Ana"}],
        "password_hint": "pet",
        "tokenizer": True,
        "note": "token is a word",
        "n": None,
    }
    before = deepcopy(value)
    result = redact(value)
    assert result == {
        "users": [{"Token": "[REDACTED]", "name": "Ana"}],
        "password_hint": "pet",
        "tokenizer": True,
        "note": "token is a word",
        "n": None,
    }
    result["users"][0]["name"] = "changed"
    assert value == before


@pytest.mark.parametrize("value", [None, 0, False, "password", [], {}])
def test_root_values(value):
    assert redact(value) == value
