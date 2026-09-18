from __future__ import annotations

from casi.agent.evaluator import LLMTaskEvaluator, TaskEvaluation
from casi.agent.intent import TaskIntent
from casi.llm.base import ChatMessage, LLMResponse, ToolDefinition


class FakeEvaluatorClient:
    is_evaluator = True

    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls = 0

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        self.calls += 1
        return LLMResponse.final(self.response_text)


def test_evaluator_selects_explain_personality() -> None:
    json_response = """
    {
      "objective": "explain",
      "agent_role": "Code Explanation & Architecture Specialist",
      "tools_needed": ["read_file", "search_code", "list_files"],
      "plan_instructions": "1. Inspect memento.py\\n2. Explain in 5 sections",
      "reasoning": "User wants to understand memento.py architecture"
    }
    """
    client = FakeEvaluatorClient(json_response)
    evaluator = LLMTaskEvaluator(client)

    result = evaluator.evaluate("Explica qué hace memento.py")

    assert result.objective is TaskIntent.EXPLAIN
    assert result.agent_name == "explain"
    assert "Architecture Specialist" in result.agent_role
    assert "Inspect memento.py" in result.plan_instructions
    assert client.calls == 1


def test_evaluator_handles_markdown_fenced_json() -> None:
    fenced_response = """
    Here is my evaluation:
    ```json
    {
      "objective": "security",
      "agent_role": "Security Specialist",
      "tools_needed": ["read_file", "search_code"],
      "plan_instructions": "Audit inputs",
      "reasoning": "Audit requested"
    }
    ```
    """
    client = FakeEvaluatorClient(fenced_response)
    evaluator = LLMTaskEvaluator(client)

    result = evaluator.evaluate("Audit safe_path for traversal vulnerabilities")

    assert result.objective is TaskIntent.SECURITY
    assert result.agent_name == "security"


def test_evaluator_honors_explicit_category() -> None:
    client = FakeEvaluatorClient("")
    evaluator = LLMTaskEvaluator(client)

    result = evaluator.evaluate("random text", category="explain")

    assert result.objective is TaskIntent.EXPLAIN
    assert result.agent_name == "explain"
    assert "Propósito General" in result.plan_instructions
    # Explicit category does not need to query the LLM
    assert client.calls == 0


def test_evaluator_falls_back_on_malformed_llm_output() -> None:
    client = FakeEvaluatorClient("This is not json at all")
    evaluator = LLMTaskEvaluator(client)

    # Should not crash; falls back gracefully
    result = evaluator.evaluate("hola")

    assert isinstance(result, TaskEvaluation)
    assert result.objective is TaskIntent.CONVERSATION


def test_evaluator_skips_llm_when_client_does_not_opt_in() -> None:
    class PlainMockClient:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, messages, tools):
            self.calls += 1
            raise AssertionError(
                "complete() should not be called on plain mock clients"
            )

    client = PlainMockClient()
    evaluator = LLMTaskEvaluator(client)

    result = evaluator.evaluate("Inspect the repository")
    assert isinstance(result, TaskEvaluation)
    assert client.calls == 0
