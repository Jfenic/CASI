from __future__ import annotations

from pathlib import Path

from casi.agent.intent import TaskIntent
from casi.agent.pipelines import run_repository_pipeline
from casi.tools.result import ToolResult


def test_inspect_pipeline_reads_named_file_instead_of_doc_match(tmp_path: Path) -> None:
    (tmp_path / "planning.md").write_text("├── loop.py\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "agent").mkdir(parents=True)
    (tmp_path / "src" / "agent" / "loop.py").write_text(
        '"""Agent loop."""\n\ndef run():\n    pass\n',
        encoding="utf-8",
    )
    calls: list[tuple[str, dict[str, object]]] = []

    def execute(tool_name: str, arguments: dict[str, object]) -> ToolResult:
        calls.append((tool_name, arguments))
        if tool_name == "read_file":
            path = tmp_path / str(arguments["path"])
            return ToolResult(success=True, output=path.read_text(encoding="utf-8"))
        if tool_name == "search_code":
            return ToolResult(success=True, output="planning.md:405: ├── loop.py")
        return ToolResult(success=True, output="")

    run_repository_pipeline(
        TaskIntent.INSPECT,
        "dime que puedo mejorar el archivo loop.py",
        execute,
        repository_path=tmp_path,
    )

    read_calls = [arguments for tool_name, arguments in calls if tool_name == "read_file"]
    assert read_calls == [{"path": "src/agent/loop.py"}]
    assert not any(tool_name == "search_code" for tool_name, _arguments in calls)


def test_fix_pipeline_reads_files_from_failed_test_output(tmp_path: Path) -> None:
    (tmp_path / "sorter.py").write_text(
        "def bubble_sort(values: list[int]) -> list[int]:\n    return values\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_sorter.py").write_text(
        "from sorter import bubble_sort\n\n"
        "def test_bubble_sort_orders_ascending():\n"
        "    assert bubble_sort([2, 1]) == [1, 2]\n",
        encoding="utf-8",
    )
    calls: list[tuple[str, dict[str, object]]] = []

    def execute(tool_name: str, arguments: dict[str, object]) -> ToolResult:
        calls.append((tool_name, arguments))
        if tool_name == "read_file":
            path = tmp_path / str(arguments["path"])
            return ToolResult(success=True, output=path.read_text(encoding="utf-8"))
        return ToolResult(success=True, output="")

    from casi.agent.pipelines import run_fix_pipeline

    run_fix_pipeline(
        "corrige los tests",
        execute,
        repository_path=tmp_path,
        test_output="tests/test_sorter.py:6: AssertionError\nsorter.py:10: in bubble_sort",
    )

    read_calls = [arguments["path"] for tool_name, arguments in calls if tool_name == "read_file"]
    assert "tests/test_sorter.py" in read_calls
    assert "sorter.py" in read_calls


def test_fix_pipeline_resolves_source_imported_by_failed_test(tmp_path: Path) -> None:
    (tmp_path / "validators.py").write_text(
        "def validate_email(value: str) -> bool:\n    return True\n",
        encoding="utf-8",
    )
    (tmp_path / "test_validators.py").write_text(
        "from validators import validate_email\n\n"
        "def test_invalid():\n    assert not validate_email('bad')\n",
        encoding="utf-8",
    )
    calls: list[tuple[str, dict[str, object]]] = []

    def execute(tool_name: str, arguments: dict[str, object]) -> ToolResult:
        calls.append((tool_name, arguments))
        return ToolResult(success=True, output="")

    from casi.agent.pipelines import run_fix_pipeline

    run_fix_pipeline(
        "corrige los tests",
        execute,
        repository_path=tmp_path,
        test_output="FAILED test_validators.py::test_invalid - assert not True",
    )

    read_calls = [arguments["path"] for tool_name, arguments in calls if tool_name == "read_file"]
    assert read_calls == ["test_validators.py", "validators.py"]


def test_fix_pipeline_requires_propose_file_after_loading_sources() -> None:
    from casi.agent.pipelines import nudge_after_fix_pipeline

    nudge = nudge_after_fix_pipeline()

    assert "MUST call propose_file" in nudge.user_message
    assert "do not write the diff yourself" in nudge.user_message
