# Current Progress

## Direction

Multi-Agent Orchestration & Closed Catalog of Specialized Personalities (Software Engineering Roles).
Reference: [docs/features/orchestration/](docs/features/orchestration/).

## State: Feature Completed & Validated

All 5 phases of the Multi-Agent Orchestration feature have been successfully implemented, linted, formatted, and verified.

### Summary of Accomplishments

1. **Closed Catalog of 7 Personalities (`src/casi/agent/profiles.py`):**
   - Implemented `explain` with mandatory 5-section technical structure (`Propósito General`, `Componentes Clave`, `Dependencias e Interacciones`, `Flujo de Datos y Ejecución`, `Puntos Clave para el Proyecto`).
   - Implemented `test_engineer`, `refactor`, and `security` profiles with strict least-privilege tool boundaries.
   - Added `AgentProfile.with_instructions()` and `with_personality()` for non-destructive dynamic plan injection.
   - Verified via `tests/unit/test_profiles.py`.

2. **Typed Intents & Permissions (`src/casi/agent/intent.py`, `permissions.py`, `pipelines.py`):**
   - Added `TaskIntent.EXPLAIN`, `TEST_ENGINEER`, `REFACTOR`, `SECURITY`.
   - Bounded tool execution per role; read-only roles cannot mutate files or apply patches.

3. **LLM Task Evaluator (`src/casi/agent/evaluator.py`):**
   - Implemented `LLMTaskEvaluator` and `TaskEvaluation` to analyze user tasks against the closed catalog without fragile regex patterns.
   - Added deterministic fallback for test doubles / mock clients.
   - Verified via `tests/unit/test_evaluator.py`.

4. **Factory & Orchestrator Integration (`planner.py`, `factory.py`, `orchestrator.py`):**
   - Wired dynamic plan generation into `TaskPlanner.create_plan` with evaluator.
   - Passed plan instructions and specialized roles to `AgentFactory.create`.
   - Fixed mock signature compatibility in `tests/unit/test_cli.py`.

5. **Terminal UX & Commands (`interactive.py`, `cli.py`, `completion.py`, `cli_help.py`):**
   - Added `/explain <path>` command to interactive session and readline completion.
   - Wired `casi ask` to default to `explain` category.
   - Fixed Ruff formatting, line lengths, and import issues across all touched modules.
   - All linters, formatters, compileall, and unit tests passing cleanly.

## Next Backlog Priority

According to [TASKS.md](TASKS.md): **API & UI Persistence & Hardening** (storage for tasks/traces across restarts, clarification answers over HTTP, end-to-end UI verification).
