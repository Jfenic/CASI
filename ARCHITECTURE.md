# Architecture

CASI is an advanced alpha for **supervised local** repository work. CLI,
interactive mode, and the HTTP API share the same agent, patch validation, and
sandbox boundaries.

## Repository layout

```text
src/casi/
├── repository/     # Safe list/read/search
├── tools/          # Structured tool registry
├── llm/            # Ollama client, JSON parsing, prompts
├── agent/          # Planner, loop, orchestrator, nudges
├── patching/       # Diff validation and apply (human-approved)
├── sandbox/        # Local and Docker test runners
├── observability/  # Traces, metrics, structured logs
├── evaluation/     # Benchmark runner and reports
├── api/            # FastAPI task store (in-memory)
└── ui/             # Streamlit over HTTP

benchmarks/         # General, development, diagnosis, ML, …
docker/             # Sandbox image
tests/              # Unit and integration tests
```

## Runtime flow

```text
User task (CLI / API / UI)
    ↓
Task interpreter & evaluation (repository layout context, refined task, specialized profiles)
    ↓
Plan generation (sequential segments, step goals)
    ↓
Agent loop → tool calls (read, search, run_tests, propose_file, …)
    ↓
propose_file → unified diff (no direct repo write)
    ↓
Validate + sandbox tests (+ correction retries)
    ↓
Human approve / reject → apply_patch
```

`apply_patch` is **never** agent-callable. Test execution permission and patch
application are separate controls.

## Components

| Module | Role |
| --- | --- |
| `repository` | Path safety, sensitive file blocking, search |
| `tools` | Argument validation, permissions, execution |
| `llm` | Structured decisions; thinking models use JSON tool protocol |
| `agent` | Task interpreter, bounded loop, nudges, pipelines, patch verification |
| `patching` | Git-applicable diffs, size and path checks |
| `sandbox` | Copy-on-run tests; Docker without network by default |
| `observability` | Step traces, token metrics, export JSON |
| `evaluation` | Reproducible tasks + independent graders |
| `api` | Background tasks, live trace publish, patch approve/reject |
| `ui` | HTTP client, progress interpretation, Streamlit views |

## Multi-agent (current vs proposed)

**Implemented today:** `TaskPlanner` and `LLMTaskEvaluator` disambiguate the user
request into a `refined_task` with real repository layout context (without consuming
agent decision steps) and build sequential plans; `AgentOrchestrator` runs segments
with specialized profiles (read, fix, create, diagnose, test_engineer, …).

**Not implemented:** phased workers with a supervisor, dynamic step budget, or
clean context handoff per phase. See [TASKS.md](TASKS.md) → Future.

## Scope and limits

- Supported target stack: **Python + Pytest** for project under test.
- Docker tests: no network, non-root user, temp repo copy; original never mounted.
- Dependency images: optional network-enabled build, then offline test runs.
- API/UI task history: **in-memory** until persistence is added.

## Related docs

- [docs/security.md](docs/security.md)
- [docs/evaluation.md](docs/evaluation.md)
- [docs/decisions/](docs/decisions/) — ADRs
- [docs/reports/](docs/reports/) — benchmark and milestone reports

Legacy copy: [docs/architecture.md](docs/architecture.md) redirects here.
