"""Tool schemas (OpenAI function format) and dispatch."""

import json
from typing import Any, Callable

from agent.tools import email_tools, notes, web_search

ToolHandler = Callable[..., str]

TOOL_HANDLERS: dict[str, ToolHandler] = {
    "search_web": web_search.search_web,
    "save_note": notes.save_note,
    "list_notes": notes.list_notes,
    "get_note": notes.get_note,
    "delete_note": notes.delete_note,
    "send_email": email_tools.send_email,
}

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search the web for current information, news, facts, or documentation. "
                "Use when the user asks about recent events or information not in your training data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return (1-10). Default 5.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Save a note locally with a title and content for later retrieval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short title for the note."},
                    "content": {"type": "string", "description": "Full note content."},
                },
                "required": ["title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_notes",
            "description": "List all saved notes with titles and previews.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_note",
            "description": "Retrieve the full content of a saved note by title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the note to retrieve."},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_note",
            "description": "Delete a saved note by title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the note to delete."},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": (
                "Send an email to a recipient. Requires SMTP credentials in .env. "
                "Confirm recipient and content with the user before sending."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address."},
                    "subject": {"type": "string", "description": "Email subject line."},
                    "body": {"type": "string", "description": "Plain-text email body."},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
]


def execute_tool(name: str, arguments: str | dict[str, Any]) -> str:
    if name not in TOOL_HANDLERS:
        return f"Unknown tool: {name}"

    if isinstance(arguments, str):
        try:
            args = json.loads(arguments) if arguments.strip() else {}
        except json.JSONDecodeError:
            return f"Invalid tool arguments JSON: {arguments}"
    else:
        args = arguments

    if not isinstance(args, dict):
        return "Tool arguments must be a JSON object."

    try:
        return TOOL_HANDLERS[name](**args)
    except TypeError as exc:
        return f"Tool argument error for {name}: {exc}"
    except Exception as exc:
        return f"Tool {name} failed: {exc}"
