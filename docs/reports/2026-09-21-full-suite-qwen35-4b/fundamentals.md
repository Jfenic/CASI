# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 9 |
| task_success_rate | 88.89% |
| agent_success_rate | 100.00% |
| command_success_rate | 88.89% |
| patch_validity_rate | 100.00% |
| average_steps | 8.33 |
| average_duration_seconds | 25.40 |
| average_files_read | 1.67 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 43917 |
| total_completion_tokens | 2538 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| data_structures | 3 / 3 |
| search_algorithms | 1 / 1 |
| discrete_math | 1 / 1 |
| expression_evaluation | 1 / 1 |
| trees | 1 / 1 |
| sorting_algorithms | 1 / 1 |
| number_systems | 0 / 1 |

## Tasks

- `fund_001` (fix): **pass** — 9 steps, 23.93s
- `fund_002` (fix): **pass** — 10 steps, 21.76s
- `fund_003` (fix): **pass** — 7 steps, 27.91s
- `fund_004` (fix): **pass** — 9 steps, 22.46s
- `fund_005` (fix): **pass** — 8 steps, 22.88s
- `fund_006` (fix): **pass** — 8 steps, 21.25s
- `fund_007` (fix): **pass** — 9 steps, 33.15s
- `fund_008` (fix): **fail** — 8 steps, 44.53s
  - error: Independent verification failed: ..F.F...                                                                 [100%]
=================================== FAILURES ===================================
_____________________________ test_to_binary[2-10] _____________________________

n = 2, expected = '10'

    @pytest.mark.parametrize(
        "n,expected",
        [
            (0, "0"),
            (1, "1"),
            (2, "10"),
            (5, "101"),
            (8, "1000"),
            (255, "11111111"),
        ],
    )
    def test_to_binary(n, expected) -> None:
>       assert to_binary(n) == expected
E       AssertionError: assert '01' == '10'
E         
E         - 10
E         + 01

_benchmark_checks/test_acceptance.py:18: AssertionError
____________________________ test_to_binary[8-1000] ____________________________

n = 8, expected = '1000'

    @pytest.mark.parametrize(
        "n,expected",
        [
            (0, "0"),
            (1, "1"),
            (2, "10"),
            (5, "101"),
            (8, "1000"),
            (255, "11111111"),
        ],
    )
    def test_to_binary(n, expected) -> None:
>       assert to_binary(n) == expected
E       AssertionError: assert '0001' == '1000'
E         
E         - 1000
E         ? -
E         + 0001
E         ?    +

_benchmark_checks/test_acceptance.py:18: AssertionError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_to_binary[2-10] - Assertion...
FAILED _benchmark_checks/test_acceptance.py::test_to_binary[8-1000] - Asserti...
2 failed, 6 passed in 0.02s
- `fund_009` (fix): **pass** — 7 steps, 10.74s
