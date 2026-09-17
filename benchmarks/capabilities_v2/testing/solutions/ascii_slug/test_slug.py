import pytest
from slug import slugify


@pytest.mark.parametrize(
    "text,expected",
    [
        ("HELLO", "hello"),
        ("version 42", "version-42"),
        ("a_b", "a-b"),
        ("a!! b", "a-b"),
        ("!!hello!!", "hello"),
        ("", ""),
        ("!!!", ""),
    ],
)
def test_slugify(text, expected):
    assert slugify(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [("café", "caf"), ("aéb", "a-b"), ("中文", ""), ("a\tb\nc", "a-b-c")],
)
def test_non_ascii_and_whitespace(text, expected):
    assert slugify(text) == expected
