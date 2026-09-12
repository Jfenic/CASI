# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 26 |
| task_success_rate | 92.31% |
| agent_success_rate | 92.31% |
| command_success_rate | 69.23% |
| patch_validity_rate | 100.00% |
| average_steps | 9.08 |
| average_duration_seconds | 21.72 |
| average_files_read | 1.38 |
| average_correction_attempts | 0.12 |
| total_prompt_tokens | 177966 |
| total_completion_tokens | 6099 |

## Tasks

- `task_001` (inspect): **pass** — 8 steps, 12.41s
- `task_002` (read): **pass** — 3 steps, 8.90s
- `task_003` (search): **pass** — 6 steps, 10.44s
- `task_004` (read): **pass** — 6 steps, 11.23s
- `task_005` (inspect): **pass** — 4 steps, 5.84s
- `task_006` (fix): **pass** — 11 steps, 23.22s
- `task_007` (fix): **pass** — 18 steps, 47.74s
- `task_008` (fix): **pass** — 10 steps, 17.73s
- `task_009` (read): **pass** — 4 steps, 5.58s
- `task_010` (fix): **pass** — 6 steps, 9.51s
- `task_011` (fix): **pass** — 10 steps, 17.38s
- `task_012` (inspect): **pass** — 8 steps, 13.65s
- `task_013` (fix): **pass** — 6 steps, 7.70s
- `task_014` (read): **pass** — 4 steps, 6.13s
- `task_015` (fix): **pass** — 6 steps, 9.42s
- `task_016` (search): **pass** — 5 steps, 12.40s
- `task_017` (fix): **pass** — 17 steps, 24.98s
- `task_018` (search): **pass** — 4 steps, 8.26s
- `task_019` (read): **pass** — 8 steps, 12.90s
- `task_020` (fix): **pass** — 5 steps, 15.42s
- `task_021` (create): **fail** — 22 steps, 40.44s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_022` (create): **pass** — 5 steps, 60.41s
- `task_023` (create): **pass** — 18 steps, 75.43s
- `task_024` (fix): **pass** — 6 steps, 12.05s
- `task_025` (fix): **fail** — 28 steps, 82.01s
  - error: Ollama message does not contain usable content
- `task_026` (fix): **pass** — 8 steps, 13.56s
