"""Main page layout orchestrator."""

from __future__ import annotations

import streamlit as st

from casi.ui.client.protocol import CasiApiError
from casi.ui.config import UISettings
from casi.ui.services.session_store import SessionStore
from casi.ui.services.task_service import TaskService
from casi.ui.views.components.connection import render_connection_panel
from casi.ui.views.components.history import render_history_panel
from casi.ui.views.components.metrics_panel import render_metrics_panel
from casi.ui.views.components.patch_panel import render_patch_panel
from casi.ui.views.components.progress_panel import (
    render_execution_context,
    render_progress_panel,
)
from casi.ui.views.components.response_panel import render_response_panel
from casi.ui.views.components.task_form import render_task_form
from casi.ui.views.components.task_status import render_task_status
from casi.ui.views.components.trace_panel import render_trace_panel


def render_app(
    *,
    ui_settings: UISettings,
    task_service: TaskService,
    session: SessionStore,
) -> None:
    st.set_page_config(
        page_title=ui_settings.page_title,
        page_icon=ui_settings.page_icon,
        layout="wide",
    )
    st.title("CASI — interfaz visual")
    st.caption(
        "Revisa pasos, parches y tests del agente. "
        "La API debe estar en ejecución (`casi serve`)."
    )

    with st.sidebar:
        render_connection_panel(ui_settings=ui_settings, task_service=task_service)
        session.auto_refresh = st.toggle(
            "Actualizar tarea activa",
            value=session.auto_refresh,
        )
        try:
            history = task_service.list_recent_tasks()
        except CasiApiError as exc:
            history = []
            st.warning(str(exc))
        render_history_panel(tasks=history, session=session)

    payload = render_task_form()
    if payload is not None:
        _handle_submit(task_service=task_service, session=session, payload=payload)

    task_id = session.selected_task_id
    if task_id is None:
        st.info("Crea una tarea o selecciona una del historial.")
        return

    task = _load_task(task_service=task_service, task_id=task_id)
    if task is None:
        return

    render_execution_context(task, ui_settings=ui_settings)
    render_progress_panel(task)
    render_task_status(task)
    tab_response, tab_trace, tab_patch, tab_metrics = st.tabs(
        ["Respuesta", "Pasos", "Parche", "Métricas"]
    )
    with tab_response:
        render_response_panel(task)
    with tab_trace:
        render_trace_panel(task)
    with tab_patch:
        render_patch_panel(
            task,
            on_approve=lambda: _handle_patch_action(
                task_service=task_service,
                session=session,
                task_id=task_id,
                action="approve",
            ),
            on_reject=lambda: _handle_patch_action(
                task_service=task_service,
                session=session,
                task_id=task_id,
                action="reject",
            ),
        )
    with tab_metrics:
        render_metrics_panel(task)

    if session.auto_refresh and (task.is_running or task.status == "pending"):
        import time

        time.sleep(ui_settings.poll_interval_seconds)
        st.rerun()


def _handle_submit(
    *,
    task_service: TaskService,
    session: SessionStore,
    payload,
) -> None:
    try:
        created = task_service.submit_task(payload)
    except CasiApiError as exc:
        st.error(str(exc))
        return
    session.selected_task_id = created.id
    st.success(f"Tarea creada: `{created.id}`")


def _handle_patch_action(
    *,
    task_service: TaskService,
    session: SessionStore,
    task_id: str,
    action: str,
) -> None:
    try:
        if action == "approve":
            task_service.approve_patch(task_id)
            st.success("Parche aplicado.")
        else:
            task_service.reject_patch(task_id)
            st.info("Parche rechazado.")
    except CasiApiError as exc:
        st.error(str(exc))
        return
    st.rerun()


def _load_task(*, task_service: TaskService, task_id: str):
    try:
        return task_service.fetch_task(task_id)
    except CasiApiError as exc:
        st.error(str(exc))
        return None
