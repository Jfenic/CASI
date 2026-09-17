"""Abstract API client contract for the UI layer."""

from __future__ import annotations

from typing import Protocol

from casi.ui.client.models import CreateTaskPayload, TaskSnapshot, TaskSummary


class CasiApiError(RuntimeError):
    """Raised when the CASI API returns an error response."""


class CasiApiClient(Protocol):
    """Port for communicating with the CASI HTTP API."""

    def health(self) -> bool:
        """Return True when the API reports a healthy status."""

    def create_task(self, payload: CreateTaskPayload) -> TaskSnapshot:
        """Submit a new agent task."""

    def get_task(self, task_id: str) -> TaskSnapshot:
        """Fetch the latest snapshot for a task."""

    def list_tasks(self, *, limit: int = 50) -> list[TaskSummary]:
        """Return recent tasks, newest first."""

    def approve_task(self, task_id: str) -> TaskSnapshot:
        """Apply a proposed patch after human approval."""

    def reject_task(self, task_id: str) -> TaskSnapshot:
        """Reject a proposed patch."""
