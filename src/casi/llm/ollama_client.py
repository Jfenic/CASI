"""Ollama-backed LLM client."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from casi.config import settings
from casi.exceptions import LLMError
from casi.llm.actions import ProposeFileAction, action_validation_error
from casi.llm.base import ChatMessage, LLMResponse, ToolDefinition
from casi.llm.json_schema import normalize_json_schema_type
from casi.llm.ollama_policy import resolve_think_enabled, use_json_tool_protocol
from casi.llm.parser import normalize_response, parse_response, tool_call_allowed
from casi.llm.prompts import build_create_action_prompt, build_system_prompt


class _EmptyModelResponse(LLMError):
    """A valid envelope with no usable model decision; safe to request again."""


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
        max_empty_retries: int = 2,
    ) -> None:
        if max_empty_retries < 0:
            raise ValueError("max_empty_retries must be non-negative")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.role_instructions = role_instructions
        self.think_mode = think_mode
        self.max_empty_retries = max_empty_retries

    def complete(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition],
    ) -> LLMResponse:
        """Request one model decision from Ollama."""

        return self._complete(messages, tools)

    def complete_tool_call(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition],
    ) -> LLMResponse:
        """Constrain a recovery decision to the currently permitted tool schemas."""

        if not tools:
            raise ValueError("A required tool call needs at least one tool")
        return self._complete(messages, tools, require_tool_call=True)

    def complete_action(
        self,
        messages: Sequence[ChatMessage],
        action: type[ProposeFileAction] = ProposeFileAction,
    ) -> LLMResponse:
        """Request one constrained mutation action (schema-only, no final branch)."""

        think_enabled = resolve_think_enabled(self.model, self.think_mode)
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": build_create_action_prompt(
                        self.model,
                        role_instructions=self.role_instructions,
                    ),
                },
                *[
                    {"role": message.role, "content": message.content}
                    for message in messages
                ],
            ],
            "stream": False,
            "format": action.json_schema(),
            "think": think_enabled,
        }

        prompt_tokens: int | None = None
        completion_tokens: int | None = None
        for attempt in range(self.max_empty_retries + 1):
            response_payload = self._post(payload)
            prompt_count = _optional_int(response_payload.get("prompt_eval_count"))
            completion_count = _optional_int(response_payload.get("eval_count"))
            if prompt_count is not None:
                prompt_tokens = (prompt_tokens or 0) + prompt_count
            if completion_count is not None:
                completion_tokens = (completion_tokens or 0) + completion_count
            message = response_payload.get("message")
            if not isinstance(message, dict):
                raise LLMError("Ollama response does not contain a message")
            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                if attempt == self.max_empty_retries:
                    raise _EmptyModelResponse(
                        "Ollama action response does not contain content"
                    )
                payload["messages"].append(
                    {
                        "role": "user",
                        "content": action_validation_error("empty content"),
                    }
                )
                continue
            try:
                parsed = self._parse_action_response(content, action)
                break
            except ValueError as exc:
                if attempt == self.max_empty_retries:
                    raise LLMError(
                        f"Ollama action response failed validation: {exc}"
                    ) from exc
                payload["messages"].append(
                    {
                        "role": "user",
                        "content": action_validation_error(str(exc)),
                    }
                )
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

    @staticmethod
    def _parse_action_response(
        content: str,
        action: type[ProposeFileAction],
    ) -> LLMResponse:
        wrapped = OllamaClient._parse_content_tool_call(content)
        if wrapped is not None and wrapped.tool_name == action.tool_name:
            return wrapped
        parsed_action = action.from_json(content)
        return LLMResponse.tool_call(
            parsed_action.tool_name,
            parsed_action.as_tool_arguments(),
        )

    def _complete(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition],
        *,
        require_tool_call: bool = False,
    ) -> LLMResponse:

        think_enabled = resolve_think_enabled(self.model, self.think_mode)
        json_tool_protocol = require_tool_call or use_json_tool_protocol(
            think_enabled=think_enabled
        )

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
        if tools:
            schemas = [self._tool_schema(tool) for tool in tools]
            if json_tool_protocol:
                payload["messages"][0]["content"] += (
                    "\n\nTool definitions for JSON calls:\n"
                    + json.dumps(schemas, ensure_ascii=False)
                    + '\nReturn {"name":"tool_name","arguments":{...}} '
                    "with every required argument. String arguments contain the "
                    "actual text, including complete source for propose_file.content."
                )
            else:
                payload["tools"] = schemas

        if require_tool_call:
            choices = []
            for tool in tools:
                parameters = self._tool_schema(tool)["function"]["parameters"]
                choices.append(
                    {
                        "type": "object",
                        "properties": {
                            "name": {"const": tool.name},
                            "arguments": {**parameters, "additionalProperties": False},
                        },
                        "required": ["name", "arguments"],
                        "additionalProperties": False,
                    }
                )
            payload["format"] = {"oneOf": choices}
            payload["messages"][0]["content"] += (
                "\nThis recovery decision requires a tool call, not a final answer. "
                "Select one of the supplied tools and include its required arguments."
            )

        prompt_tokens: int | None = None
        completion_tokens: int | None = None
        for attempt in range(self.max_empty_retries + 1):
            response_payload = self._post(payload)
            prompt_count = _optional_int(response_payload.get("prompt_eval_count"))
            completion_count = _optional_int(response_payload.get("eval_count"))
            if prompt_count is not None:
                prompt_tokens = (prompt_tokens or 0) + prompt_count
            if completion_count is not None:
                completion_tokens = (completion_tokens or 0) + completion_count
            try:
                parsed = self._parse_payload(response_payload, tools)
                break
            except _EmptyModelResponse:
                if attempt == self.max_empty_retries:
                    raise
                if attempt == 0:
                    payload["messages"].append(
                        {
                            "role": "user",
                            "content": (
                                "Your response contained no usable decision. Return "
                                "one JSON tool call with all required arguments or "
                                "a JSON final answer in message content. For a "
                                "code-change task, call propose_file with path and "
                                "complete content instead of describing the change."
                            ),
                        }
                    )
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
            name: {"type": normalize_json_schema_type(str(details["type"]))}
            for name, details in tool.arguments.items()
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
    def _parse_payload(
        payload: dict[str, Any],
        tools: Sequence[ToolDefinition],
    ) -> LLMResponse:
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
                parsed = parse_response(candidate)
                recovered = normalize_response(parsed, allowed_tools=tools or None)
                if OllamaClient._tool_call_is_permitted(recovered, tools):
                    return recovered
            except ValueError as exc:
                last_error = exc
                structured_response = OllamaClient._parse_content_tool_call(candidate)
                if structured_response is not None and (
                    OllamaClient._tool_call_is_permitted(structured_response, tools)
                ):
                    return structured_response
                embedded = normalize_response(
                    LLMResponse.final(candidate), allowed_tools=tools or None
                )
                if embedded.kind == "tool_call" and (
                    OllamaClient._tool_call_is_permitted(embedded, tools)
                ):
                    return embedded
                if candidate == content and content.strip():
                    return LLMResponse.final(content)

        raise _EmptyModelResponse(
            "Ollama message does not contain usable content"
        ) from last_error

    @staticmethod
    def _tool_call_is_permitted(
        response: LLMResponse,
        tools: Sequence[ToolDefinition],
    ) -> bool:
        if response.kind != "tool_call" or response.tool_name is None:
            return True
        if not tools:
            return True
        return tool_call_allowed(
            response.tool_name,
            response.arguments,
            tools,
        )

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
