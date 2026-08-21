# Evaluation

# Evaluation

## Benchmark stages

The benchmark suite is divided into three stages:

- Repository exploration: identify and read relevant files.
- Patch validation: inspect or validate a proposed change safely.
- Sandbox execution: run the relevant checks with isolation and limits.

## MVP metrics

- Task success: the expected result or test outcome is achieved.
- Tool-call validity: requested tools and arguments pass schema validation.
- Safety: no path boundary, sensitive-file, or sandbox policy is violated.
- Efficiency: number of agent steps, tool calls, and elapsed time.
- Reproducibility: the same task produces a comparable result in a clean fixture.

## Reporting

Each benchmark result should record the task name, success state, error if any, elapsed time, step count, tool calls, and test output. A failed task must distinguish model failure, tool validation failure, execution failure, and patch failure.
