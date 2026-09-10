"""State returned by an agent execution."""

from __future__ import annotations

from dataclasses import dataclass, field

from casi.agent.failure_classification import FailureKind
from casi.llm.base import ChatMessage


@dataclass(frozen=True)
class PatchVerification:
    passed: bool
    output: str
    runner: str
    correction_attempts: int = 0
    failure_kind: FailureKind | None = None


@dataclass(frozen=True)
class AgentResult:
    success: bool
    response: str = ""
    clarification: str | None = None
    plan: list[str] = field(default_factory=list)
    error: str | None = None
    steps: int = 0
    messages: list[ChatMessage] = field(default_factory=list)
    patch_verification: PatchVerification | None = None
    requested_code_change: bool = False
    trace: list[str] = field(default_factory=list)
