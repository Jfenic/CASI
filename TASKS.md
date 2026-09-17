# Current Tasks

Last updated: 2026-09-16.

## Now — Phase 12: protocol enforcement

**Strategy:** agent phase state machine + schema per phase + repair fallback.
Detail: [docs/features/reliability/](docs/features/reliability/).

Baseline: **7/12** development (`qwen3.5:4b`). Target: **≥9/12**.

### Phase A — State machine (current)

- [x] `AgentPhase` + `resolve_phase` + `final_allowed` (`agent/phases.py`)
- [x] Reject illegal `final` in `ACTION_REQUIRED`; structural retry, not nudge-first
- [x] Unit tests for phase transitions and protocol violations
- [ ] Manual smoke: CREATE cannot succeed with prose-only `final`

### Phase B — CREATE constrained action

- [x] `ProposeFileAction` + Ollama single-schema `format` (`complete_action`)
- [x] Primary mutation path for CREATE when layout known
- [x] Phase-aware prompt (`build_create_action_prompt`)
- [ ] Re-measure `dev_009` + `dev_010` with `qwen3.5:4b`

### Phase C — Repair fallback

- [x] `normalize_response` + strict embedded-tool recovery (`llm/parser.py`)
- [x] Wire in `ollama_client` + optional loop safety net

### Phase D — Benchmark closure

- [x] Skip/soften CREATE patch verify when no test suite
- [x] `dev_005`, `dev_006`, `dev_011` (no rubric changes)
- [x] Full development benchmark + report (9/12 passed with qwen3.5:4b)
- [x] Git commits; close Phase 12

### Interactive Terminal UX Overhaul

- [x] Module 1: Presenter pattern, semantic palette, tree branches (`├─`, `└─`), compact diffs, line folding, spinner
- [x] Module 2: Test summary parsing, isolated failure trace, multi-option patch review `[y/N/v/save/?]`
- [x] Module 3: Readline tab completion for `/commands` and `@file` paths, persistent history (`~/.casi_history`), `/diff` command
- [ ] Module 4: `/undo` command, patch memento, session summary metrics

### Phase E — Optional (after D if needed)

- [ ] A/B native Ollama tool_calls vs schema-by-phase
- [ ] Evaluate vLLM for hard `tool_choice=required`

### Done (foundation)

- [x] Ollama JSON schema types (`integer` / `string`).
- [x] CREATE bootstrap without empty-repo `run_tests`.
- [x] Layout before mutation (`list_files` gate).

## Next

- [ ] Persist API/UI task history across restarts.
- [ ] Clarification answers over HTTP.
- [ ] Measure UI flow with real Ollama (`casi serve` + `casi ui`).

## Future

- [ ] Multi-phase orchestration (supervisor graph) — after Phase 12 closes.
- [ ] Node.js and additional project ecosystems.

## Bugs / sharp edges

- [x] Empty-repo CREATE may loop on “no tests ran” during patch verification (Phase D).
- [ ] Third-party Starlette/httpx/AnyIO deprecation warnings in API tests.

## Done recently (remove after next release note)

- [x] Capabilities v2 benchmark extension.
- [x] Phase 11 — Streamlit UI, live trace in API.

## Validation

```bash
uv run --no-sync ruff check src tests benchmarks/development
uv run --no-sync pytest -ra
```

Benchmark (requires Ollama):

```bash
casi benchmark --tasks-dir benchmarks/development/tasks \
  --repos-dir benchmarks/development/repositories \
  --model qwen3.5:4b --output /tmp/development.json --format both
```

Historical checklist: [TODO.md](TODO.md). Phase roadmap: [planning.md](planning.md).
