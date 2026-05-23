"""Local note storage (JSON file)."""

import json
from datetime import datetime, timezone
from pathlib import Path

NOTES_PATH = Path(__file__).resolve().parents[2] / "data" / "notes.json"


def _load_notes() -> dict:
    if not NOTES_PATH.exists():
        return {}
    try:
        with NOTES_PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_notes(notes: dict) -> None:
    NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with NOTES_PATH.open("w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)


def save_note(title: str, content: str) -> str:
    title = title.strip()
    if not title:
        return "Error: note title cannot be empty."

    notes = _load_notes()
    now = datetime.now(timezone.utc).isoformat()
    notes[title.lower()] = {
        "title": title,
        "content": content,
        "updated_at": now,
    }
    _save_notes(notes)
    return f"Note saved: '{title}' ({len(content)} characters)."


def list_notes() -> str:
    notes = _load_notes()
    if not notes:
        return "No notes saved yet."

    lines = ["Saved notes:\n"]
    for key in sorted(notes.keys()):
        entry = notes[key]
        updated = entry.get("updated_at", "unknown")
        preview = entry.get("content", "")[:80].replace("\n", " ")
        lines.append(f"- {entry.get('title', key)} (updated: {updated})")
        if preview:
            lines.append(f"  Preview: {preview}...")
    return "\n".join(lines)


def get_note(title: str) -> str:
    title = title.strip()
    if not title:
        return "Error: note title cannot be empty."

    notes = _load_notes()
    entry = notes.get(title.lower())
    if not entry:
        return f"No note found with title: {title}"

    return (
        f"Title: {entry.get('title', title)}\n"
        f"Updated: {entry.get('updated_at', 'unknown')}\n\n"
        f"{entry.get('content', '')}"
    )


def delete_note(title: str) -> str:
    title = title.strip()
    if not title:
        return "Error: note title cannot be empty."

    notes = _load_notes()
    key = title.lower()
    if key not in notes:
        return f"No note found with title: {title}"

    removed = notes.pop(key)["title"]
    _save_notes(notes)
    return f"Deleted note: '{removed}'."
