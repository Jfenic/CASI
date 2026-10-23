# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 6 |
| task_success_rate | 83.33% |
| agent_success_rate | 100.00% |
| command_success_rate | 83.33% |
| patch_validity_rate | 100.00% |
| average_steps | 7.50 |
| average_duration_seconds | 30.84 |
| average_files_read | 1.50 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 27198 |
| total_completion_tokens | 1947 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| evaluation_metrics | 1 / 1 |
| data_splitting | 1 / 1 |
| preprocessing | 0 / 1 |
| batching | 1 / 1 |
| encoding | 1 / 1 |
| loss_computation | 1 / 1 |

## Tasks

- `ml_001` (ml): **pass** — 9 steps, 51.11s
- `ml_002` (ml): **pass** — 8 steps, 27.97s
- `ml_003` (ml): **fail** — 8 steps, 47.84s
  - error: Independent verification failed: F...                                                                     [100%]
=================================== FAILURES ===================================
________________________ test_sample_standard_deviation ________________________

    def test_sample_standard_deviation():
        rows = [[1.0, 4.0], [3.0, 8.0], [5.0, 12.0]]
        result = standardize(rows)
>       assert result[0][0] == -1.0
E       assert -0.2734343708098653 == -1.0

_benchmark_checks/test_acceptance.py:7: AssertionError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_sample_standard_deviation
1 failed, 3 passed in 0.02s
- `ml_004` (ml): **pass** — 6 steps, 26.63s
- `ml_005` (ml): **pass** — 7 steps, 15.16s
- `ml_006` (ml): **pass** — 7 steps, 16.32s
