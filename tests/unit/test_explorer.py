from pathlib import Path

from casi.repository.explorer import list_files


def test_list_files_returns_relative_paths(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "src").mkdir()
    (repository / "src" / "app.py").write_text("print('ok')", encoding="utf-8")

    result = list_files(repository)

    assert result == [Path("src/app.py")]


def test_list_files_ignores_configured_directories(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "visible.txt").write_text("visible", encoding="utf-8")

    for directory_name in (".git", ".venv", "node_modules", "__pycache__"):
        ignored_directory = repository / directory_name
        ignored_directory.mkdir()
        (ignored_directory / "hidden.txt").write_text("hidden", encoding="utf-8")

    result = list_files(repository)

    assert result == [Path("visible.txt")]


def test_list_files_omits_sensitive_files(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / ".env").write_text("SECRET=value", encoding="utf-8")
    (repository / "credentials.json").write_text("{}", encoding="utf-8")
    (repository / "certificate.pem").write_text("private", encoding="utf-8")
    (repository / "README.md").write_text("safe", encoding="utf-8")

    result = list_files(repository)

    assert result == [Path("README.md")]


def test_list_files_respects_file_limit(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    for index in range(5):
        (repository / f"file_{index}.txt").write_text(str(index), encoding="utf-8")

    result = list_files(repository, max_files=2)

    assert len(result) == 2
    assert result == sorted(result)


def test_list_files_omits_symlink_outside_repository(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("private", encoding="utf-8")
    (repository / "linked.txt").symlink_to(outside)
    (repository / "safe.txt").write_text("safe", encoding="utf-8")

    result = list_files(repository)

    assert result == [Path("safe.txt")]
