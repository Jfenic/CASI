"""Execute benchmark tasks against local repositories and models."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from casi.agent.orchestrator import AgentOrchestrator, OrchestratorResult
from casi.agent.run_outcome import resolve_agent_run_outcome
from casi.agent.trace import AgentTraceRecorder
from casi.config import settings
from casi.evaluation.benchmark import (
    BenchmarkModelRun,
    BenchmarkTask,
    BenchmarkTaskResult,
)
from casi.evaluation.grading import grade_task
from casi.evaluation.progress import (
    emit_model_header,
    emit_task_finish,
    emit_task_start,
)
from casi.exceptions import CasiError
from casi.llm.base import LLMClient
from casi.llm.ollama_client import OllamaClient
from casi.observability.metrics import summarize_trace
from casi.observability.tracing import reconstruct_trace
from casi.patching.applier import PatchApplicationError, apply_patch


@dataclass(frozen=True)
class BenchmarkRunOptions:
    repositories_root: Path
    auto_apply_patches: bool = True
    routing: str = "assist"
    verbose: bool = False
    show_progress: bool = True
    artifacts_dir: Path | None = None


def prepare_repository(repository: Path) -> None:
    """Ensure a benchmark repository is a git work tree for patch checks."""

    if (repository / ".git").exists():
        return

    subprocess.run(["git", "init"], cwd=repository, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "benchmark@casi.local"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "CASI Benchmark"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "add", "-A"], cwd=repository, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "benchmark baseline"],
        cwd=repository,
        check=True,
        capture_output=True,
    )


def copy_repository(source: Path, destination: Path) -> None:
    """Copy a benchmark repository into an isolated temporary directory."""

    if destination.exists():
        shutil.rmtree(destination)

    def ignore(_path: str, names: list[str]) -> set[str]:
        return {
            name for name in names if name in {".git", "__pycache__", ".pytest_cache"}
        }

    shutil.copytree(source, destination, ignore=ignore)
    prepare_repository(destination)


def run_success_command(task: BenchmarkTask, repository: Path) -> bool:
    """Run a task's verification command inside the repository."""

    if not task.success_command:
        return True

    try:
        result = subprocess.run(
            task.success_command,
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
            timeout=settings.test_timeout_seconds,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0


def resolve_benchmark_max_steps(task: BenchmarkTask) -> int:
    """Apply category-aware step limits while honoring explicit task overrides."""

    if task.category == "create":
        return max(task.max_steps, settings.create_max_steps)
    if task.category == "fix":
        return max(task.max_steps, settings.fix_max_steps)
    return task.max_steps


def evaluate_task_success(
    task: BenchmarkTask,
    *,
    agent_success: bool,
    command_success: bool | None,
) -> bool:
    """Score a task using category-appropriate success criteria."""

    if task.grader_directory is not None:
        return agent_success and command_success is True
    if task.category in {"inspect", "read", "search"}:
        # Read-only tasks may run on repos with intentionally failing tests.
        return agent_success
    if command_success is not None:
        return agent_success and command_success
    return agent_success


def run_task(
    task: BenchmarkTask,
    *,
    repositories_root: Path,
    client: LLMClient,
    options: BenchmarkRunOptions | None = None,
) -> BenchmarkTaskResult:
    """Run one benchmark task in an isolated repository copy."""

    opts = options or BenchmarkRunOptions(repositories_root=repositories_root)
    if not task.repository:
        raise ValueError(f"Task {task.task_id} is missing a repository")

    source = repositories_root / task.repository
    if not source.is_dir():
        raise FileNotFoundError(f"Benchmark repository not found: {source}")

    model = getattr(client, "model", "unknown")
    if not isinstance(model, str):
        model = "unknown"

    with tempfile.TemporaryDirectory(prefix="casi-benchmark-") as temp_dir:
        repository = Path(temp_dir) / task.repository
        copy_repository(source, repository)

        trace = AgentTraceRecorder()
        started = time.perf_counter()

        def on_activity(message: str) -> None:
            if opts.verbose and opts.show_progress:
                emit_task_activity(message)

        def on_step_start(step, number, total) -> None:
            if opts.verbose and opts.show_progress:
                emit_task_activity(
                    f"Step {number}/{total}: {step.agent_name} ({step.agent_role})"
                )

        orchestrator = AgentOrchestrator(
            client,
            repository,
            max_steps=resolve_benchmark_max_steps(task),
            routing_mode=opts.routing,
            require_tool_confirmation=lambda _tool, _args: True,
            approve_segment=lambda _segment: True,
            on_activity=on_activity if opts.verbose else None,
            on_step_start=on_step_start if opts.verbose else None,
            trace=trace,
        )
        try:
            result = orchestrator.run(task.instruction, category=task.category)
        except CasiError as exc:
            result = OrchestratorResult(success=False, error=str(exc))
        duration_seconds = time.perf_counter() - started

        outcome = resolve_agent_run_outcome(repository, result)
        patch_applied = False
        patch_valid = outcome.patch_valid if outcome.patch is not None else None
        agent_success = result.success
        agent_error = result.error

        out_of_scope = set(outcome.patch_files) - set(task.allowed_files)
        scope_rejected = bool(task.allowed_files and out_of_scope)
        if scope_rejected:
            agent_success = False
            agent_error = "Patch changes disallowed files: " + ", ".join(
                sorted(out_of_scope)
            )

        if (
            not scope_rejected
            and opts.auto_apply_patches
            and outcome.awaiting_patch_approval
            and outcome.patch is not None
        ):
            try:
                apply_patch(repository, outcome.patch, approved=True, dry_run=False)
                patch_applied = True
            except PatchApplicationError as exc:
                agent_success = False
                agent_error = str(exc)

        trace.mark_finished()
        execution = reconstruct_trace(trace)
        metrics = summarize_trace(execution)
        verification_output = ""
        verification_runner = None
        verification_timed_out = False
        if task.grader_directory is not None:
            try:
                verification, verification_runner = grade_task(
                    task,
                    original=source,
                    candidate=repository,
                    timeout_seconds=settings.test_timeout_seconds,
                )
                verification_output = (
                    verification.stdout + "\n" + verification.stderr
                ).strip()
                verification_timed_out = verification.timed_out
                command_success = (
                    verification.exit_code == 0 and not verification.timed_out
                )
            except (RuntimeError, ValueError, OSError) as exc:
                command_success = False
                verification_output = str(exc)
                verification_runner = "unavailable"
            if not command_success and not agent_error:
                agent_error = "Independent verification failed: " + verification_output
        else:
            command_success = (
                run_success_command(task, repository) if task.success_command else None
            )
        if opts.artifacts_dir is not None:
            safe_model = re.sub(r"[^a-zA-Z0-9_.-]", "_", model).strip(".") or "model"
            safe_task = (
                re.sub(r"[^a-zA-Z0-9_.-]", "_", task.task_id).strip(".") or "task"
            )
            artifact_dir = opts.artifacts_dir / safe_model / safe_task
            artifact_dir.mkdir(parents=True, exist_ok=True)
            trace.save(artifact_dir / "trace.json")
            (artifact_dir / "response.txt").write_text(
                result.response, encoding="utf-8"
            )
            (artifact_dir / "verification.txt").write_text(
                verification_output, encoding="utf-8"
            )
            proposal_path = artifact_dir / "proposal.diff"
            if outcome.patch is not None:
                proposal_path.write_text(outcome.patch, encoding="utf-8")
            else:
                proposal_path.unlink(missing_ok=True)
        task_success = evaluate_task_success(
            task,
            agent_success=agent_success,
            command_success=command_success,
        )

        correction_attempts = 0
        if result.patch_verification is not None:
            correction_attempts = result.patch_verification.correction_attempts

        benchmark_result = BenchmarkTaskResult(
            task_id=task.task_id,
            name=task.name,
            repository=task.repository,
            category=task.category,
            model=model,
            agent_success=agent_success,
            task_success=task_success,
            agent_response=result.response,
            agent_error=agent_error,
            steps=int(metrics.total_steps),
            duration_seconds=duration_seconds,
            command_success=command_success,
            patch_valid=patch_valid,
            patch_applied=patch_applied,
            files_read=int(metrics.files_read),
            tool_calls=int(metrics.tool_calls),
            prompt_tokens=int(metrics.prompt_tokens),
            completion_tokens=int(metrics.completion_tokens),
            correction_attempts=correction_attempts,
            capability=task.capability,
            difficulty=task.difficulty,
            verification_output=verification_output,
            verification_runner=verification_runner,
            verification_timed_out=verification_timed_out,
        )
        if opts.artifacts_dir is not None:
            (artifact_dir / "result.json").write_text(
                json.dumps(asdict(benchmark_result), indent=2, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
        return benchmark_result


def emit_task_activity(message: str) -> None:
    from casi.evaluation.progress import emit_benchmark_line

    emit_benchmark_line(f"[benchmark]     {message}")


def run_model_benchmark(
    tasks: list[BenchmarkTask],
    *,
    client: LLMClient,
    options: BenchmarkRunOptions,
) -> BenchmarkModelRun:
    """Run all tasks for one model."""

    model = getattr(client, "model", "unknown")
    if not isinstance(model, str):
        model = "unknown"

    if options.show_progress:
        emit_model_header(model, task_count=len(tasks))

    results: list[BenchmarkTaskResult] = []
    total = len(tasks)
    for index, task in enumerate(tasks, start=1):
        if options.show_progress:
            emit_task_start(task, index=index, total=total, model=model)
        result = run_task(
            task,
            repositories_root=options.repositories_root,
            client=client,
            options=options,
        )
        results.append(result)
        if options.show_progress:
            emit_task_finish(result)
    return BenchmarkModelRun(model=model, results=results)


def compare_models(
    tasks: list[BenchmarkTask],
    models: list[str],
    *,
    options: BenchmarkRunOptions,
    client_factory: Callable[[str], LLMClient] | None = None,
) -> list[BenchmarkModelRun]:
    """Run the same tasks against multiple local models."""

    factory = client_factory or (lambda model: OllamaClient(model=model))
    return [
        run_model_benchmark(tasks, client=factory(model), options=options)
        for model in models
    ]
