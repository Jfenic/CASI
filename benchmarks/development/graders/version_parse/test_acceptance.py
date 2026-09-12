import pytest

from version import parse_version


def test_valid_version() -> None:
    assert parse_version("10.0.1") == (10, 0, 1)


@pytest.mark.parametrize("text", ["1", "1.2", "1.2.3.4", ""])
def test_invalid_part_count_raises(text: str) -> None:
    with pytest.raises(ValueError):
        parse_version(text)


@pytest.mark.parametrize("text", ["1.a.3", "1.2.x"])
def test_non_integer_parts_raise(text: str) -> None:
    with pytest.raises(ValueError):
        parse_version(text)
