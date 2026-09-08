"""Session-scoped tools that do not inspect the repository."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from casi.agent.planner import AgentPlan
from casi.tools.base import Tool, ToolArgumentSpec
from casi.tools.result import ToolResult


class GetSessionPlanTool(Tool):
	"""Return the active or last generated multi-agent plan for this session."""

	name = "get_session_plan"
	description = (
		"Return the CASI session plan stored in memory for the current task. "
		"Use this when the user asks for the plan, next steps, or what CASI "
		"intends to do. Do not read README.md or other repository files for this."
	)

	def __init__(self, plan_provider: Callable[[], AgentPlan | None]) -> None:
		self._plan_provider = plan_provider

	@property
	def argument_schema(self) -> dict[str, ToolArgumentSpec]:
		return {}

	def run(self, arguments: dict[str, Any]) -> ToolResult:
		_ = arguments
		plan = self._plan_provider()
		if plan is None:
			return ToolResult(
				success=True,
				output=(
					"No session plan is stored yet. Tell the user to start a task "
					"first, then ask again for the plan."
				),
				metadata={"available": False},
			)
		lines = [f"Task: {plan.original_task}", *plan.summary_lines()]
		return ToolResult(
			success=True,
			output="\n".join(lines),
			metadata={
				"available": True,
				"original_task": plan.original_task,
				"step_count": plan.step_count(),
			},
		)
