"""Structured tools for validating proposed patches."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from casi.patching.validator import validate_patch
from casi.tools.base import Tool, ToolArgumentSpec
from casi.tools.result import ToolResult


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