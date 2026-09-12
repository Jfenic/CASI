# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 12 |
| task_success_rate | 66.67% |
| agent_success_rate | 83.33% |
| command_success_rate | 66.67% |
| patch_validity_rate | 100.00% |
| average_steps | 9.17 |
| average_duration_seconds | 38.20 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 75617 |
| total_completion_tokens | 5929 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| boundary_conditions | 1 / 1 |
| input_validation | 1 / 2 |
| data_processing | 1 / 1 |
| business_rules | 1 / 1 |
| state_and_time | 1 / 1 |
| regression_and_mutability | 0 / 1 |
| module_creation | 1 / 1 |
| algorithm_and_validation | 1 / 1 |
| test_design | 0 / 1 |
| regression_test_design | 0 / 1 |
| mini_project_integration | 1 / 1 |

## Tasks

- `dev_001` (fix): **pass** — 12 steps, 32.61s
- `dev_002` (fix): **fail** — 12 steps, 26.81s
  - error: Independent verification failed: ..............FF...                                                      [100%]
=================================== FAILURES ===================================
_______________________________ test_bad_type[0] _______________________________

value = 0

    @pytest.mark.parametrize("value", [0, 1, [], {}])
    def test_bad_type(value):
>       with pytest.raises(TypeError):
E       Failed: DID NOT RAISE TypeError

_benchmark_checks/test_acceptance.py:28: Failed
_______________________________ test_bad_type[1] _______________________________

value = 1

    @pytest.mark.parametrize("value", [0, 1, [], {}])
    def test_bad_type(value):
>       with pytest.raises(TypeError):
E       Failed: DID NOT RAISE TypeError

_benchmark_checks/test_acceptance.py:28: Failed
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_bad_type[0] - Failed: DID N...
FAILED _benchmark_checks/test_acceptance.py::test_bad_type[1] - Failed: DID N...
2 failed, 17 passed in 0.04s
- `dev_003` (fix): **pass** — 6 steps, 17.82s
- `dev_004` (fix): **pass** — 6 steps, 17.49s
- `dev_005` (fix): **pass** — 8 steps, 25.72s
- `dev_006` (fix): **fail** — 8 steps, 45.71s
  - error: Independent verification failed: F..                                                                      [100%]
=================================== FAILURES ===================================
_________________________ test_no_aliases_or_mutations _________________________

    def test_no_aliases_or_mutations():
        defaults = {"db": {"ports": [1], "flags": {"a": True}}, "extra": [{"x": 1}]}
        overrides = {"db": {"name": "main"}, "custom": [{"y": 2}]}
        before = (deepcopy(defaults), deepcopy(overrides))
        result = merge_settings(defaults, overrides)
        assert (defaults, overrides) == before
        result["db"]["ports"].append(2)
        result["db"]["flags"]["a"] = False
        result["extra"][0]["x"] = 3
        result["custom"][0]["y"] = 4
>       assert (defaults, overrides) == before
E       AssertionError: assert ({'db': {'por...: [{'y': 4}]}) == ({'db': {'por...: [{'y': 2}]})
E         
E         At index 1 diff: {'db': {'name': 'main'}, 'custom': [{'y': 4}]} != {'db': {'name': 'main'}, 'custom': [{'y': 2}]}
E         Use -v to get more diff

_benchmark_checks/test_acceptance.py:16: AssertionError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_no_aliases_or_mutations - A...
1 failed, 2 passed in 0.02s
- `dev_007` (create): **pass** — 11 steps, 72.43s
- `dev_008` (create): **pass** — 5 steps, 35.76s
- `dev_009` (create): **fail** — 16 steps, 85.52s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_010` (create): **fail** — 6 steps, 66.99s
  - error: Ollama message does not contain usable content
- `dev_011` (fix): **pass** — 10 steps, 18.77s
- `dev_012` (fix): **pass** — 10 steps, 12.73s
