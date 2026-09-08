"""Task-scoped permission escalation for direct agent runs."""

from __future__ import annotations

from dataclasses import dataclass

from casi.agent.permissions import PermissionTier, tool_covered_by_approved_tier


@dataclass
class TaskPermissionState:
	"""Tracks cumulative tool approval granted during one agent task."""

	approved_tier: PermissionTier = PermissionTier.READ

	def covers_tool(self, tool_name: str) -> bool:
		"""Return whether the tool is already covered by granted approval."""

		return tool_covered_by_approved_tier(tool_name, self.approved_tier)

	def grant(self, tier: PermissionTier) -> None:
		"""Raise the approved tier without lowering it."""

		ranks = {
			PermissionTier.READ: 0,
			PermissionTier.EXECUTE: 1,
			PermissionTier.MUTATE: 2,
		}
		if ranks[tier] > ranks[self.approved_tier]:
			self.approved_tier = tier
