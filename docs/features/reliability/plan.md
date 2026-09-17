# Reliability — implementation plan

Last updated: 2026-09-16.

## Strategy

Replace “prompt → JSON → guess intent” with:

```text
agent phase → typed action channel → validation → execution → verify → final
```

Priority order:

1. **State machine** — `final` illegal when action is required.
2. **Schema per phase** — model cannot legally emit `final` during CREATE mutation.
3. **Repair fallback** — normalize embedded tool JSON if strict rules pass.
4. **Measure** — spot benchmark, then full development run.

**Not in scope for this track:** LangGraph migration, rubric changes, semantic-only nudges as primary fix.

## Components

| Area | Files |
| --- | --- |
| Agent phases | `src/casi/agent/phases.py` (new), `loop.py` |
| LLM constrained calls | `src/casi/llm/ollama_client.py`, `ollama_policy.py` |
| Action schemas | `src/casi/llm/actions.py` (new, Pydantic) |
| Parser / repair | `src/casi/llm/parser.py` |
| Response policy | `src/casi/agent/response_policy.py`, `nudges.py` |
| Prompts | `src/casi/llm/prompts.py` (phase-aware, not dual grammar in ACTION) |
| Create / verify | `create_workflow.py`, `patch_verify.py` |

---

## Phase A — State machine foundation

**Objective:** the runtime decides what response kinds are legal; the model cannot
end a mutation task with `final` before a validated action runs.

### Deliverables

- [x] `AgentPhase` enum and `resolve_phase(...)` from intent + conversation state.
- [x] `final_allowed(phase) -> bool` helper with unit tests.
- [x] In `AgentLoop._run_steps`: when `kind == final` and not allowed → structural
  retry (append user message with protocol error), do not call `evaluate_nudge` first.
- [x] Trace records phase transitions and protocol violations.
- [x] Legacy exception: final with embedded unified diff still proceeds to verify.

### Structural retry template (example)

```text
Protocol violation: FinalResponse is illegal while phase=ACTION_REQUIRED.
Expected a validated propose_file action. Retry with the required schema only.
```

### Tests

- [x] CREATE without patch: `final` → retry, loop continues.
- [x] INSPECT / conversation: `final` still accepted.
- [x] After successful `propose_file`: phase allows verify then final.

### Exit criteria

- [x] Unit tests pass; no behaviour change for non-mutation intents.
- [ ] Manual smoke: CREATE task cannot succeed with prose-only `final`.

---

## Phase B — Constrained action schema (CREATE)

**Objective:** eliminate `dev_009` / `dev_010` class failures by removing `final`
from the grammar during mandatory mutation turns.

### Deliverables

- [x] `ProposeFileAction` model (`path: str`, `content: str`) in `llm/actions.py`.
- [x] `OllamaClient.complete_action(messages, action)` for single-schema turns.
- [x] CREATE + `ACTION_REQUIRED` + layout known → `ProposeFileAction` schema only.
- [x] Validated action → `propose_file` via existing tool execution path.
- [x] Phase-specific prompt (`build_create_action_prompt`); no dual grammar on schema turn.

### Tests

- [x] Fake client + schema path produces `propose_file` execution.
- [x] Ollama payload uses single JSON schema (unit test with monkeypatch).
- [ ] Invalid schema → structural retry (Ollama client retries; loop integration TBD).
- [ ] Large `content` strings handled (document max size if Ollama truncates).

### Exit criteria

- [ ] Spot benchmark `dev_009` + `dev_010` with `qwen3.5:4b`:
  `tools≥1`, `patches_proposed≥1`.
- Failures, if any, are test quality / mutations — not missing file delivery.

---

## Phase C — Repair fallback (normalization)

**Objective:** recover tool-shaped JSON embedded in `final` when phases B strict
path still misses (compatibility layer).

### Deliverables

- [x] `extract_tool_call_payload(text) -> dict | None` in `parser.py`.
- [x] `normalize_response(LLMResponse) -> LLMResponse` with strict rules:
  - known tool name
  - arguments pass tool schema
  - exactly one action
  - current phase permits that tool
- [x] Wire in `OllamaClient._parse_payload` and optional loop safety net.
- [x] Log `recovered_embedded_tool_call` when fallback fires.

### Tests

- [x] `type:final` wrapping `propose_file` → tool_call.
- [x] Genuine final unchanged; invalid JSON unchanged; clarification unchanged.

### Exit criteria

- [x] Normalization tests green.
- [ ] Re-run `dev_009` / `dev_010` if Phase B alone insufficient.

---

## Phase D — Benchmark closure

**Objective:** reach **≥9/12** development benchmark; document residual gaps.

### Deliverables

- [ ] Skip or soften patch sandbox verification when CREATE repo has no tests.
- [ ] Task-specific fixes without rubric changes:
  - [ ] `dev_005` — TTL zero contract
  - [ ] `dev_006` — `propose_file` missing `content` (schema enforcement should help)
  - [ ] `dev_011` — version exceptions without invented imports
- [ ] Extend ACTION schema pattern to FIX where needed (read + propose phases).
- [ ] Full development benchmark with `qwen3.5:4b`.
- [ ] Dated report under `docs/reports/`.
- [ ] Update [TASKS.md](../../../TASKS.md); delete [.agent/progress.md](../../../.agent/progress.md).

### Exit criteria

- **≥9/12** independent acceptance on documented command.
- `pytest -ra` and ruff clean.
- Small descriptive git commits.

---

## Phase E — Transport experiments (optional)

**Objective:** improve inspect/fix reliability or hard tool requirement only if
Phase A–D miss target.

### Options (evaluate in order)

1. Native Ollama `tool_calls` + `think=True` on INSPECT profiles (A/B vs JSON protocol).
2. Schema-by-phase for FIX (`ProposeFileAction` after sufficient context).
3. vLLM with `tool_choice=required` if Ollama cannot enforce actions reliably.

### Exit criteria

- Documented A/B report; adopt only if measurable benchmark gain without security regression.

---

## Completed steps (retained)

1. [x] Map Python types → JSON Schema for Ollama.
2. [x] Skip bootstrap `run_tests` when CREATE repo has no tests.
3. [x] Relax CREATE tool set and search redirect rules.
4. [x] Require repository layout before mutation; gate `propose_file`.

## Superseded approach

The following is **no longer the primary plan**:

- Rely on semantic nudges alone after `type:final`.
- Tool-call normalization as the only fix (now Phase C fallback).
- Removing `complete_tool_call` permanently (Phase B reintroduces as primary for ACTION).
- LangGraph migration before protocol enforcement (deferred).

---

## Validation

```bash
uv run --no-sync ruff check src tests benchmarks/development
uv run --no-sync pytest -ra

# Spot CREATE tasks (Ollama required)
casi benchmark --tasks dev_009 dev_010 \
  --tasks-dir benchmarks/development/tasks \
  --repos-dir benchmarks/development/repositories \
  --model qwen3.5:4b --output /tmp/dev-create-spot.json --format both

# Full development measurement
casi benchmark --tasks-dir benchmarks/development/tasks \
  --repos-dir benchmarks/development/repositories \
  --model qwen3.5:4b --output docs/reports/development-latest.json --format both
```

## Phase summary

| Phase | Objective | Key outcome |
| --- | --- | --- |
| **A** | State machine | `final` illegal in ACTION_REQUIRED |
| **B** | CREATE schema | `ProposeFileAction` only; fixes dev_009/010 |
| **C** | Repair fallback | Normalize embedded tool JSON (strict) |
| **D** | Benchmark closure | ≥9/12, report, remaining dev tasks |
| **E** | Transport A/B | Optional native tools / vLLM |
