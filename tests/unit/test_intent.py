from casi.agent.intent import TaskIntent, build_task_context, classify_intent, task_requests_code_change
from casi.llm.base import ChatMessage


def test_classify_overview_prompts_in_spanish() -> None:
    assert classify_intent("dime que trata este proyecto") is TaskIntent.OVERVIEW
    assert classify_intent("lista la estructura del proyecto") is TaskIntent.OVERVIEW


def test_classify_meta_and_conversation() -> None:
    assert classify_intent("dime que modelo eres") is TaskIntent.META
    assert classify_intent("dime que tool tiene activada") is TaskIntent.META
    assert classify_intent("hola") is TaskIntent.CONVERSATION


def test_classify_inspect_and_fix() -> None:
    assert classify_intent("Explain what foo_bar does") is TaskIntent.INSPECT
    assert classify_intent("pasa los tests") is TaskIntent.FIX


def test_task_requests_code_change_detects_patch_prompts() -> None:
    assert task_requests_code_change("genera un parche valido") is True
    assert task_requests_code_change("provide a valid diff") is True


def test_build_task_context_keeps_recent_user_turns() -> None:
    messages = [
        ChatMessage(role="user", content="dime que puedo mejorar el archivo loop.py"),
        ChatMessage(role="assistant", content="¿Qué quieres mejorar?"),
        ChatMessage(role="user", content="quiero mejorar la legibilidad"),
    ]
    context = build_task_context("dime en que parte no se cumple", messages)

    assert "loop.py" in context
    assert "legibilidad" in context


def test_should_defer_clarification_for_inspect_and_named_files() -> None:
    from casi.agent.intent import should_defer_clarification

    assert should_defer_clarification(
        "Explain what foo_bar does",
        TaskIntent.INSPECT,
        repository_inspected=False,
    )
    assert should_defer_clarification(
        "Improve things please",
        TaskIntent.UNKNOWN,
        repository_inspected=False,
    ) is False
    assert should_defer_clarification(
        "Improve things please",
        TaskIntent.UNKNOWN,
        repository_inspected=True,
    )
