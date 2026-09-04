"""Decision and safety policies for tool execution."""

from __future__ import annotations

from enum import Enum


class ToolPermission(str, Enum):
	"""Permission level required to execute a registered tool."""

	READ = "read"
	EXECUTE = "execute"
	MUTATE = "mutate"


TOOL_PERMISSIONS: dict[str, ToolPermission] = {
	"list_files": ToolPermission.READ,
	"read_file": ToolPermission.READ,
	"search_code": ToolPermission.READ,
	"git_diff": ToolPermission.READ,
	"validate_patch": ToolPermission.READ,
	"propose_file": ToolPermission.READ,
	"run_tests": ToolPermission.EXECUTE,
	"apply_patch": ToolPermission.MUTATE,
}

AGENT_TOOL_NAMES = frozenset(
	name
	for name, permission in TOOL_PERMISSIONS.items()
	if permission != ToolPermission.MUTATE
)


def get_tool_permission(name: str) -> ToolPermission | None:
	"""Return the configured permission for a tool name."""

	return TOOL_PERMISSIONS.get(name)


def is_agent_tool(name: str) -> bool:
	"""Return whether the tool may be exposed to the agent."""

	return name in AGENT_TOOL_NAMES


def requires_confirmation(name: str) -> bool:
	"""Return whether interactive mode must confirm the tool call."""

	return get_tool_permission(name) == ToolPermission.EXECUTE


def is_mutation_tool(name: str) -> bool:
	"""Return whether the tool can modify repository state."""

	return get_tool_permission(name) == ToolPermission.MUTATE
