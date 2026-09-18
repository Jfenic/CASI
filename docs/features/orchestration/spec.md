# Multi-Agent Orchestration & Specialized Personalities — Specification

Last updated: 2026-09-18.

## Goal

Provide CASI with a modular, LLM-evaluated multi-agent orchestration architecture that routes repository work to a closed, robust catalog of **7 specialized software engineering personalities** with least-privilege tool access, concrete execution plans, and standardized response structures (notably the 5-section technical architecture breakdown).

---

## Motivation & Problem Statement

Previously, task routing relied on rigid regexes (`_CONVERSATION_PATTERN`, `_CHANGE_REQUEST_PATTERN`, etc.) or collapsed non-mutation tasks into `TaskIntent.UNKNOWN` with a generic agent. This caused two problems:
1. **Lack of deep understanding:** Read-only requests about files produced generic answers without structured architectural depth.
2. **Orchestrator hallucination risk:** If an LLM orchestrator is left unconstrained to invent roles and instructions from scratch, it can hallucinate invalid tools, unsafe scopes, or contradictory goals.

**Solution:** An LLM-based orchestrator that evaluates user requests against a **closed, hardened catalog of 7 software engineering personalities**, assigning each specialist an explicit plan and strictly bounded tools.

---

## Architecture

```text
User Request (CLI / Interactive / API)
                │
                ▼
      AgentOrchestrator
                │
                ▼
        LLMTaskEvaluator
   (Evaluates intent, picks 1 of 7 roles,
    bounds tools, produces step-by-step plan)
                │
                ▼
         AgentFactory
  (Configures SpecializedAgent with dynamic
   personality, role prompt & plan instructions)
                │
                ▼
       Specialized Agent
  (Executes within tool bounds and outputs
   prescribed structured format, e.g. 5-section markdown)
```

---

## Closed Catalog of 7 Personalities

| Personality | Objective (`TaskIntent`) | Role & Mission | Allowed Tools | Response Contract |
| :--- | :--- | :--- | :--- | :--- |
| **`explain`** | `TaskIntent.EXPLAIN` | **Code Explanation & Architecture Specialist**: Inspect files/modules and explain architecture, components, and project role. | `read_file`, `search_code`, `list_files` (Read-only) | Strict 5-section Markdown: Propósito, Componentes clave, Dependencias, Flujo de ejecución, Puntos clave. |
| **`diagnose`** | `TaskIntent.DIAGNOSE` | **Root Cause Diagnosis Specialist**: Trace test failures and bugs back to the exact faulty statement. | `run_tests`, `read_file`, `search_code` (No patch) | JSON with `file`, `line`, `cause`, `evidence`. |
| **`fix`** | `TaskIntent.FIX` | **Bug Fix & Patch Specialist**: Fix bugs and pass failing tests with minimal, focused diffs. | `read_file`, `search_code`, `run_tests`, `propose_file` | Valid unified diff via `propose_file`. |
| **`test_engineer`** | `TaskIntent.TEST_ENGINEER` | **Test Engineering & QA Specialist**: Write deterministic unit and integration tests covering edge cases and regressions. | `read_file`, `search_code`, `run_tests`, `propose_file` (scoped to `tests/`) | Test suite creation without mutating `src/`. |
| **`refactor`** | `TaskIntent.REFACTOR` | **Refactoring Specialist**: Improve code clarity, modularity, and typing while strictly preserving external behavior. | `read_file`, `search_code`, `run_tests`, `propose_file` | 100% test pass invariant. |
| **`security`** | `TaskIntent.SECURITY` | **Security & Defensive Audit Specialist**: Audit code for security vulnerabilities, secret leaks, and sanitization gaps. | `read_file`, `search_code`, `list_files` (Read-only) | Security audit report with risk level and defensive mitigation. |
| **`overview`** | `TaskIntent.OVERVIEW` | **Repository Overview Specialist**: Onboarding explanation of project purpose, layout, and entry points. | `list_files`, `read_file` (README/docs) | High-level onboarding guide. |

---

## Invariants

1. **No regex-based intent classification:** Intent evaluation is driven by LLM evaluation or explicit user command (`/explain`, `casi ask`).
2. **Least Privilege Tool Access:** Read-only specialists (`explain`, `security`, `overview`) can never call `propose_file` or `apply_patch`.
3. **5-Section Technical Structure for `explain`:** Explanations of files and code must strictly structure output under:
   - `### 1. Propósito General`
   - `### 2. Componentes Clave (Clases y Funciones)`
   - `### 3. Dependencias e Interacciones`
   - `### 4. Flujo de Datos y Ejecución`
   - `### 5. Puntos Clave para el Proyecto`
4. **Deterministic Testing:** All unit tests must pass without requiring a live Ollama server, using deterministic test doubles and fallbacks.
5. **No regressions:** All 505 existing unit, integration, and benchmark tests must remain green.

---

## Success Criteria

- Clean modular implementation adhering to SOLID principles.
- `/explain <path>` in interactive CLI and `casi ask` activate the `explain` specialist.
- All 7 personalities available and verified with unit tests.
- Full test suite passes: `pytest -ra` (505+ passed).
- Lint and format clean: `ruff check` and `ruff format`.
