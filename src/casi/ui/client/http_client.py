"""HTTP implementation of the CASI API client."""

from __future__ import annotations

from typing import Any

import httpx

from casi.ui.client.models import CreateTaskPayload, TaskSnapshot, TaskSummary
from casi.ui.client.protocol import CasiApiError


class HttpCasiApiClient:
    """Repository-style client backed by httpx."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def health(self) -> bool:
        try:
            response = self._client.get("/health")
        except httpx.HTTPError:
            return False
        if response.status_code != 200:
            return False
        payload = response.json()
        return isinstance(payload, dict) and payload.get("status") == "ok"

    def create_task(self, payload: CreateTaskPayload) -> TaskSnapshot:
        response = self._client.post("/tasks", json=payload.to_json())
        return self._parse_task_response(response)

    def get_task(self, task_id: str) -> TaskSnapshot:
        response = self._client.get(f"/tasks/{task_id}")
        return self._parse_task_response(response)

    def list_tasks(self, *, limit: int = 50) -> list[TaskSummary]:
        response = self._client.get("/tasks", params={"limit": limit})
        payload = self._parse_json(response)
        tasks = payload.get("tasks")
        if not isinstance(tasks, list):
            raise CasiApiError("Unexpected task list payload.")
        return [TaskSummary.from_payload(item) for item in tasks]

    def approve_task(self, task_id: str) -> TaskSnapshot:
        response = self._client.post(f"/tasks/{task_id}/approve")
        return self._parse_task_response(response)

    def reject_task(self, task_id: str) -> TaskSnapshot:
        response = self._client.post(f"/tasks/{task_id}/reject")
        return self._parse_task_response(response)

    def _parse_task_response(self, response: httpx.Response) -> TaskSnapshot:
        payload = self._parse_json(response)
        return TaskSnapshot.from_payload(payload)

    def _parse_json(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            detail = self._extract_error_detail(response)
            raise CasiApiError(detail)
        payload = response.json()
        if not isinstance(payload, dict):
            raise CasiApiError("Unexpected API response format.")
        return payload

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"HTTP {response.status_code}: {response.text.strip() or 'error'}"
        if isinstance(payload, dict) and payload.get("detail"):
            return str(payload["detail"])
        return f"HTTP {response.status_code}: request failed."
