from strip import strip_lines


def test_strips_whitespace() -> None:
	assert strip_lines(["  a  ", " b "]) == ["a", "b"]
