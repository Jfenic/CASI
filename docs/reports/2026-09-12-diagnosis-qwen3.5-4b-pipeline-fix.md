# CASI Benchmark Report — qwen3.5:4b


> Post pipeline fix: transitive import preload for diagnose tasks (8 tasks, diag_008 PASS).

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 8 |
| task_success_rate | 87.50% |
| agent_success_rate | 100.00% |
| command_success_rate | 87.50% |
| patch_validity_rate | 0.00% |
| average_steps | 5.75 |
| average_duration_seconds | 17.58 |
| average_files_read | 2.75 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 17242 |
| total_completion_tokens | 907 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| bug_localization | 1 / 2 |
| failure_analysis | 2 / 2 |
| test_expectation_analysis | 1 / 1 |
| call_stack_diagnosis | 1 / 1 |
| requirement_mismatch_diagnosis | 1 / 1 |
| mini_project_integration | 1 / 1 |

## Tasks

- `diag_001` (diagnose): **pass** — 5 steps, 35.31s
- `diag_002` (diagnose): **fail** — 5 steps, 11.63s
  - error: Diagnosis grading failed: evidence missing expected symbol or expression
- `diag_003` (diagnose): **pass** — 5 steps, 8.08s
- `diag_004` (diagnose): **pass** — 5 steps, 16.88s
- `diag_005` (diagnose): **pass** — 5 steps, 11.74s
- `diag_006` (diagnose): **pass** — 7 steps, 22.09s
- `diag_007` (diagnose): **pass** — 5 steps, 22.30s
- `diag_008` (diagnose): **pass** — 9 steps, 12.60s
