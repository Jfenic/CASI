from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from casi.sandbox.project_environment import (
    detect_project_environment,
    prepare_project_environment,
    project_image_if_available,
)


def test_requirements_environment_is_content_addressed(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("requests==2.32.0\n", encoding="utf-8")

    first = detect_project_environment(tmp_path)
    assert first is not None
    assert first.manager == "pip-requirements"
    assert first.dependency_files == ("requirements.txt",)
    assert first.image.startswith("casi-project-env:")

    requirements.write_text("requests==2.33.0\n", encoding="utf-8")
    second = detect_project_environment(tmp_path)
    assert second is not None
    assert second.image != first.image


def test_lock_file_selects_uv_strategy(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\n", encoding="utf-8"
    )
    (tmp_path / "uv.lock").write_text("version = 1\n", encoding="utf-8")

    environment = detect_project_environment(tmp_path)

    assert environment is not None
    assert environment.manager == "uv"
    assert environment.dependency_files == ("pyproject.toml", "uv.lock")


def test_prepare_builds_sanitized_context(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.32.0\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
    observed: dict[str, object] = {}

    def fake_run(command, **kwargs):
        context = Path(kwargs["cwd"])
        observed["command"] = command
        observed["has_app"] = (context / "app.py").exists()
        observed["has_secret"] = (context / ".env").exists()
        observed["dockerfile"] = (context / "Dockerfile.casi").read_text(
            encoding="utf-8"
        )
        return SimpleNamespace(returncode=0, stdout="built", stderr="")

    monkeypatch.setattr(
        "casi.sandbox.project_environment.shutil.which", lambda _: "/usr/bin/docker"
    )
    monkeypatch.setattr("casi.sandbox.project_environment.subprocess.run", fake_run)

    result = prepare_project_environment(tmp_path)

    assert result.success is True
    assert observed["has_app"] is True
    assert observed["has_secret"] is False
    assert "pip install pytest -r requirements.txt" in str(observed["dockerfile"])
    assert observed["command"][0:2] == ("docker", "build")


def test_project_image_must_exist_locally(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    monkeypatch.setattr(
        "casi.sandbox.project_environment.shutil.which", lambda _: "/usr/bin/docker"
    )
    monkeypatch.setattr(
        "casi.sandbox.project_environment.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    image = project_image_if_available(tmp_path)

    assert image is not None
    assert image.startswith("casi-project-env:")
