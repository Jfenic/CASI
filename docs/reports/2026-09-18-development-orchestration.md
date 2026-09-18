# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 12 |
| task_success_rate | 41.67% |
| agent_success_rate | 75.00% |
| command_success_rate | 41.67% |
| patch_validity_rate | 100.00% |
| average_steps | 12.83 |
| average_duration_seconds | 131.68 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.17 |
| total_prompt_tokens | 88531 |
| total_completion_tokens | 9892 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| boundary_conditions | 1 / 1 |
| input_validation | 1 / 2 |
| data_processing | 0 / 1 |
| business_rules | 0 / 1 |
| state_and_time | 1 / 1 |
| regression_and_mutability | 0 / 1 |
| module_creation | 1 / 1 |
| algorithm_and_validation | 0 / 1 |
| test_design | 0 / 1 |
| regression_test_design | 0 / 1 |
| mini_project_integration | 1 / 1 |

## Tasks

- `dev_001` (fix): **pass** — 9 steps, 27.28s
- `dev_002` (fix): **fail** — 9 steps, 35.20s
  - error: Independent verification failed: ..............FFFF.                                                      [100%]
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
____________________________ test_bad_type[value2] _____________________________

value = []

    @pytest.mark.parametrize("value", [0, 1, [], {}])
    def test_bad_type(value):
        with pytest.raises(TypeError):
>           parse_bool(value)

_benchmark_checks/test_acceptance.py:29: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

value = [], default = False

    def parse_bool(value, default=False):
        """Parse boolean value from various input types.
    
        None returns default.
        Booleans remain unchanged.
        Strings are stripped and case-insensitive:
        - true/1/yes/on → True
        - false/0/no/off → False
        - Other strings raise ValueError
        Non-string non-bool values raise TypeError.
        """
        # Handle None - return default
        if value is None:
            return default
    
        # Handle boolean types - return unchanged
        if isinstance(value, bool):
            return value
    
        # Check if value can be converted to string
        try:
            str_value = str(value)
        except TypeError:
            raise TypeError(f"Cannot convert {type(value).__name__} to string for boolean parsing")
    
        # Strip whitespace and convert to lowercase
        str_value = str_value.strip().lower()
    
        # Check for True values
        if str_value in ("true", "1", "yes", "on"):
            return True
    
        # Check for False values
        if str_value in ("false", "0", "no", "off"):
            return False
    
        # Any unrecognized string value raises ValueError
>       raise ValueError(f"Invalid boolean representation: '{str_value}'")
E       ValueError: Invalid boolean representation: '[]'

config.py:38: ValueError
____________________________ test_bad_type[value3] _____________________________

value = {}

    @pytest.mark.parametrize("value", [0, 1, [], {}])
    def test_bad_type(value):
        with pytest.raises(TypeError):
>           parse_bool(value)

_benchmark_checks/test_acceptance.py:29: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

value = {}, default = False

    def parse_bool(value, default=False):
        """Parse boolean value from various input types.
    
        None returns default.
        Booleans remain unchanged.
        Strings are stripped and case-insensitive:
        - true/1/yes/on → True
        - false/0/no/off → False
        - Other strings raise ValueError
        Non-string non-bool values raise TypeError.
        """
        # Handle None - return default
        if value is None:
            return default
    
        # Handle boolean types - return unchanged
        if isinstance(value, bool):
            return value
    
        # Check if value can be converted to string
        try:
            str_value = str(value)
        except TypeError:
            raise TypeError(f"Cannot convert {type(value).__name__} to string for boolean parsing")
    
        # Strip whitespace and convert to lowercase
        str_value = str_value.strip().lower()
    
        # Check for True values
        if str_value in ("true", "1", "yes", "on"):
            return True
    
        # Check for False values
        if str_value in ("false", "0", "no", "off"):
            return False
    
        # Any unrecognized string value raises ValueError
>       raise ValueError(f"Invalid boolean representation: '{str_value}'")
E       ValueError: Invalid boolean representation: '{}'

config.py:38: ValueError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_bad_type[0] - Failed: DID N...
FAILED _benchmark_checks/test_acceptance.py::test_bad_type[1] - Failed: DID N...
FAILED _benchmark_checks/test_acceptance.py::test_bad_type[value2] - ValueErr...
FAILED _benchmark_checks/test_acceptance.py::test_bad_type[value3] - ValueErr...
4 failed, 15 passed in 0.04s
- `dev_003` (fix): **fail** — 7 steps, 16.83s
  - error: Independent verification failed: .F...                                                                    [100%]
=================================== FAILURES ===================================
____________________________ test_multiline_product ____________________________

    def test_multiline_product():
>       assert totals('product,quantity\n"two\nlines",4\n') == {"two\nlines": 4}
E       AssertionError: assert {'twolines': 4} == {'two\nlines': 4}
E         
E         Left contains 1 more item:
E         {'twolines': 4}
E         Right contains 1 more item:
E         {'two\nlines': 4}
E         Use -v to get more diff

_benchmark_checks/test_acceptance.py:11: AssertionError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_multiline_product - Asserti...
1 failed, 4 passed in 0.02s
- `dev_004` (fix): **fail** — 7 steps, 27.53s
  - error: Independent verification failed: ...F..                                                                   [100%]
=================================== FAILURES ===================================
___________________________ test_precision_and_input ___________________________

    def test_precision_and_input():
        lines = [("9007199254740993.01", 1), ("0.10", 3)]
        before = list(lines)
>       assert invoice_total(lines) == "9007199254740993.31"
E       AssertionError: assert '9007199254740994.00' == '9007199254740993.31'
E         
E         - 9007199254740993.31
E         ?                ^ ^^
E         + 9007199254740994.00
E         ?                ^ ^^

_benchmark_checks/test_acceptance.py:21: AssertionError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_precision_and_input - Asser...
1 failed, 5 passed in 0.02s
- `dev_005` (fix): **pass** — 9 steps, 21.38s
- `dev_006` (fix): **fail** — 28 steps, 185.74s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> nudge: empty model response: Ollama message does not contain usable content
- `dev_007` (create): **pass** — 6 steps, 24.16s
- `dev_008` (create): **fail** — 6 steps, 36.82s
  - error: Independent verification failed: F.....                                                                   [100%]
=================================== FAILURES ===================================
_____________________ test_ready_queue_and_implicit_nodes ______________________

    def test_ready_queue_and_implicit_nodes():
        graph = {"a": ["b", "b"], "z": [], "d": ["c"]}
        before = deepcopy(graph)
>       assert build_order(graph) == ["b", "a", "c", "d", "z"]
               ^^^^^^^^^^^^^^^^^^

_benchmark_checks/test_acceptance.py:10: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

graph = {'a': ['b', 'b'], 'z': [], 'd': ['c']}

    def build_order(graph):
        """Return tasks in topological order, selecting lexicographically smallest available at each step.
    
        Args:
            graph: dict mapping task name -> list of prerequisites
    
        Returns:
            List of tasks in build order
    
        Raises:
            ValueError: If there is a cycle in the dependency graph
        """
        if not graph:
            return []
    
        # Collect all tasks (both as keys and as prerequisite values)
        all_tasks = set(graph.keys())
        for prereq_list in graph.values():
            all_tasks.update(prereq_list)
    
        n = len(all_tasks)
    
        # Track in-degree: number of unprocessed prerequisites
        in_degree = {task: 0 for task in all_tasks}
    
        # Build adjacency list: reverse dependencies (who depends on this task)
        dependents = defaultdict(set)  # task -> set of tasks that depend on it
    
        for task, prereqs in graph.items():
            for prereq in prereqs:
                if prereq not in all_tasks:
                    raise ValueError(f"Unknown prerequisite {prereq}")
                in_degree[task] += 1
                dependents[prereq].add(task)
    
        # Min-heap to store tasks whose prerequisites are satisfied
        # Always picks lexicographically smallest
        heap = [task for task, deg in in_degree.items() if deg == 0]
        heapq.heapify(heap)
    
        result = []
        processed_count = 0
    
        while heap:
            task = heapq.heappop(heap)
            result.append(task)
            processed_count += 1
    
            # Update dependents: decrement their in-degree
            for dependent in dependents[task]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    heapq.heappush(heap, dependent)
    
        # Check for cycle: all tasks must have been processed
        if processed_count < n:
>           raise ValueError("Cycle detected in dependency graph")
E           ValueError: Cycle detected in dependency graph

dependencies.py:62: ValueError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_ready_queue_and_implicit_nodes
1 failed, 5 passed in 0.02s
- `dev_009` (create): **fail** — 30 steps, 705.57s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> list_files ok: retrying.py test_visible.py
- `dev_010` (create): **fail** — 23 steps, 457.54s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> nudge: empty model response: Ollama action response does not contain content
- `dev_011` (fix): **pass** — 7 steps, 21.21s
- `dev_012` (fix): **pass** — 13 steps, 20.85s
