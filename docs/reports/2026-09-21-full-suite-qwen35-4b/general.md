# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 26 |
| task_success_rate | 96.15% |
| agent_success_rate | 96.15% |
| command_success_rate | 76.92% |
| patch_validity_rate | 100.00% |
| average_steps | 7.85 |
| average_duration_seconds | 20.84 |
| average_files_read | 1.42 |
| average_correction_attempts | 0.08 |
| total_prompt_tokens | 128351 |
| total_completion_tokens | 4729 |

## Tasks

- `task_001` (inspect): **pass** — 6 steps, 12.32s
- `task_002` (read): **pass** — 3 steps, 10.25s
- `task_003` (search): **pass** — 4 steps, 7.92s
- `task_004` (read): **pass** — 6 steps, 13.22s
- `task_005` (inspect): **pass** — 4 steps, 6.88s
- `task_006` (fix): **pass** — 7 steps, 15.76s
- `task_007` (fix): **pass** — 12 steps, 25.27s
- `task_008` (fix): **pass** — 7 steps, 10.75s
- `task_009` (read): **pass** — 14 steps, 36.06s
- `task_010` (fix): **pass** — 9 steps, 11.27s
- `task_011` (fix): **pass** — 9 steps, 14.12s
- `task_012` (inspect): **pass** — 8 steps, 13.71s
- `task_013` (fix): **pass** — 7 steps, 7.72s
- `task_014` (read): **pass** — 8 steps, 14.67s
- `task_015` (fix): **pass** — 9 steps, 13.24s
- `task_016` (search): **pass** — 5 steps, 13.08s
- `task_017` (fix): **pass** — 8 steps, 11.11s
- `task_018` (search): **pass** — 4 steps, 10.28s
- `task_019` (read): **pass** — 6 steps, 8.17s
- `task_020` (fix): **pass** — 6 steps, 18.60s
- `task_021` (create): **pass** — 6 steps, 12.52s
- `task_022` (create): **pass** — 6 steps, 8.31s
- `task_023` (create): **fail** — 27 steps, 210.69s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> nudge: empty model response: Ollama action response does not contain content
- `task_024` (fix): **pass** — 9 steps, 14.09s
- `task_025` (fix): **pass** — 7 steps, 10.66s
- `task_026` (fix): **pass** — 7 steps, 11.14s
