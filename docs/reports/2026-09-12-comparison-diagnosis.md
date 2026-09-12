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
| average_duration_seconds | 8.00 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 10316 |
| total_completion_tokens | 522 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| bug_localization | 0 / 2 |
| failure_analysis | 1 / 2 |
| test_expectation_analysis | 0 / 1 |

## Tasks

- `diag_001` (diagnose): **fail** — 5 steps, 23.33s
  - error: Diagnosis grading failed: response too long: 47 words (max 40)
- `diag_002` (diagnose): **fail** — 5 steps, 4.41s
  - error: Diagnosis grading failed: line 9 below minimum 10; response too long: 50 words (max 40)
- `diag_003` (diagnose): **pass** — 5 steps, 3.82s
- `diag_004` (diagnose): **fail** — 5 steps, 5.39s
  - error: Diagnosis grading failed: response too long: 60 words (max 40)
- `diag_005` (diagnose): **fail** — 5 steps, 3.06s
  - error: Diagnosis grading failed: line 4 below minimum 6


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
| average_duration_seconds | 7.32 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 9425 |
| total_completion_tokens | 242 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| bug_localization | 0 / 2 |
| failure_analysis | 1 / 2 |
| test_expectation_analysis | 0 / 1 |

## Tasks

- `diag_001` (diagnose): **fail** — 5 steps, 20.15s
  - error: Diagnosis grading failed: cause missing expected failure description
- `diag_002` (diagnose): **fail** — 5 steps, 4.56s
  - error: Diagnosis grading failed: line 9 below minimum 10
- `diag_003` (diagnose): **pass** — 5 steps, 3.62s
- `diag_004` (diagnose): **fail** — 5 steps, 4.29s
  - error: Diagnosis grading failed: cause missing expected failure description
- `diag_005` (diagnose): **fail** — 5 steps, 3.98s
  - error: Diagnosis grading failed: line 5 below minimum 6
