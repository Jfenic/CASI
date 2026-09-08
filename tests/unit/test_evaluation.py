from __future__ import annotations

import sys
from pathlib import Path

import pytest

from casi.agent.state import AgentResult
from casi.cli import main
from casi.evaluation.benchmark import BenchmarkTask, BenchmarkTaskResult, load_tasks, run_benchmark
from casi.evaluation.metrics import summarize_results
from casi.evaluation.report import render_report
from casi.llm.base import LLMResponse
from casi.sandbox.docker_runner import DockerRunner


def test_cli_test_runs_pytest(tmp_path: Path, capsys) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_passes():\n    assert True\n",
        encoding="utf-8",
    )

    exit_code = main(["test", "--repo", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "exit_code=0" in output


def test_cli_test_reports_failure(tmp_path: Path, capsys) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_fails():\n    assert False\n",
        encoding="utf-8",
    )

    exit_code = main(["test", "--repo", str(tmp_path)])

    assert exit_code == 1


def test_load_benchmark_tasks() -> None:
    tasks = load_tasks(Path("benchmarks/tasks"))

    assert len(tasks) >= 20
    assert tasks[0].task_id
    assert tasks[0].instruction
    assert tasks[0].repository
    assert tasks[0].category


def test_benchmark_runner_collects_results() -> None:
    tasks = [
        BenchmarkTask(task_id="t1", name="One", instruction="Inspect"),
        BenchmarkTask(task_id="t2", name="Two", instruction="Search"),
    ]

    def run_task(task: BenchmarkTask) -> AgentResult:
        return AgentResult(
            success=task.task_id == "t1",
            response="ok",
            steps=2,
        )

    results = run_benchmark(tasks, run_task)

    assert len(results) == 2
    assert results[0].agent_success is True
    assert results[1].agent_success is False
    assert summarize_results(results)["tasks"] == 2
    assert "t1 [general]: ok" in render_report(results)


def test_benchmark_report_json_payload() -> None:
    results = [
        BenchmarkTaskResult(
            task_id="t1",
            name="One",
            repository="healthy_lib",
            category="read",
            model="mock",
            agent_success=True,
            task_success=True,
            steps=3,
            duration_seconds=1.5,
        )
    ]

    from casi.evaluation.report import build_report_payload, render_markdown_report

    payload = build_report_payload(results, model="mock")
    assert payload["model"] == "mock"
    assert payload["metrics"]["tasks"] == 1
    assert "task_success_rate" in payload["metrics"]
    assert render_markdown_report(results, model="mock").startswith("# CASI Benchmark")


def test_benchmark_runner_uses_isolated_repository(tmp_path: Path, monkeypatch) -> None:
    from casi.agent.orchestrator import OrchestratorResult
    from casi.evaluation.benchmark import BenchmarkTask
    from casi.evaluation.runner import BenchmarkRunOptions, run_task

    repos_root = Path("benchmarks/repositories")
    task = BenchmarkTask(
        task_id="read_only",
        name="Read healthy lib",
        instruction="Explain the repository",
        repository="healthy_lib",
        category="read",
        success_command=["python3", "-m", "pytest", "-q"],
        max_steps=4,
    )

    monkeypatch.setattr(
        "casi.evaluation.runner.AgentOrchestrator.run",
        lambda self, instruction: OrchestratorResult(
            success=True,
            response=f"done: {instruction[:20]}",
        ),
    )

    class FakeClient:
        model = "mock-model"

        def complete(self, messages, tools):
            raise AssertionError("complete should not be called in this test")

    result = run_task(
        task,
        repositories_root=repos_root,
        client=FakeClient(),
        options=BenchmarkRunOptions(repositories_root=repos_root),
    )

    assert result.agent_success is True
    assert result.task_success is True
    assert result.model == "mock-model"
    assert result.command_success is True


def test_cli_benchmark_lists_tasks(capsys) -> None:
    exit_code = main(["benchmark", "--list"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "task_001" in output
    assert "healthy_lib" in output


def test_docker_runner_reports_unavailable_without_docker() -> None:
    runner = DockerRunner(image="casi-sandbox:missing")
    if runner.is_available():
        pytest.skip("Docker is available; skipping unavailable-path test")

    with pytest.raises(RuntimeError, match="Docker is not available"):
        runner.run(Path("."), [sys.executable, "-c", "print('hi')"])
