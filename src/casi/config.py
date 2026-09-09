"""Runtime configuration for CASI."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
  max_file_size_bytes: int = 120_000
  max_files: int = 300
  max_search_results: int = 50
  ollama_base_url: str = os.getenv(
    "LOCALCODE_AGENT_OLLAMA_URL",
    "http://localhost:11434",
  )
  ollama_model: str = os.getenv(
    "LOCALCODE_AGENT_OLLAMA_MODEL",
    "qwen2.5-coder:7b",
  )
  ollama_timeout_seconds: float = float(
    os.getenv("LOCALCODE_AGENT_OLLAMA_TIMEOUT", "120")
  )
  test_timeout_seconds: float = float(
    os.getenv("LOCALCODE_AGENT_TEST_TIMEOUT", "120")
  )
  max_command_output_chars: int = int(
    os.getenv("LOCALCODE_AGENT_MAX_COMMAND_OUTPUT", "20000")
  )
  git_timeout_seconds: float = float(
    os.getenv("LOCALCODE_AGENT_GIT_TIMEOUT", "30")
  )
  max_patch_size_bytes: int = int(
    os.getenv("LOCALCODE_AGENT_MAX_PATCH_SIZE", "100000")
  )
  max_patch_files: int = int(
    os.getenv("LOCALCODE_AGENT_MAX_PATCH_FILES", "20")
  )
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
    "true",
  ).lower() in {"1", "true", "yes"}
  docker_pids_limit: int = int(os.getenv("LOCALCODE_AGENT_DOCKER_PIDS_LIMIT", "64"))
  max_correction_attempts: int = int(
    os.getenv("LOCALCODE_AGENT_MAX_CORRECTION_ATTEMPTS", "4")
  )
  fix_max_steps: int = int(
    os.getenv("LOCALCODE_AGENT_FIX_MAX_STEPS", "12")
  )
  create_max_steps: int = int(
    os.getenv("LOCALCODE_AGENT_CREATE_MAX_STEPS", "18")
  )
  agent_routing_mode: str = os.getenv(
    "LOCALCODE_AGENT_ROUTING_MODE",
    "assist",
  )


settings = Settings()
