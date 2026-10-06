import argparse
import csv
import re
from datetime import date
from pathlib import Path

import auditor
import finder
import planner
import search
import writer


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def save_csv(path, leads):
    cols = ["name", "website", "score", "gaps", "email", "phone", "subject", "message"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for l in leads:
            a = l.get("audit", {})
            o = l.get("outreach", {})
            w.writerow({
                "name": l.get("name", ""),
                "website": l.get("website", ""),
                "score": l.get("score", 0),
                "gaps": "; ".join(l.get("gaps", [])),
                "email": a.get("email", ""),
                "phone": a.get("phone", ""),
                "subject": o.get("subject", ""),
                "message": o.get("message", ""),
            })


def save_report(path, leads, niche, city):
    lines = [f"# Leads: {niche} in {city}", "", f"Total leads: {len(leads)}", ""]
    for i, l in enumerate(leads, 1):
        a = l.get("audit", {})
        lines.append(f"## {i}. {l.get('name', '?')} (score {l.get('score', 0)})")
        lines.append(f"- Website: {l.get('website', '') or 'none'}")
        if a.get("email"):
            lines.append(f"- Email: {a['email']}")
        if a.get("phone"):
            lines.append(f"- Phone: {a['phone']}")
        gaps = l.get("gaps", [])
        lines.append("- Gaps: " + ("; ".join(gaps) if gaps else "none found"))
        o = l.get("outreach")
        if o and o.get("message"):
            lines += ["", f"**Subject:** {o.get('subject', '')}", "", o["message"]]
        elif o and o.get("error"):
            lines.append(f"- Outreach error: {o['error']}")
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("niche")
    p.add_argument("city")
    p.add_argument("--lang", default="English")
    p.add_argument("--max-businesses", type=int, default=20)
    p.add_argument("--outreach", type=int, default=8)
    args = p.parse_args()

    print("1/5 Planning search queries...")
    queries = planner.plan_queries(args.niche, args.city)
    print(f"    {len(queries)} queries")

    print("2/5 Searching the web...")
    results = search.search_many(queries)
    print(f"    {len(results)} results found")

    print("3/5 Extracting businesses...")
    businesses = finder.extract_businesses(results, args.niche, args.city)
    businesses = businesses[: args.max_businesses]
    print(f"    {len(businesses)} businesses")
    if not businesses:
        print("No businesses found. Try a different niche or city.")
        return

    print("4/5 Auditing websites...")
    leads = auditor.audit_many(businesses)
    leads.sort(key=lambda l: l.get("score", 0), reverse=True)

    print("5/5 Writing outreach messages...")
    writer.write_all(leads, args.niche, args.city, args.lang, args.outreach)

    out = Path("output") / f"{slug(args.niche)}-{slug(args.city)}-{date.today()}"
    out.mkdir(parents=True, exist_ok=True)
    save_report(out / "report.md", leads, args.niche, args.city)
    save_csv(out / "leads.csv", leads)
    print(f"Done! Files saved in: {out}")


if __name__ == "__main__":
    main()