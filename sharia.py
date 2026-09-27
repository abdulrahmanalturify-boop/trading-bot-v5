"""
sharia.py - Sharia compliance of a company share, in the site's style (stock page, Company tab).

An educational screen with the usual AAOIFI-style thresholds, computed from Yahoo Finance data:
  1. Business activity: the main business must be permissible (no conventional banking, insurance, alcohol, tobacco, gambling ...).
  2. Revenue: income that is not halal (interest income) plus doubtful income (other non-operating income whose source is not
     disclosed) must stay under 5% of total revenue.
  3. Interest-bearing securities & assets (cash and short-term investments) under 30% of the 36-month average market cap.
  4. Interest-bearing debt under 30% of the 36-month average market cap.
It is not a religious ruling; screening providers and scholars can differ.
"""
import numpy as np
import pandas as pd
import streamlit as st

import data
import theme as T
import ui
from i18n import L, industry_name, is_ar

BUILD = "10.0.1"

REV_MAX, RATIO_MAX = 5.0, 30.0
HALAL, DOUBT, HARAM = "#4ADE80", "#F5B94A", "#F87171"

# industries whose main business is not permissible, and ones that need a closer look (Yahoo's industry names, lower case)
NOT_OK = ("bank", "insurance", "credit services", "mortgage finance", "brewers", "winer", "distill", "tobacco", "gambling", "casino")
DOUBTFUL = ("capital markets", "asset management", "financial conglomerates", "reit - mortgage", "shell companies")


def _row(df, *names):
    """The latest reported value of the first line item found (Yahoo puts the newest period first)."""
    if not isinstance(df, pd.DataFrame) or df.empty:
        return None
    for n in names:
        if n in df.index:
            s = pd.to_numeric(df.loc[n], errors="coerce")
            if isinstance(s, pd.DataFrame):
                s = s.iloc[0]
            s = s.dropna()
            if len(s):
                return float(s.iloc[0])
    return None


def business(industry):
    ind = str(industry or "").lower().replace("—", " - ").replace("–", " - ")
    if not ind:
        return "unknown"
    if any(k in ind for k in NOT_OK):
        return "fail"
    if any(k in ind for k in DOUBTFUL):
        return "doubt"
    return "pass"


@st.cache_data(ttl=21600, show_spinner=False)
def _screen(sym):
    inf = data.info(sym)
    kind = str(inf.get("quoteType") or "EQUITY").upper()
    if kind not in ("EQUITY", ""):
        return {"kind": kind}
    p = data.profile(sym)
    stm = data.statements(sym)
    inc, bal = stm.get("inc_a"), stm.get("bal_a")
    if (not isinstance(inc, pd.DataFrame) or inc.empty) and (not isinstance(bal, pd.DataFrame) or bal.empty):
        raise LookupError("no statements yet")               # not kept: tried again next time
    out = {"kind": "EQUITY", "industry": p.get("industry"), "sector": p.get("sector"), "business": business(p.get("industry"))}
    # revenue breakdown (latest fiscal year)
    rev = _row(inc, "Total Revenue", "Operating Revenue")
    intr = _row(inc, "Interest Income", "Interest Income Non Operating") or 0.0
    other = _row(inc, "Other Non Operating Income Expenses", "Other Income Expense") or 0.0
    if rev and rev > 0:
        if out["business"] == "fail":
            haram, doubt = 100.0, 0.0                          # the main business itself is not permissible
        else:
            haram = min(100.0, max(intr, 0.0) / rev * 100)
            doubt = min(100.0 - haram, max(other, 0.0) / rev * 100)
        out.update(rev=rev, haram=haram, doubt=doubt, halal=max(0.0, 100.0 - haram - doubt))
    # the 36-month average market cap (today's share count x the average month-end price)
    shares = inf.get("sharesOutstanding") or inf.get("impliedSharesOutstanding")
    mcap = None
    try:
        h = data.history(sym, "5y")
        m = h["Close"].resample("ME").last().dropna().tail(36) if not h.empty else pd.Series(dtype=float)
        if shares and len(m) >= 12:
            mcap, out["months"] = float(m.mean()) * float(shares), len(m)
    except Exception:
        mcap = None
    if not mcap:
        mcap = inf.get("marketCap")
        out["months"] = 0
    out["mcap"] = float(mcap) if mcap else None
    cash = _row(bal, "Cash Cash Equivalents And Short Term Investments")
    if cash is None:
        c1 = _row(bal, "Cash And Cash Equivalents")
        c2 = _row(bal, "Other Short Term Investments")
        cash = None if c1 is None and c2 is None else (c1 or 0.0) + (c2 or 0.0)
    debt = _row(bal, "Total Debt")
    if debt is None:
        d1, d2 = _row(bal, "Long Term Debt"), _row(bal, "Current Debt")
        debt = None if d1 is None and d2 is None else (d1 or 0.0) + (d2 or 0.0)
    if out["mcap"]:
        out["sec"] = None if cash is None else cash / out["mcap"] * 100
        out["debt"] = None if debt is None else debt / out["mcap"] * 100
    return out


def screen(sym):
    try:
        return _screen(sym)
    except Exception:
        return None


def verdict(r):
    """'pass' (halal), 'fail' (not halal) or 'doubt' (a doubtful business or missing data) with the four checks."""
    checks = {"business": r.get("business", "unknown"),
              "revenue": None if r.get("rev") is None else ("pass" if r["haram"] + r["doubt"] < REV_MAX else "fail"),
              "sec": None if r.get("sec") is None else ("pass" if r["sec"] < RATIO_MAX else "fail"),
              "debt": None if r.get("debt") is None else ("pass" if r["debt"] < RATIO_MAX else "fail")}
    if "fail" in checks.values():
        return "fail", checks
    if None in checks.values() or "doubt" in checks.values() or "unknown" in checks.values():
        return "doubt", checks
    return "pass", checks


# ---------------------------------------------------------------- the look
CSS = f"""<style>
.shbn {{ position:relative; overflow:hidden; border-radius:18px; border:1px solid var(--edge); min-height:132px; display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:4px; margin:4px 0 14px; background:var(--line) top / 100% 3px no-repeat,
  radial-gradient(420px 150px at 50% 55%, var(--glow), transparent 70%), {T.CARD}; }}
.shbn .patw {{ position:absolute; inset:0; pointer-events:none;
  -webkit-mask-image:linear-gradient(90deg,#000 0%,rgba(0,0,0,.85) 18%,transparent 36%,transparent 64%,rgba(0,0,0,.85) 82%,#000 100%);
  mask-image:linear-gradient(90deg,#000 0%,rgba(0,0,0,.85) 18%,transparent 36%,transparent 64%,rgba(0,0,0,.85) 82%,#000 100%); }}
.shbn .patw svg {{ width:100%; height:100%; display:block; }}
.shbn .fade {{ position:absolute; inset:0; pointer-events:none; background:radial-gradient(34% 90% at 50% 50%, {T.CARD} 0%, rgba(11,21,48,.92) 45%, transparent 100%); }}
.shbn .ic {{ position:relative; width:54px; height:54px; }}
.shbn .v {{ position:relative; font-size:1.55rem; font-weight:800; color:#fff; letter-spacing:-.01em; }}
.shbn .s {{ position:relative; font-size:.8rem; color:#C9D2E8; text-align:center; max-width:520px; padding:0 12px; }}
.shgrid {{ display:grid; grid-template-columns:minmax(0,2fr) minmax(0,1fr); gap:12px; }}
.shgrid.two {{ grid-template-columns:repeat(2,minmax(0,1fr)); margin-top:12px; }}
@media (max-width: 900px) {{ .shgrid, .shgrid.two {{ grid-template-columns:minmax(0,1fr); }} }}
.shc {{ position:relative; background:{T.BOX_BG}; border:1px solid {T.BORDER}; border-radius:18px; padding:16px 18px 16px; display:flex;
  flex-direction:column; gap:8px; }}
.shc .hd {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
.shc .t {{ font-size:1.08rem; font-weight:800; color:#fff; line-height:1.3; }}
.shc .rule {{ color:#AEB8D0; font-size:.82rem; line-height:1.55; }}
.shc .big {{ font-size:1.6rem; font-weight:800; color:#fff; direction:ltr; margin-top:auto; font-variant-numeric:tabular-nums; }}
.shc .big small {{ font-size:.78rem; color:#AEB8D0; font-weight:600; margin-inline-start:6px; }}
.shchip {{ display:inline-flex; align-items:center; gap:4px; font-size:.72rem; font-weight:800; letter-spacing:.04em; padding:3px 10px; border-radius:8px; }}
.shchip.pass {{ background:{T.POS_BG}; color:{T.POS_FG}; }} .shchip.fail {{ background:{T.NEG_BG}; color:{T.NEG_FG}; }}
.shchip.doubt, .shchip.none {{ background:{T.YEL_BG}; color:{T.YEL_FG}; }}
.shbar {{ position:relative; height:10px; border-radius:6px; background:rgba(138,148,167,.2); direction:ltr; margin-top:4px; }}
.shbar i {{ position:absolute; left:0; top:0; bottom:0; border-radius:6px; }}
.shbar b {{ position:absolute; top:-4px; bottom:-4px; width:2px; background:#fff; border-radius:2px; }}
.shbar + .sc {{ display:flex; justify-content:space-between; font-size:.68rem; color:#8E9BC0; direction:ltr; }}
.shrev {{ display:grid; grid-template-columns:minmax(150px,200px) minmax(0,1fr); gap:18px 34px; align-items:center; margin-top:6px; }}
@media (max-width: 700px) {{ .shrev {{ grid-template-columns:minmax(0,1fr); justify-items:center; }} }}
.shrev svg {{ width:100%; max-width:200px; height:auto; }}
.shleg {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
@media (max-width: 1100px) {{ .shleg {{ grid-template-columns:minmax(0,1fr); }} }}
.shleg .it {{ display:flex; align-items:stretch; gap:12px; }}
.shleg .it i {{ width:6px; border-radius:4px; flex:none; }}
.shleg .it span {{ display:block; font-size:.72rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:#AEB8D0; }}
.shleg .it b {{ display:block; font-size:1.35rem; color:#fff; direction:ltr; text-align:start; font-variant-numeric:tabular-nums; }}
.shnote {{ color:#AEB8D0; font-size:.76rem; line-height:1.6; margin-top:10px; }}
.ar .shleg .it span {{ letter-spacing:0; font-size:.8rem; }}
</style>"""

_TILE = ("M30 6 L36 24 L54 30 L36 36 L30 54 L24 36 L6 30 L24 24 Z "
         "M13 13 L30 20 L47 13 L40 30 L47 47 L30 40 L13 47 L20 30 Z M0 0 L13 13 M60 0 L47 13 M0 60 L13 47 M60 60 L47 47")


def _pattern(color, pid):
    return (f'<div class="patw"><svg aria-hidden="true"><defs><pattern id="{pid}" width="60" height="60" patternUnits="userSpaceOnUse">'
            f'<path d="{_TILE}" fill="none" stroke="{color}" stroke-opacity=".5" stroke-width="1.1"/></pattern></defs>'
            f'<rect width="100%" height="100%" fill="url(#{pid})"/></svg></div><div class="fade"></div>')


def _icon(state):
    col = {"pass": HALAL, "fail": HARAM}.get(state, DOUBT)
    mark = {"pass": '<path d="M36 46 l4 4 l8 -8" fill="none" stroke="#06200F" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>',
            "fail": '<path d="M38 40 l8 8 M46 40 l-8 8" fill="none" stroke="#2A0707" stroke-width="3" stroke-linecap="round"/>'}.get(
        state, '<path d="M42 38 v6 M42 48 v1" fill="none" stroke="#2A1D04" stroke-width="3" stroke-linecap="round"/>')
    return (f'<svg class="ic" viewBox="0 0 56 56" aria-hidden="true">'
            f'<path d="M26 3 L31 9 L39 7 L40 15 L48 18 L44 25 L49 32 L41 35 L40 43 L32 41 L27 48 L21 42 L13 45 L12 37 L4 34 L8 27 L3 20 '
            f'L11 17 L12 9 L20 11 Z" fill="none" stroke="#DCE4F7" stroke-width="2" stroke-linejoin="round"/>'
            f'<path d="M30 16 A11 11 0 1 0 30 36 A8.5 8.5 0 1 1 30 16 Z" fill="#DCE4F7"/>'
            f'<path d="M33 22 l1.2 2.6 2.8 .3 -2.1 1.9 .6 2.8 -2.5 -1.4 -2.5 1.4 .6 -2.8 -2.1 -1.9 2.8 -.3 Z" fill="#DCE4F7"/>'
            f'<circle cx="42" cy="44" r="10" fill="{col}"/>{mark}</svg>')


def _chip(state):
    txt = {"pass": L("PASS", "مطابق"), "fail": L("FAIL", "غير مطابق"), "doubt": L("CHECK", "مشكوك"), None: L("NO DATA", "بيانات ناقصة"),
           "unknown": L("NO DATA", "بيانات ناقصة")}[state]
    return f'<span class="shchip {state or "none"}">{txt}</span>'


def _donut(halal, doubt, haram):
    r, c = 62, 2 * np.pi * 62
    parts, off, gap = [], 0.0, 1.2
    for v, col in ((halal, HALAL), (doubt, DOUBT), (haram, HARAM)):
        if v <= 0:
            continue
        ln = max(c * v / 100 - (gap if v < 100 else 0), 1.2)
        parts.append(f'<circle cx="80" cy="80" r="{r}" fill="none" stroke="{col}" stroke-width="20" stroke-dasharray="{ln:.2f} {c:.2f}" '
                     f'stroke-dashoffset="{-off:.2f}" transform="rotate(-90 80 80)"/>')
        off += c * v / 100
    return (f'<svg viewBox="0 0 160 160" aria-hidden="true"><circle cx="80" cy="80" r="{r}" fill="none" stroke="rgba(138,148,167,.18)" '
            f'stroke-width="20"/>{"".join(parts)}</svg>')


def _ratio_card(title, rule, value, state):
    if value is None:
        body = f'<div class="big">—</div>'
    else:
        top = RATIO_MAX * 2
        w = max(0.0, min(100.0, value / top * 100))
        col = HALAL if state == "pass" else HARAM
        body = (f'<div class="big">{value:.2f}%</div><div class="shbar"><i style="width:{w:.1f}%;background:{col}"></i>'
                f'<b style="left:calc({RATIO_MAX / top * 100:.0f}% - 1px)"></b></div>'
                f'<div class="sc"><span>0%</span><span dir="{"rtl" if is_ar() else "ltr"}">{L("limit", "الحد")} \u2066{RATIO_MAX:.0f}%\u2069</span>'
                f'<span>{top:.0f}%</span></div>')
    return f'<div class="shc"><div class="hd">{_chip(state)}</div><div class="t">{title}</div><div class="rule">{rule}</div>{body}</div>'


def section(sym, industry=None):
    """The Sharia compliance block of one company."""
    ui.sec("mosque", "Sharia compliance", "التوافق مع الشريعة")
    r = screen(sym)
    if r is None:
        st.caption(L("Yahoo Finance sent no financial statements for this company right now; the screen is tried again on the next view.",
                     "ياهو فاينانس ما أرسل القوائم المالية لهذه الشركة الحين، والفحص ينعاد مع الفتح القادم."))
        return
    if r.get("kind") != "EQUITY":
        st.caption(L("The Sharia screen is for company shares (not funds, indices or crypto).",
                     "فحص التوافق الشرعي للأسهم فقط (ما يشمل الصناديق والمؤشرات والعملات الرقمية)."))
        return
    state, checks = verdict(r)
    head = {"pass": L("Halal", "حلال"), "fail": L("Not halal", "غير حلال"), "doubt": L("Doubtful", "مشكوك فيه")}[state]
    sub = {"pass": L("Passes all four checks below.", "يجتاز الفحوص الأربعة تحت."),
           "fail": L("Fails at least one of the checks below.", "ما يجتاز فحصاً واحداً على الأقل من الفحوص تحت."),
           "doubt": L("A check could not be completed or the business needs a closer look.",
                      "فيه فحص ما اكتمل أو نشاط الشركة يحتاج نظرة أدق.")}[state]
    edge = {"pass": T.UP_EDGE, "fail": T.DN_EDGE}.get(state, T.GOLD)
    line = {"pass": "linear-gradient(90deg,#16A34A,#4ADE80)", "fail": "linear-gradient(90deg,#DC2626,#F87171)"}.get(
        state, f"linear-gradient(90deg,#D97706,{T.GOLD})")
    glow = {"pass": "rgba(34,197,94,.16)", "fail": "rgba(239,68,68,.16)"}.get(state, "rgba(245,185,74,.14)")
    pat = {"pass": "#22C55E", "fail": "#EF4444"}.get(state, T.GOLD)
    ar = " ar" if is_ar() else ""
    banner = (f'<div class="shbn{ar}" style="--edge:{edge};--line:{line};--glow:{glow}">{_pattern(pat, f"shpat_{state}")}{_icon(state)}'
              f'<div class="v">{head}</div><div class="s">{sub}</div></div>')
    # revenue breakdown
    if r.get("rev") is not None:
        rev = (f'<div class="shrev">{_donut(r["halal"], r["doubt"], r["haram"])}<div class="shleg">'
               + "".join(f'<div class="it"><i style="background:{col}"></i><div><span>{lab}</span><b>{v:.2f}%</b></div></div>'
                         for lab, v, col in ((L("Halal", "حلال"), r["halal"], HALAL), (L("Doubtful", "مشكوك فيه"), r["doubt"], DOUBT),
                                             (L("Not halal", "غير حلال"), r["haram"], HARAM)))
               + "</div></div>")
    else:
        rev = f'<div class="rule">{L("No revenue figure from Yahoo Finance.", "ما فيه رقم إيرادات من ياهو فاينانس.")}</div>'
    rev_card = (f'<div class="shc"><div class="hd"><div class="t">{L("Revenue breakdown", "تفصيل الإيرادات")}</div>{_chip(checks["revenue"])}</div>'
                f'<div class="rule">{L(f"Income that is not halal plus doubtful income must stay under {REV_MAX:.0f}% of total revenue.", f"الإيرادات غير الحلال والمشكوك فيها لازم تكون أقل من {REV_MAX:.0f}% من إجمالي الإيرادات.")}</div>{rev}</div>')
    ind = industry or r.get("industry")
    biz_txt = {"pass": L("The main business is permissible.", "النشاط الرئيسي مباح."),
               "fail": L("The main business is not permissible (such as conventional banking, insurance, alcohol, tobacco or gambling).",
                         "النشاط الرئيسي غير مباح (مثل البنوك التقليدية أو التأمين أو الكحول أو التبغ أو القمار)."),
               "doubt": L("A financial business: it needs a closer look.", "نشاط مالي يحتاج نظرة أدق."),
               "unknown": L("Yahoo Finance gives no industry for this company.", "ياهو فاينانس ما يعطي صناعة لهذه الشركة.")}[checks["business"]]
    biz = (f'<div class="shc"><div class="hd">{_chip(checks["business"])}</div><div class="t">{L("Business activity", "نشاط الشركة")}</div>'
           f'<div class="rule">{biz_txt}</div><div class="big" style="font-size:1.05rem">{T.esc(industry_name(ind) if ind else "—")}</div></div>')
    months = r.get("months") or 0
    base = (L(f"of the {months}-month average market cap", f"من متوسط القيمة السوقية لآخر {months} شهر") if months
            else L("of today's market cap", "من القيمة السوقية الحالية"))
    sec_card = _ratio_card(L("Interest-bearing securities &amp; assets", "الأوراق والأصول بفائدة"),
                           L(f"Cash and short-term investments must be under {RATIO_MAX:.0f}% {base}.",
                             f"النقد والاستثمارات قصيرة الأجل لازم تكون أقل من {RATIO_MAX:.0f}% {base}."), r.get("sec"), checks["sec"])
    debt_card = _ratio_card(L("Interest-bearing debt", "الديون بفائدة"),
                            L(f"Total debt must be under {RATIO_MAX:.0f}% {base}.", f"إجمالي الديون لازم يكون أقل من {RATIO_MAX:.0f}% {base}."),
                            r.get("debt"), checks["debt"])
    note = L("An educational screen with AAOIFI-style thresholds on Yahoo Finance's latest annual statements, not a religious ruling (fatwa); "
             "screening providers and scholars can differ. Not halal = interest income; doubtful = other non-operating income whose source "
             "isn't disclosed. The average market cap uses today's share count.",
             "فحص تعليمي بحدود مشابهة لمعايير هيئة المحاسبة والمراجعة للمؤسسات المالية الإسلامية (AAOIFI) على آخر قوائم سنوية من ياهو فاينانس، "
             "وليس فتوى؛ وقد تختلف جهات الفحص والعلماء. غير الحلال = إيرادات الفوائد، والمشكوك فيه = إيرادات أخرى من خارج النشاط "
             "مصدرها غير معلن. متوسط القيمة السوقية محسوب بعدد الأسهم الحالي.")
    ui.html(CSS + f'<div class="{ar.strip()}">{banner}<div class="shgrid">{rev_card}{biz}</div><div class="shgrid two">{sec_card}{debt_card}</div>'
            f'<div class="shnote">{note}</div></div>')
