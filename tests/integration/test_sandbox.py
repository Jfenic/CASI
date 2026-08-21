from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from casi.sandbox.docker_runner import DockerRunner
from casi.sandbox.local_runner import LocalRunner


def test_local_runner_executes_command_in_repository(tmp_path: Path) -> None:
    result = LocalRunner().run(
        tmp_path,
        [sys.executable, "-c", "print('sandbox-ok')"],
    )

    assert result.exit_code == 0
    assert "sandbox-ok" in result.stdout
    assert result.timed_out is False


@pytest.mark.skipif(shutil.which("docker") is None, reason="Docker not installed")
def test_docker_runner_executes_command_when_available() -> None:
    runner = DockerRunner()
    if not runner.is_available():
        pytest.skip("Docker daemon is not available")

    result = runner.run(
        Path("."),
        ["python", "-c", "print('docker-ok')"],
        timeout_seconds=30,
    )

    assert result.timed_out is False
    assert result.exit_code == 0
    assert "docker-ok" in result.stdout
