import csv
import json
from pathlib import Path

SRC = Path("output/dental-clinics-islamabad-2026-10-06/leads.csv")

leads = []
with open(SRC, encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        gaps = [g.strip() for g in row["gaps"].split(";") if g.strip()]
        lead = {
            "name": row["name"],
            "website": row["website"],
            "score": int(row["score"] or 0),
            "gaps": gaps,
        }
        if row["message"].strip():
            lead["outreach"] = {"subject": row["subject"], "message": row["message"]}
        leads.append(lead)

Path("sample_leads.json").write_text(
    json.dumps(leads, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"Saved {len(leads)} leads to sample_leads.json")
print("Names:", [l["name"] for l in leads])