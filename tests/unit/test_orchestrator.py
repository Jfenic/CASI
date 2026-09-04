from __future__ import annotations

from pathlib import Path

from casi.agent.orchestrator import AgentOrchestrator
from casi.agent.intent import TaskIntent
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


def test_orchestrator_runs_read_segment_without_approval(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("demo\n", encoding="utf-8")
    approvals: list[PermissionTier] = []
    client = FakeClient(
        [
            LLMResponse.final("Overview ready."),
            LLMResponse.final("Overview ready."),
            LLMResponse.final("## Resumen\n\nOverview ready."),
        ]
    )

    result = AgentOrchestrator(
        client,
        tmp_path,
        approve_segment=lambda segment: approvals.append(segment.tier) or True,
    ).run("dime que trata este proyecto")

    assert result.success is True
    assert approvals == []
    assert result.step_results[-1].step.objective is TaskIntent.PRESENT


def test_orchestrator_asks_before_execute_segment(tmp_path: Path) -> None:
    (tmp_path / "module.py").write_text("x = 1\n", encoding="utf-8")
    asked: list[PermissionTier] = []
    client = FakeClient(
        [
            LLMResponse.final("Inspected."),
            LLMResponse.final("## Inspección\n\nInspected."),
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.final("Tests done."),
        ]
    )

    result = AgentOrchestrator(
        client,
        tmp_path,
        require_tool_confirmation=lambda *_args: True,
        approve_segment=lambda segment: asked.append(segment.tier) or True,
    ).run("revisa module.py y ejecuta los tests")

    assert result.success is True
    assert asked == [PermissionTier.EXECUTE]


def test_orchestrator_cancels_when_execute_segment_rejected(tmp_path: Path) -> None:
    client = FakeClient(
        [
            LLMResponse.final("Inspected."),
            LLMResponse.final("## Inspección\n\nInspected."),
        ]
    )

    result = AgentOrchestrator(
        client,
        tmp_path,
        approve_segment=lambda _segment: False,
    ).run("revisa module.py y ejecuta los tests")

    assert result.cancelled is True
    assert result.step_results
    assert result.step_results[0].step.tier is PermissionTier.READ


def test_orchestrator_does_not_reconfirm_tools_after_execute_approval(tmp_path: Path) -> None:
    (tmp_path / "module.py").write_text("x = 1\n", encoding="utf-8")
    confirmed: list[str] = []
    client = FakeClient(
        [
            LLMResponse.final("Inspected."),
            LLMResponse.final("## Inspección\n\nInspected."),
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.final("Tests done."),
        ]
    )

    result = AgentOrchestrator(
        client,
        tmp_path,
        require_tool_confirmation=lambda name, _args: confirmed.append(name) or True,
        approve_segment=lambda _segment: True,
    ).run("revisa module.py y ejecuta los tests")

    assert result.success is True
    assert confirmed == []


def test_orchestrator_confirms_unexpected_execute_during_read(tmp_path: Path) -> None:
    (tmp_path / "module.py").write_text("x = 1\n", encoding="utf-8")
    confirmed: list[str] = []
    client = FakeClient(
        [
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.final("Done."),
            LLMResponse.final("## Resultado\n\nDone."),
        ]
    )

    result = AgentOrchestrator(
        client,
        tmp_path,
        require_tool_confirmation=lambda name, _args: confirmed.append(name) or True,
        approve_segment=lambda _segment: True,
        routing_mode="off",
    ).run("explica module.py")

    assert result.success is True
    assert confirmed == ["run_tests"]


def test_orchestrator_resumes_same_agent_after_clarification(tmp_path: Path) -> None:
    (tmp_path / "validators.py").write_text("def validate_email():\n    pass\n", encoding="utf-8")
    client = FakeClient(
        [
            LLMResponse.clarification("Which behavior should change?"),
            LLMResponse.final("I will tighten validate_email."),
            LLMResponse.final("## Plan\n\nI will tighten validate_email."),
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


def test_orchestrator_passes_previous_step_context(tmp_path: Path) -> None:
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
        approve_segment=lambda _segment: True,
    ).run("explica validate_email y ejecuta los tests")

    assert result.success is True
    assert len(result.step_results) == 2
    assert result.step_results[0].step.agent_name == "inspect"
    assert result.step_results[1].step.tier is PermissionTier.EXECUTE
