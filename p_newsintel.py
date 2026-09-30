"""
p_newsintel.py - Discover → News Intelligence Engine: the news bot's headlines read by newsintel.py (event, sentiment,
materiality, impact, horizon, companies hit directly and indirectly, confidence, price reaction) and set against the price
(a setup score out of 100 with its parts). A live table; a story opens with its AI analysis, the affected stocks, why it
matters, the expected impact, the technical confirmation and a trading scenario.
"""
import json
import time

import pandas as pd
import requests
import streamlit as st

import data
import newsintel as NI
import newsiq
import theme as T
import ui
import universe as U
from i18n import SECTOR_AR, L, is_ar

ss = st.session_state

CSS = """<style>
.nie-pipe { display:flex; flex-wrap:wrap; align-items:stretch; gap:6px; margin:4px 0 14px; }
.nie-pipe .st { flex:1 1 120px; min-width:110px; background:linear-gradient(180deg, rgba(40,28,70,.72), rgba(24,17,40,.78));
  border:1px solid rgba(157,151,165,.22); border-radius:12px; padding:9px 11px; }
.nie-pipe .st .ms { color:#A78BFA; font-size:1.1rem; }
.nie-pipe .st b { display:block; color:#fff; font-size:.8rem; margin-top:3px; }
.nie-pipe .st span.s { display:block; color:#9D97A5; font-size:.7rem; margin-top:2px; line-height:1.35; }
.nie-pipe .ar { align-self:center; color:#6D5BA8; font-size:1rem; }
.nie-lv { display:flex; flex-wrap:wrap; gap:8px; margin:0 0 16px; }
.nie-lv span { display:inline-flex; align-items:center; gap:6px; font-size:.74rem; font-weight:600; color:#DCD6F7; padding:4px 11px;
  border-radius:999px; border:1px solid rgba(167,139,250,.35); background:rgba(124,58,237,.12); }
.nie-lv span b { color:#A78BFA; }
.nie-card { display:flex; gap:14px; align-items:flex-start; background:linear-gradient(180deg, rgba(34,24,58,.86), rgba(20,14,34,.9));
  border:1px solid rgba(157,151,165,.25); border-radius:16px; padding:14px; margin:6px 0 12px; }
.nie-card .nth.big { flex:none; width:170px; height:112px; }
.nie-card .tx { min-width:0; flex:1; }
.nie-card .tt { font-size:1.08rem; font-weight:700; color:#fff; line-height:1.4; }
.nie-card .tt a { color:#fff; text-decoration:none; } .nie-card .tt a:hover { text-decoration:underline; }
.nie-card .mt { color:#9D97A5; font-size:.76rem; margin-top:4px; }
.nie-card .hd { display:flex; flex-wrap:wrap; gap:6px; margin-top:9px; }
.nie-tag { display:inline-flex; align-items:center; gap:5px; font-size:.78rem; font-weight:700; padding:4px 10px; border-radius:9px;
  border:1px solid; }
.nie-grid { display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:8px; margin:4px 0 12px; }
.nie-f { background:rgba(24,18,38,.82); border:1px solid rgba(157,151,165,.18); border-radius:12px; padding:9px 12px; }
.nie-f .l { color:#9D97A5; font-size:.68rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; }
.nie-f .v { color:#fff; font-size:.9rem; font-weight:600; margin-top:3px; line-height:1.4; }
.nie-score { background:rgba(12,9,20,.88); border:1px solid rgba(157,151,165,.22); border-radius:14px; padding:12px 16px; margin:4px 0 12px;
  font-family:'Roboto Mono', ui-monospace, monospace; direction:ltr; }
.nie-score .r { display:grid; grid-template-columns: 1fr auto; gap:12px; font-size:.86rem; color:#DDD8E6; padding:3px 0; }
.nie-score .r b.p { color:#4ADE80; } .nie-score .r b.n { color:#F87171; } .nie-score .r b.z { color:#9D97A5; }
.nie-score .t { border-top:1px dashed rgba(157,151,165,.35); margin-top:6px; padding-top:7px; font-weight:700; color:#fff; }
.nie-score .lab { margin-top:9px; font-family:'DM Sans','Readex Pro',sans-serif; font-size:1rem; font-weight:800; }
.nie-note { color:#9D97A5; font-size:.76rem; line-height:1.55; margin-top:8px; }
.nie-li { margin:0; padding-inline-start:18px; color:#DDD8E6; font-size:.88rem; line-height:1.7; }
@media (max-width: 700px) { .nie-card { flex-direction:column; } .nie-card .nth.big { width:100%; height:150px; }
  .nie-grid { grid-template-columns: minmax(0, 1fr); } }
</style>"""

IMPACT_LEVELS = [(70, "High", "عالي"), (45, "Medium", "متوسط"), (0, "Low", "منخفض")]
_EV_ABBR = {"macro": "MAC", "market": "MKT", "earnings": "EPS", "guidance": "GUI", "mna": "M&A", "regulation": "REG", "lawsuit": "LAW",
            "management": "CEO", "contract": "WIN", "analyst": "RTG", "offering": "OFF", "payout": "DIV", "restructuring": "CUT",
            "product": "NEW", "distress": "RSK", "other": "CO"}


def impact_level(x):
    for lo, en, ar in IMPACT_LEVELS:
        if x >= lo:
            return L(en, ar)
    return L("Low", "منخفض")


def _ev_pic(ev):
    """A small picture for a story with no photo and no company: the kind of event on the site's colours (a data URL)."""
    col = {"macro": ("#3B82F6", "#7C3AED"), "market": ("#0EA5E9", "#6366F1")}.get(ev, ("#7C3AED", "#DB2777"))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="64"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
           f'<stop offset="0" stop-color="{col[0]}"/><stop offset="1" stop-color="{col[1]}"/></linearGradient></defs>'
           f'<rect width="96" height="64" rx="12" fill="url(#g)"/><text x="48" y="40" font-family="Arial" font-size="20" font-weight="700" '
           f'fill="#fff" text-anchor="middle">{_EV_ABBR.get(ev, "NEWS").replace("&", "&amp;")}</text></svg>')
    import base64
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def picture(a):
    """Every story has a picture: the outlet's photo, else the company's logo, else the kind of event."""
    img = str(a["n"].get("img") or "")
    if img.startswith("http"):
        return img
    if a["direct"]:
        return data.logo_url(a["direct"][0])
    return _ev_pic(a["event"])


def _sent_txt(lab):
    en, ar, _ = NI.SENT[lab]
    arrow = {"bull": "▲", "bear": "▼", "neutral": "●"}[lab]
    return f"{arrow} {L(en, ar)}"


def _stock_txt(a):
    return ", ".join(a["direct"][:3]) if a["direct"] else L("Market (SPY)", "السوق (SPY)")


def _ny_time(ts):
    try:
        t = pd.Timestamp(ts)
        t = t.tz_localize("UTC") if t.tzinfo is None else t
        return t.tz_convert("America/New_York").strftime("%m/%d %H:%M")
    except Exception:
        return ""


@st.cache_data(ttl=3600, show_spinner=False)
def _translate(titles):
    """{english headline: arabic} (the translator keeps the order; a headline it could not translate keeps its english)."""
    try:
        out = data.translate(list(titles), "ar")
    except Exception:
        return {}
    return {a: b for a, b in zip(titles, out or []) if b}


# ---------------------------------------------------------------- the optional AI analysis (only when the site has a key)
def _ai_key():
    try:
        import ai_assistant as AI
        return AI.settings()
    except Exception:
        return "", ""


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _ai_analysis(payload, lang):
    """A language model explains one story from the engine's numbers (it never decides a trade). '' when it cannot."""
    key, model = _ai_key()
    if not key:
        return ""
    try:
        import ai_assistant as AI
        ins = ("You are the News Analyst of a market-research website. Explain in 5 short bullet points what this news means for the "
               "companies named, why, how long the effect may last and what would confirm or cancel it, using ONLY the facts given. "
               "No buy/sell instructions; it is education. Answer in " + ("Arabic (clear Gulf-friendly Arabic)." if lang == "ar" else "English."))
        r = requests.post(AI.API_URL, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                          json={"model": model, "instructions": ins, "input": payload, "max_output_tokens": 500, "store": False}, timeout=35)
        if r.status_code < 400:
            return AI.extract(r.json())
    except Exception:
        pass
    return ""


def _engine_summary(a):
    """The engine's own reading in a few lines (shown when there is no AI key, and as the base of the AI's input)."""
    n, ev = a["n"], a["event"]
    en_ev, ar_ev = NI.EVENT.get(ev, NI.EVENT["other"])[:2]
    sen, sar, _ = NI.SENT[a["lab"]]
    hz = NI.HORIZON[a["horizon"]]
    who = _stock_txt(a)
    fa = a["facts"] or {}
    lines = [(f"Event: {en_ev} · {who}", f"الحدث: {ar_ev} · {who}"),
             (f"Reading: {sen} ({a['sent']:+.2f}), impact {a['impact']:.0f}/100, materiality {a['materiality']:.1f}/10, confidence {a['confidence']}%",
              f"القراءة: {sar} ({a['sent']:+.2f})، الأثر {a['impact']:.0f}/100، الأهمية {a['materiality']:.1f}/10، الثقة {a['confidence']}%"),
             (f"Horizon: {hz[0]}", f"الأفق الزمني: {hz[1]}")]
    if fa.get("chg") is not None:
        rv = f", volume {fa['rvol']:.1f}× its average" if fa.get("rvol") else ""
        rvar = f"، والحجم {fa['rvol']:.1f}× متوسطه" if fa.get("rvol") else ""
        lines.append((f"Price today: {fa['chg']:+.2f}%{rv}", f"السعر اليوم: {fa['chg']:+.2f}%{rvar}"))
    if a["words"]:
        w = ", ".join(dict.fromkeys(x.lower() for x in a["words"][:6]))
        lines.append((f"Words that decided the sentiment: {w}", f"الكلمات اللي حددت الاتجاه: {w}"))
    return lines


# ---------------------------------------------------------------- page
def _pipeline(n_items, n_co, n_macro, n_setups):
    steps = [("rss_feed", ("Sources", "المصادر"), ("35 feeds + Yahoo Finance", "35 مصدر + ياهو فاينانس")),
             ("filter_alt", ("Filter", "الفلترة"), ("duplicates merged, opinion pieces marked", "دمج المكرر وتمييز مقالات الرأي")),
             ("psychology", ("Understand", "الفهم"), (f"{n_items} stories: event, sentiment, materiality", f"{n_items} خبر: الحدث والاتجاه والأهمية")),
             ("hub", ("Link companies", "ربط الشركات"), (f"{n_co} with companies, direct and indirect", f"{n_co} مع شركات، مباشرة وغير مباشرة")),
             ("speed", ("Impact", "تقييم الأثر"), (f"impact 0-100, {n_macro} macro stories by sector", f"أثر 0-100، و{n_macro} خبر اقتصادي حسب القطاع")),
             ("insights", ("Setup", "الفرصة"), (f"{n_setups} setups: news + momentum + volume + trend + market",
                                                  f"{n_setups} فرصة: الخبر + الزخم + الحجم + الاتجاه + السوق"))]
    out = []
    for i, (ic, (en, ar), (sen, sar)) in enumerate(steps):
        if i:
            out.append(f'<span class="ar">{"←" if is_ar() else "→"}</span>')
        out.append(f'<div class="st">{T.icon(ic)}<b>{T.esc(L(en, ar))}</b><span class="s">{T.esc(L(sen, sar))}</span></div>')
    lv = [("Level 1", "المستوى 1", "News Scanner", "ماسح الأخبار"), ("Level 2", "المستوى 2", "News Analyst", "محلل الأخبار"),
          ("Level 3", "المستوى 3", "Trading Setup", "محرك الفرص")]
    lvh = "".join(f'<span><b>{T.esc(L(a, b))}</b>{T.esc(L(c, d))} ✓</span>' for a, b, c, d in lv)
    return f'<div class="nie-pipe">{"".join(out)}</div><div class="nie-lv">{lvh}</div>'


def _fact(label, value):
    return f'<div class="nie-f"><div class="l">{T.esc(label)}</div><div class="v">{value}</div></div>'


def _score_block(a):
    s = a["setup"]
    rows = []
    for k, en, ar, mx in NI.PARTS:
        v = s["parts"][k]
        cls = "p" if v > 0.5 else "n" if v < -0.5 else "z"
        rows.append(f'<div class="r"><span>{T.esc(L(en, ar))} <small style="color:#6F6A78">/{mx}</small></span><b class="{cls}">{v:+.0f}</b></div>')
    col = "#4ADE80" if s["dir"] > 0 and s["total"] >= 40 else "#F87171" if s["dir"] < 0 and s["total"] >= 40 else "#C4B5FD"
    return (f'<div class="nie-score">{"".join(rows)}<div class="r t"><span>{T.esc(L("Total Score", "المجموع"))}</span><b>{s["total"]}/100</b></div>'
            f'<div class="lab" style="color:{col}">{T.esc(L(*s["label"]))} — {s["total"]}/100</div></div>')


def _detail(a, chg, sec_chg, titles_ar):
    n = a["n"]
    ar = is_ar()
    title = (titles_ar.get(n["title"]) if ar and titles_ar else None) or n["title"]
    en_ev, ar_ev, ic, hz = NI.EVENT.get(a["event"], NI.EVENT["other"])
    sen, sar, scol = NI.SENT[a["lab"]]
    who = a["direct"][0] if a["direct"] else "SPY"
    imp_word = {"bull": ("Positive Impact", "أثر إيجابي"), "bear": ("Negative Impact", "أثر سلبي"), "neutral": ("Neutral Impact", "أثر محايد")}[a["lab"]]
    tags = (f'<span class="nie-tag" style="color:{scol};border-color:{scol}55;background:{scol}14">{T.esc(who)} — {T.esc(L(*imp_word))}</span>'
            f'<span class="nie-tag" style="color:#C4B5FD;border-color:#C4B5FD44;background:#7C3AED14">{T.icon(ic)}{T.esc(L(en_ev, ar_ev))}</span>')
    also = T.also_badge(n.get("also"), ar)
    ui.html(f'<div class="nie-card">{T.news_thumb(n, big=True)}<div class="tx"><div class="tt"><a href="{T.esc(n.get("link") or "#")}" '
            f'target="_blank">{T.esc(title)}</a></div><div class="mt">{T.esc(n.get("source") or "")}{also} · '
            f'{T.time_ago(n["time"], ar) if pd.notna(n.get("time")) else ""}</div><div class="hd">{tags}</div></div></div>')
    # the facts, as in a research note
    secs = " / ".join(dict.fromkeys(x for sec, sub in a["sectors"] for x in (L(sec, SECTOR_AR.get(sec, sec)), sub) if x))
    if not secs and a["macro"]:                    # macro news: the sectors it usually helps and hurts most
        eff = a["macro"][3]
        nm = lambda sec: L(sec, SECTOR_AR.get(sec, sec))
        up = [nm(k) for k, e in sorted(eff.items(), key=lambda x: -x[1]) if e >= 1][:3]
        dn = [nm(k) for k, e in sorted(eff.items(), key=lambda x: x[1]) if e <= -1][:2]
        secs = " · ".join(([L("Helped: ", "يستفيد: ") + "، ".join(up) if is_ar() else "Helped: " + ", ".join(up)] if up else [])
                          + ([L("Hurt: ", "يتضرر: ") + "، ".join(dn) if is_ar() else "Hurt: " + ", ".join(dn)] if dn else []))
    secs = secs or L("The whole market", "السوق كله")
    rel = ", ".join(a["indirect"][:5]) or "—"
    fa = a["facts"] or {}
    if a["moved_before"] is None:
        mb = L("Not known (no prices before it)", "غير معروف (ما فيه أسعار قبله)")
    elif a["moved_before"]:
        mb = L(f"Yes: {fa['pre']:+.1f}% in the 3 sessions before (more than 1.5× a normal move)",
               f"نعم: {fa['pre']:+.1f}% في الـ 3 جلسات قبله (أكثر من 1.5 ضعف الحركة العادية)")
    else:
        mb = L(f"No: {fa['pre']:+.1f}% in the 3 sessions before", f"لا: {fa['pre']:+.1f}% في الـ 3 جلسات قبله")
    age = a["age_h"]
    if age is None:
        new = "—"
    elif a["new"]:
        new = L(f"Yes, first seen {age * 60:.0f} min ago" if age < 1 else f"Yes, first seen {age:.1f} h ago",
                f"نعم، أول ظهور قبل {age * 60:.0f} دقيقة" if age < 1 else f"نعم، أول ظهور قبل {age:.1f} ساعة")
    else:
        new = L(f"No, reported {age:.0f} h ago" if age < 48 else f"No, reported {age / 24:.0f} days ago",
                f"لا، نُشر قبل {age:.0f} ساعة" if age < 48 else f"لا، نُشر قبل {age / 24:.0f} يوم")
    why_en, why_ar = NI.why(a)
    reason = L(why_en, why_ar).split(". ")[1] if ". " in L(why_en, why_ar) else L(why_en, why_ar)
    hzt = NI.HORIZON[hz]
    cells = [_fact(L("Event type", "نوع الخبر"), T.esc(L(en_ev, ar_ev))),
             _fact(L("Expected impact", "التأثير المتوقع"), f'<span style="color:{scol}">{T.esc(L(sen, sar))}</span>'),
             _fact(L("Time horizon", "الأفق الزمني"), T.esc(L(*hzt))),
             _fact(L("Impact severity", "شدة التأثير"), f"{a['severity']}/10 <small style='color:#9D97A5'>({a['impact']:.0f}/100 · {T.esc(impact_level(a['impact']))})</small>"),
             _fact(L("Confidence", "الثقة"), f"{a['confidence']}%"),
             _fact(L("Materiality", "أهمية الخبر للسهم"), f"{a['materiality']:.1f}/10 · " + T.esc(
                 L("material", "مهم فعلاً") if a["materiality"] >= 6 else L("worth watching", "يستحق المتابعة") if a["materiality"] >= 4 else L("mostly noise", "غالباً ضوضاء"))),
             _fact(L("Sectors affected", "القطاعات المتأثرة"), T.esc(secs)),
             _fact(L("Related companies", "شركات مرتبطة"), T.esc(rel)),
             _fact(L("Reason", "السبب"), T.esc(reason)),
             _fact(L("Is the news new?", "هل الخبر جديد؟"), T.esc(new)),
             _fact(L("Did the price move before the news?", "هل تحرك السعر قبل الخبر؟"), T.esc(mb)),
             _fact(L("Market regime", "حالة السوق"), T.esc(L(*NI.REGIME[a["regime"]])))]
    ui.html(f'<div class="nie-grid">{"".join(cells)}</div>')
    ui.html(_score_block(a))
    tabs = st.tabs([L("AI Analysis", "تحليل الذكاء الاصطناعي"), L("Affected Stocks", "الأسهم المتأثرة"), L("Why It Matters", "ليش يهم"),
                    L("Expected Market Impact", "الأثر المتوقع على السوق"), L("Technical Confirmation", "التأكيد الفني"),
                    L("Trading Scenario", "سيناريو التداول")])
    with tabs[0]:
        lines = _engine_summary(a)
        key, _m = _ai_key()
        payload = json.dumps({"headline": n["title"], "summary": (n.get("summary") or "")[:600], "source": n.get("source"),
                              "engine": [ln[0] for ln in lines], "companies_direct": a["direct"], "companies_indirect": a["indirect"],
                              "setup": {"score": a["setup"]["total"], "label": a["setup"]["label"][0], "parts": a["setup"]["parts"]}})
        if key:
            k_ = "nie_ai_" + str(abs(hash(n.get("link") or n["title"])))
            if st.button(L("Analyse this story with AI", "حلّل هالخبر بالذكاء الاصطناعي"), icon=":material/auto_awesome:", key=k_):
                ss[k_ + "_on"] = True
            if ss.get(k_ + "_on"):
                with st.spinner(L("The AI analyst is reading the story...", "محلل الذكاء الاصطناعي يقرأ الخبر...")):
                    txt = _ai_analysis(payload, "ar" if ar else "en")
                st.markdown(txt or L("The AI could not answer this time; the engine's reading is below.",
                                     "الذكاء الاصطناعي ما رد هالمرة، وقراءة المحرك تحت."))
        ui.html('<ul class="nie-li">' + "".join(f"<li>{T.esc(L(*ln))}</li>" for ln in lines) + "</ul>")
        if not key:
            ui.html(f'<div class="nie-note">{T.esc(L("This is the engine’s own reading (rules and numbers). With an AI key (OPENAI_API_KEY in the site’s Secrets) a button here asks the AI analyst to explain the story in words.", "هذي قراءة المحرك نفسه (قواعد وأرقام). ولما يكون للموقع مفتاح ذكاء اصطناعي (OPENAI_API_KEY في Secrets) يطلع هنا زر يطلب من محلل الذكاء الاصطناعي يشرح الخبر بالكلام."))}</div>')
    with tabs[1]:
        rows = []
        for kind, syms in ((L("Direct", "مباشر"), a["direct"]), (L("Indirect", "غير مباشر"), a["indirect"])):
            for sym in syms:
                name, sec, sub = NI.company(sym)
                c = chg.get(sym)
                rows.append({L("Link", "العلاقة"): kind, L("Stock", "السهم"): sym, L("Company", "الشركة"): name,
                             L("Sector", "القطاع"): L(sec, SECTOR_AR.get(sec, sec)) if sec else "", L("Industry", "الصناعة"): sub or "",
                             L("Today", "اليوم"): (f"{c[1]:+.2f}%" if c and c[1] is not None else "—")})
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            ui.html(f'<div class="nie-note">{T.esc(L("Indirect: suppliers, customers and closest rivals the site knows, then the largest companies of the same industry.", "غير مباشر: الموردين والعملاء وأقرب المنافسين اللي يعرفهم الموقع، وبعدهم أكبر شركات نفس الصناعة."))}</div>')
        else:
            st.caption(L("No single company: this story moves the market as a whole (see the expected impact by sector).",
                         "ما فيه شركة محددة: هالخبر يحرك السوق كله (شف الأثر المتوقع حسب القطاع)."))
    with tabs[2]:
        st.markdown(L(why_en, why_ar))
    with tabs[3]:
        st.markdown(L(f"**{sen}** · {hzt[0]} · severity **{a['severity']}/10** · confidence **{a['confidence']}%**",
                      f"**{sar}** · {hzt[1]} · الشدة **{a['severity']}/10** · الثقة **{a['confidence']}%**"))
        if a["macro"]:
            key_, en_m, ar_m, eff = a["macro"]
            st.caption(L(f"{en_m}: how each sector usually takes it (a rule of thumb) and how its fund actually moved today.",
                         f"{ar_m}: كيف يتأثر كل قطاع عادةً (قاعدة عامة) وكيف تحرك صندوقه فعلاً اليوم."))
            etf_of = {v: k for k, v in U.SECTOR_ETFS.items()}
            rows = []
            for sec, e in sorted(eff.items(), key=lambda x: -x[1]):
                etf = etf_of.get(sec)
                c = sec_chg.get(etf) if etf else None
                agree = "—" if not c or e == 0 else ("✓" if (c[1] > 0) == (e > 0) else "✗")
                rows.append({L("Sector", "القطاع"): L(sec, SECTOR_AR.get(sec, sec)), L("Usually", "عادةً"): {2: "▲▲", 1: "▲", 0: "●", -1: "▼", -2: "▼▼"}[e],
                             L("Fund", "الصندوق"): etf or "", L("Today", "اليوم"): f"{c[1]:+.2f}%" if c else "—", L("As usual?", "مثل العادة؟"): agree})
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        elif a["direct"]:
            st.caption(L("The story's weight on the stock is the impact score; the related companies usually move less, in the same direction.",
                         "وزن الخبر على السهم هو درجة الأثر، والشركات المرتبطة غالباً تتحرك أقل وبنفس الاتجاه."))
    with tabs[4]:
        if fa:
            sym = a["main"]
            items = []
            c = fa.get("close")
            for k, en, ar_ in (("sma20", "20-day", "20 يوم"), ("sma50", "50-day", "50 يوم"), ("sma200", "200-day", "200 يوم")):
                v = fa.get(k)
                if v and c:
                    items.append(L(f"{sym} is {'above' if c > v else 'below'} its {en} average ({v:,.2f}), {c / v - 1:+.1%}",
                                   f"{sym} {'فوق' if c > v else 'تحت'} متوسط {ar_} ({v:,.2f})، {c / v - 1:+.1%}"))
            if fa.get("rvol"):
                items.append(L(f"Volume today: {fa['rvol']:.1f}× its 20-day average", f"حجم التداول اليوم: {fa['rvol']:.1f}× متوسط 20 يوم"))
            if a["move"] is not None and fa.get("chg") is not None:
                items.append(L(f"Today's move {fa['chg']:+.2f}% = {abs(a['move']):.1f}× a normal day (ATR {fa['atr_pct']:.1f}%)" if fa.get("atr_pct") else f"Today's move {fa['chg']:+.2f}%",
                               f"حركة اليوم {fa['chg']:+.2f}% = {abs(a['move']):.1f} ضعف اليوم العادي (ATR {fa['atr_pct']:.1f}%)" if fa.get("atr_pct") else f"حركة اليوم {fa['chg']:+.2f}%"))
            if fa.get("ret21") is not None:
                items.append(L(f"Last month: {fa['ret21']:+.1f}%", f"آخر شهر: {fa['ret21']:+.1f}%"))
            ui.html('<ul class="nie-li">' + "".join(f"<li>{T.esc(x)}</li>" for x in items) + "</ul>")
        else:
            st.caption(L("No prices for this stock right now.", "ما فيه أسعار لهالسهم الحين."))
    with tabs[5]:
        sc = NI.scenario(a)
        st.markdown(L(*sc) if sc else L("No trading scenario: the news and the price do not line up enough (the setup is under 40/100).",
                                        "ما فيه سيناريو تداول: الخبر والسعر ما يتفقون كفاية (الفرصة أقل من 40/100)."))
        ui.html(f'<div class="nie-note">{T.esc(L("Education, not a recommendation. The rules above decide the setup; a language model only explains a story and never trades.", "للتعليم، مو توصية. القواعد فوق هي اللي تحدد الفرصة، والذكاء الاصطناعي يشرح الخبر بس وما يتداول أبداً."))}</div>')


def page_news_intel():
    ui.html(CSS)
    ui.header("neurology", "News Intelligence Engine", "محرك ذكاء الأخبار",
              "Every headline read like an analyst would: the kind of event, bullish or bearish, how material it is, its impact from 0 to 100, "
              "how long it may last, the companies it hits directly and indirectly, and whether the price confirms it — then a setup score "
              "out of 100 with its parts.",
              "كل خبر ينقرأ مثل ما يقرأه المحلل: نوع الحدث، صاعد أو هابط، أهميته، أثره من 0 إلى 100، كم يدوم، الشركات اللي يأثر عليها "
              "مباشرة وغير مباشرة، وهل السعر يؤكده، وبعدين درجة الفرصة من 100 مع أجزائها.")
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.6, 1.2, 1.2, 1], vertical_alignment="bottom")
    hrs = c1.segmented_control(L("Time", "الوقت"), [6, 24, 96], default=24, key="nie_hrs",
                               format_func=lambda h: {6: L("6 hours", "6 ساعات"), 24: L("24 hours", "24 ساعة"), 96: L("4 days", "4 أيام")}[h]) or 24
    ev_keys = [k for k, *_ in NI.EVENTS] + ["market", "other"]
    ui.valid_multi("nie_ev", ev_keys)
    pick_ev = c2.multiselect(L("Event type", "نوع الخبر"), ev_keys, key="nie_ev", placeholder=L("All events", "كل الأحداث"),
                             format_func=lambda k: L(*NI.EVENT[k][:2]))
    sent = c3.segmented_control(L("Sentiment", "الاتجاه"), ["all", "bull", "bear"], default="all", key="nie_sent",
                                format_func=lambda k: L("All", "الكل") if k == "all" else L(*NI.SENT[k][:2])) or "all"
    sort = c4.segmented_control(L("Sort by", "الترتيب"), ["impact", "setup", "new"], default="impact", key="nie_sort",
                                format_func=lambda k: {"impact": L("Impact", "الأثر"), "setup": L("Setup", "الفرصة"), "new": L("Latest", "الأحدث")}[k]) or "impact"
    tr = c5.toggle(L("Translate to Arabic", "ترجمة للعربية"), value=is_ar(), key="nie_tr")
    with st.spinner(L("Reading the news and the prices...", "يقرأ الأخبار والأسعار...")):
        items = data.market_news(96)
        now = pd.Timestamp.now(tz="UTC")
        items = [n for n in items if pd.notna(n.get("time")) and n["time"] >= now - pd.Timedelta(hours=hrs)][:400]
        tick = sorted({t for n in items[:300] for t in (n.get("tickers") or [])[:2] if t})
        chg = data.quick_changes(tick) if tick else {}
        newsiq.enrich(items, chg)
        items = [n for n in items if not any(k[0] == "opinion" for k in n["iq"].get("keywords", []))]      # opinion pieces out
        mains = [((n.get("tickers") or [None])[0]) for n in items]
        syms = ("SPY",) + tuple(sorted({s for s in mains if s and s != "SPY"}))[:79]
        px = data.history_many(syms, "1y") if syms else {}
        res = NI.analyze_all(items, px, chg, px.get("SPY"), now)
    if not res:
        st.info(L("The news bot has no headlines for this time yet; try a longer time or come back in a few minutes.",
                  "بوت الأخبار ما عنده عناوين لهالوقت للحين، جرّب وقت أطول أو ارجع بعد دقائق."), icon=":material/hourglass_empty:")
        return
    ui.html(_pipeline(len(res), sum(1 for a in res if a["direct"]), sum(1 for a in res if a["event"] == "macro"),
                      sum(1 for a in res if a["setup"]["total"] >= 55)))
    shown = [a for a in res if (not pick_ev or a["event"] in pick_ev) and (sent == "all" or a["lab"] == sent)]
    key_of = {"impact": lambda a: -a["impact"], "setup": lambda a: -a["setup"]["total"],
              "new": lambda a: -(a["n"]["time"].timestamp() if pd.notna(a["n"].get("time")) else 0)}
    shown.sort(key=key_of[sort])
    # headline numbers
    bull, bear = sum(1 for a in shown if a["lab"] == "bull"), sum(1 for a in shown if a["lab"] == "bear")
    high = sum(1 for a in shown if a["impact"] >= 70)
    top_ev = pd.Series([a["event"] for a in shown]).value_counts().index[0] if shown else None
    k = st.columns(4)
    k[0].markdown(T.kpi("newspaper", L("Stories analysed", "أخبار تم تحليلها"), f"{len(shown):,}", L("opinion pieces left out", "بدون مقالات الرأي")), unsafe_allow_html=True)
    k[1].markdown(T.kpi("balance", L("Bullish · Bearish", "صاعد · هابط"), f"{bull} · {bear}", L("by the words and the price", "حسب الكلمات والسعر"),
                        "pos" if bull > bear else "neg" if bear > bull else None), unsafe_allow_html=True)
    k[2].markdown(T.kpi("bolt", L("High impact (70+)", "أثر عالي (70+)"), f"{high}", L("worth your attention now", "تستحق انتباهك الحين"), "neg" if high else None),
                  unsafe_allow_html=True)
    k[3].markdown(T.kpi(NI.EVENT[top_ev][2] if top_ev else "category", L("Most common event", "أكثر نوع خبر"),
                        T.esc(L(*NI.EVENT[top_ev][:2])) if top_ev else "—", L("in this window", "في هالفترة")), unsafe_allow_html=True)
    if not shown:
        st.caption(L("No story matches these filters.", "ما فيه خبر يطابق هالفلاتر."))
        return
    ui.sec("monitoring", "Live Market Intelligence", "ذكاء السوق المباشر")
    rows = shown[:120]
    titles_ar = _translate(tuple(a["n"]["title"] for a in rows)) if tr else {}
    df = pd.DataFrame([{"pic": picture(a), "time": _ny_time(a["n"]["time"]), "stock": _stock_txt(a),
                        "news": (titles_ar.get(a["n"]["title"]) if titles_ar else None) or a["n"]["title"],
                        "event": L(*NI.EVENT[a["event"]][:2]), "impact": f"{impact_level(a['impact'])} · {a['impact']:.0f}",
                        "sent": _sent_txt(a["lab"]), "score": a["setup"]["total"]} for a in rows])
    cfg = {"pic": st.column_config.ImageColumn("", width="small"),
           "time": st.column_config.TextColumn(L("Time (NY)", "الوقت (نيويورك)"), width="small"),
           "stock": st.column_config.TextColumn(L("Stock", "السهم"), width="small"),
           "news": st.column_config.TextColumn(L("News", "الخبر"), width="large"),
           "event": st.column_config.TextColumn(L("Event", "الحدث")),
           "impact": st.column_config.TextColumn(L("Impact", "الأثر")),
           "sent": st.column_config.TextColumn(L("Sentiment", "الاتجاه")),
           "score": st.column_config.ProgressColumn(L("Setup", "الفرصة"), min_value=0, max_value=100, format="%d")}
    try:
        ev = st.dataframe(df, hide_index=True, width="stretch", height=min(38 * len(df) + 40, 520), column_config=cfg,
                          on_select="rerun", selection_mode="single-row", key="nie_tbl")
        sel = list(getattr(getattr(ev, "selection", None), "rows", None) or [])
    except TypeError:                                  # an older Streamlit without row selection
        st.dataframe(df, hide_index=True, width="stretch", column_config=cfg)
        sel = []
    st.caption(L("Tick a row to open the story. Impact: how strongly the news can move its stock (0-100). Setup: the news set against "
                 "momentum, volume, trend and the market (0-100).",
                 "علّم على أي سطر عشان يفتح الخبر. الأثر: قوة الخبر في تحريك سهمه (0-100). الفرصة: الخبر مقابل الزخم والحجم والاتجاه "
                 "والسوق (0-100)."))
    i = sel[0] if sel and sel[0] < len(rows) else 0
    a = rows[i]
    ui.sec("article", "Story analysis", "تحليل الخبر")
    peers_ = sorted({s for s in a["direct"] + a["indirect"]})
    chg2 = dict(chg)
    if peers_:
        chg2.update(data.quick_changes(peers_))
    sec_chg = data.quick_changes(list(U.SECTOR_ETFS)) if a["macro"] else {}
    _detail(a, chg2, sec_chg, titles_ar)

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "15.6"
