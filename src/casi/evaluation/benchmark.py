"""Benchmark orchestration utilities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from casi.agent.state import AgentResult


@dataclass(frozen=True)
class BenchmarkTask:
    """Definition for a single benchmark task."""

    task_id: str
    name: str
    instruction: str
    repository: str = ""
    category: str = "general"
    max_steps: int = 8
    success_command: list[str] = field(default_factory=list)
    capability: str = "unspecified"
    difficulty: str = "unspecified"
    allowed_files: tuple[str, ...] = ()
    grader_directory: Path | None = None


@dataclass(frozen=True)
class BenchmarkTaskResult:
    """Outcome for one benchmark task execution."""

    task_id: str
    name: str = ""
    repository: str = ""
    category: str = ""
    model: str = ""
    agent_success: bool = False
    task_success: bool = False
    agent_response: str = ""
    agent_error: str | None = None
    steps: int = 0
    duration_seconds: float = 0.0
    command_success: bool | None = None
    patch_valid: bool | None = None
    patch_applied: bool = False
    files_read: int = 0
    tool_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    correction_attempts: int = 0
    capability: str = "unspecified"
    difficulty: str = "unspecified"
    verification_output: str = ""
    verification_runner: str | None = None
    verification_timed_out: bool = False


@dataclass(frozen=True)
class BenchmarkModelRun:
    """Results for one model across all benchmark tasks."""

    model: str
    results: list[BenchmarkTaskResult]


def load_tasks(tasks_dir: str | Path) -> list[BenchmarkTask]:
    """Load benchmark task definitions from YAML files."""

    root = Path(tasks_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Benchmark tasks directory not found: {root}")

    tasks: list[BenchmarkTask] = []
    for path in sorted(root.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Invalid benchmark task file: {path}")

        task_id = str(data.get("id") or data.get("name") or path.stem)
        name = str(data.get("name") or task_id)
        instruction = str(data.get("instruction") or data.get("description") or name)
        repository = str(data.get("repository") or "")
        category = str(data.get("category") or "general")
        max_steps = int(data.get("max_steps", 8))
        success_command = data.get("success_command") or []
        if not isinstance(success_command, list):
            raise ValueError(f"success_command must be a list in {path}")

        allowed_files = data.get("allowed_files") or []
        if not isinstance(allowed_files, list) or any(
            not isinstance(name, str)
            or not name
            or Path(name).is_absolute()
            or ".." in Path(name).parts
            or name == "."
            for name in allowed_files
        ):
            raise ValueError(
                f"allowed_files must contain repository-relative files: {path}"
            )
        grader_directory = None
        if data.get("grader"):
            grader_directory = (path.parent / str(data["grader"])).resolve()
            if not grader_directory.is_dir() or not allowed_files:
                raise ValueError(
                    f"grader requires an existing directory and allowed_files: {path}"
                )

        tasks.append(
            BenchmarkTask(
                task_id=task_id,
                name=name,
                instruction=instruction,
                repository=repository,
                category=category,
                max_steps=max_steps,
                capability=str(data.get("capability", "unspecified")),
                difficulty=str(data.get("difficulty", "unspecified")),
                allowed_files=tuple(allowed_files),
                grader_directory=grader_directory,
                success_command=[str(part) for part in success_command],
            )
        )

    return tasks


def run_benchmark(
    tasks: list[BenchmarkTask],
    run_task: Callable[[BenchmarkTask], AgentResult],
    *,
    verify_command: Callable[[BenchmarkTask], bool] | None = None,
) -> list[BenchmarkTaskResult]:
    """Execute benchmark tasks with a legacy AgentResult callback."""

    results: list[BenchmarkTaskResult] = []
    for task in tasks:
        agent_result = run_task(task)
        command_success = None
        if verify_command is not None and task.success_command:
            command_success = verify_command(task)

        if task.category in {"inspect", "read", "search"}:
            task_success = agent_result.success
        elif command_success is not None:
            task_success = agent_result.success and command_success
        else:
            task_success = agent_result.success

        results.append(
            BenchmarkTaskResult(
                task_id=task.task_id,
                name=task.name,
                repository=task.repository,
                category=task.category,
                agent_success=agent_result.success,
                task_success=task_success,
                agent_response=agent_result.response,
                agent_error=agent_result.error,
                steps=agent_result.steps,
                command_success=command_success,
            )
        )
    return results
