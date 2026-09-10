"""Unit tests for adaptive task tool confirmation."""

from __future__ import annotations

from casi.agent.intent import TaskIntent
from casi.agent.permissions import PermissionTier
from casi.agent.task_permission import TaskPermissionState
from casi.agent.tool_confirmation import build_task_tool_confirmation


def test_build_task_tool_confirmation_grants_cumulative_execute() -> None:
    state = TaskPermissionState()
    calls: list[str] = []

    def confirm(tool_name: str, arguments: dict[str, object]) -> bool:
        calls.append(tool_name)
        return True

    wrapped = build_task_tool_confirmation(confirm, state)
    assert wrapped is not None
    assert wrapped("run_tests", {}) is True
    assert wrapped("run_tests", {}) is True
    assert calls == ["run_tests"]
    assert state.approved_tier is PermissionTier.EXECUTE


def test_fix_intent_no_longer_preapproves_execute_tier() -> None:
    state = TaskPermissionState()
    wrapped = build_task_tool_confirmation(
        lambda *_args: True, state, intent=TaskIntent.FIX
    )
    assert wrapped is not None
    assert wrapped("list_files", {}) is True
    assert state.approved_tier is PermissionTier.READ
    assert wrapped("run_tests", {}) is True
    assert state.approved_tier is PermissionTier.EXECUTE
