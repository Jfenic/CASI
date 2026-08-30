"""Final-response evaluation and retry policy for the agent loop."""

from __future__ import annotations

from dataclasses import dataclass

from casi.agent.intent import TaskIntent, response_defers_repository_work
from casi.agent.nudges import (
	ResponseNudge,
	nudge_for_fix_without_inspection,
	nudge_for_malformed_json,
	nudge_for_missing_patch,
	nudge_for_repository_deferral,
)
from casi.agent.responses import is_malformed_json, response_missing_required_patch
from casi.patching.extract import extract_patch


@dataclass
class RetryBudget:
	format_nudges: int = 0
	deferral_nudges: int = 0
	patch_nudges: int = 0
	pipeline_fallbacks: int = 0
	max_format: int = 2
	max_deferral: int = 2
	max_patch: int = 2
	max_pipeline: int = 1


class ResponsePolicy:
	"""Decide whether a final model response should be nudged or rejected."""

	def evaluate_nudge(
		self,
		content: str,
		*,
		task_context: str,
		intent: TaskIntent,
		retries: RetryBudget,
		repository_inspected: bool,
		continuing_after_clarification: bool,
	) -> ResponseNudge | None:
		if is_malformed_json(content) and retries.format_nudges < retries.max_format:
			retries.format_nudges += 1
			return nudge_for_malformed_json()

		if (
			intent is TaskIntent.FIX
			and not continuing_after_clarification
			and not repository_inspected
			and extract_patch(content) is None
			and retries.deferral_nudges < retries.max_deferral
		):
			retries.deferral_nudges += 1
			return nudge_for_fix_without_inspection()

		if (
			response_defers_repository_work(content, intent)
			and retries.deferral_nudges < retries.max_deferral
		):
			retries.deferral_nudges += 1
			return nudge_for_repository_deferral()

		if (
			response_missing_required_patch(
				content,
				task_context,
				repository_inspected=repository_inspected,
			)
			and retries.patch_nudges < retries.max_patch
		):
			retries.patch_nudges += 1
			return nudge_for_missing_patch()

		return None

	def missing_required_patch(
		self,
		content: str,
		task_context: str,
		*,
		repository_inspected: bool,
	) -> bool:
		return response_missing_required_patch(
			content,
			task_context,
			repository_inspected=repository_inspected,
		)
