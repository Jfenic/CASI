from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from casi.agent.orchestrator import OrchestratorResult
from casi.api.app import create_app
from casi.api.tasks import TaskStatus, TaskStore


def _init_git_repo(path: Path) -> None:
	(path / "module.py").write_text("value = 1\n", encoding="utf-8")
	subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
	subprocess.run(
		["git", "config", "user.email", "test@example.com"],
		cwd=path,
		check=True,
		capture_output=True,
	)
	subprocess.run(
		["git", "config", "user.name", "CASI Test"],
		cwd=path,
		check=True,
		capture_output=True,
	)
	subprocess.run(["git", "add", "module.py"], cwd=path, check=True, capture_output=True)
	subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)


_PATCH = (
	"```diff\n"
	"--- a/module.py\n"
	"+++ b/module.py\n"
	"@@ -1 +1 @@\n"
	"-value = 1\n"
	"+value = 2\n"
	"```"
)


def _wait_for_status(client: TestClient, task_id: str, status: TaskStatus, *, timeout: float = 2.0) -> dict:
	deadline = time.time() + timeout
	while time.time() < deadline:
		response = client.get(f"/tasks/{task_id}")
		assert response.status_code == 200
		payload = response.json()
		if payload["status"] == status.value:
			return payload
		time.sleep(0.01)
	raise AssertionError(f"Task {task_id} did not reach status {status.value}")


@pytest.fixture
def text_task_client() -> TestClient:
	def runner(
		_repository: Path,
		_task: str,
		_max_steps: int | None,
		_routing: str,
		_trace=None,
	) -> OrchestratorResult:
		return OrchestratorResult(success=True, response="Task completed")

	store = TaskStore(runner=runner)
	return TestClient(create_app(task_store=store))


def test_health_endpoint(text_task_client: TestClient) -> None:
	response = text_task_client.get("/health")

	assert response.status_code == 200
	assert response.json() == {"status": "ok"}


def test_create_and_get_task(text_task_client: TestClient, tmp_path: Path) -> None:
	repo = tmp_path / "repo"
	repo.mkdir()

	create_response = text_task_client.post(
		"/tasks",
		json={"repository": str(repo), "task": "Explain the repository"},
	)
	assert create_response.status_code == 201
	payload = create_response.json()
	task_id = payload["id"]

	final = _wait_for_status(text_task_client, task_id, TaskStatus.COMPLETED)
	assert final["response"] == "Task completed"
	assert final["metrics"]


def test_create_task_rejects_missing_repository(text_task_client: TestClient) -> None:
	response = text_task_client.post(
		"/tasks",
		json={"repository": "/does/not/exist", "task": "Inspect"},
	)

	assert response.status_code == 400
	assert "detail" in response.json()


def test_get_task_not_found(text_task_client: TestClient) -> None:
	response = text_task_client.get("/tasks/missing")

	assert response.status_code == 404


def test_patch_approve_and_reject_flow(tmp_path: Path) -> None:
	repo = tmp_path / "repo"
	repo.mkdir()
	_init_git_repo(repo)

	def runner(
		_repository: Path,
		_task: str,
		_max_steps: int | None,
		_routing: str,
		_trace=None,
	) -> OrchestratorResult:
		return OrchestratorResult(success=True, response=_PATCH)

	client = TestClient(create_app(task_store=TaskStore(runner=runner)))

	create_response = client.post(
		"/tasks",
		json={"repository": str(repo), "task": "Fix module"},
	)
	task_id = create_response.json()["id"]
	awaiting = _wait_for_status(client, task_id, TaskStatus.AWAITING_APPROVAL)
	assert awaiting["patch"] is not None
	assert awaiting["patch_files"] == ["module.py"]

	reject_response = client.post(f"/tasks/{task_id}/reject")
	assert reject_response.status_code == 200
	assert reject_response.json()["status"] == TaskStatus.CANCELLED.value

	create_response = client.post(
		"/tasks",
		json={"repository": str(repo), "task": "Fix module again"},
	)
	task_id = create_response.json()["id"]
	_wait_for_status(client, task_id, TaskStatus.AWAITING_APPROVAL)

	approve_response = client.post(f"/tasks/{task_id}/approve")
	assert approve_response.status_code == 200
	approved = approve_response.json()
	assert approved["status"] == TaskStatus.COMPLETED.value
	assert approved["applied_files"] == ["module.py"]
	assert (repo / "module.py").read_text(encoding="utf-8") == "value = 2\n"


def test_approve_conflict_when_not_awaiting(text_task_client: TestClient, tmp_path: Path) -> None:
	repo = tmp_path / "repo"
	repo.mkdir()

	create_response = text_task_client.post(
		"/tasks",
		json={"repository": str(repo), "task": "Explain"},
	)
	task_id = create_response.json()["id"]
	_wait_for_status(text_task_client, task_id, TaskStatus.COMPLETED)

	response = text_task_client.post(f"/tasks/{task_id}/approve")

	assert response.status_code == 409
