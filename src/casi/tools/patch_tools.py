"""Structured tools for validating and applying proposed patches."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from casi.patching.validator import validate_patch
from casi.patching.applier import PatchApplicationError, apply_patch
from casi.tools.base import Tool, ToolArgumentSpec
from casi.tools.result import ToolResult


class ProposeFileTool(Tool):
	"""Build a correct unified diff from a complete replacement file."""

	name = "propose_file"
	description = (
		"Propose a file change without writing it. Provide the repository-relative "
		"path and the complete desired file content; CASI builds the unified diff."
	)

	def __init__(self, repository_path: str | Path) -> None:
		self.repository_path = Path(repository_path).resolve()

	@property
	def argument_schema(self) -> dict[str, ToolArgumentSpec]:
		return {
			"path": ToolArgumentSpec("path", str),
			"content": ToolArgumentSpec("content", str),
		}

	def run(self, arguments: dict[str, Any]) -> ToolResult:
		relative = Path(arguments["path"])
		target = (self.repository_path / relative).resolve()
		if relative.is_absolute() or self.repository_path not in target.parents:
			raise ValueError("Path must stay inside the repository")
		if not target.is_file():
			raise FileNotFoundError(f"File not found: {relative.as_posix()}")
		before = target.read_text(encoding="utf-8").splitlines(keepends=True)
		content = arguments["content"]
		if content and not content.endswith("\n"):
			content += "\n"
		after = content.splitlines(keepends=True)
		patch = "".join(
			difflib.unified_diff(
				before,
				after,
				fromfile=f"a/{relative.as_posix()}",
				tofile=f"b/{relative.as_posix()}",
			)
		)
		if not patch:
			raise ValueError("The proposed content does not change the file")
		return ToolResult(success=True, output=patch, metadata={"path": relative.as_posix()})


class ValidatePatchTool(Tool):
	"""Validate a unified diff without changing the repository."""

	name = "validate_patch"
	description = "Validate a proposed unified diff without applying it."

	def __init__(self, repository_path: str | Path) -> None:
		self.repository_path = repository_path

	@property
	def argument_schema(self) -> dict[str, ToolArgumentSpec]:
		return {"patch": ToolArgumentSpec("patch", str)}

	def run(self, arguments: dict[str, Any]) -> ToolResult:
		validation = validate_patch(self.repository_path, arguments["patch"])
		return ToolResult(
			success=validation.valid,
			output="Patch is valid" if validation.valid else "",
			error=validation.error,
			metadata={"files": validation.files, "valid": validation.valid},
		)


class ApplyPatchTool(Tool):
	"""Apply a validated patch only after explicit approval."""

	name = "apply_patch"
	description = "Apply a validated unified diff after explicit user approval."

	def __init__(self, repository_path: str | Path) -> None:
		self.repository_path = repository_path

	@property
	def argument_schema(self) -> dict[str, ToolArgumentSpec]:
		return {
			"patch": ToolArgumentSpec("patch", str),
			"approved": ToolArgumentSpec("approved", bool, required=False, default=False),
			"dry_run": ToolArgumentSpec("dry_run", bool, required=False, default=True),
		}

	def run(self, arguments: dict[str, Any]) -> ToolResult:
		try:
			files = apply_patch(
				self.repository_path,
				arguments["patch"],
				approved=arguments["approved"],
				dry_run=arguments["dry_run"],
			)
		except PatchApplicationError as exc:
			return ToolResult(success=False, output="", error=str(exc))

		return ToolResult(
			success=True,
			output="Patch validated (dry-run)" if arguments["dry_run"] else "Patch applied",
			metadata={"files": files, "dry_run": arguments["dry_run"]},
		)
