"""Search-oriented tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from casi.repository.search import search_code
from casi.tools.base import Tool, ToolArgumentSpec
from casi.tools.result import ToolResult


class SearchCodeTool(Tool):
    name = "search_code"
    description = "Search for text inside safe repository files."

    def __init__(self, repository_path: str | Path) -> None:
        self.repository_path = repository_path

    @property
    def argument_schema(self) -> dict[str, ToolArgumentSpec]:
        return {
            "query": ToolArgumentSpec("query", str),
            "max_results": ToolArgumentSpec("max_results", int, required=False),
        }

    def run(self, arguments: dict[str, Any]) -> ToolResult:
        results = search_code(
            self.repository_path,
            arguments["query"],
            max_results=arguments["max_results"],
        )
        output = "\n".join(
            f"{result.path}:{result.line_number}: {result.line}" for result in results
        )
        return ToolResult(
            success=True,
            output=output,
            metadata={
                "count": len(results),
                "results": [
                    {
                        "path": result.path,
                        "line_number": result.line_number,
                        "line": result.line,
                    }
                    for result in results
                ],
            },
        )
