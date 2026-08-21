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
```

Inside the session, use `/help`, `/history`, `/clear`, and `/exit`. Conversation
context is preserved between tasks until `/clear` resets it.

Casual messages such as `hola` are answered directly. Repository tools are
reserved for tasks that require inspecting the project.

The default model is `qwen2.5-coder:7b`. Override it with
`LOCALCODE_AGENT_OLLAMA_MODEL` when needed.

## Tools and safety

The agent can use these registered tools:

- `list_files`, `read_file`, `search_code`, `git_diff`, `validate_patch` — allowed automatically
- `run_tests` — requires confirmation in interactive mode
- `apply_patch` — never callable by the agent; patches are proposed as unified diffs

Local command execution is intended for development. Docker isolation is available
through `DockerRunner` for sandboxed test execution on a temporary repository copy.

In interactive mode, a valid unified diff in the model response is displayed and
CASI asks `Apply patch? [y/N]` before writing. Rejecting the prompt leaves the
repository unchanged.

## Development

Run the test suite:

```bash
pytest
python3 -m compileall -q src tests
```

See also `planning.md`, `TODO.md`, and `docs/implementation-tracker.md`.
