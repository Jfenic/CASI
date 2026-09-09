from __future__ import annotations

from pathlib import Path

from casi.agent.intent import (
    derive_search_queries,
    extract_search_targets,
    task_requests_code_change,
)
from casi.agent.loop import AgentLoop
from casi.llm.base import ChatMessage, LLMResponse, ToolDefinition
from casi.patching.extract import extract_patch
from casi.tools.registry import ToolRegistry


class FakeClient:
    def __init__(self, responses: list[LLMResponse]) -> None:
        self.responses = iter(responses)
        self.calls: list[tuple[list[ChatMessage], list[ToolDefinition]]] = []

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        self.calls.append((messages[:], tools[:]))
        return next(self.responses)


def test_agent_loop_executes_tool_then_returns_final_response(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")
    client = FakeClient(
        [
            LLMResponse.tool_call("read_file", {"path": "README.md"}),
            LLMResponse.final("The file contains hello."),
        ]
    )

    result = AgentLoop(client, ToolRegistry(tmp_path), routing_mode="off").run("Inspect README.md")

    assert result.success is True
    assert result.response == "The file contains hello."
    assert result.steps == 2
    assert client.calls[0][1][1].name == "read_file"
    assert "hello" in client.calls[1][0][-1].content


def test_agent_loop_stops_at_step_limit(tmp_path: Path) -> None:
    client = FakeClient([LLMResponse.tool_call("list_files", {})] * 2)

    result = AgentLoop(client, ToolRegistry(tmp_path), max_steps=2, routing_mode="off").run("Inspect")

    assert result.success is False
    assert result.steps == 2
    assert "maximum of 2 steps" in (result.error or "")


def test_agent_loop_excludes_mutation_tools_from_definitions(tmp_path: Path) -> None:
    client = FakeClient([LLMResponse.final("done")])
    registry = ToolRegistry(tmp_path)

    AgentLoop(client, registry, routing_mode="off").run("Inspect")

    tool_names = {tool.name for tool in client.calls[0][1]}
    assert "apply_patch" not in tool_names
    assert "read_file" in tool_names


def test_fix_agent_hides_patch_validator_and_limits_tools_after_context(
    tmp_path: Path,
) -> None:
    (tmp_path / "module.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "test_module.py").write_text(
        "from module import value\n\ndef test_value():\n    assert value == 2\n",
        encoding="utf-8",
    )
    client = FakeClient(
        [
            LLMResponse.tool_call(
                "propose_file",
                {"path": "module.py", "content": "value = 2\n"},
            ),
        ]
    )

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        max_correction_attempts=0,
        require_tool_confirmation=lambda *_args: True,
        routing_mode="off",
    ).run("corrige el código")

    assert result.success is True
    assert "validate_patch" not in {tool.name for tool in client.calls[0][1]}
    limited_tool_sets = [
        {tool.name for tool in tools}
        for _, tools in client.calls
    ]
    assert {"read_file", "propose_file"} in limited_tool_sets


def test_fix_agent_allows_source_reread_after_inspection(tmp_path: Path) -> None:
    (tmp_path / "module.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "test_module.py").write_text(
        "from module import value\n\ndef test_value():\n    assert value == 2\n",
        encoding="utf-8",
    )
    client = FakeClient(
        [
            LLMResponse.tool_call("read_file", {"path": "module.py"}),
            LLMResponse.tool_call(
                "propose_file",
                {"path": "module.py", "content": "value = 2\n"},
            ),
        ]
    )

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        max_correction_attempts=0,
        require_tool_confirmation=lambda *_args: True,
        routing_mode="off",
    ).run("corrige module.py")

    assert result.success is True
    read_results = [
        message for message in result.messages
        if message.role == "tool" and message.content.startswith("tool=read_file")
    ]
    assert len(read_results) >= 2


def test_agent_loop_blocks_apply_patch_tool_call(tmp_path: Path) -> None:
    client = FakeClient(
        [
            LLMResponse.tool_call(
                "apply_patch",
                {"patch": "--- a/x\n+++ b/x\n", "approved": True, "dry_run": False},
            ),
            LLMResponse.final("Stopped"),
        ]
    )

    result = AgentLoop(client, ToolRegistry(tmp_path), routing_mode="off").run("Apply patch")

    assert result.success is True
    tool_message = client.calls[1][0][-1].content
    assert "success=False" in tool_message
    assert "Mutation tools cannot be executed" in tool_message


def test_agent_loop_requires_confirmation_for_run_tests(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n",
        encoding="utf-8",
    )
    client = FakeClient(
        [
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.final("Tests finished"),
        ]
    )
    confirmations: list[tuple[str, dict[str, object]]] = []

    def confirm(tool_name: str, arguments: dict[str, object]) -> bool:
        confirmations.append((tool_name, arguments))
        return False

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        require_tool_confirmation=confirm,
        routing_mode="off",
    ).run("Run tests")

    assert confirmations == [("run_tests", {})]
    assert result.success is True
    assert "Tool execution denied by user" in client.calls[1][0][-1].content


def test_agent_loop_bootstraps_repository_before_first_model_call(tmp_path: Path) -> None:
    (tmp_path / "validators.py").write_text(
        "def validate_email():\n    return True\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_validators.py").write_text(
        "def test_validate_email_rejects_missing_at_symbol():\n    pass\n",
        encoding="utf-8",
    )
    client = FakeClient(
        [
            LLMResponse.final("validate_email always returns True."),
            LLMResponse.final("validate_email always returns True."),
        ]
    )
    loop = AgentLoop(client, ToolRegistry(tmp_path))

    result = loop.run(
        "Explica qué hace validate_email y por qué falla "
        "test_validate_email_rejects_missing_at_symbol"
    )

    assert result.success is True
    tool_messages = [message for message in result.messages if message.role == "tool"]
    assert any("validate_email" in message.content for message in tool_messages)
    assert any("read_file" in message.content for message in tool_messages)


def test_agent_loop_runs_search_code_after_clarification(tmp_path: Path) -> None:
    (tmp_path / "validators.py").write_text(
        "def validate_email():\n    pass\n",
        encoding="utf-8",
    )
    client = FakeClient([LLMResponse.clarification("Which behavior should change?")])
    loop = AgentLoop(client, ToolRegistry(tmp_path), routing_mode="off")

    clarification = loop.run("Improve things please")
    assert clarification.clarification == "Which behavior should change?"

    client.responses = iter([LLMResponse.final("Found validate_email in validators.py.")])
    result = loop.run("Tighten validate_email to reject bad addresses")

    assert result.success is True
    assert result.response == "Found validate_email in validators.py."
    tool_messages = [message for message in result.messages if message.role == "tool"]
    assert any("validate_email" in message.content for message in tool_messages)
    assert client.calls[0][0][-1].role == "user"


def test_agent_loop_defers_clarification_for_actionable_repository_task(
    tmp_path: Path,
) -> None:
    (tmp_path / "module.py").write_text("def foo_bar():\n    return 1\n", encoding="utf-8")
    client = FakeClient(
        [
            LLMResponse.clarification("Which file should I inspect?"),
            LLMResponse.final("foo_bar is defined in module.py."),
        ]
    )

    result = AgentLoop(client, ToolRegistry(tmp_path), routing_mode="off").run("Explain what foo_bar does")

    assert result.success is True
    assert result.clarification is None
    assert result.response == "foo_bar is defined in module.py."
    assert client.calls[1][0][-1].content.startswith("Do not ask the user for more details yet")


def test_agent_loop_does_not_bootstrap_for_casual_greeting(tmp_path: Path) -> None:
    client = FakeClient([LLMResponse.final("Hola")])
    loop = AgentLoop(client, ToolRegistry(tmp_path), routing_mode="off")

    result = loop.run("hola")

    assert result.success is True
    tool_messages = [message for message in result.messages if message.role == "tool"]
    assert tool_messages == []


def test_agent_loop_prefetches_named_file_before_model_call(tmp_path: Path) -> None:
    (tmp_path / "planning.md").write_text("├── loop.py\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "agent").mkdir(parents=True)
    (tmp_path / "src" / "agent" / "loop.py").write_text(
        "def run():\n    pass\n",
        encoding="utf-8",
    )
    client = FakeClient([LLMResponse.final("El archivo define run().")])
    loop = AgentLoop(client, ToolRegistry(tmp_path))

    result = loop.run("dime que puedo mejorar el archivo loop.py")

    assert result.success is True
    transcript = "\n".join(message.content for message in result.messages)
    assert "src/agent/loop.py" in transcript
    assert "def run():" in client.calls[0][0][-2].content


def test_agent_loop_bootstraps_for_spanish_project_overview(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\nA sample repo.\n", encoding="utf-8")
    client = FakeClient(
        [
            LLMResponse.final("placeholder"),
            LLMResponse.final("Es un repositorio de demo."),
        ]
    )
    loop = AgentLoop(client, ToolRegistry(tmp_path))

    result = loop.run("dime que trata este proyecto")

    assert result.success is True
    assert result.response == "Es un repositorio de demo."
    tool_messages = [message for message in result.messages if message.role == "tool"]
    assert any("list_files" in message.content for message in tool_messages)
    assert any("read_file" in message.content for message in tool_messages)
    assert "sample repo" in client.calls[1][0][-2].content


def test_agent_loop_strict_mode_prefetches_overview_context(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\nA sample repo.\n", encoding="utf-8")
    client = FakeClient([LLMResponse.final("Es un repositorio de demo.")])
    loop = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        routing_mode="strict",
    )

    result = loop.run("dime que trata este proyecto")

    assert result.success is True
    tool_messages = [message for message in result.messages if message.role == "tool"]
    assert any("list_files" in message.content for message in tool_messages)
    assert any("read_file" in message.content for message in tool_messages)
    assert "sample repo" in client.calls[0][0][-2].content


def test_agent_loop_retries_malformed_json_final_response(tmp_path: Path) -> None:
    client = FakeClient(
        [
            LLMResponse.final('{"tool_response": {"error": null}}'),
            LLMResponse.final('{"type":"final","content":"CASI es un agente local."}'),
            LLMResponse.final("CASI es un agente local."),
        ]
    )

    result = AgentLoop(client, ToolRegistry(tmp_path), routing_mode="off").run("dime que trata este proyecto")

    assert result.success is True
    assert "CASI es un agente local." in result.response


def test_derive_search_queries_from_clarified_task() -> None:
    assert extract_search_targets(
        "Explica foo_bar y test_baz_failure"
    ) == ["foo_bar", "test_baz_failure"]
    assert derive_search_queries(
        "corrige la validación de email y agrega tests"
    ) == ["corrige", "validación", "email", "agrega", "tests"]
    assert derive_search_queries(
        "Tighten foo_bar to reject bad addresses"
    ) == ["foo_bar"]


def test_agent_loop_nudges_for_patch_when_fix_request_has_no_diff(tmp_path: Path) -> None:
    (tmp_path / "validators.py").write_text(
        "def validate_email(email: str) -> bool:\n    return True\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_validators.py").write_text(
        "from validators import validate_email\n\n"
        "def test_rejects_missing_at():\n"
        "    assert validate_email('bad') is False\n",
        encoding="utf-8",
    )
    patch = (
        "--- a/validators.py\n"
        "+++ b/validators.py\n"
        "@@ -1,2 +1,2 @@\n"
        "-def validate_email(email: str) -> bool:\n"
        "-    return True\n"
        "+def validate_email(email: str) -> bool:\n"
        "+    return '@' in email\n"
    )
    client = FakeClient(
        [
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.final("Aquí está la corrección propuesta para validators.py."),
            LLMResponse.final(patch),
        ]
    )

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        max_correction_attempts=0,
        require_tool_confirmation=lambda *_args: True,
        routing_mode="off",
    ).run("pasa los tests")

    assert result.success is True
    assert result.requested_code_change is True
    assert extract_patch(result.response) is not None
    assert client.calls[2][0][-1].content.startswith("The user requested a code change")


def test_task_requests_code_change_detects_pass_tests_prompt() -> None:
    assert task_requests_code_change("pasa los test puede?") is True
    assert task_requests_code_change("Explica validate_email") is False


def test_agent_loop_rejects_final_response_that_defers_repository_work(
    tmp_path: Path,
) -> None:
    (tmp_path / "module.py").write_text("def foo_bar():\n    pass\n", encoding="utf-8")
    client = FakeClient(
        [
            LLMResponse.final("Please provide the code for foo_bar."),
            LLMResponse.final("foo_bar is defined in module.py."),
            LLMResponse.final("foo_bar is defined in module.py."),
        ]
    )

    result = AgentLoop(client, ToolRegistry(tmp_path), routing_mode="off").run("Explain foo_bar")

    assert result.success is True
    assert result.response == "foo_bar is defined in module.py."
    assert client.calls[1][0][-1].content.startswith("The repository is available")


def test_agent_loop_reads_source_after_failed_tests(tmp_path: Path) -> None:
    (tmp_path / "sorter.py").write_text(
        "def bubble_sort(values: list[int]) -> list[int]:\n    return values\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_sorter.py").write_text(
        "from sorter import bubble_sort\n\n"
        "def test_bubble_sort_orders_ascending():\n"
        "    assert bubble_sort([2, 1]) == [1, 2]\n",
        encoding="utf-8",
    )
    patch = (
        "--- a/sorter.py\n"
        "+++ b/sorter.py\n"
        "@@ -1,2 +1,8 @@\n"
        " def bubble_sort(values: list[int]) -> list[int]:\n"
        "-    return values\n"
        "+    items = values[:]\n"
        "+    for i in range(len(items)):\n"
        "+        for j in range(0, len(items) - i - 1):\n"
        "+            if items[j] > items[j + 1]:\n"
        "+                items[j], items[j + 1] = items[j + 1], items[j]\n"
        "+    return items\n"
    )
    client = FakeClient(
        [
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.final(patch),
            LLMResponse.final(patch),
        ]
    )
    loop = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        max_correction_attempts=0,
        require_tool_confirmation=lambda *_args: True,
        routing_mode="off",
    )

    result = loop.run("revisa los test y corrige el error")

    assert result.success is True
    read_calls = [
        message.content
        for message in result.messages
        if message.role == "tool" and message.content.startswith("tool=read_file")
    ]
    assert read_calls
    assert any("sorter" in message for message in read_calls)


def test_agent_loop_redirects_repeat_search_code_to_read_file(tmp_path: Path) -> None:
    (tmp_path / "sorter.py").write_text(
        "def bubble_sort(values: list[int]) -> list[int]:\n    return values\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_sorter.py").write_text(
        "from sorter import bubble_sort\n\n"
        "def test_bubble_sort_orders_ascending():\n"
        "    assert bubble_sort([2, 1]) == [1, 2]\n",
        encoding="utf-8",
    )
    patch = (
        "--- a/sorter.py\n"
        "+++ b/sorter.py\n"
        "@@ -1,2 +1,8 @@\n"
        " def bubble_sort(values: list[int]) -> list[int]:\n"
        "-    return values\n"
        "+    items = values[:]\n"
        "+    for i in range(len(items)):\n"
        "+        for j in range(0, len(items) - i - 1):\n"
        "+            if items[j] > items[j + 1]:\n"
        "+                items[j], items[j + 1] = items[j + 1], items[j]\n"
        "+    return items\n"
    )
    client = FakeClient(
        [
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.tool_call("search_code", {"query": "bubble_sort"}),
            LLMResponse.tool_call("search_code", {"query": "bubble_sort"}),
            LLMResponse.final(patch),
            LLMResponse.final(patch),
        ]
    )
    loop = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        max_correction_attempts=0,
        require_tool_confirmation=lambda *_args: True,
        routing_mode="off",
    )

    result = loop.run("revisa los test y corrige el error")

    assert result.success is True
    assert "search_code results are already available" in client.calls[3][0][-1].content
    search_tool_results = [
        message
        for message in result.messages
        if message.role == "tool" and message.content.startswith("tool=search_code")
    ]
    assert len(search_tool_results) == 0


def test_agent_loop_nudges_when_propose_file_fails(tmp_path: Path) -> None:
    (tmp_path / "module.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "test_module.py").write_text(
        "from module import value\n\ndef test_value():\n    assert value == 2\n",
        encoding="utf-8",
    )
    patch = "--- a/module.py\n+++ b/module.py\n@@ -1 +1 @@\n-value = 1\n+value = 2\n"
    client = FakeClient(
        [
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.tool_call("read_file", {"path": "module.py"}),
            LLMResponse.tool_call(
                "propose_file",
                {"path": "module.py", "content": "value = 1\n"},
            ),
            LLMResponse.tool_call(
                "propose_file",
                {"path": "module.py", "content": "value = 2\n"},
            ),
            LLMResponse.final(patch),
        ]
    )

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        max_correction_attempts=0,
        require_tool_confirmation=lambda *_args: True,
        routing_mode="off",
    ).run("corrige module.py")

    assert result.success is True
    assert client.calls[3][0][-1].content.startswith(
        "propose_file could not build the patch"
    )
    assert "does not change the file" in client.calls[3][0][-1].content


def test_agent_loop_reuses_execute_permission_after_first_confirmation(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n",
        encoding="utf-8",
    )
    confirmations: list[str] = []

    def confirm(tool_name: str, arguments: dict[str, object]) -> bool:
        confirmations.append(tool_name)
        return True

    client = FakeClient(
        [
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.tool_call("run_tests", {}),
            LLMResponse.final("Tests finished"),
            LLMResponse.final("Tests finished"),
        ]
    )

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        require_tool_confirmation=confirm,
        routing_mode="off",
    ).run("Run tests")

    assert result.success is True
    assert confirmations == ["run_tests"]
