"""Task submission form."""

from __future__ import annotations

import streamlit as st

from casi.ui.client.models import CreateTaskPayload


def render_task_form() -> CreateTaskPayload | None:
    st.subheader("Nueva tarea")
    with st.form("create_task_form", clear_on_submit=False):
        repository = st.text_input(
            "Repositorio",
            placeholder="/ruta/al/proyecto",
            help="Ruta absoluta o relativa al repositorio a analizar.",
        )
        task = st.text_area(
            "Instrucción",
            placeholder="Explica la estructura del repositorio o pide una corrección.",
            height=120,
        )
        routing = st.selectbox(
            "Enrutamiento",
            options=("assist", "strict", "off"),
            index=0,
            help="Modo de enrutamiento del agente.",
        )
        max_steps_raw = st.number_input(
            "Máximo de pasos",
            min_value=1,
            max_value=100,
            value=12,
            help=(
                "Límite de decisiones del modelo. "
                "Déjalo en 12 para el valor por defecto."
            ),
        )
        submitted = st.form_submit_button("Ejecutar tarea", type="primary")

    if not submitted:
        return None
    if not repository.strip():
        st.error("Indica la ruta del repositorio.")
        return None
    if not task.strip():
        st.error("Describe la tarea para el agente.")
        return None

    return CreateTaskPayload(
        repository=repository.strip(),
        task=task.strip(),
        routing=routing,
        max_steps=int(max_steps_raw),
    )
