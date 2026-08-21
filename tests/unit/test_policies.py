from __future__ import annotations

from casi.agent.policies import (
    AGENT_TOOL_NAMES,
    ToolPermission,
    get_tool_permission,
    is_agent_tool,
    is_mutation_tool,
    requires_confirmation,
)


def test_tool_permissions_cover_registered_tools() -> None:
    assert "read_file" in AGENT_TOOL_NAMES
    assert "apply_patch" not in AGENT_TOOL_NAMES
    assert get_tool_permission("run_tests") == ToolPermission.EXECUTE
    assert get_tool_permission("apply_patch") == ToolPermission.MUTATE


def test_permission_helpers() -> None:
    assert is_agent_tool("search_code") is True
    assert is_agent_tool("apply_patch") is False
    assert requires_confirmation("run_tests") is True
    assert requires_confirmation("read_file") is False
    assert is_mutation_tool("apply_patch") is True
    assert is_mutation_tool("validate_patch") is False
