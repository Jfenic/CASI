"""Lightweight execution trace for debugging agent decisions."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def _preview(text: str, *, max_chars: int = 120) -> str:
	compact = " ".join(text.split())
	if len(compact) <= max_chars:
		return compact
	return f"{compact[: max_chars - 3]}..."


def _format_args(arguments: dict[str, object]) -> str:
	if not arguments:
		return ""
	parts: list[str] = []
	for key, value in arguments.items():
		lowered = key.lower()
		if any(marker in lowered for marker in ("password", "secret", "token", "key")):
			formatted = "<redacted>"
		elif isinstance(value, str):
			formatted = repr(_preview(value, max_chars=160))
		else:
			formatted = repr(value)
		parts.append(f"{key}={formatted}")
	return " " + ", ".join(parts)


class AgentTraceRecorder:
	"""Collect human-readable step events for one agent run."""

	def __init__(
		self,
		*,
		on_event: Callable[[str], None] | None = None,
		live: bool = False,
	) -> None:
		self.events: list[str] = []
		self.structured_events: list[dict[str, object]] = []
		self.run_id = uuid4().hex
		self.on_event = on_event
		self.live = live
		self.model: str | None = None
		self.repository: str | None = None
		self.task: str | None = None
		self.started_at: datetime | None = None
		self.finished_at: datetime | None = None
		self.prompt_tokens = 0
		self.completion_tokens = 0

	def set_context(
		self,
		*,
		model: str | None = None,
		repository: str | None = None,
		task: str | None = None,
	) -> None:
		if model is not None:
			self.model = model
		if repository is not None:
			self.repository = repository
		if task is not None:
			self.task = task

	def mark_started(self) -> None:
		if self.started_at is None:
			self.started_at = datetime.now(UTC)

	def mark_finished(self) -> None:
		self.finished_at = datetime.now(UTC)

	def set_live(self, enabled: bool) -> None:
		self.live = enabled

	def clear(self) -> None:
		self.events.clear()
		self.structured_events.clear()
		self.run_id = uuid4().hex
		self.started_at = None
		self.finished_at = None
		self.prompt_tokens = 0
		self.completion_tokens = 0

	def record(
		self,
		message: str,
		*,
		kind: str = "event",
		data: dict[str, object] | None = None,
	) -> None:
		self.events.append(message)
		self.structured_events.append(
			{
				"timestamp": datetime.now(UTC).isoformat(),
				"kind": kind,
				"message": message,
				"data": data or {},
			}
		)
		if self.live and self.on_event is not None:
			self.on_event(message)

	def record_decision(self, step: int, step_limit: int, kind: str, detail: str = "") -> None:
		suffix = f": {detail}" if detail else ""
		self.record(
			f"decision {step}/{step_limit}: {kind}{suffix}",
			kind="decision",
			data={"step": step, "step_limit": step_limit, "decision_kind": kind},
		)

	def record_tool_call(
		self,
		step: int,
		step_limit: int,
		tool_name: str,
		arguments: dict[str, object],
	) -> None:
		self.record(
			f"decision {step}/{step_limit}: tool {tool_name}{_format_args(arguments)}",
			kind="tool_call",
			data={"step": step, "step_limit": step_limit, "tool": tool_name},
		)

	def record_tool_result(
		self,
		tool_name: str,
		*,
		success: bool,
		output: str,
		metadata: dict[str, object] | None = None,
	) -> None:
		status = "ok" if success else "failed"
		details = ""
		if metadata:
			selected = {
				key: metadata[key]
				for key in ("runner", "exit_code", "timed_out", "path")
				if key in metadata
			}
			if selected:
				details = f" {selected}"
		self.record(
			f"  -> {tool_name} {status}{details}: {_preview(output)}",
			kind="tool_result",
			data={"tool": tool_name, "success": success, **(metadata or {})},
		)

	def record_usage(self, *, prompt_tokens: int | None, completion_tokens: int | None) -> None:
		if prompt_tokens is not None:
			self.prompt_tokens += max(prompt_tokens, 0)
		if completion_tokens is not None:
			self.completion_tokens += max(completion_tokens, 0)
		if prompt_tokens is None and completion_tokens is None:
			return
		self.record(
			f"usage prompt={prompt_tokens or 0} completion={completion_tokens or 0}",
			kind="usage",
			data={
				"prompt_tokens": prompt_tokens,
				"completion_tokens": completion_tokens,
			},
		)

	def record_step_timing(
		self,
		step: int,
		step_limit: int,
		decision_kind: str,
		duration_ms: float,
	) -> None:
		self.record(
			f"timing {step}/{step_limit}: {decision_kind} {duration_ms:.1f}ms",
			kind="step_timing",
			data={
				"step": step,
				"step_limit": step_limit,
				"decision_kind": decision_kind,
				"duration_ms": round(duration_ms, 2),
			},
		)

	def total_duration_ms(self) -> float | None:
		if self.started_at is None or self.finished_at is None:
			return None
		return (self.finished_at - self.started_at).total_seconds() * 1000

	def record_nudge(self, reason: str) -> None:
		self.record(f"  -> nudge: {reason}", kind="nudge")

	def record_final_preview(self, step: int, step_limit: int, content: str) -> None:
		self.record(
			f"decision {step}/{step_limit}: final {_preview(content)}",
			kind="final",
			data={"step": step, "step_limit": step_limit},
		)

	def save(self, path: str | Path, *, events: list[str] | None = None) -> Path:
		"""Save a structured diagnostic snapshot to an explicitly requested path."""

		from casi.observability.logging import build_execution_payload
		from casi.observability.metrics import summarize_trace
		from casi.observability.tracing import reconstruct_trace

		target = Path(path).expanduser().resolve()
		target.parent.mkdir(parents=True, exist_ok=True)
		structured_events = self.structured_events
		if events is not None:
			structured_events = [
				{
					"timestamp": datetime.now(UTC).isoformat(),
					"kind": "event",
					"message": message,
					"data": {},
				}
				for message in events
			]
		execution = reconstruct_trace(self)
		metrics = summarize_trace(execution)
		payload = build_execution_payload(execution, metrics)
		payload["events"] = structured_events
		target.write_text(
			json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
			encoding="utf-8",
		)
		return target

	def format_summary(self, *, title: str = "Agent trace") -> list[str]:
		if not self.events:
			return [f"{title}: (no events recorded)"]
		lines = [f"{title} ({len(self.events)} events):"]
		lines.extend(f"  {event}" for event in self.events)
		return lines
