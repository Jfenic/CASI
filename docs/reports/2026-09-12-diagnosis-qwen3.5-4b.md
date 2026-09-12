# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 8 |
| task_success_rate | 75.00% |
| agent_success_rate | 100.00% |
| command_success_rate | 75.00% |
| patch_validity_rate | 0.00% |
| average_steps | 6.00 |
| average_duration_seconds | 12.07 |
| average_files_read | 2.75 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 19183 |
| total_completion_tokens | 917 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| bug_localization | 1 / 2 |
| failure_analysis | 1 / 2 |
| test_expectation_analysis | 1 / 1 |
| call_stack_diagnosis | 1 / 1 |
| requirement_mismatch_diagnosis | 1 / 1 |
| mini_project_integration | 1 / 1 |

## Tasks

- `diag_001` (diagnose): **pass** — 5 steps, 13.31s
- `diag_002` (diagnose): **fail** — 5 steps, 11.38s
  - error: Diagnosis grading failed: cause missing expected failure description
- `diag_003` (diagnose): **pass** — 5 steps, 12.38s
- `diag_004` (diagnose): **fail** — 5 steps, 10.06s
  - error: Diagnosis grading failed: cause missing expected failure description
- `diag_005` (diagnose): **pass** — 7 steps, 13.21s
- `diag_006` (diagnose): **pass** — 7 steps, 14.81s
- `diag_007` (diagnose): **pass** — 5 steps, 11.10s
- `diag_008` (diagnose): **pass** — 9 steps, 10.29s
