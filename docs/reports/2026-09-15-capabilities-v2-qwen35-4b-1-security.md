# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 4 |
| task_success_rate | 75.00% |
| agent_success_rate | 75.00% |
| command_success_rate | 75.00% |
| patch_validity_rate | 100.00% |
| average_steps | 7.50 |
| average_duration_seconds | 36.60 |
| average_files_read | 2.00 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 19484 |
| total_completion_tokens | 1607 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| tenant_authorization | 1 / 1 |
| archive_path_validation | 1 / 1 |
| parameterized_query_behavior | 1 / 1 |
| structured_secret_redaction | 0 / 1 |

## Tasks

- `sec_v2_001` (fix): **pass** — 8 steps, 43.90s
- `sec_v2_002` (fix): **pass** — 6 steps, 33.22s
- `sec_v2_003` (fix): **pass** — 8 steps, 21.70s
- `sec_v2_004` (fix): **fail** — 8 steps, 47.57s
  - error: Ollama message does not contain usable content
