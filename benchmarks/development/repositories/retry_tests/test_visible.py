from retrying import retry


def test_visible_smoke():
    assert retry(lambda: 42) == 42
