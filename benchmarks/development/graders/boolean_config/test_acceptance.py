import pytest
from config import parse_bool


@pytest.mark.parametrize("value", [" TRUE ", "1", "Yes", "on", True])
def test_true(value):
    assert parse_bool(value) is True


@pytest.mark.parametrize("value", [" FALSE ", "0", "No", "off", False])
def test_false(value):
    assert parse_bool(value) is False


def test_default():
    assert parse_bool(None) is False
    assert parse_bool(None, default=True) is True


@pytest.mark.parametrize("value", ["", "enabled", "2"])
def test_bad_string(value):
    with pytest.raises(ValueError):
        parse_bool(value)


@pytest.mark.parametrize("value", [0, 1, [], {}])
def test_bad_type(value):
    with pytest.raises(TypeError):
        parse_bool(value)
