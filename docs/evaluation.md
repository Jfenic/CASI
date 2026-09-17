# Evaluation

CASI distinguishes runtime correctness from model task success. Unit and integration
tests validate the runtime; benchmark results measure a particular model execution.

## Suites

| Suite | Tasks | Verification |
| --- | ---: | --- |
| General | 26 | Task-specific repository checks |
| Development | 12 | Withheld acceptance checks; mutation scoring for test writing |
| Diagnosis | 8 | Structured file, line, cause and evidence grading |
| ML | 6 | Independent behavior checks |
| Fundamentals | 9 | Independent behavior checks |
| Security | 3 | Independent behavior checks |
| Capability extension v2 — Testing | 4 | Correct-code control and 5–8 mutations per task |
| Capability extension v2 — Security | 4 | Attack cases and legitimate behavior |
| Capability extension v2 — ML/features | 4 | Fixed data, training/inference boundaries and numerical checks |

See [capabilities](../benchmarks/CAPABILITIES.md) and each suite README for scope.

The [v2 extension](../benchmarks/capabilities_v2/README.md) is measured separately
by area. Existing suites and their historical rubrics are unchanged. Its test-writing
checks distinguish delivery, correct-code execution and individual mutations; a
failure on the correct implementation leaves mutation quality unscored.

## Interpreting results

- `agent_success` records runtime completion; it can be true when acceptance fails.
- `task_success` is the task outcome, including independent checks when configured.
- A valid patch can implement the wrong behavior; patch validity is not task success.
- Aggregate steps include events beyond model decisions. Duration measures the agent
  run, not all preparation and grading. Token usage depends on model reporting.
- Preserve model, task count, configuration and code state when comparing reports.
  Different suite sizes and single stochastic runs do not establish an improvement.

## Reproducibility

The development evaluator withholds graders and reference solutions from the agent,
restores protected tests and restricts editable files. Final scoring uses Docker
without network or local fallback. Generated tests must pass the reference and
reject five mutations; collection errors are not valid mutation detection.

Reports include JSON, Markdown and per-task artifacts: response, trace, proposal,
verification output and result. A directory from an interrupted execution is a
partial measurement and must not be reported as a complete suite.

Keep historical reports unchanged and record follow-up measurements separately.
Regression tests should reproduce failure behavior without depending on Ollama or
exposing withheld acceptance checks to the agent. See the
[tracker](implementation-tracker.md) for the latest validation.
