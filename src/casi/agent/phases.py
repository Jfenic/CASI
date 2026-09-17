"""Agent execution phases for protocol enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from casi.agent.intent import TaskIntent, is_mutation_intent
from casi.agent.state import PatchVerification


class AgentPhase(StrEnum):
    """High-level loop phase that constrains legal model response kinds."""

    INSPECT = "inspect"
    ACTION_REQUIRED = "action_required"
    VERIFY = "verify"
    FINAL_ALLOWED = "final_allowed"


@dataclass(frozen=True)
class PhaseContext:
    """Inputs used to resolve the current agent phase."""

    intent: TaskIntent
    mutation_workflow: bool
    mutation_submitted: bool
    task_requests_mutation: bool


def resolve_phase(context: PhaseContext) -> AgentPhase:
    """Return the phase that governs whether a final answer is legal."""

    if context.intent in {
        TaskIntent.CONVERSATION,
        TaskIntent.META,
        TaskIntent.PRESENT,
    }:
        return AgentPhase.FINAL_ALLOWED

    if context.intent is TaskIntent.DIAGNOSE:
        return AgentPhase.FINAL_ALLOWED

    if _requires_mutation_action(context):
        if not context.mutation_submitted:
            return AgentPhase.ACTION_REQUIRED
        return AgentPhase.VERIFY

    return AgentPhase.INSPECT


def final_allowed(phase: AgentPhase) -> bool:
    """Return whether the model may end the turn with a final response."""

    return phase is not AgentPhase.ACTION_REQUIRED


def nudge_for_protocol_violation(phase: AgentPhase) -> str:
    """Return a structural retry message for an illegal final response."""

    if phase is AgentPhase.ACTION_REQUIRED:
        return (
            "Protocol violation: FinalResponse is illegal while phase=ACTION_REQUIRED. "
            "Expected a validated tool call with complete arguments. "
            "Call propose_file with the repository-relative path and complete file "
            "content. Do not return a final answer until the mutation is submitted."
        )
    return (
        f"Protocol violation: FinalResponse is illegal while phase={phase.value}. "
        "Return the required structured action or tool call for this phase."
    )


def _requires_mutation_action(context: PhaseContext) -> bool:
    return (
        is_mutation_intent(context.intent)
        or context.mutation_workflow
        or context.task_requests_mutation
    )


def should_use_create_action_schema(
    *,
    intent: TaskIntent,
    layout_known: bool,
    propose_file_succeeded: bool,
    patch_verification: PatchVerification | None,
) -> bool:
    """Return whether the CREATE turn must use ProposeFileAction schema only."""

    if intent is not TaskIntent.CREATE or not layout_known:
        return False
    if not propose_file_succeeded:
        return True
    if patch_verification is None:
        return False
    return not patch_verification.passed
