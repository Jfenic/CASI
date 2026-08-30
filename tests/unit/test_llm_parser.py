import pytest

from casi.llm.base import LLMResponse
from casi.llm.parser import parse_response


def test_parse_final_response() -> None:
    response = parse_response('{"type": "final", "content": "Done"}')

    assert response == LLMResponse.final("Done")


def test_parse_tool_call() -> None:
    response = parse_response(
        '{"type": "tool_call", "name": "read_file", '
        '"arguments": {"path": "README.md"}}'
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
