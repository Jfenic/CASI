# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 12 |
| task_success_rate | 58.33% |
| agent_success_rate | 75.00% |
| command_success_rate | 58.33% |
| patch_validity_rate | 100.00% |
| average_steps | 8.50 |
| average_duration_seconds | 43.54 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 78752 |
| total_completion_tokens | 6729 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| boundary_conditions | 1 / 1 |
| input_validation | 1 / 2 |
| data_processing | 1 / 1 |
| business_rules | 1 / 1 |
| state_and_time | 0 / 1 |
| regression_and_mutability | 0 / 1 |
| module_creation | 1 / 1 |
| algorithm_and_validation | 1 / 1 |
| test_design | 0 / 1 |
| regression_test_design | 0 / 1 |
| mini_project_integration | 1 / 1 |

## Tasks

- `dev_001` (fix): **pass** — 6 steps, 74.35s
- `dev_002` (fix): **pass** — 8 steps, 22.71s
- `dev_003` (fix): **pass** — 6 steps, 18.76s
- `dev_004` (fix): **pass** — 6 steps, 12.94s
- `dev_005` (fix): **fail** — 15 steps, 49.47s
  - error: Independent verification failed: .F.                                                                      [100%]
=================================== FAILURES ===================================
__________________________ test_zero_and_negative_ttl __________________________

    def test_zero_and_negative_ttl():
        cache = Cache(lambda: 100)
>       cache.set("zero", 5, 0)

_benchmark_checks/test_acceptance.py:22: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <cache.Cache object at 0x7f0eea8bed10>, key = 'zero', value = 5, ttl = 0

    def set(self, key, value, ttl):
        # Validate TTL: zero or negative expires immediately or raises ValueError
        if ttl <= 0:
>           raise ValueError("TTL must be positive")
E           ValueError: TTL must be positive

cache.py:9: ValueError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_zero_and_negative_ttl - Val...
1 failed, 2 passed in 0.02s
- `dev_006` (fix): **fail** — 13 steps, 95.13s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_007` (create): **pass** — 5 steps, 20.14s
- `dev_008` (create): **pass** — 9 steps, 67.96s
- `dev_009` (create): **fail** — 10 steps, 64.75s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_010` (create): **fail** — 4 steps, 47.76s
  - error: Ollama message does not contain usable content
- `dev_011` (fix): **fail** — 10 steps, 39.70s
  - error: Independent verification failed: .....FF..                                                                [100%]
=================================== FAILURES ===================================
_____________________ test_non_integer_parts_raise[1.a.3] ______________________

text = '1.a.3'

    def parse_version(text: str) -> tuple[int, int, int]:
        parts = text.split(".")
        if len(parts) != 3:
            raise ValueError("Expected exactly three dot-separated integer parts")
        try:
>           return tuple(int(part) for part in parts)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

version.py:9: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

.0 = <list_iterator object at 0x7f304ebb5ea0>

>   return tuple(int(part) for part in parts)
                 ^^^^^^^^^
E   ValueError: invalid literal for int() with base 10: 'a'

version.py:9: ValueError

During handling of the above exception, another exception occurred:

text = '1.a.3'

    @pytest.mark.parametrize("text", ["1.a.3", "1.2.x"])
    def test_non_integer_parts_raise(text: str) -> None:
        with pytest.raises(ValueError):
>           parse_version(text)

_benchmark_checks/test_acceptance.py:18: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

text = '1.a.3'

    def parse_version(text: str) -> tuple[int, int, int]:
        parts = text.split(".")
        if len(parts) != 3:
            raise ValueError("Expected exactly three dot-separated integer parts")
        try:
            return tuple(int(part) for part in parts)
        except ValueError:
>           raise ValueError(f"Invalid version format: {text}") from __import__('errors').set_exc_value(ValueError, None)
                                                                     ^^^^^^^^^^^^^^^^^^^^
E           ModuleNotFoundError: No module named 'errors'

version.py:11: ModuleNotFoundError
_____________________ test_non_integer_parts_raise[1.2.x] ______________________

text = '1.2.x'

    def parse_version(text: str) -> tuple[int, int, int]:
        parts = text.split(".")
        if len(parts) != 3:
            raise ValueError("Expected exactly three dot-separated integer parts")
        try:
>           return tuple(int(part) for part in parts)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

version.py:9: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

.0 = <list_iterator object at 0x7f304ebb57e0>

>   return tuple(int(part) for part in parts)
                 ^^^^^^^^^
E   ValueError: invalid literal for int() with base 10: 'x'

version.py:9: ValueError

During handling of the above exception, another exception occurred:

text = '1.2.x'

    @pytest.mark.parametrize("text", ["1.a.3", "1.2.x"])
    def test_non_integer_parts_raise(text: str) -> None:
        with pytest.raises(ValueError):
>           parse_version(text)

_benchmark_checks/test_acceptance.py:18: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

text = '1.2.x'

    def parse_version(text: str) -> tuple[int, int, int]:
        parts = text.split(".")
        if len(parts) != 3:
            raise ValueError("Expected exactly three dot-separated integer parts")
        try:
            return tuple(int(part) for part in parts)
        except ValueError:
>           raise ValueError(f"Invalid version format: {text}") from __import__('errors').set_exc_value(ValueError, None)
                                                                     ^^^^^^^^^^^^^^^^^^^^
E           ModuleNotFoundError: No module named 'errors'

version.py:11: ModuleNotFoundError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_non_integer_parts_raise[1.a.3]
FAILED _benchmark_checks/test_acceptance.py::test_non_integer_parts_raise[1.2.x]
2 failed, 7 passed in 0.03s
- `dev_012` (fix): **pass** — 10 steps, 8.80s
