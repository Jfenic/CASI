import pytest
from cache import Cache


def test_overwrite_and_independent_keys():
    now = [0]
    cache = Cache(lambda: now[0])
    cache.set("a", 1, 2)
    cache.set("b", False, 10)
    now[0] = 1
    cache.set("a", 2, 5)
    now[0] = 3
    assert cache.get("a") == 2
    assert cache.get("b") is False
    now[0] = 6
    assert cache.get("a", "missing") == "missing"
    assert cache.get("b") is False


def test_zero_and_negative_ttl():
    cache = Cache(lambda: 100)
    cache.set("zero", 5, 0)
    assert cache.get("zero") is None
    cache.set("kept", 7, 10)
    with pytest.raises(ValueError):
        cache.set("kept", 9, -1)
    assert cache.get("kept") == 7
    assert cache.get("missing", "fallback") == "fallback"
