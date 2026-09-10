from __future__ import annotations

import subprocess
import sys


def test_tool_registry_imports_in_fresh_interpreter() -> None:
    """Import order must not create a registry/agent dependency cycle."""

    result = subprocess.run(
        [sys.executable, "-c", "from casi.tools.registry import ToolRegistry"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_agent_package_keeps_public_exports() -> None:
    """Lazy loading must preserve imports supported by the package API."""

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from casi.agent import AgentLoop, PermissionTier",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
