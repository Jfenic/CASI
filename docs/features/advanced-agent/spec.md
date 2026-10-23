# Advanced Coding Agent Architecture (CASI v2) — Specification

Last updated: 2026-10-14.

## Goal

Evolve CASI from a local patch-oriented agent into a high-capability, multi-provider **Advanced Coding Agent**. This evolution enables CASI to leverage powerful commercial models (OpenAI GPT, Anthropic Claude) alongside local models (Ollama), equipped with native tool-calling, semantic repository comprehension (AST & ripgrep), sandboxed diagnostic terminal execution, isolated multi-file worktrees, and persistent project memory.

All capabilities strictly adhere to CASI's core principle: **safe, supervised execution with Docker isolation and mandatory human approval before changes touch the user's workspace**.

---

## Motivation & Problem Statement

Currently, CASI operates under constraints designed around small local LLMs (Qwen 4B–7B):
1. **Single-provider limitation:** The LLM client is coupled to Ollama and structured JSON generation per phase, unable to use native `tool_calls` protocols or parallel tool calling offered by modern frontier models.
2. **Sensory bandwidth bottleneck:** Code search is limited to basic text matches, lacking structural AST navigation (symbols, definitions, references) and fast regex searching across large codebases.
3. **Single-file patch scope:** `propose_file` produces changes one file at a time; tasks requiring cross-module refactors or test-driven changes in multiple files require complex, fragile iterations.
4. **Diagnostic blindness:** The agent cannot execute quick diagnostic commands (e.g. running an isolated test, inspecting a type with mypy, or testing a Python snippet) without submitting a full candidate patch.
5. **Session amnesia:** Server or session restarts lose task traces, historical context, and architectural decisions.

---

## Core Principles & Safety Invariants

1. **Human Approval Invariant:** The model **never** writes directly to the user's working tree. All mutations happen in ephemeral git worktrees, undergo Docker verification, and produce a unified diff for human review (`[y/N/v/save/?]`).
2. **Containerized Sandbox Invariant:** Any command or code execution requested by the agent runs strictly inside an isolated Docker container with timeouts, memory limits, and no host network access by default.
3. **Model-Agnostic Abstraction:** The agent runtime interacts with an abstract `ModelProvider`. Frontier models use native function calling; small local models continue using structured JSON schemas to prevent regressions.
4. **Benchmark-Driven Quality:** No capability is considered complete without passing both deterministic unit tests and the 12-task acceptance suite in `benchmarks/development/`.

---

## Target Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                        User Interfaces                      │
│            CLI  ·  Interactive  ·  Streamlit  ·  VS Code    │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                        Agent Runtime                        │
│         Orchestrator  ·  Evaluator  ·  Planner  ·  Nudges   │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
┌──────────────▼──────────────┐ ┌──────────────▼──────────────┐
│       Model Providers       │ │        Tool Registry        │
│  OpenAI  ·  Anthropic · Ollama│ │  Git · AST · Shell · Web · MCP│
└─────────────────────────────┘ └──────────────┬──────────────┘
                                               │
┌─────────────────────────────┐ ┌──────────────▼──────────────┐
│      Context & Memory       │ │       Safety & Sandbox      │
│  SQLite  ·  Traces  ·  Index│ │ Docker Runner · Git Worktree│
└─────────────────────────────┘ └─────────────────────────────┘
```

---

## Tool Ecosystem: Evolution

| Capability | Current State | Target State in CASI v2 |
| :--- | :--- | :--- |
| **Model Providers** | Ollama only (`LLMClient`) | Abstract `ModelProvider`: OpenAI (`tool_calls`), Anthropic, Ollama |
| **File Reading** | Line ranges & full text | Range reading + symbol-focused semantic extraction |
| **Code Search** | Substring / basic text search | `ripgrep` (regex, file filters, ignore rules) |
| **Code Understanding** | None (pure text) | AST symbol indexing (`find_symbol`, `list_declarations`, imports) |
| **Mutations** | Single-file patch (`propose_file`) | Multi-file proposals via ephemeral `git worktree` |
| **Command Execution** | Only predefined test suite in Docker | Controlled diagnostic terminal (whitelisted commands in Docker) |
| **Git Operations** | Basic diff computation | Status, log, blame, worktrees, isolated branches |
| **Memory & Context** | Ephemeral in-memory traces | SQLite persistence (tasks, traces, project facts) |
| **External Integrations** | Closed internal registry | MCP (Model Context Protocol) client for standardized external tools |
| **Web & Documentation** | None | Sandboxed web search & doc fetcher with injection filters |

---

## Component Specifications

### 1. Model Provider Abstraction (`src/casi/llm/providers/`)
- Unified interface `ModelProvider` supporting:
  - `generate_action(messages, tools, response_schema=None) -> ProviderAction`
  - Streaming token support and token consumption metrics.
  - Native function calling adapter (`OpenAIProvider`) translating internal `ToolDefinition` to OpenAI tools format.
  - Structured output adapter (`OllamaProvider`) preserving the existing schema-constrained generation for local models.

### 2. Isolated Workspace & Multi-File Mutations (`src/casi/workspace/`)
- `WorktreeManager`: Creates a detached git worktree in `.casi/worktrees/<task_id>/`.
- Allows applying incremental patches across multiple files inside the worktree.
- Runs `DockerTestRunner` against the worktree.
- Extracts clean unified diff against `HEAD` of the user's working branch for human approval.

### 3. Semantic Code Analysis (`src/casi/tools/code_tools.py`)
- `search_code`: Integrated with `ripgrep` for sub-second regex search honoring `.gitignore`.
- `find_symbol`: AST-based locator returning class, function, or method definitions, signature, docstring, and line ranges.
- Lightweight, zero-external-daemon implementation (Python `ast` / `tree-sitter`).

### 4. Sandboxed Diagnostic Shell (`src/casi/tools/shell_tools.py`)
- Exposes `run_diagnostic(command, timeout_seconds=30)`.
- Enforces command whitelist (e.g. `pytest`, `ruff`, `python -m`, `mypy`, `git`).
- Strict Docker execution with `--network none` and non-root user.

### 5. Persistent Context & Memory (`src/casi/context/`)
- SQLite storage backend: `tasks`, `turns`, `traces`, and `project_notes`.
- Seamless recovery: `casi serve` and `casi ui` can reload sessions across restarts.
