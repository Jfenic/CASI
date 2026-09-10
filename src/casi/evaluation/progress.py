"""Human-readable progress output for benchmark runs."""

from __future__ import annotations

import sys
from typing import TextIO

from casi.evaluation.benchmark import BenchmarkTask, BenchmarkTaskResult


def _preview(text: str, *, max_chars: int = 100) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return f"{compact[: max_chars - 3]}..."


def emit_benchmark_line(message: str, *, stream: TextIO | None = None) -> None:
    target = stream if stream is not None else sys.stderr
    print(message, file=target, flush=True)


def emit_task_start(
    task: BenchmarkTask,
    *,
    index: int,
    total: int,
    model: str,
    stream: TextIO | None = None,
) -> None:
    emit_benchmark_line(
        f"[benchmark] Task {index}/{total}: {task.task_id} — {task.name}",
        stream=stream,
    )
    emit_benchmark_line(
        f"[benchmark]   model={model} repo={task.repository} "
        f"category={task.category} max_steps={task.max_steps}",
        stream=stream,
    )
    emit_benchmark_line(
        f"[benchmark]   instruction: {_preview(task.instruction)}",
        stream=stream,
    )
    emit_benchmark_line("[benchmark]   running agent...", stream=stream)


def emit_task_finish(
    result: BenchmarkTaskResult, *, stream: TextIO | None = None
) -> None:
    status = "PASS" if result.task_success else "FAIL"
    pytest = (
        "ok"
        if result.command_success is True
        else "fail"
        if result.command_success is False
        else "n/a"
    )
    patch = (
        "applied"
        if result.patch_applied
        else "valid"
        if result.patch_valid
        else "invalid"
        if result.patch_valid is False
        else "none"
    )
    line = (
        f"[benchmark]   result: {status} | agent="
        f"{'ok' if result.agent_success else 'fail'}"
        f" | pytest={pytest}"
    )
    if result.category in {"inspect", "read", "search"}:
        line += " (pytest ignored for read-only tasks)"
    line += (
        f" | {result.duration_seconds:.1f}s"
        f" | steps={result.steps} | tools={result.tool_calls}"
        f" | files_read={result.files_read} | patch={patch}"
    )
    emit_benchmark_line(line, stream=stream)
    if result.prompt_tokens or result.completion_tokens:
        emit_benchmark_line(
            f"[benchmark]   tokens: prompt={result.prompt_tokens} "
            f"completion={result.completion_tokens}",
            stream=stream,
        )
    if result.agent_error:
        emit_benchmark_line(
            f"[benchmark]   error: {_preview(result.agent_error, max_chars=200)}",
            stream=stream,
        )
    emit_benchmark_line("", stream=stream)


def emit_model_header(
    model: str, *, task_count: int, stream: TextIO | None = None
) -> None:
    emit_benchmark_line(
        f"[benchmark] Model {model!r} — {task_count} task(s)",
        stream=stream,
    )
    emit_benchmark_line("", stream=stream)
