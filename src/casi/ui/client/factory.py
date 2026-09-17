"""Factory helpers for UI clients."""

from __future__ import annotations

from casi.ui.client.http_client import HttpCasiApiClient
from casi.ui.client.protocol import CasiApiClient
from casi.ui.config import UISettings


def create_api_client(settings: UISettings) -> CasiApiClient:
    """Build the default HTTP client for the configured API base URL."""

    return HttpCasiApiClient(settings.api_base_url)
