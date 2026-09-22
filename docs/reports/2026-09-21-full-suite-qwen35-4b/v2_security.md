# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 4 |
| task_success_rate | 50.00% |
| agent_success_rate | 75.00% |
| command_success_rate | 50.00% |
| patch_validity_rate | 100.00% |
| average_steps | 14.75 |
| average_duration_seconds | 97.21 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 89215 |
| total_completion_tokens | 2802 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| tenant_authorization | 1 / 1 |
| archive_path_validation | 0 / 1 |
| parameterized_query_behavior | 1 / 1 |
| structured_secret_redaction | 0 / 1 |

## Tasks

- `sec_v2_001` (fix): **pass** — 9 steps, 30.40s
- `sec_v2_002` (fix): **fail** — 9 steps, 56.39s
  - error: Independent verification failed: .........F.                                                              [100%]
=================================== FAILURES ===================================
______________________ test_symlink_escape_and_safe_link _______________________

tmp_path = PosixPath('/tmp/pytest-of-unknown/pytest-0/test_symlink_escape_and_safe_l0')

    def test_symlink_escape_and_safe_link(tmp_path):
        root = tmp_path / "base"
        root.mkdir()
        outside = tmp_path / "base-other"
        outside.mkdir()
        (root / "escape").symlink_to(outside, target_is_directory=True)
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE ValueError

_benchmark_checks/test_acceptance.py:25: Failed
=========================== short test summary info ============================
FAILED _benchmark_checks/test_acceptance.py::test_symlink_escape_and_safe_link
1 failed, 10 passed in 0.03s
- `sec_v2_003` (fix): **pass** — 7 steps, 11.14s
- `sec_v2_004` (fix): **fail** — 34 steps, 290.92s
  - error: Agent reached the maximum of 18 steps without a valid patch. Last event:   -> nudge: protocol violation: action_required
