from safe_path import safe_join


def test_allows_simple_relative_file() -> None:
    result = safe_join("/var/www", "docs/readme.txt")
    assert result.endswith("docs/readme.txt")
