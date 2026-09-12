# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 12 |
| task_success_rate | 33.33% |
| agent_success_rate | 41.67% |
| command_success_rate | 33.33% |
| patch_validity_rate | 100.00% |
| average_steps | 10.42 |
| average_duration_seconds | 42.98 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.08 |
| total_prompt_tokens | 98719 |
| total_completion_tokens | 6120 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| boundary_conditions | 1 / 1 |
| input_validation | 1 / 2 |
| data_processing | 0 / 1 |
| business_rules | 0 / 1 |
| state_and_time | 1 / 1 |
| regression_and_mutability | 0 / 1 |
| module_creation | 0 / 1 |
| algorithm_and_validation | 0 / 1 |
| test_design | 0 / 1 |
| regression_test_design | 0 / 1 |
| mini_project_integration | 1 / 1 |

## Tasks

- `dev_001` (fix): **pass** — 16 steps, 44.70s
- `dev_002` (fix): **fail** — 13 steps, 34.17s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_003` (fix): **fail** — 13 steps, 77.32s
  - error: Ollama message does not contain usable content
- `dev_004` (fix): **fail** — 13 steps, 61.31s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_005` (fix): **pass** — 6 steps, 15.53s
- `dev_006` (fix): **fail** — 13 steps, 76.50s
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
1 failed, 2 passed in 0.03s
- `dev_007` (create): **fail** — 2 steps, 5.08s
  - error: Ollama request failed: HTTP Error 500: Internal Server Error
- `dev_008` (create): **fail** — 7 steps, 53.58s
  - error: Ollama message does not contain usable content
- `dev_009` (create): **fail** — 12 steps, 44.99s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_010` (create): **fail** — 14 steps, 81.04s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_011` (fix): **pass** — 6 steps, 9.14s
- `dev_012` (fix): **pass** — 10 steps, 12.36s
