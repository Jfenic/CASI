"""Ollama-backed LLM client."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from casi.config import settings
from casi.exceptions import LLMError
from casi.llm.base import ChatMessage, LLMResponse, ToolDefinition
from casi.llm.ollama_policy import resolve_think_enabled, use_json_tool_protocol
from casi.llm.parser import parse_response
from casi.llm.prompts import build_system_prompt


class OllamaClient:
    """Call Ollama's chat endpoint using the project's LLM contract."""

    def __init__(
        self,
        base_url: str = settings.ollama_base_url,
        model: str = settings.ollama_model,
        timeout_seconds: float = settings.ollama_timeout_seconds,
        *,
        role_instructions: str = "",
        think_mode: str = settings.ollama_think_mode,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.role_instructions = role_instructions
        self.think_mode = think_mode

    def complete(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition],
    ) -> LLMResponse:
        """Request one model decision from Ollama."""

        think_enabled = resolve_think_enabled(self.model, self.think_mode)
        json_tool_protocol = use_json_tool_protocol(think_enabled=think_enabled)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": build_system_prompt(
                        self.model,
                        tools,
                        role_instructions=self.role_instructions,
                    ),
                },
                *[
                    {"role": message.role, "content": message.content}
                    for message in messages
                ],
            ],
            "stream": False,
            "format": "json",
            "think": think_enabled,
        }
        if tools and not json_tool_protocol:
            payload["tools"] = [self._tool_schema(tool) for tool in tools]

        response_payload = self._post(payload)
        parsed = self._parse_payload(response_payload)
        prompt_tokens = _optional_int(response_payload.get("prompt_eval_count"))
        completion_tokens = _optional_int(response_payload.get("eval_count"))
        if prompt_tokens is None and completion_tokens is None:
            return parsed
        return LLMResponse(
            kind=parsed.kind,
            content=parsed.content,
            tool_name=parsed.tool_name,
            arguments=parsed.arguments,
            plan=list(parsed.plan),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc

        try:
            payload: Any = json.loads(body)
        except json.JSONDecodeError as exc:
            raise LLMError("Ollama returned invalid JSON") from exc

        if not isinstance(payload, dict):
            raise LLMError("Ollama response must be a JSON object")
        if "error" in payload:
            raise LLMError(f"Ollama returned an error: {payload['error']}")
        return payload

    @staticmethod
    def _tool_schema(tool: ToolDefinition) -> dict[str, Any]:
        properties = {
            name: {"type": details["type"]} for name, details in tool.arguments.items()
        }
        required = [
            name for name, details in tool.arguments.items() if details["required"]
        ]
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    @staticmethod
    def _parse_payload(payload: dict[str, Any]) -> LLMResponse:
        message = payload.get("message")
        if not isinstance(message, dict):
            raise LLMError("Ollama response does not contain a message")

        content = message.get("content")
        if not isinstance(content, str):
            content = ""

        tool_calls = message.get("tool_calls", [])
        if tool_calls and content.strip():
            # Prefer explicit JSON content when the model supplied both.
            tool_calls = []

        if tool_calls:
            return OllamaClient._parse_tool_call(tool_calls)

        thinking = message.get("thinking")
        candidates = [content]
        if isinstance(thinking, str) and thinking.strip():
            candidates.append(thinking)

        last_error: ValueError | None = None
        for candidate in candidates:
            if not candidate.strip():
                continue
            try:
                return parse_response(candidate)
            except ValueError as exc:
                last_error = exc
                structured_response = OllamaClient._parse_content_tool_call(candidate)
                if structured_response is not None:
                    return structured_response
                if candidate == content and content.strip():
                    return LLMResponse.final(content)

        raise LLMError("Ollama message does not contain usable content") from last_error

    @staticmethod
    def _parse_content_tool_call(content: str) -> LLMResponse | None:
        content = content.strip()
        if content.startswith("```") and content.endswith("```"):
            content = content[3:-3].strip()
            if content.startswith("json"):
                content = content[4:].strip()

        try:
            payload: Any = json.loads(content)
        except json.JSONDecodeError:
            return None

        if not isinstance(payload, dict):
            return None
        name = payload.get("name")
        arguments = payload.get("arguments", {})
        if isinstance(name, str) and isinstance(arguments, dict):
            return LLMResponse.tool_call(name, arguments)
        return None

    @staticmethod
    def _parse_tool_call(tool_calls: Any) -> LLMResponse:
        if not isinstance(tool_calls, list) or not isinstance(tool_calls[0], dict):
            raise LLMError("Ollama returned an invalid tool call")

        function = tool_calls[0].get("function")
        if not isinstance(function, dict):
            raise LLMError("Ollama tool call does not contain a function")

        name = function.get("name")
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as exc:
                raise LLMError("Ollama tool arguments are invalid JSON") from exc
        if not isinstance(name, str) or not isinstance(arguments, dict):
            raise LLMError("Ollama returned invalid tool-call fields")
        return LLMResponse.tool_call(name, arguments)


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None
