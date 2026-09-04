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

	def set_live(self, enabled: bool) -> None:
		self.live = enabled

	def clear(self) -> None:
		self.events.clear()
		self.structured_events.clear()
		self.run_id = uuid4().hex

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

		target = Path(path).expanduser().resolve()
		target.parent.mkdir(parents=True, exist_ok=True)
		structured_events = self.structured_events
		if events is not None:
			structured_events = [
				{"kind": "event", "message": message, "data": {}}
				for message in events
			]
		payload = {
			"schema_version": 1,
			"run_id": self.run_id,
			"created_at": datetime.now(UTC).isoformat(),
			"events": structured_events,
		}
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
