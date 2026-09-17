# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 4 |
| task_success_rate | 75.00% |
| agent_success_rate | 100.00% |
| command_success_rate | 75.00% |
| patch_validity_rate | 100.00% |
| average_steps | 9.00 |
| average_duration_seconds | 45.87 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 33826 |
| total_completion_tokens | 3154 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| leakage_free_preprocessing | 1 / 1 |
| categorical_feature_extraction | 0 / 1 |
| temporal_feature_extraction | 1 / 1 |
| signal_feature_extraction | 1 / 1 |

## Tasks

- `ml_v2_001` (ml): **pass** — 6 steps, 63.23s
- `ml_v2_002` (ml): **fail** — 8 steps, 31.59s
  - error: Independent verification failed: .F.                                                                      [100%]
=================================== FAILURES ===================================
________________________ test_empty_refit_and_unfitted _________________________

    def test_empty_refit_and_unfitted():
        with pytest.raises(ValueError):
            Encoder().transform([])
        model = Encoder().fit(["a"])
        model.fit(["b"])
>       assert model.transform(["a", "b"]) == [[0], [1]]
E       assert [[1, 0], [0, 1]] == [[0], [1]]
E         
E         At index 0 diff: [1, 0] != [0]
E         Use -v to get more diff

_benchmark_checks/test_acceptance.py:24: AssertionError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_empty_refit_and_unfitted - ...
1 failed, 2 passed in 0.02s
- `ml_v2_003` (ml): **pass** — 16 steps, 71.76s
- `ml_v2_004` (ml): **pass** — 6 steps, 16.90s
