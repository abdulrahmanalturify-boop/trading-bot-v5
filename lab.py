"""
lab.py - The bots' lab on real prices, for the bot form. Every strategy was run through the site's own bot engine on real
daily prices (research/run.py, on GitHub), in 2012-2019 and again in 2020-now, with a set of tested settings (filters,
stops, risk sizing). lab_results.json holds the numbers (research/compact.py writes it).

A setting is recommended only when it holds up in both periods: better in 2020-now (the years it was not tuned on), not
much worse in 2012-2019, and without giving away most of the return.
"""
import json
import os

import streamlit as st

import theme as T
from i18n import L

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab_results.json")
SKIP = {"trailing_10"}                         # hurt almost everywhere: never recommended
FIELDS = {"regime": ("pb_regime", 0), "trend_filter": ("pb_trend", False), "stop_pct": ("pb_stop", 0.0),
          "atr_mult": ("pb_atr", 0.0), "trail_pct": ("pb_trail", 0.0), "risk_pct": ("pb_riskpt", 0.0), "tp_pct": ("pb_tp", 0.0)}
FILTER_ONLY = {"regime", "trend_filter"}        # what a combined (playbook) bot can use: its stops are its own
LABEL = {
    "baseline": ("No filter, no stop", "بدون فلتر ولا وقف"),
    "site_default": ("Stop loss 2%", "وقف خسارة 2%"),
    "stop_5": ("Stop loss 5%", "وقف خسارة 5%"),
    "stop_8": ("Stop loss 8%", "وقف خسارة 8%"),
    "atr_stop_3": ("ATR stop ×3", "وقف ATR ×3"),
    "trailing_10": ("Trailing stop 10%", "وقف متحرك 10%"),
    "risk_1_atr_3": ("Risk 1% per trade, ATR stop ×3", "مخاطرة 1% لكل صفقة ووقف ATR ×3"),
    "market_filter": ("Market filter: no new buys", "فلتر السوق: بدون شراء جديد"),
    "market_exit": ("Market filter: no buys, and sell", "فلتر السوق: بدون شراء ويبيع"),
    "trend_filter": ("Stock above its 200-day average", "السهم فوق متوسط 200 يوم"),
    "market_and_trend": ("Stock trend + market filter", "اتجاه السهم + فلتر السوق"),
    "trend_market_exit": ("Stock trend + market filter that sells", "اتجاه السهم + فلتر السوق مع البيع"),
    "trend_atr_3": ("Stock trend + ATR stop ×3", "اتجاه السهم + وقف ATR ×3"),
}
VIEW_LABEL = {"company": ("one company (100 large companies tested)", "شركة وحدة (مجرّبة على 100 شركة كبيرة)"),
              "sector": ("a sector, up to 5 trades", "قطاع، لين 5 صفقات"),
              "all10": ("all companies, up to 10 trades", "كل الشركات، لين 10 صفقات"),
              "all20": ("all companies, up to 20 trades", "كل الشركات، لين 20 صفقة")}


@st.cache_data(ttl=3600, show_spinner=False)
def _load(mtime):
    with open(FILE, encoding="utf-8") as f:
        return json.load(f)


def data():
    try:
        return _load(os.path.getmtime(FILE))
    except (OSError, ValueError):
        return None


def view_of(kind, max_pos):
    if kind == "company":
        return "company"
    if kind in ("sector", "industry"):
        return "sector"
    return "all10" if int(max_pos or 10) <= 14 else "all20"


def _full(settings):
    return {k: float(settings.get(k) or 0) for k in FIELDS}


def variant_of(settings, lab=None):
    """The tested variant that matches these bot settings exactly (regime, trend filter, stops, risk), or None."""
    lab = lab or data()
    if not lab:
        return None
    want = _full(settings)
    for v, s in lab["variants"].items():
        if _full(s) == want:
            return v
    return None


def cell(strategy, view, variant, lab=None):
    lab = lab or data()
    return (((lab or {}).get("rows", {}).get(strategy) or {}).get(view) or {}).get(variant)


def recommend(strategy, view, filters_only=False, lab=None):
    """The tested setting that holds up best for this strategy and bot type (baseline when nothing beats it)."""
    lab = lab or data()
    rows = (((lab or {}).get("rows", {}).get(strategy)) or {}).get(view) or {}
    base = rows.get("baseline")
    if not base or None in base[:6]:
        return None
    best, top = "baseline", 0.0
    for v, r in rows.items():
        if v == "baseline" or v in SKIP or not r or None in r[:6]:
            continue
        if filters_only and set(k for k, x in lab["variants"].get(v, {}).items() if x) - FILTER_ONLY:
            continue
        d_in, d_out = r[0] - base[0], r[3] - base[3]
        d_dd = (r[5] - base[5]) * 100                              # drawdowns are negative: a smaller one is a gain
        if d_in < -0.15 or d_out < -0.02 or (base[4] > 0 and r[4] < 0.6 * base[4]):
            continue
        if view == "company" and None not in (r[8], base[8]) and r[8] < base[8] - 0.03:
            continue                                               # the typical single-company bot must not get worse
        score = d_out + 0.5 * d_in + 0.01 * d_dd
        if score >= 0.05 and score > top:
            best, top = v, score
    return best


def form_values(variant, lab=None):
    """Session-state values that put the bot form on a tested variant."""
    lab = lab or data()
    s = (lab or {}).get("variants", {}).get(variant, {})
    out = {}
    for k, (key, zero) in FIELDS.items():
        x = s.get(k) or 0
        out[key] = bool(x) if isinstance(zero, bool) else (int(x) if k == "regime" else float(x))
    return out


def ranking(view, filters_only=False, lab=None):
    """Every strategy for this bot type, with its recommended setting, best 2020-now Sharpe first."""
    lab = lab or data()
    out = []
    for s in (lab or {}).get("rows", {}):
        v = recommend(s, view, filters_only, lab)
        r = cell(s, view, v, lab) if v else None
        if r:
            out.append((s, v, r))
    return sorted(out, key=lambda x: -(x[2][3] or 0))


# ---------------------------------------------------------------- display
def pct(x, signed=True):
    return "—" if x is None else (f"{x * 100:+.0f}%" if signed else f"{x * 100:.0f}%")


def sharpe(x):
    return "—" if x is None else f"{x:.2f}"


def verdict(strategy, view, lab=None):
    """One plain sentence on how the strategy did against simply holding the stocks (2020-now)."""
    lab = lab or data()
    v = recommend(strategy, view, lab=lab)
    r = cell(strategy, view, v, lab) if v else None
    if not r:
        return ""
    if view == "company":
        beat = r[9]
        return L(f"On one company, this bot beat simply holding that company in {pct(beat, False)} of the 100 companies tested "
                 "(2020 → now). Bots on all companies usually did better.",
                 f"على شركة وحدة، تفوّق هالبوت على مجرد الاحتفاظ بالسهم في {pct(beat, False)} من الـ 100 شركة المجرّبة "
                 "(من 2020 لين اليوم). بوتات كل الشركات غالباً أفضل.")
    bh = (lab.get("buy_hold") or {}).get("all") or [None] * 6
    if bh[3] is None:
        return ""
    if r[3] >= bh[3] + 0.05:
        return L("2020 → now it beat holding all the stocks, on return for the risk taken.",
                 "من 2020 لين اليوم تفوّق على الاحتفاظ بكل الأسهم، في العائد مقابل المخاطرة.")
    if r[3] >= bh[3] - 0.05:
        return L("2020 → now it did about as well as holding all the stocks, for the risk taken.",
                 "من 2020 لين اليوم كان تقريباً مثل الاحتفاظ بكل الأسهم، مقابل المخاطرة.")
    return L("2020 → now it did worse than simply holding all the stocks.", "من 2020 لين اليوم كان أضعف من مجرد الاحتفاظ بكل الأسهم.")

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "17.2"
