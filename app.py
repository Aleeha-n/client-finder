import csv
import io
import json
from pathlib import Path

import streamlit as st

import auditor
import finder
import planner
import search
import writer

st.set_page_config(page_title="Client Finder Bot", page_icon="🎀", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;700&display=swap');
html, body, .stApp, p, label, h1, h2, h3, span, div { font-family: 'Quicksand', sans-serif; }
.stApp {
    background:
        radial-gradient(circle at 15% 20%, #ffe0f0 0, transparent 40%),
        radial-gradient(circle at 85% 10%, #e8d9ff 0, transparent 40%),
        linear-gradient(160deg, #fff0f7 0%, #f3e8ff 100%);
}
h1, h2, h3, label, p, span, div { color: #4a2b6b; }
h1 { text-align: left; letter-spacing: 0.5px; }
.stButton > button {
    background: linear-gradient(90deg, #ff8fc8, #b388ff);
    color: white; border: none; border-radius: 999px;
    padding: 0.7rem 2rem; font-weight: 700; font-size: 1.05rem;
    box-shadow: 0 8px 20px rgba(179, 136, 255, 0.4);
    transition: all 0.2s ease;
}
.stButton > button:hover { transform: translateY(-3px) scale(1.04); color: white; }
.stDownloadButton > button {
    background: white; color: #8a5bd6; border: 2px solid #e3cffc; border-radius: 999px;
}
.bot-wrap { display: flex; align-items: center; gap: 22px; margin: 8px 0 22px 0; }
.bot { animation: float 3.2s ease-in-out infinite; filter: drop-shadow(0 10px 14px rgba(179,136,255,0.35)); }
.bubble {
    position: relative; background: white; border: 3px solid #e9d8ff; border-radius: 26px;
    padding: 14px 22px; font-size: 1.1rem; font-weight: 700; max-width: 540px;
    box-shadow: 0 10px 26px rgba(179, 136, 255, 0.22);
}
.bubble::before {
    content: ""; position: absolute; left: -14px; top: 50%; width: 22px; height: 22px;
    background: white; border-left: 3px solid #e9d8ff; border-bottom: 3px solid #e9d8ff;
    transform: translateY(-50%) rotate(45deg);
}
.eye { animation: blink 4s infinite; transform-origin: center; transform-box: fill-box; }
.arm-l { animation: wave 1.5s ease-in-out infinite; transform-origin: 30px 100px; transform-box: view-box; }
.arm-r { animation: wave2 2.2s ease-in-out infinite; transform-origin: 90px 100px; transform-box: view-box; }
.spark { animation: twinkle 1.8s ease-in-out infinite; transform-origin: center; transform-box: fill-box; }
.spark.s2 { animation-delay: 0.6s; }
.spark.s3 { animation-delay: 1.1s; }
.heart { animation: rise 3s ease-in infinite; opacity: 0; }
.heart.h2 { animation-delay: 1.5s; }
.working .bot { animation: bounce 0.7s ease-in-out infinite; }
.working .heart { animation-duration: 1.2s; }
@keyframes float { 0%,100% { transform: translateY(0) rotate(-1.5deg); } 50% { transform: translateY(-12px) rotate(1.5deg); } }
@keyframes bounce { 0%,100% { transform: translateY(0) scale(1,1); } 50% { transform: translateY(-14px) scale(1.04,0.96); } }
@keyframes blink { 0%,92%,100% { transform: scaleY(1); } 96% { transform: scaleY(0.1); } }
@keyframes wave { 0%,100% { transform: rotate(0deg); } 50% { transform: rotate(-30deg); } }
@keyframes wave2 { 0%,100% { transform: rotate(0deg); } 50% { transform: rotate(22deg); } }
@keyframes twinkle { 0%,100% { transform: scale(0.6); opacity: 0.4; } 50% { transform: scale(1.2); opacity: 1; } }
@keyframes rise { 0% { transform: translateY(0) scale(0.6); opacity: 0; } 20% { opacity: 1; } 100% { transform: translateY(-40px) scale(1.1); opacity: 0; } }
</style>
"""

BOT_SVG = """
<svg class="bot" width="150" height="165" viewBox="0 0 120 140" xmlns="http://www.w3.org/2000/svg">
<path class="spark s1" d="M10 20 l2 6 l6 2 l-6 2 l-2 6 l-2 -6 l-6 -2 l6 -2 z" fill="#ffd36e"/>
<path class="spark s2" d="M108 36 l2 5 l5 2 l-5 2 l-2 5 l-2 -5 l-5 -2 l5 -2 z" fill="#ff8fc8"/>
<path class="spark s3" d="M104 8 l1.5 4 l4 1.5 l-4 1.5 l-1.5 4 l-1.5 -4 l-4 -1.5 l4 -1.5 z" fill="#b388ff"/>
<path class="heart" d="M60 20 c-4 -6 -12 0 -6 6 l6 6 l6 -6 c6 -6 -2 -12 -6 -6 z" fill="#ff8fc8"/>
<path class="heart h2" d="M80 28 c-3 -5 -10 0 -5 5 l5 5 l5 -5 c5 -5 -2 -10 -5 -5 z" fill="#b388ff"/>
<path d="M26 40 L22 14 L46 30 Z" fill="#ffd1ea" stroke="#b388ff" stroke-width="4" stroke-linejoin="round"/>
<path d="M94 40 L98 14 L74 30 Z" fill="#ffd1ea" stroke="#b388ff" stroke-width="4" stroke-linejoin="round"/>
<path d="M28 34 L26 22 L38 30 Z" fill="#ff8fc8"/>
<path d="M92 34 L94 22 L82 30 Z" fill="#ff8fc8"/>
<rect x="16" y="28" width="88" height="64" rx="30" fill="#ffd1ea" stroke="#b388ff" stroke-width="4"/>
<rect x="30" y="40" width="60" height="38" rx="18" fill="#fff5fb"/>
<ellipse class="eye" cx="45" cy="58" rx="8" ry="10" fill="#4a2b6b"/>
<ellipse class="eye" cx="75" cy="58" rx="8" ry="10" fill="#4a2b6b"/>
<circle cx="48" cy="54" r="3" fill="white"/>
<circle cx="78" cy="54" r="3" fill="white"/>
<ellipse cx="32" cy="72" rx="7" ry="5" fill="#ff8fc8" opacity="0.6"/>
<ellipse cx="88" cy="72" rx="7" ry="5" fill="#ff8fc8" opacity="0.6"/>
<path d="M52 72 Q60 82 68 72" stroke="#4a2b6b" stroke-width="4" fill="none" stroke-linecap="round"/>
<rect x="36" y="96" width="48" height="36" rx="16" fill="#e9d8ff" stroke="#b388ff" stroke-width="4"/>
<circle cx="60" cy="114" r="6" fill="#ff8fc8"/>
<rect class="arm-l" x="8" y="98" width="26" height="10" rx="5" fill="#b388ff"/>
<rect class="arm-r" x="86" y="98" width="26" height="10" rx="5" fill="#b388ff"/>
<rect x="42" y="132" width="14" height="6" rx="3" fill="#b388ff"/>
<rect x="64" y="132" width="14" height="6" rx="3" fill="#b388ff"/>
</svg>
"""

CARD = (
    "background:white;border:3px solid #e9d8ff;border-radius:24px;"
    "padding:18px 20px;box-shadow:0 10px 26px rgba(179,136,255,0.18);"
    "text-align:center;height:100%;"
)


def bot_html(text, working=False):
    cls = "bot-wrap working" if working else "bot-wrap"
    return f'<div class="{cls}">{BOT_SVG}<div class="bubble">{text}</div></div>'


def make_csv(leads):
    cols = ["name", "website", "score", "gaps", "email", "phone", "subject", "message"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols)
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
    return buf.getvalue().encode("utf-8-sig")


st.markdown(CSS, unsafe_allow_html=True)
st.title("🎀 Client Finder Pookie")

bot_slot = st.empty()
bot_slot.markdown(
    bot_html("Hi! Tell me a niche and a city, and I will find local businesses that need your help!"),
    unsafe_allow_html=True,
)

LIVE = any((p / ".env").exists() for p in [Path.cwd(), *Path.cwd().parents])
if LIVE:
    mode = st.radio("Mode", ["Demo (saved results)", "Live search"], horizontal=True)
else:
    mode = "Demo (saved results)"
    
c1, c2, c3 = st.columns(3)
niche = c1.text_input("Niche", "dental clinics")
city = c2.text_input("City", "Islamabad")
lang = c3.selectbox("Message language", ["English", "Urdu", "Roman Urdu"])
c4, c5 = st.columns(2)
max_biz = c4.slider("Max businesses", 3, 30, 8)
n_out = c5.slider("Outreach messages", 0, 10, 2)

clicked = st.button("Find leads ✨")
if clicked and mode.startswith("Demo"):
    st.session_state["leads"] = json.loads(
        Path("sample_leads.json").read_text(encoding="utf-8")
    )
    bot_slot.markdown(
        bot_html(f"Here are {len(st.session_state['leads'])} saved sample leads. Higher score = bigger opportunity."),
        unsafe_allow_html=True,
    )
if clicked and not mode.startswith("Demo"):
    try:
        bot_slot.markdown(bot_html("Thinking of search queries...", True), unsafe_allow_html=True)
        queries = planner.plan_queries(niche, city)

        bot_slot.markdown(bot_html("Searching the web...", True), unsafe_allow_html=True)
        results = search.search_many(queries)

        bot_slot.markdown(bot_html("Picking out real businesses...", True), unsafe_allow_html=True)
        businesses = finder.extract_businesses(results, niche, city)[:max_biz]
        if not businesses:
            bot_slot.markdown(
                bot_html("I could not find any businesses. Try another niche or city!"),
                unsafe_allow_html=True,
            )
            st.stop()

        bot_slot.markdown(bot_html("Checking their websites...", True), unsafe_allow_html=True)
        leads = auditor.audit_many(businesses)
        leads.sort(key=lambda l: l.get("score", 0), reverse=True)

        if n_out > 0:
            bot_slot.markdown(bot_html("Writing friendly messages...", True), unsafe_allow_html=True)
            writer.write_all(leads, niche, city, lang, n_out)

        st.session_state["leads"] = leads
        bot_slot.markdown(
            bot_html(f"Done! I found {len(leads)} leads. Higher score = bigger opportunity."),
            unsafe_allow_html=True,
        )
    except Exception as e:
        bot_slot.markdown(bot_html("Oops, something went wrong."), unsafe_allow_html=True)
        st.error(str(e))

leads = st.session_state.get("leads")
if leads:
    
    st.subheader("Leads")
    rows = [
        {
            "Business": l.get("name", ""),
            "Score": l.get("score", 0),
            "Website": l.get("website", ""),
            "Gaps": "; ".join(l.get("gaps", [])),
        }
        for l in leads
    ]
    st.table(rows)

    st.subheader("Outreach drafts")
    shown = False
    for l in leads:
        o = l.get("outreach")
        if o and o.get("message"):
            shown = True
            with st.expander(f"{l.get('name', '?')} (score {l.get('score', 0)})"):
                st.write(f"**Subject:** {o.get('subject', '')}")
                st.write(o["message"])
    if not shown:
        st.caption("No outreach drafts yet.")

    st.download_button("Download leads.csv", make_csv(leads), "leads.csv", "text/csv")
else:
    st.markdown("### ✨ How it works")
    h1, h2, h3 = st.columns(3)
    h1.markdown(
        f'<div style="{CARD}"><div style="font-size:2.4rem">🔍</div>'
        "<b>1. Search</b><br>I look for local businesses in your niche and city.</div>",
        unsafe_allow_html=True,
    )
    h2.markdown(
        f'<div style="{CARD}"><div style="font-size:2.4rem">🩺</div>'
        "<b>2. Audit</b><br>I check their website: chatbot, booking, WhatsApp, mobile.</div>",
        unsafe_allow_html=True,
    )
    h3.markdown(
        f'<div style="{CARD}"><div style="font-size:2.4rem">💌</div>'
        "<b>3. Outreach</b><br>I write a friendly message for the best leads.</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    '<p style="text-align:center;margin-top:40px;opacity:0.7;">'
    "Made by Aleeha </p>",
    unsafe_allow_html=True,
)