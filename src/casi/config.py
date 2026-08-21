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


settings = Settings()