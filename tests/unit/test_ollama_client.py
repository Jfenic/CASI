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
	assert captured["payload"]["format"] == "json"
	assert captured["payload"]["messages"][0]["role"] == "system"
	assert "qwen2.5-coder:7b" in captured["payload"]["messages"][0]["content"]
	assert "list_files" in captured["payload"]["messages"][0]["content"]
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


def test_client_parses_final_response_with_separate_patch_field(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setattr(
		"casi.llm.ollama_client.urlopen",
		lambda request, timeout: FakeHTTPResponse(
			{
				"message": {
					"content": (
						'{"type":"final","content":"Applied fix",'
						'"patch":"--- a/x.py\\n+++ b/x.py\\n@@ -1 +1 @@\\n-x\\n+y"}'
					)
				}
			}
		),
	)

	response = OllamaClient().complete([], [])

	assert response.kind == "final"
	assert response.content.startswith("Applied fix")
	assert "--- a/x.py" in response.content


def test_client_parses_greeting_as_final_response(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setattr(
		"casi.llm.ollama_client.urlopen",
		lambda request, timeout: FakeHTTPResponse(
			{"message": {"content": '{"type":"final","content":"Hola"}'}}
		),
	)

	response = OllamaClient().complete(
		[ChatMessage(role="user", content="hola")],
		[],
	)

	assert response.kind == "final"
	assert response.content == "Hola"


def test_client_parses_content_json_tool_call(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(
		"casi.llm.ollama_client.urlopen",
		lambda request, timeout: FakeHTTPResponse(
			{"message": {"content": '{"name":"read_file","arguments":{"path":"README.md"}}'}}
		),
	)

	response = OllamaClient().complete([], [])

	assert response.kind == "tool_call"
	assert response.tool_name == "read_file"
	assert response.arguments == {"path": "README.md"}


def test_client_parses_fenced_content_json_tool_call(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setattr(
		"casi.llm.ollama_client.urlopen",
		lambda request, timeout: FakeHTTPResponse(
			{"message": {"content": '```json\n{"name":"read_file","arguments":{}}\n```'}}
		),
	)

	response = OllamaClient().complete([], [])

	assert response.kind == "tool_call"
	assert response.tool_name == "read_file"


def test_client_rejects_invalid_model_response(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(
		"casi.llm.ollama_client.urlopen",
		lambda request, timeout: FakeHTTPResponse({"message": {"content": ""}}),
	)

	with pytest.raises(LLMError, match="usable content"):
		OllamaClient().complete([], [])