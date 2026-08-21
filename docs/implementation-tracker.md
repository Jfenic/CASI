# Implementation Tracker

Estado rapido del proyecto y de las partes ya implementadas.

## Done

- [x] Repository safety helpers: repository resolution, safe path checks, sensitive path blocking, symlink blocking, and `.git` ignoring.
- [x] Repository read helper: safe file reading, binary rejection, file size checks, and numbered line output.
- [x] Repository search helper: safe text search with path, line number, and line content results.
- [x] CLI commands: `inspect`, `read`, and `search`.
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
- [x] `run_tests` tool with local timeout and output limits.
- [x] `git_diff` read-only tool for working-tree and staged changes.

## In Progress / Pending

- [ ] LLM integration with the tool registry.
- [ ] Additional tools: `validate_patch`, `apply_patch`.
- [ ] Sandbox-backed tool execution for commands that need isolation.
- [ ] End-to-end benchmark execution and reporting.

## Notes

- The current package is still a scaffold, so `casi` is usable for the implemented repository operations, but the full agent workflow is not complete yet.
- The source tree uses `src/`, so local development works best with a virtual environment or `uv`.
- Baseline verification: the current test suite passes with `pytest -q`.
- Iteration 1 verification: 32 tests pass and `python3 -m compileall -q src tests` completes successfully.
- Ruff validation is pending because the `ruff` executable is not installed in the current environment.
- Ollama verification: server `0.32.11`; model `qwen2.5-coder:7b`, Q4_K_M, 32K context, native tools.
- `run_tests` currently uses the local runner with an explicit pytest command; Docker isolation remains pending.
- `git_diff` uses an explicit allowlisted Git command and does not modify the repository.
- Interactive mode currently starts a bounded agent run for each task; shared conversational context and permissions remain pending.
- Next implementation step: validate unified patches before adding mutation capabilities.