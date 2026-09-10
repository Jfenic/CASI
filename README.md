# CASI

CASI (Code Agent for Software Inspection) is a local code agent that can inspect repositories, suggest patches, run tests, and evaluate results.

## Structure

- `src/casi`: application package
- `tests`: unit and integration tests
- `benchmarks`: benchmark task definitions and expected results
- `docker`: sandbox container assets
- `scripts`: helper scripts
- `docs`: architecture, security, and evaluation notes

## Usage

Install the project in editable mode:

```bash
pip install -e .
```

Inspect a repository:

```bash
casi inspect --repo .
casi read --repo . --file README.md
casi search --repo . --query "AgentLoop"
```

Run the repository test suite:

```bash
casi test --repo .
```

For a Python project with external dependencies, prepare a cached environment
once before testing it:

```bash
casi env prepare --repo /path/to/project
casi test --repo /path/to/project
```

Preparation detects `uv.lock`, `poetry.lock`, `requirements.txt`, or
`pyproject.toml`, displays the selected files and image name, and requires
explicit confirmation before running a network-enabled Docker build. Use
`--yes` only in an already approved automated workflow. The image name includes
a hash of the dependency files, so changing them selects a new environment.

Run the agent with the configured Ollama model:

```bash
casi run --repo . --task "Explain the repository structure"
```

Start an interactive session:

```bash
casi interactive --repo .
# Backward-compatible alias:
casi run interactive --repo .
```

Inside the session, use `/help`, `/history`, `/clear`, and `/exit`. Conversation
context is preserved between tasks until `/clear` resets it.

For agent debugging, enable live tracing before a task and export the last run:

```text
CASI> /trace on
CASI> corrige los tests que fallan
CASI> /last-trace
CASI> /save-trace diagnostics/casi-trace.json
```

Traces include model decisions, deterministic pipeline reads, tool results,
runner and exit status, rejected calls, steering messages, and exact patch
validation failures. Large source arguments are shortened and argument names
that indicate passwords, tokens, secrets, or keys are redacted.

With `-v` on `run`, `ask`, or `fix`, CASI also emits one structured JSON log
line to stderr with step timings, aggregate metrics, and token usage when the
model reports it. API task responses include the same `metrics` and
`execution` summaries after each run.

If the model asks for clarification, answer at the `Answer>` prompt. CASI will
search the repository automatically after you clarify scope. Use `/exit` to leave
during a clarification prompt.

Casual messages such as `hola` are answered directly. Repository tools are
reserved for tasks that require inspecting the project.

The default model is `qwen2.5-coder:7b`. Override it with
`LOCALCODE_AGENT_OLLAMA_MODEL` when needed.

Environment variables:

- `LOCALCODE_AGENT_USE_DOCKER` — prefer Docker sandbox for tests (default: `true`).
- `LOCALCODE_AGENT_MAX_CORRECTION_ATTEMPTS` — patch retry limit after test failures (default: `2`).
- `LOCALCODE_AGENT_DOCKER_IMAGE` — sandbox image tag (default: `casi-sandbox:latest`).

Run the benchmark suite:

```bash
casi benchmark --list
casi benchmark --model qwen2.5-coder:7b --output /tmp/benchmark.json --format both
casi benchmark --models qwen2.5-coder:7b,llama3.2 --format text
```

For typical development and test-writing tasks, use the separate
[development suite](benchmarks/development/README.md). Its ten tasks use
independent acceptance checks and mutation testing:

```bash
casi benchmark --tasks-dir benchmarks/development/tasks \
  --repos-dir benchmarks/development/repositories \
  --model qwen2.5-coder:7b --output /tmp/development.json --format both
```

Start the HTTP API (requires `pip install -e '.[api]'`):

```bash
casi serve --host 127.0.0.1 --port 8000
```

Swagger UI is available at `http://127.0.0.1:8000/docs`. Create a task with
`POST /tasks`, poll `GET /tasks/{task_id}`, then approve or reject a proposed
patch with `POST /tasks/{task_id}/approve` or `/reject`.

Build the sandbox image when Docker isolation is required:

```bash
docker build -t casi-sandbox:latest -f docker/sandbox.Dockerfile .
```

## Tools and safety

The agent can use these registered tools:

- `list_files`, `read_file`, `search_code`, `git_diff`, `validate_patch` — allowed automatically
- `run_tests` — requires confirmation in interactive mode; uses Docker sandbox when available
- `apply_patch` — never callable by the agent; patches are proposed as unified diffs

`run_tests`, `casi test`, and the agent correction loop prefer `DockerRunner`.
They automatically use a prepared, repository-specific dependency image when
its dependency hash matches. Otherwise they use `casi-sandbox:latest` when it is
available, then fall back to `LocalRunner`.

Environment preparation is the only network-enabled phase. Test execution uses
a temporary repository copy with no network and excludes VCS data, virtual
environments, caches, `.env` files, private keys, and known credential files.
The original repository is never mounted into the test container.

When the agent proposes a unified diff, CASI validates it, runs tests on an
isolated copy, and retries up to two times if tests fail before showing the
result for human approval.

In interactive mode, a valid unified diff in the model response is displayed with
sandbox test status and CASI asks `Apply patch? [y/N]` before writing. Rejecting
the prompt leaves the repository unchanged.

## Development

Prepare the development environment from the committed lockfile and run checks:

```bash
uv sync --locked --group dev
uv run --no-sync ruff check src tests benchmarks/development
uv run --no-sync ruff format --check src tests benchmarks/development
uv run --no-sync pytest -ra
uv run --no-sync python -m compileall -q src tests
```

CI runs the same checks on Python 3.11 and builds the Docker sandbox image
before running the suite. Locally, the Docker integration test is skipped when
the daemon is unavailable. Real Ollama repair testing is opt-in:

```bash
OLLAMA_E2E=1 uv run --no-sync pytest tests/integration/test_ollama_repair.py -ra
```

This requires a running Ollama server with `qwen2.5-coder:7b` (or the configured
model). The test requires a proposed patch whose isolated test verification passes.

Latest validation: [P0/P1 stabilization report](docs/reports/2026-09-09-stabilization.md).

See also `planning.md`, `TODO.md`, and `docs/implementation-tracker.md`.
