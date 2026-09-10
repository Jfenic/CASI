from __future__ import annotations

from pathlib import Path

from casi.tools import ToolRegistry


def test_list_files_tool_returns_structured_result(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "README.md").write_text("hello", encoding="utf-8")

    registry = ToolRegistry(repository)
    result = registry.execute("list_files", {"max_files": 10})

    assert result.success is True
    assert result.error is None
    assert result.output == "README.md"
    assert result.metadata["count"] == 1


def test_read_file_tool_validates_arguments_and_returns_numbered_lines(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "README.md").write_text("alpha\nbeta\n", encoding="utf-8")

    registry = ToolRegistry(repository)
    result = registry.execute(
        "read_file",
        {
            "path": "README.md",
            "start_line": 1,
            "end_line": 2,
        },
    )

    assert result.success is True
    assert result.output == "1: alpha\n2: beta"
    assert result.metadata["path"] == "README.md"


def test_search_code_tool_returns_path_and_line(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "app.py").write_text("safe_path\n", encoding="utf-8")

    registry = ToolRegistry(repository)
    result = registry.execute("search_code", {"query": "safe_path"})

    assert result.success is True
    assert result.output == "app.py:1: safe_path"
    assert result.metadata["count"] == 1


def test_unknown_tool_is_rejected(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()

    registry = ToolRegistry(repository)
    result = registry.execute("missing_tool", {})

    assert result.success is False
    assert result.error == "Unknown tool: missing_tool"


def test_invalid_arguments_are_returned_structurally(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()

    registry = ToolRegistry(repository)
    result = registry.execute("read_file", {"path": "README.md", "start_line": 0})

    assert result.success is False
    assert result.error is not None
    assert "greater than or equal to 1" in result.error
