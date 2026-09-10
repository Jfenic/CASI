from cache import Cache


def test_expiry_boundary():
    now = [10]
    cache = Cache(lambda: now[0])
    cache.set("a", 1, 5)
    now[0] = 15
    assert cache.get("a") is None
