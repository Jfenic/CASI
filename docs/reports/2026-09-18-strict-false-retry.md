# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 2 |
| task_success_rate | 50.00% |
| agent_success_rate | 50.00% |
| command_success_rate | 50.00% |
| patch_validity_rate | 100.00% |
| average_steps | 17.50 |
| average_duration_seconds | 124.30 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 48896 |
| total_completion_tokens | 3161 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| data_processing | 1 / 1 |
| regression_and_mutability | 0 / 1 |

## Tasks

- `dev_003` (fix): **pass** — 9 steps, 39.11s
- `dev_006` (fix): **fail** — 26 steps, 209.49s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
