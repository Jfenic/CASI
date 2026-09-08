"""Reconstruct structured execution traces from agent events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from casi.agent.trace import AgentTraceRecorder


@dataclass(frozen=True)
class StepRecord:
	step: int
	decision_kind: str
	tool: str | None = None
	duration_ms: float | None = None
	success: bool | None = None
	output_preview: str | None = None


@dataclass(frozen=True)
class TestRunRecord:
	tool: str
	passed: bool
	runner: str | None = None
	exit_code: int | None = None
	output_preview: str | None = None


@dataclass
class ExecutionTrace:
	run_id: str
	model: str | None = None
	repository: str | None = None
	task: str | None = None
	started_at: datetime | None = None
	finished_at: datetime | None = None
	steps: list[StepRecord] = field(default_factory=list)
	files_read: list[str] = field(default_factory=list)
	tools_called: list[str] = field(default_factory=list)
	patches_proposed: int = 0
	test_runs: list[TestRunRecord] = field(default_factory=list)
	errors: list[str] = field(default_factory=list)
	prompt_tokens: int = 0
	completion_tokens: int = 0
	total_duration_ms: float | None = None

	@property
	def failed_step(self) -> StepRecord | None:
		for step in reversed(self.steps):
			if step.success is False:
				return step
		return None


def reconstruct_trace(recorder: AgentTraceRecorder) -> ExecutionTrace:
	"""Build a structured trace from a recorder and its structured events."""

	trace = ExecutionTrace(
		run_id=recorder.run_id,
		model=recorder.model,
		repository=recorder.repository,
		task=recorder.task,
		started_at=recorder.started_at,
		finished_at=recorder.finished_at,
		prompt_tokens=recorder.prompt_tokens,
		completion_tokens=recorder.completion_tokens,
		total_duration_ms=recorder.total_duration_ms(),
	)
	_apply_events(trace, recorder.structured_events)
	return trace


def reconstruct_from_payload(payload: dict[str, object]) -> ExecutionTrace:
	"""Rebuild a trace from a saved JSON payload."""

	metadata = payload.get("execution")
	if isinstance(metadata, dict):
		trace = ExecutionTrace(
			run_id=str(payload.get("run_id") or ""),
			model=_optional_str(metadata.get("model")),
			repository=_optional_str(metadata.get("repository")),
			task=_optional_str(metadata.get("task")),
			prompt_tokens=_optional_int(metadata.get("prompt_tokens")) or 0,
			completion_tokens=_optional_int(metadata.get("completion_tokens")) or 0,
			total_duration_ms=_optional_float(metadata.get("total_duration_ms")),
			patches_proposed=_optional_int(metadata.get("patches_proposed")) or 0,
			files_read=_string_list(metadata.get("files_read")),
			tools_called=_string_list(metadata.get("tools_called")),
			errors=_string_list(metadata.get("errors")),
		)
	else:
		trace = ExecutionTrace(run_id=str(payload.get("run_id") or ""))

	events = payload.get("events")
	if isinstance(events, list):
		_apply_events(trace, [event for event in events if isinstance(event, dict)])
	return trace


def _apply_events(trace: ExecutionTrace, events: list[dict[str, object]]) -> None:
	pending_tool: str | None = None
	pending_step = 0
	seen_files: set[str] = set(trace.files_read)
	seen_tools: set[str] = set(trace.tools_called)

	for event in events:
		kind = str(event.get("kind") or "event")
		message = str(event.get("message") or "")
		data = event.get("data")
		if not isinstance(data, dict):
			data = {}

		if kind == "step_timing":
			step = _optional_int(data.get("step")) or pending_step
			trace.steps.append(
				StepRecord(
					step=step,
					decision_kind=str(data.get("decision_kind") or "unknown"),
					duration_ms=_optional_float(data.get("duration_ms")),
				)
			)
			continue

		if kind == "decision":
			pending_step = _optional_int(data.get("step")) or pending_step
			trace.steps.append(
				StepRecord(
					step=pending_step,
					decision_kind=str(data.get("decision_kind") or "decision"),
				)
			)
			continue

		if kind == "tool_call":
			pending_step = _optional_int(data.get("step")) or pending_step
			tool = str(data.get("tool") or "unknown")
			pending_tool = tool
			if tool not in seen_tools:
				seen_tools.add(tool)
				trace.tools_called.append(tool)
			if tool == "propose_file":
				trace.patches_proposed += 1
			continue

		if kind == "tool_result":
			tool = str(data.get("tool") or pending_tool or "unknown")
			success = bool(data.get("success", True))
			path = _optional_str(data.get("path"))
			if tool == "read_file" and path and path not in seen_files:
				seen_files.add(path)
				trace.files_read.append(path)
			if tool == "run_tests":
				trace.test_runs.append(
					TestRunRecord(
						tool=tool,
						passed=success,
						runner=_optional_str(data.get("runner")),
						exit_code=_optional_int(data.get("exit_code")),
						output_preview=_preview(message),
					)
				)
			trace.steps.append(
				StepRecord(
					step=pending_step,
					decision_kind="tool_result",
					tool=tool,
					success=success,
					output_preview=_preview(message),
				)
			)
			if not success:
				trace.errors.append(message)
			continue

		if kind == "final":
			trace.steps.append(
				StepRecord(
					step=_optional_int(data.get("step")) or pending_step,
					decision_kind="final",
					output_preview=_preview(message),
				)
			)


def _preview(message: str) -> str | None:
	compact = " ".join(message.split())
	if not compact:
		return None
	if len(compact) <= 160:
		return compact
	return f"{compact[:157]}..."


def _optional_str(value: object) -> str | None:
	return value if isinstance(value, str) and value else None


def _optional_int(value: object) -> int | None:
	if isinstance(value, bool):
		return None
	if isinstance(value, int):
		return value
	return None


def _optional_float(value: object) -> float | None:
	if isinstance(value, (int, float)) and not isinstance(value, bool):
		return float(value)
	return None


def _string_list(value: object) -> list[str]:
	if not isinstance(value, list):
		return []
	return [item for item in value if isinstance(item, str)]
