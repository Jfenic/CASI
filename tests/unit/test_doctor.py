from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from casi.doctor import (
    check_docker_sandbox,
    check_git_workspace,
    check_ollama,
    check_openai,
    check_python_runtime,
    run_doctor,
)


def test_check_python_runtime() -> None:
    result = check_python_runtime()
    assert result.passed is True
    assert "Python" in result.message


def test_check_git_workspace(tmp_path: Path) -> None:
    non_existent = tmp_path / "does_not_exist"
    res_fail = check_git_workspace(non_existent)
    assert res_fail.passed is False

    repo = tmp_path / "valid_dir"
    repo.mkdir()
    res_ok = check_git_workspace(repo)
    assert res_ok.passed is True


def test_check_ollama_success() -> None:
    mock_payload = json.dumps({"models": [{"name": "qwen2.5-coder:7b"}]}).encode(
        "utf-8"
    )
    mock_response = io.BytesIO(mock_payload)

    with patch("casi.doctor.urlopen", return_value=mock_response):
        checks = check_ollama(model="qwen2.5-coder:7b")
        assert len(checks) == 2
        assert checks[0].passed is True
        assert "Online" in checks[0].message
        assert checks[1].passed is True
        assert "available" in checks[1].message


def test_check_ollama_missing_model() -> None:
    mock_payload = json.dumps({"models": [{"name": "llama3:latest"}]}).encode("utf-8")
    mock_response = io.BytesIO(mock_payload)

    with patch("casi.doctor.urlopen", return_value=mock_response):
        checks = check_ollama(model="qwen2.5-coder:7b")
        assert checks[0].passed is True
        assert checks[1].passed is False
        assert "not found" in checks[1].message
        assert "ollama pull" in str(checks[1].hint)


def test_check_ollama_offline() -> None:
    with patch("casi.doctor.urlopen", side_effect=URLError("Connection refused")):
        checks = check_ollama(model="qwen2.5-coder:7b")
        assert len(checks) == 2
        assert checks[0].passed is False
        assert checks[1].passed is False
        assert "ollama serve" in str(checks[0].hint)


def test_check_openai() -> None:
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-123"}):
        res = check_openai()
        assert res.passed is True

    with patch.dict("os.environ", {}, clear=True):
        res = check_openai()
        assert res.passed is False
        assert "OPENAI_API_KEY" in str(res.hint)


def test_check_docker_sandbox_disabled() -> None:
    checks = check_docker_sandbox(use_sandbox=False)
    assert len(checks) == 1
    assert checks[0].passed is True


def test_check_docker_sandbox_active() -> None:
    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        patch("subprocess.run") as mock_run,
    ):
        # First call: docker info -> returncode 0
        # Second call: docker image inspect -> returncode 0
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=0),
        ]
        checks = check_docker_sandbox(use_sandbox=True)
        assert len(checks) == 2
        assert checks[0].passed is True
        assert checks[1].passed is True


def test_run_doctor_all_passed(tmp_path: Path) -> None:
    output: list[str] = []
    with patch("casi.doctor.collect_diagnostics") as mock_collect:
        from casi.doctor import DiagnosticCheck

        mock_collect.return_value = [
            DiagnosticCheck(name="Python", passed=True, message="Python 3.12"),
            DiagnosticCheck(name="Docker", passed=True, message="Running"),
        ]

        success = run_doctor(tmp_path, output_fn=output.append)
        assert success is True
        assert any("All checks passed" in line for line in output)
        assert any("Python" in line for line in output)


def test_run_doctor_with_failures(tmp_path: Path) -> None:
    output: list[str] = []
    with patch("casi.doctor.collect_diagnostics") as mock_collect:
        from casi.doctor import DiagnosticCheck

        mock_collect.return_value = [
            DiagnosticCheck(name="Python", passed=True, message="Python 3.12"),
            DiagnosticCheck(
                name="Docker",
                passed=False,
                message="Offline",
                hint="Start docker service",
            ),
        ]

        success = run_doctor(tmp_path, output_fn=output.append)
        assert success is False
        assert any("Start docker service" in line for line in output)
