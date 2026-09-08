from __future__ import annotations

import json

from casi.agent.trace import AgentTraceRecorder
from casi.observability.logging import build_execution_payload, emit_execution_log
from casi.observability.metrics import summarize_trace
from casi.observability.tracing import reconstruct_trace


def test_reconstruct_trace_collects_tools_files_and_timing() -> None:
	recorder = AgentTraceRecorder()
	recorder.set_context(model="demo-model", repository="/tmp/repo", task="fix tests")
	recorder.mark_started()
	recorder.record_step_timing(1, 4, "tool_call", 120.5)
	recorder.record_tool_call(1, 4, "read_file", {"path": "app.py"})
	recorder.record_tool_result(
		"read_file",
		success=True,
		output="1: value = 1",
		metadata={"path": "app.py"},
	)
	recorder.record_tool_call(2, 4, "run_tests", {})
	recorder.record_tool_result(
		"run_tests",
		success=False,
		output="AssertionError",
		metadata={"runner": "docker", "exit_code": 1},
	)
	recorder.record_usage(prompt_tokens=100, completion_tokens=25)
	recorder.mark_finished()

	execution = reconstruct_trace(recorder)
	metrics = summarize_trace(execution)

	assert execution.model == "demo-model"
	assert execution.files_read == ["app.py"]
	assert execution.tools_called == ["read_file", "run_tests"]
	assert execution.test_runs[0].passed is False
	assert execution.prompt_tokens == 100
	assert execution.completion_tokens == 25
	assert metrics.tool_calls == 2
	assert metrics.failed_tools == 1
	assert metrics.total_duration_ms is not None


def test_build_execution_payload_is_json_serializable() -> None:
	recorder = AgentTraceRecorder()
	recorder.record_decision(1, 2, "final")
	recorder.mark_finished()
	execution = reconstruct_trace(recorder)
	metrics = summarize_trace(execution)
	payload = build_execution_payload(execution, metrics)

	encoded = json.dumps(payload)
	decoded = json.loads(encoded)

	assert decoded["schema_version"] == 2
	assert decoded["metrics"]["total_steps"] >= 1


def test_emit_execution_log_writes_json_line(capsys) -> None:
	recorder = AgentTraceRecorder()
	recorder.record_decision(1, 1, "final")

	emit_execution_log(recorder)

	line = capsys.readouterr().err.strip()
	payload = json.loads(line)
	assert payload["run_id"] == recorder.run_id
	assert "metrics" in payload
