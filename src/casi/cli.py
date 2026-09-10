"""Command-line entrypoint for CASI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from casi.agent.orchestrator import AgentOrchestrator, format_segment_approval_prompt
from casi.agent.planner import PlanSegment
from casi.agent.trace import AgentTraceRecorder
from casi.cli_agent import finalize_agent_run
from casi.cli_help import format_help
from casi.config import settings
from casi.exceptions import CasiError
from casi.interactive import InteractiveSession
from casi.llm.ollama_client import OllamaClient
from casi.observability.logging import emit_execution_log
from casi.repository.explorer import list_files
from casi.repository.reader import read_file
from casi.repository.search import search_code
from casi.sandbox.project_environment import (
    detect_project_environment,
    prepare_project_environment,
)
from casi.sandbox.test_execution import run_repository_pytest


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
        help=(
            "Maximum model decisions per agent. Defaults to each agent's profile limit."
        ),
    )
    parser.add_argument(
        "--routing",
        choices=("assist", "strict", "off"),
        default=settings.agent_routing_mode,
        help="Repository routing mode: assist, strict, or off.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print plan and trace details on stderr.",
    )
    parser.add_argument(
        "--save-patch",
        metavar="PATH",
        help="Write a proposed patch to PATH without applying it.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Approve tools and apply a valid patch without prompting.",
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
    read_parser.add_argument(
        "--file", required=True, help="File path within the repository."
    )
    read_parser.add_argument(
        "--start-line", type=int, default=1, help="First line to read."
    )
    read_parser.add_argument(
        "--end-line", type=int, default=300, help="Last line to read."
    )

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
        help=(
            "Maximum model decisions per agent. Defaults to each agent's profile limit."
        ),
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
        help=(
            "Command to explain (inspect, read, search, run, ask, "
            "fix, interactive, test, serve, env)."
        ),
    )

    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the CASI HTTP API server.",
    )
    serve_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address for the API server.",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the API server.",
    )

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="Run reproducible benchmark tasks and generate reports.",
    )
    benchmark_parser.add_argument(
        "--tasks-dir",
        default="benchmarks/tasks",
        help="Directory containing benchmark task YAML files.",
    )
    benchmark_parser.add_argument(
        "--repos-dir",
        default="benchmarks/repositories",
        help="Directory containing benchmark repository fixtures.",
    )
    benchmark_parser.add_argument(
        "--model",
        default=settings.ollama_model,
        help="Ollama model to use for a single-model run.",
    )
    benchmark_parser.add_argument(
        "--models",
        help="Comma-separated list of models to compare.",
    )
    benchmark_parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON (and optional Markdown) reports to this path.",
    )
    benchmark_parser.add_argument(
        "--format",
        choices=("text", "json", "markdown", "both"),
        default="text",
        help="Report format for stdout or file output.",
    )
    benchmark_parser.add_argument(
        "--routing",
        choices=("assist", "strict", "off"),
        default=settings.agent_routing_mode,
        help="Repository routing mode for agent tasks.",
    )
    benchmark_parser.add_argument(
        "--list",
        action="store_true",
        help="List loaded benchmark tasks and exit.",
    )
    benchmark_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show agent step progress for each benchmark task.",
    )
    benchmark_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-task progress output.",
    )

    return parser


def _run_inspect(repository: str | Path) -> int:
    files = list_files(repository)
    print(f"Repository: {Path(repository).resolve()}")
    print(f"Files ({len(files)}):")

    for file_path in files:
        print(file_path.as_posix())

    return 0


def _run_read(
    repository: str | Path, file_path: str, start_line: int, end_line: int
) -> int:
    print(read_file(repository, file_path, start_line=start_line, end_line=end_line))
    return 0


def _run_search(repository: str | Path, query: str, limit: int) -> int:
    results = search_code(repository, query, max_results=limit)
    print(f"Results ({len(results)}):")

    for result in results:
        print(f"{result.path}:{result.line_number}: {result.line}")

    return 0


def _emit_run_progress(plan, *, verbose: bool) -> None:
    if verbose:
        print("[plan]", file=sys.stderr)
        for line in plan.summary_lines():
            print(line, file=sys.stderr)
    print("[working] Executing plan...", file=sys.stderr)


def _confirm_tool(tool_name: str, arguments: dict[str, object], *, yes: bool) -> bool:
    _ = arguments
    if yes:
        return True
    print(f"[confirm] The agent wants to run `{tool_name}`.", file=sys.stderr)
    answer = input(f"Run {tool_name}? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def _approve_plan_segment(segment: PlanSegment, *, yes: bool) -> bool:
    if yes:
        return True
    print(format_segment_approval_prompt(segment), file=sys.stderr)
    answer = input("Approve phase> ").strip().lower()
    return answer in {"y", "yes", "s", "si", "sí"}


def _run_agent(
    repository: str | Path,
    task: str,
    max_steps: int | None,
    routing: str,
    *,
    save_patch: str | None = None,
    yes: bool = False,
    verbose: bool = False,
) -> int:
    """Run the bounded agent loop using the configured Ollama client."""

    trace = AgentTraceRecorder()
    orchestrator = AgentOrchestrator(
        OllamaClient(),
        repository,
        max_steps=max_steps,
        routing_mode=routing,
        require_tool_confirmation=lambda tool, args: _confirm_tool(tool, args, yes=yes),
        approve_segment=lambda segment: _approve_plan_segment(segment, yes=yes),
        on_context_compact=lambda message: print(
            f"[context] {message}", file=sys.stderr
        ),
        on_plan=lambda plan: _emit_run_progress(plan, verbose=verbose),
        on_step_start=lambda step, number, total: print(
            f"[working] Step {number}/{total}: {step.agent_name} ({step.agent_role})",
            file=sys.stderr,
        ),
        on_activity=lambda message: print(
            f"[working] {message}" if not verbose else f"[verbose] {message}",
            file=sys.stderr,
        ),
        trace=trace,
    )
    print("[working] Running agent...", file=sys.stderr)
    result = orchestrator.run(task)

    if verbose:
        emit_execution_log(trace)

    return finalize_agent_run(
        repository,
        result,
        save_patch=save_patch,
        yes=yes,
        verbose=verbose,
    )


def _run_interactive(
    repository: str | Path, max_steps: int | None, routing: str
) -> int:
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


def _run_serve(host: str, port: int) -> int:
    """Start the FastAPI application with uvicorn."""

    try:
        import uvicorn
    except ImportError as exc:
        raise CasiError(
            "The API server requires optional dependencies. "
            "Install them with: pip install -e '.[api]'"
        ) from exc

    from casi.api.app import create_app

    uvicorn.run(create_app(), host=host, port=port)
    return 0


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


def _run_benchmark(
    tasks_dir: Path,
    repos_dir: Path,
    *,
    model: str,
    models: str | None,
    output: Path | None,
    report_format: str,
    routing: str,
    list_only: bool,
    verbose: bool,
    quiet: bool,
) -> int:
    from casi.evaluation.benchmark import load_tasks
    from casi.evaluation.report import (
        build_comparison_payload,
        build_report_payload,
        render_comparison_report,
        render_markdown_report,
        render_report,
        write_report_files,
    )
    from casi.evaluation.runner import (
        BenchmarkRunOptions,
        compare_models,
        run_model_benchmark,
    )

    tasks = load_tasks(tasks_dir)
    if list_only:
        for task in tasks:
            print(f"{task.task_id}\t{task.category}\t{task.repository}\t{task.name}")
        return 0

    options = BenchmarkRunOptions(
        repositories_root=repos_dir,
        routing=routing,
        verbose=verbose,
        show_progress=not quiet,
        artifacts_dir=(output.parent / f"{output.stem}-artifacts") if output else None,
    )
    if models:
        model_list = [item.strip() for item in models.split(",") if item.strip()]
        if not model_list:
            raise ValueError("Provide at least one model in --models")
        runs = compare_models(tasks, model_list, options=options)
        if report_format == "text":
            print(render_comparison_report(runs))
        payload = build_comparison_payload(runs)
        markdown = None
        if report_format in {"markdown", "both"}:
            markdown = "\n\n".join(
                render_markdown_report(run.results, model=run.model) for run in runs
            )
        if output is not None:
            write_report_files(payload, output, markdown=markdown)
        elif report_format == "json":
            import json

            print(json.dumps(payload, indent=2, ensure_ascii=False))
        elif report_format in {"markdown", "both"} and markdown is not None:
            print(markdown)
        return 0

    client = OllamaClient(model=model)
    run = run_model_benchmark(tasks, client=client, options=options)
    if report_format == "text":
        print(render_report(run.results, model=run.model))
    payload = build_report_payload(run.results, model=run.model)
    markdown = render_markdown_report(run.results, model=run.model)
    if output is not None:
        write_report_files(
            payload,
            output,
            markdown=markdown if report_format in {"markdown", "both"} else None,
        )
    elif report_format == "json":
        import json

        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif report_format in {"markdown", "both"}:
        print(markdown)
    return 0


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
            return _run_agent(
                args.repo,
                args.task,
                args.max_steps,
                args.routing,
                save_patch=getattr(args, "save_patch", None),
                yes=getattr(args, "yes", False),
                verbose=getattr(args, "verbose", False),
            )

        if args.command == "interactive":
            return _run_interactive(args.repo, args.max_steps, args.routing)

        if args.command == "test":
            return _run_test(args.repo, args.timeout)

        if args.command == "env" and args.env_command == "prepare":
            return _prepare_environment(args.repo, approved=args.yes)

        if args.command == "help":
            print(format_help(getattr(args, "topic", None)))
            return 0

        if args.command == "serve":
            return _run_serve(args.host, args.port)

        if args.command == "benchmark":
            return _run_benchmark(
                Path(args.tasks_dir),
                Path(args.repos_dir),
                model=args.model,
                models=args.models,
                output=args.output,
                report_format=args.format,
                routing=args.routing,
                list_only=args.list,
                verbose=args.verbose,
                quiet=args.quiet,
            )

        parser.error(f"Unknown command: {args.command}")
    except CasiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (FileNotFoundError, IsADirectoryError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
