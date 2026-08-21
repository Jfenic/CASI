# Architecture

# Architecture

## Current baseline

The repository is organized around five boundaries:

- `repository`: safe inspection, file reading, and text search.
- `tools`: structured argument validation and tool execution results.
- `llm`: model clients and response parsing.
- `agent`: the decision loop and tool executor.
- `patching` and `sandbox`: change validation/application and isolated command execution.

The currently usable path is read-only repository inspection through the CLI and the first three tools. The LLM, agent loop, patching, and sandbox modules are extension points and are not yet part of the end-to-end workflow.

## MVP flow

The first complete workflow should be:

1. Receive a repository path and a task.
2. Ask the LLM for either a final response or a structured tool call.
3. Validate and execute the requested tool through `ToolRegistry`.
4. Return the tool result to the LLM.
5. Stop on a final response, an execution error, or a configured step limit.

Commands that execute tests or inspect changes must go through the sandbox boundary. File modifications must go through patch validation before application.

## Design constraints

- Tool inputs and outputs remain structured and deterministic.
- The agent loop has explicit limits for steps, command time, and output size.
- Read-only operations stay separate from mutation and process execution.
- Every completed capability gets a focused test and a benchmark task.
