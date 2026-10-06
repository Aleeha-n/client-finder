"""Agent 2 - Finder: reads search results and extracts the individual businesses in them."""
import re
from urllib.parse import urlparse

from llm import chat_json

# Sites that are directories / social / maps, never a business's own website
NOT_OWN_SITE = (
    "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com", "youtube.com",
    "tiktok.com", "pinterest.com", "google.", "yelp.", "tripadvisor.", "wikipedia.org",
    "yellowpages", "justdial", "foursquare", "mapquest", "bing.com", "reddit.com",
    "medium.com", "quora.com", "doctoralia", "marham.pk", "oladoc.com", "practo.com",
    "healthgrades", "zocdoc", "clutch.co", "indeed.com", "glassdoor",
)

SYSTEM = (
    "You extract real local businesses from web search results. Return JSON: "
    '{"businesses": [{"name": str, "website": str or null}]}. Rules: '
    "1) Only businesses of the requested type located in or near the requested city. "
    "2) 'website' is only allowed if one of the result URLs is that business's OWN domain "
    "(not a directory, social network, map, news or listing page); otherwise null. "
    "3) Result pages that are lists or articles are not businesses themselves, but DO extract "
    "the individual businesses named in their titles/snippets. "
    "4) Never invent names or URLs."
)


def host(url):
    h = urlparse(url if "//" in url else "//" + url).netloc.lower()
    return h[4:] if h.startswith("www.") else h


def is_own_site(url):
    h = host(url)
    return bool(h) and not any(bad in h for bad in NOT_OWN_SITE)


def extract_businesses(results, niche, city, batch=25):
    seen_hosts = {host(r["url"]) for r in results}
    found = []
    for i in range(0, len(results), batch):
        chunk = results[i : i + batch]
        listing = "\n".join(
            f"{n}. {r['title']} | {r['url']} | {r['snippet'][:200]}" for n, r in enumerate(chunk, 1)
        )
        try:
            data = chat_json(
                SYSTEM, f"Business type: {niche}\nCity: {city}\n\nSearch results:\n{listing}", 1500
            )
        except RuntimeError as exc:
            print(f"   extraction batch failed: {exc}")
            continue
        for b in data.get("businesses", []):
            if not isinstance(b, dict):
                continue
            name = str(b.get("name") or "").strip()
            site = str(b.get("website") or "").strip()
            if not name:
                continue
            # guard against hallucinated sites: must be a real result URL, and not a directory
            if site and not (host(site) in seen_hosts and is_own_site(site)):
                site = ""
            found.append({"name": name, "website": site})

    # de-duplicate by plain name (keep the entry that has a website), then by website host
    by_name = {}
    for b in found:
        key = re.sub(r"[^a-z0-9]", "", b["name"].lower())
        if key and (key not in by_name or (b["website"] and not by_name[key]["website"])):
            by_name[key] = b
    unique, hosts = [], set()
    for b in by_name.values():
        if b["website"]:
            if host(b["website"]) in hosts:
                continue
            hosts.add(host(b["website"]))
        unique.append(b)
    return unique
