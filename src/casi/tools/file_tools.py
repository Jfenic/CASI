"""File manipulation tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from casi.repository.explorer import list_files
from casi.repository.reader import read_file
from casi.tools.base import Tool, ToolArgumentSpec, path_argument
from casi.tools.result import ToolResult


class ListFilesTool(Tool):
    name = "list_files"
    description = "List safe files within the repository."

    def __init__(self, repository_path: str | Path) -> None:
        self.repository_path = repository_path

    @property
    def argument_schema(self) -> dict[str, ToolArgumentSpec]:
        return {
            "max_files": ToolArgumentSpec("max_files", int, required=False),
        }

    def run(self, arguments: dict[str, Any]) -> ToolResult:
        files = list_files(self.repository_path, max_files=arguments["max_files"])
        output = "\n".join(file_path.as_posix() for file_path in files)
        return ToolResult(
            success=True,
            output=output,
            metadata={
                "count": len(files),
                "files": [file_path.as_posix() for file_path in files],
            },
        )


class ReadFileTool(Tool):
    name = "read_file"
    description = "Read a safe file from the repository."

    def __init__(self, repository_path: str | Path) -> None:
        self.repository_path = repository_path

    @property
    def argument_schema(self) -> dict[str, ToolArgumentSpec]:
        return {
            "path": ToolArgumentSpec("path", (str, Path)),
            "start_line": ToolArgumentSpec(
                "start_line",
                int,
                required=False,
                default=1,
                minimum=1,
            ),
            "end_line": ToolArgumentSpec(
                "end_line",
                int,
                required=False,
                default=300,
                minimum=1,
            ),
        }

    def run(self, arguments: dict[str, Any]) -> ToolResult:
        file_path = path_argument(arguments["path"])
        output = read_file(
            self.repository_path,
            file_path,
            start_line=arguments["start_line"],
            end_line=arguments["end_line"],
        )
        return ToolResult(
            success=True,
            output=output,
            metadata={
                "path": file_path.as_posix(),
                "start_line": arguments["start_line"],
                "end_line": arguments["end_line"],
            },
        )