"""Task status header."""

from __future__ import annotations

import streamlit as st

from casi.ui.client.models import TaskSnapshot

_STATUS_LABELS = {
    "pending": "Pendiente",
    "running": "En ejecución",
    "patch_proposed": "Parche propuesto",
    "awaiting_approval": "Esperando aprobación",
    "completed": "Completada",
    "failed": "Fallida",
    "cancelled": "Cancelada",
}


def render_task_status(task: TaskSnapshot) -> None:
    label = _STATUS_LABELS.get(task.status, task.status)
    st.subheader(f"Tarea · {label}")
    cols = st.columns(4)
    cols[0].metric("Estado", label)
    cols[1].metric("Repositorio", _short_path(task.repository))
    cols[2].metric("Actualizada", task.updated_at.strftime("%H:%M:%S"))
    cols[3].metric("Eventos", len(task.trace))
    st.markdown("**Instrucción**")
    st.write(task.task)

    with st.expander("Ruta completa del repositorio", expanded=task.is_running):
        st.code(task.repository, language="text")

    if task.plan:
        with st.expander("Plan", expanded=False):
            for index, step in enumerate(task.plan, start=1):
                st.markdown(f"{index}. {step}")


def _short_path(path: str, *, max_length: int = 42) -> str:
    if len(path) <= max_length:
        return path
    return f"...{path[-(max_length - 3) :]}"
