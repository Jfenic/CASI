# CASI Benchmark Report — qwen2.5-coder:7b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 5 |
| task_success_rate | 80.00% |
| agent_success_rate | 100.00% |
| command_success_rate | 80.00% |
| patch_validity_rate | 0.00% |
| average_steps | 5.00 |
| average_duration_seconds | 4.89 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 9426 |
| total_completion_tokens | 319 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| bug_localization | 1 / 2 |
| failure_analysis | 2 / 2 |
| test_expectation_analysis | 1 / 1 |

## Tasks

- `diag_001` (diagnose): **pass** — 5 steps, 4.48s
- `diag_002` (diagnose): **fail** — 5 steps, 6.59s
  - error: Diagnosis grading failed: line 9 below minimum 10; response too long: 41 words (max 40); evidence missing expected symbol or expression
- `diag_003` (diagnose): **pass** — 5 steps, 4.27s
- `diag_004` (diagnose): **pass** — 5 steps, 4.35s
- `diag_005` (diagnose): **pass** — 5 steps, 4.76s
