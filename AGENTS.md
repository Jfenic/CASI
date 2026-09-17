# Agent Instructions

## Project

CASI is a local code agent for supervised repository work: read/search, propose
patches via `propose_file`, verify in Docker, human approval before apply.

Python 3.11+. Package: `src/casi`. CLI entry: `casi`.

## Before changing code

1. Read [TASKS.md](TASKS.md) for the current priority.
2. If the task maps to a feature folder, read its `spec.md` and `plan.md`.
3. Read [ARCHITECTURE.md](ARCHITECTURE.md) only for the modules you touch.
4. Inspect relevant source and tests before expanding scope.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md).

## Rules

- Keep diffs minimal and focused on the requested behavior.
- Reuse existing abstractions; match surrounding style and naming.
- Do not modify unrelated files or benchmarks unless the task requires it.
- Never expose `apply_patch` to the model; patches need validation and approval.
- Prefer deterministic tests; avoid requiring a live Ollama server in unit tests.
- Do not weaken benchmark rubrics to make a model pass; fix agent behavior instead.
- Do not add dependencies without justification in `pyproject.toml`.
- Update [TASKS.md](TASKS.md) or `.agent/progress.md` when closing a work block.

## Key modules

| Path | Responsibility |
| --- | --- |
| `src/casi/agent/` | Loop, planner, orchestrator, nudges, profiles |
| `src/casi/llm/` | Ollama client, JSON schema, prompts |
| `src/casi/tools/` | Tool registry and implementations |
| `src/casi/api/` | FastAPI task lifecycle |
| `src/casi/ui/` | Streamlit client over the API |
| `benchmarks/development/` | Independent acceptance suite (12 tasks) |

## Validation

```bash
uv run --no-sync ruff check src tests benchmarks/development
uv run --no-sync ruff format --check src tests benchmarks/development
uv run --no-sync pytest -ra
uv run --no-sync python -m compileall -q src tests
```

## Session continuity

If continuing work across sessions, read [.agent/progress.md](.agent/progress.md).
Update it at end of session; delete it when the feature is done.
