"""Command-line entrypoint for CASI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from casi.agent.orchestrator import AgentOrchestrator
from casi.cli_help import format_help
from casi.config import settings
from casi.exceptions import CasiError
from casi.interactive import InteractiveSession
from casi.llm.ollama_client import OllamaClient
from casi.repository.explorer import list_files
from casi.repository.reader import read_file
from casi.repository.search import search_code
from casi.sandbox.project_environment import (
    detect_project_environment,
    prepare_project_environment,
)
from casi.sandbox.test_execution import run_repository_pytest
from casi.tools.registry import ToolRegistry


def _add_agent_task_parser(
    subparsers,
    name: str,
    *,
    help_text: str,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name, help=help_text)
    parser.add_argument("--repo", required=True, help="Repository path.")
    parser.add_argument("--task", required=True, help="Task for the coding agent.")
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Maximum model decisions per agent. Defaults to each agent's profile limit.",
    )
    parser.add_argument(
        "--routing",
        choices=("assist", "strict", "off"),
        default=settings.agent_routing_mode,
        help="Repository routing mode: assist, strict, or off.",
    )
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="casi",
        description=(
            "CASI — local code agent for repository inspection, patching, "
            "sandboxed testing, and evaluation."
        ),
        epilog="Run `casi help` for a guided overview of each command.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="List repository files.",
    )
    inspect_parser.add_argument("--repo", required=True, help="Repository path.")

    read_parser = subparsers.add_parser(
        "read",
        help="Read a file from the repository.",
    )
    read_parser.add_argument("--repo", required=True, help="Repository path.")
    read_parser.add_argument("--file", required=True, help="File path within the repository.")
    read_parser.add_argument("--start-line", type=int, default=1, help="First line to read.")
    read_parser.add_argument("--end-line", type=int, default=300, help="Last line to read.")

    search_parser = subparsers.add_parser(
        "search",
        help="Search text inside the repository.",
    )
    search_parser.add_argument("--repo", required=True, help="Repository path.")
    search_parser.add_argument("--query", required=True, help="Text to search for.")
    search_parser.add_argument(
        "--limit",
        type=int,
        default=settings.max_search_results,
        help="Maximum number of results to show.",
    )

    _add_agent_task_parser(
        subparsers,
        "run",
        help_text="Run the coding agent on a repository task.",
    )
    _add_agent_task_parser(
        subparsers,
        "ask",
        help_text="Ask a read-focused question about the repository.",
    )
    _add_agent_task_parser(
        subparsers,
        "fix",
        help_text="Ask CASI to fix code or tests in the repository.",
    )

    interactive_parser = subparsers.add_parser(
        "interactive",
        help="Start an interactive agent session.",
    )
    interactive_parser.add_argument("--repo", required=True, help="Repository path.")
    interactive_parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Maximum model decisions per agent. Defaults to each agent's profile limit.",
    )
    interactive_parser.add_argument(
        "--routing",
        choices=("assist", "strict", "off"),
        default=settings.agent_routing_mode,
        help="Repository routing mode: assist, strict, or off.",
    )

    test_parser = subparsers.add_parser(
        "test",
        help="Run the repository test suite.",
    )
    test_parser.add_argument("--repo", required=True, help="Repository path.")
    test_parser.add_argument(
        "--timeout",
        type=float,
        default=settings.test_timeout_seconds,
        help="Timeout in seconds for the test command.",
    )

    env_parser = subparsers.add_parser(
        "env",
        help="Manage a repository-specific test environment.",
    )
    env_subparsers = env_parser.add_subparsers(dest="env_command", required=True)
    prepare_parser = env_subparsers.add_parser(
        "prepare",
        help="Build a cached Docker image containing project dependencies.",
    )
    prepare_parser.add_argument("--repo", required=True, help="Repository path.")
    prepare_parser.add_argument(
        "--yes",
        action="store_true",
        help="Approve the networked dependency installation without prompting.",
    )

    help_parser = subparsers.add_parser(
        "help",
        help="Explain CASI commands and show usage examples.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    help_parser.add_argument(
        "topic",
        nargs="?",
        help="Command to explain (inspect, read, search, run, ask, fix, interactive, test, env).",
    )

    return parser


def _run_inspect(repository: str | Path) -> int:
    files = list_files(repository)
    print(f"Repository: {Path(repository).resolve()}")
    print(f"Files ({len(files)}):")

    for file_path in files:
        print(file_path.as_posix())

    return 0


def _run_read(repository: str | Path, file_path: str, start_line: int, end_line: int) -> int:
    print(read_file(repository, file_path, start_line=start_line, end_line=end_line))
    return 0


def _run_search(repository: str | Path, query: str, limit: int) -> int:
    results = search_code(repository, query, max_results=limit)
    print(f"Results ({len(results)}):")

    for result in results:
        print(f"{result.path}:{result.line_number}: {result.line}")

    return 0


def _emit_run_progress(plan) -> None:
    print("[plan]", file=sys.stderr)
    for line in plan.summary_lines():
        print(line, file=sys.stderr)
    print("[working] Executing plan...", file=sys.stderr)


def _run_agent(
    repository: str | Path,
    task: str,
    max_steps: int | None,
    routing: str,
) -> int:
    """Run the bounded agent loop using the configured Ollama client."""

    orchestrator = AgentOrchestrator(
        OllamaClient(),
        repository,
        max_steps=max_steps,
        routing_mode=routing,
        approve_segment=lambda _segment: True,
        on_context_compact=lambda message: print(f"[context] {message}", file=sys.stderr),
        on_plan=lambda plan: _emit_run_progress(plan),
        on_step_start=lambda step, number, total: print(
            f"[working] Step {number}/{total}: {step.agent_name} ({step.agent_role})",
            file=sys.stderr,
        ),
        on_activity=lambda message: print(f"[working] {message}", file=sys.stderr),
    )
    print("[working] Running agent...", file=sys.stderr)
    result = orchestrator.run(task)

    if result.success:
        print(result.response)
        return 0

    print(result.error or "Agent failed without an error message.", file=sys.stderr)
    return 1


def _run_interactive(repository: str | Path, max_steps: int | None, routing: str) -> int:
    session = InteractiveSession(
        repository,
        OllamaClient(),
        max_steps=max_steps,
        routing_mode=routing,
    )
    return session.run()


def _run_test(repository: str | Path, timeout: float) -> int:
    """Run pytest in the repository and print structured output."""

    result, runner_kind = run_repository_pytest(
        repository,
        timeout_seconds=timeout,
    )

    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)

    print(
        f"runner={runner_kind} "
        f"exit_code={result.exit_code} "
        f"duration={result.duration_seconds:.2f}s "
        f"timed_out={result.timed_out}"
    )
    return 0 if result.exit_code == 0 and not result.timed_out else 1


def _prepare_environment(repository: str | Path, *, approved: bool) -> int:
    """Prepare a cached dependency image after explicit approval."""

    environment = detect_project_environment(repository)
    if environment is None:
        raise ValueError("No supported Python dependency files were found")

    print(f"manager={environment.manager}")
    print(f"files={','.join(environment.dependency_files)}")
    print(f"image={environment.image}")
    print("This build downloads dependencies and may execute package build scripts.")
    if not approved:
        answer = input("Build project environment with network access? [y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            print("Environment preparation cancelled.")
            return 1

    result = prepare_project_environment(repository)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.success:
        print(f"Prepared image: {result.image}")
        return 0
    print(
        f"Environment build failed with exit code {result.returncode}.",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    else:
        argv = list(argv)

    if len(argv) >= 2 and argv[0] == "run" and argv[1] == "interactive":
        argv = ["interactive", *argv[2:]]

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "inspect":
            return _run_inspect(args.repo)

        if args.command == "read":
            return _run_read(args.repo, args.file, args.start_line, args.end_line)

        if args.command == "search":
            return _run_search(args.repo, args.query, args.limit)

        if args.command in {"run", "ask", "fix"}:
            return _run_agent(args.repo, args.task, args.max_steps, args.routing)

        if args.command == "interactive":
            return _run_interactive(args.repo, args.max_steps, args.routing)

        if args.command == "test":
            return _run_test(args.repo, args.timeout)

        if args.command == "env" and args.env_command == "prepare":
            return _prepare_environment(args.repo, approved=args.yes)

        if args.command == "help":
            print(format_help(getattr(args, "topic", None)))
            return 0

        parser.error(f"Unknown command: {args.command}")
    except CasiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (FileNotFoundError, IsADirectoryError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
