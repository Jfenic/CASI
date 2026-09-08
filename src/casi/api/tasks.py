"""In-memory task lifecycle for the HTTP API."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from casi.agent.orchestrator import AgentOrchestrator, OrchestratorResult
from casi.agent.run_outcome import resolve_agent_run_outcome
from casi.agent.trace import AgentTraceRecorder
from casi.llm.ollama_client import OllamaClient
from casi.observability.logging import build_execution_payload
from casi.observability.metrics import summarize_trace
from casi.observability.tracing import reconstruct_trace
from casi.patching.applier import PatchApplicationError, apply_patch
from casi.repository.security import resolve_repository


class TaskStatus(str, Enum):
	PENDING = "pending"
	RUNNING = "running"
	PATCH_PROPOSED = "patch_proposed"
	AWAITING_APPROVAL = "awaiting_approval"
	COMPLETED = "completed"
	FAILED = "failed"
	CANCELLED = "cancelled"


OrchestratorRunner = Callable[
	[Path, str, int | None, str, AgentTraceRecorder | None],
	OrchestratorResult,
]


@dataclass
class TaskRecord:
	id: str
	repository: str
	task: str
	status: TaskStatus
	created_at: datetime
	updated_at: datetime
	routing: str = "assist"
	max_steps: int | None = None
	response: str = ""
	error: str | None = None
	clarification: str | None = None
	patch: str | None = None
	patch_files: list[str] = field(default_factory=list)
	patch_error: str | None = None
	tests_passed: bool | None = None
	test_output: str | None = None
	test_runner: str | None = None
	applied_files: list[str] = field(default_factory=list)
	plan: list[str] = field(default_factory=list)
	trace: list[str] = field(default_factory=list)
	metrics: dict[str, object] = field(default_factory=dict)
	execution: dict[str, object] = field(default_factory=dict)


def default_orchestrator_runner(
	repository: Path,
	task: str,
	max_steps: int | None,
	routing: str,
	trace: AgentTraceRecorder | None = None,
) -> OrchestratorResult:
	orchestrator = AgentOrchestrator(
		OllamaClient(),
		repository,
		max_steps=max_steps,
		routing_mode=routing,
		require_tool_confirmation=lambda _tool, _args: True,
		approve_segment=lambda _segment: True,
		trace=trace,
	)
	return orchestrator.run(task)


class TaskStore:
	"""Track agent tasks and run them in background threads."""

	def __init__(
		self,
		*,
		runner: OrchestratorRunner | None = None,
	) -> None:
		self._runner = runner or default_orchestrator_runner
		self._tasks: dict[str, TaskRecord] = {}
		self._lock = threading.Lock()

	def create(
		self,
		repository: str | Path,
		task: str,
		*,
		routing: str = "assist",
		max_steps: int | None = None,
	) -> TaskRecord:
		root = resolve_repository(repository)
		now = datetime.now(tz=UTC)
		record = TaskRecord(
			id=uuid.uuid4().hex,
			repository=str(root),
			task=task,
			status=TaskStatus.PENDING,
			created_at=now,
			updated_at=now,
			routing=routing,
			max_steps=max_steps,
		)
		with self._lock:
			self._tasks[record.id] = record

		thread = threading.Thread(
			target=self._execute,
			args=(record.id,),
			name=f"casi-task-{record.id[:8]}",
			daemon=True,
		)
		thread.start()
		return record

	def get(self, task_id: str) -> TaskRecord | None:
		with self._lock:
			record = self._tasks.get(task_id)
			if record is None:
				return None
			return _copy_record(record)

	def approve(self, task_id: str) -> TaskRecord:
		with self._lock:
			record = self._tasks.get(task_id)
			if record is None:
				raise KeyError(task_id)
			if record.status is not TaskStatus.AWAITING_APPROVAL:
				raise TaskStateError(
					f"Task {task_id} is {record.status.value}; approval requires awaiting_approval."
				)
			if record.patch is None:
				raise TaskStateError(f"Task {task_id} has no patch to apply.")

			try:
				files = apply_patch(
					record.repository,
					record.patch,
					approved=True,
					dry_run=False,
				)
			except PatchApplicationError as exc:
				record.status = TaskStatus.FAILED
				record.error = str(exc)
				record.updated_at = datetime.now(tz=UTC)
				return _copy_record(record)

			record.status = TaskStatus.COMPLETED
			record.applied_files = list(files)
			record.updated_at = datetime.now(tz=UTC)
			return _copy_record(record)

	def reject(self, task_id: str) -> TaskRecord:
		with self._lock:
			record = self._tasks.get(task_id)
			if record is None:
				raise KeyError(task_id)
			if record.status is not TaskStatus.AWAITING_APPROVAL:
				raise TaskStateError(
					f"Task {task_id} is {record.status.value}; rejection requires awaiting_approval."
				)
			record.status = TaskStatus.CANCELLED
			record.updated_at = datetime.now(tz=UTC)
			return _copy_record(record)

	def _execute(self, task_id: str) -> None:
		with self._lock:
			record = self._tasks.get(task_id)
			if record is None:
				return
			record.status = TaskStatus.RUNNING
			record.updated_at = datetime.now(tz=UTC)

		try:
			trace = AgentTraceRecorder()
			trace.set_context(repository=record.repository, task=record.task)
			result = self._runner(
				Path(record.repository),
				record.task,
				record.max_steps,
				record.routing,
				trace,
			)
		except Exception as exc:  # noqa: BLE001 - surface unexpected failures to clients
			with self._lock:
				record = self._tasks[task_id]
				record.status = TaskStatus.FAILED
				record.error = str(exc)
				record.updated_at = datetime.now(tz=UTC)
			return

		outcome = resolve_agent_run_outcome(record.repository, result)
		trace.mark_finished()
		execution = reconstruct_trace(trace)
		metrics = summarize_trace(execution)
		payload = build_execution_payload(execution, metrics)
		with self._lock:
			record = self._tasks[task_id]
			record.response = outcome.response
			record.error = outcome.error
			record.clarification = outcome.clarification
			record.plan = list(outcome.plan)
			record.trace = list(trace.events) or list(outcome.trace)
			record.metrics = dict(metrics.to_dict())
			execution_payload = payload.get("execution")
			record.execution = (
				dict(execution_payload) if isinstance(execution_payload, dict) else {}
			)
			record.patch = outcome.patch
			record.patch_files = list(outcome.patch_files)
			record.patch_error = outcome.patch_error
			record.tests_passed = outcome.tests_passed
			record.test_output = outcome.test_output
			record.test_runner = outcome.test_runner
			record.updated_at = datetime.now(tz=UTC)

			if not outcome.success:
				record.status = TaskStatus.FAILED
				return

			if outcome.clarification is not None:
				record.status = TaskStatus.FAILED
				record.error = outcome.clarification
				return

			if outcome.patch is None:
				record.status = TaskStatus.COMPLETED
				return

			record.status = TaskStatus.PATCH_PROPOSED
			if not outcome.patch_valid:
				record.status = TaskStatus.FAILED
				record.error = outcome.patch_error or "Patch validation failed."
				return

			if outcome.tests_passed is False:
				record.status = TaskStatus.FAILED
				record.error = "Patch sandbox tests failed."
				return

			record.status = TaskStatus.AWAITING_APPROVAL


class TaskStateError(ValueError):
	"""Raised when an action is invalid for the current task status."""


def _copy_record(record: TaskRecord) -> TaskRecord:
	return TaskRecord(
		id=record.id,
		repository=record.repository,
		task=record.task,
		status=record.status,
		created_at=record.created_at,
		updated_at=record.updated_at,
		routing=record.routing,
		max_steps=record.max_steps,
		response=record.response,
		error=record.error,
		clarification=record.clarification,
		patch=record.patch,
		patch_files=list(record.patch_files),
		patch_error=record.patch_error,
		tests_passed=record.tests_passed,
		test_output=record.test_output,
		test_runner=record.test_runner,
		applied_files=list(record.applied_files),
		plan=list(record.plan),
		trace=list(record.trace),
		metrics=dict(record.metrics),
		execution=dict(record.execution),
	)
