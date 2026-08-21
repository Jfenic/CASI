"""Benchmark orchestration utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

from casi.agent.state import AgentResult


@dataclass(frozen=True)
class BenchmarkTask:
	"""Definition for a single benchmark task."""

	task_id: str
	name: str
	instruction: str
	max_steps: int = 8
	success_command: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BenchmarkTaskResult:
	"""Outcome for one benchmark task execution."""

	task_id: str
	agent_success: bool
	agent_response: str = ""
	agent_error: str | None = None
	steps: int = 0
	command_success: bool | None = None


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
		instruction = str(
			data.get("instruction") or data.get("description") or name
		)
		max_steps = int(data.get("max_steps", 8))
		success_command = data.get("success_command") or []
		if not isinstance(success_command, list):
			raise ValueError(f"success_command must be a list in {path}")

		tasks.append(
			BenchmarkTask(
				task_id=task_id,
				name=name,
				instruction=instruction,
				max_steps=max_steps,
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
	"""Execute benchmark tasks and collect structured results."""

	results: list[BenchmarkTaskResult] = []
	for task in tasks:
		agent_result = run_task(task)
		command_success = None
		if verify_command is not None and task.success_command:
			command_success = verify_command(task)

		results.append(
			BenchmarkTaskResult(
				task_id=task.task_id,
				agent_success=agent_result.success,
				agent_response=agent_result.response,
				agent_error=agent_result.error,
				steps=agent_result.steps,
				command_success=command_success,
			)
		)
	return results
