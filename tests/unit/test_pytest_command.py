from __future__ import annotations

import sys
from pathlib import Path

from casi.sandbox.pytest_command import DOCKER_WORKSPACE, pytest_command


def test_pytest_command_uses_host_python_for_local_runner(tmp_path: Path) -> None:
    command = pytest_command(tmp_path, runner="local")

    assert command[0] == sys.executable
    assert command[1:] == [
        "-m",
        "pytest",
        "-q",
        "--rootdir",
        str(tmp_path.resolve()),
        str(tmp_path.resolve()),
    ]


def test_pytest_command_uses_container_paths_for_docker_runner() -> None:
    command = pytest_command("/tmp/example-repo", runner="docker")

    assert command == [
        "python3",
        "-m",
        "pytest",
        "-q",
        "--rootdir",
        DOCKER_WORKSPACE,
        DOCKER_WORKSPACE,
    ]
