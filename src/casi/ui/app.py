"""Streamlit entrypoint for the CASI visual interface."""

from __future__ import annotations

import streamlit as st

from casi.ui.client.factory import create_api_client
from casi.ui.config import UISettings
from casi.ui.services.session_store import SessionStore
from casi.ui.services.task_service import TaskService
from casi.ui.views.layout import render_app


def main() -> None:
    settings = UISettings.from_env()
    client = create_api_client(settings)
    try:
        task_service = TaskService(client, settings)
        session = SessionStore(st.session_state)
        render_app(ui_settings=settings, task_service=task_service, session=session)
    finally:
        if hasattr(client, "close"):
            client.close()


if __name__ == "__main__":
    main()
