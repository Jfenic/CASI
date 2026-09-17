# Changelog

## Unreleased

### Added

- Versioned capability benchmark extension with twelve tasks: test writing,
  defensive security, and ML/feature extraction; independent reference validation
  and per-mutation checks, preserving historical suites.
- Interactive CLI, patch export and approval, FastAPI task lifecycle and serving.
- Cached Python dependency images with approved preparation and offline tests.
- Structured traces, execution metrics and per-task benchmark artifacts.
- General, development, diagnosis, ML, fundamentals and security benchmark suites.
- Independent acceptance checks and mutation scoring for generated tests.


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
