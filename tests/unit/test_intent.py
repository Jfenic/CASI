from casi.agent.intent import (
    TaskIntent,
    build_task_context,
    classify_intent,
    is_fast_path_intent,
    resolve_task_intent,
    task_requests_code_change,
)


def test_classify_overview_and_inspect_use_general_agent() -> None:
    assert classify_intent("dime que trata este proyecto") is TaskIntent.UNKNOWN
    assert classify_intent("lista la estructura del proyecto") is TaskIntent.UNKNOWN
    assert classify_intent("Explain what foo_bar does") is TaskIntent.UNKNOWN


def test_classify_meta_and_conversation_fast_paths() -> None:
    assert classify_intent("dime que modelo eres") is TaskIntent.META
    assert classify_intent("dime que tool tiene activada") is TaskIntent.META
    assert classify_intent("hola") is TaskIntent.CONVERSATION


def test_classify_fix_phrasing_uses_general_agent() -> None:
    assert classify_intent("pasa los tests") is TaskIntent.UNKNOWN
    assert classify_intent("busca el error y corrigelo") is TaskIntent.UNKNOWN
    assert classify_intent("corrígelo") is TaskIntent.UNKNOWN
    assert classify_intent("arreglalo") is TaskIntent.UNKNOWN
    assert classify_intent("vamos a agregar más prueba unitaria") is TaskIntent.UNKNOWN


def test_classify_plan_recall_requests() -> None:
    assert classify_intent("dime el plan") is TaskIntent.RECALL_PLAN
    assert classify_intent("cuál es el plan actual") is TaskIntent.RECALL_PLAN
    assert classify_intent("qué vas a hacer") is TaskIntent.RECALL_PLAN
    assert classify_intent("show me the plan") is TaskIntent.RECALL_PLAN


def test_is_fast_path_intent() -> None:
    assert is_fast_path_intent(TaskIntent.CONVERSATION) is True
    assert is_fast_path_intent(TaskIntent.RECALL_PLAN) is True
    assert is_fast_path_intent(TaskIntent.UNKNOWN) is False


def test_task_requests_code_change_still_detects_explicit_fix_verbs() -> None:
    assert task_requests_code_change("corrige validate_email") is True
    assert task_requests_code_change("Create the missing stats.py module") is True
    assert task_requests_code_change("vamos a agregar más prueba unitaria") is False


def test_resolve_task_intent_routes_code_change_to_fix() -> None:
    assert resolve_task_intent("corrige validate_email") is TaskIntent.FIX
    assert resolve_task_intent("Explain what foo_bar does") is TaskIntent.UNKNOWN
    assert resolve_task_intent("hola") is TaskIntent.CONVERSATION


def test_resolve_task_intent_routes_create_requests() -> None:
    assert (
        resolve_task_intent(
            "Create the missing stats.py module and make all tests pass."
        )
        is TaskIntent.CREATE
    )
    assert (
        resolve_task_intent("Implement helper", category="create") is TaskIntent.CREATE
    )
    assert resolve_task_intent("Fix bug", category="fix") is TaskIntent.FIX


def test_resolve_task_intent_routes_diagnose_category() -> None:
    assert (
        resolve_task_intent("Find the bug", category="diagnose") is TaskIntent.DIAGNOSE
    )


def test_resolve_task_intent_routes_ml_category_and_keywords() -> None:
    assert resolve_task_intent("Fix metrics", category="ml") is TaskIntent.ML
    assert (
        resolve_task_intent("Fix precision and recall in metrics.py") is TaskIntent.ML
    )
    assert resolve_task_intent("Fix pagination bug") is TaskIntent.FIX


def test_build_task_context_includes_recent_user_messages() -> None:
    from casi.llm.base import ChatMessage

    context = build_task_context(
        "corrígelo",
        [ChatMessage(role="user", content="Fix validate_email in src/app.py")],
    )
    assert "Fix validate_email" in context
    assert "corrígelo" in context
