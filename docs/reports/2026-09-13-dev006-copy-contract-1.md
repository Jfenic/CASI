# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 1 |
| task_success_rate | 0.00% |
| agent_success_rate | 0.00% |
| command_success_rate | 0.00% |
| patch_validity_rate | 0.00% |
| average_steps | 11.00 |
| average_duration_seconds | 112.49 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 21045 |
| total_completion_tokens | 2113 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| regression_and_mutability | 0 / 1 |

## Tasks

- `dev_006` (fix): **fail** — 11 steps, 112.49s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
