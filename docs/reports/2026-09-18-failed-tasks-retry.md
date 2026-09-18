# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 7 |
| task_success_rate | 42.86% |
| agent_success_rate | 57.14% |
| command_success_rate | 42.86% |
| patch_validity_rate | 100.00% |
| average_steps | 15.29 |
| average_duration_seconds | 107.49 |
| average_files_read | 1.57 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 85223 |
| total_completion_tokens | 7095 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| input_validation | 1 / 1 |
| data_processing | 0 / 1 |
| business_rules | 1 / 1 |
| regression_and_mutability | 0 / 1 |
| algorithm_and_validation | 0 / 1 |
| test_design | 1 / 1 |
| regression_test_design | 0 / 1 |

## Tasks

- `dev_002` (fix): **pass** — 9 steps, 40.34s
- `dev_003` (fix): **fail** — 28 steps, 217.77s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `dev_004` (fix): **pass** — 9 steps, 38.21s
- `dev_006` (fix): **fail** — 26 steps, 161.24s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> nudge: empty model response: Ollama message does not contain usable content
- `dev_008` (create): **fail** — 6 steps, 36.22s
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
        """
        Perform topological sort with lexicographic ordering at each step.
    
        Args:
            graph: dict mapping task names to lists of prerequisite tasks
    
        Returns:
            List of tasks in topological order
    
        Raises:
            ValueError: If there's a cycle in the dependency graph
        """
        # Build the set of all nodes (including only prerequisites)
        all_nodes = set(graph.keys())
        for prereq in graph.values():
            all_nodes.update(prereq)
    
        # Build adjacency list and in-degree count
        adj = defaultdict(set)
        in_degree = defaultdict(int)
    
        # Initialize all nodes with in-degree 0, then process edges
        for node in all_nodes:
            in_degree[node] = 0
    
        # For each task, add edges from its prerequisites to it
        for task, prereqs in graph.items():
            in_degree[task] += len(prereqs)
            for prereq in set(prereqs):  # Unique prerequisites
                adj[prereq].add(task)
    
        # Get all tasks with in-degree 0 (no unmet prerequisites)
        available = sorted([n for n, d in in_degree.items() if d == 0])
        result = []
        processed = set()
    
        while available:
            current = available.pop(0)  # Pick lexicographically smallest first
            result.append(current)
            processed.add(current)
    
            # Find all tasks that depend on current and update in-degree
            for task in sorted(adj.get(current, [])):
                in_degree[task] -= 1
                if in_degree[task] == 0:
                    available.append(task)
    
            available.sort()
    
        # Check for cycles - any remaining nodes weren't processed
        if len(result) < len(all_nodes):
>           raise ValueError("Cycle detected in dependency graph")
E           ValueError: Cycle detected in dependency graph

dependencies.py:55: ValueError
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_ready_queue_and_implicit_nodes
1 failed, 5 passed in 0.03s
- `dev_009` (create): **pass** — 6 steps, 38.71s
- `dev_010` (create): **fail** — 23 steps, 219.91s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> nudge: empty model response: Ollama action response does not contain content
