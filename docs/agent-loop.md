# How the AgentLoop Works

`AgentLoop` coordinates model decisions and registered tools. CLI and API use it
through task planning and specialized profiles. It has bounded model steps,
file reads, repeated calls, format retries and patch correction attempts.

## Task and context

The loop rejects an empty task, preserves conversation history, determines intent
and loads relevant repository context. Repair pipelines run tests and read relevant
source and test files; diagnosis loads evidence without proposing changes.
The task contract remains part of creation and repair guidance even when visible
tests cover only some requirements. Latest patch-test failures guide corrections.

Interactive sessions preserve context until `/clear`. `/context` and `/compact`
inspect or summarize history; automatic compaction is bounded by configuration.
Planning and profiles guide work; task permissions accumulate as the model needs
READ, EXECUTE or MUTATE capabilities.

## Decisions and tools

The model receives agent-safe tool definitions and returns a final response,
clarification or tool call. The registry checks names and arguments and the
executor enforces authorization. Tool results return to conversation history.
The loop may narrow available tools after context has been loaded to stop repeated
searches. `apply_patch` is never agent-callable.

`propose_file(path, content)` builds a unified diff from complete file content.
It does not write the original repository. A successful proposal enters patch
verification rather than simply returning an unverified success.

## Completion and retries

- Read tasks may complete with a grounded final answer.
- Diagnosis requires structured `file`, `line`, `cause` and `evidence`; invalid
  responses receive bounded format nudges and ultimately fail.
- Change tasks cannot complete successfully without a required valid patch.
  Premature answers receive bounded nudges to inspect or propose the change.
- Patch verification checks syntax, paths and applicability, then runs tests on
  a temporary copy. Failures return their latest output and classification to
  the model, with up to four correction attempts by default.
- Empty Ollama decisions are retried inside the client at most twice. This does
  not increase model-step limits, but each request has its own timeout. Exhausted
  empty-response retries propagate an error; their token usage is not retained
  in the current error contract.
- Exceeding step or retry limits returns failure with the available trace.

Tool authorization and human approval of a concrete patch are separate. The CLI
or API presents a verified proposal for approval before modifying the repository.
Passing repository tests is evidence about those tests; the independent benchmark
may still reject the proposal for unmet requirements.

## Observability

`AgentResult` carries status, response, error, clarification, messages, step count,
patch verification and trace information. Structured traces record model decisions,
pipeline reads, tools, rejected calls, nudges, timings and reported token usage.
The execution summary exposes aggregate metrics to CLI logs and API responses.

See [architecture](architecture.md), [security](security.md) and
[evaluation](evaluation.md) for the surrounding contracts.
