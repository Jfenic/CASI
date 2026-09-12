# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 9 |
| task_success_rate | 77.78% |
| agent_success_rate | 77.78% |
| command_success_rate | 77.78% |
| patch_validity_rate | 100.00% |
| average_steps | 10.11 |
| average_duration_seconds | 36.83 |
| average_files_read | 1.67 |
| average_correction_attempts | 0.11 |
| total_prompt_tokens | 74076 |
| total_completion_tokens | 3777 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| data_structures | 3 / 3 |
| search_algorithms | 1 / 1 |
| discrete_math | 0 / 1 |
| expression_evaluation | 1 / 1 |
| trees | 1 / 1 |
| sorting_algorithms | 1 / 1 |
| number_systems | 0 / 1 |

## Tasks

- `fund_001` (fix): **pass** — 6 steps, 12.98s
- `fund_002` (fix): **pass** — 7 steps, 10.96s
- `fund_003` (fix): **fail** — 11 steps, 53.83s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `fund_004` (fix): **pass** — 10 steps, 22.74s
- `fund_005` (fix): **pass** — 5 steps, 13.38s
- `fund_006` (fix): **pass** — 7 steps, 22.95s
- `fund_007` (fix): **pass** — 11 steps, 70.10s
- `fund_008` (fix): **fail** — 28 steps, 112.16s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `fund_009` (fix): **pass** — 6 steps, 12.35s
