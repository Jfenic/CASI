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
