# Current Progress

## Direction

Protocol enforcement & Interactive Terminal UX Overhaul

## Working on

**Interactive Terminal UX Overhaul** — Modules 1, 2, 3 complete; Module 4 pending.

## Completed

### Interactive Terminal UX Overhaul (2026-09-17)

- `src/casi/terminal/`:
  - `theme.py`: semantic 4-role palette, TTY detection, NO_COLOR, ASCII fallback.
  - `tree.py`: composite hierarchical tree renderer (`├─`, `└─`, badges, status).
  - `diff_view.py`: compact unified diff parser with +X/-Y stats and syntax coloring.
  - `fold.py`: intelligent output folding for long multi-line outputs.
  - `spinner.py`: non-blocking background daemon thread spinner (<200ms).
  - `test_summary.py`: extraction of clean summary lines and isolated failure traces.
  - `review.py`: multi-action interactive review loop `[y/N/v/save/?]`.
  - `completion.py`: readline completion for slash commands and `@file` repository paths.
  - `line_editor.py`: persistent `~/.casi_history` and terminal TTY readline bindings.
  - `presenter.py`: unified presenter facade.
- `src/casi/interactive.py`: integrated `TerminalPresenter`, `/diff` command, and `@file` mentions.
- `src/casi/cli.py`: added `--plain` flag.
- Tests: 43 new unit tests across 8 suites (491 total passed).

### Phase D — Soften CREATE verify & contract nudges (2026-09-17)

- `patch_verify.py`: soften patch verification on empty-repo CREATE when no tests exist in repo and pytest exits with 5.
- `loop.py`: pass `intent` to `verify_patch_response`; use `resolve_task_intent` in `_resolve_intent`.
- `prompts.py`: contract guidance for zero vs negative TTL (`dev_005`), deepcopy requirements (`dev_006`), and avoiding hallucinated imports/modules (`dev_011`).
- Tests: `test_sandbox_integration.py` coverage for CREATE empty repo verification. Full suite: 448 passed.

### Phase C — Repair fallback (2026-09-16)

- `extract_tool_call_payload`: nested final/tool_call wrappers, single-action guard.
- `normalize_response(..., allowed_tools=...)`: strict schema + known-tool recovery.
- `OllamaClient._parse_payload`: passes tools, validates recovered tool calls.
- `AgentLoop`: safety net with `step_tools`; trace `recovered_embedded_tool_call`.
- Tests: parser strict rules + ollama final-wrapped recovery.

### Phase B — CREATE constrained action (2026-09-16)

- `src/casi/llm/actions.py`: `ProposeFileAction`, validation, JSON schema.
- `OllamaClient.complete_action()`: Ollama `format` = schema only; no `final` branch.
- `AgentLoop._request_model_decision()`: CREATE + ACTION_REQUIRED + layout → schema path.
- `build_create_action_prompt()` in `prompts.py`.
- Tests: `test_actions.py`, `test_ollama_client` action test, CREATE integration test.

### Phase A — state machine

- `phases.py`, illegal `final` in ACTION_REQUIRED, structural retry.

## Next

1. Git commits; close Phase 12.
2. Persist API/UI task history across restarts.

Delete this file when Phase 12 closes.
