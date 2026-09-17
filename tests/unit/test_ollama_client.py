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

    def __enter__(self) -> FakeHTTPResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def test_client_sends_messages_and_parses_native_tool_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    assert captured["payload"]["think"] is False
    assert "tools" in captured["payload"]
    assert captured["payload"]["messages"][0]["role"] == "system"
    assert "qwen2.5-coder:7b" in captured["payload"]["messages"][0]["content"]
    assert "list_files" in captured["payload"]["messages"][0]["content"]
    assert captured["timeout"] == 120


def test_client_parses_structured_final_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_client_complete_action_uses_single_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
        captured["payload"] = json.loads(request.data)
        return FakeHTTPResponse(
            {
                "message": {
                    "content": ('{"path":"test_retry.py","content":"import pytest\\n"}')
                }
            }
        )

    monkeypatch.setattr("casi.llm.ollama_client.urlopen", fake_urlopen)
    client = OllamaClient(model="qwen3.5:4b", think_mode="auto")

    response = client.complete_action(
        [ChatMessage(role="user", content="Create test_retry.py")],
    )

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["format"] == {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
        "additionalProperties": False,
    }
    assert payload["think"] is True
    assert "Return ONLY a JSON object" in payload["messages"][0]["content"]
    assert response.kind == "tool_call"
    assert response.tool_name == "propose_file"
    assert response.arguments["path"] == "test_retry.py"


def test_client_parses_content_json_tool_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "casi.llm.ollama_client.urlopen",
        lambda request, timeout: FakeHTTPResponse(
            {
                "message": {
                    "content": '{"name":"read_file","arguments":{"path":"README.md"}}'
                }
            }
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
            {
                "message": {
                    "content": '```json\n{"name":"read_file","arguments":{}}\n```'
                }
            }
        ),
    )

    response = OllamaClient().complete([], [])

    assert response.kind == "tool_call"
    assert response.tool_name == "read_file"


def test_client_uses_thinking_and_json_tools_for_qwen35(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
        captured["payload"] = json.loads(request.data)
        return FakeHTTPResponse(
            {
                "message": {
                    "content": '{"type":"final","content":"Done"}',
                    "thinking": "Reasoning trace",
                }
            }
        )

    monkeypatch.setattr("casi.llm.ollama_client.urlopen", fake_urlopen)
    client = OllamaClient(model="qwen3.5:4b", think_mode="auto")
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

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["think"] is True
    assert "tools" not in payload
    assert response.kind == "final"
    assert response.content == "Done"


def test_client_rejects_invalid_model_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "casi.llm.ollama_client.urlopen",
        lambda request, timeout: FakeHTTPResponse({"message": {"content": ""}}),
    )

    with pytest.raises(LLMError, match="usable content"):
        OllamaClient().complete([], [])


def test_json_protocol_transmits_required_tool_arguments(monkeypatch) -> None:
    captured = []

    def post(self, payload):
        captured.append(payload)
        return {"message": {"content": '{"type":"final","content":"Done"}'}}

    monkeypatch.setattr(OllamaClient, "_post", post)
    OllamaClient(model="qwen3.5:4b").complete(
        [],
        [
            ToolDefinition(
                name="propose_file",
                description="Propose a complete replacement file",
                arguments={
                    "path": {"type": "string", "required": True},
                    "content": {"type": "string", "required": True},
                },
            )
        ],
    )
    payload = captured[0]
    assert "tools" not in payload
    system = payload["messages"][0]["content"]
    schema_line = system.split("Tool definitions for JSON calls:\n", 1)[1].splitlines()[
        0
    ]
    definition = json.loads(schema_line)[0]["function"]
    assert definition["name"] == "propose_file"
    assert definition["parameters"]["required"] == ["path", "content"]
    assert definition["parameters"]["properties"]["content"] == {"type": "string"}


def test_empty_response_retry_recovers_and_counts_all_tokens(monkeypatch) -> None:
    payloads = []
    responses = iter(
        [
            {
                "message": {"content": "", "thinking": "Still thinking"},
                "prompt_eval_count": 10,
                "eval_count": 5,
            },
            {
                "message": {
                    "content": '{"name":"propose_file","arguments":'
                    '{"path":"test_new.py","content":"x = 1"}}'
                },
                "prompt_eval_count": 12,
                "eval_count": 8,
            },
        ]
    )

    def post(self, payload):
        payloads.append(json.loads(json.dumps(payload)))
        return next(responses)

    monkeypatch.setattr(OllamaClient, "_post", post)
    messages = [ChatMessage(role="user", content="Create test_new.py")]
    result = OllamaClient(model="qwen3.5:4b").complete(messages, [])
    assert result.tool_name == "propose_file"
    assert result.arguments["path"] == "test_new.py"
    assert result.prompt_tokens == 22
    assert result.completion_tokens == 13
    assert len(payloads) == 2
    assert len(payloads[1]["messages"]) == len(payloads[0]["messages"]) + 1
    assert len(messages) == 1


@pytest.mark.parametrize("retries", [0, 2])
def test_empty_response_retry_is_bounded(monkeypatch, retries) -> None:
    calls = []

    def post(self, payload):
        calls.append(payload)
        return {"message": {"content": " "}}

    monkeypatch.setattr(OllamaClient, "_post", post)
    with pytest.raises(LLMError, match="usable content"):
        OllamaClient(max_empty_retries=retries).complete([], [])
    assert len(calls) == retries + 1


def test_invalid_envelope_is_not_retried(monkeypatch) -> None:
    calls = []

    def post(self, payload):
        calls.append(payload)
        return {"message": None}

    monkeypatch.setattr(OllamaClient, "_post", post)
    with pytest.raises(LLMError, match="does not contain a message"):
        OllamaClient().complete([], [])
    assert len(calls) == 1


@pytest.mark.parametrize("think_mode", ["true", "false"])
def test_required_tool_recovery_constrains_names_and_arguments(monkeypatch, think_mode):
    payloads = []

    def post(self, payload):
        payloads.append(payload)
        return {
            "message": {
                "content": json.dumps(
                    {
                        "name": "propose_file",
                        "arguments": {"path": "module.py", "content": "value = 2\n"},
                    }
                )
            }
        }

    monkeypatch.setattr(OllamaClient, "_post", post)
    tools = [
        ToolDefinition(
            name="propose_file",
            description="Propose a file",
            arguments={
                "path": {"type": "string", "required": True},
                "content": {"type": "string", "required": True},
            },
        )
    ]
    response = OllamaClient(think_mode=think_mode).complete_tool_call([], tools)
    assert response.arguments == {"path": "module.py", "content": "value = 2\n"}
    assert "tools" not in payloads[0]
    choices = payloads[0]["format"]["oneOf"]
    assert len(choices) == 1
    assert choices[0]["properties"]["name"] == {"const": "propose_file"}
    assert choices[0]["required"] == ["name", "arguments"]
    args = choices[0]["properties"]["arguments"]
    assert args["required"] == ["path", "content"]
    assert args["properties"]["content"] == {"type": "string"}
    assert args["additionalProperties"] is False


def test_required_tool_recovery_rejects_empty_tool_set():
    with pytest.raises(ValueError, match="at least one tool"):
        OllamaClient().complete_tool_call([], [])


def test_client_recovers_final_wrapped_tool_call_with_allowed_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "casi.llm.ollama_client.urlopen",
        lambda request, timeout: FakeHTTPResponse(
            {
                "message": {
                    "content": (
                        '{"type":"final","content":"{\\"name\\":\\"propose_file\\",'
                        '\\"arguments\\":{\\"path\\":\\"test_slug.py\\",'
                        '\\"content\\":\\"x\\"}}"}'
                    )
                }
            }
        ),
    )

    response = OllamaClient().complete(
        [],
        [
            ToolDefinition(
                name="propose_file",
                description="Propose a file",
                arguments={
                    "path": {"type": "string", "required": True},
                    "content": {"type": "string", "required": True},
                },
            )
        ],
    )

    assert response.kind == "tool_call"
    assert response.tool_name == "propose_file"
    assert response.arguments["path"] == "test_slug.py"


def test_client_leaves_final_wrapped_unknown_tool_when_tools_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "casi.llm.ollama_client.urlopen",
        lambda request, timeout: FakeHTTPResponse(
            {
                "message": {
                    "content": (
                        '{"type":"final","content":"{\\"name\\":\\"propose_file\\",'
                        '\\"arguments\\":{\\"path\\":\\"test_slug.py\\",'
                        '\\"content\\":\\"x\\"}}"}'
                    )
                }
            }
        ),
    )

    response = OllamaClient().complete(
        [],
        [
            ToolDefinition(
                name="read_file",
                description="Read a file",
                arguments={"path": {"type": "string", "required": True}},
            )
        ],
    )

    assert response.kind == "final"
    assert "propose_file" in response.content
