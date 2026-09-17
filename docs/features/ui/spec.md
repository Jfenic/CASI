# Visual interface — specification

Status: **implemented** (Phase 11, 2026-09-14).

## Goal

Let a user run tasks, review agent steps, inspect patches and tests, and
approve or reject changes without using the terminal.

## Requirements (met)

- Submit repository path and task via Streamlit.
- Poll API for status, trace, metrics, patch, test output.
- Approve or reject when status is `awaiting_approval`.
- Show where execution runs (repo path, API URL, model).
- Live progress while task is `pending` / `running`.

## Out of scope (remaining)

- Persistent task history after API restart.
- Answering agent clarification prompts from the UI.
- Replacing Streamlit with a SPA (future if needed).

## Usage

```bash
pip install -e ".[ui,api]"
casi serve --port 8000
casi ui --api-url http://127.0.0.1:8000
```

Implementation: `src/casi/ui/`.
