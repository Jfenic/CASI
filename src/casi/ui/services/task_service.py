"""Task orchestration for the visual interface."""

from __future__ import annotations

import time
from collections.abc import Callable

from casi.ui.client.models import CreateTaskPayload, TaskSnapshot, TaskSummary
from casi.ui.client.protocol import CasiApiClient, CasiApiError
from casi.ui.config import UISettings


class TaskService:
    """Coordinates task lifecycle operations against the API."""

    TERMINAL_STATUSES = frozenset(
        {"completed", "failed", "cancelled", "awaiting_approval"}
    )

    def __init__(self, client: CasiApiClient, settings: UISettings) -> None:
        self._client = client
        self._settings = settings

    def check_connection(self) -> bool:
        return self._client.health()

    def submit_task(self, payload: CreateTaskPayload) -> TaskSnapshot:
        return self._client.create_task(payload)

    def fetch_task(self, task_id: str) -> TaskSnapshot:
        return self._client.get_task(task_id)

    def list_recent_tasks(self) -> list[TaskSummary]:
        return self._client.list_tasks(limit=self._settings.history_limit)

    def approve_patch(self, task_id: str) -> TaskSnapshot:
        return self._client.approve_task(task_id)

    def reject_patch(self, task_id: str) -> TaskSnapshot:
        return self._client.reject_task(task_id)

    def wait_for_terminal(
        self,
        task_id: str,
        *,
        on_update: Callable[[TaskSnapshot], None] | None = None,
    ) -> TaskSnapshot:
        """Poll until the task reaches a terminal status or times out."""

        deadline = time.time() + self._settings.poll_timeout_seconds
        latest = self.fetch_task(task_id)
        if on_update is not None:
            on_update(latest)
        while latest.status not in self.TERMINAL_STATUSES:
            if time.time() >= deadline:
                raise CasiApiError(
                    f"Task {task_id} did not finish within "
                    f"{self._settings.poll_timeout_seconds:.0f}s."
                )
            time.sleep(self._settings.poll_interval_seconds)
            latest = self.fetch_task(task_id)
            if on_update is not None:
                on_update(latest)
        return latest
