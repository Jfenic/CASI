# Changelog

## Unreleased

### Added

- Docker-first test execution for `run_tests` and `casi test` with local fallback.
- Patch correction loop: verify diffs on an isolated copy and retry up to 2 times when tests fail.
- Clarification flow improvements: automatic repository search after user answers scope questions.
- `/exit` support during clarification prompts in interactive mode.
- Project-local pytest temp directory via `tests/conftest.py` (`.pytest-tmp/`).

### Changed

- Interactive mode shows sandbox test results (`[tests:passed|failed]`) before patch approval.
- `AgentLoop` blocks repeated clarification loops once the user has answered.

## 0.1.0

- Initial project scaffold.
