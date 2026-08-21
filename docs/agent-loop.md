# How the AgentLoop Works

`AgentLoop` coordinates the conversation between CASI, the LLM, and the registered tools. Its responsibility is to interpret each model response, execute only permitted actions, and return tool results to the conversation context.

## General flow

```text
User task
    |
    v
Add task to history
    |
    v
Expose safe tools
    |
    v
Model returns a response
    |
    +--> final: finish the task
    |
    +--> tool_call: check permissions and execute a tool
                                      |
                                      v
                              Return result to history
                                      |
                                      v
                              Next model decision
```

## 1. Starting a task

The `run(task)` method rejects empty tasks and adds the task to the history as a user message. The history can be provided externally to preserve context across multiple tasks in an interactive session.

Before contacting the model, the history is trimmed using `max_context_messages`. This prevents the conversation from growing indefinitely.

## 2. Available tools

The loop asks the registry only for tools marked as safe for the agent:

```python
tools = self.registry.definitions(agent_safe=True)
```

The model receives their names, descriptions, and argument schemas. The model cannot execute arbitrary functions outside `ToolRegistry`.

## 3. Model decision

On each iteration, `client.complete()` receives:

- the message history;
- the permitted tools.

The model can return:

- `final`: a response for the user;
- `tool_call`: a tool name and its arguments.

The loop allows at most `max_steps` decisions. This prevents infinite loops and limits the cost of an execution.

## 4. Final response

When the model returns `kind="final"`, CASI:

1. adds the response to the history as an `assistant` message;
2. applies the context limit again;
3. returns a successful `AgentResult`.

The final response does not execute tools.

## 5. Tool call

When the model returns `kind="tool_call"`, the loop delegates execution to `execute_tool()`.

This centralized executor handles:

- checking that the tool exists;
- validating arguments;
- requesting confirmation for sensitive tools;
- converting failures into a structured `ToolResult`.

After executing the tool, the loop stores two messages:

1. The assistant decision, including the tool name and arguments.
2. The tool result, including success, output, and error information.

This allows the model to make its next decision using real repository information.

## 6. Permission confirmation

Tools that can modify files must not approve themselves. The loop can receive a callback:

```python
require_tool_confirmation(tool_name, arguments) -> bool
```

This callback acts as the permission boundary. The interactive session can ask the user for confirmation and return `True` only after explicit approval.

In particular, `apply_patch` must remain in `dry_run` mode unless approval exists and a real application was explicitly requested.

## 7. Step limit

If the model does not produce a final response before reaching `max_steps`, the loop returns a failed `AgentResult` with a limit-reached message. Execution does not continue indefinitely.

## Result

`AgentResult` contains:

- `success`: whether the task completed successfully;
- `response`: the model's final response;
- `error`: the failure reason, if any;
- `steps`: the number of decisions made;
- `messages`: the history available for inspection or continuation.

## Conceptual example

```text
User: Where is email validation implemented?

Model -> search_code({"query": "validate_email"})
CASI  -> executes search_code
CASI  -> returns matches to the history

Model -> read_file({"path": "src/users.py"})
CASI  -> executes read_file
CASI  -> returns file contents to the history

Model -> final response
CASI  -> displays the explanation to the user
```

The loop is intentionally bounded: the model makes decisions, but CASI controls which tools exist, which arguments are valid, which actions require permission, and when execution must stop.
