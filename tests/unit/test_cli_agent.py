from __future__ import annotations

import subprocess
from pathlib import Path

from casi.agent.orchestrator import OrchestratorResult
from casi.cli_agent import (
    EXIT_ERROR,
    EXIT_PATCH_PENDING,
    EXIT_SUCCESS,
    finalize_agent_run,
)


def _init_git_repo(path: Path) -> None:
    (path / "module.py").write_text("value = 1\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "CASI Test"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "add", "module.py"], cwd=path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True
    )


_PATCH = (
    "```diff\n"
    "--- a/module.py\n"
    "+++ b/module.py\n"
    "@@ -1 +1 @@\n"
    "-value = 1\n"
    "+value = 2\n"
    "```"
)


def test_finalize_agent_run_prints_text_response(capsys) -> None:
    result = OrchestratorResult(success=True, response="All good")

    exit_code = finalize_agent_run("/tmp", result)

    assert exit_code == EXIT_SUCCESS
    captured = capsys.readouterr()
    assert captured.out.strip() == "All good"
    assert captured.err == ""


def test_finalize_agent_run_rejects_pending_patch(tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    result = OrchestratorResult(success=True, response=_PATCH)

    exit_code = finalize_agent_run(
        repo,
        result,
        input_fn=lambda _prompt: "n",
    )

    assert exit_code == EXIT_PATCH_PENDING
    captured = capsys.readouterr()
    assert "Patch rejected" in captured.err
    assert "value = 2" in captured.out


def test_finalize_agent_run_saves_patch_without_apply(tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    patch_path = tmp_path / "out.patch"

    result = OrchestratorResult(success=True, response=_PATCH)

    exit_code = finalize_agent_run(
        repo,
        result,
        save_patch=str(patch_path),
        input_fn=lambda _prompt: "n",
    )

    assert exit_code == EXIT_SUCCESS
    assert patch_path.read_text(encoding="utf-8").startswith("--- a/module.py")
    captured = capsys.readouterr()
    assert "Patch saved to:" in captured.err


def test_finalize_agent_run_applies_patch_with_yes(tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    result = OrchestratorResult(success=True, response=_PATCH)

    exit_code = finalize_agent_run(repo, result, yes=True)

    assert exit_code == EXIT_SUCCESS
    assert (repo / "module.py").read_text(encoding="utf-8") == "value = 2\n"
    captured = capsys.readouterr()
    assert "Patch applied to: module.py" in captured.err


def test_finalize_agent_run_fails_on_invalid_patch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    result = OrchestratorResult(
        success=True,
        response=(
            "```diff\n--- a/missing.py\n+++ b/missing.py\n@@ -1 +1 @@\n-old\n+new\n```"
        ),
    )

    exit_code = finalize_agent_run(repo, result, yes=True)

    assert exit_code == EXIT_ERROR


def test_finalize_agent_run_reports_agent_failure(capsys) -> None:
    result = OrchestratorResult(success=False, error="boom")

    exit_code = finalize_agent_run("/tmp", result)

    assert exit_code == EXIT_ERROR
    assert "boom" in capsys.readouterr().err
