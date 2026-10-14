from __future__ import annotations

import pytest

from casi.agent.factory import _client_for_profile
from casi.agent.profiles import resolve_profile
from casi.llm.base import LLMClient
from casi.llm.ollama_client import OllamaClient
from casi.llm.providers.base import ModelProvider
from casi.llm.providers.factory import create_llm_client
from casi.llm.providers.ollama import OllamaProvider
from casi.llm.providers.openai import OpenAIClient, OpenAIProvider


def test_provider_protocols() -> None:
    ollama = OllamaProvider()
    openai = OpenAIProvider(api_key="test-key")

    assert isinstance(ollama, ModelProvider)
    assert isinstance(openai, ModelProvider)
    assert isinstance(ollama, LLMClient)
    assert isinstance(openai, LLMClient)

    assert ollama.provider_name == "ollama"
    assert openai.provider_name == "openai"


def test_create_llm_client_factory() -> None:
    client_ollama = create_llm_client("ollama", model="qwen-custom")
    assert isinstance(client_ollama, OllamaClient)
    assert client_ollama.model == "qwen-custom"

    client_openai = create_llm_client(
        "openai",
        model="gpt-4o-mini",
        api_key="sk-override",
    )
    assert isinstance(client_openai, OpenAIClient)
    assert client_openai.model == "gpt-4o-mini"
    assert client_openai.api_key == "sk-override"

    client_inferred = create_llm_client(model="gpt-4o-mini")
    assert isinstance(client_inferred, OpenAIClient)
    assert client_inferred.model == "gpt-4o-mini"

    with pytest.raises(ValueError) as exc:
        create_llm_client("unsupported_provider")
    assert "Unknown LLM provider" in str(exc.value)


def test_client_for_profile_polymorphic_adaptation() -> None:
    profile = resolve_profile("fix").with_instructions("Fix strictly line 42")

    ollama_client = OllamaClient(model="qwen")
    adapted_ollama = _client_for_profile(ollama_client, profile)
    assert isinstance(adapted_ollama, OllamaClient)
    assert "Fix strictly line 42" in adapted_ollama.role_instructions

    openai_client = OpenAIClient(api_key="sk-key", model="gpt-4o")
    adapted_openai = _client_for_profile(openai_client, profile)
    assert isinstance(adapted_openai, OpenAIClient)
    assert "Fix strictly line 42" in adapted_openai.role_instructions
