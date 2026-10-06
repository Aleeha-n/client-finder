"""Offline checks (no internet, no API key): python test_offline.py"""
import tempfile
from pathlib import Path

import finder
import auditor
import main as m

# --- auditor on sample HTML
html = '<meta name="viewport" content="x"><footer>© 2019 Smile Clinic</footer><a href="tel:+92 300 1234567">call</a> info@smile.pk'
a = auditor.analyze_html(html, "https://smile.pk")
a["has_website"] = True
sc, gaps = auditor.score(a)
assert a["mobile_friendly"] and not a["chatbot"] and a["email"] == "info@smile.pk" and a["phone"] == "+92 300 1234567"
assert sc == 10 + 30 + 20 + 10 + 10 and "No chatbot / live chat" in gaps, (sc, gaps)
assert auditor.score({"has_website": False})[0] == 90
a2 = auditor.analyze_html("<script src='https://embed.tawk.to/x'></script> Book online wa.me/92", "https://x.pk")
assert a2["chatbot"] and a2["online_booking"] and a2["whatsapp"]

# --- finder guards against invented / directory websites
results = [{"url": "https://www.smile.pk/", "title": "t", "snippet": "s"},
           {"url": "https://www.facebook.com/x", "title": "t", "snippet": "s"}]
finder.chat_json = lambda *a, **k: {"businesses": [
    {"name": "Smile Clinic", "website": "https://smile.pk"},
    {"name": "Fake Clinic", "website": "https://invented.com"},
    {"name": "FB Clinic", "website": "https://www.facebook.com/x"},
    {"name": "Smile Clinic", "website": ""},
]}
b = finder.extract_businesses(results, "dental", "Islamabad")
sites = {x["name"]: x["website"] for x in b}
assert sites["Smile Clinic"] == "https://smile.pk" and sites["Fake Clinic"] == "" and sites["FB Clinic"] == "", sites
assert len(b) == 3, b  # Smile Clinic counted once

# --- report writing
leads = [{"name": "A", "website": "", "audit": {"has_website": False}, "score": 90,
          "gaps": ["No website found"], "subject": "Hi", "message": "Hello", "pitch": "New website"}]
with tempfile.TemporaryDirectory() as d:
    m.write_outputs(leads, "dental", "Islamabad", Path(d))
    assert "Hello" in (Path(d) / "report.md").read_text() and (Path(d) / "leads.csv").exists()
print("All offline tests passed.")
