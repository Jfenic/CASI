# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 3 |
| task_success_rate | 100.00% |
| agent_success_rate | 100.00% |
| command_success_rate | 100.00% |
| patch_validity_rate | 100.00% |
| average_steps | 8.00 |
| average_duration_seconds | 23.64 |
| average_files_read | 1.33 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 12798 |
| total_completion_tokens | 911 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| path_traversal_prevention | 1 / 1 |
| timing_attack_mitigation | 1 / 1 |
| injection_prevention | 1 / 1 |

## Tasks

- `sec_001` (fix): **pass** — 10 steps, 33.51s
- `sec_002` (fix): **pass** — 6 steps, 11.08s
- `sec_003` (fix): **pass** — 8 steps, 26.33s
