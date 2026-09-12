# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 26 |
| task_success_rate | 76.92% |
| agent_success_rate | 76.92% |
| command_success_rate | 61.54% |
| patch_validity_rate | 100.00% |
| average_steps | 9.96 |
| average_duration_seconds | 14.35 |
| average_files_read | 1.27 |
| average_correction_attempts | 0.12 |
| total_prompt_tokens | 242974 |
| total_completion_tokens | 8256 |

## Tasks

- `task_001` (inspect): **pass** — 4 steps, 4.41s
- `task_002` (read): **pass** — 3 steps, 4.19s
- `task_003` (search): **pass** — 4 steps, 3.06s
- `task_004` (read): **pass** — 4 steps, 4.61s
- `task_005` (inspect): **pass** — 4 steps, 3.23s
- `task_006` (fix): **fail** — 18 steps, 21.91s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_007` (fix): **fail** — 29 steps, 40.69s
  - error: Agent reached the maximum of 12 steps without a valid patch. Last event:   -> nudge: The user requested a code change or passing tests. Tests are still failing: test_validator.py; test_rejects_missing_at_symbol. Fix every remaining failure, not only the requirement mentioned in the task. Call read_file on the failing source and test files if you have not loaded them yet, then Call propose_file with the repository-relative path and the complete file content. CASI will build the unified diff; do not write the diff yourself. Do not describe the fix without calling propose_file.
- `task_008` (fix): **pass** — 6 steps, 6.24s
- `task_009` (read): **fail** — 23 steps, 86.09s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_010` (fix): **pass** — 6 steps, 5.14s
- `task_011` (fix): **pass** — 6 steps, 5.60s
- `task_012` (inspect): **pass** — 4 steps, 3.03s
- `task_013` (fix): **pass** — 15 steps, 14.55s
- `task_014` (read): **pass** — 4 steps, 3.18s
- `task_015` (fix): **pass** — 6 steps, 4.37s
- `task_016` (search): **pass** — 5 steps, 3.53s
- `task_017` (fix): **pass** — 19 steps, 15.37s
- `task_018` (search): **pass** — 4 steps, 3.63s
- `task_019` (read): **pass** — 8 steps, 6.05s
- `task_020` (fix): **fail** — 12 steps, 17.03s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_021` (create): **fail** — 25 steps, 42.61s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_022` (create): **pass** — 5 steps, 6.06s
- `task_023` (create): **fail** — 21 steps, 41.36s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_024` (fix): **pass** — 6 steps, 6.46s
- `task_025` (fix): **pass** — 10 steps, 10.63s
- `task_026` (fix): **pass** — 8 steps, 10.12s


# CASI Benchmark Report — qwen2.5-coder:7b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 26 |
| task_success_rate | 84.62% |
| agent_success_rate | 84.62% |
| command_success_rate | 61.54% |
| patch_validity_rate | 100.00% |
| average_steps | 9.38 |
| average_duration_seconds | 14.40 |
| average_files_read | 1.15 |
| average_correction_attempts | 0.15 |
| total_prompt_tokens | 220530 |
| total_completion_tokens | 4769 |

## Tasks

- `task_001` (inspect): **pass** — 6 steps, 24.60s
- `task_002` (read): **pass** — 3 steps, 2.91s
- `task_003` (search): **pass** — 6 steps, 7.15s
- `task_004` (read): **pass** — 4 steps, 4.12s
- `task_005` (inspect): **pass** — 6 steps, 5.47s
- `task_006` (fix): **pass** — 6 steps, 9.12s
- `task_007` (fix): **fail** — 22 steps, 25.57s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_008` (fix): **pass** — 6 steps, 8.86s
- `task_009` (read): **pass** — 4 steps, 5.77s
- `task_010` (fix): **fail** — 21 steps, 26.17s
  - error: The agent finished without a valid patch. Ask CASI again to call propose_file with the complete corrected file content.
- `task_011` (fix): **pass** — 8 steps, 16.37s
- `task_012` (inspect): **pass** — 6 steps, 6.30s
- `task_013` (fix): **fail** — 26 steps, 41.12s
  - error: Agent reached the maximum of 12 steps without a valid patch. Last event:   -> nudge: propose_file failed: Proposed Python content for greeter.py has a syntax error at line 1: illegal target for annotation
- `task_014` (read): **pass** — 6 steps, 6.25s
- `task_015` (fix): **pass** — 26 steps, 39.40s
- `task_016` (search): **pass** — 5 steps, 6.54s
- `task_017` (fix): **pass** — 7 steps, 6.50s
- `task_018` (search): **pass** — 6 steps, 6.83s
- `task_019` (read): **pass** — 4 steps, 3.02s
- `task_020` (fix): **pass** — 7 steps, 25.36s
- `task_021` (create): **pass** — 5 steps, 6.42s
- `task_022` (create): **pass** — 5 steps, 5.08s
- `task_023` (create): **fail** — 29 steps, 56.95s
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
2 failed in 0.02s

- `task_024` (fix): **pass** — 8 steps, 14.31s
- `task_025` (fix): **pass** — 6 steps, 7.07s
- `task_026` (fix): **pass** — 6 steps, 7.20s
