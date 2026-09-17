"""Task history sidebar."""

from __future__ import annotations

import streamlit as st

from casi.ui.client.models import TaskSummary
from casi.ui.services.session_store import SessionStore


def render_history_panel(
    *,
    tasks: list[TaskSummary],
    session: SessionStore,
) -> None:
    st.subheader("Historial")
    if not tasks:
        st.caption("Aún no hay tareas en el servidor.")
        return

    for summary in tasks:
        label = _format_summary_label(summary)
        if st.button(label, key=f"history-{summary.id}", use_container_width=True):
            session.selected_task_id = summary.id


def _format_summary_label(summary: TaskSummary) -> str:
    short_task = summary.task if len(summary.task) <= 48 else f"{summary.task[:45]}..."
    return f"{summary.status} · {short_task}"
