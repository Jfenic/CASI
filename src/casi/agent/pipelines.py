"""Deterministic repository inspection pipelines."""

from __future__ import annotations

import ast
import re
import sys
from collections.abc import Callable
from importlib.metadata import packages_distributions
from pathlib import Path

from casi.agent.intent import TaskIntent, derive_search_queries, extract_search_targets
from casi.agent.nudges import PIPELINE_FALLBACK_PREFIX, ResponseNudge
from casi.agent.test_failures import extract_failure_paths
from casi.repository.explorer import looks_like_filename, resolve_named_paths
from casi.tools.result import ToolResult

ToolExecutor = Callable[[str, dict[str, object]], ToolResult]


def _local_module_candidates(module: str) -> list[str]:
    root = module.split(".")[0]
    base = Path(root)
    return [base.with_suffix(".py").as_posix(), (base / "__init__.py").as_posix()]


def missing_local_module_paths(
    repository_path: str | Path,
    test_paths: list[str],
    *,
    test_output: str | None = None,
) -> list[str]:
    """Return repository-relative paths for imported local modules that do not exist."""

    repository = Path(repository_path).resolve()
    missing: list[str] = []
    external_modules = sys.stdlib_module_names | packages_distributions().keys()

    def record(module: str) -> None:
        root = module.split(".")[0]
        if root in external_modules:
            return
        candidate = Path(root).with_suffix(".py").as_posix()
        package_init = (Path(root) / "__init__.py").as_posix()
        if (repository / candidate).is_file() or (repository / package_init).is_file():
            return
        if candidate not in missing:
            missing.append(candidate)

    for relative_path in test_paths:
        if not Path(relative_path).name.startswith("test_"):
            continue
        try:
            tree = ast.parse((repository / relative_path).read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                record(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    record(alias.name)

    if test_output:
        for match in re.finditer(
            (
                "(?:ModuleNotFoundError|ImportError).*?(?:No module "
                "named )['\\\"]([^'\\\"]+)['\\\"]"
            ),
            test_output,
            flags=re.DOTALL,
        ):
            record(match.group(1))

    return missing


def _external_module_roots() -> set[str]:
    return set(sys.stdlib_module_names) | set(packages_distributions().keys())


def _local_module_paths_from_file(
    repository: Path,
    relative_path: str,
) -> list[str]:
    """Resolve repository-relative paths imported by one Python file."""

    paths: list[str] = []
    external_modules = _external_module_roots()
    try:
        tree = ast.parse((repository / relative_path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeError):
        return paths

    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)

    for module in modules:
        root = module.split(".")[0]
        if root in external_modules:
            continue
        module_path = Path(*module.split("."))
        for candidate in (
            module_path.with_suffix(".py"),
            module_path / "__init__.py",
        ):
            if (repository / candidate).is_file():
                path = candidate.as_posix()
                if path not in paths:
                    paths.append(path)
                break
    return paths


def _source_paths_imported_by_tests(
    repository_path: str | Path,
    test_paths: list[str],
) -> list[str]:
    """Resolve simple local imports from failed Python test files."""

    repository = Path(repository_path).resolve()
    paths: list[str] = []
    for relative_path in test_paths:
        if not Path(relative_path).name.startswith("test_"):
            continue
        for path in _local_module_paths_from_file(repository, relative_path):
            if path not in paths:
                paths.append(path)
    return paths


def _expand_transitive_local_imports(
    repository: Path,
    read_paths: list[str],
    *,
    limit: int = 8,
) -> list[str]:
    """Follow local imports across modules so multi-file bugs preload the chain."""

    ordered = list(read_paths)
    seen = set(ordered)
    queue = [path for path in ordered if path.endswith(".py")]
    while queue and len(ordered) < limit:
        current = queue.pop(0)
        for path in _local_module_paths_from_file(repository, current):
            if path in seen:
                continue
            seen.add(path)
            ordered.append(path)
            queue.append(path)
    return ordered


def paths_from_search_output(output: str) -> list[str]:
    """Extract unique file paths from search_code output lines."""

    paths: list[str] = []
    for line in output.splitlines():
        if ":" not in line:
            continue
        path = line.split(":", 1)[0].strip()
        if path and path not in paths:
            paths.append(path)
    return paths


def run_inspect_pipeline(
    context: str,
    execute: ToolExecutor,
    *,
    repository_path: str | Path,
) -> None:
    """Search the repository and read the most relevant files."""

    read_paths = resolve_named_paths(repository_path, extract_search_targets(context))

    for query in derive_search_queries(context):
        if looks_like_filename(query):
            continue
        result = execute("search_code", {"query": query})
        if not result.output.strip():
            continue
        for path in paths_from_search_output(result.output):
            if path not in read_paths:
                read_paths.append(path)
        if read_paths:
            break

    for path in read_paths[:3]:
        execute("read_file", {"path": path})

    if not read_paths:
        execute("list_files", {})


def run_overview_pipeline(execute: ToolExecutor) -> None:
    """Collect a repository overview from structure and documentation."""

    execute("list_files", {})
    execute("read_file", {"path": "README.md"})


def run_git_status_pipeline(execute: ToolExecutor) -> None:
    """Collect current repository changes."""

    execute("git_diff", {})


def repair_context_paths(
    test_output: str | None,
    repository_path: str | Path,
) -> list[str]:
    """Return test and source paths that repair work should load."""

    if not test_output:
        return []
    paths: list[str] = []
    for path in extract_failure_paths(test_output):
        if (Path(repository_path) / path).is_file() and path not in paths:
            paths.append(path)
    test_paths = [path for path in paths if Path(path).name.startswith("test_")]
    for path in _source_paths_imported_by_tests(repository_path, test_paths):
        if path not in paths:
            paths.append(path)
    return paths


def run_fix_pipeline(
    context: str,
    execute: ToolExecutor,
    *,
    repository_path: str | Path,
    test_output: str | None = None,
) -> list[str]:
    """Load source and test files involved in a failing test run."""

    repository = Path(repository_path).resolve()
    read_paths: list[str] = []

    if test_output:
        for path in extract_failure_paths(test_output):
            if path not in read_paths:
                read_paths.append(path)
        for path in _source_paths_imported_by_tests(repository_path, read_paths):
            if path not in read_paths:
                read_paths.append(path)

    for path in resolve_named_paths(repository_path, extract_search_targets(context)):
        if path not in read_paths:
            read_paths.append(path)

    if not read_paths:
        for query in derive_search_queries(context):
            if looks_like_filename(query):
                continue
            result = execute("search_code", {"query": query})
            if not result.output.strip():
                continue
            for path in paths_from_search_output(result.output):
                if path not in read_paths:
                    read_paths.append(path)
            if read_paths:
                break

    if not read_paths:
        read_paths.extend(
            path.relative_to(repository).as_posix()
            for path in sorted(repository.glob("test_*.py"))
        )

    read_paths = _expand_transitive_local_imports(repository, read_paths)

    for path in read_paths[:8]:
        if (repository / path).is_file():
            execute("read_file", {"path": path})

    test_paths = [path for path in read_paths if Path(path).name.startswith("test_")]
    if not test_paths:
        test_paths = [
            path.relative_to(repository).as_posix()
            for path in sorted(repository.glob("test_*.py"))
        ]

    return missing_local_module_paths(
        repository_path,
        test_paths,
        test_output=test_output,
    )


def run_diagnose_pipeline(
    context: str,
    execute: ToolExecutor,
    *,
    repository_path: str | Path,
    test_output: str | None = None,
) -> list[str]:
    """Run tests and load failing source files for bounded diagnosis tasks."""

    if test_output is None:
        result = execute("run_tests", {})
        if not result.success:
            test_output = result.output or result.error or ""
    return run_fix_pipeline(
        context,
        execute,
        repository_path=repository_path,
        test_output=test_output,
    )


def run_repository_pipeline(
    intent: TaskIntent,
    context: str,
    execute: ToolExecutor,
    *,
    repository_path: str | Path,
) -> None:
    """Run the deterministic pipeline associated with a task intent."""

    if intent == TaskIntent.OVERVIEW:
        run_overview_pipeline(execute)
        return
    if intent == TaskIntent.DIAGNOSE:
        run_diagnose_pipeline(context, execute, repository_path=repository_path)
        return
    if intent in {TaskIntent.INSPECT, TaskIntent.UNKNOWN}:
        if extract_search_targets(context):
            run_inspect_pipeline(context, execute, repository_path=repository_path)
        else:
            run_overview_pipeline(execute)
        return
    if intent == TaskIntent.GIT_STATUS:
        run_git_status_pipeline(execute)
        return
    if intent in {TaskIntent.FIX, TaskIntent.ML, TaskIntent.CREATE}:
        run_fix_pipeline(context, execute, repository_path=repository_path)


def nudge_after_fix_pipeline() -> ResponseNudge:
    return ResponseNudge(
        user_message=(
            f"{PIPELINE_FALLBACK_PREFIX} 'fix' loaded failing test and source files. "
            "Use the read_file results already in the conversation. You MUST call "
            "propose_file with the repository-relative source path and the complete "
            "corrected file content. CASI will generate the unified diff; do not "
            "write the diff yourself."
        ),
    )


def nudge_after_diagnose_pipeline() -> ResponseNudge:
    return ResponseNudge(
        user_message=(
            f"{PIPELINE_FALLBACK_PREFIX} 'diagnose' loaded failing tests and source "
            "files. Use the tool results already in the conversation. Reply with one "
            "final JSON response only. The content must be a JSON object with keys "
            "file, line, cause, and evidence. Do not call propose_file, apply_patch, "
            "or include diffs. Identify the implementation statement causing the "
            "failure and explain why it disagrees with the expected behavior; "
            "the failed assertion alone is a symptom, not a root cause."
        ),
    )


def nudge_after_create_pipeline() -> ResponseNudge:
    return ResponseNudge(
        user_message=(
            f"{PIPELINE_FALLBACK_PREFIX} 'create' loaded the failing tests. "
            "The missing module does not exist yet. You MUST call propose_file with "
            "the repository-relative path and complete new file content that satisfies "
            "the tests. CASI will generate the unified diff; "
            "do not write the diff yourself."
        ),
    )


def nudge_after_pipeline_fallback(intent: TaskIntent) -> ResponseNudge:
    return ResponseNudge(
        user_message=(
            f"{PIPELINE_FALLBACK_PREFIX} '{intent.value}' is now available "
            "from tool results. Answer the user's request from those results "
            'using {"type":"final","content":"your answer"}.'
        ),
    )
