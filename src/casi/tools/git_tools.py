"""Read-only Git workflow tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from casi.config import settings
from casi.sandbox.local_runner import LocalRunner
from casi.tools.base import Tool, ToolArgumentSpec
from casi.tools.result import ToolResult


class GitDiffTool(Tool):
	"""Return the working-tree or staged Git diff for a repository."""

	name = "git_diff"
	description = "Show repository changes without modifying files."

	def __init__(self, repository_path: str | Path) -> None:
		self.repository_path = repository_path

	@property
	def argument_schema(self) -> dict[str, ToolArgumentSpec]:
		return {
			"staged": ToolArgumentSpec("staged", bool, required=False, default=False),
		}

	def run(self, arguments: dict[str, Any]) -> ToolResult:
		command = ["git", "diff", "--no-ext-diff", "--unified=3"]
		if arguments["staged"]:
			command.append("--cached")

		result = LocalRunner(
			max_output_chars=settings.max_command_output_chars,
		).run(
			self.repository_path,
			command,
			timeout_seconds=settings.git_timeout_seconds,
		)

		if result.timed_out:
			return ToolResult(
				success=False,
				output=result.stdout,
				error="Git diff command timed out",
				metadata={"command": result.command, "timed_out": True},
			)
		if result.exit_code != 0:
			return ToolResult(
				success=False,
				output=result.stdout,
				error=result.stderr or "Git diff failed",
				metadata={"command": result.command, "exit_code": result.exit_code},
			)

		return ToolResult(
			success=True,
			output=result.stdout,
			metadata={
				"command": result.command,
				"staged": arguments["staged"],
				"changed": bool(result.stdout.strip()),
			},
		)
