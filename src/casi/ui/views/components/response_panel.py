"""Agent response and test output panel."""

from __future__ import annotations

import streamlit as st

from casi.ui.client.models import TaskSnapshot


def render_response_panel(task: TaskSnapshot) -> None:
    if task.error:
        st.error(task.error)
    if task.clarification:
        st.warning(f"Clarificación requerida: {task.clarification}")

    if task.response:
        st.subheader("Respuesta del agente")
        st.markdown(task.response)

    if task.tests_passed is not None or task.test_output or task.test_runs:
        st.subheader("Resultado de tests")
        if task.tests_passed is True:
            st.success("Tests superados en sandbox")
        elif task.tests_passed is False:
            st.error("Tests fallidos en sandbox")
        if task.test_runner:
            st.caption(f"Runner: `{task.test_runner}`")
        if task.test_output:
            st.code(task.test_output, language="text")
        for index, run in enumerate(task.test_runs, start=1):
            with st.expander(f"Ejecución de test #{index}", expanded=False):
                st.json(run)

    if task.applied_files:
        st.success("Archivos aplicados: " + ", ".join(task.applied_files))
