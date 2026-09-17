"""Configuration for the Streamlit UI."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class UISettings:
    """Runtime settings for the visual interface."""

    api_base_url: str
    poll_interval_seconds: float
    poll_timeout_seconds: float
    history_limit: int
    page_title: str
    page_icon: str

    @classmethod
    def from_env(cls) -> UISettings:
        return cls(
            api_base_url=os.getenv("CASI_API_URL", "http://127.0.0.1:8000").rstrip("/"),
            poll_interval_seconds=float(os.getenv("CASI_UI_POLL_INTERVAL", "0.75")),
            poll_timeout_seconds=float(os.getenv("CASI_UI_POLL_TIMEOUT", "600")),
            history_limit=int(os.getenv("CASI_UI_HISTORY_LIMIT", "50")),
            page_title=os.getenv("CASI_UI_PAGE_TITLE", "CASI"),
            page_icon=os.getenv("CASI_UI_PAGE_ICON", "🛠️"),
        )
