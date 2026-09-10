from slug import slugify


def test_visible_smoke():
    assert slugify("hello world") == "hello-world"
