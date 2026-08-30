"""Deterministic repository inspection pipelines."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from casi.agent.intent import TaskIntent, derive_search_queries, extract_search_targets
from casi.agent.nudges import PIPELINE_FALLBACK_PREFIX, ResponseNudge
from casi.agent.test_failures import extract_failure_paths
from casi.repository.explorer import looks_like_filename, resolve_named_paths
from casi.tools.result import ToolResult

ToolExecutor = Callable[[str, dict[str, object]], ToolResult]


def paths_from_search_output(output: str) -> list[str]:
	"""Extract unique file paths from search_code output lines."""

	paths: list[str] = []
	for line in output.splitlines():
		if ":" not in line:
			continue
		path = line.split(":", 1)[0].strip()
		if path and path not in paths:
			paths.append(path)
	return paths


def run_inspect_pipeline(
	context: str,
	execute: ToolExecutor,
	*,
	repository_path: str | Path,
) -> None:
	"""Search the repository and read the most relevant files."""

	read_paths = resolve_named_paths(repository_path, extract_search_targets(context))

	for query in derive_search_queries(context):
		if looks_like_filename(query):
			continue
		result = execute("search_code", {"query": query})
		if not result.output.strip():
			continue
		for path in paths_from_search_output(result.output):
			if path not in read_paths:
				read_paths.append(path)
		if read_paths:
			break

	for path in read_paths[:3]:
		execute("read_file", {"path": path})

	if not read_paths:
		execute("list_files", {})


def run_overview_pipeline(execute: ToolExecutor) -> None:
	"""Collect a repository overview from structure and documentation."""

	execute("list_files", {})
	execute("read_file", {"path": "README.md"})


def run_git_status_pipeline(execute: ToolExecutor) -> None:
	"""Collect current repository changes."""

	execute("git_diff", {})


def run_fix_pipeline(
	context: str,
	execute: ToolExecutor,
	*,
	repository_path: str | Path,
	test_output: str | None = None,
) -> None:
	"""Load source and test files involved in a failing test run."""

	read_paths: list[str] = []

	if test_output:
		for path in extract_failure_paths(test_output):
			if path not in read_paths:
				read_paths.append(path)

	for path in resolve_named_paths(repository_path, extract_search_targets(context)):
		if path not in read_paths:
			read_paths.append(path)

	if not read_paths:
		for query in derive_search_queries(context):
			if looks_like_filename(query):
				continue
			result = execute("search_code", {"query": query})
			if not result.output.strip():
				continue
			for path in paths_from_search_output(result.output):
				if path not in read_paths:
					read_paths.append(path)
			if read_paths:
				break

	for path in read_paths[:4]:
		execute("read_file", {"path": path})


def run_repository_pipeline(
	intent: TaskIntent,
	context: str,
	execute: ToolExecutor,
	*,
	repository_path: str | Path,
) -> None:
	"""Run the deterministic pipeline associated with a task intent."""

	if intent == TaskIntent.OVERVIEW:
		run_overview_pipeline(execute)
		return
	if intent == TaskIntent.INSPECT:
		run_inspect_pipeline(context, execute, repository_path=repository_path)
		return
	if intent == TaskIntent.GIT_STATUS:
		run_git_status_pipeline(execute)
		return
	if intent == TaskIntent.FIX:
		run_fix_pipeline(context, execute, repository_path=repository_path)


def nudge_after_fix_pipeline() -> ResponseNudge:
	return ResponseNudge(
		user_message=(
			f"{PIPELINE_FALLBACK_PREFIX} 'fix' loaded failing test and source files. "
			"Use the read_file results already in the conversation and reply with a "
			"complete unified diff inside a ```diff block. Each changed line must "
			"start with ---/+++, @@, space, +, or -."
		),
	)


def nudge_after_pipeline_fallback(intent: TaskIntent) -> ResponseNudge:
	return ResponseNudge(
		user_message=(
			f"{PIPELINE_FALLBACK_PREFIX} '{intent.value}' is now available "
			"from tool results. Answer the user's request from those results "
			'using {"type":"final","content":"your answer"}.'
		),
	)
