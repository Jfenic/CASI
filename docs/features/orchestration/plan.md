# Multi-Agent Orchestration & Specialized Personalities — Implementation Plan

Last updated: 2026-09-18.

## Strategy

Implement the feature incrementally across 5 modular phases, respecting existing design patterns (Factory, Strategy, Registry, Orchestrator), verifying each phase with deterministic tests before advancing.

---

## Phases

### Phase 1 — Closed Catalog of 7 Personalities (`src/casi/agent/profiles.py`)
- [x] Add `explain` profile with the mandatory 5-section technical explanation structure.
- [x] Add `test_engineer`, `refactor`, and `security` profiles with role boundaries and guidelines.
- [x] Add `AgentProfile.with_instructions(extra_instructions)` for non-destructive dynamic plan injection.
- [x] Add `AgentProfile.with_personality(...)` for dynamic role adaptation.
- [x] Unit tests for the 7 profiles and profile derivation methods.

### Phase 2 — Typed Intents & Permission Mapping (`src/casi/agent/intent.py`, `permissions.py`)
- [x] Add `TaskIntent.EXPLAIN`, `TEST_ENGINEER`, `REFACTOR`, `SECURITY` to `TaskIntent` enum.
- [x] Map intents to appropriate permission tiers (`READ` for explain/security, `MUTATE` for fix/refactor/test_engineer).
- [x] Update pipeline compatibility and response policy checks.
- [x] Unit tests for intent enums and tier mappings without regex reliance.

### Phase 3 — LLM Task Evaluator (`src/casi/agent/evaluator.py`)
- [x] Define `TaskEvaluation` dataclass (`objective`, `agent_role`, `tools_needed`, `plan_instructions`, `response_template`).
- [x] Implement `LLMTaskEvaluator` querying the model for structured task analysis against the closed catalog.
- [x] Implement deterministic fallback for tests when running with mock/fake LLM clients.
- [x] Unit tests for evaluator with mock responses and fallback behavior.

### Phase 4 — Factory & Orchestrator Integration (`factory.py`, `orchestrator.py`, `planner.py`)
- [x] Update `TaskPlanner` to invoke the evaluator and construct `AgentPlanStep` with the assigned personality and plan instructions.
- [x] Update `AgentFactory.create(...)` to accept plan instructions and configure the specialized agent.
- [x] Update `AgentOrchestrator` to inject the orchestrator plan into step execution.
- [x] Unit tests for orchestrator planning and execution with specialized agents.

### Phase 5 — User Interface & Commands (`interactive.py`, `cli.py`, `cli_help.py`, `completion.py`)
- [x] Add `/explain <path or symbol>` command in `src/casi/interactive.py`.
- [x] Add `/explain` to readline tab completion (`src/casi/terminal/completion.py`).
- [x] Document `/explain` in `src/casi/cli_help.py`.
- [x] Wire `casi ask` to default to the `explain` specialist.
- [x] Interactive and CLI unit tests.

---

## Validation Commands

```bash
uv run --no-sync ruff check src tests benchmarks/development
uv run --no-sync ruff format --check src tests benchmarks/development
uv run --no-sync pytest -ra
uv run --no-sync python -m compileall -q src tests
```
