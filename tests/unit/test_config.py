from __future__ import annotations

from pathlib import Path

from casi.config import Settings, _load_casi_toml


def test_settings_default_values() -> None:
    settings = Settings()
    assert settings.llm_provider in {"ollama", "openai"}
    assert settings.ollama_model
    assert settings.openai_model
    assert settings.max_file_size_bytes == 120_000


def test_load_casi_toml_nonexistent(tmp_path: Path) -> None:
    res = _load_casi_toml(tmp_path / "nonexistent.toml")
    assert res == {}


def test_settings_from_toml_sections(tmp_path: Path) -> None:
    toml_path = tmp_path / "casi.toml"
    toml_path.write_text(
        """
[llm]
provider = "openai"

[openai]
model = "gpt-4o-mini"
api_key = "sk-toml-secret"
base_url = "https://custom.openai.endpoint/v1"
timeout_seconds = 45.0

[ollama]
model = "deepseek-coder:6.7b"
base_url = "http://ollama-server:11434"
timeout_seconds = 60.0
""",
        encoding="utf-8",
    )

    settings = Settings.from_toml(toml_path)
    assert settings.llm_provider == "openai"
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.openai_api_key == "sk-toml-secret"
    assert settings.openai_base_url == "https://custom.openai.endpoint/v1"
    assert settings.openai_timeout_seconds == 45.0
    assert settings.ollama_model == "deepseek-coder:6.7b"
    assert settings.ollama_base_url == "http://ollama-server:11434"
    assert settings.ollama_timeout_seconds == 60.0


def test_settings_from_toml_flat_format(tmp_path: Path) -> None:
    toml_path = tmp_path / "casi.toml"
    toml_path.write_text(
        """
provider = "openai"
""",
        encoding="utf-8",
    )

    settings = Settings.from_toml(toml_path)
    assert settings.llm_provider == "openai"


def test_load_casi_toml_malformed(tmp_path: Path) -> None:
    bad_toml = tmp_path / "bad.toml"
    bad_toml.write_text("invalid = toml content ][ [[", encoding="utf-8")
    assert _load_casi_toml(bad_toml) == {}


def test_settings_from_toml_flat_model_and_other_fields(tmp_path: Path) -> None:
    toml_path = tmp_path / "casi.toml"
    toml_path.write_text(
        """
provider = "openai"
model = "gpt-4o-custom"
max_search_results = 25
docker_image = "casi-custom:1.0"
""",
        encoding="utf-8",
    )

    settings = Settings.from_toml(toml_path)
    assert settings.llm_provider == "openai"
    assert settings.openai_model == "gpt-4o-custom"
    assert settings.ollama_model == "gpt-4o-custom"
    assert settings.max_search_results == 25
    assert settings.docker_image == "casi-custom:1.0"


def test_settings_from_toml_invalid_timeout(tmp_path: Path) -> None:
    toml_path = tmp_path / "casi.toml"
    toml_path.write_text(
        """
[openai]
timeout_seconds = "invalid"
""",
        encoding="utf-8",
    )

    settings = Settings.from_toml(toml_path)
    assert settings.openai_timeout_seconds == 120.0
