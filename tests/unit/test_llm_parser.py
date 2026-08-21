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
