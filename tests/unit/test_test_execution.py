from __future__ import annotations

from pathlib import Path

from casi.sandbox.base import TestResult as SandboxTestResult
from casi.sandbox.test_execution import is_docker_infrastructure_failure


def test_is_docker_infrastructure_failure_detects_missing_python() -> None:
    result = SandboxTestResult(
        command=["python3", "-m", "pytest"],
        exit_code=127,
        stdout="",
        stderr="/entrypoint.sh: exec: /usr/bin/python3: not found",
        duration_seconds=0.1,
        timed_out=False,
    )

    assert is_docker_infrastructure_failure(result) is True


def test_is_docker_infrastructure_failure_detects_missing_pytest_module() -> None:
    result = SandboxTestResult(
        command=["python3", "-m", "pytest"],
        exit_code=1,
        stdout="",
        stderr="No module named pytest",
        duration_seconds=0.1,
        timed_out=False,
    )

    assert is_docker_infrastructure_failure(result) is True


def test_is_docker_infrastructure_failure_ignores_real_test_failures() -> None:
    result = SandboxTestResult(
        command=["python3", "-m", "pytest"],
        exit_code=1,
        stdout="FAILED tests/test_sample.py::test_fails - assert False",
        stderr="",
        duration_seconds=0.1,
        timed_out=False,
    )

    assert is_docker_infrastructure_failure(result) is False
