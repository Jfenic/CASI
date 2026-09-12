import pytest

from version import parse_version


def test_valid_version() -> None:
    assert parse_version("1.2.3") == (1, 2, 3)


def test_invalid_part_count_raises() -> None:
    with pytest.raises(ValueError):
        parse_version("1.2")
