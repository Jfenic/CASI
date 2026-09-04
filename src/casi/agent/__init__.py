"""Agent runtime components.

Public classes are exposed lazily so importing a lightweight module such as
``casi.agent.policies`` does not initialize the complete agent runtime. The
runtime depends on the tool registry, which imports those policies.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
	"AgentFactory": ("casi.agent.factory", "AgentFactory"),
	"AgentLoop": ("casi.agent.loop", "AgentLoop"),
	"AgentOrchestrator": ("casi.agent.orchestrator", "AgentOrchestrator"),
	"AgentPlan": ("casi.agent.planner", "AgentPlan"),
	"AgentPlanStep": ("casi.agent.planner", "AgentPlanStep"),
	"AgentProfile": ("casi.agent.profiles", "AgentProfile"),
	"AgentResult": ("casi.agent.state", "AgentResult"),
	"AgentStepResult": ("casi.agent.orchestrator", "AgentStepResult"),
	"OrchestratorResult": ("casi.agent.orchestrator", "OrchestratorResult"),
	"PatchVerification": ("casi.agent.state", "PatchVerification"),
	"PendingOrchestration": ("casi.agent.orchestrator", "PendingOrchestration"),
	"PermissionTier": ("casi.agent.permissions", "PermissionTier"),
	"PlanSegment": ("casi.agent.planner", "PlanSegment"),
	"ResponsePolicy": ("casi.agent.response_policy", "ResponsePolicy"),
	"RetryBudget": ("casi.agent.response_policy", "RetryBudget"),
	"SpecializedAgent": ("casi.agent.factory", "SpecializedAgent"),
	"TaskPlanner": ("casi.agent.planner", "TaskPlanner"),
	"TaskScope": ("casi.agent.session", "TaskScope"),
	"format_segment_approval_prompt": (
		"casi.agent.orchestrator",
		"format_segment_approval_prompt",
	),
	"resolve_permission_tier": (
		"casi.agent.permissions",
		"resolve_permission_tier",
	),
	"resolve_profile": ("casi.agent.profiles", "resolve_profile"),
	"tier_requires_approval": (
		"casi.agent.permissions",
		"tier_requires_approval",
	),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
	"""Load a public export on first access and cache the result."""

	try:
		module_name, attribute_name = _EXPORTS[name]
	except KeyError as exc:
		raise AttributeError(
			f"module {__name__!r} has no attribute {name!r}"
		) from exc

	value = getattr(import_module(module_name), attribute_name)
	globals()[name] = value
	return value


def __dir__() -> list[str]:
	"""Include lazy public exports in interactive introspection."""

	return sorted({*globals(), *__all__})
