# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 10 |
| task_success_rate | 20.00% |
| agent_success_rate | 20.00% |
| command_success_rate | 20.00% |
| patch_validity_rate | 100.00% |
| average_steps | 17.30 |
| average_duration_seconds | 37.99 |
| average_files_read | 1.60 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 212456 |
| total_completion_tokens | 8237 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| boundary_conditions | 1 / 1 |
| input_validation | 0 / 1 |
| data_processing | 0 / 1 |
| business_rules | 0 / 1 |
| state_and_time | 1 / 1 |
| regression_and_mutability | 0 / 1 |
| module_creation | 0 / 1 |
| algorithm_and_validation | 0 / 1 |
| test_design | 0 / 1 |
| regression_test_design | 0 / 1 |

## Tasks

- `dev_001` (fix): **pass** — 12 steps, 27.60s
- `dev_002` (fix): **fail** — 25 steps, 46.08s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_003` (fix): **fail** — 14 steps, 20.89s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_004` (fix): **fail** — 11 steps, 41.96s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_005` (fix): **pass** — 12 steps, 21.20s
- `dev_006` (fix): **fail** — 34 steps, 46.90s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_007` (create): **fail** — 22 steps, 52.66s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_008` (create): **fail** — 17 steps, 42.27s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_009` (create): **fail** — 14 steps, 63.58s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_010` (create): **fail** — 12 steps, 16.81s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.


# CASI Benchmark Report — qwen2.5-coder:7b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 10 |
| task_success_rate | 20.00% |
| agent_success_rate | 60.00% |
| command_success_rate | 20.00% |
| patch_validity_rate | 100.00% |
| average_steps | 13.80 |
| average_duration_seconds | 71.85 |
| average_files_read | 1.60 |
| average_correction_attempts | 0.70 |
| total_prompt_tokens | 161382 |
| total_completion_tokens | 8014 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| boundary_conditions | 1 / 1 |
| input_validation | 1 / 1 |
| data_processing | 0 / 1 |
| business_rules | 0 / 1 |
| state_and_time | 0 / 1 |
| regression_and_mutability | 0 / 1 |
| module_creation | 0 / 1 |
| algorithm_and_validation | 0 / 1 |
| test_design | 0 / 1 |
| regression_test_design | 0 / 1 |

## Tasks

- `dev_001` (fix): **pass** — 6 steps, 30.48s
- `dev_002` (fix): **pass** — 6 steps, 12.71s
- `dev_003` (fix): **fail** — 13 steps, 155.88s
  - error: Ollama request failed: timed out
- `dev_004` (fix): **fail** — 23 steps, 66.08s
  - error: Independent verification failed: F.....                                                                   [100%]
=================================== FAILURES ===================================
_________________________ test_round_lines_before_sum __________________________

    def test_round_lines_before_sum():
>       assert invoice_total([("0.005", 1), ("0.005", 1)]) == "0.02"
E       AssertionError: assert '0.01' == '0.02'
E         
E         - 0.02
E         ?    ^
E         + 0.01
E         ?    ^

_benchmark_checks/test_acceptance.py:6: AssertionError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_round_lines_before_sum - As...
1 failed, 5 passed in 0.02s
- `dev_005` (fix): **fail** — 6 steps, 13.85s
  - error: Independent verification failed: .F.                                                                      [100%]
=================================== FAILURES ===================================
__________________________ test_zero_and_negative_ttl __________________________

    def test_zero_and_negative_ttl():
        cache = Cache(lambda: 100)
        cache.set("zero", 5, 0)
>       assert cache.get("zero") is None
E       AssertionError: assert 5 is None
E        +  where 5 = get('zero')
E        +    where get = <cache.Cache object at 0x7fbec1c96710>.get

_benchmark_checks/test_acceptance.py:23: AssertionError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_zero_and_negative_ttl - Ass...
1 failed, 2 passed in 0.02s
- `dev_006` (fix): **fail** — 6 steps, 7.67s
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
- `dev_007` (create): **fail** — 5 steps, 9.79s
  - error: Independent verification failed: .FFFFF..                                                                 [100%]
=================================== FAILURES ===================================
________________________ test_physical_line_number[[1]] ________________________

bad = '[1]'

    @pytest.mark.parametrize("bad", ["[1]", "null", "true", "3", '"text"', "{bad"])
    def test_physical_line_number(bad):
>       with pytest.raises(ValueError, match=r"line 3\b"):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:14: Failed
_______________________ test_physical_line_number[null] ________________________

bad = 'null'

    @pytest.mark.parametrize("bad", ["[1]", "null", "true", "3", '"text"', "{bad"])
    def test_physical_line_number(bad):
>       with pytest.raises(ValueError, match=r"line 3\b"):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:14: Failed
_______________________ test_physical_line_number[true] ________________________

bad = 'true'

    @pytest.mark.parametrize("bad", ["[1]", "null", "true", "3", '"text"', "{bad"])
    def test_physical_line_number(bad):
>       with pytest.raises(ValueError, match=r"line 3\b"):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:14: Failed
_________________________ test_physical_line_number[3] _________________________

bad = '3'

    @pytest.mark.parametrize("bad", ["[1]", "null", "true", "3", '"text"', "{bad"])
    def test_physical_line_number(bad):
>       with pytest.raises(ValueError, match=r"line 3\b"):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:14: Failed
______________________ test_physical_line_number["text"] _______________________

bad = '"text"'

    @pytest.mark.parametrize("bad", ["[1]", "null", "true", "3", '"text"', "{bad"])
    def test_physical_line_number(bad):
>       with pytest.raises(ValueError, match=r"line 3\b"):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:14: Failed
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_physical_line_number[[1]]
FAILED _benchmark_checks/test_acceptance.py::test_physical_line_number[null]
FAILED _benchmark_checks/test_acceptance.py::test_physical_line_number[true]
FAILED _benchmark_checks/test_acceptance.py::test_physical_line_number[3] - F...
FAILED _benchmark_checks/test_acceptance.py::test_physical_line_number["text"]
5 failed, 3 passed in 0.02s
- `dev_008` (create): **fail** — 19 steps, 98.73s
  - error: Patch verification failed after exhausting correction attempts: F                                                                        [100%]
=================================== FAILURES ===================================
______________________________ test_simple_order _______________________________

    def test_simple_order():
>       assert build_order({"app": ["lib"], "lib": []}) == ["lib", "app"]
E       AssertionError: assert ['app', 'lib'] == ['lib', 'app']
E         
E         At index 0 diff: 'app' != 'lib'
E         Use -v to get more diff

test_visible.py:5: AssertionError
=========================== short test summary info ============================
FAILED test_visible.py::test_simple_order - AssertionError: assert ['app', 'l...
1 failed in 0.01s

- `dev_009` (create): **fail** — 26 steps, 249.98s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_010` (create): **fail** — 28 steps, 73.33s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
