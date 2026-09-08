from lib import excerpt, slugify


def test_slugify() -> None:
	assert slugify("Hello World") == "hello-world"


def test_excerpt() -> None:
	assert excerpt("short") == "short"
	assert excerpt("x" * 50).endswith("...")
