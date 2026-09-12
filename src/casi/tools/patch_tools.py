"""Structured tools for validating and applying proposed patches."""

from __future__ import annotations

import ast
import difflib
import re
from pathlib import Path
from typing import Any

from casi.patching.applier import PatchApplicationError, apply_patch
from casi.patching.validator import validate_patch
from casi.repository.security import is_sensitive_path
from casi.tools.base import Tool, ToolArgumentSpec
from casi.tools.result import ToolResult

_NUMBERED_LINE = re.compile(r"^(\d+):(?: ?)(.*)$")


def _strip_numbered_reader_output(content: str) -> tuple[str, bool]:
    """Remove ``read_file`` display prefixes when a model echoes them verbatim."""

    lines = content.splitlines()
    if not lines:
        return content, False
    matches = [_NUMBERED_LINE.match(line) for line in lines]
    if not all(matches):
        return content, False
    numbers = [int(match.group(1)) for match in matches if match is not None]
    if numbers != list(range(1, len(lines) + 1)):
        return content, False
    cleaned = "\n".join(match.group(2) for match in matches if match is not None)
    return cleaned, True


def _strip_trailing_line_whitespace(content: str) -> str:
    """Remove trailing spaces/tabs on each line so git apply accepts the diff."""

    if not content:
        return content
    return "\n".join(line.rstrip() for line in content.splitlines())


def _new_test_functions(before: str, after: str) -> set[str]:
    """Return test functions newly inserted into a non-test Python module."""

    try:
        before_tree = ast.parse(before)
        after_tree = ast.parse(after)
    except SyntaxError:
        return set()
    before_tests = {
        node.name
        for node in before_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }
    return {
        node.name
        for node in after_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
        and node.name not in before_tests
    }


class ProposeFileTool(Tool):
    """Build a correct unified diff from a complete replacement file."""

    name = "propose_file"
    description = (
        "Propose a file create or update without writing it. Provide the "
        "repository-relative path and the complete desired file content; CASI "
        "builds the unified diff."
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
        if is_sensitive_path(relative):
            raise ValueError(f"Sensitive path is not allowed: {relative.as_posix()}")
        creating = not target.is_file()
        if creating:
            if target.exists() and target.is_dir():
                raise ValueError(f"Path is a directory: {relative.as_posix()}")
            if not target.parent.exists():
                raise ValueError(
                    f"Parent directory does not exist for {relative.as_posix()}. "
                    "Choose a path inside an existing directory."
                )
            before_content = ""
        else:
            before_content = target.read_text(encoding="utf-8")
        before = before_content.splitlines(keepends=True)
        content, stripped_numbers = _strip_numbered_reader_output(arguments["content"])
        content = _strip_trailing_line_whitespace(content)
        is_test_file = relative.name.startswith("test_") or "tests" in relative.parts
        unexpected_tests = (
            set() if is_test_file else _new_test_functions(before_content, content)
        )
        if unexpected_tests:
            names = ", ".join(sorted(unexpected_tests))
            raise ValueError(
                f"Content for {relative.as_posix()} includes test functions "
                f"from another file ({names}). Propose only the complete content "
                "of the requested file."
            )
        if content and not content.endswith("\n"):
            content += "\n"
        # Blank lines after the last Python statement carry no program data and
        # cause git apply --whitespace=error to reject otherwise valid proposals.
        if relative.suffix == ".py" and content.strip():
            content = content.rstrip("\r\n") + "\n"
        if relative.suffix == ".py" and content.strip():
            try:
                ast.parse(content)
            except SyntaxError as exc:
                lineno = exc.lineno or 0
                raise ValueError(
                    f"Proposed Python content for {relative.as_posix()} has a syntax "
                    f"error at line {lineno}: {exc.msg}"
                ) from exc
        after = content.splitlines(keepends=True)
        if creating:
            diff = difflib.unified_diff(
                before,
                after,
                fromfile="/dev/null",
                tofile=f"b/{relative.as_posix()}",
            )
        else:
            diff = difflib.unified_diff(
                before,
                after,
                fromfile=f"a/{relative.as_posix()}",
                tofile=f"b/{relative.as_posix()}",
            )
        patch = "".join(diff)
        if not patch:
            raise ValueError(
                "The proposed content does not change the file"
                if not creating
                else "The proposed content is empty; new files need non-empty content"
            )
        return ToolResult(
            success=True,
            output=patch,
            metadata={
                "path": relative.as_posix(),
                "stripped_line_numbers": stripped_numbers,
                "created": creating,
            },
        )


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
            "approved": ToolArgumentSpec(
                "approved", bool, required=False, default=False
            ),
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
            output="Patch validated (dry-run)"
            if arguments["dry_run"]
            else "Patch applied",
            metadata={"files": files, "dry_run": arguments["dry_run"]},
        )
