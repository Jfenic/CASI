"""Trace and execution steps panel."""

from __future__ import annotations

import streamlit as st

from casi.ui.client.models import TaskSnapshot


def render_trace_panel(task: TaskSnapshot) -> None:
    st.subheader("Pasos del agente")

    files_read = task.files_read
    if files_read:
        st.markdown("**Archivos leídos**")
        st.code("\n".join(files_read), language="text")

    steps = task.execution_steps
    if steps:
        st.markdown("**Pasos estructurados**")
        st.dataframe(steps, use_container_width=True, hide_index=True)

    if task.trace:
        st.markdown("**Traza**")
        st.text("\n".join(task.trace))
    elif not steps and not files_read:
        st.caption("Todavía no hay pasos registrados para esta tarea.")
