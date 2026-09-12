# CASI Benchmark Report — qwen2.5-coder:7b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 5 |
| task_success_rate | 0.00% |
| agent_success_rate | 100.00% |
| command_success_rate | 0.00% |
| patch_validity_rate | 0.00% |
| average_steps | 7.00 |
| average_duration_seconds | 21.26 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 17733 |
| total_completion_tokens | 465 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| bug_localization | 0 / 2 |
| failure_analysis | 0 / 2 |
| test_expectation_analysis | 0 / 1 |

## Tasks

- `diag_001` (diagnose): **fail** — 7 steps, 40.36s
  - error: Diagnosis grading failed: missing or invalid diagnosis JSON payload
- `diag_002` (diagnose): **fail** — 7 steps, 31.56s
  - error: Diagnosis grading failed: missing or invalid diagnosis JSON payload
- `diag_003` (diagnose): **fail** — 7 steps, 12.09s
  - error: Diagnosis grading failed: missing or invalid diagnosis JSON payload
- `diag_004` (diagnose): **fail** — 7 steps, 11.82s
  - error: Diagnosis grading failed: missing or invalid diagnosis JSON payload
- `diag_005` (diagnose): **fail** — 7 steps, 10.48s
  - error: Diagnosis grading failed: missing or invalid diagnosis JSON payload
