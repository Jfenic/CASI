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
| average_duration_seconds | 15.13 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 9064 |
| total_completion_tokens | 226 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| bug_localization | 0 / 2 |
| failure_analysis | 1 / 2 |
| test_expectation_analysis | 0 / 1 |

## Tasks

- `diag_001` (diagnose): **fail** — 5 steps, 60.51s
  - error: Diagnosis grading failed: expected file 'counter.py', got 'test_counter.py'; cause missing expected failure description; evidence missing expected symbol or expression
- `diag_002` (diagnose): **fail** — 5 steps, 3.78s
  - error: Diagnosis grading failed: expected file 'clamp.py', got 'test_clamp.py'; line 5 below minimum 10; cause missing expected failure description; evidence missing expected symbol or expression
- `diag_003` (diagnose): **pass** — 5 steps, 3.57s
- `diag_004` (diagnose): **fail** — 5 steps, 4.30s
  - error: Diagnosis grading failed: expected file 'stats.py', got 'test_stats.py'; line 5 below minimum 6; cause missing expected failure description
- `diag_005` (diagnose): **fail** — 5 steps, 3.49s
  - error: Diagnosis grading failed: line 5 below minimum 6; cause missing expected failure description
