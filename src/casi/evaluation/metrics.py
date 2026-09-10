"""Benchmark metrics helpers."""

from __future__ import annotations

from casi.evaluation.benchmark import BenchmarkModelRun, BenchmarkTaskResult


def task_success_rate(results: list[BenchmarkTaskResult]) -> float:
    """Return the fraction of tasks that fully succeeded."""

    if not results:
        return 0.0
    successes = sum(1 for result in results if result.task_success)
    return successes / len(results)


def agent_success_rate(results: list[BenchmarkTaskResult]) -> float:
    """Return the fraction of tasks where the agent completed without error."""

    if not results:
        return 0.0
    successes = sum(1 for result in results if result.agent_success)
    return successes / len(results)


def command_success_rate(results: list[BenchmarkTaskResult]) -> float:
    """Return the fraction of tasks whose verification command passed."""

    verified = [result for result in results if result.command_success is not None]
    if not verified:
        return 0.0
    successes = sum(1 for result in verified if result.command_success)
    return successes / len(verified)


def patch_validity_rate(results: list[BenchmarkTaskResult]) -> float:
    """Return the fraction of patch tasks that produced a valid diff."""

    patch_tasks = [result for result in results if result.patch_valid is not None]
    if not patch_tasks:
        return 0.0
    valid = sum(1 for result in patch_tasks if result.patch_valid)
    return valid / len(patch_tasks)


def average_steps(results: list[BenchmarkTaskResult]) -> float:
    if not results:
        return 0.0
    return sum(result.steps for result in results) / len(results)


def average_duration_seconds(results: list[BenchmarkTaskResult]) -> float:
    if not results:
        return 0.0
    return sum(result.duration_seconds for result in results) / len(results)


def average_files_read(results: list[BenchmarkTaskResult]) -> float:
    if not results:
        return 0.0
    return sum(result.files_read for result in results) / len(results)


def average_correction_attempts(results: list[BenchmarkTaskResult]) -> float:
    if not results:
        return 0.0
    return sum(result.correction_attempts for result in results) / len(results)


def summarize_results(results: list[BenchmarkTaskResult]) -> dict[str, float | int]:
    """Return aggregate metrics for one benchmark run."""

    return {
        "tasks": len(results),
        "task_success_rate": task_success_rate(results),
        "agent_success_rate": agent_success_rate(results),
        "command_success_rate": command_success_rate(results),
        "patch_validity_rate": patch_validity_rate(results),
        "average_steps": average_steps(results),
        "average_duration_seconds": average_duration_seconds(results),
        "average_files_read": average_files_read(results),
        "average_correction_attempts": average_correction_attempts(results),
        "total_prompt_tokens": sum(result.prompt_tokens for result in results),
        "total_completion_tokens": sum(result.completion_tokens for result in results),
    }


def summarize_model_runs(
    model_runs: list[BenchmarkModelRun],
) -> dict[str, dict[str, float | int]]:
    """Return metrics keyed by model name."""

    return {run.model: summarize_results(run.results) for run in model_runs}
