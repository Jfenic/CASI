# Current Tasks

Last updated: 2026-10-14.

## Now — API & UI Persistence & Hardening (Phase 5 of CASI v2)

1. **Persist API/UI task history across restarts:**
   - [ ] Implement file or SQLite-backed storage for tasks and traces in `src/casi/api/`.
   - [ ] Ensure `casi ui` can reload and inspect past sessions across server restarts.
2. **Clarification answers over HTTP:**
   - [ ] Add endpoint to submit clarification answers for tasks paused in `awaiting_clarification`.
3. **End-to-end UI verification:**
   - [ ] Measure UI flow with real Ollama model (`casi serve` + `casi ui`) on real repository tasks.

## Next — Advanced Coding Agent (CASI v2) Initiative

Detailed specification: [docs/features/advanced-agent/spec.md](docs/features/advanced-agent/spec.md)
Implementation plan: [docs/features/advanced-agent/plan.md](docs/features/advanced-agent/plan.md)

1. **Phase 1 — Model Provider Abstraction & OpenAI Support (COMPLETED):**
   - [x] Abstract `ModelProvider` in `src/casi/llm/providers/` (`OpenAIProvider`, `OllamaProvider`).
   - [x] Native `tool_calls` handling and provider CLI selection (`--provider`, `--model`).
   - [x] Configuration via `casi.toml` and environment variables.
2. **Phase 2 — Isolated Worktree & Multi-File Patching (COMPLETED):**
   - [x] `WorktreeManager` in `src/casi/workspace/worktree.py` for ephemeral git worktrees under `.casi/worktrees/<task_id>`.
   - [x] Multi-file staging and diff extraction without touching user workspace.
   - [x] Non-git and detached HEAD fallback support.
   - [x] DockerTestRunner integration directly against worktree paths.
3. **Phase 3 — Semantic Code Navigation (`ripgrep` + AST):**
   - AST-based symbol locator (`find_symbol`) and `ripgrep` regex search.
4. **Phase 4 — Sandboxed Diagnostic Terminal:**
   - Whitelisted command execution inside ephemeral Docker containers.
5. **Phase 5 — Persistent Context & Memory:**
   - SQLite store for tasks, traces, and session resumption (completes current *Now* priorities).
6. **Phase 6 — Extensibility & External Integrations:**
   - MCP client, web doc fetching with anti-injection sanitization, and VS Code bridge.

- [ ] Investigate third-party Starlette/httpx/AnyIO deprecation warnings in API tests.

## Done recently

### Phase 2 — Isolated Worktree & Multi-File Patching (Closed: 2026-10-14)
- [x] Implemented `WorktreeManager` and `WorktreeSession` in `src/casi/workspace/worktree.py` with support for ephemeral git worktrees, detached HEAD states, and non-git fallback directory copies.
- [x] Supported multi-file patching, incremental mutations, and staging across multiple files (`write_file`, `stage_file`, `stage_files`, `delete_file`, `apply_patch`).
- [x] Integrated `DockerRunner` / `DockerTestRunner` to execute test verification directly against the worktree path (`run_in_worktree`).
- [x] Unified multi-file diff extraction against base commit (`get_diff`, `get_diff_stats`) and human review integration (`[y/N/v/save/?]`).
- [x] Pruning and rollback routines (`reset`, `cleanup`, `cleanup_all`, `remove_worktree`) ensuring worktrees and temporary branches are cleaned up cleanly.
- [x] Comprehensive unit tests in `tests/unit/test_worktree.py` covering creation, file isolation, diff extraction, review, and cleanup.

### Phase 1 — Model Provider Abstraction & OpenAI Support (Closed: 2026-10-14)
- [x] Defined `ModelProvider` protocol in `src/casi/llm/providers/base.py` with unified action, tool call, and token metrics contract.
- [x] Implemented `OpenAIClient` and `OpenAIProvider` in `src/casi/llm/providers/openai.py` with native `tool_calls`, action completion (`complete_action`), tool-call requirement recovery (`complete_tool_call`), token accounting, and stdlib HTTP request handling.
- [x] Implemented `OllamaProvider` in `src/casi/llm/providers/ollama.py` inheriting from `OllamaClient`.
- [x] Created provider factory `create_llm_client` in `src/casi/llm/providers/factory.py`.
- [x] Added `casi.toml` and environment variable support in `src/casi/config.py` (`Settings.from_toml`).
- [x] Added `--provider` (`ollama` | `openai`) and `--model` CLI options across `casi run`, `casi interactive`, and `casi benchmark`.
- [x] Added comprehensive unit tests in `tests/unit/test_openai_client.py`, `tests/unit/test_providers.py`, and `tests/unit/test_config.py`.

### Task Interpreter, 'create' Role, Empty-Repo Tolerance & Readline Fix (Closed: 2026-09-19)
- [x] Evaluator catalog expansion: Added `create` role (New File & Feature Specialist) to `EVALUATOR_SYSTEM_PROMPT` in `evaluator.py`.
- [x] Task Interpreter & Refiner: Pre-step task disambiguation (`refined_task`) with existing repository files context passed to the evaluator before agent loop starts (zero step consumption).
- [x] Dynamic step task assembly: `AgentOrchestrator._build_step_task` provides `refined_task` and `plan_instructions` across all specialized roles.
- [x] Empty-repo test tolerance: `patch_verify.py` and `create_workflow.py` (`require_actual_files=True`) recognize repositories without test files (`test_*.py`), allowing new file creation without failing on pytest exit code 5 (`no tests ran`).
- [x] Terminal Readline fix: Wrapped ANSI escape sequences in `Theme.user()` and `_apply_prompt` with `\001` and `\002` markers to fix prompt length calculation and line-wrapping overwriting in interactive mode.
- [x] Interactive error shield: Wrapped turn execution in `interactive.py` with `try...except Exception` to maintain the session active on unexpected exceptions.

### Error Sanitization & Permissive Control Characters in JSON Parser (Closed: 2026-09-18)
- [x] Length check `len()` and strategy-based error truncation (`truncate_by_strategy`, `sanitize_and_compact_error`).
- [x] Implemented `tail` strategy ("quedarse con lo último") to preserve failure assertions without flooding context.
- [x] Enabled permissive control characters (`strict=False`) in JSON parser across `parser.py`, `actions.py`, `diagnosis.py`, `ollama_client.py` for LLM multiline string code proposals.
- [x] Recovered `dev_003` (csv_totals), `dev_008` (dependency_order), and `dev_010` (slug_tests).
- [x] Development benchmark score reaches **11/12 (91.67%)** on `qwen3.5:4b`.

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
