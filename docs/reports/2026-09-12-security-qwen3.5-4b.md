# CASI Benchmark Report — qwen3.5:4b

## Summary

| Metric | Value |
| --- | ---: |
| tasks | 3 |
| task_success_rate | 66.67% |
| agent_success_rate | 66.67% |
| command_success_rate | 66.67% |
| patch_validity_rate | 100.00% |
| average_steps | 12.33 |
| average_duration_seconds | 49.40 |
| average_files_read | 1.33 |
| average_correction_attempts | 0.00 |
| total_prompt_tokens | 34237 |
| total_completion_tokens | 1553 |

## Capabilities

| Capability | Passed / total |
| --- | ---: |
| path_traversal_prevention | 0 / 1 |
| timing_attack_mitigation | 1 / 1 |
| injection_prevention | 1 / 1 |

## Tasks

- `sec_001` (fix): **fail** — 23 steps, 111.32s
  - error: Ollama message does not contain usable content
- `sec_002` (fix): **pass** — 9 steps, 29.58s
- `sec_003` (fix): **pass** — 5 steps, 7.30s
