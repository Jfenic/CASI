# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 12 |
| task_success_rate | 75.00% |
| agent_success_rate | 75.00% |
| command_success_rate | 75.00% |
| patch_validity_rate | 100.00% |
| average_steps | 12.00 |
| average_duration_seconds | 134.51 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 43216 |
| total_completion_tokens | 6245 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| boundary_conditions | 1 / 1 |
| input_validation | 2 / 2 |
| data_processing | 1 / 1 |
| business_rules | 1 / 1 |
| state_and_time | 1 / 1 |
| regression_and_mutability | 1 / 1 |
| module_creation | 1 / 1 |
| algorithm_and_validation | 0 / 1 |
| test_design | 0 / 1 |
| regression_test_design | 0 / 1 |
| mini_project_integration | 1 / 1 |

## Tasks

- `dev_001` (fix): **pass** — 9 steps, 40.09s
- `dev_002` (fix): **pass** — 9 steps, 23.16s
- `dev_003` (fix): **pass** — 9 steps, 65.97s
- `dev_004` (fix): **pass** — 9 steps, 26.11s
- `dev_005` (fix): **pass** — 7 steps, 18.73s
- `dev_006` (fix): **pass** — 9 steps, 48.29s
- `dev_007` (create): **pass** — 6 steps, 22.59s
- `dev_008` (create): **fail** — 23 steps, 688.06s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> nudge: empty model response: Ollama action response does not contain content
- `dev_009` (create): **fail** — 23 steps, 460.24s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> nudge: empty model response: Ollama action response does not contain content
- `dev_010` (create): **fail** — 23 steps, 194.16s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> nudge: empty model response: Ollama action response does not contain content
- `dev_011` (fix): **pass** — 7 steps, 11.09s
- `dev_012` (fix): **pass** — 10 steps, 15.59s
