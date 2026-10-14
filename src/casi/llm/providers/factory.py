"""Factory for creating LLM clients and model providers."""

from __future__ import annotations

from casi.config import settings
from casi.llm.base import LLMClient
from casi.llm.ollama_client import OllamaClient
from casi.llm.providers.ollama import OllamaProvider
from casi.llm.providers.openai import OpenAIClient, OpenAIProvider


def create_llm_client(
    provider: str | None = None,
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout_seconds: float | None = None,
    role_instructions: str = "",
) -> LLMClient:
    """Instantiate the appropriate LLM client based on provider selection.

    Supported providers:
    - 'ollama' / 'local': Local models served via Ollama
    - 'openai' / 'gpt': Cloud models served via OpenAI or compatible endpoints
    """
    if provider is None:
        if model and model.strip().lower().startswith(
            ("gpt-", "o1-", "o3-", "chatgpt-")
        ):
            selected_provider = "openai"
        else:
            selected_provider = settings.llm_provider.strip().lower()
    else:
        selected_provider = provider.strip().lower()

    if selected_provider in {"openai", "gpt"}:
        return OpenAIProvider(
            api_key=api_key if api_key is not None else settings.openai_api_key,
            base_url=base_url if base_url is not None else settings.openai_base_url,
            model=model if model is not None else settings.openai_model,
            timeout_seconds=(
                timeout_seconds
                if timeout_seconds is not None
                else settings.openai_timeout_seconds
            ),
            role_instructions=role_instructions,
        )

    if selected_provider in {"ollama", "local"}:
        return OllamaProvider(
            base_url=base_url if base_url is not None else settings.ollama_base_url,
            model=model if model is not None else settings.ollama_model,
            timeout_seconds=(
                timeout_seconds
                if timeout_seconds is not None
                else settings.ollama_timeout_seconds
            ),
            role_instructions=role_instructions,
            think_mode=settings.ollama_think_mode,
        )

    raise ValueError(
        f"Unknown LLM provider: '{selected_provider}'. Supported: 'ollama', 'openai'"
    )


__all__ = [
    "OllamaClient",
    "OllamaProvider",
    "OpenAIClient",
    "OpenAIProvider",
    "create_llm_client",
]
