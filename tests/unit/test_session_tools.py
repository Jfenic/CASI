"""Unit tests for get_session_plan tool."""

from __future__ import annotations

from casi.agent.planner import AgentPlan, AgentPlanStep, PlanSegment
from casi.agent.permissions import PermissionTier
from casi.agent.intent import TaskIntent
from casi.tools.registry import ToolRegistry


def test_get_session_plan_returns_stored_plan(tmp_path) -> None:
	step = AgentPlanStep.from_intent("Inspect the repository", TaskIntent.UNKNOWN)
	plan = AgentPlan(
		original_task="Inspect the repository",
		segments=(PlanSegment(tier=PermissionTier.READ, steps=(step,)),),
	)

	registry = ToolRegistry(tmp_path, plan_provider=lambda: plan)
	result = registry.execute("get_session_plan", {})

	assert result.success is True
	assert "Inspect the repository" in result.output
	assert result.metadata["available"] is True


def test_get_session_plan_reports_missing_plan(tmp_path) -> None:
	registry = ToolRegistry(tmp_path, plan_provider=lambda: None)
	result = registry.execute("get_session_plan", {})

	assert result.success is True
	assert "No session plan is stored" in result.output
	assert result.metadata["available"] is False
