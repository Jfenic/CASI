"""Runtime regressions from the September 11 evaluation artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from casi.agent.factory import AgentFactory
from casi.agent.intent import TaskIntent
from casi.agent.loop import AgentLoop
from casi.agent.pipelines import missing_local_module_paths, repair_context_paths
from casi.evaluation.diagnosis import grade_diagnosis_task
from casi.llm.base import LLMResponse
from casi.llm.diagnosis import diagnosis_response_error
from casi.llm.parser import parse_response
from casi.patching.applier import apply_patch
from casi.patching.validator import validate_patch
from casi.sandbox.base import TestResult as SandboxTestResult
from casi.tools.patch_tools import ProposeFileTool
from casi.tools.registry import ToolRegistry
from casi.tools.result import ToolResult

DIAGNOSIS = {
    "file": "counter.py",
    "line": 9,
    "cause": "increment adds zero so the value never changes",
    "evidence": "self._value += 0",
}


class DiagnosisClient:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    def complete(self, messages, tools):
        self.calls.append(list(messages))
        return next(self.replies)


@pytest.mark.parametrize("wrapped", [False, True])
def test_diagnosis_survives_parser_policy_and_grader(tmp_path, monkeypatch, wrapped):
    (tmp_path / "counter.py").write_text("value = 0\n")
    monkeypatch.setattr(
        "casi.tools.test_tools.RunTestsTool.run",
        lambda *_: ToolResult(success=False, output="counter.py:1: AssertionError"),
    )
    payload = {"type": "final", "content": DIAGNOSIS}
    reply = (
        parse_response(json.dumps(payload))
        if wrapped
        else LLMResponse.final(json.dumps(DIAGNOSIS))
    )
    client = DiagnosisClient([reply])
    result = AgentFactory.create(
        TaskIntent.DIAGNOSE, client=client, repository=tmp_path
    ).run("Diagnose the failing tests without changing code.")
    assert result.success, result.error
    assert len(client.calls) == 1
    assert not result.requested_code_change
    assert result.patch_verification is None
    rubric = (
        Path(__file__).resolve().parents[2] / "benchmarks/diagnosis/rubrics/diag_001"
    )
    assert grade_diagnosis_task(result.response, grader_directory=rubric).passed


@pytest.mark.parametrize("recover", [False, True])
def test_diagnosis_retries_prose_and_rejects_exhausted_format(
    tmp_path, monkeypatch, recover
):
    monkeypatch.setattr(
        "casi.tools.test_tools.RunTestsTool.run",
        lambda *_: ToolResult(success=True, output="1 passed"),
    )
    prose = LLMResponse.final("The counter adds zero.")
    client = DiagnosisClient(
        [prose, LLMResponse.final(json.dumps(DIAGNOSIS))]
        if recover
        else [prose, prose, prose]
    )
    result = AgentFactory.create(
        TaskIntent.DIAGNOSE, client=client, repository=tmp_path
    ).run("Find the failure cause.")
    assert result.success is recover
    assert "response contract" in client.calls[1][-1].content
    if not recover:
        assert "diagnosis JSON" in result.error


@pytest.mark.parametrize("line", [True, 0, "9", None])
def test_diagnosis_rejects_invalid_line(line):
    assert diagnosis_response_error(json.dumps({**DIAGNOSIS, "line": line}))


def test_repair_context_excludes_external_traceback_paths(tmp_path):
    (tmp_path / "test_app.py").write_text("from app import value\n")
    (tmp_path / "app.py").write_text("value = 0\n")
    output = (
        "/usr/local/lib/python3.11/importlib/__init__.py:126: ImportError\n"
        "test_app.py:1: AssertionError\n"
    )
    assert repair_context_paths(output, tmp_path) == ["test_app.py", "app.py"]


def test_missing_modules_excludes_standard_library_and_installed_packages(tmp_path):
    (tmp_path / "test_app.py").write_text(
        "import json\nimport pytest\nfrom collections import deque\n"
        "from missing_app import value\n"
    )
    assert missing_local_module_paths(tmp_path, ["test_app.py"]) == ["missing_app.py"]


def test_create_python_with_trailing_blank_lines_produces_applicable_patch(tmp_path):
    proposal = ProposeFileTool(tmp_path).run(
        {"path": "new_module.py", "content": "value = 'a\\n'\n\n\n"}
    )
    validation = validate_patch(tmp_path, proposal.output)
    assert validation.valid, validation.error
    assert not (tmp_path / "new_module.py").exists()
    apply_patch(tmp_path, proposal.output, approved=True, dry_run=False)
    assert (tmp_path / "new_module.py").read_text() == "value = 'a\\n'\n"


def test_patch_retry_uses_latest_failure_instead_of_initial_missing_module(
    tmp_path, monkeypatch
):
    (tmp_path / "test_app.py").write_text("from app import value\n")
    monkeypatch.setattr(
        "casi.tools.test_tools.RunTestsTool.run",
        lambda *_: ToolResult(
            success=False,
            output="test_app.py:1: ModuleNotFoundError: No module named 'app'",
        ),
    )
    output = "test_app.py:3: AssertionError: assert 1 == 2\n1 failed"
    outcomes = iter(
        [
            SandboxTestResult(
                command=["pytest"],
                exit_code=1,
                stdout=output,
                stderr="",
                duration_seconds=0,
            ),
            SandboxTestResult(
                command=["pytest"],
                exit_code=0,
                stdout="1 passed",
                stderr="",
                duration_seconds=0,
            ),
        ]
    )
    monkeypatch.setattr(
        "casi.agent.patch_verify.run_patched_tests",
        lambda *_: (next(outcomes), "local"),
    )
    client = DiagnosisClient(
        [
            LLMResponse.tool_call(
                "propose_file", {"path": "app.py", "content": "value = 1\n"}
            ),
            LLMResponse.final("The module is fixed."),
            LLMResponse.tool_call(
                "propose_file", {"path": "app.py", "content": "value = 2\n"}
            ),
        ]
    )
    result = AgentLoop(client, ToolRegistry(tmp_path), routing_mode="off").run(
        "Create app.py with value equal to 2"
    )
    assert result.success, result.error
    assert result.patch_verification.correction_attempts == 1
    last_nudge = client.calls[2][-1].content
    assert "expected '2'" in last_nudge
    assert "ModuleNotFoundError" not in last_nudge
    assert not (tmp_path / "app.py").exists()
