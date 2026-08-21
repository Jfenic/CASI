"""Evaluation report generation."""

from __future__ import annotations

from casi.evaluation.benchmark import BenchmarkTaskResult
from casi.evaluation.metrics import summarize_results


def render_report(results: list[BenchmarkTaskResult]) -> str:
	"""Render a human-readable benchmark report."""

	lines = ["CASI benchmark report", "====================="]
	metrics = summarize_results(results)
	lines.append(f"Tasks: {metrics['tasks']}")
	lines.append(f"Task success rate: {metrics['task_success_rate']:.2%}")
	lines.append(f"Command success rate: {metrics['command_success_rate']:.2%}")
	lines.append(f"Average steps: {metrics['average_steps']:.2f}")
	lines.append("")

	for result in results:
		status = "ok" if result.agent_success else "failed"
		lines.append(f"- {result.task_id}: {status} ({result.steps} steps)")
		if result.agent_error:
			lines.append(f"  error: {result.agent_error}")

	return "\n".join(lines)
