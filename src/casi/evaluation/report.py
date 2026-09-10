"""Evaluation report generation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from casi.evaluation.benchmark import BenchmarkModelRun, BenchmarkTaskResult
from casi.evaluation.metrics import summarize_model_runs, summarize_results


def render_report(
    results: list[BenchmarkTaskResult], *, model: str | None = None
) -> str:
    """Render a human-readable benchmark report."""

    title = f"CASI benchmark report{f' ({model})' if model else ''}"
    lines = [title, "=" * len(title)]
    metrics = summarize_results(results)
    lines.extend(_format_metric_lines(metrics))
    lines.append("")
    lines.extend(_format_task_lines(results))
    return "\n".join(lines)


def render_comparison_report(model_runs: list[BenchmarkModelRun]) -> str:
    """Render a side-by-side comparison across models."""

    lines = ["CASI benchmark comparison", "========================="]
    summary = summarize_model_runs(model_runs)
    for model, metrics in summary.items():
        lines.append("")
        lines.append(f"Model: {model}")
        lines.extend(f"  {line}" for line in _format_metric_lines(metrics))
    return "\n".join(lines)


def render_markdown_report(
    results: list[BenchmarkTaskResult], *, model: str | None = None
) -> str:
    """Render a Markdown benchmark report."""

    metrics = summarize_results(results)
    heading = f"# CASI Benchmark Report{f' — {model}' if model else ''}"
    lines = [
        heading,
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in metrics.items():
        if isinstance(value, float):
            display = f"{value:.2%}" if "rate" in key else f"{value:.2f}"
        else:
            display = str(value)
        lines.append(f"| {key} | {display} |")

    capabilities = summarize_capabilities(results)
    if capabilities:
        lines.extend(
            [
                "",
                "## Capabilities",
                "",
                "| Capability | Passed / total |",
                "| --- | ---: |",
            ]
        )
        for capability, counts in capabilities.items():
            lines.append(f"| {capability} | {counts['passed']} / {counts['tasks']} |")
    lines.extend(["", "## Tasks", ""])
    for result in results:
        status = "pass" if result.task_success else "fail"
        lines.append(
            f"- `{result.task_id}` ({result.category}): **{status}** "
            f"— {result.steps} steps, {result.duration_seconds:.2f}s"
        )
        if result.agent_error:
            lines.append(f"  - error: {result.agent_error}")
    return "\n".join(lines) + "\n"


def summarize_capabilities(
    results: list[BenchmarkTaskResult],
) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for result in results:
        if result.capability == "unspecified":
            continue
        counts = summary.setdefault(result.capability, {"tasks": 0, "passed": 0})
        counts["tasks"] += 1
        counts["passed"] += int(result.task_success)
    return summary


def build_report_payload(
    results: list[BenchmarkTaskResult],
    *,
    model: str | None = None,
) -> dict[str, object]:
    """Return a JSON-serializable benchmark payload."""

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "model": model,
        "metrics": summarize_results(results),
        "by_capability": summarize_capabilities(results),
        "tasks": [_task_to_dict(result) for result in results],
    }


def build_comparison_payload(model_runs: list[BenchmarkModelRun]) -> dict[str, object]:
    """Return a JSON payload comparing multiple model runs."""

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "models": {
            run.model: {
                "metrics": summarize_results(run.results),
                "by_capability": summarize_capabilities(run.results),
                "tasks": [_task_to_dict(result) for result in run.results],
            }
            for run in model_runs
        },
        "comparison": summarize_model_runs(model_runs),
    }


def write_report_files(
    payload: dict[str, object],
    output: Path,
    *,
    markdown: str | None = None,
) -> None:
    """Write JSON and optional Markdown report files."""

    output.parent.mkdir(parents=True, exist_ok=True)
    json_path = output if output.suffix == ".json" else output.with_suffix(".json")
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if markdown is not None:
        md_path = output.with_suffix(".md")
        md_path.write_text(markdown, encoding="utf-8")


def _format_metric_lines(metrics: dict[str, float | int]) -> list[str]:
    lines = [f"Tasks: {metrics['tasks']}"]
    for key, value in metrics.items():
        if key == "tasks":
            continue
        if isinstance(value, float):
            display = f"{value:.2%}" if "rate" in key else f"{value:.2f}"
        else:
            display = str(value)
        lines.append(f"{key.replace('_', ' ')}: {display}")
    return lines


def _format_task_lines(results: list[BenchmarkTaskResult]) -> list[str]:
    lines: list[str] = []
    for result in results:
        status = "ok" if result.task_success else "failed"
        lines.append(
            f"- {result.task_id} [{result.category}]: {status} "
            f"({result.steps} steps, {result.duration_seconds:.2f}s)"
        )
        if result.agent_error:
            lines.append(f"  error: {result.agent_error}")
    return lines


def _task_to_dict(result: BenchmarkTaskResult) -> dict[str, object]:
    return {
        "task_id": result.task_id,
        "name": result.name,
        "repository": result.repository,
        "category": result.category,
        "model": result.model,
        "agent_success": result.agent_success,
        "task_success": result.task_success,
        "command_success": result.command_success,
        "patch_valid": result.patch_valid,
        "patch_applied": result.patch_applied,
        "steps": result.steps,
        "duration_seconds": result.duration_seconds,
        "files_read": result.files_read,
        "tool_calls": result.tool_calls,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "correction_attempts": result.correction_attempts,
        "error": result.agent_error,
        "capability": result.capability,
        "difficulty": result.difficulty,
        "verification_output": result.verification_output,
        "verification_runner": result.verification_runner,
        "verification_timed_out": result.verification_timed_out,
    }
