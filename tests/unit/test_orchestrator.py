from __future__ import annotations

from pathlib import Path

from casi.agent.intent import TaskIntent
from casi.agent.orchestrator import AgentOrchestrator
from casi.agent.permissions import PermissionTier
from casi.llm.base import ChatMessage, LLMResponse, ToolDefinition


class FakeClient:
    def __init__(self, responses: list[LLMResponse]) -> None:
        self.responses = iter(responses)
        self.calls = 0

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        self.calls += 1
        return next(self.responses)


def test_orchestrator_runs_general_agent_without_segment_approval(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("demo\n", encoding="utf-8")
    approvals: list[PermissionTier] = []
    client = FakeClient([LLMResponse.final("Overview ready.")])

    result = AgentOrchestrator(
        client,
        tmp_path,
        approve_segment=lambda segment: approvals.append(segment.tier) or True,
        routing_mode="off",
    ).run("dime que trata este proyecto")

    assert result.success is True
    assert approvals == []
    assert result.step_results[0].step.agent_name == "general"
    assert result.step_results[0].step.tier is PermissionTier.READ


def test_orchestrator_confirms_run_tests_at_tool_call(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n",
        encoding="utf-8",
    )
    confirmed: list[str] = []
    client = FakeClient(
        [
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.final("All tests passed."),
        ]
    )

    result = AgentOrchestrator(
        client,
        tmp_path,
        require_tool_confirmation=lambda name, _args: confirmed.append(name) or True,
        routing_mode="off",
    ).run("ejecuta los tests")

    assert result.success is True
    assert confirmed == ["run_tests"]
    assert result.step_results[0].step.agent_name == "general"


def test_orchestrator_does_not_require_segment_approval_for_compound_tasks(
    tmp_path: Path,
) -> None:
    asked: list[PermissionTier] = []
    client = FakeClient([LLMResponse.final("Done.")])

    result = AgentOrchestrator(
        client,
        tmp_path,
        approve_segment=lambda segment: asked.append(segment.tier) or False,
        routing_mode="off",
    ).run("revisa module.py y ejecuta los tests")

    assert result.success is True
    assert asked == []


def test_orchestrator_reuses_tool_confirmation_after_first_run_tests_approval(
    tmp_path: Path,
) -> None:
    (tmp_path / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n",
        encoding="utf-8",
    )
    confirmed: list[str] = []
    client = FakeClient(
        [
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.final("All tests passed."),
        ]
    )

    result = AgentOrchestrator(
        client,
        tmp_path,
        require_tool_confirmation=lambda name, _args: confirmed.append(name) or True,
        routing_mode="off",
    ).run("ejecuta los tests")

    assert result.success is True
    assert confirmed == ["run_tests"]


def test_orchestrator_resumes_same_agent_after_clarification(tmp_path: Path) -> None:
    (tmp_path / "validators.py").write_text(
        "def validate_email():\n    pass\n", encoding="utf-8"
    )
    client = FakeClient(
        [
            LLMResponse.clarification("Which behavior should change?"),
            LLMResponse.final("I will tighten validate_email."),
        ]
    )
    orchestrator = AgentOrchestrator(client, tmp_path, routing_mode="off")

    first = orchestrator.run("Improve things please")
    assert first.clarification == "Which behavior should change?"
    assert first.pending is not None
    assert first.pending.agent is not None
    pending_agent = first.pending.agent

    second = orchestrator.run(
        "Tighten validate_email to reject bad addresses",
        pending=first.pending,
    )

    assert second.success is True
    assert second.pending is None
    assert second.step_results[0].result.messages[0].content == "Improve things please"
    assert pending_agent is first.pending.agent


def test_orchestrator_single_general_step_for_compound_task(tmp_path: Path) -> None:
    client = FakeClient(
        [
            LLMResponse.final("Found validate_email in validators.py."),
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.final("Tests finished."),
        ]
    )

    result = AgentOrchestrator(
        client,
        tmp_path,
        require_tool_confirmation=lambda *_args: True,
        routing_mode="off",
    ).run("explica validate_email y ejecuta los tests")

    assert result.success is True
    assert len(result.step_results) == 1
    assert result.step_results[0].step.agent_name == "general"
    assert result.step_results[0].step.objective is TaskIntent.UNKNOWN


def test_orchestrator_propagates_patch_verification_on_failure(
    tmp_path: Path,
) -> None:
    (tmp_path / "sample.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "test_sample.py").write_text(
        "from sample import value\n\ndef test_value():\n    assert value == 2\n",
        encoding="utf-8",
    )
    bad_patch = (
        "--- a/sample.py\n+++ b/sample.py\n@@ -1 +1 @@\n-value = 1\n+value = 1\n"
    )
    client = FakeClient(
        [
            LLMResponse.final(f"Broken patch\n{bad_patch}"),
            LLMResponse.final(f"Broken patch\n{bad_patch}"),
            LLMResponse.final(f"Broken patch\n{bad_patch}"),
        ]
    )

    result = AgentOrchestrator(
        client,
        tmp_path,
        max_correction_attempts=2,
        routing_mode="off",
    ).run("fix the failing test", category="fix")

    assert result.success is False
    assert result.patch_verification is not None
    assert result.patch_verification.passed is False
    assert result.patch_verification.correction_attempts == 2
