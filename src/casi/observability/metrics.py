"""Aggregate metrics derived from execution traces."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from casi.observability.tracing import ExecutionTrace


@dataclass(frozen=True)
class ExecutionMetrics:
    total_steps: int
    decision_steps: int
    tool_calls: int
    files_read: int
    patches_proposed: int
    test_runs: int
    failed_tools: int
    prompt_tokens: int
    completion_tokens: int
    total_duration_ms: float | None
    step_duration_ms: float | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def summarize_trace(trace: ExecutionTrace) -> ExecutionMetrics:
    """Compute aggregate metrics for one execution."""

    tool_calls = len(trace.tools_called)
    failed_tools = sum(1 for step in trace.steps if step.success is False)
    decision_steps = sum(
        1 for step in trace.steps if step.decision_kind not in {"tool_result", "final"}
    )
    step_durations = [
        step.duration_ms for step in trace.steps if step.duration_ms is not None
    ]
    step_duration_ms = (
        sum(step_durations) / len(step_durations) if step_durations else None
    )
    return ExecutionMetrics(
        total_steps=len(trace.steps),
        decision_steps=decision_steps,
        tool_calls=tool_calls,
        files_read=len(trace.files_read),
        patches_proposed=trace.patches_proposed,
        test_runs=len(trace.test_runs),
        failed_tools=failed_tools,
        prompt_tokens=trace.prompt_tokens,
        completion_tokens=trace.completion_tokens,
        total_duration_ms=trace.total_duration_ms,
        step_duration_ms=step_duration_ms,
    )
