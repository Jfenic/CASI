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

Run the agent with the configured Ollama model:

```bash
casi run --repo . --task "Explain the repository structure"
```

Start an interactive session:

```bash
casi interactive --repo .
```

Inside the session, use `/help`, `/history`, `/clear`, and `/exit`. Each task
is executed as a bounded agent run; conversational context is not yet shared
between tasks.

Casual messages such as `hola` are answered directly. Repository tools are
reserved for tasks that require inspecting the project.

The default model is `qwen2.5-coder:7b`. Override it with
`LOCALCODE_AGENT_OLLAMA_MODEL` when needed.

The agent can run the repository's Pytest suite through the registered
`run_tests` tool. Local command execution is currently intended for development;
Docker isolation is planned for a later phase.

The registered `git_diff` tool can inspect working-tree changes or staged changes
without modifying files.

The registered `validate_patch` tool checks a unified diff, protects repository
boundaries and sensitive files, and runs `git apply --check` without applying it.

The registered `apply_patch` tool defaults to dry-run. It writes files only when
both validation succeeds and explicit approval is supplied; it never creates a
Git commit automatically.

In interactive mode, a valid unified diff in the model response is displayed
and CASI asks `Apply patch? [y/N]` before writing. Rejecting the prompt leaves
the repository unchanged.
