"""Web search via DDGS metasearch (no API key required)."""

from typing import Any

BACKENDS = ("duckduckgo", "bing", "brave")


def _ddgs_client():
    """Prefer `ddgs`; fall back to legacy `duckduckgo_search` package."""
    try:
        from ddgs import DDGS

        return DDGS, True
    except ImportError:
        try:
            from duckduckgo_search import DDGS

            return DDGS, False
        except ImportError as exc:
            raise ImportError(
                "Web search requires the 'ddgs' package. Install dependencies:\n"
                "  pip install -r requirements.txt\n"
                "Or activate the project venv:\n"
                "  .venv\\Scripts\\activate"
            ) from exc


def _run_search(
    ddgs: Any, query: str, max_results: int, *, supports_backend: bool
) -> list[dict[str, Any]]:
    if supports_backend:
        last_error = ""
        for backend in BACKENDS:
            try:
                results = list(
                    ddgs.text(query, max_results=max_results, backend=backend)
                )
            except TypeError:
                results = list(ddgs.text(query, max_results=max_results))
                return results
            except Exception as exc:
                last_error = str(exc)
                continue
            if results:
                return results
        if last_error:
            raise RuntimeError(last_error)
        return []
    return list(ddgs.text(query, max_results=max_results))


def search_web(query: str, max_results: int = 5) -> str:
    if not query.strip():
        return "Error: search query cannot be empty."

    max_results = max(1, min(max_results, 10))

    try:
        DDGS, supports_backend = _ddgs_client()
        with DDGS() as ddgs:
            results = _run_search(
                ddgs, query, max_results, supports_backend=supports_backend
            )
    except ImportError as exc:
        return str(exc)
    except Exception as exc:
        return f"Web search failed: {exc}"

    if not results:
        return f"No results found for: {query}"

    lines = [f"Web search results for: {query}\n"]
    for i, item in enumerate(results, 1):
        title = item.get("title", "No title")
        url = item.get("href", item.get("link", ""))
        snippet = item.get("body", item.get("snippet", ""))
        lines.append(f"{i}. {title}")
        if url:
            lines.append(f"   URL: {url}")
        if snippet:
            lines.append(f"   {snippet[:300]}")
        lines.append("")

    return "\n".join(lines).strip()
