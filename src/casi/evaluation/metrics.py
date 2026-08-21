"""Benchmark metrics helpers."""

from __future__ import annotations

from casi.evaluation.benchmark import BenchmarkTaskResult


def task_success_rate(results: list[BenchmarkTaskResult]) -> float:
	"""Return the fraction of tasks where the agent completed successfully."""

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


def average_steps(results: list[BenchmarkTaskResult]) -> float:
	"""Return the average number of agent steps across benchmark tasks."""

	if not results:
		return 0.0
	return sum(result.steps for result in results) / len(results)


def summarize_results(results: list[BenchmarkTaskResult]) -> dict[str, float | int]:
	"""Return a compact metrics dictionary for a benchmark run."""

	return {
		"tasks": len(results),
		"task_success_rate": task_success_rate(results),
		"command_success_rate": command_success_rate(results),
		"average_steps": average_steps(results),
	}
