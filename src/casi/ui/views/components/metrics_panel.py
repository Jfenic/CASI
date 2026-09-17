"""Metrics summary panel."""

from __future__ import annotations

import streamlit as st

from casi.ui.client.models import TaskSnapshot

_METRIC_LABELS = {
    "total_steps": "Pasos totales",
    "decision_steps": "Decisiones",
    "tool_calls": "Herramientas",
    "files_read": "Archivos leídos",
    "patches_proposed": "Parches",
    "test_runs": "Tests ejecutados",
    "failed_tools": "Herramientas fallidas",
    "prompt_tokens": "Tokens entrada",
    "completion_tokens": "Tokens salida",
    "total_duration_ms": "Duración (ms)",
}


def render_metrics_panel(task: TaskSnapshot) -> None:
    metrics = task.metrics
    if not metrics:
        return

    st.subheader("Métricas")
    items = [
        (_METRIC_LABELS.get(key, key), value)
        for key, value in metrics.items()
        if value not in (None, 0, 0.0, "")
    ]
    if not items:
        st.caption("Sin métricas agregadas todavía.")
        return

    columns = st.columns(min(len(items), 4))
    for index, (label, value) in enumerate(items):
        columns[index % len(columns)].metric(label, value)
