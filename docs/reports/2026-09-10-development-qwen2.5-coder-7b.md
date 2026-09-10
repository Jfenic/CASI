# CASI Benchmark Report — qwen2.5-coder:7b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 10 |
| task_success_rate | 10.00% |
| agent_success_rate | 80.00% |
| command_success_rate | 10.00% |
| patch_validity_rate | 100.00% |
| average_steps | 8.30 |
| average_duration_seconds | 26.61 |
| average_files_read | 1.60 |
| average_correction_attempts | 0.50 |
| total_prompt_tokens | 49733 |
| total_completion_tokens | 2214 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| boundary_conditions | 1 / 1 |
| input_validation | 0 / 1 |
| data_processing | 0 / 1 |
| business_rules | 0 / 1 |
| state_and_time | 0 / 1 |
| regression_and_mutability | 0 / 1 |
| module_creation | 0 / 1 |
| algorithm_and_validation | 0 / 1 |
| test_design | 0 / 1 |
| regression_test_design | 0 / 1 |

## Tasks

- `dev_001` (fix): **pass** — 6 steps, 7.08s
- `dev_002` (fix): **fail** — 6 steps, 8.74s
  - error: Independent verification failed: ...........FFF.....                                                      [100%]
=================================== FAILURES ===================================
______________________________ test_bad_string[] _______________________________

value = ''

    @pytest.mark.parametrize("value", ["", "enabled", "2"])
    def test_bad_string(value):
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:22: Failed
___________________________ test_bad_string[enabled] ___________________________

value = 'enabled'

    @pytest.mark.parametrize("value", ["", "enabled", "2"])
    def test_bad_string(value):
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:22: Failed
______________________________ test_bad_string[2] ______________________________

value = '2'

    @pytest.mark.parametrize("value", ["", "enabled", "2"])
    def test_bad_string(value):
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:22: Failed
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_bad_string[] - Failed: DID ...
FAILED _benchmark_checks/test_acceptance.py::test_bad_string[enabled] - Faile...
FAILED _benchmark_checks/test_acceptance.py::test_bad_string[2] - Failed: DID...
3 failed, 16 passed in 0.03s
- `dev_003` (fix): **fail** — 11 steps, 17.55s
  - error: Independent verification failed: FF...                                                                    [100%]
=================================== FAILURES ===================================
_________________________ test_quoting_and_adjustments _________________________

    def test_quoting_and_adjustments():
        text = 'product,quantity\r\n"red, large",3\r\n"red, large",-1\r\n\r\nblue,0\r\n'
>       assert totals(text) == {"red, large": 2, "blue": 0}
               ^^^^^^^^^^^^

_benchmark_checks/test_acceptance.py:7: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

text = 'product,quantity\r\n"red, large",3\r\n"red, large",-1\r\n\r\nblue,0\r\n'

    def totals(text):
        result = {}
        for line in text.splitlines()[1:]:
            if not line.strip():
                continue
>           product, quantity = line.split(",")
            ^^^^^^^^^^^^^^^^^
E           ValueError: too many values to unpack (expected 2)

sales.py:6: ValueError
____________________________ test_multiline_product ____________________________

    def test_multiline_product():
>       assert totals('product,quantity\n"two\nlines",4\n') == {"two\nlines": 4}
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

_benchmark_checks/test_acceptance.py:11: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

text = 'product,quantity\n"two\nlines",4\n'

    def totals(text):
        result = {}
        for line in text.splitlines()[1:]:
            if not line.strip():
                continue
>           product, quantity = line.split(",")
            ^^^^^^^^^^^^^^^^^
E           ValueError: not enough values to unpack (expected 2, got 1)

sales.py:6: ValueError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_quoting_and_adjustments - V...
FAILED _benchmark_checks/test_acceptance.py::test_multiline_product - ValueEr...
2 failed, 3 passed in 0.03s
- `dev_004` (fix): **fail** — 15 steps, 34.24s
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
- `dev_005` (fix): **fail** — 6 steps, 11.31s
  - error: Independent verification failed: .F.                                                                      [100%]
=================================== FAILURES ===================================
__________________________ test_zero_and_negative_ttl __________________________

    def test_zero_and_negative_ttl():
        cache = Cache(lambda: 100)
>       cache.set("zero", 5, 0)

_benchmark_checks/test_acceptance.py:22: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <cache.Cache object at 0x7ff46c2e2090>, key = 'zero', value = 5, ttl = 0

    def set(self, key, value, ttl):
        if ttl <= 0:
>           raise ValueError("Negative or zero TTL is not allowed")
E           ValueError: Negative or zero TTL is not allowed

cache.py:8: ValueError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_zero_and_negative_ttl - Val...
1 failed, 2 passed in 0.02s
- `dev_006` (fix): **fail** — 6 steps, 8.23s
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
- `dev_007` (create): **fail** — 5 steps, 8.95s
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
- `dev_008` (create): **fail** — 8 steps, 13.86s
  - error: Independent verification failed: F.FFF.                                                                   [100%]
=================================== FAILURES ===================================
_____________________ test_ready_queue_and_implicit_nodes ______________________

    def test_ready_queue_and_implicit_nodes():
        graph = {"a": ["b", "b"], "z": [], "d": ["c"]}
        before = deepcopy(graph)
>       assert build_order(graph) == ["b", "a", "c", "d", "z"]
E       AssertionError: assert ['z', 'c', 'd', 'b', 'a'] == ['b', 'a', 'c', 'd', 'z']
E         
E         At index 0 diff: 'z' != 'b'
E         Use -v to get more diff

_benchmark_checks/test_acceptance.py:10: AssertionError
_____________________________ test_cycles[graph0] ______________________________

graph = {'a': ['a']}

    @pytest.mark.parametrize(
        "graph", [{"a": ["a"]}, {"a": ["b"], "b": ["a"]}, {"z": [], "a": ["b"], "b": ["a"]}]
    )
    def test_cycles(graph):
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:28: Failed
_____________________________ test_cycles[graph1] ______________________________

graph = {'a': ['b'], 'b': ['a']}

    @pytest.mark.parametrize(
        "graph", [{"a": ["a"]}, {"a": ["b"], "b": ["a"]}, {"z": [], "a": ["b"], "b": ["a"]}]
    )
    def test_cycles(graph):
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:28: Failed
_____________________________ test_cycles[graph2] ______________________________

graph = {'z': [], 'a': ['b'], 'b': ['a']}

    @pytest.mark.parametrize(
        "graph", [{"a": ["a"]}, {"a": ["b"], "b": ["a"]}, {"z": [], "a": ["b"], "b": ["a"]}]
    )
    def test_cycles(graph):
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:28: Failed
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_ready_queue_and_implicit_nodes
FAILED _benchmark_checks/test_acceptance.py::test_cycles[graph0] - Failed: DI...
FAILED _benchmark_checks/test_acceptance.py::test_cycles[graph1] - Failed: DI...
FAILED _benchmark_checks/test_acceptance.py::test_cycles[graph2] - Failed: DI...
4 failed, 2 passed in 0.02s
- `dev_009` (create): **fail** — 2 steps, 120.68s
  - error: Ollama request failed: timed out
- `dev_010` (create): **fail** — 18 steps, 35.43s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.

