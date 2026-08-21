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
  docker_image: str = os.getenv(
    "LOCALCODE_AGENT_DOCKER_IMAGE",
    "casi-sandbox:latest",
  )
  docker_memory: str = os.getenv("LOCALCODE_AGENT_DOCKER_MEMORY", "512m")
  docker_cpus: str = os.getenv("LOCALCODE_AGENT_DOCKER_CPUS", "1")


settings = Settings()