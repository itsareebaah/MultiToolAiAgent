#!/usr/bin/env python3
"""CLI for the Advanced Multi-Tool AI Agent."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

# Ensure project root is on path when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent.core import MultiToolAgent  # noqa: E402

console = Console()


def run_interactive(agent: MultiToolAgent) -> None:
    console.print(
        "[bold green]Advanced Multi-Tool AI Agent[/]\n"
        "Tools: web search · notes · email · function calling\n"
        "Commands: [dim]/reset[/] clear history · [dim]/quit[/] exit\n"
    )

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]You[/]")
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye.")
            break

        text = user_input.strip()
        if not text:
            continue
        if text.lower() in ("/quit", "/exit", "quit", "exit"):
            console.print("Goodbye.")
            break
        if text.lower() == "/reset":
            agent.reset()
            console.print("[dim]Conversation reset.[/]")
            continue

        try:
            reply = agent.chat(text)
            console.print("\n[bold magenta]Agent[/]")
            agent.print_response(reply)
        except Exception as exc:
            console.print(f"[red]Error:[/] {exc}")


def main() -> None:
    load_dotenv()
    provider = os.getenv("AI_PROVIDER")

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        try:
            agent = MultiToolAgent(provider=provider, verbose=True)
            reply = agent.chat(query)
            console.print("\n[bold magenta]Agent[/]")
            agent.print_response(reply)
        except ValueError as exc:
            console.print(f"[red]{exc}[/]")
            sys.exit(1)
        return

    try:
        agent = MultiToolAgent(provider=provider, verbose=True)
    except ValueError as exc:
        console.print(f"[red]{exc}[/]")
        sys.exit(1)

    console.print(f"[dim]Provider: {agent.provider_label} · Model: {agent.model}[/]\n")
    run_interactive(agent)


if __name__ == "__main__":
    main()
