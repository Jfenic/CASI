"""FastAPI dependencies."""

from __future__ import annotations

from fastapi import Request

from casi.api.tasks import TaskStore


def get_task_store(request: Request) -> TaskStore:
	"""Return the application-wide task store."""

	return request.app.state.task_store
