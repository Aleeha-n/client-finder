"""Web search through DuckDuckGo (free, no API key)."""
import time

from ddgs import DDGS


def web_search(query, max_results=10):
    """Returns [{"title","url","snippet"}]. Never raises: a failed search returns []."""
    try:
        rows = DDGS().text(query, max_results=max_results)
    except Exception as exc:  # noqa: BLE001
        print(f"   search failed for {query!r}: {type(exc).__name__}")
        return []
    return [
        {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
        for r in rows or []
        if r.get("href")
    ]


def search_many(queries, per_query=10, pause=1.5):
    seen, results = set(), []
    for q in queries:
        for r in web_search(q, per_query):
            if r["url"] not in seen:
                seen.add(r["url"])
                results.append(r)
        time.sleep(pause)
    return results
