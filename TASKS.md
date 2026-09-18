# Current Tasks

Last updated: 2026-09-18.

## Now — API & UI Persistence & Hardening

1. **Persist API/UI task history across restarts:**
   - [ ] Implement file or SQLite-backed storage for tasks and traces in `src/casi/api/`.
   - [ ] Ensure `casi ui` can reload and inspect past sessions across server restarts.
2. **Clarification answers over HTTP:**
   - [ ] Add endpoint to submit clarification answers for tasks paused in `awaiting_clarification`.
3. **End-to-end UI verification:**
   - [ ] Measure UI flow with real Ollama model (`casi serve` + `casi ui`) on real repository tasks.

## Next

- [ ] Investigate third-party Starlette/httpx/AnyIO deprecation warnings in API tests.
- [ ] Phase E (Optional): A/B test native Ollama `tool_calls` vs schema-by-phase; evaluate vLLM for hard `tool_choice=required`.

## Done recently

### Multi-Agent Orchestration & Closed Catalog of Personalities (Closed: 2026-09-18)
- [x] Phase 1: Closed catalog of 7 personalities in `profiles.py` (with 5-section `explain`).
- [x] Phase 2: Typed intents and permission mapping in `intent.py` and `permissions.py`.
- [x] Phase 3: `LLMTaskEvaluator` (`evaluator.py`) for structured task evaluation without regexes.
- [x] Phase 4: Factory and orchestrator integration with dynamic personality adaptation (`planner.py`, `factory.py`, `orchestrator.py`).
- [x] Phase 5: Interactive `/explain` command, tab completion, and CLI wiring (`interactive.py`, `cli.py`, `completion.py`).
- [x] Verification: Deterministic unit test suite passing (`test_evaluator.py`, `test_profiles.py`, `test_interactive.py`, `test_cli.py`).

### Phase 12 — Protocol Enforcement & Reliability (Closed: 2026-09-17)
- [x] `AgentPhase` state machine (`agent/phases.py`): reject illegal `final` in `ACTION_REQUIRED`.
- [x] `ProposeFileAction` Pydantic model (`llm/actions.py`) and single-schema constrained generation (`complete_action`) for CREATE mutations.
- [x] Strict embedded-tool fallback recovery parser (`normalize_response`, `extract_tool_call_payload`).
- [x] Softened patch verification on empty-repo CREATE tasks (handling pytest exit code 5).
- [x] Target reached: **9/12 (75%)** development benchmark score with `qwen3.5:4b` ([report](docs/reports/2026-09-17-development-phase12.md)).

### Interactive Terminal UX Overhaul (Closed: 2026-09-17)
- [x] Module 1: Presenter pattern, semantic palette, tree branches (`├─`, `└─`), compact diffs, line folding, spinner.
- [x] Module 2: Test summary parsing, isolated failure trace, multi-option patch review `[y/N/v/save/?]`.
- [x] Module 3: Readline tab completion for `/commands` and `@file` paths, persistent history (`~/.casi_history`), `/diff` command.
- [x] Module 4: `/undo` command via `PatchMementoStack` LIFO rollback, `/stats` and `/metrics` commands, session summary on exit.

### Foundation & UI
- [x] Phase 11: Streamlit visual interface (`casi ui`) modular client/services/views.
- [x] Capabilities v2 benchmark expansion (12 additional tasks).

## Future

- [ ] Multi-phase orchestration (supervisor graph: Inspector → Implementer → Verifier).
- [ ] Node.js and additional project ecosystems.

## Validation

```bash
uv run --no-sync ruff check src tests benchmarks/development
uv run --no-sync ruff format --check src tests benchmarks/development
uv run --no-sync pytest -ra
uv run --no-sync python -m compileall -q src tests
```
