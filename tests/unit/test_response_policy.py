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
        layout_known=True,
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
        layout_known=False,
        continuing_after_clarification=False,
    )

    assert nudge is not None
    assert retries.deferral_nudges == 1
    assert retries.patch_nudges == 0
    assert "Repository layout is not loaded yet" in nudge.user_message


def test_response_policy_requires_layout_before_create() -> None:
    policy = ResponsePolicy()
    retries = RetryBudget()

    nudge = policy.evaluate_nudge(
        "Voy a crear main.py.",
        task_context="crea el archivo main.py",
        intent=TaskIntent.CREATE,
        retries=retries,
        repository_inspected=False,
        layout_known=False,
        continuing_after_clarification=False,
    )

    assert nudge is not None
    assert "Repository layout is not loaded yet" in nudge.user_message
    assert retries.deferral_nudges == 1


def test_test_creation_nudge_keeps_contract_without_inventing_failures() -> None:
    task = "Create only test_retry.py. Do not change implementation."
    nudge = ResponsePolicy().evaluate_nudge(
        "I will add tests.",
        task_context=task,
        intent=TaskIntent.CREATE,
        retries=RetryBudget(),
        repository_inspected=True,
        layout_known=True,
        continuing_after_clarification=False,
        mutation_workflow=True,
        remaining_test_output=". [100%]\n1 passed in 0.00s",
    )
    assert nudge is not None
    assert "Tests are still failing" not in nudge.user_message
    assert task in nudge.user_message
    assert "propose_file" in nudge.user_message
