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
    on_permission: Callable[[str, PermissionTier, bool], None] | None = None,
) -> ToolConfirmation | None:
    """Wrap a confirmation callback with cumulative task permission coverage."""

    _ = intent
    if base_callback is None:
        return None

    def confirm(tool_name: str, arguments: dict[str, object]) -> bool:
        if permission_state.covers_tool(tool_name):
            return True
        permission = get_tool_permission(tool_name)
        tier = PermissionTier(permission.value) if permission is not None else None
        approved = base_callback(tool_name, arguments)
        if approved and tier is not None:
            permission_state.grant(tier)
            if on_permission is not None:
                on_permission(tool_name, tier, True)
            elif on_escalation is not None and tier is not PermissionTier.READ:
                on_escalation(tier)
        elif not approved and tier is not None and on_permission is not None:
            on_permission(tool_name, tier, False)
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
