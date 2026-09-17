from __future__ import annotations

from datetime import UTC, datetime

from casi.ui.client.models import TaskSnapshot
from casi.ui.services.progress_interpreter import interpret_progress


def _task(**overrides) -> TaskSnapshot:
    base = {
        "id": "abc",
        "repository": "/tmp/demo",
        "task": "Explain the repository",
        "status": "running",
        "created_at": "2026-09-14T10:00:00+00:00",
        "updated_at": "2026-09-14T10:00:05+00:00",
        "routing": "assist",
        "max_steps": 12,
        "response": "",
    }
    base.update(overrides)
    return TaskSnapshot.from_payload(base)


def test_interpret_progress_for_pending_task() -> None:
    view = interpret_progress(
        _task(status="pending", trace=[]),
        now=datetime(2026, 9, 14, 10, 0, 2, tzinfo=UTC),
    )

    assert view.headline == "En cola"
    assert "repositorio" in view.next_step.lower()


def test_interpret_progress_for_read_file_event() -> None:
    view = interpret_progress(
        _task(trace=["decision 2/12: tool read_file path='src/app.py'"]),
        now=datetime(2026, 9, 14, 10, 0, 10, tzinfo=UTC),
    )

    assert view.headline == "Leyendo código"
    assert view.step_label == "Paso 2 de 12"


def test_interpret_progress_for_awaiting_approval() -> None:
    view = interpret_progress(
        _task(status="awaiting_approval", trace=["decision 8/12: final done"]),
    )

    assert view.headline == "Esperando tu revisión"
    assert "aprueba" in view.next_step.lower()
