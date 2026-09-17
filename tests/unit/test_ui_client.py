from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from casi.agent.orchestrator import OrchestratorResult
from casi.api.app import create_app
from casi.api.tasks import TaskStatus, TaskStore
from casi.ui.client.http_client import HttpCasiApiClient
from casi.ui.client.models import CreateTaskPayload, TaskSnapshot
from casi.ui.client.protocol import CasiApiClient, CasiApiError
from casi.ui.config import UISettings
from casi.ui.services.task_service import TaskService


def _runner(
    _repository: Path,
    _task: str,
    _max_steps: int | None,
    _routing: str,
    _trace=None,
) -> OrchestratorResult:
    return OrchestratorResult(success=True, response="Done")


class FastApiClientAdapter:
    """Adapter that implements the UI client port over FastAPI TestClient."""

    def __init__(self, client: TestClient) -> None:
        self._client = client

    def health(self) -> bool:
        response = self._client.get("/health")
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

    def list_tasks(self, *, limit: int = 50) -> list:
        response = self._client.get("/tasks", params={"limit": limit})
        body = self._parse_json(response)
        tasks = body.get("tasks")
        if not isinstance(tasks, list):
            raise CasiApiError("Unexpected task list payload.")
        from casi.ui.client.models import TaskSummary

        return [TaskSummary.from_payload(item) for item in tasks]

    def approve_task(self, task_id: str) -> TaskSnapshot:
        response = self._client.post(f"/tasks/{task_id}/approve")
        return self._parse_task_response(response)

    def reject_task(self, task_id: str) -> TaskSnapshot:
        response = self._client.post(f"/tasks/{task_id}/reject")
        return self._parse_task_response(response)

    def _parse_task_response(self, response) -> TaskSnapshot:
        return TaskSnapshot.from_payload(self._parse_json(response))

    def _parse_json(self, response) -> dict:
        if response.status_code >= 400:
            payload = response.json()
            detail = payload.get("detail") if isinstance(payload, dict) else None
            raise CasiApiError(str(detail or "request failed"))
        return response.json()


@pytest.fixture
def api_client() -> CasiApiClient:
    store = TaskStore(runner=_runner)
    client = TestClient(create_app(task_store=store))
    return FastApiClientAdapter(client)


def test_http_client_health(api_client: CasiApiClient) -> None:
    assert api_client.health() is True


def test_http_client_create_and_get_task(
    api_client: CasiApiClient, tmp_path: Path
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    created = api_client.create_task(
        CreateTaskPayload(repository=str(repo), task="Explain structure")
    )
    latest = api_client.get_task(created.id)
    assert latest.status == TaskStatus.COMPLETED.value
    assert latest.response == "Done"
    assert latest.metrics


def test_http_client_list_tasks(api_client: CasiApiClient, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    api_client.create_task(CreateTaskPayload(repository=str(repo), task="One"))
    api_client.create_task(CreateTaskPayload(repository=str(repo), task="Two"))

    summaries = api_client.list_tasks(limit=10)
    assert len(summaries) == 2
    assert summaries[0].task == "Two"


def test_http_client_surfaces_api_errors(api_client: CasiApiClient) -> None:
    with pytest.raises(CasiApiError, match="not found"):
        api_client.get_task("missing")


def test_http_client_extract_error_detail() -> None:
    response = httpx.Response(404, json={"detail": "Task missing was not found."})
    detail = HttpCasiApiClient._extract_error_detail(response)
    assert "missing" in detail


def test_task_snapshot_parses_execution_fields() -> None:
    snapshot = TaskSnapshot.from_payload(
        {
            "id": "abc",
            "repository": "/tmp/repo",
            "task": "Inspect",
            "status": "completed",
            "created_at": "2026-09-14T10:00:00+00:00",
            "updated_at": "2026-09-14T10:00:05+00:00",
            "routing": "assist",
            "max_steps": 12,
            "response": "ok",
            "execution": {
                "files_read": ["src/app.py"],
                "steps": [{"step": 1, "tool": "read_file"}],
                "test_runs": [{"passed": True, "runner": "docker"}],
            },
        }
    )

    assert snapshot.files_read == ["src/app.py"]
    assert snapshot.execution_steps[0]["tool"] == "read_file"
    assert snapshot.test_runs[0]["runner"] == "docker"
    assert snapshot.is_terminal is True


def test_task_service_wait_for_terminal(
    api_client: CasiApiClient, tmp_path: Path
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    settings = UISettings(
        api_base_url="http://testserver",
        poll_interval_seconds=0.01,
        poll_timeout_seconds=2.0,
        history_limit=10,
        page_title="CASI",
        page_icon="",
    )
    service = TaskService(api_client, settings)
    created = service.submit_task(
        CreateTaskPayload(repository=str(repo), task="Finish quickly")
    )
    final = service.wait_for_terminal(created.id)
    assert final.status == TaskStatus.COMPLETED.value
