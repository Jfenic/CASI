from __future__ import annotations

from casi.agent.intent import TaskIntent
from casi.agent.nudges import is_agent_nudge, nudge_for_missing_patch
from casi.agent.response_policy import ResponsePolicy, RetryBudget


def test_is_agent_nudge_detects_system_messages() -> None:
    nudge = nudge_for_missing_patch()
    assert is_agent_nudge(nudge.user_message) is True
    assert is_agent_nudge("corrige el código que falla") is False


def test_response_policy_nudges_for_missing_patch_after_inspection() -> None:
    policy = ResponsePolicy()
    retries = RetryBudget()

    nudge = policy.evaluate_nudge(
        "Aquí está la corrección.",
        task_context="pasa los tests",
        intent=TaskIntent.FIX,
        retries=retries,
        repository_inspected=True,
        continuing_after_clarification=False,
    )

    assert nudge is not None
    assert retries.patch_nudges == 1


def test_response_policy_skips_patch_nudge_without_inspection() -> None:
    policy = ResponsePolicy()
    retries = RetryBudget()

    nudge = policy.evaluate_nudge(
        "Aquí está la corrección.",
        task_context="pasa los tests",
        intent=TaskIntent.FIX,
        retries=retries,
        repository_inspected=False,
        continuing_after_clarification=False,
    )

    assert nudge is not None
    assert retries.deferral_nudges == 1
    assert retries.patch_nudges == 0
