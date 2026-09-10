import pytest
from reader import read_records


def test_empty_and_unicode():
    assert read_records(" \n\t\n") == []
    assert read_records('{"name":"José","ok":true,"nested":{"n":null}}') == [
        {"name": "José", "ok": True, "nested": {"n": None}}
    ]


@pytest.mark.parametrize("bad", ["[1]", "null", "true", "3", '"text"', "{bad"])
def test_physical_line_number(bad):
    with pytest.raises(ValueError, match=r"line 3\b"):
        read_records('{"ok":1}\n\n' + bad)
