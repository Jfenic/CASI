from __future__ import annotations

import sys
from pathlib import Path

import pytest

from casi.agent.state import AgentResult
from casi.cli import main
from casi.evaluation.benchmark import BenchmarkTask, load_tasks, run_benchmark
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

    assert len(tasks) >= 3
    assert tasks[0].task_id
    assert tasks[0].instruction


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
    assert "t1: ok" in render_report(results)


def test_docker_runner_reports_unavailable_without_docker() -> None:
    runner = DockerRunner(image="casi-sandbox:missing")
    if runner.is_available():
        pytest.skip("Docker is available; skipping unavailable-path test")

    with pytest.raises(RuntimeError, match="Docker is not available"):
        runner.run(Path("."), [sys.executable, "-c", "print('hi')"])
