"""Tools for running the repository's test suite."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from casi.config import settings
from casi.sandbox.test_execution import run_repository_pytest
from casi.tools.base import Tool, ToolArgumentSpec
from casi.tools.result import ToolResult


class RunTestsTool(Tool):
	name = "run_tests"
	description = "Run the repository test suite with Python pytest."

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
		result, runner_kind = run_repository_pytest(
			self.repository_path,
			timeout_seconds=arguments["timeout_seconds"],
		)
		output = result.stdout
		if result.stderr:
			output = f"{output}\n{result.stderr}".strip()
		return ToolResult(
			success=result.exit_code == 0 and not result.timed_out,
			output=output,
			error="Test command timed out" if result.timed_out else None,
			metadata={
				"command": result.command,
				"exit_code": result.exit_code,
				"duration_seconds": result.duration_seconds,
				"timed_out": result.timed_out,
				"runner": runner_kind,
			},
		)
