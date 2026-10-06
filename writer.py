import json

import llm

SYSTEM = (
    "You write short, polite, honest cold outreach messages from a freelance "
    "web developer and AI automation builder named Aleeha to a local business. "
    "Rules: use ONLY the facts given in the audit data, never invent facts, "
    "prices, results or claims. Mention one or two specific problems found on "
    "their website and offer a small free help (for example a quick demo or "
    "a short audit). Keep the message under 90 words, friendly, no hype, "
    "no emojis spam. End with the sign-off 'Aleeha'. "
    "Reply ONLY with JSON: {\"subject\": \"...\", \"message\": \"...\"}"
)


def write_outreach(lead, niche, city, lang="English"):
    """Ek lead ke liye outreach message banata hai."""
    facts = json.dumps(lead, ensure_ascii=False, default=str)[:1500]
    user = (
        f"Business niche: {niche}\n"
        f"City: {city}\n"
        f"Write the message in this language: {lang}\n"
        f"Audit data about the business:\n{facts}"
    )
    try:
        data = llm.chat_json(SYSTEM, user, max_tokens=700)
    except Exception as e:
        return {"subject": "", "message": "", "error": str(e)}
    if not isinstance(data, dict):
        return {"subject": "", "message": "", "error": "bad llm output"}
    return {
        "subject": str(data.get("subject", "")).strip(),
        "message": str(data.get("message", "")).strip(),
    }


def write_all(leads, niche, city, lang="English", limit=8):
    """Top leads (score ke hisaab se) ke liye outreach likhta hai."""
    top = sorted(leads, key=lambda l: l.get("score", 0), reverse=True)[:limit]
    for lead in top:
        lead["outreach"] = write_outreach(lead, niche, city, lang)
    return top