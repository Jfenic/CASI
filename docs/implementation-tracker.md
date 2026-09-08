# Implementation Tracker

Estado rapido del proyecto y de las partes ya implementadas.

## Done

- [x] Repository safety helpers: repository resolution, safe path checks, sensitive path blocking, symlink blocking, and `.git` ignoring.
- [x] Repository read helper: safe file reading, binary rejection, file size checks, and numbered line output.
- [x] Repository search helper: safe text search with path, line number, and line content results.
- [x] CLI commands: `inspect`, `read`, `search`, `run`, `interactive`, and `test`.
- [x] Structured tool system: base tool model, structured result model, tool registry, and argument validation.
- [x] Initial tools: `list_files`, `read_file`, and `search_code`.
- [x] Unit tests for repository helpers, CLI, and tools.
- [x] Initial architecture, security, and evaluation contracts documented.
- [x] Provider-independent LLM response contract and strict JSON parser.
- [x] Bounded agent loop connected to the structured tool registry.
- [x] Ollama client with native tool-call and structured JSON response support.
- [x] Python package renamed from `casi_code_agent` to `casi` to match the CASI project name.
- [x] `casi run` connected to `AgentLoop` and `OllamaClient`.
- [x] Interactive terminal session with help, history, clear, and exit commands.
- [x] System prompt and JSON response mode prevent unnecessary tool calls for casual input.
- [x] `run_tests` tool with timeout, output limits, and Docker-first runner selection.
- [x] `git_diff` read-only tool for working-tree and staged changes.
- [x] `validate_patch` tool with path, size, sensitivity, and Git applicability checks.
- [x] `apply_patch` function with dry-run default and explicit approval requirement.
- [x] Interactive diff display and human approval before applying a patch.
- [x] Tool permission policies: read tools auto, execute tools confirmed in interactive mode, mutation tools blocked from the agent.
- [x] Persistent conversational context in interactive mode with `/clear` reset.
- [x] Patch tests for create, delete, rejection, and registry blocking.
- [x] `DockerRunner` with temporary repository copy, no network, and resource limits.
- [x] Benchmark loader, metrics helpers, and report renderer.
- [x] Patch correction loop: validate diff, run tests on isolated copy, retry up to 2 times.
- [x] Clarification flow: auto `search_code` after user answers, block repeated scope questions.
- [x] Project-local pytest temp directory (`.pytest-tmp/`) to avoid `/tmp` ownership issues.
- [x] Content-addressed Docker environments for Python project dependencies, with explicit network-build approval and offline test execution.
- [x] Agent diagnostics with live traces, rejected-tool evidence, patch validation details, metadata, redaction, and JSON export.

## Current status

- Release stage: advanced alpha (`0.1.0`); the CLI workflow is usable locally.
- Verification baseline: `193 passed, 1 skipped` with no collection errors or warnings.
- Python compilation and `git diff --check` pass.
- The repair flow runs tests, loads failed tests and imported source files, asks the model for complete file content through `propose_file`, rebuilds the diff deterministically, and verifies it on an isolated copy.
- Python dependency environments support `uv.lock`, `poetry.lock`, `requirements.txt`, `requirements-dev.txt`, and `pyproject.toml` through content-addressed Docker images.
- Interactive diagnostics support `/trace on`, `/last-trace`, and structured JSON export with `/save-trace`.
- The local branch is three commits ahead of `origin/main`; publication is pending.

## In progress

- [ ] End-to-end repair fixtures using the real Ollama model, including malformed output and recovery cases.
- [ ] Docker sandbox hardening with a non-root image user and stricter runtime limits.
- [ ] Clear dependency/infrastructure failure classification without unsafe silent fallback for untrusted repositories.
- [ ] Test-command detection beyond the current Python/Pytest default.
- [ ] Complete observability with structured logs, timings, aggregate metrics, and trace correlation across orchestrated agents.

## Later

- [ ] FastAPI task lifecycle with patch approval endpoints.
- [ ] Expanded benchmark suite with reproducible repositories and model comparisons.
- [ ] Node.js and additional project ecosystems.
- [ ] Visual interface after the API contract is stable.

## Notes

- The package supports repository inspection, bounded agent runs, patch validation, sandboxed test verification, and human-approved writes.
- The source tree uses `src/`, so local development works best with a virtual environment or `uv`.
- Baseline verification: `pytest` reports 193 passed and 1 skipped.
- Ruff validation is pending because the `ruff` executable is not installed in the current environment.
- Ollama verification: server `0.32.11`; model `qwen2.5-coder:7b`, Q4_K_M, 32K context, native tools.
- `run_tests` and `casi test` prefer a matching project dependency image, then `casi-sandbox:latest`, and currently fall back to `LocalRunner` when Docker infrastructure is unavailable.
- Proposed patches are verified with `run_patched_tests` on a temporary copy before the agent returns a final response.
- Patch validation uses Git recounting to tolerate incorrect hunk lengths from small local models while retaining path and applicability checks.
- `LOCALCODE_AGENT_USE_DOCKER` and `LOCALCODE_AGENT_MAX_CORRECTION_ATTEMPTS` configure sandbox and retry behavior.
- `git_diff` uses an explicit allowlisted Git command and does not modify the repository.
- `validate_patch` is non-mutating and must pass before apply.
- `apply_patch` is blocked through `ToolRegistry.execute`; interactive mode applies validated diffs after explicit `y`/`yes` confirmation.
- Interactive mode preserves conversation context between tasks until `/clear`.
- Ollama requests include a system prompt and `format=json`; casual greetings return final responses without repository tools.
- Next implementation milestone: prove repair reliability with real-model end-to-end fixtures, then harden sandbox isolation before exposing FastAPI.
