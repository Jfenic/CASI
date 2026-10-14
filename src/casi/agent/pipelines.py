"""Deterministic repository inspection pipelines."""

from __future__ import annotations

import ast
import re
from collections.abc import Callable
from pathlib import Path

from casi.agent.intent import TaskIntent, derive_search_queries, extract_search_targets
from casi.agent.nudges import PIPELINE_FALLBACK_PREFIX, ResponseNudge
from casi.agent.test_failures import extract_failure_paths
from casi.exceptions import SecurityError
from casi.repository.explorer import looks_like_filename, resolve_named_paths
from casi.repository.python_project import discover_test_files, python_source_roots
from casi.repository.security import safe_path
from casi.tools.result import ToolResult

ToolExecutor = Callable[[str, dict[str, object]], ToolResult]


def missing_local_module_paths(
    repository_path: str | Path,
    test_paths: list[str],
    *,
    test_output: str | None = None,
    task_context: str = "",
) -> list[str]:
    """Suggest absent imported files only when the task names their local path."""

    repository = Path(repository_path).resolve()
    missing: list[str] = []
    requested = [
        Path(target)
        for target in extract_search_targets(task_context)
        if Path(target).suffix == ".py"
    ]
    roots = python_source_roots(repository)

    def record(module: str) -> None:
        module_path = Path(*module.split("."))
        if any(
            (root / module_path.with_suffix(".py")).is_file()
            or (root / module_path).is_dir()
            for root in roots
        ):
            return
        for candidate in requested:
            if candidate.stem != module_path.name:
                continue
            try:
                path = safe_path(repository, candidate)
            except SecurityError:
                continue
            if not path.exists() and candidate.as_posix() not in missing:
                missing.append(candidate.as_posix())

    for relative_path in test_paths:
        if Path(relative_path).suffix != ".py":
            continue
        try:
            tree = ast.parse(
                safe_path(repository, relative_path).read_text(encoding="utf-8")
            )
        except (OSError, SyntaxError, UnicodeError, SecurityError):
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


def _local_module_paths_from_file(
    repository: Path,
    relative_path: str,
) -> list[str]:
    """Resolve repository-relative paths imported by one Python file."""

    paths: list[str] = []
    try:
        tree = ast.parse(
            safe_path(repository, relative_path).read_text(encoding="utf-8")
        )
    except (OSError, SyntaxError, UnicodeError, SecurityError):
        return paths

    module_paths: list[Path] = []
    roots = python_source_roots(repository)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                parent = (repository / relative_path).parent
                for _ in range(node.level - 1):
                    parent = parent.parent
                bases = [parent / Path(*(node.module or "").split("."))]
            else:
                bases = [root / Path(*(node.module or "").split(".")) for root in roots]
            module_paths.extend(bases)
            module_paths.extend(
                base / alias.name for base in bases for alias in node.names
            )
        elif isinstance(node, ast.Import):
            module_paths.extend(
                root / Path(*alias.name.split("."))
                for alias in node.names
                for root in roots
            )

    for module_path in module_paths:
        for candidate in (
            module_path.with_suffix(".py"),
            module_path / "__init__.py",
        ):
            try:
                resolved = safe_path(repository, candidate)
            except SecurityError:
                continue
            if resolved.is_file():
                path = resolved.relative_to(repository).as_posix()
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
        if Path(relative_path).suffix != ".py":
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

    result = execute("list_files", {})
    if not result.success:
        return
    readmes = sorted(
        (
            path
            for path in result.output.splitlines()
            if Path(path).stem.casefold() == "readme"
        ),
        key=lambda path: (len(Path(path).parts), path),
    )
    if readmes:
        execute("read_file", {"path": readmes[0]})


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
    for path in _source_paths_imported_by_tests(repository_path, paths[:]):
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
        read_paths.extend(discover_test_files(repository))

    read_paths = _expand_transitive_local_imports(repository, read_paths)

    for path in read_paths[:8]:
        if (repository / path).is_file():
            execute("read_file", {"path": path})

    discovered_tests = discover_test_files(repository)
    test_paths = [path for path in read_paths if path in discovered_tests]
    if not test_paths:
        test_paths = discovered_tests

    return missing_local_module_paths(
        repository_path,
        test_paths,
        test_output=test_output,
        task_context=context,
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
    if intent in {
        TaskIntent.INSPECT,
        TaskIntent.EXPLAIN,
        TaskIntent.SECURITY,
        TaskIntent.UNKNOWN,
    }:
        if extract_search_targets(context):
            run_inspect_pipeline(context, execute, repository_path=repository_path)
        else:
            run_overview_pipeline(execute)
        return
    if intent == TaskIntent.GIT_STATUS:
        run_git_status_pipeline(execute)
        return
    if intent in {
        TaskIntent.FIX,
        TaskIntent.ML,
        TaskIntent.CREATE,
        TaskIntent.TEST_ENGINEER,
        TaskIntent.REFACTOR,
    }:
        run_fix_pipeline(context, execute, repository_path=repository_path)


def nudge_after_fix_pipeline() -> ResponseNudge:
    return ResponseNudge(
        user_message=(
            f"{PIPELINE_FALLBACK_PREFIX} 'fix' loaded failing test and source files. "
            "Use the read_file results already in the conversation. You MUST call "
            "propose_file with the repository-relative source path and the complete "
            "corrected file content. CASI will generate the unified diff; do not "
            "write the diff yourself. Ensure your fix satisfies all explicit task "
            "specifications, types, and edge cases, not just visible tests. "
            "Start from the original source and change only the faulty behavior. "
            "Preserve existing validation guards, signatures, and return structure "
            "unless the task contract requires changing them. Stay within the "
            "requested scope and report unrelated pre-existing failures."
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
            f"{PIPELINE_FALLBACK_PREFIX} 'create' loaded relevant repository files. "
            "Use list_files results and the task contract to choose the correct path. "
            "You MUST call propose_file with the repository-relative path and complete "
            "new file content. CASI will generate the unified diff; "
            "do not write the diff yourself. For test-writing tasks, emit tests "
            "covering happy paths, boundary conditions, and expected exceptions."
        ),
    )


def nudge_after_explain_pipeline() -> ResponseNudge:
    return ResponseNudge(
        user_message=(
            f"{PIPELINE_FALLBACK_PREFIX} 'explain' loaded target files and "
            "repository context. "
            "Synthesize your explanation using the 5 technical sections: "
            "1. Propósito General, 2. Componentes Clave (Clases y Funciones), "
            "3. Dependencias e Interacciones, 4. Flujo de Datos y Ejecución, "
            "5. Puntos Clave para el Proyecto."
        ),
    )


def nudge_after_pipeline_fallback(intent: TaskIntent) -> ResponseNudge:
    if intent is TaskIntent.EXPLAIN:
        return nudge_after_explain_pipeline()
    return ResponseNudge(
        user_message=(
            f"{PIPELINE_FALLBACK_PREFIX} '{intent.value}' is now available "
            "from tool results. Answer the user's request from those results "
            'using {"type":"final","content":"your answer"}.'
        ),
    )
