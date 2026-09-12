# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 5 |
| task_success_rate | 80.00% |
| agent_success_rate | 100.00% |
| command_success_rate | 80.00% |
| patch_validity_rate | 0.00% |
| average_steps | 5.00 |
| average_duration_seconds | 28.87 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 9944 |
| total_completion_tokens | 527 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| bug_localization | 1 / 2 |
| failure_analysis | 2 / 2 |
| test_expectation_analysis | 1 / 1 |

## Tasks

- `diag_001` (diagnose): **pass** — 5 steps, 67.95s
- `diag_002` (diagnose): **fail** — 5 steps, 10.80s
  - error: Diagnosis grading failed: line 9 below minimum 10
- `diag_003` (diagnose): **pass** — 5 steps, 11.15s
- `diag_004` (diagnose): **pass** — 5 steps, 25.48s
- `diag_005` (diagnose): **pass** — 5 steps, 28.94s


# CASI Benchmark Report — qwen2.5-coder:7b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 5 |
| task_success_rate | 20.00% |
| agent_success_rate | 100.00% |
| command_success_rate | 20.00% |
| patch_validity_rate | 0.00% |
| average_steps | 5.00 |
| average_duration_seconds | 10.72 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 9442 |
| total_completion_tokens | 284 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| bug_localization | 0 / 2 |
| failure_analysis | 1 / 2 |
| test_expectation_analysis | 0 / 1 |

## Tasks

- `diag_001` (diagnose): **fail** — 5 steps, 34.60s
  - error: Diagnosis grading failed: cause missing expected failure description
- `diag_002` (diagnose): **fail** — 5 steps, 5.47s
  - error: Diagnosis grading failed: line 5 below minimum 10; cause missing expected failure description
- `diag_003` (diagnose): **pass** — 5 steps, 4.32s
- `diag_004` (diagnose): **fail** — 5 steps, 3.93s
  - error: Diagnosis grading failed: cause missing expected failure description
- `diag_005` (diagnose): **fail** — 5 steps, 5.29s
  - error: Diagnosis grading failed: cause missing expected failure description
