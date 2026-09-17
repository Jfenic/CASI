"""Execution context and live progress panel."""

from __future__ import annotations

import streamlit as st

from casi.config import settings as casi_settings
from casi.ui.client.models import TaskSnapshot
from casi.ui.config import UISettings
from casi.ui.services.progress_interpreter import ProgressView, interpret_progress


def render_execution_context(
    task: TaskSnapshot,
    *,
    ui_settings: UISettings,
) -> None:
    st.subheader("Dónde se ejecuta")
    col_repo, col_api = st.columns(2)
    with col_repo:
        st.markdown("**Repositorio**")
        st.code(task.repository, language="text")
    with col_api:
        st.markdown("**Servicios**")
        st.caption(f"API CASI: `{ui_settings.api_base_url}`")
        st.caption(f"Modelo: `{casi_settings.ollama_model}`")
        st.caption(f"Ollama: `{casi_settings.ollama_base_url}`")

    meta_cols = st.columns(4)
    meta_cols[0].caption(f"Enrutamiento: `{task.routing}`")
    meta_cols[1].caption(
        f"Máx. pasos: `{task.max_steps if task.max_steps is not None else 'perfil'}`"
    )
    meta_cols[2].caption(f"Creada: `{task.created_at.strftime('%H:%M:%S')}`")
    meta_cols[3].caption(f"ID: `{task.id[:8]}...`")


def render_progress_panel(task: TaskSnapshot) -> None:
    progress = interpret_progress(task)

    if task.is_running or task.status == "pending":
        with st.status(progress.headline, expanded=True, state="running"):
            _render_progress_body(task, progress)
        return

    if task.status == "awaiting_approval":
        with st.status(progress.headline, expanded=True, state="complete"):
            _render_progress_body(task, progress)
        return

    if task.status == "failed":
        with st.status(progress.headline, expanded=True, state="error"):
            _render_progress_body(task, progress)
        return

    if task.status == "completed":
        st.success(f"{progress.headline}: {progress.detail}")
        return

    st.info(progress.detail)


def _render_progress_body(task: TaskSnapshot, progress: ProgressView) -> None:
    metric_cols = st.columns(3)
    metric_cols[0].metric("Tiempo transcurrido", f"{progress.elapsed_seconds:.0f}s")
    metric_cols[1].metric("Eventos registrados", len(task.trace))
    if progress.step_label:
        metric_cols[2].metric("Progreso", progress.step_label)
    else:
        metric_cols[2].metric("Estado", task.status)

    st.markdown(f"**Ahora:** {progress.detail}")
    st.markdown(f"**Próximo paso esperado:** {progress.next_step}")

    if progress.recent_events:
        st.markdown("**Actividad reciente**")
        for event in progress.recent_events:
            st.text(f"• {event}")

    st.caption(
        "La vista se actualiza automáticamente mientras la tarea está en ejecución."
    )
