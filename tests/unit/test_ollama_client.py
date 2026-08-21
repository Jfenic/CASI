from __future__ import annotations

import json
from typing import Any

import pytest

from casi.exceptions import LLMError
from casi.llm.base import ChatMessage, ToolDefinition
from casi.llm.ollama_client import OllamaClient


class FakeHTTPResponse:
	def __init__(self, payload: dict[str, Any]) -> None:
		self.body = json.dumps(payload).encode("utf-8")

	def __enter__(self) -> "FakeHTTPResponse":
		return self

	def __exit__(self, *args: object) -> None:
		return None

	def read(self) -> bytes:
		return self.body


def test_client_sends_messages_and_parses_native_tool_call(monkeypatch: pytest.MonkeyPatch) -> None:
	captured: dict[str, Any] = {}

	def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
		captured["url"] = request.full_url
		captured["payload"] = json.loads(request.data)
		captured["timeout"] = timeout
		return FakeHTTPResponse(
			{
				"message": {
					"tool_calls": [
						{
							"function": {
								"name": "read_file",
								"arguments": '{"path": "README.md"}',
							}
						}
					]
				}
			}
		)

	monkeypatch.setattr("casi.llm.ollama_client.urlopen", fake_urlopen)
	client = OllamaClient(base_url="http://ollama.test", model="qwen2.5-coder:7b")

	response = client.complete(
		[ChatMessage(role="user", content="Inspect README")],
		[
			ToolDefinition(
				name="read_file",
				description="Read a file",
				arguments={"path": {"type": "string", "required": True}},
			)
		],
	)

	assert response.tool_name == "read_file"
	assert response.arguments == {"path": "README.md"}
	assert captured["url"] == "http://ollama.test/api/chat"
	assert captured["payload"]["model"] == "qwen2.5-coder:7b"
	assert captured["timeout"] == 120


def test_client_parses_structured_final_response(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(
		"casi.llm.ollama_client.urlopen",
		lambda request, timeout: FakeHTTPResponse(
			{"message": {"content": '{"type":"final","content":"Done"}'}}
		),
	)

	response = OllamaClient().complete([], [])

	assert response.kind == "final"
	assert response.content == "Done"


def test_client_rejects_invalid_model_response(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(
		"casi.llm.ollama_client.urlopen",
		lambda request, timeout: FakeHTTPResponse({"message": {"content": "plain text"}}),
	)

	with pytest.raises(LLMError, match="unsupported response"):
		OllamaClient().complete([], [])