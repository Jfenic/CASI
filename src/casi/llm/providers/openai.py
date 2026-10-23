"""OpenAI-compatible LLM client and provider implementation."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from casi.config import settings
from casi.exceptions import LLMError
from casi.llm.actions import ProposeFileAction, action_validation_error
from casi.llm.base import ChatMessage, LLMResponse, ToolDefinition
from casi.llm.json_schema import normalize_json_schema_type
from casi.llm.parser import parse_response, tool_call_allowed


class _EmptyModelResponse(LLMError):
    """A valid envelope with no usable model decision; safe to request again."""


def _strip_markdown_json(text: str) -> str:
    content = text.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if (
            len(lines) >= 2
            and lines[0].startswith("```")
            and lines[-1].strip() == "```"
        ):
            content = "\n".join(lines[1:-1]).strip()
    return content


class OpenAIClient:
    """Call OpenAI-compatible endpoints using project's LLM contract."""

    supports_evaluation: bool = True
    provider_name: str = "openai"

    def __init__(
        self,
        api_key: str = settings.openai_api_key,
        base_url: str = settings.openai_base_url,
        model: str = settings.openai_model,
        timeout_seconds: float = settings.openai_timeout_seconds,
        *,
        role_instructions: str = "",
        max_empty_retries: int = 2,
    ) -> None:
        if max_empty_retries < 0:
            raise ValueError("max_empty_retries must be non-negative")
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.role_instructions = role_instructions
        self.max_empty_retries = max_empty_retries

    @property
    def model_name(self) -> str:
        return self.model

    def with_role_instructions(self, role_instructions: str) -> OpenAIClient:
        """Return a new OpenAIClient configured with specific role instructions."""
        return OpenAIClient(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            timeout_seconds=self.timeout_seconds,
            role_instructions=role_instructions,
            max_empty_retries=self.max_empty_retries,
        )

    @staticmethod
    def _bound_message_content(content: str) -> str:
        if len(content) <= settings.max_message_chars:
            return content
        from casi.agent.test_failures import truncate_by_strategy

        return truncate_by_strategy(
            content,
            max_chars=settings.max_message_chars,
            strategy="tail",
        )

    def complete(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition],
    ) -> LLMResponse:
        """Request one model decision from OpenAI."""
        return self._complete(messages, tools)

    def complete_tool_call(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition],
    ) -> LLMResponse:
        """Constrain a recovery decision to require a tool call."""
        if not tools:
            raise ValueError("A required tool call needs at least one tool")
        return self._complete(messages, tools, require_tool_call=True)

    def complete_action(
        self,
        messages: Sequence[ChatMessage],
        action: type[ProposeFileAction] = ProposeFileAction,
    ) -> LLMResponse:
        """Request one constrained mutation action via propose_file tool_choice."""
        propose_tool = {
            "type": "function",
            "function": {
                "name": action.tool_name,
                "description": (
                    "Propose complete file content for a new or modified file."
                ),
                "parameters": action.json_schema(),
            },
        }

        formatted_messages = self._format_messages(messages)
        system_content = (
            f"You are CASI running on model {self.model}.\n"
            "The repository has been inspected. You must create or replace one "
            "file now using the propose_file function with valid path and content."
        )
        if self.role_instructions.strip():
            system_content += f"\nSpecialist role:\n{self.role_instructions.strip()}\n"

        if formatted_messages and formatted_messages[0].get("role") == "system":
            formatted_messages[0]["content"] = system_content
        else:
            formatted_messages.insert(0, {"role": "system", "content": system_content})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "tools": [propose_tool],
            "tool_choice": {
                "type": "function",
                "function": {"name": action.tool_name},
            },
        }

        prompt_tokens: int | None = None
        completion_tokens: int | None = None

        for attempt in range(self.max_empty_retries + 1):
            response_payload = self._post(payload)
            usage = response_payload.get("usage", {})
            if isinstance(usage, dict):
                p_cnt = _optional_int(usage.get("prompt_tokens"))
                c_cnt = _optional_int(usage.get("completion_tokens"))
                if p_cnt is not None:
                    prompt_tokens = (prompt_tokens or 0) + p_cnt
                if c_cnt is not None:
                    completion_tokens = (completion_tokens or 0) + c_cnt

            choices = response_payload.get("choices", [])
            if not isinstance(choices, list) or not choices:
                raise LLMError("OpenAI response contains no choices")

            choice = choices[0]
            if not isinstance(choice, dict):
                raise LLMError("OpenAI choice is not an object")

            msg = choice.get("message", {})
            if not isinstance(msg, dict):
                raise LLMError("OpenAI choice does not contain a message")

            tool_calls = msg.get("tool_calls", [])
            if tool_calls and isinstance(tool_calls, list):
                raw_call = tool_calls[0]
                if isinstance(raw_call, dict):
                    fn = raw_call.get("function", {})
                    if isinstance(fn, dict):
                        args_raw = fn.get("arguments", "")
                        call_id = raw_call.get("id")
                        if isinstance(args_raw, str):
                            try:
                                parsed_action = action.from_json(args_raw)
                                parsed_response = LLMResponse.tool_call(
                                    action.tool_name,
                                    parsed_action.as_tool_arguments(),
                                    call_id=call_id,
                                )
                                break
                            except ValueError as exc:
                                if attempt == self.max_empty_retries:
                                    raise LLMError(
                                        "OpenAI action response failed "
                                        f"validation: {exc}"
                                    ) from exc
                                payload["messages"].append(
                                    {
                                        "role": "user",
                                        "content": action_validation_error(str(exc)),
                                    }
                                )
                                continue

            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                clean_content = _strip_markdown_json(content)
                parsed_action_cand = None
                try:
                    parsed_action_cand = action.from_json(clean_content)
                except ValueError:
                    try:
                        envelope = json.loads(clean_content, strict=False)
                        if isinstance(envelope, dict):
                            args_cand = envelope.get("arguments", envelope)
                            if isinstance(args_cand, dict):
                                path_val = args_cand.get("path")
                                content_val = args_cand.get("content")
                                if (
                                    isinstance(path_val, str)
                                    and path_val.strip()
                                    and isinstance(content_val, str)
                                ):
                                    parsed_action_cand = action(
                                        path=path_val.strip(),
                                        content=content_val,
                                    )
                    except Exception:
                        pass

                if parsed_action_cand is not None:
                    parsed_response = LLMResponse.tool_call(
                        action.tool_name,
                        parsed_action_cand.as_tool_arguments(),
                    )
                    break
                else:
                    if attempt == self.max_empty_retries:
                        raise LLMError(
                            "OpenAI action response failed validation: "
                            "invalid action payload"
                        )
                    payload["messages"].append(
                        {
                            "role": "user",
                            "content": action_validation_error(
                                "invalid action payload"
                            ),
                        }
                    )
                    continue

            if attempt == self.max_empty_retries:
                raise _EmptyModelResponse(
                    "OpenAI action response produced no valid decision"
                )
            payload["messages"].append(
                {
                    "role": "user",
                    "content": action_validation_error("empty or missing tool call"),
                }
            )

        return LLMResponse(
            kind=parsed_response.kind,
            content=parsed_response.content,
            tool_name=parsed_response.tool_name,
            arguments=parsed_response.arguments,
            plan=list(parsed_response.plan),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            call_id=parsed_response.call_id,
        )

    def _complete(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition],
        *,
        require_tool_call: bool = False,
    ) -> LLMResponse:
        formatted_messages = self._format_messages(messages)
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
        }

        if tools:
            payload["tools"] = [self._tool_schema(tool) for tool in tools]
            if require_tool_call:
                payload["tool_choice"] = "required"

        prompt_tokens: int | None = None
        completion_tokens: int | None = None

        for attempt in range(self.max_empty_retries + 1):
            response_payload = self._post(payload)
            usage = response_payload.get("usage", {})
            if isinstance(usage, dict):
                p_cnt = _optional_int(usage.get("prompt_tokens"))
                c_cnt = _optional_int(usage.get("completion_tokens"))
                if p_cnt is not None:
                    prompt_tokens = (prompt_tokens or 0) + p_cnt
                if c_cnt is not None:
                    completion_tokens = (completion_tokens or 0) + c_cnt

            choices = response_payload.get("choices", [])
            if not isinstance(choices, list) or not choices:
                raise LLMError("OpenAI response contains no choices")

            choice = choices[0]
            if not isinstance(choice, dict):
                raise LLMError("OpenAI choice is not an object")

            msg = choice.get("message", {})
            if not isinstance(msg, dict):
                raise LLMError("OpenAI choice does not contain a message")

            try:
                parsed = self._parse_message(msg, tools)
                break
            except _EmptyModelResponse:
                if attempt == self.max_empty_retries:
                    raise
                payload["messages"].append(
                    {
                        "role": "user",
                        "content": (
                            "Empty decision. Provide a tool call or a final answer."
                        ),
                    }
                )

        return LLMResponse(
            kind=parsed.kind,
            content=parsed.content,
            tool_name=parsed.tool_name,
            arguments=parsed.arguments,
            plan=list(parsed.plan),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            call_id=parsed.call_id,
        )

    def _format_messages(
        self,
        messages: Sequence[ChatMessage],
    ) -> list[dict[str, Any]]:
        formatted: list[dict[str, Any]] = []

        has_system = any(m.role == "system" for m in messages)
        if not has_system:
            system_content = (
                f"You are CASI, an advanced repository code agent on {self.model}.\n"
                "Rules:\n"
                "- For questions about the repository, its state, files, code or "
                "tests, you MUST use repository tools before answering.\n"
                "- For code changes or bug fixes, inspect the relevant files and "
                "tests first, then propose complete replacement content via "
                "propose_file.\n"
                "- When the user asks for the plan, next steps, or session progress, "
                "call get_session_plan.\n"
                "- Never claim you cannot access the repository when tools are "
                "available.\n"
                "- Respond in Spanish when the user writes in Spanish."
            )
            if self.role_instructions.strip():
                system_content += (
                    f"\n\nSpecialist role:\n{self.role_instructions.strip()}"
                )
            formatted.append({"role": "system", "content": system_content})

        for i, msg in enumerate(messages):
            bounded_content = self._bound_message_content(msg.content)
            if msg.role == "system":
                sys_text = bounded_content
                role_text = self.role_instructions.strip()
                if role_text and role_text not in sys_text:
                    sys_text += f"\n\nSpecialist role:\n{role_text}"
                formatted.append({"role": "system", "content": sys_text})
            elif msg.role == "assistant":
                if msg.tool_call is not None:
                    call_id = msg.tool_call.call_id or f"call_{i}"
                    formatted.append(
                        {
                            "role": "assistant",
                            "content": bounded_content or None,
                            "tool_calls": [
                                {
                                    "id": call_id,
                                    "type": "function",
                                    "function": {
                                        "name": msg.tool_call.name,
                                        "arguments": json.dumps(
                                            msg.tool_call.arguments,
                                            ensure_ascii=False,
                                        ),
                                    },
                                }
                            ],
                        }
                    )
                else:
                    formatted.append({"role": "assistant", "content": bounded_content})
            elif msg.role == "tool":
                call_id = None
                if formatted and formatted[-1].get("role") == "assistant":
                    t_calls = formatted[-1].get("tool_calls")
                    if t_calls and isinstance(t_calls, list) and len(t_calls) > 0:
                        call_id = t_calls[0].get("id")

                if call_id is not None:
                    formatted.append(
                        {
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": bounded_content,
                        }
                    )
                else:
                    formatted.append(
                        {
                            "role": "user",
                            "content": f"[Tool Result]\n{bounded_content}",
                        }
                    )
            else:
                formatted.append({"role": "user", "content": bounded_content})

        return formatted

    def _parse_message(
        self,
        msg: dict[str, Any],
        tools: Sequence[ToolDefinition],
    ) -> LLMResponse:
        tool_calls = msg.get("tool_calls", [])
        if tool_calls and isinstance(tool_calls, list):
            tc = tool_calls[0]
            if not isinstance(tc, dict):
                raise LLMError("OpenAI tool call is not an object")
            fn = tc.get("function", {})
            if not isinstance(fn, dict):
                raise LLMError("OpenAI tool call missing function object")
            name = fn.get("name")
            if not isinstance(name, str) or not name.strip():
                raise LLMError("OpenAI tool call missing function name")

            call_id = tc.get("id")
            if isinstance(call_id, str):
                call_id = call_id.strip() or None
            else:
                call_id = None

            args_raw = fn.get("arguments", "{}")
            if isinstance(args_raw, str):
                args_raw = args_raw.strip()
                if not args_raw:
                    args = {}
                else:
                    try:
                        args = json.loads(args_raw, strict=False)
                    except json.JSONDecodeError as exc:
                        raise LLMError(
                            f"OpenAI returned invalid JSON in tool arguments: {exc}"
                        ) from exc
            elif isinstance(args_raw, dict):
                args = args_raw
            else:
                args = {}

            if not isinstance(args, dict):
                raise LLMError("OpenAI tool arguments must be an object")

            if not tool_call_allowed(name, args, tools):
                raise LLMError(f"Tool call '{name}' is not allowed in current context")

            return LLMResponse.tool_call(name, args, call_id=call_id)

        content = msg.get("content")
        if not isinstance(content, str) or not content.strip():
            raise _EmptyModelResponse("OpenAI returned empty message content")

        content = content.strip()
        try:
            parsed = parse_response(content)
            if self._tool_call_is_permitted(parsed, tools):
                return parsed
        except ValueError:
            pass

        return LLMResponse.final(content)

    @staticmethod
    def _tool_call_is_permitted(
        response: LLMResponse,
        tools: Sequence[ToolDefinition],
    ) -> bool:
        if response.kind != "tool_call" or response.tool_name is None:
            return True
        if not tools:
            return True
        return tool_call_allowed(response.tool_name, response.arguments, tools)

    @staticmethod
    def _tool_schema(tool: ToolDefinition) -> dict[str, Any]:
        properties: dict[str, Any] = {}
        required: list[str] = []

        for name, details in tool.arguments.items():
            if isinstance(details, dict):
                prop_type = normalize_json_schema_type(
                    str(details.get("type", "string"))
                )
                prop: dict[str, Any] = {"type": prop_type}
                if "description" in details:
                    prop["description"] = str(details["description"])
                properties[name] = prop
                if details.get("required"):
                    required.append(name)
            else:
                properties[name] = {"type": "string"}

        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body_bytes = json.dumps(payload).encode("utf-8")
        url = f"{self.base_url}/chat/completions"
        request = Request(url, data=body_bytes, headers=headers, method="POST")

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            error_message = f"HTTP {exc.code}"
            try:
                err_json = json.loads(err_body)
                if isinstance(err_json, dict) and "error" in err_json:
                    err_info = err_json["error"]
                    if isinstance(err_info, dict) and "message" in err_info:
                        error_message = f"{error_message}: {err_info['message']}"
                    else:
                        error_message = f"{error_message}: {err_info}"
            except Exception:
                if err_body.strip():
                    error_message = f"{error_message}: {err_body[:200]}"

            if exc.code == 401:
                raise LLMError(
                    "OpenAI authentication failed (401): check your "
                    f"OPENAI_API_KEY. {error_message}"
                ) from exc
            if exc.code == 429:
                raise LLMError(
                    f"OpenAI rate limit or quota exceeded (429): {error_message}"
                ) from exc
            raise LLMError(f"OpenAI request failed: {error_message}") from exc
        except TimeoutError as exc:
            raise LLMError(
                f"OpenAI request timed out after {self.timeout_seconds}s"
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise LLMError(
                    f"OpenAI request timed out after {self.timeout_seconds}s"
                ) from exc
            raise LLMError(
                f"Could not connect to OpenAI at {self.base_url}: {exc.reason}"
            ) from exc
        except OSError as exc:
            raise LLMError(f"OpenAI network error: {exc}") from exc

        try:
            data: Any = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise LLMError("OpenAI returned invalid JSON") from exc

        if not isinstance(data, dict):
            raise LLMError("OpenAI response must be a JSON object")
        if "error" in data:
            raise LLMError(f"OpenAI returned an error: {data['error']}")

        return data


class OpenAIProvider(OpenAIClient):
    """ModelProvider alias for OpenAIClient."""

    pass


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None
