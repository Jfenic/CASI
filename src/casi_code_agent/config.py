"""Configuration helpers for casi_code_agent.
  This file must contain variable like URLs, Name of models, Timeouts, etc.
  that can be used across the project.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_file_size_bytes: int = 120_000
    max_files: int = 300
    max_search_results: int = 50


settings = Settings()