"""Execute benchmark tasks against local repositories and models."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from casi.agent.orchestrator import AgentOrchestrator
from casi.agent.run_outcome import resolve_agent_run_outcome
from casi.agent.trace import AgentTraceRecorder
from casi.evaluation.benchmark import BenchmarkModelRun, BenchmarkTask, BenchmarkTaskResult
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
	subprocess.run(["git", "add", "-A"], cwd=repository, check=True, capture_output=True)
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
		return {name for name in names if name in {".git", "__pycache__", ".pytest_cache"}}

	shutil.copytree(source, destination, ignore=ignore)
	prepare_repository(destination)


def run_success_command(task: BenchmarkTask, repository: Path) -> bool:
	"""Run a task's verification command inside the repository."""

	if not task.success_command:
		return True

	result = subprocess.run(
		task.success_command,
		cwd=repository,
		capture_output=True,
		text=True,
		check=False,
	)
	return result.returncode == 0


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
		orchestrator = AgentOrchestrator(
			client,
			repository,
			max_steps=task.max_steps,
			routing_mode=opts.routing,
			require_tool_confirmation=lambda _tool, _args: True,
			approve_segment=lambda _segment: True,
			trace=trace,
		)
		result = orchestrator.run(task.instruction)
		duration_seconds = time.perf_counter() - started

		outcome = resolve_agent_run_outcome(repository, result)
		patch_applied = False
		patch_valid = outcome.patch_valid if outcome.patch is not None else None
		agent_success = result.success
		agent_error = result.error

		if (
			opts.auto_apply_patches
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
		command_success = (
			run_success_command(task, repository) if task.success_command else None
		)
		task_success = agent_success
		if command_success is not None:
			task_success = agent_success and command_success

		correction_attempts = 0
		if result.patch_verification is not None:
			correction_attempts = result.patch_verification.correction_attempts

		return BenchmarkTaskResult(
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
		)


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

	results = [
		run_task(task, repositories_root=options.repositories_root, client=client, options=options)
		for task in tasks
	]
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
