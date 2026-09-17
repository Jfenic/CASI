# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 12 |
| task_success_rate | 75.00% |
| agent_success_rate | 83.33% |
| command_success_rate | 75.00% |
| patch_validity_rate | 100.00% |
| average_steps | 11.17 |
| average_duration_seconds | 105.32 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.08 |
| total_prompt_tokens | 59557 |
| total_completion_tokens | 7194 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| boundary_conditions | 1 / 1 |
| input_validation | 2 / 2 |
| data_processing | 1 / 1 |
| business_rules | 1 / 1 |
| state_and_time | 1 / 1 |
| regression_and_mutability | 1 / 1 |
| module_creation | 1 / 1 |
| algorithm_and_validation | 0 / 1 |
| test_design | 0 / 1 |
| regression_test_design | 0 / 1 |
| mini_project_integration | 1 / 1 |

## Tasks

- `dev_001` (fix): **pass** — 9 steps, 41.66s
- `dev_002` (fix): **pass** — 9 steps, 24.38s
- `dev_003` (fix): **pass** — 9 steps, 28.08s
- `dev_004` (fix): **pass** — 9 steps, 19.03s
- `dev_005` (fix): **pass** — 9 steps, 20.58s
- `dev_006` (fix): **pass** — 9 steps, 31.42s
- `dev_007` (create): **pass** — 6 steps, 28.26s
- `dev_008` (create): **fail** — 6 steps, 32.00s
  - error: Independent verification failed: FF....                                                                   [100%]
=================================== FAILURES ===================================
_____________________ test_ready_queue_and_implicit_nodes ______________________

    def test_ready_queue_and_implicit_nodes():
        graph = {"a": ["b", "b"], "z": [], "d": ["c"]}
        before = deepcopy(graph)
>       assert build_order(graph) == ["b", "a", "c", "d", "z"]
               ^^^^^^^^^^^^^^^^^^

_benchmark_checks/test_acceptance.py:10: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
dependencies.py:32: in build_order
    available = [t for t in all_tasks if t not in completed and prereq_graph[t].issubset(completed)]
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

.0 = <set_iterator object at 0x7ff18c93f7c0>

>   available = [t for t in all_tasks if t not in completed and prereq_graph[t].issubset(completed)]
                                                                ^^^^^^^^^^^^^^^
E   KeyError: 'b'

dependencies.py:32: KeyError
_________________________________ test_diamond _________________________________

    def test_diamond():
>       assert build_order({"d": ["b", "c"], "b": ["a"], "c": ["a"]}) == [
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            "a",
            "b",
            "c",
            "d",
        ]

_benchmark_checks/test_acceptance.py:15: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
dependencies.py:32: in build_order
    available = [t for t in all_tasks if t not in completed and prereq_graph[t].issubset(completed)]
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

.0 = <set_iterator object at 0x7ff18c31b5c0>

>   available = [t for t in all_tasks if t not in completed and prereq_graph[t].issubset(completed)]
                                                                ^^^^^^^^^^^^^^^
E   KeyError: 'a'

dependencies.py:32: KeyError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_ready_queue_and_implicit_nodes
FAILED _benchmark_checks/test_acceptance.py::test_diamond - KeyError: 'a'
2 failed, 4 passed in 0.02s
- `dev_009` (create): **fail** — 25 steps, 606.25s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> nudge: empty model response: Ollama action response failed validation: Unterminated string starting at: line 1 column 38 (char 37)
- `dev_010` (create): **fail** — 23 steps, 395.48s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> nudge: empty model response: Ollama action response failed validation: Unterminated string starting at: line 1 column 26 (char 25)
- `dev_011` (fix): **pass** — 7 steps, 17.42s
- `dev_012` (fix): **pass** — 13 steps, 19.25s
