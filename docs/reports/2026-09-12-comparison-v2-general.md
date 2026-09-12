# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 26 |
| task_success_rate | 80.77% |
| agent_success_rate | 80.77% |
| command_success_rate | 61.54% |
| patch_validity_rate | 100.00% |
| average_steps | 10.69 |
| average_duration_seconds | 23.61 |
| average_files_read | 1.31 |
| average_correction_attempts | 0.08 |
| total_prompt_tokens | 231581 |
| total_completion_tokens | 7196 |

## Tasks

- `task_001` (inspect): **pass** — 6 steps, 20.58s
- `task_002` (read): **pass** — 3 steps, 8.98s
- `task_003` (search): **pass** — 6 steps, 11.47s
- `task_004` (read): **pass** — 6 steps, 9.06s
- `task_005` (inspect): **pass** — 6 steps, 13.89s
- `task_006` (fix): **fail** — 26 steps, 52.32s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_007` (fix): **pass** — 25 steps, 60.08s
- `task_008` (fix): **pass** — 6 steps, 9.26s
- `task_009` (read): **pass** — 10 steps, 19.23s
- `task_010` (fix): **pass** — 6 steps, 7.94s
- `task_011` (fix): **pass** — 6 steps, 8.65s
- `task_012` (inspect): **pass** — 8 steps, 13.55s
- `task_013` (fix): **pass** — 10 steps, 20.24s
- `task_014` (read): **pass** — 4 steps, 6.21s
- `task_015` (fix): **pass** — 14 steps, 27.69s
- `task_016` (search): **pass** — 5 steps, 11.03s
- `task_017` (fix): **pass** — 9 steps, 15.34s
- `task_018` (search): **pass** — 10 steps, 18.33s
- `task_019` (read): **pass** — 4 steps, 7.74s
- `task_020` (fix): **fail** — 15 steps, 60.06s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_021` (create): **fail** — 19 steps, 39.11s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_022` (create): **pass** — 14 steps, 25.37s
- `task_023` (create): **fail** — 20 steps, 53.29s
  - error: Ollama message does not contain usable content
- `task_024` (fix): **pass** — 18 steps, 60.23s
- `task_025` (fix): **fail** — 16 steps, 26.54s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_026` (fix): **pass** — 6 steps, 7.68s


# CASI Benchmark Report — qwen2.5-coder:7b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 26 |
| task_success_rate | 84.62% |
| agent_success_rate | 84.62% |
| command_success_rate | 69.23% |
| patch_validity_rate | 100.00% |
| average_steps | 9.04 |
| average_duration_seconds | 20.01 |
| average_files_read | 1.27 |
| average_correction_attempts | 0.27 |
| total_prompt_tokens | 210888 |
| total_completion_tokens | 5867 |

## Tasks

- `task_001` (inspect): **pass** — 6 steps, 33.10s
- `task_002` (read): **pass** — 3 steps, 4.07s
- `task_003` (search): **pass** — 6 steps, 6.51s
- `task_004` (read): **pass** — 4 steps, 4.40s
- `task_005` (inspect): **pass** — 4 steps, 3.23s
- `task_006` (fix): **fail** — 28 steps, 62.53s
  - error: Agent reached the maximum of 12 steps without a valid patch. Last event:   -> nudge: The user requested a code change or passing tests. Tests are still failing: usr/local/lib/python3.11/importlib/__init__.py; test_validator.py; validator.py. Fix every remaining failure, not only the requirement mentioned in the task. Call read_file on the failing source and test files if you have not loaded them yet, then Call propose_file with the repository-relative path and the complete file content. CASI will build the unified diff; do not write the diff yourself. Do not describe the fix without calling propose_file.
- `task_007` (fix): **pass** — 7 steps, 10.71s
- `task_008` (fix): **pass** — 6 steps, 11.49s
- `task_009` (read): **pass** — 7 steps, 9.29s
- `task_010` (fix): **pass** — 6 steps, 5.67s
- `task_011` (fix): **pass** — 6 steps, 10.66s
- `task_012` (inspect): **pass** — 4 steps, 4.96s
- `task_013` (fix): **fail** — 25 steps, 47.99s
  - error: Agent reached the maximum of 12 steps without a valid patch. Last event:   -> nudge: blocked repeated read_file on test_greeter.py
- `task_014` (read): **pass** — 10 steps, 13.50s
- `task_015` (fix): **pass** — 11 steps, 16.63s
- `task_016` (search): **pass** — 5 steps, 4.09s
- `task_017` (fix): **pass** — 7 steps, 7.66s
- `task_018` (search): **pass** — 6 steps, 6.35s
- `task_019` (read): **pass** — 4 steps, 6.79s
- `task_020` (fix): **fail** — 30 steps, 172.10s
  - error: Patch verification failed after exhausting correction attempts: <stdin>:9: trailing whitespace.
 
<stdin>:24: trailing whitespace.
 
error: 2 lines add whitespace errors.
- `task_021` (create): **pass** — 5 steps, 6.08s
- `task_022` (create): **pass** — 5 steps, 5.15s
- `task_023` (create): **fail** — 20 steps, 32.81s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_024` (fix): **pass** — 6 steps, 10.85s
- `task_025` (fix): **pass** — 6 steps, 8.33s
- `task_026` (fix): **pass** — 8 steps, 15.18s
