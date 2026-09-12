from __future__ import annotations

from casi.llm.ollama_policy import (
    model_supports_thinking,
    resolve_think_enabled,
    use_json_tool_protocol,
)


def test_model_supports_thinking_detects_qwen35_and_qwen3():
    assert model_supports_thinking("qwen3.5:4b")
    assert model_supports_thinking("qwen3:8b")
    assert not model_supports_thinking("qwen2.5-coder:7b")


def test_resolve_think_enabled_respects_explicit_override():
    assert resolve_think_enabled("qwen2.5-coder:7b", "true")
    assert not resolve_think_enabled("qwen3.5:4b", "false")


def test_resolve_think_enabled_auto_enables_for_thinking_models():
    assert resolve_think_enabled("qwen3.5:4b", "auto")
    assert not resolve_think_enabled("qwen2.5-coder:7b", "auto")


def test_json_tool_protocol_follows_thinking_mode():
    assert use_json_tool_protocol(think_enabled=True)
    assert not use_json_tool_protocol(think_enabled=False)
