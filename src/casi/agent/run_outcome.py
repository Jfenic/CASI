"""Structured outcomes for one-shot agent runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from casi.agent.orchestrator import OrchestratorResult
from casi.patching.extract import extract_patch
from casi.patching.validator import validate_patch


@dataclass(frozen=True)
class AgentRunOutcome:
	"""Normalized result for CLI and API consumers."""

	success: bool
	response: str
	error: str | None
	clarification: str | None
	requested_code_change: bool
	plan: tuple[str, ...]
	trace: tuple[str, ...]
	patch: str | None
	patch_valid: bool
	patch_error: str | None
	patch_files: tuple[str, ...]
	tests_passed: bool | None
	test_output: str | None
	test_runner: str | None

	@property
	def awaiting_patch_approval(self) -> bool:
		"""Return whether a valid patch is ready for human approval."""

		if not self.success or self.patch is None or not self.patch_valid:
			return False
		if self.tests_passed is False:
			return False
		return True


def resolve_agent_run_outcome(
	repository: str | Path,
	result: OrchestratorResult,
) -> AgentRunOutcome:
	"""Extract patch metadata from an orchestrator result without side effects."""

	patch = extract_patch(result.response) if result.success else None
	patch_valid = False
	patch_error: str | None = None
	patch_files: tuple[str, ...] = ()
	tests_passed: bool | None = None
	test_output: str | None = None
	test_runner: str | None = None

	if result.patch_verification is not None:
		tests_passed = result.patch_verification.passed
		test_output = result.patch_verification.output
		test_runner = result.patch_verification.runner

	if patch is not None:
		validation = validate_patch(repository, patch)
		patch_valid = validation.valid
		patch_error = validation.error
		patch_files = tuple(validation.files)

	return AgentRunOutcome(
		success=result.success,
		response=result.response,
		error=result.error,
		clarification=result.clarification,
		requested_code_change=result.requested_code_change,
		plan=tuple(result.plan),
		trace=tuple(result.trace),
		patch=patch,
		patch_valid=patch_valid,
		patch_error=patch_error,
		patch_files=patch_files,
		tests_passed=tests_passed,
		test_output=test_output,
		test_runner=test_runner,
	)
