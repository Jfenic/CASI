"""Sidebar connection and environment panel."""

from __future__ import annotations

import streamlit as st

from casi.config import settings as casi_settings
from casi.ui.config import UISettings
from casi.ui.services.task_service import TaskService


def render_connection_panel(
    *,
    ui_settings: UISettings,
    task_service: TaskService,
) -> None:
    st.subheader("Conexión")
    st.text_input("API base URL", value=ui_settings.api_base_url, disabled=True)
    healthy = task_service.check_connection()
    if healthy:
        st.success("API disponible")
    else:
        st.error("No se puede contactar con la API. Ejecuta `casi serve`.")

    with st.expander("Entorno del agente", expanded=False):
        st.caption(f"Modelo Ollama: `{casi_settings.ollama_model}`")
        st.caption(f"URL Ollama: `{casi_settings.ollama_base_url}`")
        st.caption(
            "Docker sandbox: "
            f"{'activado' if casi_settings.use_docker_sandbox else 'desactivado'}"
        )
        st.caption(
            "Fallback local: "
            f"{'permitido' if casi_settings.allow_local_test_fallback else 'bloqueado'}"
        )
