# Client Finder Agent

A small multi-agent system that finds local businesses that need a website, chatbot or automation, audits their online presence, and drafts a personalised outreach message for each top lead.

```
"dental clinics" + "Islamabad"
   |
   v
Planner  -> writes 5 different search queries            (LLM)
Search   -> DuckDuckGo results                            (free, no key)
Finder   -> extracts the individual businesses            (LLM + guards against invented sites)
Auditor  -> checks each website: chatbot? booking? WhatsApp? mobile? HTTPS? outdated?   (plain code)
Scorer   -> opportunity score 0-100 (explainable rules)
Writer   -> short outreach message for the top leads      (LLM)
   |
   v
output/<niche>-<city>-<date>/report.md  +  leads.csv
```

Design choices: the audit and score are deterministic code (explainable, free, no hallucinations); the LLM is used only where language understanding is needed. Outreach is only drafted, never sent automatically.

## Setup
```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```
Copy `.env.example` to `.env` and paste a free Groq API key (https://console.groq.com).

## Run
```bash
python main.py "dental clinics" "Islamabad"
python test_offline.py          # tests without internet or API key
```

## Limitations
- Search quality depends on DuckDuckGo; some businesses have no website and only a social page.
- The audit looks at the homepage HTML only (JavaScript-injected chat widgets may be missed).
- Always review drafted messages before sending, and respect each country's rules on cold outreach.
