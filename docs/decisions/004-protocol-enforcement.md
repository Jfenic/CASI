# 004: Protocol enforcement by agent phase

Status: accepted (2026-09-16).

## Context

Development benchmark failures (`dev_009`, `dev_010`) persist because the model
can return `final` while mutation is still required. CASI nudges semantically but
does not structurally forbid premature finals. A dual JSON grammar (tool vs final)
in prompts increases ambiguity.

Earlier plan focused on normalizing tool JSON out of `final` answers. That helps
but does not remove the root cause: **final remains a legal output during ACTION**.

## Decision

Adopt a phased protocol enforcement strategy:

1. **AgentPhase** state machine with `final` illegal in `ACTION_REQUIRED`.
2. **Schema per phase** for mandatory mutation (CREATE → `ProposeFileAction` only).
3. **Normalization** as strict repair fallback, not primary architecture.
4. Defer LangGraph migration until Phase 12 benchmark target is met.

## Consequences

- `complete_tool_call` / constrained Ollama `format` become primary for ACTION turns.
- Prompts become phase-aware; dual tool/final grammar removed from mutation turns.
- Structural retries replace many semantic nudges for protocol violations.
- More explicit loop state; easier to test invariants.

## Alternatives rejected

| Alternative | Why rejected |
| --- | --- |
| Normalization only | Does not prevent prose finals; treats symptom |
| LangGraph first | Does not fix protocol without same invariants in nodes |
| Disable thinking globally | Loses reasoning; Ollama supports think + structured output |
| `oneOf(tool, final)` in ACTION | Model can still pick wrong branch |

## Implementation

[reliability/plan.md](../features/reliability/plan.md)
