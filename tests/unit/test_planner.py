from __future__ import annotations

from casi.agent.intent import TaskIntent
from casi.agent.permissions import PermissionTier, resolve_permission_tier
from casi.agent.planner import TaskPlanner, decompose_task, group_segments
from casi.agent.planner import AgentPlanStep


def test_decompose_task_splits_read_and_execute_requests() -> None:
    parts = decompose_task("revisa loop.py y ejecuta los tests")
    assert len(parts) == 2
    assert "loop.py" in parts[0]
    assert "tests" in parts[1]


def test_decompose_task_keeps_fix_requests_single_step() -> None:
    parts = decompose_task("corrige el bug y haz que pasen los tests")
    assert parts == ["corrige el bug y haz que pasen los tests"]


def test_plan_assigns_read_then_execute_tiers() -> None:
    plan = TaskPlanner.create_plan("revisa loop.py y ejecuta los tests")
    assert plan.step_count() == 2
    assert plan.segments[0].tier is PermissionTier.READ
    assert plan.segments[1].tier is PermissionTier.EXECUTE
    assert plan.segments[0].steps[0].objective is TaskIntent.INSPECT


def test_plan_fix_request_is_single_mutate_segment() -> None:
    plan = TaskPlanner.create_plan("corrige validate_email y pasa los tests")
    assert plan.step_count() == 1
    assert plan.segments[0].tier is PermissionTier.MUTATE
    assert plan.segments[0].steps[0].objective is TaskIntent.FIX


def test_plan_appends_presenter_for_overview_requests() -> None:
    plan = TaskPlanner.create_plan("dime que trata este proyecto")
    assert plan.step_count() == 2
    assert plan.segments[0].steps[0].objective is TaskIntent.OVERVIEW
    assert plan.segments[0].steps[-1].objective is TaskIntent.PRESENT


def test_plan_skips_presenter_for_conversation() -> None:
    plan = TaskPlanner.create_plan("hola")
    assert plan.step_count() == 1
    assert plan.segments[0].steps[0].objective is TaskIntent.CONVERSATION


def test_plan_skips_presenter_for_fix_requests() -> None:
    plan = TaskPlanner.create_plan("corrige validate_email y pasa los tests")
    assert all(step.objective is not TaskIntent.PRESENT for step in _plan_steps(plan))


def _plan_steps(plan):
    for segment in plan.segments:
        yield from segment.steps


def test_resolve_permission_tier_for_run_tests_only() -> None:
    tier = resolve_permission_tier("ejecuta los tests", TaskIntent.UNKNOWN)
    assert tier is PermissionTier.EXECUTE


def test_group_segments_merges_same_tier_steps() -> None:
    steps = [
        AgentPlanStep.from_task("explain foo", session_messages=[]),
        AgentPlanStep.from_task("explain bar", session_messages=[]),
        AgentPlanStep.from_task("run tests", session_messages=[]),
    ]
    segments = group_segments(steps)
    assert len(segments) == 2
    assert len(segments[0].steps) == 2
    assert segments[0].tier is PermissionTier.READ
    assert segments[1].tier is PermissionTier.EXECUTE
