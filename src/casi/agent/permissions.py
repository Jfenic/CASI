"""Permission tiers for orchestrated agent execution."""

from __future__ import annotations

from enum import Enum, StrEnum

from casi.agent.intent import TaskIntent
from casi.agent.policies import get_tool_permission


class PermissionTier(StrEnum):
    """How much user approval a plan phase requires."""

    # Keep the public string representation used before StrEnum.
    __str__ = Enum.__str__
    __format__ = Enum.__format__

    READ = "read"
    EXECUTE = "execute"
    MUTATE = "mutate"


_TIER_LABELS = {
    PermissionTier.READ: "lectura",
    PermissionTier.EXECUTE: "ejecución",
    PermissionTier.MUTATE: "modificación",
}


def tier_label(tier: PermissionTier) -> str:
    """Return a short human label for prompts."""

    return _TIER_LABELS[tier]


def resolve_permission_tier(task: str, intent: TaskIntent) -> PermissionTier:
    """Map a subtask to the approval tier required before running its agent."""

    _ = (task, intent)
    return PermissionTier.READ


def tier_requires_approval(tier: PermissionTier) -> bool:
    """Return whether the user must approve this tier before execution."""

    return tier is not PermissionTier.READ


_TIER_RANK = {
    PermissionTier.READ: 0,
    PermissionTier.EXECUTE: 1,
    PermissionTier.MUTATE: 2,
}


def tool_covered_by_approved_tier(
    tool_name: str, approved_tier: PermissionTier
) -> bool:
    """Return whether a tool is already covered by a granted phase approval."""

    if not tier_requires_approval(approved_tier):
        return False
    permission = get_tool_permission(tool_name)
    if permission is None:
        return False
    try:
        tool_tier = PermissionTier(permission.value)
    except ValueError:
        return False
    return _TIER_RANK[tool_tier] <= _TIER_RANK[approved_tier]
