from settings import merge_settings


def test_recursive_merge():
    assert merge_settings(
        {"db": {"host": "local", "port": 10}}, {"db": {"port": 20}}
    ) == {"db": {"host": "local", "port": 20}}
