from __future__ import annotations

import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


def _load_casi_toml(path: Path | None = None) -> dict[str, Any]:
    candidates = [path] if path is not None else [Path("casi.toml"), Path(".casi.toml")]
    for candidate in candidates:
        if candidate and candidate.is_file():
            try:
                import tomllib

                with candidate.open("rb") as f:
                    return tomllib.load(f)
            except Exception:
                return {}
    return {}


def _to_float(value: Any, default: float) -> float:
    try:
        if value is None or isinstance(value, bool):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int) -> int:
    try:
        if value is None or isinstance(value, bool):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


_cfg = _load_casi_toml()
_llm_cfg = _cfg.get("llm", {}) if isinstance(_cfg.get("llm"), dict) else {}
_openai_cfg = _cfg.get("openai", {}) if isinstance(_cfg.get("openai"), dict) else {}
_ollama_cfg = _cfg.get("ollama", {}) if isinstance(_cfg.get("ollama"), dict) else {}


@dataclass(frozen=True)
class Settings:
    max_file_size_bytes: int = 120_000
    max_files: int = 300
    max_search_results: int = 50
    llm_provider: str = os.getenv(
        "LOCALCODE_AGENT_PROVIDER",
        os.getenv(
            "CASI_LLM_PROVIDER",
            str(_llm_cfg.get("provider", _cfg.get("provider", "ollama"))),
        ),
    )
    ollama_base_url: str = os.getenv(
        "LOCALCODE_AGENT_OLLAMA_URL",
        str(_ollama_cfg.get("base_url", "http://localhost:11434")),
    )
    ollama_model: str = os.getenv(
        "LOCALCODE_AGENT_OLLAMA_MODEL",
        str(
            _ollama_cfg.get(
                "model",
                _llm_cfg.get("model", _cfg.get("model", "qwen2.5-coder:7b")),
            )
        ),
    )
    ollama_timeout_seconds: float = float(
        os.getenv(
            "LOCALCODE_AGENT_OLLAMA_TIMEOUT",
            str(_ollama_cfg.get("timeout_seconds", 120)),
        )
    )
    openai_base_url: str = os.getenv(
        "OPENAI_BASE_URL",
        str(_openai_cfg.get("base_url", "https://api.openai.com/v1")),
    )
    openai_api_key: str = os.getenv(
        "OPENAI_API_KEY",
        str(_openai_cfg.get("api_key", "")),
    )
    openai_model: str = os.getenv(
        "OPENAI_MODEL",
        str(
            _openai_cfg.get(
                "model",
                _llm_cfg.get("model", _cfg.get("model", "gpt-4o")),
            )
        ),
    )
    openai_timeout_seconds: float = float(
        os.getenv(
            "OPENAI_TIMEOUT_SECONDS",
            str(_openai_cfg.get("timeout_seconds", 120)),
        )
    )
    test_timeout_seconds: float = float(
        os.getenv("LOCALCODE_AGENT_TEST_TIMEOUT", "120")
    )
    max_command_output_chars: int = int(
        os.getenv("LOCALCODE_AGENT_MAX_COMMAND_OUTPUT", "20000")
    )
    git_timeout_seconds: float = float(os.getenv("LOCALCODE_AGENT_GIT_TIMEOUT", "30"))
    max_patch_size_bytes: int = int(
        os.getenv("LOCALCODE_AGENT_MAX_PATCH_SIZE", "100000")
    )
    max_patch_files: int = int(os.getenv("LOCALCODE_AGENT_MAX_PATCH_FILES", "20"))
    max_context_messages: int = int(
        os.getenv("LOCALCODE_AGENT_MAX_CONTEXT_MESSAGES", "40")
    )
    context_compact_warn_ratio: float = float(
        os.getenv("LOCALCODE_AGENT_CONTEXT_WARN_RATIO", "0.8")
    )
    docker_image: str = os.getenv(
        "LOCALCODE_AGENT_DOCKER_IMAGE",
        "casi-sandbox:latest",
    )
    docker_memory: str = os.getenv("LOCALCODE_AGENT_DOCKER_MEMORY", "512m")
    docker_cpus: str = os.getenv("LOCALCODE_AGENT_DOCKER_CPUS", "1")
    use_docker_sandbox: bool = os.getenv(
        "LOCALCODE_AGENT_USE_DOCKER",
        "true",
    ).lower() in {"1", "true", "yes"}
    allow_local_test_fallback: bool = os.getenv(
        "LOCALCODE_AGENT_ALLOW_LOCAL_FALLBACK",
        "false",
    ).lower() in {"1", "true", "yes"}
    docker_pids_limit: int = int(os.getenv("LOCALCODE_AGENT_DOCKER_PIDS_LIMIT", "64"))
    max_correction_attempts: int = int(
        os.getenv("LOCALCODE_AGENT_MAX_CORRECTION_ATTEMPTS", "4")
    )
    fix_max_steps: int = int(os.getenv("LOCALCODE_AGENT_FIX_MAX_STEPS", "12"))
    create_max_steps: int = int(os.getenv("LOCALCODE_AGENT_CREATE_MAX_STEPS", "18"))
    max_agent_file_reads: int = int(os.getenv("LOCALCODE_AGENT_MAX_FILE_READS", "12"))
    max_reads_per_file: int = int(os.getenv("LOCALCODE_AGENT_MAX_READS_PER_FILE", "2"))
    agent_routing_mode: str = os.getenv(
        "LOCALCODE_AGENT_ROUTING_MODE",
        "assist",
    )
    ollama_think_mode: str = os.getenv("LOCALCODE_AGENT_OLLAMA_THINK", "auto")
    max_error_output_chars: int = int(
        os.getenv("LOCALCODE_AGENT_MAX_ERROR_OUTPUT", "1500")
    )
    error_truncation_strategy: str = os.getenv("LOCALCODE_AGENT_ERROR_STRATEGY", "auto")
    max_message_chars: int = int(os.getenv("LOCALCODE_AGENT_MAX_MESSAGE_CHARS", "6000"))

    @classmethod
    def from_toml(cls, path: Path | str) -> Settings:
        """Create Settings loaded from a specific TOML file."""
        cfg = _load_casi_toml(Path(path))
        llm_cfg = cfg.get("llm", {}) if isinstance(cfg.get("llm"), dict) else {}
        openai_cfg = (
            cfg.get("openai", {}) if isinstance(cfg.get("openai"), dict) else {}
        )
        ollama_cfg = (
            cfg.get("ollama", {}) if isinstance(cfg.get("ollama"), dict) else {}
        )

        kwargs: dict[str, Any] = {
            "llm_provider": str(llm_cfg.get("provider", cfg.get("provider", "ollama"))),
            "ollama_base_url": str(
                ollama_cfg.get(
                    "base_url",
                    cfg.get("ollama_base_url", "http://localhost:11434"),
                )
            ),
            "ollama_model": str(
                ollama_cfg.get(
                    "model",
                    llm_cfg.get(
                        "model",
                        cfg.get("model", "qwen2.5-coder:7b"),
                    ),
                )
            ),
            "ollama_timeout_seconds": _to_float(
                ollama_cfg.get("timeout_seconds", cfg.get("ollama_timeout_seconds")),
                120.0,
            ),
            "openai_base_url": str(
                openai_cfg.get(
                    "base_url",
                    cfg.get("openai_base_url", "https://api.openai.com/v1"),
                )
            ),
            "openai_api_key": str(
                openai_cfg.get("api_key", cfg.get("openai_api_key", ""))
            ),
            "openai_model": str(
                openai_cfg.get(
                    "model",
                    llm_cfg.get(
                        "model",
                        cfg.get("model", "gpt-4o"),
                    ),
                )
            ),
            "openai_timeout_seconds": _to_float(
                openai_cfg.get("timeout_seconds", cfg.get("openai_timeout_seconds")),
                120.0,
            ),
        }

        # Populate any other declared Settings fields present in cfg
        for fld in fields(cls):
            if fld.name not in kwargs and fld.name in cfg:
                kwargs[fld.name] = cfg[fld.name]

        return cls(**kwargs)


settings = Settings()
