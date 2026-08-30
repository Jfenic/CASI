from __future__ import annotations

from pathlib import Path

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