# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 12 |
| task_success_rate | 58.33% |
| agent_success_rate | 75.00% |
| command_success_rate | 58.33% |
| patch_validity_rate | 100.00% |
| average_steps | 11.92 |
| average_duration_seconds | 52.35 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 141133 |
| total_completion_tokens | 9131 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| boundary_conditions | 1 / 1 |
| input_validation | 2 / 2 |
| data_processing | 1 / 1 |
| business_rules | 1 / 1 |
| state_and_time | 1 / 1 |
| regression_and_mutability | 0 / 1 |
| module_creation | 0 / 1 |
| algorithm_and_validation | 0 / 1 |
| test_design | 0 / 1 |
| regression_test_design | 0 / 1 |
| mini_project_integration | 1 / 1 |

## Tasks

- `dev_001` (fix): **pass** — 12 steps, 55.28s
- `dev_002` (fix): **pass** — 12 steps, 29.88s
- `dev_003` (fix): **pass** — 14 steps, 65.65s
- `dev_004` (fix): **pass** — 8 steps, 38.38s
- `dev_005` (fix): **pass** — 10 steps, 40.65s
- `dev_006` (fix): **fail** — 10 steps, 59.90s
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
E         At index 0 diff: {'db': {'ports': [1, 2], 'flags': {'a': False}}, 'extra': [{'x': 3}]} != {'db': {'ports': [1], 'flags': {'a': True}}, 'extra': [{'x': 1}]}
E         Use -v to get more diff

_benchmark_checks/test_acceptance.py:16: AssertionError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_no_aliases_or_mutations - A...
1 failed, 2 passed in 0.02s
- `dev_007` (create): **fail** — 11 steps, 50.37s
  - error: Independent verification failed: .FFFFFF.                                                                 [100%]
=================================== FAILURES ===================================
________________________ test_physical_line_number[[1]] ________________________

bad = '[1]'

    @pytest.mark.parametrize("bad", ["[1]", "null", "true", "3", '"text"', "{bad"])
    def test_physical_line_number(bad):
>       with pytest.raises(ValueError, match=r"line 3\b"):
E       AssertionError: Regex pattern did not match.
E         Expected regex: 'line 3\\b'
E         Actual message: 'Line 1: Expected JSON object, got list'

_benchmark_checks/test_acceptance.py:14: AssertionError
_______________________ test_physical_line_number[null] ________________________

bad = 'null'

    @pytest.mark.parametrize("bad", ["[1]", "null", "true", "3", '"text"', "{bad"])
    def test_physical_line_number(bad):
>       with pytest.raises(ValueError, match=r"line 3\b"):
E       AssertionError: Regex pattern did not match.
E         Expected regex: 'line 3\\b'
E         Actual message: 'Line 1: Expected JSON object, got NoneType'

_benchmark_checks/test_acceptance.py:14: AssertionError
_______________________ test_physical_line_number[true] ________________________

bad = 'true'

    @pytest.mark.parametrize("bad", ["[1]", "null", "true", "3", '"text"', "{bad"])
    def test_physical_line_number(bad):
>       with pytest.raises(ValueError, match=r"line 3\b"):
E       AssertionError: Regex pattern did not match.
E         Expected regex: 'line 3\\b'
E         Actual message: 'Line 1: Expected JSON object, got bool'

_benchmark_checks/test_acceptance.py:14: AssertionError
_________________________ test_physical_line_number[3] _________________________

bad = '3'

    @pytest.mark.parametrize("bad", ["[1]", "null", "true", "3", '"text"', "{bad"])
    def test_physical_line_number(bad):
>       with pytest.raises(ValueError, match=r"line 3\b"):
E       AssertionError: Regex pattern did not match.
E         Expected regex: 'line 3\\b'
E         Actual message: 'Line 1: Expected JSON object, got int'

_benchmark_checks/test_acceptance.py:14: AssertionError
______________________ test_physical_line_number["text"] _______________________

bad = '"text"'

    @pytest.mark.parametrize("bad", ["[1]", "null", "true", "3", '"text"', "{bad"])
    def test_physical_line_number(bad):
>       with pytest.raises(ValueError, match=r"line 3\b"):
E       AssertionError: Regex pattern did not match.
E         Expected regex: 'line 3\\b'
E         Actual message: 'Line 1: Expected JSON object, got str'

_benchmark_checks/test_acceptance.py:14: AssertionError
_______________________ test_physical_line_number[{bad] ________________________

bad = '{bad'

    @pytest.mark.parametrize("bad", ["[1]", "null", "true", "3", '"text"', "{bad"])
    def test_physical_line_number(bad):
>       with pytest.raises(ValueError, match=r"line 3\b"):
E       AssertionError: Regex pattern did not match.
E         Expected regex: 'line 3\\b'
E         Actual message: 'Malformed JSON at line 1'

_benchmark_checks/test_acceptance.py:14: AssertionError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_physical_line_number[[1]]
FAILED _benchmark_checks/test_acceptance.py::test_physical_line_number[null]
FAILED _benchmark_checks/test_acceptance.py::test_physical_line_number[true]
FAILED _benchmark_checks/test_acceptance.py::test_physical_line_number[3] - A...
FAILED _benchmark_checks/test_acceptance.py::test_physical_line_number["text"]
FAILED _benchmark_checks/test_acceptance.py::test_physical_line_number[{bad]
6 failed, 2 passed in 0.05s
- `dev_008` (create): **fail** — 16 steps, 87.37s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_009` (create): **fail** — 14 steps, 90.76s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_010` (create): **fail** — 14 steps, 62.91s
  - error: Ollama message does not contain usable content
- `dev_011` (fix): **pass** — 6 steps, 15.10s
- `dev_012` (fix): **pass** — 16 steps, 31.92s
