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

    read_calls = [
        arguments for tool_name, arguments in calls if tool_name == "read_file"
    ]
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
        test_output=(
            "tests/test_sorter.py:6: AssertionError\nsorter.py:10: in bubble_sort"
        ),
    )

    read_calls = [
        arguments["path"] for tool_name, arguments in calls if tool_name == "read_file"
    ]
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

    read_calls = [
        arguments["path"] for tool_name, arguments in calls if tool_name == "read_file"
    ]
    assert read_calls == ["test_validators.py", "validators.py"]


def test_fix_pipeline_requires_propose_file_after_loading_sources() -> None:
    from casi.agent.pipelines import nudge_after_fix_pipeline

    nudge = nudge_after_fix_pipeline()

    assert "MUST call propose_file" in nudge.user_message
    assert "do not write the diff yourself" in nudge.user_message


def test_missing_local_module_paths_does_not_guess_import_is_local(
    tmp_path: Path,
) -> None:
    (tmp_path / "test_stats.py").write_text(
        "from stats import mean\n\ndef test_mean():\n    assert mean([1, 2, 3]) == 2\n",
        encoding="utf-8",
    )

    from casi.agent.pipelines import missing_local_module_paths

    missing = missing_local_module_paths(tmp_path, ["test_stats.py"])

    assert missing == []

    missing = missing_local_module_paths(
        tmp_path, ["test_stats.py"], task_context="Create the missing stats.py module"
    )
    assert missing == ["stats.py"]


def test_fix_pipeline_reports_missing_local_module(tmp_path: Path) -> None:
    (tmp_path / "test_stats.py").write_text(
        "from stats import mean\n\ndef test_mean():\n    assert mean([1, 2, 3]) == 2\n",
        encoding="utf-8",
    )

    from casi.agent.pipelines import run_fix_pipeline

    missing = run_fix_pipeline(
        "Create stats.py and make all tests pass",
        lambda *_args, **_kwargs: ToolResult(success=True, output=""),
        repository_path=tmp_path,
        test_output="ModuleNotFoundError: No module named 'stats'",
    )

    assert missing == ["stats.py"]


def test_fix_pipeline_follows_transitive_local_imports(tmp_path: Path) -> None:
    (tmp_path / "catalog.py").write_text("PRICE = 1\n", encoding="utf-8")
    (tmp_path / "totals.py").write_text(
        "import catalog\n\ndef subtotal():\n    return catalog.PRICE\n",
        encoding="utf-8",
    )
    (tmp_path / "receipt.py").write_text(
        "import totals\n\ndef build():\n    return totals.subtotal()\n",
        encoding="utf-8",
    )
    (tmp_path / "test_receipt.py").write_text(
        "from receipt import build\n\ndef test_build():\n    assert build() == 2\n",
        encoding="utf-8",
    )
    calls: list[tuple[str, dict[str, object]]] = []

    def execute(tool_name: str, arguments: dict[str, object]) -> ToolResult:
        calls.append((tool_name, arguments))
        return ToolResult(success=True, output="")

    from casi.agent.pipelines import run_fix_pipeline

    run_fix_pipeline(
        "diagnose failing receipt",
        execute,
        repository_path=tmp_path,
        test_output="FAILED test_receipt.py::test_build - AssertionError",
    )

    read_calls = [
        arguments["path"] for tool_name, arguments in calls if tool_name == "read_file"
    ]
    assert "test_receipt.py" in read_calls
    assert "receipt.py" in read_calls
    assert "totals.py" in read_calls
    assert "catalog.py" in read_calls


def test_repair_context_paths_includes_source_from_failed_test(tmp_path: Path) -> None:
    from casi.agent.pipelines import repair_context_paths

    (tmp_path / "sorter.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "test_sorter.py").write_text(
        "from sorter import value\n\ndef test_value():\n    assert value == 2\n",
        encoding="utf-8",
    )
    output = (
        "FAILED test_sorter.py::test_value - AssertionError\n"
        "test_sorter.py:4: AssertionError\n"
    )

    paths = repair_context_paths(output, tmp_path)

    assert "test_sorter.py" in paths
    assert "sorter.py" in paths


def test_overview_discovers_documentation_without_assuming_readme_md(
    tmp_path: Path,
) -> None:
    from casi.agent.pipelines import run_overview_pipeline

    calls: list[tuple[str, dict[str, object]]] = []

    def execute(name: str, arguments: dict[str, object]) -> ToolResult:
        calls.append((name, arguments))
        return ToolResult(success=True, output="src/app.py\nreadme.rst\ndocs/README.md")

    run_overview_pipeline(execute)
    assert calls == [("list_files", {}), ("read_file", {"path": "readme.rst"})]

    calls.clear()
    run_overview_pipeline(
        lambda name, args: (
            calls.append((name, args)) or ToolResult(success=True, output="src/app.py")
        )
    )
    assert calls == [("list_files", {})]


def test_fix_context_resolves_configured_source_and_relative_imports(
    tmp_path: Path,
) -> None:
    from casi.agent.pipelines import run_fix_pipeline

    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\npythonpath = ["lib"]\n'
        'python_files = ["check_*.py"]\n'
    )
    package = tmp_path / "lib" / "shop"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "totals.py").write_text("from . import rates\nTOTAL = rates.RATE\n")
    (package / "rates.py").write_text("RATE = 1\n")
    checks = tmp_path / "checks"
    checks.mkdir()
    (checks / "check_totals.py").write_text(
        "from shop.totals import TOTAL\n\ndef test_total():\n    assert TOTAL == 2\n"
    )
    calls: list[tuple[str, dict[str, object]]] = []

    def execute(name: str, args: dict[str, object]) -> ToolResult:
        calls.append((name, args))
        return ToolResult(success=True, output="")

    assert run_fix_pipeline("Fix the totals", execute, repository_path=tmp_path) == []
    reads = [args["path"] for name, args in calls if name == "read_file"]
    assert reads == [
        "checks/check_totals.py",
        "lib/shop/totals.py",
        "lib/shop/__init__.py",
        "lib/shop/rates.py",
    ]


def test_src_layout_and_unknown_dependency_do_not_trigger_module_creation(
    tmp_path: Path,
) -> None:
    from casi.agent.pipelines import missing_local_module_paths, repair_context_paths

    package = tmp_path / "src" / "shop"
    package.mkdir(parents=True)
    (package / "cart.py").write_text("TOTAL = 1\n")
    (tmp_path / "cart_test.py").write_text(
        "from shop.cart import TOTAL\nimport external_service_sdk\n"
    )
    output = "FAILED cart_test.py::test_total - AssertionError"
    assert repair_context_paths(output, tmp_path) == [
        "cart_test.py",
        "src/shop/cart.py",
    ]
    assert (
        missing_local_module_paths(
            tmp_path, ["cart_test.py"], task_context="Fix cart.py"
        )
        == []
    )
