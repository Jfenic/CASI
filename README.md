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

The default model is `qwen2.5-coder:7b`. Override it with
`LOCALCODE_AGENT_OLLAMA_MODEL` when needed.

The agent can run the repository's Pytest suite through the registered
`run_tests` tool. Local command execution is currently intended for development;
Docker isolation is planned for a later phase.

The registered `git_diff` tool can inspect working-tree changes or staged changes
without modifying files.
