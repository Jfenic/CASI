# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 4 |
| task_success_rate | 50.00% |
| agent_success_rate | 50.00% |
| command_success_rate | 50.00% |
| patch_validity_rate | 100.00% |
| average_steps | 17.00 |
| average_duration_seconds | 88.54 |
| average_files_read | 1.50 |
| average_correction_attempts | 0.25 |
| total_prompt_tokens | 80557 |
| total_completion_tokens | 3437 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| data_processing | 0 / 1 |
| regression_and_mutability | 0 / 1 |
| algorithm_and_validation | 1 / 1 |
| regression_test_design | 1 / 1 |

## Tasks

- `dev_003` (fix): **fail** — 25 steps, 150.92s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_006` (fix): **fail** — 28 steps, 124.46s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_008` (create): **pass** — 6 steps, 32.49s
- `dev_010` (create): **pass** — 9 steps, 46.28s
