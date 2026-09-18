# Changelog

## Unreleased

### Added

- **Phase 12 (Protocol Enforcement & Reliability):**
  - `AgentPhase` state machine (`src/casi/agent/phases.py`) rejecting prose-only `final` decisions when actions are required (`ACTION_REQUIRED`), triggering structural retries.
  - `ProposeFileAction` Pydantic model (`src/casi/llm/actions.py`) and single-schema constrained generation (`OllamaClient.complete_action`) for CREATE mutations.
  - Fallback recovery parser (`extract_tool_call_payload`, `normalize_response`) recovering tool calls embedded in `final` envelopes.
  - Softened patch verification on empty-repository CREATE tasks when no tests exist (handling Pytest exit code 5).
  - Contract guidance prompts for edge cases (`dev_005`, `dev_006`, `dev_011`), reaching a 9/12 (75%) success rate on the development benchmark with `qwen3.5:4b`.
- **Interactive Terminal UX Overhaul:**
  - `PatchMemento` and `PatchMementoStack` (`src/casi/patching/memento.py`) for safe patch rollback via the `/undo` command.
  - Live session metrics tracking tool calls, steps, duration, and patches (`src/casi/terminal/session_metrics.py`) with `/stats`, `/metrics`, and summary on exit.
  - Presenter pattern (`src/casi/terminal/presenter.py`), semantic theme palette, tree branch visualizer (`├─`, `└─`), compact/collapsible diffs, and spinner.
  - Pytest summary parser (`src/casi/terminal/test_summary.py`) with isolated failure traces.
  - Multi-option patch review prompt (`[y/N/v/save/?]`).
  - Readline completion for `/commands` and `@file` paths (`src/casi/terminal/completion.py`) and persistent command history (`~/.casi_history`).
- Versioned capability benchmark extension with twelve tasks: test writing, defensive security, and ML/feature extraction; independent reference validation and per-mutation checks.
- Interactive CLI, patch export and approval, FastAPI task lifecycle and serving (`casi serve`).
- Streamlit visual interface (`casi ui`) with modular client, services, and views.
- Cached Python dependency images with approved preparation and offline tests.
- Structured traces (schema v2), execution metrics, and per-task benchmark artifacts.
- General, development, diagnosis, ML, fundamentals, and security benchmark suites.
- Docker-first test execution for `run_tests` and `casi test` with explicit opt-in local fallback.
- Patch correction loop: verify diffs on an isolated copy and retry up to 4 times when tests fail.
- Clarification flow improvements: automatic repository search after user answers scope questions.
- `/exit` support during clarification prompts in interactive mode.
- Project-local pytest temp directory via `tests/conftest.py` (`.pytest-tmp/`).

### Changed

- Docker failures stop execution by default; local fallback requires explicit opt-in.
- Thinking-model JSON requests include full tool schemas and required arguments.
- Empty Ollama decisions receive at most two retries, retaining usage on recovery.
- Repair context preserves the task contract and uses the latest test failure.
- Interactive mode shows sandbox test results (`[tests:passed|failed]`) before patch approval.
- `AgentLoop` blocks repeated clarification loops once the user has answered.

## 0.1.0

- Initial project scaffold.
