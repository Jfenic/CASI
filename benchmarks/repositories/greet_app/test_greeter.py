from greeter import greet


def test_greet_is_title_case() -> None:
	assert greet("casi") == "Hello, casi"
