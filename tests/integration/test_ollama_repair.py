"""Opt-in end-to-end repair tests using a real Ollama model."""

from __future__ import annotations

import pytest

from casi.agent.loop import AgentLoop
from casi.llm.ollama_client import OllamaClient
from casi.patching.extract import extract_patch
from casi.tools.registry import ToolRegistry


@pytest.mark.ollama
def test_repair_invalid_email_fixture_with_ollama(
    invalid_email_repo,
    ollama_available,
) -> None:
    """Repair the bundled invalid-email fixture with the configured Ollama model."""

    loop = AgentLoop(
        OllamaClient(),
        ToolRegistry(invalid_email_repo),
        max_steps=12,
        max_correction_attempts=2,
    )
    result = loop.run(
        "Fix validate_email so emails without @ are rejected and tests pass."
    )

    assert result.requested_code_change is True
    patch = extract_patch(result.response)
    assert result.success, result.error or result.response
    assert patch is not None, result.response
    assert result.patch_verification is not None, result.response
    assert result.patch_verification.passed, result.patch_verification.output
