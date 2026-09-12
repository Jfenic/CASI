# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 5 |
| task_success_rate | 20.00% |
| agent_success_rate | 100.00% |
| command_success_rate | 20.00% |
| patch_validity_rate | 0.00% |
| average_steps | 5.00 |
| average_duration_seconds | 4.93 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 10316 |
| total_completion_tokens | 556 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| bug_localization | 0 / 2 |
| failure_analysis | 1 / 2 |
| test_expectation_analysis | 0 / 1 |

## Tasks

- `diag_001` (diagnose): **fail** — 5 steps, 7.44s
  - error: Diagnosis grading failed: response too long: 56 words (max 40)
- `diag_002` (diagnose): **fail** — 5 steps, 3.99s
  - error: Diagnosis grading failed: line 9 below minimum 10; response too long: 46 words (max 40)
- `diag_003` (diagnose): **pass** — 5 steps, 3.85s
- `diag_004` (diagnose): **fail** — 5 steps, 5.25s
  - error: Diagnosis grading failed: response too long: 70 words (max 40)
- `diag_005` (diagnose): **fail** — 5 steps, 4.10s
  - error: Diagnosis grading failed: line 4 below minimum 6; response too long: 60 words (max 40); evidence missing expected symbol or expression
