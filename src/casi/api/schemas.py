"""Pydantic schemas for the HTTP API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from casi.api.tasks import TaskRecord, TaskStatus


class HealthResponse(BaseModel):
	status: str = "ok"


class CreateTaskRequest(BaseModel):
	repository: str = Field(..., description="Absolute or relative path to the repository.")
	task: str = Field(..., min_length=1, description="Task description for the agent.")
	routing: str = Field(default="assist", pattern="^(assist|strict|off)$")
	max_steps: int | None = Field(default=None, ge=1)


class TaskResponse(BaseModel):
	id: str
	repository: str
	task: str
	status: TaskStatus
	created_at: datetime
	updated_at: datetime
	routing: str
	max_steps: int | None = None
	response: str = ""
	error: str | None = None
	clarification: str | None = None
	patch: str | None = None
	patch_files: list[str] = Field(default_factory=list)
	patch_error: str | None = None
	tests_passed: bool | None = None
	test_output: str | None = None
	test_runner: str | None = None
	applied_files: list[str] = Field(default_factory=list)
	plan: list[str] = Field(default_factory=list)
	trace: list[str] = Field(default_factory=list)
	metrics: dict[str, object] = Field(default_factory=dict)
	execution: dict[str, object] = Field(default_factory=dict)

	@classmethod
	def from_record(cls, record: TaskRecord) -> TaskResponse:
		return cls(
			id=record.id,
			repository=record.repository,
			task=record.task,
			status=record.status,
			created_at=record.created_at,
			updated_at=record.updated_at,
			routing=record.routing,
			max_steps=record.max_steps,
			response=record.response,
			error=record.error,
			clarification=record.clarification,
			patch=record.patch,
			patch_files=record.patch_files,
			patch_error=record.patch_error,
			tests_passed=record.tests_passed,
			test_output=record.test_output,
			test_runner=record.test_runner,
			applied_files=record.applied_files,
			plan=record.plan,
			trace=record.trace,
			metrics=record.metrics,
			execution=record.execution,
		)


class ErrorResponse(BaseModel):
	detail: str
