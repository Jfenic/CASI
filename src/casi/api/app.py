"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from casi.api.routes import router
from casi.api.tasks import TaskStore


def create_app(*, task_store: TaskStore | None = None) -> FastAPI:
	"""Build the CASI HTTP application."""

	app = FastAPI(
		title="CASI",
		description=(
			"Local code agent API for repository tasks, patch proposals, "
			"and human-approved writes."
		),
		version="0.1.0",
	)
	app.state.task_store = task_store or TaskStore()
	app.include_router(router)
	return app
