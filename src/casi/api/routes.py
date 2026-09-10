"""HTTP route definitions."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from casi.api.dependencies import get_task_store
from casi.api.schemas import (
    CreateTaskRequest,
    ErrorResponse,
    HealthResponse,
    TaskResponse,
)
from casi.api.tasks import TaskStateError, TaskStore
from casi.exceptions import CasiError

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse()


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
    tags=["tasks"],
)
def create_task(
    body: CreateTaskRequest,
    store: Annotated[TaskStore, Depends(get_task_store)],
) -> TaskResponse:
    try:
        record = store.create(
            body.repository,
            body.task,
            routing=body.routing,
            max_steps=body.max_steps,
        )
    except CasiError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except (FileNotFoundError, IsADirectoryError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return TaskResponse.from_record(record)


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["tasks"],
)
def get_task(
    task_id: str,
    store: Annotated[TaskStore, Depends(get_task_store)],
) -> TaskResponse:
    record = store.get(task_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} was not found.",
        )
    return TaskResponse.from_record(record)


@router.post(
    "/tasks/{task_id}/approve",
    response_model=TaskResponse,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    tags=["tasks"],
)
def approve_task(
    task_id: str,
    store: Annotated[TaskStore, Depends(get_task_store)],
) -> TaskResponse:
    try:
        record = store.approve(task_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} was not found.",
        ) from exc
    except TaskStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return TaskResponse.from_record(record)


@router.post(
    "/tasks/{task_id}/reject",
    response_model=TaskResponse,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    tags=["tasks"],
)
def reject_task(
    task_id: str,
    store: Annotated[TaskStore, Depends(get_task_store)],
) -> TaskResponse:
    try:
        record = store.reject(task_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} was not found.",
        ) from exc
    except TaskStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return TaskResponse.from_record(record)
