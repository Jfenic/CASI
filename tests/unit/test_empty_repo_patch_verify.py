from __future__ import annotations

from pathlib import Path

from casi.agent.create_workflow import repository_has_test_files


def test_repository_has_test_files_requires_actual_files(tmp_path: Path) -> None:
    # With only pyproject.toml and no test files
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='foo'\n", encoding="utf-8"
    )
    assert repository_has_test_files(tmp_path, require_actual_files=False) is True
    assert repository_has_test_files(tmp_path, require_actual_files=True) is False

    # Now add an actual test file
    (tmp_path / "test_foo.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    assert repository_has_test_files(tmp_path, require_actual_files=True) is True
