# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 4 |
| task_success_rate | 75.00% |
| agent_success_rate | 100.00% |
| command_success_rate | 75.00% |
| patch_validity_rate | 100.00% |
| average_steps | 8.50 |
| average_duration_seconds | 38.89 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 22103 |
| total_completion_tokens | 1240 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| leakage_free_preprocessing | 1 / 1 |
| categorical_feature_extraction | 0 / 1 |
| temporal_feature_extraction | 1 / 1 |
| signal_feature_extraction | 1 / 1 |

## Tasks

- `ml_v2_001` (ml): **pass** — 9 steps, 55.97s
- `ml_v2_002` (ml): **fail** — 9 steps, 35.04s
  - error: Independent verification failed: .F.                                                                      [100%]
=================================== FAILURES ===================================
________________________ test_empty_refit_and_unfitted _________________________

    def test_empty_refit_and_unfitted():
        with pytest.raises(ValueError):
            Encoder().transform([])
        model = Encoder().fit(["a"])
        model.fit(["b"])
        assert model.transform(["a", "b"]) == [[0], [1]]
        model.fit([])
>       result = model.transform(["x", "y"])
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^

_benchmark_checks/test_acceptance.py:26: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <encoding.Encoder object at 0x7ff789840450>, values = ['x', 'y']

    def transform(self, values):
        if not hasattr(self, "categories") or len(self.categories) == 0:
>           raise ValueError("not fitted")
E           ValueError: not fitted

encoding.py:13: ValueError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_empty_refit_and_unfitted - ...
1 failed, 2 passed in 0.02s
- `ml_v2_003` (ml): **pass** — 9 steps, 44.52s
- `ml_v2_004` (ml): **pass** — 7 steps, 20.04s
