"""Command-line entrypoint for CASI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from casi.agent.loop import AgentLoop
from casi.config import settings
from casi.exceptions import CasiError
from casi.interactive import InteractiveSession
from casi.llm.ollama_client import OllamaClient
from casi.repository.explorer import list_files
from casi.repository.reader import read_file
from casi.repository.search import search_code
from casi.tools.registry import ToolRegistry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="casi")
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

    run_parser = subparsers.add_parser(
        "run",
        help="Run the coding agent on a repository task.",
    )
    run_parser.add_argument("--repo", required=True, help="Repository path.")
    run_parser.add_argument("--task", required=True, help="Task for the coding agent.")
    run_parser.add_argument(
        "--max-steps",
        type=int,
        default=8,
        help="Maximum number of model decisions.",
    )

    interactive_parser = subparsers.add_parser(
        "interactive",
        help="Start an interactive agent session.",
    )
    interactive_parser.add_argument("--repo", required=True, help="Repository path.")
    interactive_parser.add_argument(
        "--max-steps",
        type=int,
        default=8,
        help="Maximum number of model decisions per task.",
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


def _run_agent(repository: str | Path, task: str, max_steps: int) -> int:
    """Run the bounded agent loop using the configured Ollama client."""

    client = OllamaClient()
    registry = ToolRegistry(repository)
    result = AgentLoop(client, registry, max_steps=max_steps).run(task)

    if result.success:
        print(result.response)
        return 0

    print(result.error or "Agent failed without an error message.", file=sys.stderr)
    return 1


def _run_interactive(repository: str | Path, max_steps: int) -> int:
    session = InteractiveSession(
        repository,
        OllamaClient(),
        max_steps=max_steps,
    )
    return session.run()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "inspect":
            return _run_inspect(args.repo)

        if args.command == "read":
            return _run_read(args.repo, args.file, args.start_line, args.end_line)

        if args.command == "search":
            return _run_search(args.repo, args.query, args.limit)

        if args.command == "run":
            return _run_agent(args.repo, args.task, args.max_steps)

        if args.command == "interactive":
            return _run_interactive(args.repo, args.max_steps)

        parser.error(f"Unknown command: {args.command}")
    except CasiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (FileNotFoundError, IsADirectoryError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
