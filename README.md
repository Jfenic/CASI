# CASI

CASI (Code Agent for Software Inspection) is a local Python agent that inspects
repositories, proposes patches, runs tests in an isolated sandbox, and asks for
human approval before writing changes.

## Stack

- Python 3.11+
- Ollama (local LLM)
- Pytest (target project tests)
- Docker (optional sandbox)
- FastAPI + Streamlit (optional API and UI)

## Quick start

```bash
pip install -e ".[api,ui]"
docker build -t casi-sandbox:latest -f docker/sandbox.Dockerfile .

casi inspect --repo .
casi run --repo . --task "Explain the repository structure"
casi interactive --repo .
```

API and UI (two terminals):

```bash
casi serve --port 8000
casi ui --api-url http://127.0.0.1:8000
```

Default model: `qwen2.5-coder:7b` (`LOCALCODE_AGENT_OLLAMA_MODEL`).

## Development

```bash
uv sync --locked --group dev
uv run --no-sync ruff check src tests benchmarks/development
uv run --no-sync pytest -ra
```

Optional real-model check:

```bash
OLLAMA_E2E=1 uv run --no-sync pytest tests/integration/test_ollama_repair.py -ra
```

## Documentation

| Document | Purpose |
| --- | --- |
| [AGENTS.md](AGENTS.md) | How AI agents should work in this repo |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Modules, boundaries, workflows |
| [TASKS.md](TASKS.md) | Current and next work |
| [planning.md](planning.md) | Historical phase roadmap (reference) |
| [docs/](docs/) | Security, evaluation, reports, ADRs |

Active feature specs live under `docs/features/<name>/`.
