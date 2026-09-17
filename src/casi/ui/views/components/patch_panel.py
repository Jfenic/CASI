"""Patch review and approval panel."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from casi.ui.client.models import TaskSnapshot


def render_patch_panel(
    task: TaskSnapshot,
    *,
    on_approve: Callable[[], None],
    on_reject: Callable[[], None],
) -> None:
    if task.patch is None and not task.patch_files:
        return

    st.subheader("Parche propuesto")
    if task.patch_files:
        st.caption("Archivos afectados: " + ", ".join(task.patch_files))
    if task.patch_error:
        st.warning(task.patch_error)

    if task.patch:
        st.code(task.patch, language="diff")

    if task.status == "awaiting_approval":
        col_approve, col_reject = st.columns(2)
        if col_approve.button("Aprobar y aplicar", type="primary"):
            on_approve()
        if col_reject.button("Rechazar parche"):
            on_reject()
