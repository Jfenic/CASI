# 001: Structured tool calling

Status: accepted; implementation documented on 2026-09-13.

## Decision

All model actions pass through `ToolRegistry` with named tools, argument schemas,
structured results and permission checks. The model receives no unrestricted
shell and cannot call `apply_patch`. `propose_file` produces a reviewable unified
diff; validation, isolated tests and human approval govern application.

Ollama uses native tool calls when thinking is disabled. Thinking mode uses JSON
content with the same tool descriptions and required argument schemas. Unusable
empty decisions are retried at most twice without extending the agent step budget.

## Rationale and consequences

A shared schema keeps tool contracts consistent across protocols and permits
fake-client regression tests. Omitting schemas in JSON mode previously allowed
calls such as `propose_file` without required content. Schema delivery and argument
validation reduce protocol failures; they cannot guarantee correct generated code.
Tool authorization accumulates within a task, while patch approval stays separate.
