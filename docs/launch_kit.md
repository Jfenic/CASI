# 🚀 CASI Community Launch Kit

This kit contains pre-formatted launch posts ready to submit on **Hacker News (Show HN)**, **Reddit (r/LocalLLaMA, r/Python)**, and **Twitter / X**.

---

## 1. Show HN: Hacker News

**URL**: https://news.ycombinator.com/submit  
**Title**:
```text
Show HN: CASI – A local code agent that tests in Docker before asking approval
```
*(Alternative title: `Show HN: CASI – An open-source local AI code agent with isolated sandboxes`)*

**Post Body**:
```text
Hi HN! We built CASI (Code Agent for Software Inspection), a local Python coding agent designed for supervised repository work: https://github.com/fenic/casi-code-agent

Like many here, we love the productivity of AI coding assistants, but we grew uncomfortable with two recurring problems in existing agents:
1. Cloud telemetry and code exfiltration (sending private proprietary codebases to remote servers).
2. Autonomous agents blindly executing arbitrary shell commands and writing changes directly to the host filesystem.

CASI takes the opposite, "zero-trust" approach:

• 100% Local: Runs against local Ollama models (default: qwen2.5-coder:7b) with zero network calls or telemetry. OpenAI is optional if desired.
• Isolated Sandbox: Verification test suites execute inside copy-on-run ephemeral Docker containers with disabled networking (--network none), non-root execution, and strict PID limits. Malicious code cannot phone home.
• Ephemeral Git Worktrees: Multi-file mutations and diagnostic edits happen under .casi/worktrees/<task_id>. Your active branch and unstaged changes remain completely untouched.
• Architectural Gatekeeper: The model is strictly forbidden from calling apply_patch. All proposed patches are presented as unified diffs and require explicit human review [y/N/v/save/?].
• Native Rollback: An undo stack (/undo) lets you revert applied patches with a single keystroke.

We also added a built-in health check (`casi doctor` / `/doctor`) to verify your local Ollama instance, Docker sandbox image, and git workspace in under a second.

On our independent development acceptance suite (12 real-world tasks covering ML algorithms, dependency graphs, CSV parsing, and API contracts), CASI achieves a 91.7% pass rate on qwen3.5:4b without weakening grader rubrics.

CLI, interactive REPL mode, and a visual Streamlit web UI (over a FastAPI backend) are all included.

We’d love to hear your feedback, thoughts on the safety model, and feature requests!

Repo: https://github.com/fenic/casi-code-agent
Architecture doc: https://github.com/fenic/casi-code-agent/blob/main/ARCHITECTURE.md
```

---

## 2. Reddit: r/LocalLLaMA

**Subreddit**: `r/LocalLLaMA`  
**Flair**: `Project` / `Software`  
**Title**:
```text
CASI: Open-source local code agent (Ollama) with Docker sandbox verification and mandatory human approval
```

**Post Body**:
```text
Hey everyone,

I've been working on **CASI**, an open-source, local-first code agent that runs on consumer hardware via Ollama:
👉 GitHub: https://github.com/fenic/casi-code-agent

### The Motivation
Most agentic tools either require cloud API keys or run commands directly on your bare-metal machine without safety boundaries. If the LLM hallucinates a command or tries to pull an untrusted package, your machine is at risk.

### How CASI Works
1. **Zero Cloud Requirement**: Built for local models (`qwen2.5-coder:7b`, `qwen3.5:4b`, etc.) using Ollama.
2. **Isolated Docker Sandbox**: Pytest suites run inside a container with networking disabled (`--network none`).
3. **Ephemeral Git Worktrees**: Experiments and patches take place in `.casi/worktrees/`, keeping your active branch clean.
4. **Human Gatekeeper Invariant**: The model *cannot* apply patches. It must submit a `propose_file` diff, run the sandbox tests to prove they pass, and ask for your approval (`[y/N/v/save/?]`).
5. **Interactive REPL**: Includes tab completion (`@file`), `/explain` for 5-section architecture summaries, `/status`, and instant `/undo` rollback.

### Quick Start
```bash
pip install -e ".[api,ui]"
docker build -t casi-sandbox:latest -f docker/sandbox.Dockerfile .

# Run diagnostics
casi doctor

# Start interactive mode
casi interactive --repo .
```

It also includes an independent benchmark suite where it scores 11/12 (91.7%) with `qwen3.5:4b`.

Feedback, contributions, and PRs are very welcome!
```

---

## 3. Twitter / X Thread

**Tweet 1 (Hook + GIF)**:
```text
Meet CASI 🛡️ — an open-source, local AI coding agent that runs tests in isolated Docker containers and never writes to your repo without approval.

100% private with Ollama.
Zero-network sandbox.
Instant /undo.

👇 Here is how it works:
[Attach docs/assets/demo.gif]
```

**Tweet 2 (The Problem)**:
```text
Most AI coding agents today either:
1. Upload your private codebase to third-party servers.
2. Blindly execute unconstrained shell commands on your host system.

CASI is built on a Zero-Trust architecture:
• Ephemeral git worktrees
• Docker sandbox (no network)
• apply_patch forbidden to the LLM
```

**Tweet 3 (Interactive CLI)**:
```text
The new interactive CLI feels like Claude Code / Antigravity:
• Automated environment check (`casi doctor`)
• Auto-complete repository paths with `@file`
• Architectural breakdowns with `/explain`
• Instant rollback with `/undo`
• Optional FastAPI + Streamlit visual UI
```

**Tweet 4 (CTA)**:
```text
CASI is free, open-source (MIT), and scores 91.7% on independent software development benchmarks.

⭐ Star on GitHub: https://github.com/fenic/casi-code-agent
📖 Documentation: https://fenic.github.io/casi/
```
