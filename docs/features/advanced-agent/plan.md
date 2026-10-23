# Advanced Coding Agent Architecture (CASI v2) — Implementation Plan

Last updated: 2026-10-14.

## Strategy

Implement the transition incrementally across **6 verified phases**, preserving existing test guarantees, backward compatibility for local models on Ollama, and full benchmark scores on `benchmarks/development/`.

---

## Phases

### Phase 1 — Model Provider Abstraction & OpenAI Support (`src/casi/llm/`)
- [x] Define `ModelProvider` abstract base class with unified message, tool call, and token usage types.
- [x] Implement `OpenAIProvider` with native `tool_calls` and responses handling.
- [x] Adapt `OllamaProvider` wrapping the existing `OllamaClient` logic.
- [x] Add provider configuration in `casi.toml` and CLI flags (`--provider openai|ollama`, `--model`).
- [x] Unit tests for provider adapters with mocks.
- [x] Benchmark comparison CLI integration (`casi benchmark --provider openai|ollama --model <name>`).

### Phase 2 — Isolated Worktree & Multi-File Patching (`src/casi/workspace/`)
- [x] Implement `WorktreeManager` for creating and managing ephemeral git worktrees under `.casi/worktrees/`.
- [x] Support multi-file patch generation: aggregate incremental file changes within the active worktree.
- [x] Adapt `DockerTestRunner` to execute test verification directly against the worktree path.
- [x] Extract clean unified multi-file diff for human approval (`[y/N/v/save/?]`).
- [x] Rollback and cleanup routines on task cancel or rejection.
- [x] Unit and integration tests for worktree lifecycle.


### Phase 3 — Semantic Code Navigation (`ripgrep` + AST) (`src/casi/tools/`)
- [ ] Implement `ripgrep` search tool with regex support, path globbing, and `.gitignore` awareness.
- [ ] Implement `find_symbol` tool using Python's `ast` (and extensible parser for other languages).
- [ ] Expose symbol signatures, docstrings, and line bounds without dumping full files into context.
- [ ] Wire semantic tools into `ToolRegistry` and agent profile permissions.
- [ ] Unit tests for symbol discovery, edge cases, and syntax error tolerance.

### Phase 4 — Sandboxed Diagnostic Terminal (`src/casi/tools/`)
- [ ] Define `DiagnosticRunner` executing whitelisted commands inside ephemeral Docker containers.
- [ ] Enforce security bounds: read-only mounts where appropriate, timeout limit (e.g. 30s), zero network by default.
- [ ] Structured command output truncation preserving tail failure traces.
- [ ] Add `run_diagnostic` tool restricted to `diagnose`, `fix`, and `test_engineer` profiles.
- [ ] Unit tests verifying whitelist enforcement, timeout termination, and error compaction.

### Phase 5 — Persistent Context & Memory (SQLite) (`src/casi/context/`, `src/casi/api/`)
- [ ] Implement SQLite schema and storage manager for task states, turns, decisions, and traces.
- [ ] Connect API endpoints to persist and reload sessions across server restarts.
- [ ] Update `casi ui` (Streamlit) to list and inspect historical sessions.
- [ ] Endpoint for submitting clarification responses on paused tasks (`awaiting_clarification`).
- [ ] Unit tests for database migrations, task retrieval, and trace replay.

### Phase 6 — Extensibility & External Integrations (MCP & Web Docs)
- [ ] Implement lightweight MCP (Model Context Protocol) client for discovering external tools.
- [ ] Add `fetch_documentation` and `web_search` tools with prompt-injection sanitization.
- [ ] Design VS Code extension bridge / language server protocol interface.
- [ ] End-to-end integration tests and documentation update.

---

## Validation & Verification

After every phase, the following validation commands must pass with zero errors:

```bash
uv run --no-sync ruff check src tests benchmarks/development
uv run --no-sync ruff format --check src tests benchmarks/development
uv run --no-sync pytest -ra
uv run --no-sync python -m compileall -q src tests
```
