import pytest

from casi.llm.base import LLMResponse, ToolDefinition
from casi.llm.parser import (
    extract_tool_call_payload,
    normalize_response,
    parse_response,
)


def test_parse_final_response() -> None:
    response = parse_response('{"type": "final", "content": "Done"}')

    assert response == LLMResponse.final("Done")


def test_parse_tool_call() -> None:
    response = parse_response(
        '{"type": "tool_call", "name": "read_file", "arguments": {"path": "README.md"}}'
    )

    assert response.kind == "tool_call"
    assert response.tool_name == "read_file"
    assert response.arguments == {"path": "README.md"}


def test_parse_clarification_with_plan() -> None:
    response = parse_response(
        '{"type":"clarification","question":"Which file?",'
        '"plan":["Find the module","Read the implementation"]}'
    )

    assert response.kind == "clarification"
    assert response.content == "Which file?"
    assert response.plan == ["Find the module", "Read the implementation"]


def test_parse_alternate_final_response_keys() -> None:
    for raw_response in (
        '{"response": "Done"}',
        '{"assistant": "Done"}',
        '{"message": "Done"}',
    ):
        response = parse_response(raw_response)
        assert response == LLMResponse.final("Done")


def test_parse_final_response_with_separate_patch_field() -> None:
    raw_response = (
        '{"type":"final","content":"Applied fix",'
        '"patch":"--- a/x.py\\n+++ b/x.py\\n@@ -1 +1 @@\\n-x\\n+y"}'
    )
    response = parse_response(raw_response)

    assert response.kind == "final"
    assert response.content.startswith("Applied fix")
    assert "--- a/x.py" in response.content
    assert "+++ b/x.py" in response.content


def test_parse_final_response_allows_patch_only_payload() -> None:
    raw_response = (
        '{"type":"final","content":"",'
        '"patch":"--- a/x.py\\n+++ b/x.py\\n@@ -1 +1 @@\\n-x\\n+y"}'
    )
    response = parse_response(raw_response)

    assert response.kind == "final"
    assert response.content.startswith("--- a/x.py")


def test_parse_tool_call_without_type_field() -> None:
    response = parse_response('{"name":"list_files","arguments":{}}')

    assert response.kind == "tool_call"
    assert response.tool_name == "list_files"
    assert response.arguments == {}


@pytest.mark.parametrize(
    "raw_response",
    [
        "not json",
        "[]",
        '{"type": "unknown"}',
        '{"type": "final", "content": ""}',
        '{"type": "tool_call", "name": "read_file", "arguments": []}',
    ],
)
def test_parse_rejects_invalid_response(raw_response: str) -> None:
    with pytest.raises(ValueError):
        parse_response(raw_response)


def test_normalize_response_coerces_final_wrapped_tool_call() -> None:
    from casi.llm.parser import normalize_response

    response = normalize_response(
        LLMResponse.final(
            '{"type":"final","content":"{\\"name\\":\\"propose_file\\",'
            '\\"arguments\\":{\\"path\\":\\"test_slug.py\\",\\"content\\":\\"x\\"}}"}'
        )
    )

    assert response.kind == "tool_call"
    assert response.tool_name == "propose_file"
    assert response.arguments["path"] == "test_slug.py"


def test_normalize_response_leaves_genuine_final_unchanged() -> None:
    response = normalize_response(LLMResponse.final("All done."))

    assert response.kind == "final"
    assert response.content == "All done."


def test_normalize_response_leaves_clarification_unchanged() -> None:
    response = normalize_response(
        LLMResponse.clarification("Which file?", ["Inspect repo"])
    )

    assert response.kind == "clarification"
    assert response.content == "Which file?"


def test_normalize_response_leaves_invalid_embedded_json_unchanged() -> None:
    response = normalize_response(LLMResponse.final('{"type":"final","content":""}'))

    assert response.kind == "final"


def test_normalize_response_rejects_unknown_tool_when_tools_provided() -> None:
    response = normalize_response(
        LLMResponse.final('{"name":"unknown_tool","arguments":{"path":"README.md"}}'),
        allowed_tools=[
            ToolDefinition(
                name="read_file",
                description="Read a file",
                arguments={"path": {"type": "string", "required": True}},
            )
        ],
    )

    assert response.kind == "final"


def test_normalize_response_rejects_invalid_arguments_when_tools_provided() -> None:
    response = normalize_response(
        LLMResponse.final('{"name":"propose_file","arguments":{"path":"x.py"}}'),
        allowed_tools=[
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

    assert response.kind == "final"


def test_normalize_response_accepts_valid_tool_when_tools_provided() -> None:
    response = normalize_response(
        LLMResponse.final(
            '{"name":"propose_file","arguments":'
            '{"path":"test_slug.py","content":"x = 1\\n"}}'
        ),
        allowed_tools=[
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
    assert response.arguments["content"] == "x = 1\n"


def test_extract_tool_call_payload_rejects_multiple_actions() -> None:
    payload = extract_tool_call_payload(
        '[{"name":"read_file","arguments":{"path":"a.py"}},'
        '{"name":"read_file","arguments":{"path":"b.py"}}]'
    )

    assert payload is None


def test_extract_tool_call_payload_handles_tool_call_type_wrapper() -> None:
    payload = extract_tool_call_payload(
        '{"type":"tool_call","name":"propose_file",'
        '"arguments":{"path":"x.py","content":"y"}}'
    )

    assert payload == {
        "name": "propose_file",
        "arguments": {"path": "x.py", "content": "y"},
    }


def test_parse_response_tolerates_literal_newlines_in_strings() -> None:
    raw = '{"type":"final","content":"line 1\nline 2"}'
    response = parse_response(raw)
    assert response.kind == "final"
    assert response.content == "line 1\nline 2"


def test_extract_tool_call_payload_tolerates_literal_newlines() -> None:
    raw = (
        '{"name":"propose_file","arguments":'
        '{"path":"sales.py","content":"import csv\ndef totals():\n    pass"}}'
    )
    payload = extract_tool_call_payload(raw)
    assert payload is not None
    assert payload["name"] == "propose_file"
    assert "import csv\ndef totals():" in str(payload["arguments"]["content"])
