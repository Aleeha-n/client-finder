"""Agent 1 - Planner: turns "niche + city" into several different search queries."""
from llm import chat_json

SYSTEM = (
    "You plan web searches to find local businesses. Return JSON: "
    '{"queries": ["..."]} with 5 different search queries that would surface individual '
    "businesses of the given type in the given city (vary wording, nearby areas, and "
    "words like clinic/office/near me/contact/appointment). No more than 6 queries."
)


def plan_queries(niche, city):
    fallback = [
        f"{niche} in {city}",
        f"best {niche} {city}",
        f"{niche} {city} contact",
        f"{niche} {city} book appointment",
    ]
    try:
        data = chat_json(SYSTEM, f"Business type: {niche}\nCity: {city}", max_tokens=400)
        queries = [q.strip() for q in data.get("queries", []) if isinstance(q, str) and q.strip()]
    except RuntimeError:
        queries = []
    return (queries or fallback)[:6]
