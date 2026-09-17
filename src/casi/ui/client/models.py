"""Data transfer objects for the CASI API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class TaskSummary:
    id: str
    repository: str
    task: str
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> TaskSummary:
        return cls(
            id=str(payload["id"]),
            repository=str(payload["repository"]),
            task=str(payload["task"]),
            status=str(payload["status"]),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )


@dataclass(frozen=True)
class CreateTaskPayload:
    repository: str
    task: str
    routing: str = "assist"
    max_steps: int | None = None

    def to_json(self) -> dict[str, object]:
        body: dict[str, object] = {
            "repository": self.repository,
            "task": self.task,
            "routing": self.routing,
        }
        if self.max_steps is not None:
            body["max_steps"] = self.max_steps
        return body


@dataclass(frozen=True)
class TaskSnapshot:
    id: str
    repository: str
    task: str
    status: str
    created_at: datetime
    updated_at: datetime
    routing: str
    max_steps: int | None
    response: str
    error: str | None
    clarification: str | None
    patch: str | None
    patch_files: list[str]
    patch_error: str | None
    tests_passed: bool | None
    test_output: str | None
    test_runner: str | None
    applied_files: list[str]
    plan: list[str]
    trace: list[str]
    metrics: dict[str, object]
    execution: dict[str, object]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> TaskSnapshot:
        return cls(
            id=str(payload["id"]),
            repository=str(payload["repository"]),
            task=str(payload["task"]),
            status=str(payload["status"]),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
            routing=str(payload.get("routing", "assist")),
            max_steps=payload.get("max_steps"),
            response=str(payload.get("response", "")),
            error=payload.get("error"),
            clarification=payload.get("clarification"),
            patch=payload.get("patch"),
            patch_files=list(payload.get("patch_files") or []),
            patch_error=payload.get("patch_error"),
            tests_passed=payload.get("tests_passed"),
            test_output=payload.get("test_output"),
            test_runner=payload.get("test_runner"),
            applied_files=list(payload.get("applied_files") or []),
            plan=list(payload.get("plan") or []),
            trace=list(payload.get("trace") or []),
            metrics=dict(payload.get("metrics") or {}),
            execution=dict(payload.get("execution") or {}),
        )

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            "completed",
            "failed",
            "cancelled",
            "awaiting_approval",
        }

    @property
    def is_running(self) -> bool:
        return self.status in {"pending", "running"}

    @property
    def files_read(self) -> list[str]:
        raw = self.execution.get("files_read")
        if isinstance(raw, list):
            return [str(path) for path in raw]
        return []

    @property
    def execution_steps(self) -> list[dict[str, object]]:
        raw = self.execution.get("steps")
        if isinstance(raw, list):
            return [dict(step) for step in raw if isinstance(step, dict)]
        return []

    @property
    def test_runs(self) -> list[dict[str, object]]:
        raw = self.execution.get("test_runs")
        if isinstance(raw, list):
            return [dict(item) for item in raw if isinstance(item, dict)]
        return []
