# CASI Benchmark Report — qwen2.5-coder:7b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 10 |
| task_success_rate | 20.00% |
| agent_success_rate | 60.00% |
| command_success_rate | 20.00% |
| patch_validity_rate | 100.00% |
| average_steps | 11.60 |
| average_duration_seconds | 46.57 |
| average_files_read | 1.60 |
| average_correction_attempts | 0.40 |
| total_prompt_tokens | 119164 |
| total_completion_tokens | 4473 |

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

- `dev_001` (fix): **pass** — 6 steps, 7.34s
- `dev_002` (fix): **pass** — 6 steps, 11.78s
- `dev_003` (fix): **fail** — 23 steps, 45.67s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_004` (fix): **fail** — 8 steps, 22.18s
  - error: Independent verification failed: F...F.                                                                   [100%]
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
____________________________ test_negative_quantity ____________________________

    def test_negative_quantity():
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:26: Failed
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_round_lines_before_sum - As...
FAILED _benchmark_checks/test_acceptance.py::test_negative_quantity - Failed:...
2 failed, 4 passed in 0.02s
- `dev_005` (fix): **fail** — 6 steps, 13.47s
  - error: Independent verification failed: .F.                                                                      [100%]
=================================== FAILURES ===================================
__________________________ test_zero_and_negative_ttl __________________________

    def test_zero_and_negative_ttl():
        cache = Cache(lambda: 100)
>       cache.set("zero", 5, 0)

_benchmark_checks/test_acceptance.py:22: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <cache.Cache object at 0x7fd5902be090>, key = 'zero', value = 5, ttl = 0

    def set(self, key, value, ttl):
        if ttl <= 0:
>           raise ValueError("Negative TTL")
E           ValueError: Negative TTL

cache.py:8: ValueError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_zero_and_negative_ttl - Val...
1 failed, 2 passed in 0.02s
- `dev_006` (fix): **fail** — 6 steps, 10.70s
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
- `dev_007` (create): **fail** — 5 steps, 10.33s
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
5 failed, 3 passed in 0.03s
- `dev_008` (create): **fail** — 32 steps, 111.32s
  - error: Patch verification failed after exhausting correction attempts: <stdin>:32: new blank line at EOF.
+
error: 1 line adds whitespace errors.
- `dev_009` (create): **fail** — 2 steps, 120.85s
  - error: Ollama request failed: timed out
- `dev_010` (create): **fail** — 22 steps, 112.06s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
