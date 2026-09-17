from __future__ import annotations

import pytest

from casi.llm.actions import ProposeFileAction, action_validation_error


def test_propose_file_action_json_schema_has_required_keys() -> None:
    schema = ProposeFileAction.json_schema()
    assert schema["required"] == ["path", "content"]
    assert schema["additionalProperties"] is False


def test_propose_file_action_from_json() -> None:
    action = ProposeFileAction.from_json(
        '{"path":"test_retry.py","content":"import pytest\\n"}'
    )
    assert action.path == "test_retry.py"
    assert action.content == "import pytest\n"
    assert action.as_tool_arguments() == {
        "path": "test_retry.py",
        "content": "import pytest\n",
    }


def test_propose_file_action_rejects_empty_path() -> None:
    with pytest.raises(ValueError, match="path"):
        ProposeFileAction.from_json('{"path":"  ","content":"x"}')


def test_action_validation_error_is_structural() -> None:
    message = action_validation_error("missing content")
    assert "ProposeFileAction" in message
    assert "Protocol violation" in message
