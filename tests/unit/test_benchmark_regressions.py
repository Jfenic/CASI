"""Deterministic regressions for documented benchmark failures."""

from __future__ import annotations

from pathlib import Path

import pytest

from casi.agent.loop import AgentLoop
from casi.evaluation.benchmark import load_tasks
from casi.evaluation.grading import grade_task
from casi.llm.base import LLMResponse
from casi.sandbox.local_runner import LocalRunner
from casi.tools.registry import ToolRegistry

ROOT = Path(__file__).resolve().parents[2]
SORT_REPO = ROOT / "benchmarks" / "repositories" / "sort_app"
INITIALS_REPO = ROOT / "benchmarks" / "repositories" / "initials_app"
DEV_SUITE = ROOT / "benchmarks" / "development"
DEV_TASKS = load_tasks(DEV_SUITE / "tasks")


class ScriptedClient:
    def __init__(self, responses: list[LLMResponse]) -> None:
        self.responses = responses
        self.calls = 0

    def complete(self, messages, tools):
        index = self.calls
        self.calls += 1
        if index < len(self.responses):
            return self.responses[index]
        return self.responses[-1]


def test_task_017_regression_nudges_when_empty_list_still_fails(tmp_path: Path) -> None:
    """task_017: agent must not finish without a patch while tests still fail."""

    (tmp_path / "sorter.py").write_text(
        "def sort_asc(values: list[int]) -> list[int]:\n"
        "    return sorted(values, reverse=True)\n",
        encoding="utf-8",
    )
    (tmp_path / "test_sorter.py").write_text(
        "from sorter import sort_asc\n\n"
        "def test_sorts_ascending() -> None:\n"
        "    assert sort_asc([3, 1, 2]) == [1, 2, 3]\n\n"
        "def test_empty_list() -> None:\n"
        "    assert sort_asc([]) == []\n",
        encoding="utf-8",
    )
    client = ScriptedClient(
        [
            LLMResponse.final("Ascending order already works for non-empty lists."),
            LLMResponse.final("No patch is required."),
            LLMResponse.final("Still no patch."),
            LLMResponse.final("Still no patch."),
            LLMResponse.final("Still no patch."),
        ]
    )

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        max_correction_attempts=0,
        require_tool_confirmation=lambda *_args: True,
        routing_mode="off",
    ).run("Fix sort_asc so empty lists work and keep all tests passing")

    assert result.success is False
    assert "maximum of" in (result.error or "")
    nudges = [
        message.content
        for message in result.messages
        if message.role == "user" and "Protocol violation" in message.content
    ]
    assert nudges
    assert "ACTION_REQUIRED" in nudges[0]
    inspected = any(
        "sorter.py" in message.content
        for message in result.messages
        if message.role in {"tool", "user", "assistant"}
    )
    assert inspected


def test_task_023_regression_nudges_for_missing_module(tmp_path: Path) -> None:
    """task_023: missing local module must trigger create guidance."""

    (tmp_path / "test_initials.py").write_text(
        "from initials import initials\n\n"
        "def test_builds_initials_from_names() -> None:\n"
        "    assert initials('Ada', 'Lovelace') == 'A.L.'\n",
        encoding="utf-8",
    )
    client = ScriptedClient(
        [
            LLMResponse.final("I would create initials.py later."),
            LLMResponse.final("Still describing the module."),
            LLMResponse.final("Still describing the module."),
            LLMResponse.final("Still describing the module."),
            LLMResponse.final("Still describing the module."),
        ]
    )

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        max_correction_attempts=0,
        require_tool_confirmation=lambda *_args: True,
        routing_mode="off",
    ).run("Create the missing initials.py module so all tests pass")

    assert result.success is False
    missing_module = [
        message.content
        for message in result.messages
        if message.role == "user" and "missing local file" in message.content
    ]
    assert missing_module
    assert "initials.py" in missing_module[0]


def test_agent_loop_blocks_repeated_read_file(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "test_sample.py").write_text(
        "from sample import value\n\ndef test_value():\n    assert value == 2\n",
        encoding="utf-8",
    )
    patch = "--- a/sample.py\n+++ b/sample.py\n@@ -1 +1 @@\n-value = 1\n+value = 2\n"
    client = ScriptedClient(
        [
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.tool_call("read_file", {"path": "sample.py"}),
            LLMResponse.tool_call("read_file", {"path": "sample.py"}),
            LLMResponse.final(patch),
        ]
    )

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        max_correction_attempts=0,
        require_tool_confirmation=lambda *_args: True,
        routing_mode="off",
    ).run("Fix the failing test")

    assert result.success is True
    blocked = [
        message.content
        for message in result.messages
        if message.role == "user"
        and "read_file on sample.py is not needed again" in message.content
    ]
    assert blocked


def test_agent_loop_retries_after_corrupt_patch(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "test_sample.py").write_text(
        "from sample import value\n\ndef test_value():\n    assert value == 2\n",
        encoding="utf-8",
    )
    corrupt = "--- a/sample.py\n+++ b/sample.py\n corrupt diff\n"
    good = "--- a/sample.py\n+++ b/sample.py\n@@ -1 +1 @@\n-value = 1\n+value = 2\n"
    client = ScriptedClient(
        [
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.tool_call("read_file", {"path": "sample.py"}),
            LLMResponse.final(corrupt),
            LLMResponse.final(good),
        ]
    )

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        max_correction_attempts=2,
        require_tool_confirmation=lambda *_args: True,
        routing_mode="off",
    ).run("Fix the failing test")

    assert result.success is True
    assert result.patch_verification is not None
    assert result.patch_verification.passed is True


@pytest.mark.parametrize("task", DEV_TASKS, ids=lambda task: task.task_id)
def test_development_reference_passes_hidden_graders(task) -> None:
    reference = DEV_SUITE / "solutions" / task.repository
    result, _ = grade_task(
        task,
        original=DEV_SUITE / "repositories" / task.repository,
        candidate=reference,
        runner=LocalRunner(),
    )
    assert result.exit_code == 0, result.stdout + result.stderr


def test_dev_002_baseline_fails_hidden_grader() -> None:
    task = next(task for task in DEV_TASKS if task.task_id == "dev_002")
    result, _ = grade_task(
        task,
        original=DEV_SUITE / "repositories" / task.repository,
        candidate=DEV_SUITE / "repositories" / task.repository,
        runner=LocalRunner(),
    )
    assert result.exit_code != 0
