# Reliability — specification

Last updated: 2026-09-16.

## Goal

Improve real-model success on the **development benchmark** (12 tasks with
independent acceptance checks) without changing rubrics or exposing hidden graders
to the agent.

Target: **≥9/12** with `qwen3.5:4b` and documented measurement command.

## Root cause (revised 2026-09-16)

The primary failure is **not** “thinking models cannot use tools”. It is:

```text
dual protocol (tool + final in the same channel)
    +
final allowed too early in mutation workflows
    +
no structural enforcement (only semantic nudges)
```

Observed on `dev_009` / `dev_010` after layout fix: model returns correct paths but
as `{"type":"final",...}` or prose; `tools=0`, `patches_proposed=0`.

## Architecture (target)

```text
INSPECT          read / list / search / test context
    ↓
ACTION_REQUIRED  mutation needed; final = ILLEGAL
    ↓
EXECUTE + VALIDATE  schema-valid action → ToolRegistry
    ↓
VERIFY           sandbox / diff / tests
    ↓
FINAL_ALLOWED    user-facing answer only when contract met
```

### Invariants (must hold after Phase 12)

1. Never complete a CREATE task without `mutation_succeeded=true`.
2. Never accept `final` while phase is `ACTION_REQUIRED`.
3. Never execute tool arguments that failed schema validation.
4. Never treat prose or `final.content` as proof a tool ran.

## Requirements

### Completed (foundation)

- [x] Valid JSON Schema types for Ollama structured output.
- [x] Skip bootstrap `run_tests` on empty CREATE repos.
- [x] Repository layout before mutation (`list_files` gate on `propose_file`).

### Phase A — Agent phase state machine

- Explicit `AgentPhase`: `INSPECT`, `ACTION_REQUIRED`, `VERIFY`, `FINAL_ALLOWED`.
- Phase derived from intent, mutation workflow, and patch/test state.
- Loop rejects `final` responses when phase forbids them.
- Structural retry messages (protocol violation), not only semantic nudges.

### Phase B — Constrained action schema (CREATE / mutation)

- In `ACTION_REQUIRED` for CREATE: Ollama `format` = single action schema
  (e.g. `ProposeFileAction`: `path`, `content`) — no `final` branch.
- Pydantic validation before `ToolRegistry.execute`.
- Re-enable constrained LLM path (`complete_tool_call` / schema-only call) as
  **primary** path for mandatory mutation turns, not recovery-only.

### Phase C — Repair fallback

- Tool-call normalization when model still returns tool-shaped JSON inside a
  `final` envelope (strict rules: known tool, valid schema, one action).
- Normalization is **fallback**, not the main architecture.

### Phase D — Benchmark closure

- Skip or soften patch sandbox verification when CREATE has no test suite.
- Address remaining dev gaps: `dev_005`, `dev_006`, `dev_011`.
- Full development measurement + dated report.

### Phase E — Transport experiments (optional, after D)

- A/B native Ollama `tool_calls` + thinking vs schema-by-phase on inspect profiles.
- Evaluate vLLM only if Phase A–D still miss target and hard `tool_choice` is needed.

## Out of scope

- Changing benchmark fixtures, rubrics, or mutation sets.
- LangGraph / LangChain migration (deferred; protocol enforcement first).
- Node.js or non-Pytest target projects.

## Success criteria

- **≥9/12** on full development run with unchanged rubrics.
- `dev_009` / `dev_010`: `tools≥1`, `patches_proposed≥1`, file delivered.
- No regression in unit/integration suite (`pytest -ra`).
- Residual failures documented with artifacts under `docs/reports/`.

Implementation detail: [plan.md](plan.md).
