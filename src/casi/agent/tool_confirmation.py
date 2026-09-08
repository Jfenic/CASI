"""Build adaptive tool confirmation callbacks for agent tasks."""

from __future__ import annotations

from collections.abc import Callable

from casi.agent.intent import TaskIntent
from casi.agent.permissions import PermissionTier
from casi.agent.policies import ToolPermission, get_tool_permission
from casi.agent.task_permission import TaskPermissionState


ToolConfirmation = Callable[[str, dict[str, object]], bool]


def build_task_tool_confirmation(
	base_callback: ToolConfirmation | None,
	permission_state: TaskPermissionState,
	*,
	intent: TaskIntent | None = None,
	on_escalation: Callable[[PermissionTier], None] | None = None,
) -> ToolConfirmation | None:
	"""Wrap a confirmation callback with cumulative task permission coverage."""

	_ = intent
	if base_callback is None:
		return None

	def confirm(tool_name: str, arguments: dict[str, object]) -> bool:
		if permission_state.covers_tool(tool_name):
			return True
		permission = get_tool_permission(tool_name)
		approved = base_callback(tool_name, arguments)
		if approved and permission is not None:
			try:
				granted = PermissionTier(permission.value)
			except ValueError:
				granted = None
			if granted is not None:
				permission_state.grant(granted)
				if on_escalation is not None and granted is not PermissionTier.READ:
					on_escalation(granted)
		return approved

	return confirm


def permission_tier_for_tool(tool_name: str) -> PermissionTier | None:
	"""Return the approval tier required for a tool."""

	permission = get_tool_permission(tool_name)
	if permission is None:
		return None
	if permission is ToolPermission.READ:
		return PermissionTier.READ
	if permission is ToolPermission.EXECUTE:
		return PermissionTier.EXECUTE
	return PermissionTier.MUTATE
