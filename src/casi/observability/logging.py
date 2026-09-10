"""Structured execution logging."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from typing import IO, TYPE_CHECKING

from casi.observability.metrics import ExecutionMetrics, summarize_trace
from casi.observability.tracing import ExecutionTrace, reconstruct_trace

if TYPE_CHECKING:
    from casi.agent.trace import AgentTraceRecorder


def build_execution_payload(
    execution: ExecutionTrace,
    metrics: ExecutionMetrics,
) -> dict[str, object]:
    """Return a JSON-serializable execution summary."""

    return {
        "schema_version": 2,
        "run_id": execution.run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "execution": {
            "model": execution.model,
            "repository": execution.repository,
            "task": execution.task,
            "started_at": execution.started_at.isoformat()
            if execution.started_at
            else None,
            "finished_at": execution.finished_at.isoformat()
            if execution.finished_at
            else None,
            "files_read": execution.files_read,
            "tools_called": execution.tools_called,
            "patches_proposed": execution.patches_proposed,
            "errors": execution.errors,
            "prompt_tokens": execution.prompt_tokens,
            "completion_tokens": execution.completion_tokens,
            "total_duration_ms": execution.total_duration_ms,
            "steps": [
                {
                    "step": step.step,
                    "decision_kind": step.decision_kind,
                    "tool": step.tool,
                    "duration_ms": step.duration_ms,
                    "success": step.success,
                }
                for step in execution.steps
            ],
            "test_runs": [
                {
                    "tool": run.tool,
                    "passed": run.passed,
                    "runner": run.runner,
                    "exit_code": run.exit_code,
                }
                for run in execution.test_runs
            ],
        },
        "metrics": metrics.to_dict(),
    }


def emit_execution_log(
    recorder: AgentTraceRecorder,
    *,
    stream: IO[str] | None = None,
) -> dict[str, object]:
    """Write one structured JSON log line for an execution."""

    recorder.mark_finished()
    execution = reconstruct_trace(recorder)
    metrics = summarize_trace(execution)
    payload = build_execution_payload(execution, metrics)
    target = stream if stream is not None else sys.stderr
    print(json.dumps(payload, ensure_ascii=False), file=target)
    return payload
