from config import parse_bool


def test_false_setting():
    assert parse_bool("false") is False
