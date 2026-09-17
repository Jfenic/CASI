# Implementation Tracker

> **Trabajo activo:** [TASKS.md](../TASKS.md). **Arquitectura:** [ARCHITECTURE.md](../ARCHITECTURE.md).

Estado rapido del proyecto y de las partes ya implementadas.

## Done

- [x] Repository safety helpers: repository resolution, safe path checks, sensitive path blocking, symlink blocking, and `.git` ignoring.
- [x] Repository read helper: safe file reading, binary rejection, file size checks, and numbered line output.
- [x] Repository search helper: safe text search with path, line number, and line content results.
- [x] CLI commands: `inspect`, `read`, `search`, `run`, `ask`, `fix`, `interactive`, `test`, `benchmark`, `serve`, and `help`.
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
- [x] Patch correction loop: validate diff, run tests on isolated copy, retry up to 4 times by default.
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
- [x] Streamlit visual interface with modular client/services/views and `casi ui`.
- [x] `GET /tasks` endpoint for recent task history in the API.
- [x] Structured execution logs, step timings, aggregate metrics, and trace export schema v2.
- [x] Initial benchmark suite with 26 reproducible tasks, isolated runner, and JSON/Markdown reports.
- [x] Separate 12-task development suite with withheld acceptance checks, allowed-file policies, reference validation, mutation testing, capability reports, and per-task artifacts.

## Current status

- Release stage: advanced alpha (`0.1.0`); usable for supervised local work.
- Verification on 2026-09-13 during milestone closure: `369 passed, 2 skipped` on Python 3.12.3, including Docker and API tests. Ruff lint, format, compilation, and `git diff --check` pass.
- The skipped tests are the opt-in Ollama repair fixture and the Docker-unavailable branch when Docker is present. Two third-party API test deprecation warnings remain.
- Diagnosis JSON objects now survive parsing, runtime validation, and grading. Invalid prose receives bounded format retries and cannot be reported as a successful diagnosis.
- Repair nudges use the latest patch-test failure; external traceback paths and installed/standard-library modules no longer produce misleading local-file guidance.
- Python proposals normalize terminal blank lines. Creation and repair instructions retain the complete user contract, including requirements absent from visible tests.
- Historical diagnosis evaluation on 2026-09-12: `4/5`, compared with `0/5` on September 11. The stabilization summary is incomplete; consult individual dated reports rather than treating it as a consolidated baseline.
- The September 11 baseline was general `20/26`, development `2/10`, ML `2/5`, diagnosis `0/5`. Subsequent runs use different models and expanded suites; preserve those distinctions when comparing rates.
- Local fallback now requires explicit opt-in, including when the Docker daemon or image is unavailable. Explicit local mode remains available for trusted code.
- Ollama retries unusable empty decisions at most twice; successful recovery includes token usage from all attempts. Malformed envelopes and transport errors are not retried by this policy.
- Test-writing nudges no longer label passing tests as failures, and retain the complete task contract. Creation instructions explicitly support test files.
- Code through `d37ef45` is committed. The isolation/reliability milestone changes remain uncommitted for review.
- Added deterministic grading regressions for repairs that pass visible tests but share mutable override values or miscount physical JSONL lines.

- Latest complete development measurement (2026-09-13, `qwen3.5:4b`): `7/12` independent success, `9/12` agent completion. No overall improvement over the first milestone run; failures concern TTL, missing proposal content, generated tests and version exceptions. See [closure](reports/2026-09-13-milestone-closure.md).

## Remaining work

See [TASKS.md](../TASKS.md) for the current checklist. Summary:
- [ ] Improve model reliability against the independent acceptance checks (Phase 12).
- [ ] Investigate the third-party Starlette/httpx/AnyIO deprecation warnings before the next dependency update.
- [ ] Node.js and additional project ecosystems.
- [ ] Persistent task storage for API and UI history across restarts.

## Validation notes

The first restricted test run did not finish. An unrestricted run completed with
one Docker startup timeout. A direct Docker probe and the subsequent complete
runs passed; the timeout was not reproduced. Local Docker/Ollama verification
requires access to those services from the execution environment.

See the dated report for commands, benchmark artifacts, and remaining failures.
