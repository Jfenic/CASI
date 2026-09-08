"""Tools for running the repository's test suite."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from casi.config import settings
from casi.agent.failure_classification import (
	classify_test_result,
	failure_kind_label,
)
from casi.sandbox.test_execution import TestExecutionError, run_repository_tests
from casi.tools.base import Tool, ToolArgumentSpec
from casi.tools.result import ToolResult


class RunTestsTool(Tool):
	name = "run_tests"
	description = (
		"Run the repository test suite using the detected project test command."
	)

	def __init__(self, repository_path: str | Path) -> None:
		self.repository_path = repository_path

	@property
	def argument_schema(self) -> dict[str, ToolArgumentSpec]:
		return {
			"timeout_seconds": ToolArgumentSpec(
				"timeout_seconds",
				(int, float),
				required=False,
				default=settings.test_timeout_seconds,
				minimum=1,
			),
		}

	def run(self, arguments: dict[str, Any]) -> ToolResult:
		try:
			result, runner_kind = run_repository_tests(
				self.repository_path,
				timeout_seconds=arguments["timeout_seconds"],
			)
		except TestExecutionError as exc:
			return ToolResult(
				success=False,
				output="",
				error=str(exc),
				metadata={
					"failure_kind": exc.failure_kind.value,
					"runner": "docker",
				},
			)
		output = result.stdout
		if result.stderr:
			output = f"{output}\n{result.stderr}".strip()
		failure_kind = None
		if result.exit_code != 0 or result.timed_out:
			failure_kind = classify_test_result(result, runner_kind)
		return ToolResult(
			success=result.exit_code == 0 and not result.timed_out,
			output=output,
			error=(
				f"Test command timed out ({failure_kind_label(failure_kind)})"
				if result.timed_out and failure_kind is not None
				else ("Test command timed out" if result.timed_out else None)
			),
			metadata={
				"command": result.command,
				"exit_code": result.exit_code,
				"duration_seconds": result.duration_seconds,
				"timed_out": result.timed_out,
				"runner": runner_kind,
				"failure_kind": failure_kind.value if failure_kind else None,
			},
		)
