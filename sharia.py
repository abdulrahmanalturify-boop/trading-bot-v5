"""
sharia.py - Sharia compliance of a company share, in the site's style (stock page, Company tab).

An educational screen with the usual AAOIFI-style thresholds, computed from Yahoo Finance data:
  1. Business activity: the main business must be permissible (no conventional banking, commercial insurance, alcohol, tobacco,
     gambling ...).
  2. Revenue: income that is not halal (interest income) plus doubtful income (other non-operating income whose source is not
     disclosed) must stay under 5% of total revenue.
  3. Interest-bearing securities & assets (cash and short-term investments) under 30% of the 36-month average market cap.
  4. Interest-bearing debt under 30% of the 36-month average market cap.
It is not a religious ruling; screening providers and scholars can differ.

The Saudi market is read by its own rules, not by Yahoo's English industry name (which puts every bank and insurer in one box):
  - Islamic banks (Al Rajhi, Albilad, Alinma, AlJazira): all their business under their own Sharia boards, so they pass; the
    ratio tests don't apply to a bank's deposits and financing (Yahoo even calls their financing profit "interest income").
  - insurance is cooperative by law, and cooperative insurance is permitted in principle (the Council of Senior Scholars), but
    Sharia lists accept some insurers and not others by how each one works and invests: "check a Sharia list", never "not halal".
  - finance companies must finance in a way that does not conflict with Sharia (Finance Companies Control Law, Article 3), under
    their own Sharia committees: "check a Sharia list" as well.
  - there are no casinos in the kingdom: "Resorts & Casinos" there is tourism.

A Saudi company on the Sharia boards' lists (sharia_lists.json, read weekly by scripts/build_sharia.py) is judged by those
lists first: Al Rajhi Capital's and Albilad Capital's lists of permitted shares, and the Almaqased Center's yearly study (Dr.
Mohammed Al-Osaimi) with its class (pure, mixed, not compliant) and its purification amount per share. The site's own screen
stays under them as the detail. Any other company gets the site's own estimate of the purification amount: its interest income
over its shares.
"""
import json
import os

import numpy as np
import pandas as pd
import streamlit as st

import data
import theme as T
import ui
from i18n import L, industry_name, is_ar

BUILD = "23.4.55"

REV_MAX, RATIO_MAX = 5.0, 30.0
HALAL, DOUBT, HARAM = "#4ADE80", "#F5B94A", "#F87171"

# industries whose main business is not permissible, and ones that need a closer look (Yahoo's industry names, lower case)
NOT_OK = ("bank", "insurance", "credit services", "mortgage finance", "brewers", "winer", "distill", "tobacco", "gambling", "casino")
DOUBTFUL = ("capital markets", "asset management", "financial conglomerates", "reit - mortgage", "shell companies")

# the Saudi market (see the top of the file): the Islamic banks by their codes, the rest by their industry
SA_ISLAMIC_BANKS = {"1120.SR": "Al Rajhi Bank", "1140.SR": "Bank Albilad", "1150.SR": "Alinma Bank", "1020.SR": "Bank AlJazira"}
SA_INSURANCE = ("insurance",)                                 # insurers, reinsurers and insurance brokers
SA_FINANCE = ("credit services", "mortgage finance")
SA_TOURISM = ("resorts & casinos", "resorts and casinos")
SPECIAL = ("islamic", "coop", "finance")                     # read by the Saudi rules: the ratio tests don't apply


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


def business(industry, sym=""):
    """'pass', 'fail', 'doubt' or 'unknown'; in the Saudi market also 'islamic' (an Islamic bank), 'coop' (cooperative insurance)
    and 'finance' (a finance company)."""
    ind = str(industry or "").lower().replace("—", " - ").replace("–", " - ")
    s = str(sym or "").strip().upper()
    if s in SA_ISLAMIC_BANKS:
        return "islamic"
    if not ind:
        return "unknown"
    if s.endswith(".SR"):
        if any(k in ind for k in SA_INSURANCE):
            return "coop"
        if any(k in ind for k in SA_FINANCE):
            return "finance"
        if any(k in ind for k in SA_TOURISM):
            return "pass"
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
    out = {"kind": "EQUITY", "industry": p.get("industry"), "sector": p.get("sector"), "business": business(p.get("industry"), sym)}
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
    # the purification estimate: the year's interest income over the shares (the whole income that is not halal, as the
    # Almaqased study purifies it), in the company's reporting currency
    if shares and intr and intr > 0:
        out["purify"] = float(intr) / float(shares)
        out["cur"] = inf.get("financialCurrency") or inf.get("currency")
    return out


def screen(sym):
    try:
        return _screen(sym)
    except Exception:
        return None


def verdict(r):
    """'pass' (halal), 'fail' (not halal) or 'doubt' (a doubtful business or missing data) with the four checks.
    The Saudi market's Islamic banks pass, its cooperative insurers and finance companies are 'doubt' ("check a Sharia list"),
    and their three ratio checks are 'na' (they don't apply)."""
    biz = r.get("business", "unknown")
    if biz in SPECIAL:
        checks = {"business": "pass" if biz in ("islamic", "finance") else "doubt", "revenue": "na", "sec": "na", "debt": "na"}
        return ("pass" if biz == "islamic" else "doubt"), checks
    checks = {"business": biz,
              "revenue": None if r.get("rev") is None else ("pass" if r["haram"] + r["doubt"] < REV_MAX else "fail"),
              "sec": None if r.get("sec") is None else ("pass" if r["sec"] < RATIO_MAX else "fail"),
              "debt": None if r.get("debt") is None else ("pass" if r["debt"] < RATIO_MAX else "fail")}
    if "fail" in checks.values():
        return "fail", checks
    if None in checks.values() or "doubt" in checks.values() or "unknown" in checks.values():
        return "doubt", checks
    return "pass", checks


# ---------------------------------------------------------------- the Saudi market's Sharia lists (sharia_lists.json)
LISTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sharia_lists.json")
_LISTS = {"mtime": None, "doc": {}}
BOARD_ORDER = ("rajhi", "bilad", "osaimi")
BOARD_NAMES = {"rajhi": ("Al Rajhi Capital's Sharia board", "الهيئة الشرعية في الراجحي المالية"),
               "bilad": ("Albilad Capital's Sharia board", "الهيئة الشرعية في البلاد المالية"),
               "osaimi": ("Almaqased · Dr. Mohammed Al-Osaimi", "المقاصد · د. محمد بن سعود العصيمي")}
# Almaqased's classes -> the state they count as (a mixed company is allowed by the scholars who allow mixed companies, with
# purification: it counts as neither)
OSAIMI_STATE = {"pure": "pass", "public": "pass", "mixed": "mixed", "not": "fail", "activity": "fail"}
MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def lists():
    """The lists' file ({} when missing), read again when it changes."""
    try:
        m = os.path.getmtime(LISTS_FILE)
    except OSError:
        return {}
    if _LISTS["mtime"] != m:
        try:
            with open(LISTS_FILE, encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, ValueError):
            return _LISTS["doc"]
        _LISTS["doc"], _LISTS["mtime"] = doc, m
    return _LISTS["doc"]


def boards(sym):
    """{"states": {board: pass / fail / mixed / none}, "osaimi": class or None, "purify": riyals per share a year or None,
    "verdict": pass / fail / doubt, "yes": boards that pass it, "known": boards with a verdict}, or None when the company isn't
    in the lists (any non-Saudi symbol, a Saudi one listed after them)."""
    s = str(sym or "").strip().upper()
    if not s.endswith(".SR"):
        return None
    it = (lists().get("items") or {}).get(s)
    if not it:
        return None
    states = {"rajhi": None if it.get("rajhi") is None else ("pass" if it["rajhi"] else "fail"),
              "bilad": None if it.get("bilad") is None else ("pass" if it["bilad"] else "fail"),
              "osaimi": OSAIMI_STATE.get(it.get("osaimi"))}
    known = [b for b in BOARD_ORDER if states[b]]
    if not known:
        return None
    yes = [b for b in known if states[b] == "pass"]
    v = "pass" if len(yes) == len(known) else ("fail" if all(states[b] == "fail" for b in known) else "doubt")
    return {"states": states, "osaimi": it.get("osaimi"), "purify": it.get("purify"), "verdict": v, "yes": yes, "known": known}


def _date(iso, month_only=False):
    """'2026-03-31' -> 31 Mar 2026 / 31 مارس 2026 (month_only: Mar 2026)."""
    try:
        y, m, d = (int(x) for x in str(iso)[:10].split("-"))
    except (TypeError, ValueError):
        return "—"
    mon = MONTHS_AR[m - 1] if is_ar() else MONTHS_EN[m - 1]
    return f"{mon} {y}" if month_only else f"{d} {mon} {y}"


# ---------------------------------------------------------------- the look
CSS = f"""<style>
.shbn {{ position:relative; overflow:hidden; border-radius:18px; border:1px solid var(--edge); min-height:132px; display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:4px; margin:4px 0 14px; background:var(--line) top / 100% 3px no-repeat,
  radial-gradient(420px 150px at 50% 55%, var(--glow), transparent 70%), {T.CARD}; }}
.shbn .patw {{ position:absolute; inset:0; pointer-events:none;
  -webkit-mask-image:linear-gradient(90deg,#000 0%,rgba(0,0,0,.85) 18%,transparent 36%,transparent 64%,rgba(0,0,0,.85) 82%,#000 100%);
  mask-image:linear-gradient(90deg,#000 0%,rgba(0,0,0,.85) 18%,transparent 36%,transparent 64%,rgba(0,0,0,.85) 82%,#000 100%); }}
.shbn .patw svg {{ width:100%; height:100%; display:block; }}
.shbn .fade {{ position:absolute; inset:0; pointer-events:none; background:radial-gradient(34% 90% at 50% 50%, {T.CARD} 0%, rgba(26,22,36,.92) 45%, transparent 100%); }}
.shbn .ic {{ position:relative; width:54px; height:54px; }}
.shbn .v {{ position:relative; font-size:1.55rem; font-weight:600; color:#fff; letter-spacing:-.01em; line-height:1.45; text-align:center;
  padding:0 12px; }}
.shbn {{ padding:12px 0; }}
@media (max-width: 560px) {{ .shbn .v {{ font-size:1.3rem; }} }}
.shbn .s {{ position:relative; font-size:.8rem; color:#CCC7D8; text-align:center; max-width:520px; padding:0 12px; }}
.shgrid {{ display:grid; grid-template-columns:minmax(0,2fr) minmax(0,1fr); gap:12px; }}
.shgrid.two {{ grid-template-columns:repeat(2,minmax(0,1fr)); margin-top:12px; }}
@media (max-width: 900px) {{ .shgrid, .shgrid.two {{ grid-template-columns:minmax(0,1fr); }} }}
.shc {{ position:relative; background:{T.BOX_BG}; border:1px solid {T.BORDER}; border-radius:18px; padding:16px 18px 16px; display:flex;
  flex-direction:column; gap:8px; }}
.shc .hd {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
.shc .t {{ font-size:1.08rem; font-weight:600; color:#fff; line-height:1.3; }}
.shc .rule {{ color:#B1ABBF; font-size:.82rem; line-height:1.55; }}
.shc .big {{ font-size:1.6rem; font-weight:600; color:#fff; direction:ltr; margin-top:auto; font-variant-numeric:tabular-nums; }}
.shc .big small {{ font-size:.78rem; color:#B1ABBF; font-weight:600; margin-inline-start:6px; }}
.shchip {{ display:inline-flex; align-items:center; gap:4px; font-size:.72rem; font-weight:600; letter-spacing:.04em; padding:3px 10px; border-radius:8px; }}
.shchip.pass {{ background:{T.POS_BG}; color:{T.POS_FG}; }} .shchip.fail {{ background:{T.NEG_BG}; color:{T.NEG_FG}; }}
.shchip.doubt, .shchip.none {{ background:{T.YEL_BG}; color:{T.YEL_FG}; }}
.shchip.na {{ background:rgba(157,151,165,.18); color:#CFCADB; }}
.shbar {{ position:relative; height:10px; border-radius:6px; background:rgba(157,151,165,.2); direction:ltr; margin-top:4px; }}
.shbar i {{ position:absolute; left:0; top:0; bottom:0; border-radius:6px; }}
.shbar b {{ position:absolute; top:-4px; bottom:-4px; width:2px; background:#fff; border-radius:2px; }}
.shbar + .sc {{ display:flex; justify-content:space-between; font-size:.68rem; color:#9791AD; direction:ltr; }}
.shrev {{ display:grid; grid-template-columns:minmax(150px,200px) minmax(0,1fr); gap:18px 34px; align-items:center; margin-top:6px; }}
@media (max-width: 700px) {{ .shrev {{ grid-template-columns:minmax(0,1fr); justify-items:center; }} }}
.shrev svg {{ width:100%; max-width:200px; height:auto; }}
.shleg {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
@media (max-width: 1100px) {{ .shleg {{ grid-template-columns:minmax(0,1fr); }} }}
.shleg .it {{ display:flex; align-items:stretch; gap:12px; }}
.shleg .it i {{ width:6px; border-radius:4px; flex:none; }}
.shleg .it span {{ display:block; font-size:.72rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:#B1ABBF; }}
.shleg .it b {{ display:block; font-size:1.35rem; color:#fff; direction:ltr; text-align:start; font-variant-numeric:tabular-nums; }}
.shnote {{ color:#B1ABBF; font-size:.76rem; line-height:1.6; margin-top:10px; }}
.ar .shleg .it span {{ letter-spacing:0; font-size:.8rem; }}
.shgrid.three {{ grid-template-columns:repeat(3,minmax(0,1fr)); margin-bottom:12px; }}
@media (max-width: 900px) {{ .shgrid.three {{ grid-template-columns:minmax(0,1fr); }} }}
.shc .dt {{ color:#9791AD; font-size:.74rem; margin-top:auto; padding-top:4px; }}
.shc .dt a {{ color:#79B8F4; text-decoration:none; }}
.shpur {{ margin-bottom:10px; }}
.shpur .big {{ margin-top:2px; }}
.shpur .big[dir="rtl"] {{ direction:rtl; text-align:start; }}
.shres {{ display:flex; align-items:baseline; justify-content:space-between; gap:12px; flex-wrap:wrap; background:{T.POS_BG};
  border:1px solid {T.UP_EDGE}; border-radius:14px; padding:12px 16px; margin:2px 0 6px; }}
.shres > span {{ color:#CCC7D8; font-size:.84rem; }}
.shres b {{ color:{T.POS_FG}; font-size:1.35rem; font-weight:600; font-variant-numeric:tabular-nums; }}
.shsub {{ display:flex; align-items:center; gap:8px; color:#DFDAE8; font-size:.98rem; font-weight:600; margin:20px 0 8px; }}
.shsub .ms {{ color:#A78BFA; font-size:1.15rem; }}
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
            f'L11 17 L12 9 L20 11 Z" fill="none" stroke="#DFDAE8" stroke-width="2" stroke-linejoin="round"/>'
            f'<path d="M30 16 A11 11 0 1 0 30 36 A8.5 8.5 0 1 1 30 16 Z" fill="#DFDAE8"/>'
            f'<path d="M33 22 l1.2 2.6 2.8 .3 -2.1 1.9 .6 2.8 -2.5 -1.4 -2.5 1.4 .6 -2.8 -2.1 -1.9 2.8 -.3 Z" fill="#DFDAE8"/>'
            f'<circle cx="42" cy="44" r="10" fill="{col}"/>{mark}</svg>')


def _chip(state, txt=None):
    txt = txt or {"pass": L("PASS", "مطابق"), "fail": L("FAIL", "غير مطابق"), "doubt": L("CHECK", "مشكوك"), None: L("NO DATA", "بيانات ناقصة"),
                  "unknown": L("NO DATA", "بيانات ناقصة"), "na": L("N/A", "لا ينطبق")}[state]
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
    return (f'<svg viewBox="0 0 160 160" aria-hidden="true"><circle cx="80" cy="80" r="{r}" fill="none" stroke="rgba(157,151,165,.18)" '
            f'stroke-width="20"/>{"".join(parts)}</svg>')


def _ratio_card(title, rule, value, state, why=""):
    if state == "na":                           # a test that doesn't apply: why, in place of the figure
        body = f'<div class="rule" style="color:#DFDAE8">{why}</div>'
    elif value is None:
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


def _special(kind):
    """The words for a Saudi Islamic bank, cooperative insurer or finance company: head, sub, business, revenue, ratios."""
    if kind == "islamic":
        return (L("Halal", "حلال"),
                L("An Islamic bank: all of its business runs under its own Sharia board.", "بنك إسلامي: كل أعماله تحت إشراف هيئته الشرعية."),
                L("An Islamic bank: deposits and financing in Sharia forms (murabaha, ijara and others), under its own Sharia board.",
                  "بنك إسلامي: الودائع والتمويل بصيغ شرعية (مرابحة وإجارة وغيرها)، تحت إشراف هيئته الشرعية."),
                L("Doesn't apply: Yahoo Finance calls an Islamic bank's financing profit “interest income”, but it is profit from Sharia financing.",
                  "ما ينطبق: ياهو فاينانس يسمّي أرباح تمويل البنك الإسلامي «إيرادات فوائد»، وهي أرباح تمويل بصيغ شرعية."),
                L("Doesn't apply to a bank: its cash, deposits and financing are its business itself, in Sharia forms.",
                  "ما ينطبق على البنك: النقد والودائع والتمويل هي عمله نفسه، وتكون بصيغ شرعية."))
    if kind == "coop":
        return (L("Check a Sharia list", "راجع قائمة شرعية"),
                L("Cooperative insurance is permitted in principle, but Sharia lists differ on each insurer.",
                  "التأمين التعاوني جائز من حيث الأصل، لكن القوائم الشرعية تختلف في الحكم على كل شركة."),
                L("Insurance, or a business built on it: insurance in Saudi Arabia is cooperative by law, and the Council of Senior Scholars "
                  "permitted cooperative insurance. Sharia lists still accept some insurers and not others, by how each one works and invests.",
                  "تأمين أو نشاط مرتبط فيه: التأمين في السعودية تعاوني بحكم النظام، وهيئة كبار العلماء أجازت التأمين التعاوني. ومع ذلك "
                  "القوائم الشرعية تقبل شركات وترفض شركات، حسب طريقة عمل كل شركة واستثماراتها."),
                L("Doesn't apply as a test here: an insurer's income from its deposits and investments is part of its work, and its form is "
                  "what the Sharia lists check.",
                  "ما ينطبق كاختبار هنا: دخل شركة التأمين من ودائعها واستثماراتها جزء من عملها، وصيغته هي اللي تفحصها القوائم الشرعية."),
                L("Doesn't apply as a test here: an insurer holds large cash and investments by the nature of its work, and whether they "
                  "are in Sharia forms is what the Sharia lists check.",
                  "ما ينطبق كاختبار هنا: شركة التأمين تحتفظ بنقد واستثمارات كبيرة بحكم عملها، وهل هي بصيغ شرعية هذا اللي تفحصه القوائم الشرعية."))
    return (L("Check a Sharia list", "راجع قائمة شرعية"),
            L("A finance company: the law requires its financing to agree with Sharia, and Sharia lists judge each company.",
              "شركة تمويل: النظام يلزمها بتمويل ما يتعارض مع الشريعة، والحكم على كل شركة للقوائم الشرعية."),
            L("A finance company: the Finance Companies Control Law (Article 3) requires its financing not to conflict with Sharia, "
              "under its own Sharia committee.",
              "شركة تمويل: نظام مراقبة شركات التمويل (المادة الثالثة) يلزمها إن تمويلها ما يتعارض مع أحكام الشريعة، تحت إشراف لجنتها الشرعية."),
            L("Doesn't apply as a test here: a finance company's income is the profit on its financing, and its form is what the "
              "Sharia lists check.",
              "ما ينطبق كاختبار هنا: دخل شركة التمويل هو ربح تمويلها، وصيغته هي اللي تفحصها القوائم الشرعية."),
            L("Doesn't apply as a test here: lending, and the funding behind it, is a finance company's business; its form is what "
              "the Sharia lists check.",
              "ما ينطبق كاختبار هنا: التمويل والاقتراض اللي وراه هو عمل شركة التمويل، وصيغته هي اللي تفحصها القوائم الشرعية."))


def _banner(state, head, sub):
    edge = {"pass": T.UP_EDGE, "fail": T.DN_EDGE}.get(state, T.GOLD)
    line = {"pass": "linear-gradient(90deg,#16A34A,#4ADE80)", "fail": "linear-gradient(90deg,#DC2626,#F87171)"}.get(
        state, f"linear-gradient(90deg,#D97706,{T.GOLD})")
    glow = {"pass": "rgba(34,197,94,.16)", "fail": "rgba(239,68,68,.16)"}.get(state, "rgba(245,185,74,.14)")
    pat = {"pass": "#22C55E", "fail": "#EF4444"}.get(state, T.GOLD)
    ar = " ar" if is_ar() else ""
    return (f'<div class="shbn{ar}" style="--edge:{edge};--line:{line};--glow:{glow}">{_pattern(pat, f"shpat_{state}")}{_icon(state)}'
            f'<div class="v">{head}</div><div class="s">{sub}</div></div>')


SHORT = {"rajhi": ("Al Rajhi Capital", "الراجحي المالية"), "bilad": ("Albilad Capital", "البلاد المالية"), "osaimi": ("Almaqased", "المقاصد")}


def _and(names):
    names = list(names)
    if len(names) <= 1:
        return "".join(names)
    return ("، ".join(names[:-1]) + " و" + names[-1]) if is_ar() else (", ".join(names[:-1]) + " and " + names[-1])


def _lists_banner(bd):
    v, yes, known = bd["verdict"], bd["yes"], bd["known"]
    n, k = len(known), len(yes)
    if v == "pass":
        return _banner("pass", L("Sharia compliant", "متوافقة شرعياً"),
                       L(f"Permitted on every Sharia list below ({n} of {n}).", f"متوافقة في كل القوائم الشرعية تحت ({n} من {n})."))
    if v == "fail":
        return _banner("fail", L("Not Sharia compliant", "غير متوافقة شرعياً"),
                       L("None of the Sharia lists below permits it.", "ما تجيزها أي قائمة من القوائم الشرعية تحت."))
    sub = (L(f"Permitted on {k} of {n} lists: {_and(L(*SHORT[b]) for b in yes)}.",
             f"متوافقة في {k} من {n} قوائم: {_and(L(*SHORT[b]) for b in yes)}.") if k else
           L("No list below permits it outright.", "ما تجيزها أي قائمة تحت إجازة صريحة."))
    if bd["osaimi"] == "mixed":
        sub += L(" Almaqased classes it as mixed.", " والمقاصد يصنّفها مختلطة.")
    return _banner("doubt", L("The Sharia lists differ", "القوائم الشرعية تختلف فيها"), sub)


def _bank_or_insurer(sym, industry):
    """A bank or an insurer: by the exchange's own industry group, else by Yahoo's industry."""
    import tasi
    if tasi.known(sym):
        return tasi.group_of(sym) in ("banks", "insurance")
    ind = str(industry or "").lower()
    return str(sym).upper() in SA_ISLAMIC_BANKS or "bank" in ind or "insurance" in ind


def _board_card(b, bd, src, sym, industry):
    stt = bd["states"][b]
    if b == "osaimi":
        c = bd["osaimi"]
        chip = {"pure": ("pass", L("PURE", "نقية")), "public": ("pass", L("PUBLIC SECTOR", "قطاع عام")),
                "mixed": ("doubt", L("MIXED", "مختلطة")), "not": ("fail", L("NOT COMPLIANT", "غير متوافقة")),
                "activity": ("fail", L("NOT PERMISSIBLE", "محرمة النشاط"))}.get(c, ("na", L("NOT STUDIED", "لم تُدرس")))
        rule = {"pure": L("Pure: a permissible business with no forbidden investments or financing (a small slip may still need "
                          "purifying).", "نقية: نشاطها مباح، وما عندها استثمارات ولا تمويلات محرمة (وقد يكون فيها شيء يسير يُطهَّر)."),
                "public": L("The public sector: mostly owned by the state, so it is permitted without these tests; what needs purifying is "
                            "still purified (the methodology, paragraph 17).",
                            "قطاع عام: أغلب ملكيتها للدولة، فيجوز تملكها بدون تطبيق هذه الضوابط، مع تطهير ما يجب تطهيره (المنهجية، فقرة 17)."),
                "mixed": L("Mixed: a permissible business, but with non-Sharia financing or investments of no more than a third of its "
                           "assets and forbidden income under 5% of its revenue. Permitted by the scholars who allow mixed companies, "
                           "with purification.",
                           "مختلطة: نشاطها مباح، لكن عندها تمويل أو استثمار غير شرعي ما يتجاوز ثلث موجوداتها، ودخل محرم أقل من 5% من "
                           "إيراداتها. يجيزها من يجيز الشركات المختلطة، مع التطهير."),
                "not": L("Not compliant: a permissible business, but its forbidden financing or investments pass a third of its assets, "
                         "or its forbidden income passes 5% of its revenue.",
                         "غير متوافقة: نشاطها مباح، لكن تمويلها أو استثمارها المحرم تجاوز ثلث موجوداتها، أو دخلها المحرم تجاوز 5% من إيراداتها."),
                "activity": L("Its business itself is not permissible.", "نشاطها نفسه غير مباح.")}.get(c)
        if rule is None:
            rule = (L("The study leaves out the commercial banks and the insurers: their own Sharia boards study them.",
                      "الدراسة ما تشمل البنوك التجارية وشركات التأمين، لأن لها هيئاتها الشرعية اللي تدرسها.")
                    if _bank_or_insurer(sym, industry) else
                    L(f"Not in the study of {src.get('year') or ''}: most likely listed after it.",
                      f"ما شملتها دراسة {src.get('year') or ''}: غالباً أُدرجت بعدها."))
        when = L(f"Study of {src.get('year')} · published {_date(src.get('date'), True)}",
                 f"دراسة عام {src.get('year')} · نُشرت {_date(src.get('date'), True)}")
    else:
        chip = (("pass", L("PERMITTED", "مجازة")) if stt == "pass" else ("fail", L("NOT ON THE LIST", "غير مدرجة")))
        rule = (L("On the board's list of permitted shares.", "موجودة في قائمة الأسهم المجازة عند الهيئة.") if stt == "pass" else
                L("Not on the board's list of permitted shares.", "مو موجودة في قائمة الأسهم المجازة عند الهيئة."))
        when = L(f"List of {_date(src.get('date'))}", f"قائمة {_date(src.get('date'))}")
    url = src.get("url")
    link = f' · <a href="{T.esc(url)}" target="_blank">{L("Source", "المصدر")}</a>' if url else ""
    return (f'<div class="shc"><div class="hd">{_chip(chip[0], chip[1])}</div><div class="t">{L(*BOARD_NAMES[b])}</div>'
            f'<div class="rule">{rule}</div><div class="dt">{when}{link}</div></div>')


def _money(v, cur):
    if cur in ("SAR", None):                       # the number kept left to right inside the Arabic line: "0.08 ر.س"
        return f'<span dir="rtl"><bdi dir="ltr">{v:,.2f}</bdi> ر.س</span>' if is_ar() else f"SAR {v:,.2f}"
    if cur == "USD":
        return f"${v:,.2f}" if v >= 0.01 or v == 0 else f"${v:,.4f}"
    return f"{cur} {v:,.2f}"


def _purify(sym, amount, cur, title, rule):
    """The purification amount per share for a year, and a calculator: shares x amount x days held / 365."""
    big = (f'<div class="big" dir="{"rtl" if is_ar() else "ltr"}">{_money(amount, cur)} <small>{L("per share, for a year", "للسهم عن سنة")}</small></div>'
           if amount > 0 else
           f'<div class="big" style="font-size:1.1rem">{L("No purification needed", "ما يحتاج تطهير")} '
           f'<small>({_money(0, cur)})</small></div>')
    ui.html(f'<div class="shc shpur"><div class="hd">{T.icon("volunteer_activism")}<div class="t">{title}</div></div>{big}'
            f'<div class="rule">{rule}</div></div>')
    if amount <= 0:
        return
    c1, c2 = st.columns(2)
    n = c1.number_input(L("Shares you hold", "عدد أسهمك"), min_value=0, value=100, step=10, key=f"shp_n_{sym}")
    d = c2.number_input(L("Days you held them (in the year)", "أيام التملك (خلال السنة)"), min_value=1, max_value=365, value=365,
                        step=1, key=f"shp_d_{sym}")
    total = float(n) * float(amount) * float(d) / 365
    ui.html(f'<div class="shres"><span>{L(f"Purify for {int(n):,} shares over {int(d)} days", f"تطهّر عن {int(n):,} سهم لمدة {int(d)} يوم")}'
            f'</span><b>{_money(total, cur)}</b></div>')


def section(sym, industry=None):
    """The Sharia compliance block of one company: the Sharia boards' lists first (a Saudi company on them), then the site's own
    screen, and the purification amount."""
    ui.sec("mosque", "Sharia compliance", "التوافق مع الشريعة")
    bd = boards(sym)
    r = screen(sym)
    if r is None and business(industry, sym) in SPECIAL:     # the Saudi rules need no statements
        r = {"kind": "EQUITY", "industry": industry, "business": business(industry, sym)}
    if r is not None and r.get("kind") != "EQUITY":
        st.caption(L("The Sharia screen is for company shares (not funds, indices or crypto).",
                     "فحص التوافق الشرعي للأسهم فقط (ما يشمل الصناديق والمؤشرات والعملات الرقمية)."))
        return
    ar = " ar" if is_ar() else ""
    if bd:
        src = lists().get("sources") or {}
        ui.ai_note("Sharia lists", f"{bd['verdict']} - " + ", ".join(f"{b}: {bd['states'][b] or 'not studied'}" for b in BOARD_ORDER)
                   + (f"; purification {bd['purify']:.2f} SAR per share a year (Almaqased)" if bd.get("purify") is not None else ""))
        ui.html(CSS + f'<div class="{ar.strip()}">{_lists_banner(bd)}<div class="shgrid three">'
                + "".join(_board_card(b, bd, src.get(b) or {}, sym, industry or (r or {}).get("industry")) for b in BOARD_ORDER)
                + "</div></div>")
        if bd.get("purify") is not None:
            o = src.get("osaimi") or {}
            _purify(sym, float(bd["purify"]), "SAR", L("Purification amount", "مبلغ التطهير"),
                    L(f"From the Almaqased study of {o.get('year')}: the income it judged not halal, over the number of shares. Purify "
                      "shares x amount x days held / 365. It is given away to charity to be rid of it; it is not zakat or sadaqa.",
                      f"من دراسة المقاصد لعام {o.get('year')}: الدخل اللي حكمت إنه غير حلال مقسوم على عدد الأسهم. تطهّر: عدد الأسهم × "
                      "مبلغ التطهير × أيام التملك ÷ 365. ويُخرج بنية التخلص منه في أوجه البر، وما يعتبر زكاة ولا صدقة."))
        if r is None:
            _lists_note(src)
            return
        ui.html(f'<div class="shsub">{T.icon("query_stats")}{L("The site&#39;s financial screen (educational)", "فحص الموقع المالي (تعليمي)")}</div>')
        _screen_block(sym, industry, r, banner=False)
        _lists_note(src)
        return
    if r is None:
        st.caption(L("Yahoo Finance sent no financial statements for this company right now; the screen is tried again on the next view.",
                     "ياهو فاينانس ما أرسل القوائم المالية لهذه الشركة الحين، والفحص ينعاد مع الفتح القادم."))
        return
    _screen_block(sym, industry, r, banner=True)
    state, _ = verdict(r)
    if r.get("purify") is not None and r.get("business") not in SPECIAL and state != "fail":
        _purify(sym, float(r["purify"]), r.get("cur") or ("SAR" if str(sym).upper().endswith(".SR") else "USD"),
                L("Purification amount (the site's estimate)", "مبلغ التطهير (تقدير الموقع)"),
                L("An estimate from the latest annual statements: the interest income over the number of shares. Sharia lists work it "
                  "out in more detail (they also purify a part of other income whose source isn't disclosed). Purify shares x amount x "
                  "days held / 365, given away to charity to be rid of it (not zakat or sadaqa).",
                  "تقدير من آخر قوائم سنوية: إيرادات الفوائد مقسومة على عدد الأسهم. القوائم الشرعية تحسبه بتفصيل أكثر (تطهّر مثلاً جزءاً من "
                  "الإيرادات الأخرى اللي مصدرها غير معلن). تطهّر: عدد الأسهم × مبلغ التطهير × أيام التملك ÷ 365، ويُخرج بنية التخلص منه "
                  "في أوجه البر (مو زكاة ولا صدقة)."))


def _lists_note(src):
    o = src.get("osaimi") or {}
    ui.html('<div class="shnote">' + L(
        f"The Sharia boards' verdicts as they published them, not a ruling by this site: Al Rajhi Capital's and Albilad Capital's lists "
        f"of permitted shares as Argaam puts them side by side (lists of {_date((src.get('rajhi') or {}).get('date'))}), and the "
        f"Almaqased Center's study of the Saudi companies for {o.get('year')} (Dr. Mohammed bin Saud Al-Osaimi, published "
        f"{_date(o.get('date'), True)}; its results are the center's). The lists are read again every week. A company listed after a "
        "list's date may not be on it yet.",
        f"أحكام الهيئات الشرعية كما نشرتها، وليست فتوى من الموقع: قائمتا الأسهم المجازة عند الراجحي المالية والبلاد المالية كما يجمعها "
        f"موقع أرقام (قوائم {_date((src.get('rajhi') or {}).get('date'))})، ودراسة مركز المقاصد للشركات السعودية لعام {o.get('year')} "
        f"(د. محمد بن سعود العصيمي، نُشرت {_date(o.get('date'), True)}، ونتائجها حق للمركز). القوائم تنقرأ من مصادرها كل أسبوع، "
        "والشركة اللي أُدرجت بعد تاريخ القائمة ممكن ما تكون فيها للحين.") + "</div>")


def _screen_block(sym, industry, r, banner=True):
    """The site's own screen: the banner (when the lists don't judge the company), the revenue, the business and the two ratios."""
    state, checks = verdict(r)
    kind = r.get("business")
    sp = _special(kind) if kind in SPECIAL else None
    head = {"pass": L("Halal", "حلال"), "fail": L("Not halal", "غير حلال"), "doubt": L("Doubtful", "مشكوك فيه")}[state]
    sub = {"pass": L("Passes all four checks below.", "يجتاز الفحوص الأربعة تحت."),
           "fail": L("Fails at least one of the checks below.", "ما يجتاز فحصاً واحداً على الأقل من الفحوص تحت."),
           "doubt": L("A check could not be completed or the business needs a closer look.",
                      "فيه فحص ما اكتمل أو نشاط الشركة يحتاج نظرة أدق.")}[state]
    if sp:
        head, sub = sp[0], sp[1]
    ar = " ar" if is_ar() else ""
    top = _banner(state, head, sub) if banner else ""
    # revenue breakdown
    if sp:
        rev = f'<div class="rule">{sp[3]}</div>'
    elif r.get("rev") is not None:
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
               "fail": L("The main business is not permissible (such as conventional banking, commercial insurance, alcohol, tobacco or "
                         "gambling).",
                         "النشاط الرئيسي غير مباح (مثل البنوك التقليدية أو التأمين التجاري أو الكحول أو التبغ أو القمار)."),
               "doubt": L("A financial business: it needs a closer look.", "نشاط مالي يحتاج نظرة أدق."),
               "unknown": L("Yahoo Finance gives no industry for this company.", "ياهو فاينانس ما يعطي صناعة لهذه الشركة.")}[checks["business"]]
    if sp:
        biz_txt = sp[2]
    biz_chip = _chip(checks["business"], L("CHECK", "راجع") if kind == "coop" else None)
    if kind == "islamic" and not ind:
        ind = "Banks - Regional"
    ind_txt = industry_name(ind) if ind else "—"
    if str(sym or "").upper().endswith(".SR") and any(k in str(ind or "").lower() for k in SA_TOURISM):
        ind_txt = L("Tourism & resorts", "السياحة والمنتجعات")             # Yahoo's "Resorts & Casinos": no casinos in the kingdom
        biz_txt = L("The main business is permissible: tourism and resorts (there are no casinos in Saudi Arabia).",
                    "النشاط الرئيسي مباح: سياحة ومنتجعات (ما فيه كازينوهات في السعودية).")
    biz = (f'<div class="shc"><div class="hd">{biz_chip}</div><div class="t">{L("Business activity", "نشاط الشركة")}</div>'
           f'<div class="rule">{biz_txt}</div><div class="big" style="font-size:1.05rem">{T.esc(ind_txt)}</div></div>')
    months = r.get("months") or 0
    base = (L(f"of the {months}-month average market cap", f"من متوسط القيمة السوقية لآخر {months} شهر") if months
            else L("of today's market cap", "من القيمة السوقية الحالية"))
    sec_card = _ratio_card(L("Interest-bearing securities &amp; assets", "الأوراق والأصول بفائدة"),
                           L(f"Cash and short-term investments must be under {RATIO_MAX:.0f}% {base}.",
                             f"النقد والاستثمارات قصيرة الأجل لازم تكون أقل من {RATIO_MAX:.0f}% {base}."), r.get("sec"), checks["sec"],
                           sp[4] if sp else "")
    debt_card = _ratio_card(L("Interest-bearing debt", "الديون بفائدة"),
                            L(f"Total debt must be under {RATIO_MAX:.0f}% {base}.", f"إجمالي الديون لازم يكون أقل من {RATIO_MAX:.0f}% {base}."),
                            r.get("debt"), checks["debt"], sp[4] if sp else "")
    note = L("An educational screen with AAOIFI-style thresholds on Yahoo Finance's latest annual statements, not a religious ruling (fatwa); "
             "screening providers and scholars can differ. Not halal = interest income; doubtful = other non-operating income whose source "
             "isn't disclosed. The average market cap uses today's share count.",
             "فحص تعليمي بحدود مشابهة لمعايير هيئة المحاسبة والمراجعة للمؤسسات المالية الإسلامية (AAOIFI) على آخر قوائم سنوية من ياهو فاينانس، "
             "وليس فتوى؛ وقد تختلف جهات الفحص والعلماء. غير الحلال = إيرادات الفوائد، والمشكوك فيه = إيرادات أخرى من خارج النشاط "
             "مصدرها غير معلن. متوسط القيمة السوقية محسوب بعدد الأسهم الحالي.")
    if str(sym or "").upper().endswith(".SR"):
        note += L(" In the Saudi market, Islamic banks, cooperative insurers and finance companies are read by the market's own rules, "
                  "not by Yahoo's industry name.",
                  " وفي السوق السعودي تنقرأ البنوك الإسلامية وشركات التأمين التعاوني وشركات التمويل حسب أنظمة السوق نفسه، مو حسب تصنيف ياهو.")
    ui.html(CSS + f'<div class="{ar.strip()}">{top}<div class="shgrid">{rev_card}{biz}</div><div class="shgrid two">{sec_card}{debt_card}</div>'
            f'<div class="shnote">{note}</div></div>')
