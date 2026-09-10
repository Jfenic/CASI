from dependencies import build_order


def test_simple_order():
    assert build_order({"app": ["lib"], "lib": []}) == ["lib", "app"]
