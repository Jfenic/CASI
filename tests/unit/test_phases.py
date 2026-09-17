from __future__ import annotations

from casi.agent.intent import TaskIntent
from casi.agent.phases import (
    AgentPhase,
    PhaseContext,
    final_allowed,
    nudge_for_protocol_violation,
    resolve_phase,
    should_use_create_action_schema,
)
from casi.agent.state import PatchVerification


def test_final_allowed_blocks_action_required() -> None:
    assert final_allowed(AgentPhase.ACTION_REQUIRED) is False
    assert final_allowed(AgentPhase.INSPECT) is True
    assert final_allowed(AgentPhase.VERIFY) is True
    assert final_allowed(AgentPhase.FINAL_ALLOWED) is True


def test_resolve_phase_action_required_for_create_without_mutation() -> None:
    phase = resolve_phase(
        PhaseContext(
            intent=TaskIntent.CREATE,
            mutation_workflow=True,
            mutation_submitted=False,
            task_requests_mutation=True,
        )
    )
    assert phase is AgentPhase.ACTION_REQUIRED


def test_resolve_phase_verify_after_successful_propose_file() -> None:
    phase = resolve_phase(
        PhaseContext(
            intent=TaskIntent.FIX,
            mutation_workflow=True,
            mutation_submitted=True,
            task_requests_mutation=True,
        )
    )
    assert phase is AgentPhase.VERIFY


def test_resolve_phase_inspect_for_read_only_overview() -> None:
    phase = resolve_phase(
        PhaseContext(
            intent=TaskIntent.OVERVIEW,
            mutation_workflow=False,
            mutation_submitted=False,
            task_requests_mutation=False,
        )
    )
    assert phase is AgentPhase.INSPECT
    assert final_allowed(phase) is True


def test_resolve_phase_final_allowed_for_conversation() -> None:
    phase = resolve_phase(
        PhaseContext(
            intent=TaskIntent.CONVERSATION,
            mutation_workflow=False,
            mutation_submitted=False,
            task_requests_mutation=False,
        )
    )
    assert phase is AgentPhase.FINAL_ALLOWED


def test_protocol_violation_message_mentions_action_required() -> None:
    message = nudge_for_protocol_violation(AgentPhase.ACTION_REQUIRED)
    assert "ACTION_REQUIRED" in message
    assert "propose_file" in message


def test_should_use_create_action_schema_before_success() -> None:
    assert (
        should_use_create_action_schema(
            intent=TaskIntent.CREATE,
            layout_known=True,
            propose_file_succeeded=False,
            patch_verification=None,
        )
        is True
    )


def test_should_use_create_action_schema_after_failed_patch_verify() -> None:
    assert (
        should_use_create_action_schema(
            intent=TaskIntent.CREATE,
            layout_known=True,
            propose_file_succeeded=True,
            patch_verification=PatchVerification(
                passed=False,
                output="tests failed",
                runner="docker",
            ),
        )
        is True
    )


def test_should_not_use_create_action_schema_after_passing_patch_verify() -> None:
    assert (
        should_use_create_action_schema(
            intent=TaskIntent.CREATE,
            layout_known=True,
            propose_file_succeeded=True,
            patch_verification=PatchVerification(
                passed=True,
                output="ok",
                runner="docker",
            ),
        )
        is False
    )
