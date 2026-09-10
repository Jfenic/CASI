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
        runner = LocalRunner(
            max_output_chars=settings.max_command_output_chars,
        )
        root_result = runner.run(
            self.repository_path,
            ["git", "rev-parse", "--show-toplevel"],
            timeout_seconds=settings.git_timeout_seconds,
        )
        requested_root = Path(self.repository_path).resolve()
        discovered_root = (
            Path(root_result.stdout.strip()).resolve()
            if root_result.exit_code == 0 and root_result.stdout.strip()
            else None
        )
        if root_result.timed_out:
            return ToolResult(
                success=False,
                output=root_result.stdout,
                error="Git repository check timed out",
                metadata={"command": root_result.command, "timed_out": True},
            )
        if root_result.exit_code != 0 or discovered_root != requested_root:
            return ToolResult(
                success=False,
                output=root_result.stdout,
                error=(
                    root_result.stderr or f"Not a Git repository root: {requested_root}"
                ),
                metadata={
                    "command": root_result.command,
                    "exit_code": root_result.exit_code or 128,
                },
            )

        command = ["git", "diff", "--no-ext-diff", "--unified=3"]
        if arguments["staged"]:
            command.append("--cached")

        result = runner.run(
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
