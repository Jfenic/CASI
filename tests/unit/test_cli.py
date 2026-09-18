from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from casi.cli import main
from casi.llm.base import LLMResponse


class FakeOllamaClient:
    def complete(self, messages, tools):
        return LLMResponse.final("Task completed")


def test_cli_inspect_lists_files(tmp_path: Path, capsys) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "README.md").write_text("hello", encoding="utf-8")

    exit_code = main(["inspect", "--repo", str(repository)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Repository:" in output
    assert "README.md" in output


def test_cli_read_prints_numbered_lines(tmp_path: Path, capsys) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "README.md").write_text("alpha\nbeta\n", encoding="utf-8")

    exit_code = main(["read", "--repo", str(repository), "--file", "README.md"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "1: alpha" in output
    assert "2: beta" in output


def test_cli_search_prints_matches(tmp_path: Path, capsys) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "app.py").write_text("safe_path\n", encoding="utf-8")

    exit_code = main(["search", "--repo", str(repository), "--query", "safe_path"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Results (1):" in output
    assert "app.py:1: safe_path" in output


def test_cli_run_executes_agent_task(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setattr("casi.cli.OllamaClient", FakeOllamaClient)

    exit_code = main(
        [
            "run",
            "--repo",
            str(tmp_path),
            "--task",
            "Inspect the repository",
        ]
    )

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "Task completed"


def test_cli_ask_executes_agent_task(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.setattr("casi.cli.OllamaClient", FakeOllamaClient)

    exit_code = main(["ask", "--repo", str(tmp_path), "--task", "Explain the repo"])

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "Task completed"


def test_cli_fix_executes_agent_task(tmp_path: Path, capsys, monkeypatch) -> None:
    from casi.agent.orchestrator import OrchestratorResult

    monkeypatch.setattr(
        "casi.cli.AgentOrchestrator.run",
        lambda self, task, **kwargs: OrchestratorResult(
            success=True, response="Task completed"
        ),
    )

    exit_code = main(["fix", "--repo", str(tmp_path), "--task", "Fix failing tests"])

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "Task completed"


def test_cli_fix_save_patch_writes_file(tmp_path: Path, capsys, monkeypatch) -> None:
    import subprocess

    from casi.agent.orchestrator import OrchestratorResult

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "module.py").write_text("value = 1\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "CASI Test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "add", "module.py"], cwd=repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True
    )

    patch_response = (
        "```diff\n"
        "--- a/module.py\n"
        "+++ b/module.py\n"
        "@@ -1 +1 @@\n"
        "-value = 1\n"
        "+value = 2\n"
        "```"
    )
    monkeypatch.setattr(
        "casi.cli.AgentOrchestrator.run",
        lambda self, task, **kwargs: OrchestratorResult(
            success=True, response=patch_response
        ),
    )
    patch_path = tmp_path / "fix.diff"

    exit_code = main(
        [
            "fix",
            "--repo",
            str(repo),
            "--task",
            "Fix module",
            "--save-patch",
            str(patch_path),
            "--yes",
        ]
    )

    assert exit_code == 0
    assert patch_path.exists()
    assert (repo / "module.py").read_text(encoding="utf-8") == "value = 2\n"
    captured = capsys.readouterr()
    assert "Patch applied to: module.py" in captured.err


def test_cli_help_lists_ask_and_fix(capsys) -> None:
    exit_code = main(["help"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "ask" in output
    assert "fix" in output


def test_cli_test_command(tmp_path: Path, capsys) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert True\n",
        encoding="utf-8",
    )

    exit_code = main(["test", "--repo", str(tmp_path)])

    assert exit_code == 0
    assert "exit_code=0" in capsys.readouterr().out


def test_cli_run_interactive_alias(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("casi.cli.InteractiveSession.run", lambda self: 0)

    exit_code = main(["run", "interactive", "--repo", str(tmp_path)])

    assert exit_code == 0


def test_cli_prepares_environment_with_explicit_approval(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    environment = SimpleNamespace(
        manager="pip-requirements",
        dependency_files=("requirements.txt",),
        image="casi-project-env:abc",
    )
    build_result = SimpleNamespace(
        success=True,
        image=environment.image,
        stdout="",
        stderr="",
        returncode=0,
    )
    monkeypatch.setattr("casi.cli.detect_project_environment", lambda _: environment)
    monkeypatch.setattr("casi.cli.prepare_project_environment", lambda _: build_result)

    exit_code = main(["env", "prepare", "--repo", str(tmp_path), "--yes"])

    assert exit_code == 0
    assert "Prepared image: casi-project-env:abc" in capsys.readouterr().out


def test_cli_help_shows_overview(capsys) -> None:
    exit_code = main(["help"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Comandos principales" in output
    assert "inspect" in output
    assert "interactive" in output


def test_cli_help_shows_command_topic(capsys) -> None:
    exit_code = main(["help", "read"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "casi read" in output
    assert "--file" in output


def test_cli_help_reports_unknown_topic(capsys) -> None:
    exit_code = main(["help", "unknown-command"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Unknown help topic" in output
    assert "Available topics" in output
