from __future__ import annotations

from casi.agent.intent import TaskIntent
from casi.agent.permissions import PermissionTier, resolve_permission_tier
from casi.agent.planner import AgentPlanStep, TaskPlanner, decompose_task, group_segments


def test_decompose_task_keeps_compound_requests_together() -> None:
    parts = decompose_task("revisa loop.py y ejecuta los tests")
    assert parts == ["revisa loop.py y ejecuta los tests"]


def test_plan_uses_general_agent_for_repository_work() -> None:
    plan = TaskPlanner.create_plan("Explain what foo_bar does")
    assert plan.step_count() == 1
    assert plan.segments[0].tier is PermissionTier.READ
    assert plan.segments[0].steps[0].objective is TaskIntent.UNKNOWN
    assert plan.segments[0].steps[0].agent_name == "general"


def test_plan_uses_general_agent_for_add_tests_requests() -> None:
    plan = TaskPlanner.create_plan("vamos a agregar más prueba unitaria")
    assert plan.step_count() == 1
    assert plan.segments[0].steps[0].objective is TaskIntent.UNKNOWN
    assert plan.segments[0].steps[0].agent_name == "general"
    assert all(step.objective is not TaskIntent.PRESENT for step in _plan_steps(plan))


def test_plan_uses_general_agent_for_fix_phrasing() -> None:
    plan = TaskPlanner.create_plan("corrige validate_email y pasa los tests")
    assert plan.step_count() == 1
    assert plan.segments[0].tier is PermissionTier.READ
    assert plan.segments[0].steps[0].objective is TaskIntent.UNKNOWN


def test_plan_fast_path_for_recall_plan() -> None:
    plan = TaskPlanner.create_plan("dime el plan")
    assert plan.step_count() == 1
    assert plan.segments[0].steps[0].objective is TaskIntent.RECALL_PLAN


def test_plan_fast_path_for_conversation() -> None:
    plan = TaskPlanner.create_plan("hola")
    assert plan.step_count() == 1
    assert plan.segments[0].steps[0].objective is TaskIntent.CONVERSATION


def test_plan_fast_path_for_git_status() -> None:
    plan = TaskPlanner.create_plan("git diff")
    assert plan.step_count() == 1
    assert plan.segments[0].steps[0].objective is TaskIntent.GIT_STATUS


def test_resolve_permission_tier_is_always_read() -> None:
    assert resolve_permission_tier("ejecuta los tests", TaskIntent.UNKNOWN) is PermissionTier.READ
    assert resolve_permission_tier("corrige el bug", TaskIntent.FIX) is PermissionTier.READ


def test_group_segments_merges_same_tier_steps() -> None:
    steps = [
        AgentPlanStep.from_intent("explain foo", TaskIntent.UNKNOWN),
        AgentPlanStep.from_intent("explain bar", TaskIntent.UNKNOWN),
    ]
    segments = group_segments(steps)
    assert len(segments) == 1
    assert len(segments[0].steps) == 2
    assert segments[0].tier is PermissionTier.READ


def _plan_steps(plan):
    for segment in plan.segments:
        yield from segment.steps
