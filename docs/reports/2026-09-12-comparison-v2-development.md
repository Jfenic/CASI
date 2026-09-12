# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 10 |
| task_success_rate | 10.00% |
| agent_success_rate | 10.00% |
| command_success_rate | 10.00% |
| patch_validity_rate | 100.00% |
| average_steps | 13.10 |
| average_duration_seconds | 58.99 |
| average_files_read | 1.60 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 125667 |
| total_completion_tokens | 7170 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| boundary_conditions | 0 / 1 |
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

- `dev_001` (fix): **fail** — 11 steps, 51.94s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_002` (fix): **fail** — 15 steps, 51.58s
  - error: Ollama message does not contain usable content
- `dev_003` (fix): **fail** — 12 steps, 47.11s
  - error: Ollama message does not contain usable content
- `dev_004` (fix): **fail** — 16 steps, 79.42s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_005` (fix): **pass** — 6 steps, 15.60s
- `dev_006` (fix): **fail** — 15 steps, 68.58s
  - error: Ollama message does not contain usable content
- `dev_007` (create): **fail** — 12 steps, 83.12s
  - error: Ollama message does not contain usable content
- `dev_008` (create): **fail** — 14 steps, 54.87s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_009` (create): **fail** — 18 steps, 104.47s
  - error: Ollama message does not contain usable content
- `dev_010` (create): **fail** — 12 steps, 33.23s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.


# CASI Benchmark Report — qwen2.5-coder:7b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 10 |
| task_success_rate | 50.00% |
| agent_success_rate | 70.00% |
| command_success_rate | 50.00% |
| patch_validity_rate | 100.00% |
| average_steps | 11.50 |
| average_duration_seconds | 48.55 |
| average_files_read | 1.60 |
| average_correction_attempts | 0.60 |
| total_prompt_tokens | 105703 |
| total_completion_tokens | 4465 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| boundary_conditions | 1 / 1 |
| input_validation | 1 / 1 |
| data_processing | 0 / 1 |
| business_rules | 1 / 1 |
| state_and_time | 1 / 1 |
| regression_and_mutability | 0 / 1 |
| module_creation | 1 / 1 |
| algorithm_and_validation | 0 / 1 |
| test_design | 0 / 1 |
| regression_test_design | 0 / 1 |

## Tasks

- `dev_001` (fix): **pass** — 6 steps, 42.79s
- `dev_002` (fix): **pass** — 6 steps, 11.33s
- `dev_003` (fix): **fail** — 6 steps, 13.59s
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
            if not line:
                continue
            fields = line.strip().split(",")
            if len(fields) != 2:
>               raise ValueError("Invalid CSV format")
E               ValueError: Invalid CSV format

sales.py:8: ValueError
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
            if not line:
                continue
            fields = line.strip().split(",")
            if len(fields) != 2:
>               raise ValueError("Invalid CSV format")
E               ValueError: Invalid CSV format

sales.py:8: ValueError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_quoting_and_adjustments - V...
FAILED _benchmark_checks/test_acceptance.py::test_multiline_product - ValueEr...
2 failed, 3 passed in 0.02s
- `dev_004` (fix): **pass** — 6 steps, 15.41s
- `dev_005` (fix): **pass** — 6 steps, 18.37s
- `dev_006` (fix): **fail** — 17 steps, 74.94s
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
1 failed, 2 passed in 0.12s
- `dev_007` (create): **pass** — 5 steps, 11.96s
- `dev_008` (create): **fail** — 26 steps, 130.00s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_009` (create): **fail** — 18 steps, 56.25s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_010` (create): **fail** — 19 steps, 110.82s
  - error: Patch verification failed after exhausting correction attempts: .F...........                                                            [100%]
=================================== FAILURES ===================================
_______________________ test_slugify[Python3.8-python38] _______________________

text = 'Python3.8', expected = 'python38'

    @pytest.mark.parametrize('text, expected', [
        ('Hello, World!', 'hello-world'),
        ('Python3.8', 'python38'),
        ('12345', '12345'),
        ('!@#$%', ''),
        ('--###', ''),
        ('  leading and trailing  ', 'leading-and-trailing'),
        ('', ''),
        ('ALLCAPS', 'allcaps'),
        ('lowercase', 'lowercase'),
        ('1234-abcDEF', '1234-abcdef'),
        ('--multiple---separators--', 'multiple-separators'),
        ('Boundary-123_456', 'boundary-123-456'),
    ])
    def test_slugify(text, expected):
>       assert slugify(text) == expected
E       AssertionError: assert 'python3-8' == 'python38'
E         
E         - python38
E         + python3-8
E         ?        +

test_slug.py:20: AssertionError
=========================== short test summary info ============================
FAILED test_slug.py::test_slugify[Python3.8-python38] - AssertionError: asser...
1 failed, 12 passed in 0.03s

