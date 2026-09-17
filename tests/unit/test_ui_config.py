"""Tests for UI configuration defaults."""

from __future__ import annotations

from casi.ui.config import UISettings


def test_ui_settings_from_env_defaults(monkeypatch) -> None:
    monkeypatch.delenv("CASI_API_URL", raising=False)
    settings = UISettings.from_env()

    assert settings.api_base_url == "http://127.0.0.1:8000"
    assert settings.poll_interval_seconds == 0.75
    assert settings.history_limit == 50
