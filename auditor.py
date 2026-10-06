import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import httpx

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

CHATBOT_WORDS = [
    "tawk.to", "tidio", "livechat", "crisp.chat", "intercom", "drift.com",
    "zendesk", "hubspot", "botpress", "manychat", "smartsupp", "freshchat",
    "olark", "jivochat", "chatbot", "live chat", "livechat",
]
BOOKING_WORDS = [
    "book an appointment", "book appointment", "book now", "book online",
    "online booking", "calendly", "schedule an appointment", "make an appointment",
    "request an appointment", "reservation", "appointment form",
]
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(\+92[\s-]?\d[\d\s-]{8,12}\d|\b03\d{2}[\s-]?\d{7}\b)")
YEAR_RE = re.compile(r"(?:©|&copy;|copyright)[^0-9]{0,40}((?:19|20)\d{2})", re.I)
BAD_EMAIL_END = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js")


def analyze_html(html, final_url):
    low = html.lower()
    data = {
        "reachable": True,
        "https": final_url.lower().startswith("https://"),
        "mobile_friendly": 'name="viewport"' in low or "name='viewport'" in low,
        "chatbot": any(w in low for w in CHATBOT_WORDS),
        "online_booking": any(w in low for w in BOOKING_WORDS),
        "whatsapp": any(w in low for w in ("wa.me", "api.whatsapp.com", "whatsapp")),
    }

    years = [int(y) for y in YEAR_RE.findall(html)]
    data["copyright_year"] = max(years) if years else None

    email = ""
    candidates = re.findall(r"mailto:([^\"'?>\s]+)", html, re.I) + EMAIL_RE.findall(html)
    for m in candidates:
        m = m.strip()
        if EMAIL_RE.fullmatch(m) and not m.lower().endswith(BAD_EMAIL_END):
            email = m
            break
    data["email"] = email

    phone = ""
    tel = re.search(r"tel:([+\d][\d\s\-()]{7,20})", html, re.I)
    if tel:
        phone = re.sub(r"[\s\-()]", "", tel.group(1))
    else:
        m = PHONE_RE.search(html)
        if m:
            phone = re.sub(r"[\s\-]", "", m.group(1))
    data["phone"] = phone
    return data


def audit_site(url):
    if not url:
        return {"has_website": False}
    if not url.startswith("http"):
        url = "https://" + url

    last_status = None
    for verify in (True, False):  # dusri baar SSL check band karke try
        for attempt in range(2):
            try:
                r = httpx.get(
                    url,
                    headers=BROWSER_HEADERS,
                    timeout=20,
                    follow_redirects=True,
                    verify=verify,
                )
            except httpx.HTTPError:
                time.sleep(1)
                continue
            if r.status_code < 400:
                data = analyze_html(r.text, str(r.url))
                data["has_website"] = True
                return data
            last_status = r.status_code
            break

    # Site ne jawab diya lekin andar jane nahi diya (bot block)
    if last_status in (401, 403, 429):
        return {"has_website": True, "reachable": True, "blocked": True}
    return {"has_website": True, "reachable": False}


def score(audit):
    """Returns (score 0-100, gaps list). Zyada score = zyada opportunity."""
    if not audit.get("has_website", False):
        return 100, ["No website"]
    if not audit.get("reachable", False):
        return 75, ["Website is down or unreachable"]
    if audit.get("blocked"):
        return 0, ["Site blocks automated checks (audit not possible)"]

    pts, gaps = 0, []
    if not audit.get("chatbot"):
        pts += 25
        gaps.append("No chatbot / live chat")
    if not audit.get("online_booking"):
        pts += 20
        gaps.append("No online booking")
    if not audit.get("whatsapp"):
        pts += 15
        gaps.append("No WhatsApp contact")
    if not audit.get("mobile_friendly"):
        pts += 25
        gaps.append("Not mobile-friendly")
    if not audit.get("https"):
        pts += 10
        gaps.append("No HTTPS")
    year = audit.get("copyright_year")
    if year and year < date.today().year - 2:
        pts += 10
        gaps.append(f"Outdated site (copyright {year})")
    return min(pts, 100), gaps


def _audit_one(b):
    url = b.get("website") or b.get("url") or ""
    a = audit_site(url)
    s, gaps = score(a)
    lead = dict(b)
    lead["audit"] = a
    lead["score"] = s
    lead["gaps"] = gaps
    return lead


def audit_many(businesses, workers=8):
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_audit_one, businesses))