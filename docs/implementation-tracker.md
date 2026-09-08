# Implementation Tracker

Estado rapido del proyecto y de las partes ya implementadas.

## Done

- [x] Repository safety helpers: repository resolution, safe path checks, sensitive path blocking, symlink blocking, and `.git` ignoring.
- [x] Repository read helper: safe file reading, binary rejection, file size checks, and numbered line output.
- [x] Repository search helper: safe text search with path, line number, and line content results.
- [x] CLI commands: `inspect`, `read`, `search`, `run`, `ask`, `fix`, `interactive`, `test`, `serve`, and `help`.
- [x] Structured tool system: base tool model, structured result model, tool registry, and argument validation.
- [x] Initial tools: `list_files`, `read_file`, and `search_code`.
- [x] Unit tests for repository helpers, CLI, and tools.
- [x] Initial architecture, security, and evaluation contracts documented.
- [x] Provider-independent LLM response contract and strict JSON parser.
- [x] Bounded agent loop connected to the structured tool registry.
- [x] Ollama client with native tool-call and structured JSON response support.
- [x] Python package renamed from `casi_code_agent` to `casi` to match the CASI project name.
- [x] `casi run` connected to `AgentLoop` and `OllamaClient`.
- [x] Interactive terminal session with help, history, clear, plan controls, and exit commands.
- [x] System prompt and JSON response mode prevent unnecessary tool calls for casual input.
- [x] `run_tests` tool with timeout, output limits, and Docker-first runner selection.
- [x] `git_diff` read-only tool for working-tree and staged changes.
- [x] `validate_patch` tool with path, size, sensitivity, and Git applicability checks.
- [x] `apply_patch` function with dry-run default and explicit approval requirement.
- [x] Interactive diff display and human approval before applying a patch.
- [x] Tool permission policies with adaptive cumulative approval per task.
- [x] Persistent conversational context in interactive mode with `/clear` reset.
- [x] Patch tests for create, delete, rejection, and registry blocking.
- [x] `DockerRunner` with temporary repository copy, no network, and resource limits.
- [x] Non-root sandbox image user and runtime process limits.
- [x] Benchmark loader, metrics helpers, and report renderer.
- [x] Patch correction loop: validate diff, run tests on isolated copy, retry up to 2 times.
- [x] Clarification flow: auto `search_code` after user answers, block repeated scope questions.
- [x] Project-local pytest temp directory (`.pytest-tmp/`) to avoid `/tmp` ownership issues.
- [x] Content-addressed Docker environments for Python project dependencies, with explicit network-build approval and offline test execution.
- [x] Agent diagnostics with live traces, rejected-tool evidence, patch validation details, metadata, redaction, and JSON export.
- [x] Failure classification for code, dependency, Docker, timeout, and model-format errors.
- [x] Project test-command detection (`.casi/test-command`, Makefile `test:`).
- [x] Model-driven general agent with tool-based permission escalation.
- [x] Session plan recall via `get_session_plan` and `/plan`.
- [x] CLI patch workflow: `--save-patch`, confirmation before apply, `--yes`, verbose mode, and exit codes 0/1/2.
- [x] FastAPI task lifecycle with patch approval endpoints and `casi serve`.

## Current status

- Release stage: advanced alpha (`0.1.0`); the CLI workflow is usable locally.
- Verification baseline: `228 passed, 2 skipped`.
- Python compilation passes.
- The repair flow runs tests, loads failed tests and imported source files, asks the model for complete file content through `propose_file`, rebuilds the diff deterministically, and verifies it on an isolated copy.
- Python dependency environments support `uv.lock`, `poetry.lock`, `requirements.txt`, `requirements-dev.txt`, and `pyproject.toml` through content-addressed Docker images.
- Interactive diagnostics support `/trace on`, `/last-trace`, and structured JSON export with `/save-trace`.
- The local branch is ahead of `origin/main`; publication is pending.

## In progress

- [ ] Validate repair reliability with real Ollama runs (`OLLAMA_E2E=1`).
- [ ] Complete observability with structured logs, timings, aggregate metrics, and trace correlation.

## Later

- [ ] Expanded benchmark suite with reproducible repositories and model comparisons.
- [ ] Node.js and additional project ecosystems.
- [ ] Visual interface after the API contract is stable.

## Notes

- The package supports repository inspection, bounded agent runs, patch validation, sandboxed test verification, and human-approved writes.
- The source tree uses `src/`, so local development works best with a virtual environment or `uv`.
- Baseline verification: `pytest` reports 228 passed and 2 skipped.
- Ollama verification: server `0.32.11`; model `qwen2.5-coder:7b`, Q4_K_M, 32K context, native tools.
- `run_tests` and `casi test` prefer a matching project dependency image, then `casi-sandbox:latest`, and require explicit approval for local fallback on untrusted repositories.
- Next milestone: run Ollama E2E fixtures and complete Phase 9 observability.
