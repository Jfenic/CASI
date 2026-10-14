from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError

import pytest

from casi.exceptions import LLMError
from casi.llm.actions import ProposeFileAction
from casi.llm.base import ChatMessage, ToolCallRecord, ToolDefinition
from casi.llm.providers.openai import OpenAIClient


class FakeHTTPResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> FakeHTTPResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body

    def close(self) -> None:
        pass


def test_openai_client_properties_and_with_role_instructions() -> None:
    client = OpenAIClient(
        api_key="sk-test-123",
        base_url="https://api.openai.com/v1",
        model="gpt-4o",
    )
    assert client.provider_name == "openai"
    assert client.model_name == "gpt-4o"
    assert client.supports_evaluation is True

    specialized = client.with_role_instructions("Specialist role instructions")
    assert specialized.role_instructions == "Specialist role instructions"
    assert specialized.api_key == "sk-test-123"
    assert specialized.model == "gpt-4o"


def test_openai_client_sends_messages_and_parses_tool_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
        captured["url"] = request.full_url
        captured["headers"] = request.headers
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "id": "call_abc123",
                                    "type": "function",
                                    "function": {
                                        "name": "read_file",
                                        "arguments": json.dumps(
                                            {"path": "src/main.py"}
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 55,
                    "completion_tokens": 12,
                },
            }
        )

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_urlopen)
    client = OpenAIClient(
        api_key="sk-test-abc",
        base_url="https://api.openai.test/v1",
        model="gpt-4o",
    )

    tools = [
        ToolDefinition(
            name="read_file",
            description="Read a file from repository",
            arguments={"path": {"type": "string", "required": True}},
        )
    ]
    response = client.complete(
        [ChatMessage(role="user", content="Read src/main.py")],
        tools,
    )

    assert response.kind == "tool_call"
    assert response.tool_name == "read_file"
    assert response.arguments == {"path": "src/main.py"}
    assert response.prompt_tokens == 55
    assert response.completion_tokens == 12

    assert captured["url"] == "https://api.openai.test/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sk-test-abc"
    assert len(captured["payload"]["tools"]) == 1
    assert captured["payload"]["tools"][0]["function"]["name"] == "read_file"


def test_openai_client_parses_final_text_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "The bug is fixed and tests pass.",
                        }
                    }
                ],
                "usage": {"prompt_tokens": 40, "completion_tokens": 10},
            }
        )

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_urlopen)
    client = OpenAIClient(api_key="sk-test", model="gpt-4o-mini")

    response = client.complete(
        [ChatMessage(role="user", content="Explain status")],
        [],
    )
    assert response.kind == "final"
    assert response.content == "The bug is fixed and tests pass."
    assert response.prompt_tokens == 40
    assert response.completion_tokens == 10


def test_openai_client_formats_tool_history_with_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
        captured["payload"] = json.loads(request.data)
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Finished reading file.",
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_urlopen)
    client = OpenAIClient(api_key="sk-test", model="gpt-4o")

    history = [
        ChatMessage(role="user", content="Inspect repo"),
        ChatMessage(
            role="assistant",
            content="Calling read_file",
            tool_call=ToolCallRecord(
                name="read_file",
                arguments={"path": "src/a.py"},
                success=True,
                call_id="call_12345",
            ),
        ),
        ChatMessage(role="tool", content="file content here"),
    ]

    response = client.complete(history, [])
    assert response.kind == "final"
    messages = captured["payload"]["messages"]
    assert len(messages) == 4  # system + user + assistant + tool
    assert messages[2]["role"] == "assistant"
    assert messages[2]["tool_calls"][0]["id"] == "call_12345"
    assert messages[3]["role"] == "tool"
    assert messages[3]["tool_call_id"] == "call_12345"
    assert messages[3]["content"] == "file content here"


def test_openai_client_complete_action_forces_tool_choice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
        captured["payload"] = json.loads(request.data)
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "id": "call_prop_1",
                                    "type": "function",
                                    "function": {
                                        "name": "propose_file",
                                        "arguments": json.dumps(
                                            {
                                                "path": "calculator.py",
                                                "content": (
                                                    "def add(a, b): return a + b\n"
                                                ),
                                            }
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_urlopen)
    client = OpenAIClient(api_key="sk-test", model="gpt-4o")

    response = client.complete_action(
        [ChatMessage(role="user", content="Create calculator.py")],
        ProposeFileAction,
    )

    assert response.kind == "tool_call"
    assert response.tool_name == "propose_file"
    assert response.arguments["path"] == "calculator.py"
    assert response.arguments["content"] == "def add(a, b): return a + b\n"
    assert captured["payload"]["tool_choice"] == {
        "type": "function",
        "function": {"name": "propose_file"},
    }


def test_openai_client_complete_tool_call_requires_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
        captured["payload"] = json.loads(request.data)
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "id": "call_999",
                                    "type": "function",
                                    "function": {
                                        "name": "run_tests",
                                        "arguments": "{}",
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_urlopen)
    client = OpenAIClient(api_key="sk-test", model="gpt-4o")

    tools = [
        ToolDefinition(name="run_tests", description="Run repository tests"),
    ]
    response = client.complete_tool_call(
        [ChatMessage(role="user", content="Run tests")],
        tools,
    )
    assert response.kind == "tool_call"
    assert response.tool_name == "run_tests"
    assert captured["payload"]["tool_choice"] == "required"


def test_openai_client_handles_http_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_401(request: Any, timeout: float) -> Any:
        raise HTTPError(
            url="https://api.openai.com/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs={},  # type: ignore[arg-type]
            fp=FakeHTTPResponse({"error": {"message": "Invalid API key"}}),  # type: ignore[arg-type]
        )

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_401)
    client = OpenAIClient(api_key="invalid-key")

    with pytest.raises(LLMError) as exc_info:
        client.complete([ChatMessage(role="user", content="Hello")], [])
    assert "401" in str(exc_info.value)
    assert "OPENAI_API_KEY" in str(exc_info.value)


def test_openai_client_handles_url_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_connect_err(request: Any, timeout: float) -> Any:
        raise URLError(reason="Connection refused")

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_connect_err)
    client = OpenAIClient(base_url="http://unreachable.host:9999")

    with pytest.raises(LLMError) as exc_info:
        client.complete([ChatMessage(role="user", content="Hello")], [])
    assert "Could not connect to OpenAI" in str(exc_info.value)


def test_openai_client_handles_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_timeout(request: Any, timeout: float) -> Any:
        raise TimeoutError("The read operation timed out")

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_timeout)
    client = OpenAIClient(timeout_seconds=5.0)

    with pytest.raises(LLMError) as exc_info:
        client.complete([ChatMessage(role="user", content="Hello")], [])
    assert "timed out after 5.0s" in str(exc_info.value)


def test_openai_client_handles_os_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_os_error(request: Any, timeout: float) -> Any:
        raise OSError("Connection reset by peer")

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_os_error)
    client = OpenAIClient()

    with pytest.raises(LLMError) as exc_info:
        client.complete([ChatMessage(role="user", content="Hello")], [])
    assert "OpenAI network error" in str(exc_info.value)


def test_openai_client_handles_empty_string_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "id": "call_zero_arg",
                                    "type": "function",
                                    "function": {
                                        "name": "run_tests",
                                        "arguments": "",
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_urlopen)
    client = OpenAIClient()
    tools = [
        ToolDefinition(name="run_tests", description="Run repository tests"),
    ]
    response = client.complete([ChatMessage(role="user", content="run tests")], tools)
    assert response.kind == "tool_call"
    assert response.tool_name == "run_tests"
    assert response.arguments == {}
    assert response.call_id == "call_zero_arg"


def test_openai_client_complete_action_with_markdown_fences(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                "```json\n"
                                '{"path": "fenced.py", "content": "x = 42\\n"}\n'
                                "```"
                            ),
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_urlopen)
    client = OpenAIClient()
    response = client.complete_action(
        [ChatMessage(role="user", content="create fenced.py")],
        ProposeFileAction,
    )
    assert response.kind == "tool_call"
    assert response.tool_name == "propose_file"
    assert response.arguments["path"] == "fenced.py"
    assert response.arguments["content"] == "x = 42\n"


def test_openai_client_bounds_long_message_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
        captured["payload"] = json.loads(request.data)
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "ok",
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_urlopen)
    client = OpenAIClient()
    huge_message = "A" * 15_000
    client.complete([ChatMessage(role="user", content=huge_message)], [])

    messages = captured["payload"]["messages"]
    user_content = messages[-1]["content"]
    assert len(user_content) <= 6000
    assert "truncad" in user_content.lower()


def test_openai_client_custom_system_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> FakeHTTPResponse:
        captured["payload"] = json.loads(request.data)
        return FakeHTTPResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "evaluation result",
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("casi.llm.providers.openai.urlopen", fake_urlopen)
    client = OpenAIClient()
    custom_sys = "You are a specialized evaluation prompt."
    client.complete(
        [
            ChatMessage(role="system", content=custom_sys),
            ChatMessage(role="user", content="evaluate"),
        ],
        [],
    )

    messages = captured["payload"]["messages"]
    system_messages = [m for m in messages if m["role"] == "system"]
    assert len(system_messages) == 1
    assert "You are a specialized evaluation prompt." in system_messages[0]["content"]
    assert "You are CASI, an advanced repository" not in system_messages[0]["content"]
