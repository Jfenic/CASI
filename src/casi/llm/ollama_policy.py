"""Model-specific Ollama request policy for thinking and tool protocols."""

from __future__ import annotations

_THINKING_MODEL_MARKERS = (
    "qwen3.5",
    "qwen3",
    "deepseek-r1",
    "phi4-reasoning",
)


def model_supports_thinking(model: str) -> bool:
    """Return whether the configured model family exposes Ollama thinking."""

    lowered = model.lower()
    return any(marker in lowered for marker in _THINKING_MODEL_MARKERS)


def resolve_think_enabled(model: str, mode: str) -> bool:
    """Resolve whether Ollama should run with thinking enabled."""

    normalized = mode.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return model_supports_thinking(model)


def use_json_tool_protocol(*, think_enabled: bool) -> bool:
    """Return whether tools should be requested via JSON content instead of native calls.

    Native Ollama tool calls conflict with thinking models: they often emit empty
    content and spurious tool calls even for direct answers.
    """

    return think_enabled
