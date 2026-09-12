# CASI Benchmark Report — qwen2.5-coder:7b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 26 |
| task_success_rate | 80.77% |
| agent_success_rate | 80.77% |
| command_success_rate | 61.54% |
| patch_validity_rate | 100.00% |
| average_steps | 9.96 |
| average_duration_seconds | 15.26 |
| average_files_read | 1.23 |
| average_correction_attempts | 0.42 |
| total_prompt_tokens | 240400 |
| total_completion_tokens | 5578 |

## Tasks

- `task_001` (inspect): **pass** — 4 steps, 4.36s
- `task_002` (read): **pass** — 3 steps, 4.02s
- `task_003` (search): **pass** — 6 steps, 6.76s
- `task_004` (read): **pass** — 6 steps, 6.50s
- `task_005` (inspect): **pass** — 4 steps, 3.13s
- `task_006` (fix): **fail** — 25 steps, 65.28s
  - error: Agent reached the maximum of 12 steps without a valid patch. Last event:   -> nudge: The user requested a code change or passing tests. Tests are still failing: test_validator.py; test_rejects_missing_at_symbol. Fix every remaining failure, not only the requirement mentioned in the task. Call read_file on the failing source and test files if you have not loaded them yet, then Call propose_file with the repository-relative path and the complete file content. CASI will build the unified diff; do not write the diff yourself. Do not describe the fix without calling propose_file.
- `task_007` (fix): **pass** — 11 steps, 15.06s
- `task_008` (fix): **pass** — 6 steps, 8.41s
- `task_009` (read): **pass** — 7 steps, 9.11s
- `task_010` (fix): **pass** — 6 steps, 5.63s
- `task_011` (fix): **fail** — 21 steps, 22.72s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_012` (inspect): **pass** — 12 steps, 10.76s
- `task_013` (fix): **fail** — 29 steps, 56.18s
  - error: Agent reached the maximum of 12 steps without a valid patch. Last event:   -> nudge: The user asked to fix code or pass tests. Tests already ran, but the failing source file(s) are not loaded yet: greeter.py. Call read_file on each path, then Call propose_file with the repository-relative path and the complete file content. CASI will build the unified diff; do not write the diff yourself.
- `task_014` (read): **pass** — 4 steps, 3.53s
- `task_015` (fix): **pass** — 20 steps, 32.43s
- `task_016` (search): **pass** — 5 steps, 5.42s
- `task_017` (fix): **pass** — 9 steps, 9.43s
- `task_018` (search): **pass** — 4 steps, 2.48s
- `task_019` (read): **pass** — 4 steps, 5.93s
- `task_020` (fix): **pass** — 7 steps, 21.67s
- `task_021` (create): **fail** — 20 steps, 24.92s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_022` (create): **pass** — 5 steps, 5.72s
- `task_023` (create): **fail** — 21 steps, 38.34s
  - error: Patch verification failed after exhausting correction attempts: FF                                                                       [100%]
=================================== FAILURES ===================================
_______________________ test_builds_initials_from_names ________________________

    def test_builds_initials_from_names() -> None:
>   	assert initials("Ada", "Lovelace") == "A.L."
E    AssertionError: assert 'A.L' == 'A.L.'
E      
E      - A.L.
E      ?    -
E      + A.L

test_initials.py:5: AssertionError
___________________________ test_ignores_empty_parts ___________________________

    def test_ignores_empty_parts() -> None:
>   	assert initials("Grace", "") == "G."
E    AssertionError: assert 'G' == 'G.'
E      
E      - G.
E      + G

test_initials.py:9: AssertionError
=========================== short test summary info ============================
FAILED test_initials.py::test_builds_initials_from_names - AssertionError: as...
FAILED test_initials.py::test_ignores_empty_parts - AssertionError: assert 'G...
2 failed in 0.01s

- `task_024` (fix): **pass** — 6 steps, 8.64s
- `task_025` (fix): **pass** — 6 steps, 7.40s
- `task_026` (fix): **pass** — 8 steps, 12.83s
