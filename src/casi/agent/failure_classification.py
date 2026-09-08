"""Classify agent, patch, and test failures for targeted recovery."""

from __future__ import annotations

from enum import Enum

from casi.sandbox.base import TestResult


class FailureKind(str, Enum):
	"""Coarse failure categories used in traces, nudges, and reports."""

	CODE = "code"
	DEPENDENCY = "dependency"
	DOCKER = "docker"
	TIMEOUT = "timeout"
	PATCH_INVALID = "patch_invalid"
	PATCH_APPLY = "patch_apply"
	MODEL_FORMAT = "model_format"
	UNKNOWN = "unknown"


class TestExecutionError(RuntimeError):
	"""Raised when tests cannot run in the requested sandbox mode."""

	__test__ = False

	def __init__(self, message: str, *, failure_kind: FailureKind) -> None:
		super().__init__(message)
		self.failure_kind = failure_kind


_KIND_LABELS = {
	FailureKind.CODE: "test or assertion failure",
	FailureKind.DEPENDENCY: "missing dependency or import error",
	FailureKind.DOCKER: "Docker sandbox infrastructure failure",
	FailureKind.TIMEOUT: "command timeout",
	FailureKind.PATCH_INVALID: "invalid patch format or paths",
	FailureKind.PATCH_APPLY: "patch could not be applied",
	FailureKind.MODEL_FORMAT: "model produced malformed diff output",
	FailureKind.UNKNOWN: "unknown failure",
}


def failure_kind_label(kind: FailureKind) -> str:
	"""Return a short human-readable label."""

	return _KIND_LABELS[kind]


def is_docker_infrastructure_failure(result: TestResult) -> bool:
	"""Return whether Docker failed before pytest could run meaningfully."""

	if result.exit_code == 127:
		return True
	combined = f"{result.stdout}\n{result.stderr}"
	return "No module named pytest" in combined


def classify_patch_validation_error(error: str) -> FailureKind:
	"""Classify a patch validation error string."""

	lowered = error.lower()
	if "corrupt patch" in lowered:
		return FailureKind.MODEL_FORMAT
	if "does not apply" in lowered or "patch does not apply" in lowered:
		return FailureKind.PATCH_APPLY
	return FailureKind.PATCH_INVALID


def classify_test_result(result: TestResult, runner: str) -> FailureKind:
	"""Classify a repository or sandbox test run."""

	if result.timed_out:
		return FailureKind.TIMEOUT
	if runner == "docker" and is_docker_infrastructure_failure(result):
		return FailureKind.DOCKER
	combined = f"{result.stdout}\n{result.stderr}"
	if any(
		needle in combined
		for needle in (
			"ModuleNotFoundError",
			"ImportError:",
			"No module named",
			"cannot import name",
		)
	):
		return FailureKind.DEPENDENCY
	if result.exit_code != 0:
		return FailureKind.CODE
	return FailureKind.UNKNOWN
