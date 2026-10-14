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
| average_duration_seconds | 12.06 |
| average_files_read | 2.75 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 23578 |
| total_completion_tokens | 907 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| bug_localization | 1 / 2 |
| failure_analysis | 2 / 2 |
| test_expectation_analysis | 1 / 1 |
| call_stack_diagnosis | 0 / 1 |
| requirement_mismatch_diagnosis | 1 / 1 |
| mini_project_integration | 1 / 1 |

## Tasks

- `diag_001` (diagnose): **pass** — 5 steps, 9.87s
- `diag_002` (diagnose): **fail** — 5 steps, 10.37s
  - error: Diagnosis grading failed: cause missing expected failure description
- `diag_003` (diagnose): **pass** — 7 steps, 14.06s
- `diag_004` (diagnose): **pass** — 5 steps, 12.41s
- `diag_005` (diagnose): **pass** — 5 steps, 11.20s
- `diag_006` (diagnose): **fail** — 7 steps, 12.97s
  - error: Diagnosis grading failed: evidence missing expected symbol or expression
- `diag_007` (diagnose): **pass** — 5 steps, 11.38s
- `diag_008` (diagnose): **pass** — 9 steps, 14.25s
