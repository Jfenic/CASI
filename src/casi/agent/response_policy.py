"""Final-response evaluation and retry policy for the agent loop."""

from __future__ import annotations

from dataclasses import dataclass

from casi.agent.intent import (
    TaskIntent,
    is_mutation_intent,
    response_defers_repository_work,
)
from casi.agent.nudges import (
    ResponseNudge,
    nudge_for_diagnosis_format,
    nudge_for_layout_required,
    nudge_for_malformed_json,
    nudge_for_missing_patch,
    nudge_for_repository_deferral,
    nudge_for_unread_failure_sources,
)
from casi.agent.pipelines import repair_context_paths
from casi.agent.responses import is_malformed_json, response_missing_required_patch
from casi.agent.test_failures import output_reports_failures
from casi.llm.diagnosis import diagnosis_response_error
from casi.patching.extract import extract_patch


@dataclass
class RetryBudget:
    format_nudges: int = 0
    deferral_nudges: int = 0
    patch_nudges: int = 0
    pipeline_fallbacks: int = 0
    max_format: int = 2
    max_deferral: int = 2
    max_patch: int = 3
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
        layout_known: bool,
        continuing_after_clarification: bool,
        mutation_workflow: bool = False,
        remaining_test_output: str | None = None,
        read_file_paths: set[str] | None = None,
        repository_path: str | None = None,
    ) -> ResponseNudge | None:
        if intent is TaskIntent.DIAGNOSE:
            error = diagnosis_response_error(content)
            if error is not None and retries.format_nudges < retries.max_format:
                retries.format_nudges += 1
                return nudge_for_diagnosis_format(error)
            return None

        if is_malformed_json(content) and retries.format_nudges < retries.max_format:
            retries.format_nudges += 1
            return nudge_for_malformed_json()

        if (
            (is_mutation_intent(intent) or mutation_workflow)
            and not continuing_after_clarification
            and not layout_known
            and extract_patch(content) is None
            and retries.deferral_nudges < retries.max_deferral
        ):
            retries.deferral_nudges += 1
            return nudge_for_layout_required()

        if (
            mutation_workflow
            and extract_patch(content) is None
            and remaining_test_output
            and output_reports_failures(remaining_test_output)
            and read_file_paths is not None
            and retries.deferral_nudges < retries.max_deferral
        ):
            unread = [
                path
                for path in repair_context_paths(
                    remaining_test_output,
                    repository_path or ".",
                )
                if path not in read_file_paths
            ]
            if unread:
                retries.deferral_nudges += 1
                return nudge_for_unread_failure_sources(unread)

        if (
            response_defers_repository_work(content, intent)
            and retries.deferral_nudges < retries.max_deferral
        ):
            retries.deferral_nudges += 1
            return nudge_for_repository_deferral()

        if (
            intent is not TaskIntent.DIAGNOSE
            and response_missing_required_patch(
                content,
                task_context,
                repository_inspected=repository_inspected,
                mutation_workflow=mutation_workflow,
            )
            and retries.patch_nudges < retries.max_patch
        ):
            retries.patch_nudges += 1
            return nudge_for_missing_patch(
                remaining_test_output=remaining_test_output,
                task_context=task_context,
            )

        return None

    def missing_required_patch(
        self,
        content: str,
        task_context: str,
        *,
        repository_inspected: bool,
        mutation_workflow: bool = False,
    ) -> bool:
        return response_missing_required_patch(
            content,
            task_context,
            repository_inspected=repository_inspected,
            mutation_workflow=mutation_workflow,
        )
