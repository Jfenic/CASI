"""Bounded agent execution loop."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from casi.agent.conversation import (
    ContextCompactNotifier,
    ContextCompactPrompt,
    Conversation,
)
from casi.agent.intent import (
    RoutingMode,
    TaskIntent,
    build_task_context,
    classify_intent,
    extract_search_targets,
    intent_supports_pipeline,
    is_mutation_intent,
    parse_routing_mode,
    should_defer_clarification,
    task_requests_code_change,
)
from casi.agent.nudges import (
    nudge_for_missing_local_modules,
    nudge_for_premature_clarification,
    nudge_for_propose_file_failure,
    nudge_for_read_file_instead_of_search,
    nudge_for_repeated_clarification,
)
from casi.agent.patch_verify import verify_patch_response
from casi.agent.pipelines import (
    nudge_after_create_pipeline,
    nudge_after_fix_pipeline,
    nudge_after_pipeline_fallback,
    run_fix_pipeline,
    run_repository_pipeline,
)
from casi.agent.profiles import AgentProfile
from casi.agent.response_policy import ResponsePolicy, RetryBudget
from casi.agent.session import TaskScope
from casi.agent.state import AgentResult, PatchVerification
from casi.agent.task_permission import TaskPermissionState
from casi.agent.test_failures import output_reports_failures
from casi.agent.tool_confirmation import build_task_tool_confirmation
from casi.agent.trace import AgentTraceRecorder
from casi.config import settings
from casi.llm.base import ChatMessage, LLMClient, LLMResponse, ToolDefinition
from casi.patching.extract import extract_patch
from casi.tools.registry import ToolRegistry
from casi.tools.result import ToolResult

_MISSING_PATCH_ERROR = (
    "The agent finished without a valid patch. "
    "Ask CASI again to call propose_file with the complete corrected file content."
)

ActivityNotifier = Callable[[str], None]


@dataclass
class _ActiveTask:
    """In-flight task state kept across clarification pauses."""

    scope: TaskScope
    original_task: str
    task_context: str
    intent: TaskIntent
    retries: RetryBudget
    permissions: TaskPermissionState = field(default_factory=TaskPermissionState)
    correction_attempts: int = 0
    patch_verification: PatchVerification | None = None
    continuing_after_clarification: bool = False
    next_step: int = 1


class AgentLoop:
    """Coordinate model decisions, intent routing, and structured tool execution."""

    def __init__(
        self,
        client: LLMClient,
        registry: ToolRegistry,
        *,
        profile: AgentProfile | None = None,
        max_steps: int = 8,
        max_correction_attempts: int | None = None,
        messages: list[ChatMessage] | None = None,
        require_tool_confirmation: Callable[[str, dict[str, object]], bool]
        | None = None,
        on_context_compact: ContextCompactNotifier | None = None,
        on_context_compact_prompt: ContextCompactPrompt | None = None,
        on_activity: ActivityNotifier | None = None,
        trace: AgentTraceRecorder | None = None,
        routing_mode: str | RoutingMode | None = None,
        response_policy: ResponsePolicy | None = None,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be greater than or equal to 1")
        self.client = client
        self.registry = registry
        self.profile = profile
        self.max_steps = max_steps
        self.max_correction_attempts = (
            settings.max_correction_attempts
            if max_correction_attempts is None
            else max_correction_attempts
        )
        if self.max_correction_attempts < 0:
            raise ValueError(
                "max_correction_attempts must be greater than or equal to 0"
            )
        if routing_mode is None:
            self.routing_mode = parse_routing_mode(settings.agent_routing_mode)
        elif isinstance(routing_mode, RoutingMode):
            self.routing_mode = routing_mode
        else:
            self.routing_mode = parse_routing_mode(routing_mode)
        self.messages = messages if messages is not None else []
        self.require_tool_confirmation = require_tool_confirmation
        self.on_context_compact = on_context_compact
        self.on_context_compact_prompt = on_context_compact_prompt
        self.on_activity = on_activity
        self.trace = trace
        self.response_policy = response_policy or ResponsePolicy()
        self._clarification_pending = False
        self._active_task: _ActiveTask | None = None
        self.conversation = self._build_conversation(self.messages)

    @property
    def awaiting_clarification(self) -> bool:
        """Return whether the loop is paused waiting for a user answer."""

        return self._clarification_pending and self._active_task is not None

    def _build_conversation(
        self,
        messages: list[ChatMessage],
        *,
        permission_state: TaskPermissionState | None = None,
        intent: TaskIntent | None = None,
    ) -> Conversation:
        confirmation = self.require_tool_confirmation
        if permission_state is not None:
            confirmation = build_task_tool_confirmation(
                self.require_tool_confirmation,
                permission_state,
                intent=intent,
                on_permission=(
                    lambda tool, tier, approved: (
                        self.trace.record_permission(
                            tool,
                            tier.value,
                            approved=approved,
                        )
                        if self.trace is not None
                        else None
                    )
                ),
            )
        return Conversation(
            messages,
            self.registry,
            llm_client=self.client,
            on_context_compact=self.on_context_compact,
            on_context_compact_prompt=self.on_context_compact_prompt,
            require_tool_confirmation=confirmation,
        )

    def _mark_clarification_pending(self) -> None:
        self._clarification_pending = True

    def _notify_activity(self, message: str) -> None:
        if self.on_activity is not None:
            self.on_activity(message)

    def _with_trace(self, result: AgentResult) -> AgentResult:
        if self.trace is None or not self.trace.events:
            return result
        return AgentResult(
            success=result.success,
            response=result.response,
            clarification=result.clarification,
            plan=result.plan,
            error=result.error,
            steps=result.steps,
            messages=result.messages,
            patch_verification=result.patch_verification,
            requested_code_change=result.requested_code_change,
            trace=list(self.trace.events),
        )

    def _step_limit_error(self, step_limit: int, active: _ActiveTask) -> str:
        message = f"Agent reached the maximum of {step_limit} steps"
        if is_mutation_intent(active.intent):
            message += " without a valid patch"
        if self.trace is not None and self.trace.events:
            last = self.trace.events[-1]
            message += f". Last event: {last}"
        return message

    def _in_mutation_workflow(self, active: _ActiveTask) -> bool:
        """Return whether the task has moved into test or code-change work."""

        if is_mutation_intent(active.intent):
            return True
        if task_requests_code_change(active.task_context):
            return True
        last_tests = self.conversation.last_tool_result("run_tests")
        if last_tests is not None and self._should_run_fix_pipeline(last_tests.output):
            return True
        return self.conversation.tool_was_used("propose_file")

    def _tools_for_task(self) -> list[ToolDefinition]:
        if self.profile is not None and self.profile.objective is TaskIntent.PRESENT:
            return []
        tools = self.registry.definitions(agent_safe=True)
        if (
            self.profile is not None
            and self.profile.objective is TaskIntent.RECALL_PLAN
        ):
            return [tool for tool in tools if tool.name == "get_session_plan"]
        return [tool for tool in tools if tool.name != "validate_patch"]

    def _tools_for_step(
        self,
        intent: TaskIntent,
        tools: list[ToolDefinition],
        *,
        mutation_workflow: bool,
    ) -> list[ToolDefinition]:
        """Stop tool loops once a fix has enough repository context."""

        if mutation_workflow or is_mutation_intent(intent):
            if (
                self.conversation.tool_was_used("run_tests")
                and self.conversation.read_file_paths()
            ):
                return [
                    tool for tool in tools if tool.name in {"read_file", "propose_file"}
                ]
            return [tool for tool in tools if tool.name != "validate_patch"]
        return tools

    def _model_label(self) -> str:
        model = getattr(self.client, "model", None)
        timeout = getattr(self.client, "timeout_seconds", None)
        if isinstance(model, str) and model:
            if isinstance(timeout, (int, float)):
                return f"{model} (timeout {int(timeout)}s)"
            return model
        return "model"

    def run(self, task: str) -> AgentResult:
        """Run the agent until it returns a final response or reaches the limit."""

        if not task.strip():
            raise ValueError("task must not be empty")
        if self.awaiting_clarification:
            return self._resume(task.strip())
        return self._start(task.strip())

    def _start(self, task: str) -> AgentResult:
        if self.trace is not None:
            model = getattr(self.client, "model", None)
            self.trace.set_context(
                model=model if isinstance(model, str) else None,
                repository=str(self.registry.repository_path),
                task=task,
            )
            if self.trace.started_at is None:
                self.trace.mark_started()
        scope = TaskScope(session_messages=self._session_merge_target())
        tools = self._tools_for_task()
        task_context = build_task_context(task, self.messages)
        intent = self._resolve_intent(task_context)
        active = _ActiveTask(
            scope=scope,
            original_task=task,
            task_context=task_context,
            intent=intent,
            retries=RetryBudget(),
        )
        self._active_task = active
        self.conversation = self._build_conversation(
            active.scope.task_messages,
            permission_state=active.permissions,
            intent=active.intent,
        )
        self.conversation.append("user", task)

        if task_requests_code_change(task_context):
            self._bootstrap_code_change_workflow(task_context, active.retries)
        elif self._should_prefetch_repository(intent, task_context, False):
            self._notify_activity("Inspecting repository before first model call...")
            self._run_pipeline(intent, task_context, active.retries)

        return self._run_steps(active, tools)

    def _session_merge_target(self) -> list[ChatMessage] | None:
        if self.profile is not None and self.profile.objective is TaskIntent.PRESENT:
            return None
        return self.messages

    def _resume(self, answer: str) -> AgentResult:
        active = self._active_task
        if active is None:
            return self._start(answer)

        self._clarification_pending = False
        self.conversation = self._build_conversation(
            active.scope.task_messages,
            permission_state=active.permissions,
            intent=active.intent,
        )
        self.conversation.append("user", answer)
        tools = self._tools_for_task()
        active.task_context = build_task_context(answer, self.messages)
        active.intent = self._resolve_intent(active.task_context)
        active.continuing_after_clarification = True

        if intent_supports_pipeline(active.intent):
            self._notify_activity("Inspecting repository after clarification...")
            self._run_pipeline(active.intent, active.task_context, active.retries)

        return self._run_steps(active, tools)

    def _finish(self, active: _ActiveTask, result: AgentResult) -> AgentResult:
        active.scope.merge_result(active.original_task, result)
        self._active_task = None
        self._clarification_pending = False
        self.conversation = self._build_conversation(self.messages)
        return self._with_trace(result)

    def _run_steps(
        self,
        active: _ActiveTask,
        tools: list[ToolDefinition],
    ) -> AgentResult:
        step_limit = self._step_limit_for_intent(active.intent, active)
        active_messages = active.scope.task_messages

        for step in range(active.next_step, step_limit + 1):
            self.conversation.compact_if_needed()
            mutation_workflow = self._in_mutation_workflow(active)
            step_tools = self._tools_for_step(
                active.intent,
                tools,
                mutation_workflow=mutation_workflow,
            )
            self._notify_activity(
                f"Thinking with {self._model_label()} (decision {step}/{step_limit})..."
            )
            started = time.perf_counter()
            response = self.client.complete(
                active_messages,
                step_tools,
            )
            duration_ms = (time.perf_counter() - started) * 1000
            if self.trace is not None:
                self.trace.record_step_timing(
                    step, step_limit, response.kind, duration_ms
                )
                self.trace.record_usage(
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                )

            if response.kind == "tool_call":
                tool_name = response.tool_name or "unknown"
                if self.trace is not None:
                    self.trace.record_tool_call(
                        step,
                        step_limit,
                        tool_name,
                        response.arguments,
                    )
                if tool_name == "propose_file" and any(
                    tool.name == tool_name for tool in step_tools
                ):
                    result = self.conversation.execute_tool(
                        tool_name, response.arguments
                    )
                    if self.trace is not None:
                        self.trace.record_tool_result(
                            tool_name,
                            success=result.success,
                            output=result.output or result.error or "",
                            metadata=result.metadata,
                        )
                    if not result.success:
                        error = result.error or "propose_file failed"
                        self.conversation.append_nudge(
                            Conversation.format_tool_call(
                                tool_name, response.arguments
                            ),
                            nudge_for_propose_file_failure(error).user_message,
                        )
                        if self.trace is not None:
                            self.trace.record_nudge(
                                f"propose_file failed: {error}",
                            )
                        continue
                    response = LLMResponse.final(result.output)
                elif mutation_workflow and not any(
                    tool.name == tool_name for tool in step_tools
                ):
                    if tool_name == "search_code":
                        message = nudge_for_read_file_instead_of_search(
                            self.conversation.unread_search_code_paths(),
                            sources_already_read=True,
                        ).user_message
                    else:
                        message = (
                            "Repository inspection is complete. Only read_file and "
                            "propose_file are available now. Re-read a loaded file "
                            "only if needed, then call propose_file with its "
                            "repository-relative path and complete corrected "
                            "content. Do not hand-write another diff."
                        )
                    self.conversation.append_nudge(
                        Conversation.format_tool_call(tool_name, response.arguments),
                        message,
                    )
                    if self.trace is not None:
                        allowed = ", ".join(tool.name for tool in step_tools) or "none"
                        self.trace.record_tool_result(
                            tool_name,
                            success=False,
                            output=(
                                f"Tool unavailable in this phase; allowed: {allowed}"
                            ),
                        )
                    continue
                if response.kind == "tool_call":
                    self._handle_tool_call(
                        response,
                        intent=active.intent,
                        task_context=active.task_context,
                        step=step,
                        step_limit=step_limit,
                        mutation_workflow=mutation_workflow,
                    )
                    continue

            if response.kind == "clarification":
                if self.trace is not None:
                    self.trace.record_decision(step, step_limit, "clarification")
                result = self._handle_clarification(
                    response,
                    task_context=active.task_context,
                    intent=active.intent,
                    continuing_after_clarification=active.continuing_after_clarification,
                    step=step,
                    task_messages=active_messages,
                )
                if result is not None:
                    active.next_step = step + 1
                    return result
                active.continuing_after_clarification = True
                continue

            if response.kind != "final":
                return self._finish(
                    active,
                    AgentResult(
                        success=False,
                        error=f"Unsupported LLM response kind: {response.kind}",
                        steps=step,
                        messages=active_messages,
                    ),
                )

            if self.trace is not None:
                self.trace.record_final_preview(step, step_limit, response.content)

            nudge = self.response_policy.evaluate_nudge(
                response.content,
                task_context=active.task_context,
                intent=active.intent,
                retries=active.retries,
                repository_inspected=self.conversation.repository_inspected(),
                continuing_after_clarification=active.continuing_after_clarification,
                mutation_workflow=mutation_workflow,
                remaining_test_output=self._last_test_output(),
            )
            if nudge is not None:
                if self.trace is not None:
                    self.trace.record_nudge(nudge.user_message)
                self.conversation.append_nudge(response.content, nudge.user_message)
                continue

            if self._should_fallback_to_pipeline(
                active.intent, active.task_context, active.retries, active=active
            ):
                if self.trace is not None:
                    self.trace.record("pipeline fallback triggered")
                self._run_pipeline(
                    active.intent,
                    active.task_context,
                    active.retries,
                    use_fix_pipeline=mutation_workflow,
                )
                continue

            patch_verification, should_retry = verify_patch_response(
                self.conversation,
                response.content,
                correction_attempts=active.correction_attempts,
                max_correction_attempts=self.max_correction_attempts,
                on_retry=lambda reason: (
                    self.trace.record_nudge(reason) if self.trace is not None else None
                ),
            )
            active.patch_verification = patch_verification
            if should_retry:
                active.correction_attempts += 1
                active.retries.patch_nudges = 0
                continue
            if patch_verification is not None and not patch_verification.passed:
                return self._finish(
                    active,
                    AgentResult(
                        success=False,
                        error=(
                            "Patch verification failed after exhausting correction "
                            f"attempts: {patch_verification.output}"
                        ),
                        steps=step,
                        messages=active_messages,
                        patch_verification=patch_verification,
                        requested_code_change=True,
                    ),
                )

            if self.response_policy.missing_required_patch(
                response.content,
                active.task_context,
                repository_inspected=self.conversation.repository_inspected(),
                mutation_workflow=mutation_workflow,
            ) or self._should_reject_success_without_patch(
                response.content,
                active,
                mutation_workflow=mutation_workflow,
            ):
                if self.trace is not None:
                    self.trace.record_nudge(
                        "missing required unified diff in final answer"
                    )
                return self._finish(
                    active,
                    AgentResult(
                        success=False,
                        error=_MISSING_PATCH_ERROR,
                        steps=step,
                        messages=active_messages,
                        patch_verification=patch_verification,
                        requested_code_change=True,
                    ),
                )

            self.conversation.append("assistant", response.content)
            return self._finish(
                active,
                AgentResult(
                    success=True,
                    response=response.content,
                    steps=step,
                    messages=active_messages,
                    patch_verification=patch_verification,
                    requested_code_change=self._in_mutation_workflow(active)
                    or task_requests_code_change(active.task_context),
                ),
            )

        return self._finish(
            active,
            AgentResult(
                success=False,
                error=self._step_limit_error(step_limit, active),
                steps=step_limit,
                messages=active_messages,
                patch_verification=active.patch_verification,
                requested_code_change=self._in_mutation_workflow(active)
                or task_requests_code_change(active.task_context),
            ),
        )

    def _resolve_intent(self, task_context: str) -> TaskIntent:
        if self.profile is not None:
            return self.profile.objective
        return classify_intent(task_context)

    def _step_limit_for_intent(
        self,
        intent: TaskIntent,
        active: _ActiveTask | None = None,
    ) -> int:
        if active is not None and self._in_mutation_workflow(active):
            if active.intent is TaskIntent.CREATE:
                return max(self.max_steps, settings.create_max_steps)
            return max(self.max_steps, settings.fix_max_steps)
        if intent is TaskIntent.CREATE:
            return max(self.max_steps, settings.create_max_steps)
        if intent is TaskIntent.FIX:
            return max(self.max_steps, settings.fix_max_steps)
        return self.max_steps

    def _should_prefetch_repository(
        self,
        intent: TaskIntent,
        task_context: str,
        continuing_after_clarification: bool,
    ) -> bool:
        if self.routing_mode is RoutingMode.OFF:
            return False
        if continuing_after_clarification:
            return False
        if (
            is_mutation_intent(intent)
            or intent is TaskIntent.PRESENT
            or intent is TaskIntent.RECALL_PLAN
        ):
            return False
        if intent is TaskIntent.CONVERSATION or intent is TaskIntent.META:
            return False
        if not intent_supports_pipeline(intent):
            return False
        if self.conversation.missing_named_file_reads(task_context):
            return True
        if self.routing_mode is RoutingMode.STRICT:
            return True
        return bool(extract_search_targets(task_context))

    def _should_fallback_to_pipeline(
        self,
        intent: TaskIntent,
        task_context: str,
        retries: RetryBudget,
        *,
        active: _ActiveTask,
    ) -> bool:
        if self.routing_mode is RoutingMode.OFF:
            return False
        if not intent_supports_pipeline(intent):
            return False
        mutation_workflow = self._in_mutation_workflow(active)
        if is_mutation_intent(intent) or mutation_workflow:
            if not self.conversation.tool_was_used("run_tests"):
                return False
            if self.conversation.read_file_paths():
                return False
            if retries.pipeline_fallbacks >= retries.max_pipeline:
                return False
            return True
        if self.conversation.missing_named_file_reads(task_context):
            if retries.pipeline_fallbacks >= retries.max_pipeline:
                return False
            return True
        if self.conversation.repository_inspected():
            return False
        if retries.pipeline_fallbacks >= retries.max_pipeline:
            return False
        return True

    def _run_pipeline(
        self,
        intent: TaskIntent,
        task_context: str,
        retries: RetryBudget,
        *,
        test_output: str | None = None,
        use_fix_pipeline: bool = False,
    ) -> None:
        self._notify_activity("Running repository pipeline...")
        execute = self._execute_pipeline_tool
        if is_mutation_intent(intent) or use_fix_pipeline:
            if test_output is None:
                last_tests = self.conversation.last_tool_result("run_tests")
                test_output = last_tests.output if last_tests is not None else None
            missing_modules = run_fix_pipeline(
                task_context,
                execute,
                repository_path=self.registry.repository_path,
                test_output=test_output,
            )
            if missing_modules:
                nudge = nudge_for_missing_local_modules(missing_modules)
            elif intent is TaskIntent.CREATE:
                nudge = nudge_after_create_pipeline()
            else:
                nudge = nudge_after_fix_pipeline()
        else:
            run_repository_pipeline(
                intent,
                task_context,
                execute,
                repository_path=self.registry.repository_path,
            )
            nudge = nudge_after_pipeline_fallback(intent)
        retries.pipeline_fallbacks += 1
        self.conversation.append("user", nudge.user_message)

    def _bootstrap_code_change_workflow(
        self,
        task_context: str,
        retries: RetryBudget,
    ) -> None:
        """Run tests and load repair context before the first model decision."""

        if self.conversation.tool_was_used("run_tests"):
            return

        self._notify_activity("Running tests before code-change work...")
        result = self.conversation.execute_tool(
            "run_tests",
            {},
            require_confirmation=False,
        )
        if self.trace is not None:
            self.trace.record_tool_result(
                "run_tests",
                success=result.success,
                output=result.output or result.error or "",
                metadata=result.metadata,
            )

        test_output = result.output or result.error or ""
        if not test_output.strip():
            return

        missing_modules = run_fix_pipeline(
            task_context,
            self._execute_pipeline_tool,
            repository_path=self.registry.repository_path,
            test_output=test_output,
        )
        if missing_modules:
            nudge = nudge_for_missing_local_modules(missing_modules)
        elif (
            active.intent is TaskIntent.CREATE
            if (active := self._active_task)
            else False
        ):
            nudge = nudge_after_create_pipeline()
        else:
            nudge = nudge_after_fix_pipeline()
        retries.pipeline_fallbacks += 1
        self.conversation.append("user", nudge.user_message)

    def _handle_tool_call(
        self,
        response: LLMResponse,
        *,
        intent: TaskIntent,
        task_context: str,
        step: int,
        step_limit: int,
        mutation_workflow: bool,
    ) -> None:
        """Execute a tool call, optionally redirecting redundant searches."""

        tool_name = response.tool_name or ""
        self._notify_activity(f"Running tool `{tool_name}`...")
        if self._should_redirect_search_to_read(
            tool_name, mutation_workflow=mutation_workflow
        ):
            paths = self.conversation.unread_search_code_paths()
            nudge = nudge_for_read_file_instead_of_search(
                paths,
                sources_already_read=bool(self.conversation.read_file_paths()),
            )
            if self.trace is not None:
                self.trace.record_nudge("redirect repeated search_code to read_file")
            self.conversation.append_nudge(
                Conversation.format_tool_call(tool_name, response.arguments),
                nudge.user_message,
            )
            return

        result = self.conversation.execute_tool(tool_name, response.arguments)
        if self.trace is not None:
            self.trace.record_tool_result(
                tool_name,
                success=result.success,
                output=result.output or result.error or "",
                metadata=result.metadata,
            )
        if tool_name == "run_tests" and self._should_run_fix_pipeline(result.output):
            self._run_fix_pipeline(task_context, test_output=result.output)

    def _should_run_fix_pipeline(self, test_output: str | None) -> bool:
        if not test_output:
            return False
        return output_reports_failures(test_output)

    def _last_test_output(self) -> str | None:
        last_tests = self.conversation.last_tool_result("run_tests")
        if last_tests is None:
            return None
        return last_tests.output or last_tests.error

    def _tests_still_failing(self) -> bool:
        output = self._last_test_output()
        return output_reports_failures(output or "")

    def _should_reject_success_without_patch(
        self,
        content: str,
        active: _ActiveTask,
        *,
        mutation_workflow: bool,
    ) -> bool:
        if extract_patch(content) is not None:
            return False
        if not self._tests_still_failing():
            return False
        if mutation_workflow or task_requests_code_change(active.task_context):
            return True
        return is_mutation_intent(active.intent)

    def _run_fix_pipeline(self, task_context: str, *, test_output: str | None) -> None:
        missing_modules = run_fix_pipeline(
            task_context,
            self._execute_pipeline_tool,
            repository_path=self.registry.repository_path,
            test_output=test_output,
        )
        if missing_modules:
            nudge = nudge_for_missing_local_modules(missing_modules)
        elif (
            self._active_task is not None
            and self._active_task.intent is TaskIntent.CREATE
        ):
            nudge = nudge_after_create_pipeline()
        else:
            nudge = nudge_after_fix_pipeline()
        self.conversation.append("user", nudge.user_message)

    def _execute_pipeline_tool(
        self,
        tool_name: str,
        arguments: dict[str, object],
    ) -> ToolResult:
        """Execute deterministic pipeline work while retaining diagnostic evidence."""

        if self.trace is not None:
            self.trace.record(
                f"pipeline tool {tool_name}",
                kind="pipeline_tool_call",
                data={"tool": tool_name},
            )
        result = self.conversation.execute_tool(tool_name, arguments)
        if self.trace is not None:
            self.trace.record_tool_result(
                tool_name,
                success=result.success,
                output=result.output or result.error or "",
                metadata=result.metadata,
            )
        return result

    def _should_redirect_search_to_read(
        self,
        tool_name: str,
        *,
        mutation_workflow: bool,
    ) -> bool:
        if tool_name != "search_code":
            return False
        if not mutation_workflow and not self.conversation.tool_was_used("run_tests"):
            return False
        if not self.conversation.tool_was_used("run_tests"):
            return False
        search_calls = sum(
            1
            for message in self.conversation.messages
            if message.role == "assistant"
            and message.content.startswith("Called tool=search_code")
        )
        return search_calls >= 1

    def _handle_clarification(
        self,
        response: LLMResponse,
        *,
        task_context: str,
        intent: TaskIntent,
        continuing_after_clarification: bool,
        step: int,
        task_messages: list[ChatMessage],
    ) -> AgentResult | None:
        if continuing_after_clarification:
            nudge = nudge_for_repeated_clarification()
            self.conversation.append_nudge(response.content, nudge.user_message)
            return None

        if should_defer_clarification(
            task_context,
            intent,
            repository_inspected=self.conversation.repository_inspected(),
        ):
            nudge = nudge_for_premature_clarification()
            self.conversation.append_nudge(response.content, nudge.user_message)
            return None

        self._mark_clarification_pending()
        self.conversation.append("assistant", response.content)
        return AgentResult(
            success=True,
            clarification=response.content,
            plan=response.plan,
            steps=step,
            messages=task_messages,
        )
