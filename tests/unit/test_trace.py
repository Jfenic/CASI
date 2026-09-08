from __future__ import annotations

import json
from pathlib import Path

from casi.agent.factory import AgentFactory
from casi.agent.intent import TaskIntent
from casi.agent.trace import AgentTraceRecorder
from casi.llm.base import LLMResponse, ToolDefinition


class ToolThenStallClient:
	def __init__(self) -> None:
		self._count = 0
		self.responses = [
			LLMResponse.tool_call("read_file", {"path": "app.py"}),
			LLMResponse.final("Still thinking, no patch yet."),
		]

	def complete(self, messages, tools: list[ToolDefinition]) -> LLMResponse:
		index = min(self._count, len(self.responses) - 1)
		self._count += 1
		return self.responses[index]


def test_agent_loop_records_trace_and_includes_it_on_step_limit(tmp_path: Path) -> None:
	(tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
	trace = AgentTraceRecorder()
	agent = AgentFactory.create(
		TaskIntent.INSPECT,
		client=ToolThenStallClient(),
		repository=tmp_path,
		max_steps=1,
		routing_mode="off",
		trace=trace,
	)

	result = agent.run("explain app.py")

	assert result.success is False
	assert "maximum of 1 steps" in (result.error or "")
	assert result.trace
	assert any("tool read_file" in event for event in result.trace)
	assert any("read_file ok" in event for event in result.trace)


def test_trace_redacts_sensitive_arguments_and_saves_json(tmp_path: Path) -> None:
	trace = AgentTraceRecorder()
	trace.record_tool_call(
		1,
		4,
		"propose_file",
		{"path": "app.py", "content": "x" * 500, "api_token": "secret-value"},
	)
	trace.record_tool_result(
		"run_tests",
		success=False,
		output="failed assertion",
		metadata={"runner": "docker", "exit_code": 1},
	)

	target = trace.save(tmp_path / "trace.json")
	payload = json.loads(target.read_text(encoding="utf-8"))

	assert payload["schema_version"] == 2
	assert payload["run_id"]
	assert len(payload["events"]) == 2
	assert "metrics" in payload
	assert "execution" in payload
	assert "secret-value" not in trace.events[0]
	assert "<redacted>" in trace.events[0]
	assert len(trace.events[0]) < 300
	assert "'runner': 'docker'" in trace.events[1]


def test_trace_records_rejected_fix_tool_calls(tmp_path: Path) -> None:
	(tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
	(tmp_path / "test_app.py").write_text(
		"from app import x\n\ndef test_x():\n    assert x == 2\n",
		encoding="utf-8",
	)
	trace = AgentTraceRecorder()
	client = ToolThenStallClient()
	client.responses = [
		LLMResponse.tool_call("run_tests", {}),
		LLMResponse.tool_call("search_code", {"query": "x"}),
		LLMResponse.final("No patch"),
	]
	agent = AgentFactory.create(
		TaskIntent.UNKNOWN,
		client=client,
		repository=tmp_path,
		max_steps=4,
		max_correction_attempts=0,
		require_tool_confirmation=lambda *_args: True,
		trace=trace,
		routing_mode="off",
	)

	agent.run("fix app.py")

	assert any("tool search_code" in event for event in trace.events)
	assert any(
		"Tool unavailable in this phase" in event
		or "search_code results are already available" in event
		for event in trace.events
	)
