"""Unit tests for failure classification helpers."""

from __future__ import annotations

from casi.agent.failure_classification import (
	FailureKind,
	classify_patch_validation_error,
	classify_test_result,
	is_docker_infrastructure_failure,
)
from casi.sandbox.base import TestResult


def test_classify_patch_validation_error_detects_corrupt_patch() -> None:
	kind = classify_patch_validation_error("error: corrupt patch at line 4")

	assert kind is FailureKind.MODEL_FORMAT


def test_classify_test_result_detects_dependency_failure() -> None:
	result = TestResult(
		command=["python3", "-m", "pytest"],
		exit_code=1,
		stdout="",
		stderr="ModuleNotFoundError: No module named validators",
		duration_seconds=0.1,
	)

	assert classify_test_result(result, "local") is FailureKind.DEPENDENCY


def test_is_docker_infrastructure_failure_detects_missing_pytest_module() -> None:
	result = TestResult(
		command=["python3", "-m", "pytest"],
		exit_code=1,
		stdout="",
		stderr="No module named pytest",
		duration_seconds=0.1,
	)

	assert is_docker_infrastructure_failure(result) is True
