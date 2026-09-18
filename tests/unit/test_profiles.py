from __future__ import annotations

from casi.agent.intent import TaskIntent
from casi.agent.profiles import resolve_profile


def test_resolve_new_software_personalities() -> None:
    explain = resolve_profile(TaskIntent.EXPLAIN)
    assert explain.name == "explain"
    assert "Code Explanation & Architecture Specialist" in explain.role
    assert "### 1. Propósito General" in explain.prompt_instructions
    assert "### 2. Componentes Clave" in explain.prompt_instructions
    assert "### 3. Dependencias e Interacciones" in explain.prompt_instructions
    assert "### 4. Flujo de Datos y Ejecución" in explain.prompt_instructions
    assert "### 5. Puntos Clave para el Proyecto" in explain.prompt_instructions

    test_eng = resolve_profile(TaskIntent.TEST_ENGINEER)
    assert test_eng.name == "test_engineer"
    assert "QA Specialist" in test_eng.role

    refactor = resolve_profile(TaskIntent.REFACTOR)
    assert refactor.name == "refactor"
    assert "Refactoring" in refactor.role

    security = resolve_profile(TaskIntent.SECURITY)
    assert security.name == "security"
    assert "Security" in security.role


def test_resolve_profile_by_string_name() -> None:
    assert resolve_profile("explain").objective is TaskIntent.EXPLAIN
    assert resolve_profile("test_engineer").objective is TaskIntent.TEST_ENGINEER
    assert resolve_profile("refactor").objective is TaskIntent.REFACTOR
    assert resolve_profile("security").objective is TaskIntent.SECURITY


def test_profile_with_instructions_derives_new_profile() -> None:
    base = resolve_profile(TaskIntent.EXPLAIN)
    derived = base.with_instructions("Focus on error handling in loop.py")

    assert derived is not base
    assert "Focus on error handling in loop.py" in derived.prompt_instructions
    assert "Orchestrator plan instructions:" in derived.prompt_instructions
    # Base profile remains unchanged
    assert "Focus on error handling in loop.py" not in base.prompt_instructions


def test_profile_with_empty_instructions_returns_same() -> None:
    base = resolve_profile(TaskIntent.EXPLAIN)
    assert base.with_instructions("") is base
    assert base.with_instructions("   ") is base


def test_profile_with_personality_derives_adapted_profile() -> None:
    base = resolve_profile(TaskIntent.EXPLAIN)
    adapted = base.with_personality(
        role="Custom Senior Architect",
        mission="Special review mission",
    )

    assert adapted.role == "Custom Senior Architect"
    assert adapted.mission == "Special review mission"
    assert adapted.objective == base.objective
