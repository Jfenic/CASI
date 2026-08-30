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

Build the sandbox image when Docker isolation is required:

```bash
docker build -t casi-sandbox:latest -f docker/sandbox.Dockerfile .
```

## Tools and safety

The agent can use these registered tools:

- `list_files`, `read_file`, `search_code`, `git_diff`, `validate_patch` — allowed automatically
- `run_tests` — requires confirmation in interactive mode; uses Docker sandbox when available
- `apply_patch` — never callable by the agent; patches are proposed as unified diffs

`run_tests`, `casi test`, and the agent correction loop prefer `DockerRunner`
(sandbox copy, no network) when Docker and `casi-sandbox:latest` are available.
Otherwise they fall back to `LocalRunner`.

When the agent proposes a unified diff, CASI validates it, runs tests on an
isolated copy, and retries up to two times if tests fail before showing the
result for human approval.

In interactive mode, a valid unified diff in the model response is displayed with
sandbox test status and CASI asks `Apply patch? [y/N]` before writing. Rejecting
the prompt leaves the repository unchanged.

## Development

Run the test suite:

```bash
pytest
python3 -m compileall -q src tests
```

See also `planning.md`, `TODO.md`, and `docs/implementation-tracker.md`.
