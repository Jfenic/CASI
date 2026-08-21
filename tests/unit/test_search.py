from pathlib import Path

from casi_code_agent.repository.search import search_code


def test_search_returns_path_and_line(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    target = repository / "app.py"
    target.write_text("print('hello')\nprint('world')\n", encoding="utf-8")

    results = search_code(repository, "world")

    assert len(results) == 1
    assert results[0].path == "app.py"
    assert results[0].line_number == 2
    assert results[0].line == "print('world')"
