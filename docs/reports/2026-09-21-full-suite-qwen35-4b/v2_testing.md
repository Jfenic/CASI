# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 4 |
| task_success_rate | 50.00% |
| agent_success_rate | 50.00% |
| command_success_rate | 50.00% |
| patch_validity_rate | 100.00% |
| average_steps | 14.50 |
| average_duration_seconds | 441.79 |
| average_files_read | 1.25 |
| average_correction_attempts | 0.50 |
| total_prompt_tokens | 21584 |
| total_completion_tokens | 7299 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| test_design | 0 / 1 |
| regression_test_design | 0 / 1 |
| boundary_regression_tests | 1 / 1 |
| integration_test_design | 1 / 1 |

## Tasks

- `test_001` (create): **fail** — 19 steps, 1006.24s
  - error: Patch changes disallowed files: retrying.py
- `test_002` (create): **fail** — 23 steps, 576.44s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> nudge: empty model response: Ollama action response does not contain content
- `test_003` (create): **pass** — 9 steps, 45.77s
- `test_004` (create): **pass** — 7 steps, 138.71s
