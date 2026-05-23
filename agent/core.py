"""Multi-tool agent with OpenAI-compatible function calling."""

import os
from dataclasses import dataclass, field
from typing import Any

import httpx
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from agent.providers import (
    ProviderConfig,
    get_provider,
    mask_api_key,
    resolve_api_key,
    resolve_base_url,
    resolve_model,
    validate_api_key,
)
from agent.tools.registry import TOOL_DEFINITIONS, execute_tool

SYSTEM_PROMPT = """You are an advanced multi-tool AI assistant with these capabilities:
- **Web search**: Look up current information on the internet.
- **Notes**: Save, list, retrieve, and delete local notes.
- **Email**: Send emails via SMTP (only when the user clearly requests it).

Guidelines:
- Use tools when they help answer the user accurately (especially for recent facts, saved notes, or email).
- For email: confirm recipient, subject, and body intent before calling send_email.
- After tool results, synthesize a clear, helpful reply.
- If a tool fails, explain what went wrong and suggest fixes (e.g. missing API key or SMTP config).
"""

MAX_TOOL_ROUNDS = 10


@dataclass
class ToolEvent:
    name: str
    arguments: str
    result: str


@dataclass
class ChatResult:
    reply: str
    tool_events: list[ToolEvent] = field(default_factory=list)


class MultiToolAgent:
    def __init__(
        self,
        *,
        provider: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        verbose: bool = True,
    ):
        self.provider_cfg: ProviderConfig = get_provider(provider)
        self.api_key = (api_key or resolve_api_key(self.provider_cfg)).strip()
        self.base_url = (base_url or resolve_base_url(self.provider_cfg)).strip()
        self.model = resolve_model(self.provider_cfg, model)
        self.verbose = verbose
        self.console = Console()

        if not self.api_key and self.provider_cfg.id != "ollama":
            raise ValueError(
                f"API key missing for {self.provider_cfg.label}. "
                f"Set {self.provider_cfg.api_key_env} in your .env file."
            )

        validate_api_key(self.provider_cfg, self.api_key)

        client_kwargs: dict[str, Any] = {
            "api_key": self.api_key or "ollama",
            "base_url": self.base_url,
            "timeout": httpx.Timeout(self.provider_cfg.timeout_seconds),
        }
        self.client = OpenAI(**client_kwargs)
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

    @property
    def provider_label(self) -> str:
        return self.provider_cfg.label

    def _log_tool(self, name: str, arguments: str, result: str) -> None:
        if not self.verbose:
            return
        self.console.print(
            Panel(
                f"[bold cyan]Tool:[/] {name}\n"
                f"[dim]Args:[/] {arguments}\n"
                f"[dim]Result:[/] {result[:500]}{'...' if len(result) > 500 else ''}",
                title="Function call",
                border_style="blue",
            )
        )

    def chat_detailed(self, user_input: str) -> ChatResult:
        self.messages.append({"role": "user", "content": user_input})
        tool_events: list[ToolEvent] = []

        for _ in range(MAX_TOOL_ROUNDS):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )
            message = response.choices[0].message
            assistant_payload: dict[str, Any] = {
                "role": "assistant",
                "content": message.content,
            }
            if message.tool_calls:
                assistant_payload["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]
            self.messages.append(assistant_payload)

            if not message.tool_calls:
                return ChatResult(reply=message.content or "", tool_events=tool_events)

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = tool_call.function.arguments or "{}"
                result = execute_tool(name, args)
                self._log_tool(name, args, result)
                tool_events.append(ToolEvent(name=name, arguments=args, result=result))
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

        return ChatResult(
            reply="Stopped: too many tool call rounds. Try a simpler request.",
            tool_events=tool_events,
        )

    def chat(self, user_input: str) -> str:
        return self.chat_detailed(user_input).reply

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def print_response(self, text: str) -> None:
        self.console.print(Markdown(text))
