"""Ollama-backed LLM client."""

from __future__ import annotations

import json
from typing import Any, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from casi_code_agent.config import settings
from casi_code_agent.exceptions import LLMError
from casi_code_agent.llm.base import ChatMessage, LLMResponse, ToolDefinition
from casi_code_agent.llm.parser import parse_response


class OllamaClient:
	"""Call Ollama's chat endpoint using the project's LLM contract."""

	def __init__(
		self,
		base_url: str = settings.ollama_base_url,
		model: str = settings.ollama_model,
		timeout_seconds: float = settings.ollama_timeout_seconds,
	) -> None:
		self.base_url = base_url.rstrip("/")
		self.model = model
		self.timeout_seconds = timeout_seconds

	def complete(
		self,
		messages: Sequence[ChatMessage],
		tools: Sequence[ToolDefinition],
	) -> LLMResponse:
		"""Request one model decision from Ollama."""

		payload: dict[str, Any] = {
			"model": self.model,
			"messages": [
				{"role": message.role, "content": message.content}
				for message in messages
			],
			"stream": False,
		}
		if tools:
			payload["tools"] = [self._tool_schema(tool) for tool in tools]

		response_payload = self._post(payload)
		return self._parse_payload(response_payload)

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
			name: {"type": details["type"]}
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
	def _parse_payload(payload: dict[str, Any]) -> LLMResponse:
		message = payload.get("message")
		if not isinstance(message, dict):
			raise LLMError("Ollama response does not contain a message")

		tool_calls = message.get("tool_calls", [])
		if tool_calls:
			return OllamaClient._parse_tool_call(tool_calls)

		content = message.get("content")
		if not isinstance(content, str):
			raise LLMError("Ollama message does not contain text content")
		try:
			return parse_response(content)
		except ValueError as exc:
			raise LLMError(f"Ollama returned an unsupported response: {exc}") from exc

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
