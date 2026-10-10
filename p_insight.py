"""
p_insight.py - Insight: Daily Brief · Articles (with live charts) · Fear & Greed index · Seasonality
"""
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import streamlit as st

import charts
import data
import insight as I
import markets as MK
import newsiq
import p_markets as M
import theme as T
import ui
import universe as U
from i18n import SECTOR_AR, L, is_ar, sector_name

ss = st.session_state
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
DAYS_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]


def _months():
    return MONTHS_AR if is_ar() else MONTHS_EN


def _today_line():
    now = datetime.now(MK.tz())                 # the page's market: New York, or Riyadh on a Saudi page
    if is_ar():
        return f"{DAYS_AR[now.weekday()]} {now.day} {MONTHS_AR[now.month - 1]} {now.year}"
    return now.strftime("%A, %B %d, %Y").replace(" 0", " ")


# =====================================================================
# FEAR & GREED (our own index from 7 market signals, 0 = extreme fear, 100 = extreme greed)
# =====================================================================
FG_SYMS = ("^GSPC", "^VIX", "^VIX3M", "SPY", "RSP", "TLT", "IEF", "HYG")
FG_PARTS = {
    "momentum": ("Market momentum", "زخم السوق", "trending_up",
                 ("S&P 500 versus its 125-day average. Far above = greed.", "مؤشر S&P 500 مقارنة بمتوسطه لـ 125 يوماً. كلما ابتعد للأعلى = طمع.")),
    "strength": ("Price strength", "قوة السعر", "fitness_center",
                 ("Where the S&P 500 sits between its 52-week low and high.", "موقع مؤشر S&P 500 بين أدنى وأعلى سعر له خلال 52 أسبوعاً.")),
    "breadth": ("Market breadth", "اتساع السوق", "groups",
                ("Equal-weight S&P (RSP) versus the index (SPY) over 20 days: are most stocks joining in?",
                 "صندوق الأوزان المتساوية RSP مقارنة بالمؤشر SPY خلال 20 يوماً: هل تشارك أغلب الأسهم في الحركة؟")),
    "volatility": ("Volatility (VIX)", "التذبذب (VIX)", "speed",
                   ("VIX versus its 50-day average. A falling VIX = greed, a spike = fear.", "مؤشر VIX مقارنة بمتوسطه لـ 50 يوماً. انخفاضه = طمع، وقفزته = خوف.")),
    "haven": ("Safe-haven demand", "الطلب على الملاذ الآمن", "shield",
              ("Stocks (SPY) versus Treasury bonds (TLT) over 20 days. Bonds winning = fear.", "الأسهم SPY مقارنة بالسندات TLT خلال 20 يوماً. تفوق السندات = خوف.")),
    "junk": ("Junk bond demand", "الطلب على السندات عالية العائد", "account_balance_wallet",
             ("High-yield bonds (HYG) versus Treasuries (IEF) over 20 days. Appetite for risk = greed.",
              "السندات عالية العائد HYG مقارنة بسندات الخزانة IEF خلال 20 يوماً. الإقبال على المخاطرة = طمع.")),
    "term": ("Volatility term structure", "هيكل التذبذب", "stacked_line_chart",
             ("VIX divided by 3-month VIX. Above 1 means traders fear the near term = fear.", "VIX مقسوماً على VIX لثلاثة أشهر. أعلى من 1 يعني قلقاً من المدى القريب = خوف.")),
}


def _pct_rank(s, invert=False, window=252):
    s = s.dropna()
    try:
        r = s.rolling(window, min_periods=60).rank(pct=True) * 100
    except Exception:
        r = s.rolling(window, min_periods=60).apply(lambda x: (x <= x[-1]).mean() * 100, raw=True)
    return 100 - r if invert else r


@st.cache_data(ttl=1800, show_spinner=False)
def fear_greed():
    """-> (index series 0-100, {part: {"score": series, "raw": latest raw value}}, S&P 500 close)."""
    px = data.history_many(FG_SYMS, "2y")
    c = {s: df["Close"].dropna() for s, df in px.items() if df is not None and len(df) > 80}
    parts = {}
    if "^GSPC" in c:
        g = c["^GSPC"]
        m = g / g.rolling(125).mean() - 1
        parts["momentum"] = {"score": _pct_rank(m), "raw": float(m.dropna().iloc[-1] * 100) if m.notna().any() else np.nan}
        lo, hi = g.rolling(252, min_periods=60).min(), g.rolling(252, min_periods=60).max()
        pos = ((g - lo) / (hi - lo)).clip(0, 1) * 100
        parts["strength"] = {"score": pos, "raw": float(pos.dropna().iloc[-1]) if pos.notna().any() else np.nan}
    if {"RSP", "SPY"} <= set(c):
        b = (c["RSP"].pct_change(20) - c["SPY"].pct_change(20)) * 100
        parts["breadth"] = {"score": _pct_rank(b), "raw": float(b.dropna().iloc[-1]) if b.notna().any() else np.nan}
    if "^VIX" in c:
        v = c["^VIX"]
        x = v / v.rolling(50).mean() - 1
        parts["volatility"] = {"score": _pct_rank(x, invert=True), "raw": float(v.iloc[-1])}
    if {"SPY", "TLT"} <= set(c):
        h = (c["SPY"].pct_change(20) - c["TLT"].pct_change(20)) * 100
        parts["haven"] = {"score": _pct_rank(h), "raw": float(h.dropna().iloc[-1]) if h.notna().any() else np.nan}
    if {"HYG", "IEF"} <= set(c):
        j = (c["HYG"].pct_change(20) - c["IEF"].pct_change(20)) * 100
        parts["junk"] = {"score": _pct_rank(j), "raw": float(j.dropna().iloc[-1]) if j.notna().any() else np.nan}
    if {"^VIX", "^VIX3M"} <= set(c):
        t = (c["^VIX"] / c["^VIX3M"]).dropna()
        parts["term"] = {"score": _pct_rank(t, invert=True), "raw": float(t.iloc[-1]) if len(t) else np.nan}
    parts = {k: p for k, p in parts.items() if p["score"].notna().sum() > 20}
    if not parts:
        return pd.Series(dtype=float), {}, pd.Series(dtype=float)
    frame = pd.concat({k: p["score"] for k, p in parts.items()}, axis=1).sort_index()
    idx = frame.mean(axis=1, skipna=True).dropna()
    idx = idx[idx.index >= idx.index[-1] - pd.Timedelta(days=370)]
    return idx, parts, c.get("^GSPC", pd.Series(dtype=float))


# the Saudi market's own Fear & Greed: Yahoo has no VIX, no bond funds and no TASI history for it, so it reads the market itself
# (all the main-market companies, as one equal-weighted index) and gold and oil
FG_PARTS_SA = {
    "momentum": ("Market momentum", "زخم السوق", "trending_up",
                 ("The Saudi market versus its 125-day average. Far above = greed.", "السوق السعودي مقارنة بمتوسطه لـ 125 يوماً. كلما ابتعد للأعلى = طمع.")),
    "strength": ("Price strength", "قوة السعر", "fitness_center",
                 ("Where the Saudi market sits between its 52-week low and high.", "موقع السوق السعودي بين أدنى وأعلى مستوى له خلال 52 أسبوعاً.")),
    "breadth": ("Market breadth", "اتساع السوق", "groups",
                ("The share of companies above their own 50-day average: are most stocks joining in?",
                 "نسبة الشركات اللي فوق متوسطها لـ 50 يوماً: هل تشارك أغلب الأسهم في الحركة؟")),
    "highs": ("New highs vs new lows", "القمم مقابل القيعان", "swap_vert",
              ("Companies near their 52-week high minus those near their 52-week low.", "الشركات القريبة من قمتها السنوية ناقص القريبة من قاعها السنوي.")),
    "volatility": ("Volatility", "التذبذب", "speed",
                   ("How much the market swung over the last 20 days against the past year. Calm = greed, sharp swings = fear.",
                    "قد إيش تذبذب السوق آخر 20 يوماً مقارنة بالسنة الماضية. الهدوء = طمع، والتقلب الحاد = خوف.")),
    "haven": ("Safe-haven demand", "الطلب على الملاذ الآمن", "shield",
              ("The Saudi market versus gold over 20 days. Gold winning = fear.", "السوق السعودي مقارنة بالذهب خلال 20 يوماً. تفوّق الذهب = خوف.")),
    "oil": ("Oil", "النفط", "oil_barrel",
            ("Brent crude over 20 days against the past year: a rising oil price lifts the Saudi market's mood.",
             "خام برنت خلال 20 يوماً مقارنة بالسنة الماضية: ارتفاع النفط يرفع مزاج السوق السعودي.")),
}


@st.cache_data(ttl=1800, show_spinner=False)
def fear_greed_sa():
    """The Saudi market's Fear & Greed -> (index series 0-100, {part: {"score": series, "raw": latest}}, the market as one index)."""
    cl = data.sa_closes("2y")
    if cl.empty:
        return pd.Series(dtype=float), {}, pd.Series(dtype=float)
    g = data.sa_index(cl)
    parts = {}
    m = g / g.rolling(125).mean() - 1
    parts["momentum"] = {"score": _pct_rank(m), "raw": float(m.dropna().iloc[-1] * 100) if m.notna().any() else np.nan}
    lo, hi = g.rolling(252, min_periods=60).min(), g.rolling(252, min_periods=60).max()
    pos = ((g - lo) / (hi - lo)).clip(0, 1) * 100
    parts["strength"] = {"score": pos, "raw": float(pos.dropna().iloc[-1]) if pos.notna().any() else np.nan}
    n_ok = cl.notna().sum(axis=1).replace(0, np.nan)
    above = (cl > cl.rolling(50, min_periods=40).mean()).where(cl.notna()).sum(axis=1) / n_ok * 100
    above = above.where(cl.rolling(50, min_periods=40).mean().notna().sum(axis=1) > 50)
    parts["breadth"] = {"score": _pct_rank(above), "raw": float(above.dropna().iloc[-1]) if above.notna().any() else np.nan}
    hi_ = (cl >= cl.rolling(252, min_periods=120).max() * 0.97).sum(axis=1)
    lo_ = (cl <= cl.rolling(252, min_periods=120).min() * 1.03).sum(axis=1)
    net = ((hi_ - lo_) / n_ok * 100).where(cl.rolling(252, min_periods=120).max().notna().sum(axis=1) > 50)
    parts["highs"] = {"score": _pct_rank(net), "raw": float(net.dropna().iloc[-1]) if net.notna().any() else np.nan}
    vol = g.pct_change().rolling(20).std() * np.sqrt(252) * 100
    parts["volatility"] = {"score": _pct_rank(vol, invert=True), "raw": float(vol.dropna().iloc[-1]) if vol.notna().any() else np.nan}
    px = data.history_many(("GC=F", "BZ=F"), "2y")
    to_days = lambda sr: sr.reindex(g.index, method="ffill") if sr is not None and len(sr) else None
    gold = to_days(px.get("GC=F", pd.DataFrame()).get("Close")) if px.get("GC=F") is not None else None
    if gold is not None and gold.notna().sum() > 80:
        h = (g.pct_change(20) - gold.pct_change(20)) * 100
        parts["haven"] = {"score": _pct_rank(h), "raw": float(h.dropna().iloc[-1]) if h.notna().any() else np.nan}
    oil = to_days(px.get("BZ=F", pd.DataFrame()).get("Close")) if px.get("BZ=F") is not None else None
    if oil is not None and oil.notna().sum() > 80:
        o = oil.pct_change(20) * 100
        parts["oil"] = {"score": _pct_rank(o), "raw": float(o.dropna().iloc[-1]) if o.notna().any() else np.nan}
    parts = {k: p for k, p in parts.items() if p["score"].notna().sum() > 20}
    if not parts:
        return pd.Series(dtype=float), {}, g
    frame = pd.concat({k: p["score"] for k, p in parts.items()}, axis=1).sort_index()
    idx = frame.mean(axis=1, skipna=True).dropna()
    idx = idx[idx.index >= idx.index[-1] - pd.Timedelta(days=370)]
    return idx, parts, g


def _fg_raw_text_sa(k, v):
    if v is None or pd.isna(v):
        return "—"
    if k == "momentum":
        return L(f"The market is {v:+.1f}% vs its 125-day average", f"السوق عند {v:+.1f}% مقارنة بمتوسط 125 يوماً")
    if k == "strength":
        return L(f"{v:.0f}% of the way from its 52-week low to its high", f"عند {v:.0f}% من المسافة بين أدنى وأعلى مستوى في 52 أسبوعاً")
    if k == "breadth":
        return L(f"{v:.0f}% of the companies are above their 50-day average", f"{v:.0f}% من الشركات فوق متوسطها لـ 50 يوماً")
    if k == "highs":
        return L(f"Near highs minus near lows: {v:+.0f}% of the companies", f"القريبة من القمة ناقص القريبة من القاع: {v:+.0f}% من الشركات")
    if k == "volatility":
        return L(f"20-day volatility {v:.1f}% a year", f"تذبذب 20 يوماً {v:.1f}% سنوياً")
    if k == "haven":
        return L(f"Stocks vs gold: {v:+.2f} pts over 20 days", f"الأسهم مقابل الذهب: {v:+.2f} نقطة خلال 20 يوماً")
    return L(f"Brent {v:+.1f}% over 20 days", f"برنت {v:+.1f}% خلال 20 يوماً")


def _fg_raw_text(k, v):
    if v is None or pd.isna(v):
        return "—"
    if k == "momentum":
        return L(f"S&P 500 is {v:+.1f}% vs its 125-day average", f"مؤشر S&P 500 عند {v:+.1f}% مقارنة بمتوسط 125 يوماً")
    if k == "strength":
        return L(f"{v:.0f}% of the way from its 52-week low to its high", f"عند {v:.0f}% من المسافة بين أدنى وأعلى سعر في 52 أسبوعاً")
    if k == "breadth":
        return L(f"Equal-weight vs index: {v:+.2f} pts over 20 days", f"الأوزان المتساوية مقابل المؤشر: {v:+.2f} نقطة خلال 20 يوماً")
    if k == "volatility":
        return L(f"VIX is at {v:.2f}", f"مؤشر VIX عند {v:.2f}")
    if k == "haven":
        return L(f"Stocks vs bonds: {v:+.2f} pts over 20 days", f"الأسهم مقابل السندات: {v:+.2f} نقطة خلال 20 يوماً")
    if k == "junk":
        return L(f"High yield vs Treasuries: {v:+.2f} pts over 20 days", f"عالية العائد مقابل الخزانة: {v:+.2f} نقطة خلال 20 يوماً")
    return L(f"VIX / VIX3M = {v:.2f}", f"VIX / VIX3M = {v:.2f}")


def _fg_box(v):
    en, ar, kind = T.fg_zone(v)
    bg, fg = {"pos": (T.POS_BG, T.POS_FG), "neg": (T.NEG_BG, T.NEG_FG)}.get(kind, (T.NEU_BG, T.NEU_FG))
    return bg, fg, L(en, ar)


def fg_now(market=None):
    """Latest index value (or None) for other pages (the page's market by default)."""
    try:
        idx, _, _ = fear_greed_sa() if (market or MK.current()) == MK.SA else fear_greed()
        return float(idx.iloc[-1]) if len(idx) else None
    except Exception:
        return None


def page_sentiment():
    sa = MK.is_sa()
    if sa:
        ui.header("speed", "Fear & Greed Index · Saudi Market", "مؤشر الخوف والطمع · السوق السعودي",
                  "Is the Saudi market driven by fear or by greed right now? Seven signals from the market itself, gold and oil, combined into "
                  "one score from 0 to 100.",
                  "هل يقود السوق السعودي الآن الخوف أم الطمع؟ سبع إشارات من السوق نفسه والذهب والنفط، مجمّعة في درجة واحدة من 0 إلى 100.")
    else:
        ui.header("speed", "Fear & Greed Index", "مؤشر الخوف والطمع",
                  "Is the market driven by fear or by greed right now? Seven market signals combined into one score from 0 to 100.",
                  "هل يقود السوق الآن الخوف أم الطمع؟ سبع إشارات من السوق مجمّعة في درجة واحدة من 0 إلى 100.")
    parts_def, raw_txt = (FG_PARTS_SA, _fg_raw_text_sa) if sa else (FG_PARTS, _fg_raw_text)
    with st.spinner(L("Reading the market's mood...", "جاري قراءة مزاج السوق...")):
        idx, parts, spx = fear_greed_sa() if sa else fear_greed()
    if idx.empty:
        st.warning(L("Market data for the index is not available right now. Please try again in a minute.",
                     "بيانات المؤشر غير متاحة حالياً. حاول مرة أخرى بعد دقيقة."), icon=":material/cloud_off:")
        ui.foot()
        return
    v = float(idx.iloc[-1])
    ui.ai_note("Fear & Greed score", f"{v:.0f}/100 ({'Saudi market' if MK.is_sa() else 'US market'})")
    c1, c2 = st.columns([1, 1.25], vertical_alignment="center")
    with c1:
        ui.html(f'<div class="card" style="padding:14px 10px 6px">{T.fg_gauge(v, is_ar(), L("Updated with the latest close", "محدّث بآخر إغلاق"))}</div>')
    with c2:
        def ago(days):
            sub = idx[idx.index <= idx.index[-1] - pd.Timedelta(days=days)]
            return float(sub.iloc[-1]) if len(sub) else None
        cmp = [(L("Previous close", "الإغلاق السابق"), float(idx.iloc[-2]) if len(idx) > 1 else None), (L("1 week ago", "قبل أسبوع"), ago(7)),
               (L("1 month ago", "قبل شهر"), ago(30)), (L("1 year ago", "قبل سنة"), float(idx.iloc[0]))]
        cells = ""
        for lab, x in cmp:
            if x is None:
                continue
            bg, fg, zl = _fg_box(x)
            cells += f'<div class="c" style="background:{bg};color:{fg}"><div class="l">{T.esc(lab)}</div><div class="v">{x:.0f}</div><div class="s">{T.esc(zl)}</div></div>'
        en, ar, kind = T.fg_zone(v)
        read = {"neg": L("Investors are fearful. Historically, fear has often been a better time to be patient than to panic.",
                         "المستثمرون خائفون. تاريخياً، كان الخوف غالباً وقتاً للصبر أكثر منه للذعر."),
                "neu": L("The market mood is balanced: neither fear nor greed is in control.", "مزاج السوق متوازن: لا الخوف ولا الطمع مسيطر."),
                "pos": L("Investors are greedy. Rallies can continue, but risk of a pullback rises when greed is extreme.",
                         "المستثمرون في حالة طمع. قد يستمر الصعود، لكن خطر التراجع يرتفع عندما يصبح الطمع شديداً.")}[kind]
        ui.html(f'<div class="card"><div class="muted" style="font-size:.75rem;font-weight:600;letter-spacing:.08em">{L("HOW THE MOOD CHANGED", "كيف تغيّر المزاج")}</div>'
                f'<div class="fgcmp">{cells}</div><div style="margin-top:12px;line-height:1.8">{T.icon("psychology", T.CYAN)} {T.esc(read)}</div></div>')
    ui.chart(charts.fg_history(idx, L("Fear & Greed over the past year", "الخوف والطمع خلال السنة الماضية"),
                               spx.reindex(idx.index).ffill() if len(spx) else None,
                               (L("Fear & Greed", "الخوف والطمع"), L("Saudi market (equal weight)", "السوق السعودي (أوزان متساوية)") if sa else "S&P 500")),
             key="fg_hist")
    ui.sec("tune", f"What's driving it: the {len(parts)} signals", f"ما الذي يحركه: الإشارات ({len(parts)})")
    keys = [k for k in parts_def if k in parts]
    for i in range(0, len(keys), 4):
        cols = st.columns(4)
        for col, k in zip(cols, keys[i:i + 4]):
            en, ar, ic, (xen, xar) = parts_def[k]
            sc = parts[k]["score"].dropna()
            val = float(sc.iloc[-1]) if len(sc) else 50.0
            bg, fg, zl = _fg_box(val)
            col.markdown(f'<div class="fgc"><div class="h"><b>{T.icon(ic, "#79B8F4")} {T.esc(L(en, ar))}</b>'
                         f'<span class="pbox" style="background:{bg};color:{fg}">{val:.0f} · {T.esc(zl)}</span></div>'
                         f'<div class="fgbar"><i style="left:{val:.1f}%"></i></div><div class="r">{T.esc(raw_txt(k, parts[k]["raw"]))}</div>'
                         f'<div class="x">{T.esc(L(xen, xar))}</div></div>', unsafe_allow_html=True)
    with st.expander(L("How this index is calculated", "كيف يُحسب هذا المؤشر"), icon=":material/info:"):
        if sa:
            st.markdown(L("Each signal is compared with its own history over the past year and turned into a score from 0 (the most fearful reading "
                          "of the year) to 100 (the greediest); the index is their average. The Saudi market here is all the main-market "
                          "companies as one equal-weighted index (Yahoo keeps no history for TASI), and there is no volatility index or bond "
                          "fund for it, so the signals come from the market itself (momentum, strength, breadth, new highs and lows, its own "
                          "volatility), from gold (the safe haven) and from Brent crude. It is TURA's own reading, not an official index. "
                          "Zones: 0–24 extreme fear · 25–44 fear · 45–55 neutral · 56–75 greed · 76–100 extreme greed.",
                          "تُقارن كل إشارة بتاريخها خلال السنة الماضية وتتحول إلى درجة من 0 (أكثر قراءة خوفاً في السنة) إلى 100 (أكثرها طمعاً)، "
                          "والمؤشر متوسطها. السوق السعودي هنا هو كل شركات السوق الرئيسية كمؤشر واحد بأوزان متساوية (ياهو ما يحتفظ بتاريخ تاسي)، "
                          "وما فيه مؤشر تذبذب ولا صناديق سندات له، فالإشارات من السوق نفسه (الزخم، والقوة، والاتساع، والقمم والقيعان الجديدة، "
                          "وتذبذبه)، ومن الذهب (الملاذ الآمن)، ومن خام برنت. هو قراءة TURA الخاصة وليس مؤشراً رسمياً. "
                          "المناطق: 0–24 خوف شديد · 25–44 خوف · 45–55 محايد · 56–75 طمع · 76–100 طمع شديد."))
            ui.foot()
            return
        st.markdown(L("Each signal is compared with its own history over the past year and turned into a score from 0 (the most fearful reading of the "
                      "year) to 100 (the greediest). The index is the average of the available signals. It is inspired by the well-known CNN Fear & "
                      "Greed Index but calculated independently from free market data, so the numbers will not match it exactly. "
                      "Zones: 0–24 extreme fear · 25–44 fear · 45–55 neutral · 56–75 greed · 76–100 extreme greed.",
                      "تُقارن كل إشارة بتاريخها خلال السنة الماضية وتتحول إلى درجة من 0 (أكثر قراءة خوفاً في السنة) إلى 100 (أكثرها طمعاً)، والمؤشر هو متوسط "
                      "الإشارات المتاحة. الفكرة مستوحاة من مؤشر CNN الشهير للخوف والطمع لكنه محسوب بشكل مستقل من بيانات سوق مجانية، لذلك لن تتطابق الأرقام تماماً. "
                      "المناطق: 0–24 خوف شديد · 25–44 خوف · 45–55 محايد · 56–75 طمع · 76–100 طمع شديد."))
    ui.foot()


# =====================================================================
# DAILY BRIEF
# =====================================================================
BRIEF_TILES = [("^GSPC", "S&P 500", "إس آند بي 500"), ("^IXIC", "Nasdaq", "ناسداك"), ("^DJI", "Dow Jones", "داو جونز"), ("^RUT", "Russell 2000", "راسل 2000"),
               ("^VIX", "VIX", "مؤشر الخوف VIX"), ("^TNX", "10Y yield", "عائد 10 سنوات"), ("DX-Y.NYB", "US dollar index", "مؤشر الدولار"),
               ("CL=F", "WTI crude", "نفط غرب تكساس"), ("GC=F", "Gold", "الذهب"), ("BTC-USD", "Bitcoin", "بيتكوين")]
KEY_EVENTS = ("cpi", "consumer price", "nonfarm", "payroll", "unemployment", "gdp", "fomc", "fed ", "interest rate", "pce", "retail sales", "ppi",
              "jobless", "ism", "jolts", "consumer confidence", "michigan")


def _sector_moves():
    sec = data.history_many(tuple(U.SECTOR_ETFS), "5d")
    return {U.SECTOR_ETFS[e]: float((df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100) for e, df in sec.items() if len(df) > 1}


def _headline(sp, nq, dj, perf, ybps):
    if sp is None:
        return "Markets at a glance", "لمحة سريعة عن الأسواق"
    if abs(sp) < 0.15:
        en, ar = "Stocks drift near the flat line", "الأسهم تتحرك قرب مستوى الإغلاق السابق"
    elif sp >= 1.5:
        en, ar = "Stocks rally strongly", "الأسهم ترتفع بقوة"
    elif sp >= 0.5:
        en, ar = "Stocks move higher", "الأسهم ترتفع"
    elif sp > 0:
        en, ar = "Stocks edge higher", "الأسهم ترتفع بشكل طفيف"
    elif sp <= -1.5:
        en, ar = "Stocks sell off sharply", "موجة بيع قوية في الأسهم"
    elif sp <= -0.5:
        en, ar = "Stocks slip", "الأسهم تتراجع"
    else:
        en, ar = "Stocks edge lower", "الأسهم تتراجع بشكل طفيف"
    if perf:
        best, worst = max(perf, key=perf.get), min(perf, key=perf.get)
        if sp >= 0:
            en += f" as {best} leads"
            ar += f" بقيادة قطاع {SECTOR_AR.get(best, best)}"
        else:
            en += f" as {worst} lags"
            ar += f" مع ضعف قطاع {SECTOR_AR.get(worst, worst)}"
    if nq is not None and dj is not None and abs(nq - dj) >= 0.5:
        en += "; tech outperforms" if nq > dj else "; tech lags"
        ar += "، والتقنية تتفوق" if nq > dj else "، والتقنية متأخرة"
    if ybps is not None and abs(ybps) >= 4:
        en += "; Treasury yields rise" if ybps > 0 else "; Treasury yields ease"
        ar += "، وعوائد السندات ترتفع" if ybps > 0 else "، وعوائد السندات تتراجع"
    return en, ar


def _story_rows(stories, lg_chg):
    rows = []
    titles = [n["title"] for n in stories]
    if is_ar():
        titles = data.translate(titles)
    for n, title in zip(stories, titles):
        iq = n["iq"]
        bg, fg, bd = newsiq.colors(iq["score"])
        # every story with its picture: the outlet's photo, or the topic picture with the company's logo (T.news_thumb)
        rows.append(f'<div class="bstory">{T.news_thumb(n)}<div class="b"><a href="{T.esc(n["link"])}" target="_blank" dir="auto">{T.esc(title)}</a>'
                    f'<div class="m"><span class="sc" style="background:{bg};color:{fg};border-color:{bd}" title="{T.esc(L(*newsiq.level(iq["score"])))}">'
                    f'{iq["score"]}<small>/10</small></span>{T.esc(n["source"])} · {T.time_ago(n["time"], is_ar())}</div>{T.kw_chips(iq, is_ar(), 3)}</div></div>')
    return "".join(rows)


def _events():
    cal = data.econ_calendar(0, 8)
    if cal.empty:
        return []
    cal = cal.copy()
    tcol = next((c for c in cal.columns if "Time" in c or "Date" in c), None)
    ecol = next((c for c in cal.columns if c.lower() in ("event", "econ release")), cal.columns[0])
    if tcol is None:
        return []
    cal[tcol] = pd.to_datetime(cal[tcol], errors="coerce", utc=True)
    now = pd.Timestamp.now(tz="UTC")
    cal = cal[cal[tcol] >= now - pd.Timedelta(hours=2)].sort_values(tcol).head(10)
    out = []
    for _, r in cal.iterrows():
        t = r[tcol].tz_convert("America/New_York")
        name = str(r.get(ecol, ""))
        exp, last = r.get("Expected"), r.get("Last")
        x = " · ".join(p for p in (f"{L('Exp.', 'متوقع')} {exp}" if pd.notna(exp) else "", f"{L('Prior', 'سابق')} {last}" if pd.notna(last) else "") if p)
        day = (f"{DAYS_AR[t.weekday()]} {t.day}" if is_ar() else t.strftime("%a %b %d").replace(" 0", " "))
        key = any(k in name.lower() for k in KEY_EVENTS)
        out.append(f'<div class="evt{" key" if key else ""}"><div class="d">{day}<br>{t:%H:%M} ET</div><div class="n">'
                   + (T.icon("local_fire_department", "#F5B94A") + " " if key else "") + f'{T.esc(name)}</div><div class="x">{T.esc(x)}</div></div>')
    return out


# ---------------------------------------------------------------- the Saudi market's brief
BRIEF_TILES_SA = [("^TASI.SR", "TASI", "تاسي"), ("^NOMUC.SR", "Nomu", "نمو"), ("2222.SR", "Aramco", "أرامكو"), ("1120.SR", "Al Rajhi", "الراجحي"),
                  ("1180.SR", "SNB", "الأهلي"), ("BZ=F", "Brent crude", "خام برنت"), ("CL=F", "WTI crude", "خام غرب تكساس"), ("GC=F", "Gold", "الذهب"),
                  ("DX-Y.NYB", "US dollar index", "مؤشر الدولار"), ("BTC-USD", "Bitcoin", "بيتكوين")]


def _headline_sa(tx, perf, oil):
    if tx is None:
        return "The Saudi market at a glance", "لمحة سريعة عن السوق السعودي"
    if abs(tx) < 0.15:
        en, ar = "Saudi stocks hold near the flat line", "الأسهم السعودية تتحرك قرب مستوى الإغلاق السابق"
    elif tx >= 1.5:
        en, ar = "Saudi stocks rally strongly", "الأسهم السعودية ترتفع بقوة"
    elif tx >= 0.5:
        en, ar = "Saudi stocks move higher", "الأسهم السعودية ترتفع"
    elif tx > 0:
        en, ar = "Saudi stocks edge higher", "الأسهم السعودية ترتفع بشكل طفيف"
    elif tx <= -1.5:
        en, ar = "Saudi stocks sell off sharply", "موجة بيع قوية في الأسهم السعودية"
    elif tx <= -0.5:
        en, ar = "Saudi stocks slip", "الأسهم السعودية تتراجع"
    else:
        en, ar = "Saudi stocks edge lower", "الأسهم السعودية تتراجع بشكل طفيف"
    if perf:
        best, worst = max(perf, key=perf.get), min(perf, key=perf.get)
        if tx >= 0:
            en += f" as {best} leads"
            ar += f" بقيادة قطاع {M._sa_sector(best) if is_ar() else best}"
        else:
            en += f" as {worst} lags"
            ar += f" مع ضعف قطاع {M._sa_sector(worst) if is_ar() else worst}"
    if oil is not None and abs(oil) >= 1.5:
        en += "; oil " + ("jumps" if oil > 0 else "slides")
        ar += "، والنفط " + ("يقفز" if oil > 0 else "يتراجع")
    return en, ar


def _events_sa():
    """The coming Saudi releases and SAMA's rates, and the big US ones, plus the Saudi companies reporting in the next days."""
    import caldata as C
    import mcal_sa
    today = mcal_sa.today()
    out = []
    try:
        ev = C.econ(today, today + timedelta(days=8), {"SA", "US"}, tz=mcal_sa.TZ)
    except Exception:
        ev = pd.DataFrame()
    if not ev.empty:
        now = pd.Timestamp.now(tz=mcal_sa.TZ)
        ev = ev[(ev["Time"] >= now - pd.Timedelta(hours=2)) & ((ev["Region"] == "SA") | (ev["Stars"] >= 3))]
        # the US side: the headline releases only (Yahoo lists each CPI four ways: MM / YY, with and without seasonal adjustment,
        # and its index), at most four of them
        us = ev["Region"] != "SA"
        alt = ev["Event"].str.contains(r"\bNSA\b|Index|Cleveland|Ex Food|Final|Prelim", case=False, regex=True)
        ev = ev[~(us & alt)]
        ev = ev[~us | (ev.groupby(us).cumcount() < 4)].head(10)
        for r in ev.itertuples():
            t = r.Time
            day = (f"{DAYS_AR[t.weekday()]} {t.day}" if is_ar() else t.strftime("%a %b %d").replace(" 0", " "))
            x = " · ".join(p for p in (f"{L('Exp.', 'متوقع')} {r.Expected}" if pd.notna(r.Expected) else "",
                                       f"{L('Prior', 'سابق')} {r.Last}" if pd.notna(r.Last) else "") if p)
            key = r.Stars >= 3
            tm = "" if not (t.hour or t.minute) else f"<br>{t:%H:%M}"
            out.append(f'<div class="evt{" key" if key else ""}"><div class="d">{day}{tm}</div><div class="n">'
                       + (T.icon("local_fire_department", "#F5B94A") + " " if key else "") + f'{T.esc(r.Region)} · {T.esc(r.Event)}</div>'
                       f'<div class="x">{T.esc(x)}</div></div>')
    try:
        er = C.earnings_sa(today, today + timedelta(days=8))
    except Exception:
        er = pd.DataFrame()
    import tasi
    for r in er.head(8).itertuples():
        day = (f"{DAYS_AR[r.Date.weekday()]} {r.Date.day}" if is_ar() else r.Date.strftime("%a %b %d").replace(" 0", " "))
        out.append(f'<div class="evt"><div class="d">{day}</div><div class="n">{T.icon("request_quote", "#79B8F4")} '
                   f'{T.esc(tasi.name_of(r.Symbol, is_ar()) or r.Company)} · {L("earnings", "النتائج")}</div>'
                   f'<div class="x">{T.esc(L("EPS est.", "الربحية المتوقعة") + " " + format(r.Est, ".2f")) if pd.notna(r.Est) else ""}</div></div>')
    return out


def page_brief_sa():
    ui.header("summarize", "Daily Market Brief · Saudi Market", "الموجز اليومي · السوق السعودي",
              "Everything that matters for the Saudi market today in one minute: the numbers, the stories that moved it and what to watch next.",
              "كل ما يهمك عن السوق السعودي اليوم في دقيقة: الأرقام، والأخبار اللي حركته، وما تتابعه لاحقاً.")
    px = M._tile_prices()
    last = lambda s_: M._last(px, s_)
    tx, nm_ = last("^TASI.SR")[2], last("^NOMUC.SR")[2]
    mv = data.sa_moves()
    perf = {}
    if not mv.empty:
        perf = {k: float(v) for k, v in mv.groupby("Sector")["Chg %"].mean().dropna().items() if k}
    oil = last("BZ=F")[2]
    fg = fg_now()
    en, ar = _headline_sa(tx, perf, oil)
    bullets = []
    idx_parts = [(a_, b_, v_) for a_, b_, v_ in (("TASI", "تاسي", tx), ("Nomu", "نمو", nm_)) if v_ is not None]
    if idx_parts:
        bullets.append((" · ".join(f"{a_} {v_:+.2f}%" for a_, _, v_ in idx_parts) + ".", " · ".join(f"{b_} {v_:+.2f}%" for _, b_, v_ in idx_parts) + "."))
    if not mv.empty:
        adv = (mv["Chg %"] > 0).mean() * 100
        val = float(mv["Value"].sum())
        bullets.append((f"Breadth: {adv:.0f}% of the {len(mv)} main-market companies are up · traded value SAR {T.fmt_big(val)}.",
                        f"اتساع السوق: {adv:.0f}% من {len(mv)} شركة في السوق الرئيسية صاعدة · قيمة التداول {T.fmt_big(val)} ريال."))
    if perf:
        b_, w_ = max(perf, key=perf.get), min(perf, key=perf.get)
        bullets.append((f"Best sector: {b_} ({perf[b_]:+.2f}%). Weakest: {w_} ({perf[w_]:+.2f}%).",
                        f"أفضل قطاع: {M._sa_sector(b_)} ({perf[b_]:+.2f}%)، والأضعف: {M._sa_sector(w_)} ({perf[w_]:+.2f}%)."))
    gold, usd_ = last("GC=F"), last("DX-Y.NYB")
    if oil is not None:
        bullets.append((f"Brent {oil:+.2f}% · Gold {(gold[2] or 0):+.2f}% · US dollar index {(usd_[2] or 0):+.2f}%.",
                        f"برنت {oil:+.2f}% · الذهب {(gold[2] or 0):+.2f}% · مؤشر الدولار {(usd_[2] or 0):+.2f}%."))
    liq = mv[mv["Value"] >= M.SA_LIQUID] if not mv.empty else mv
    if not liq.empty:
        g_, l_ = liq.sort_values("Chg %").iloc[-1], liq.sort_values("Chg %").iloc[0]
        bullets.append((f"Biggest gainer: {g_['Name']} ({g_['Chg %']:+.1f}%). Biggest loser: {l_['Name']} ({l_['Chg %']:+.1f}%).",
                        f"الأكثر ارتفاعاً: {g_['NameAr']} ({g_['Chg %']:+.1f}%)، والأكثر انخفاضاً: {l_['NameAr']} ({l_['Chg %']:+.1f}%)."))
    mood = ""
    if fg is not None:
        bg, fgc, zl = _fg_box(fg)
        mood = f'<span class="mood" style="background:{bg};color:{fgc}">{T.icon("speed")} {L("Fear & Greed", "الخوف والطمع")} {fg:.0f} · {T.esc(zl)}</span>'
    ui.ai_note("Brief headline", en)
    for i_, (b_en, _b_ar) in enumerate(bullets):
        ui.ai_note(f"Brief point {i_ + 1}", b_en)
    ui.html(f'<div class="brief{" rtl" if is_ar() else ""}"><div class="eyebrow">{T.icon("event")} {T.esc(_today_line())} {T.market_status(is_ar())} {mood}</div>'
            f'<div class="hl">{T.esc(L(en, ar))}</div><ul>' + "".join(f"<li>{T.esc(L(a, b))}</li>" for a, b in bullets) + "</ul></div>")
    items = []
    for sym, nen, nar in BRIEF_TILES_SA:
        p, chg, pct = last(sym)
        if p is None:
            continue
        items.append(T.tile(L(nen, nar), T.fmt_price(p), chg, pct, px[sym]["Close"].tail(22).values))
    ui.html(T.tiles(items))
    c1, c2 = st.columns([1.35, 1])
    with c1:
        ui.sec("bolt", "What moved the market", "ما الذي حرّك السوق")
        stories = ui.safe(M.top_stories, 6) or []
        if stories:
            ui.html(f'<div class="card" style="padding:6px 14px">{_story_rows(stories, None)}</div>')
            st.page_link(ui.PAGES["news"], label=L("All Saudi news with importance scores", "كل أخبار السوق السعودي مع درجات الأهمية"),
                         icon=":material/arrow_forward:")
        else:
            st.caption(L("No headlines available right now.", "لا توجد أخبار متاحة حالياً."))
    with c2:
        ui.sec("donut_small", "Sector scoreboard", "لوحة القطاعات")
        if perf:
            names = sorted(perf, key=perf.get, reverse=True)
            ui.chart(charts.hbar([M._sa_sector(s_) for s_ in names], [perf[s_] for s_ in names],
                                 L("Sectors today (average move of their companies)", "القطاعات اليوم (متوسط حركة شركاتها)"), height=420), key="br_sec_sa")
    if not liq.empty:
        ui.sec("leaderboard", "Biggest movers", "الأكثر حركة")
        srt = liq.sort_values("Chg %").assign(Name=lambda d_: d_["NameAr"] if is_ar() else d_["Name"])
        lg = data.logos(list(srt["Symbol"].head(5)) + list(srt["Symbol"].tail(5)))
        a, b = st.columns(2)
        a.markdown(f'<div class="mcard"><div class="hd">{T.icon("trending_up")}<span>{L("Top gainers", "الأكثر ارتفاعاً")}</span></div>'
                   f'{ui.row_list(srt.tail(5).iloc[::-1], lg)}</div>', unsafe_allow_html=True)
        b.markdown(f'<div class="mcard"><div class="hd">{T.icon("trending_down")}<span>{L("Top losers", "الأكثر انخفاضاً")}</span></div>'
                   f'{ui.row_list(srt.head(5), lg)}</div>', unsafe_allow_html=True)
    ui.sec("event_upcoming", "What to watch next", "ماذا تتابع لاحقاً")
    ev = ui.safe(_events_sa) or []
    if ev:
        ui.html("".join(ev))
        st.caption(L("Saudi releases and SAMA's rates, the big US releases (the riyal is pegged to the dollar) and the Saudi companies expected "
                     "to report. Times are Riyadh time.",
                     "البيانات السعودية وأسعار فائدة ساما، والبيانات الأمريكية الكبيرة (الريال مربوط بالدولار)، والشركات السعودية المتوقع تعلن "
                     "نتائجها. الأوقات بتوقيت الرياض."))
    else:
        st.caption(L("The calendar is not available right now.", "التقويم غير متاح حالياً."))
    a, b, c = st.columns(3)
    a.page_link(ui.PAGES["sentiment"], label=L("Fear & Greed index", "مؤشر الخوف والطمع"), icon=":material/speed:", width="stretch")
    b.page_link(ui.PAGES["econcal"], label=L("Economic calendar", "التقويم الاقتصادي"), icon=":material/event_note:", width="stretch")
    c.page_link(ui.PAGES["earnings"], label=L("Earnings calendar", "مواعيد الأرباح"), icon=":material/event_upcoming:", width="stretch")
    ui.foot()


def page_brief():
    if MK.is_sa():
        return page_brief_sa()
    ui.header("summarize", "Daily Market Brief", "الموجز اليومي للسوق",
              "Everything that matters today in one minute: the numbers, the stories that moved the market and what to watch next.",
              "كل ما يهمك اليوم في دقيقة: الأرقام، والأخبار التي حركت السوق، وما يجب متابعته لاحقاً.")
    px = M._tile_prices()
    last = lambda s: M._last(px, s)
    sp, nq, dj, rut = (last(s)[2] for s in ("^GSPC", "^IXIC", "^DJI", "^RUT"))
    y = last("^TNX")
    ybps = y[1] * 100 if y[1] is not None else None
    perf = ui.safe(_sector_moves) or {}
    moves = M._universe_moves()
    fg = fg_now()
    en, ar = _headline(sp, nq, dj, perf, ybps)
    bullets = []
    idx_parts = [(n_en, n_ar, v_) for n_en, n_ar, v_ in (("S&P 500", "إس آند بي 500", sp), ("Nasdaq", "ناسداك", nq), ("Dow", "داو جونز", dj),
                                                          ("Russell 2000", "راسل 2000", rut)) if v_ is not None]
    if idx_parts:
        bullets.append((" · ".join(f"{a_} {v_:+.2f}%" for a_, _, v_ in idx_parts) + ".", " · ".join(f"{b_} {v_:+.2f}%" for _, b_, v_ in idx_parts) + "."))
    if not moves.empty:
        adv = (moves["Chg %"] > 0).mean() * 100
        bullets.append((f"Breadth: {adv:.0f}% of the 175 largest US stocks are up today.", f"اتساع السوق: {adv:.0f}% من أكبر 175 سهم أمريكي صاعدة اليوم."))
    if perf:
        b_, w_ = max(perf, key=perf.get), min(perf, key=perf.get)
        bullets.append((f"Best sector: {b_} ({perf[b_]:+.2f}%). Weakest: {w_} ({perf[w_]:+.2f}%).",
                        f"أفضل قطاع: {SECTOR_AR.get(b_, b_)} ({perf[b_]:+.2f}%)، والأضعف: {SECTOR_AR.get(w_, w_)} ({perf[w_]:+.2f}%)."))
    v = last("^VIX")
    if v[0] is not None:
        bullets.append((f"VIX {v[0]:.2f} ({v[2]:+.1f}%): fear is {'rising' if v[2] > 0 else 'easing'}.",
                        f"مؤشر VIX عند {v[0]:.2f} ({v[2]:+.1f}%): القلق {'يرتفع' if v[2] > 0 else 'يتراجع'}."))
    if y[0] is not None:
        bullets.append((f"10-year Treasury yield {y[0]:.2f}% ({ybps:+.0f} bps).", f"عائد السندات لأجل 10 سنوات {y[0]:.2f}% ({ybps:+.0f} نقطة أساس)."))
    oil, gold, btc = last("CL=F"), last("GC=F"), last("BTC-USD")
    if oil[0] is not None and gold[0] is not None:
        bullets.append((f"Oil {oil[2]:+.2f}% · Gold {gold[2]:+.2f}% · Bitcoin {(btc[2] or 0):+.2f}%.",
                        f"النفط {oil[2]:+.2f}% · الذهب {gold[2]:+.2f}% · بيتكوين {(btc[2] or 0):+.2f}%."))
    if not moves.empty:
        g_, l_ = moves.sort_values("Chg %").iloc[-1], moves.sort_values("Chg %").iloc[0]
        bullets.append((f"Biggest large-cap gainer: {g_['Symbol']} ({g_['Chg %']:+.1f}%). Biggest loser: {l_['Symbol']} ({l_['Chg %']:+.1f}%).",
                        f"أكبر رابح بين الشركات الكبرى: {g_['Symbol']} ({g_['Chg %']:+.1f}%)، وأكبر خاسر: {l_['Symbol']} ({l_['Chg %']:+.1f}%)."))
    mood = ""
    if fg is not None:
        bg, fgc, zl = _fg_box(fg)
        mood = f'<span class="mood" style="background:{bg};color:{fgc}">{T.icon("speed")} {L("Fear & Greed", "الخوف والطمع")} {fg:.0f} · {T.esc(zl)}</span>'
    status = T.market_status(is_ar())
    ui.ai_note("Brief headline", en)
    for i_, (b_en, _b_ar) in enumerate(bullets):
        ui.ai_note(f"Brief point {i_ + 1}", b_en)
    ui.html(f'<div class="brief{" rtl" if is_ar() else ""}"><div class="eyebrow">{T.icon("event")} {T.esc(_today_line())} {status} {mood}</div>'
            f'<div class="hl">{T.esc(L(en, ar))}</div><ul>' + "".join(f"<li>{T.esc(L(a, b))}</li>" for a, b in bullets) + "</ul></div>")
    items = []
    for sym, nen, nar in BRIEF_TILES:
        p, chg, pct = last(sym)
        if p is None:
            continue
        val = f"{p:.2f}%" if sym == "^TNX" else T.fmt_price(p)
        items.append(T.tile(L(nen, nar), val, chg, pct, px[sym]["Close"].tail(22).values, invert=(sym == "^VIX"),
                            chg_text=f"{chg * 100:+.0f} bps" if sym == "^TNX" and chg is not None else None))
    ui.html(T.tiles(items))
    c1, c2 = st.columns([1.35, 1])
    with c1:
        ui.sec("bolt", "What moved the market", "ما الذي حرّك السوق")
        stories = ui.safe(M.top_stories, 6) or []
        if stories:
            ui.html(f'<div class="card" style="padding:6px 14px">{_story_rows(stories, None)}</div>')
            st.page_link(ui.PAGES["news"], label=L("All news with importance scores", "كل الأخبار مع درجات الأهمية"), icon=":material/arrow_forward:")
        else:
            st.caption(L("No headlines available right now.", "لا توجد أخبار متاحة حالياً."))
    with c2:
        ui.sec("donut_small", "Sector scoreboard", "لوحة القطاعات")
        if perf:
            names = list(perf)
            ui.chart(charts.hbar([sector_name(s_) for s_ in names], [perf[s_] for s_ in names], L("Sector ETFs today", "صناديق القطاعات اليوم"), height=420),
                     key="br_sec")
    if not moves.empty:
        ui.sec("leaderboard", "Biggest movers among large caps", "الأكثر حركة بين الشركات الكبرى")
        srt = moves.sort_values("Chg %")
        lg = data.logos(list(srt["Symbol"].head(5)) + list(srt["Symbol"].tail(5)))
        a, b = st.columns(2)
        a.markdown(f'<div class="mcard"><div class="hd">{T.icon("trending_up")}<span>{L("Top gainers", "الأكثر ارتفاعاً")}</span></div>'
                   f'{ui.row_list(srt.tail(5).iloc[::-1], lg)}</div>', unsafe_allow_html=True)
        b.markdown(f'<div class="mcard"><div class="hd">{T.icon("trending_down")}<span>{L("Top losers", "الأكثر انخفاضاً")}</span></div>'
                   f'{ui.row_list(srt.head(5), lg)}</div>', unsafe_allow_html=True)
    ui.sec("event_upcoming", "What to watch next", "ماذا تتابع لاحقاً")
    ev = ui.safe(_events) or []
    if ev:
        ui.html("".join(ev))
        st.caption(L("Highlighted events usually move markets the most. Times are New York time (ET).",
                     "الأحداث المميزة عادة الأكثر تأثيراً في السوق. الأوقات بتوقيت نيويورك."))
    else:
        st.caption(L("The economic calendar is not available right now.", "التقويم الاقتصادي غير متاح حالياً."))
    a, b, c = st.columns(3)
    a.page_link(ui.PAGES["sentiment"], label=L("Fear & Greed index", "مؤشر الخوف والطمع"), icon=":material/speed:", width="stretch")
    b.page_link(ui.PAGES["articles"], label=L("Read the articles", "اقرأ المقالات"), icon=":material/article:", width="stretch")
    c.page_link(ui.PAGES["economy"], label=L("Economy & rates", "الاقتصاد والفائدة"), icon=":material/account_balance:", width="stretch")
    ui.foot()


# =====================================================================
# ARTICLES
# =====================================================================
def _words(a):
    n = 0
    for b in a["body"]:
        if b[0] in ("p", "h", "note"):
            n += len(b[1].split())
        elif b[0] == "list":
            n += sum(len(x[0].split()) for x in b[1])
    n += sum(len(t[0].split()) for t in a["takeaways"])
    return n


def _mins(a):
    charts_n = sum(1 for b in a["body"] if b[0] == "chart")
    return max(2, round(_words(a) / 190 + charts_n * 0.5))


def _open_article(aid):
    ss["article"] = aid
    st.query_params["a"] = aid


def _close_article():
    ss.pop("article", None)
    st.query_params.pop("a", None)


def _card(a, feat=False):
    cat = I.CATEGORIES[a["cat"]]
    live = sum(1 for b in a["body"] if b[0] == "chart")
    meta = T.badge(L(f"{_mins(a)} min read", f"قراءة {_mins(a)} دقائق"), "neu", "schedule") + (T.badge(L("Live chart", "رسم مباشر"), "acc", "monitoring") if live else "")
    return (f'<div class="acard{" feat" if feat else ""}"><div class="aart">{I.art_scene(a["id"], a["cat"], a["id"] + ("f" if feat else "c"))}'
            f'</div><div class="abody"><span class="acat">{T.esc(L(cat[0], cat[1]))}</span>'
            f'<div class="attl">{T.esc(L(*a["title"]))}</div><div class="adek">{T.esc(L(*a["dek"]))}</div><div class="ameta">{meta}</div></div></div>')


def article_cards(arts, prefix="art", per_row=3):
    for i in range(0, len(arts), per_row):
        cols = st.columns(per_row)
        for col, a in zip(cols, arts[i:i + per_row]):
            with col:
                with st.container(key=f"{prefix}_{a['id']}"):
                    ui.html(_card(a))
                    st.button(L(*a["title"]), key=f"{prefix}b_{a['id']}", on_click=_open_article, args=(a["id"],), width="stretch")


def _chart(key):
    if key == "fed":
        fed, _ = data.fed_funds()
        if not fed.empty and len(fed) > 5:
            ui.chart(charts.fed_path(fed, L("Federal Reserve: target range and effective rate", "الفيدرالي: النطاق المستهدف والفائدة الفعلية"),
                                     (L("Fed target range", "النطاق المستهدف"), L("Effective fed funds rate", "الفائدة الفعلية"))), key="ar_fed")
            return True
    elif key == "curve":
        curve, _ = data.yield_curve()
        short = 2.0 if 2.0 in curve.columns else (0.25 if 0.25 in curve.columns else None)
        if not curve.empty and 10.0 in curve.columns and short is not None:
            sp = (curve[10.0] - curve[short]).dropna()
            lab = f"10Y − {data.maturity_label(short)}"
            if len(sp):
                ui.chart(charts.spread_area(sp, L(f"Yield spread {lab}", f"فرق العائد {lab}"), lab), key="ar_curve")
                return True
    elif key == "cpi":
        mac, _, _ = data.macro()
        ser = {L(mac[k]["en"], mac[k]["ar"]): mac[k]["hist"] for k in ("CPIAUCSL", "CPILFESL") if k in mac}
        if ser:
            ui.chart(charts.lines(ser, L("US inflation (year over year)", "التضخم الأمريكي (سنوي)"), colors=[T.GOLD, T.CYAN]), key="ar_cpi")
            return True
    elif key == "drawdown":
        df = data.history("^GSPC", "max")
        if not df.empty:
            c = df["Close"].dropna()
            c = c[c.index >= c.index[-1] - pd.Timedelta(days=365 * 25)]
            dd = (c / c.cummax() - 1) * 100
            k = st.columns(3)
            k[0].markdown(T.kpi("south_east", L("Deepest drop shown", "أعمق تراجع في الفترة"), f"{dd.min():.1f}%", f"{dd.idxmin():%b %Y}", "neg"), unsafe_allow_html=True)
            k[1].markdown(T.kpi("hourglass_bottom", L("Days 10%+ below the peak", "أيام تحت القمة بأكثر من 10%"), f"{(dd <= -10).mean() * 100:.0f}%",
                                L("share of all trading days", "من إجمالي أيام التداول")), unsafe_allow_html=True)
            k[2].markdown(T.kpi("my_location", L("Today vs record high", "اليوم مقارنة بالقمة"), f"{dd.iloc[-1]:.1f}%",
                                L("0% = at a record", "0% = عند قمة تاريخية"), "pos" if dd.iloc[-1] > -2 else "neg"), unsafe_allow_html=True)
            ui.chart(charts.drawdown(dd, L("S&P 500: distance below its record high", "إس آند بي 500: المسافة تحت أعلى قمة")), key="ar_dd")
            return True
    elif key == "vix":
        df = data.history("^VIX", "2y")
        if not df.empty:
            ui.chart(charts.vix_chart(df["Close"].dropna(), L("VIX over two years", "مؤشر VIX خلال سنتين"), (L("Calm", "هدوء"), L("Fear", "خوف"))), key="ar_vix")
            return True
    elif key == "sectors":
        sec = data.history_many(tuple(U.SECTOR_ETFS), "1y")
        perf = {sector_name(U.SECTOR_ETFS[e]): float((df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100) for e, df in sec.items() if len(df) > 20}
        if perf:
            ui.chart(charts.hbar(list(perf), list(perf.values()), L("Sector ETFs: 1-year return", "صناديق القطاعات: العائد خلال سنة"), height=440), key="ar_sec")
            return True
    elif key == "dca":
        c = st.columns(3)
        monthly = c[0].select_slider(L("Monthly amount ($)", "المبلغ الشهري ($)"), [100, 250, 500, 1000, 2000], value=500, key="dca_amt")
        years = c[1].select_slider(L("Years", "عدد السنوات"), [1, 3, 5, 10], value=5, key="dca_yrs")
        df = data.history("SPY", "10y")
        if not df.empty:
            px_ = df["Close"].dropna()
            px_ = px_[px_.index >= px_.index[-1] - pd.DateOffset(years=years)]
            buys = px_.groupby([px_.index.year, px_.index.month]).head(1)
            total = monthly * len(buys)
            shares_dca = (monthly / buys).reindex(px_.index).fillna(0).cumsum()
            invested = pd.Series(monthly, index=buys.index).reindex(px_.index).fillna(0).cumsum()
            lump_shares = total / px_.iloc[0]
            sim = pd.DataFrame({"dca": shares_dca * px_, "lump": lump_shares * px_, "invested": invested})
            win = L("Lump sum", "الدفعة الواحدة") if sim["lump"].iloc[-1] > sim["dca"].iloc[-1] else L("Monthly plan", "الخطة الشهرية")
            c[2].markdown(T.kpi("emoji_events", L("Winner this time", "الفائز هذه المرة"), T.esc(win),
                                L(f"total invested ${total:,.0f}", f"إجمالي المستثمر ${total:,.0f}"), "acc"), unsafe_allow_html=True)
            k = st.columns(2)
            for col, (lab, v_) in zip(k, ((L("Monthly plan (DCA) today", "الخطة الشهرية اليوم"), sim["dca"].iloc[-1]),
                                          (L("Lump sum today", "الدفعة الواحدة اليوم"), sim["lump"].iloc[-1]))):
                col.markdown(T.kpi("account_balance_wallet", lab, T.money(v_), f"{(v_ / total - 1) * 100:+.1f}%", T.cls(v_ - total)), unsafe_allow_html=True)
            ui.chart(charts.dca_chart(sim, L("Portfolio value over time", "قيمة المحفظة عبر الوقت"),
                                      (L("Monthly plan (DCA)", "الخطة الشهرية"), L("Lump sum on day one", "دفعة واحدة من اليوم الأول"),
                                       L("Money invested", "المبلغ المستثمر"))), key="ar_dca")
            return True
    return False


def _article_view(a):
    _, mid, _ = st.columns([0.35, 5, 0.35])
    with mid:
        st.button(L("All articles", "كل المقالات"), icon=":material/arrow_back:", on_click=_close_article, key="ar_back")
        cat = I.CATEGORIES[a["cat"]]
        rtl = " rtl" if is_ar() else ""
        live = any(b[0] == "chart" for b in a["body"])
        ui.html(f'<div class="acover">{I.art_scene(a["id"], a["cat"], a["id"] + "v")}</div>'
                f'<div class="article{rtl}"><span class="acat">{T.esc(L(cat[0], cat[1]))}</span><div class="at">{T.esc(L(*a["title"]))}</div>'
                f'<div class="dek">{T.esc(L(*a["dek"]))}</div><div class="ameta" style="display:flex;gap:6px;margin-top:10px;flex-wrap:wrap">'
                f'{T.badge(L(f"{_mins(a)} min read", f"قراءة {_mins(a)} دقائق"), "neu", "schedule")}'
                + (T.badge(L("Includes live data", "يتضمن بيانات مباشرة"), "acc", "monitoring") if live else "")
                + f'<span class="badge b-vio">{T.icon("edit_note")}{T.brand(".9em", "arb" + a["id"], dot=True, pro="inline", color="currentColor")}</span></div>'
                f'<div class="tkw"><div class="h">{T.icon("bolt")} {L("Key takeaways", "أهم النقاط")}</div>'
                + "".join(f'<div class="t">{T.icon("check_circle")}<span>{T.esc(L(e, r))}</span></div>' for e, r in a["takeaways"]) + "</div></div>")
        buf = []

        def flush():
            if buf:
                ui.html(f'<div class="article{rtl}">' + "".join(buf) + "</div>")
                buf.clear()
        for b in a["body"]:
            kind = b[0]
            if kind == "h":
                buf.append(f'<div class="ah">{T.esc(L(b[1], b[2]))}</div>')
            elif kind == "p":
                buf.append(f"<p>{T.esc(L(b[1], b[2]))}</p>")
            elif kind == "list":
                buf.append("<ul>" + "".join(f"<li>{T.esc(L(e, r))}</li>" for e, r in b[1]) + "</ul>")
            elif kind == "note":
                buf.append(f'<div class="anote">{T.icon("lightbulb")}<span>{T.esc(L(b[1], b[2]))}</span></div>')
            elif kind == "chart":
                flush()
                ok = ui.safe(_chart, b[1])
                if ok:
                    ui.html(f'<div class="acap">{T.icon("monitoring")}{T.esc(L(*b[2]))}</div>')
        flush()
        rel = [k for k in a.get("related", []) if k in ui.PAGES]
        if rel:
            ui.sec("explore", "Explore on the site", "استكشف في الموقع")
            cols = st.columns(len(rel))
            for col, k in zip(cols, rel):
                col.page_link(ui.PAGES[k], label=ui.PAGES[k].title, icon=ui.PAGES[k].icon, width="stretch")
        st.caption(L("Educational content, not investment advice. Data: Yahoo Finance, the New York Fed, the US Treasury, FRED and BLS.",
                     "محتوى تعليمي وليس توصية استثمارية. البيانات: ياهو فاينانس والفيدرالي في نيويورك ووزارة الخزانة الأمريكية وFRED ومكتب إحصاءات العمل."))
    ui.sec("auto_stories", "More articles", "مقالات أخرى")
    others = [x for x in I.ARTICLES if x["id"] != a["id"]]
    same = [x for x in others if x["cat"] == a["cat"]]
    article_cards((same + [x for x in others if x not in same])[:3], "art")


def page_articles():
    aid = ss.get("article") or st.query_params.get("a")
    a = I.article(aid) if aid else None
    if a:
        ss["article"] = a["id"]
        _article_view(a)
        ui.foot()
        return
    ui.header("article", "Articles", "المقالات",
              "Important reads on the economy, the markets and investing, in plain language and with live charts from the site's data.",
              "مقالات مهمة عن الاقتصاد والأسواق والاستثمار بلغة بسيطة، مع رسوم مباشرة من بيانات الموقع.")
    feat = I.ARTICLES[0]
    with st.container(key=f"art_{feat['id']}_feat"):
        ui.html(_card(feat, feat=True))
        st.button(L(*feat["title"]), key="artfeat_b", on_click=_open_article, args=(feat["id"],), width="stretch")
    c1, c2 = st.columns([2.2, 1], vertical_alignment="bottom")
    cats = ["all"] + list(I.CATEGORIES)
    pick = c1.segmented_control(L("Topic", "الموضوع"), cats, default="all", key="ar_cat",
                                format_func=lambda k: L("All", "الكل") if k == "all" else L(I.CATEGORIES[k][0], I.CATEGORIES[k][1])) or "all"
    q = c2.text_input(L("Search articles", "ابحث في المقالات"), "", placeholder=L("e.g. inflation, VIX", "مثال: التضخم، VIX"), key="ar_q").strip().lower()
    arts = [x for x in I.ARTICLES if (pick == "all" or x["cat"] == pick) and x["id"] != feat["id"]]
    if q:
        arts = [x for x in I.ARTICLES if q in " ".join([*x["title"], *x["dek"]]).lower()]
    if arts:
        article_cards(arts, "art")
    else:
        st.info(L("No articles match your search.", "لا توجد مقالات مطابقة لبحثك."), icon=":material/search_off:")
    ui.foot()


# =====================================================================
# SEASONALITY
# =====================================================================
SEAS = {"^GSPC": ("S&P 500", "إس آند بي 500"), "^IXIC": ("Nasdaq Composite", "ناسداك المركب"), "^DJI": ("Dow Jones", "داو جونز"),
        "^RUT": ("Russell 2000", "راسل 2000"), "GC=F": ("Gold", "الذهب"), "CL=F": ("WTI crude oil", "نفط غرب تكساس"), "BTC-USD": ("Bitcoin", "بيتكوين"),
        "other": ("Another symbol…", "رمز آخر…")}
# the Saudi market: Yahoo keeps no history for TASI, so the market is the funds that hold it (KSA since 2015, Falcom's Saudi
# equity ETF on Tadawul since 2012), then the biggest companies and what moves the Saudi economy
SEAS_SA = {"KSA": ("Saudi market (MSCI Saudi Arabia, KSA)", "السوق السعودي (MSCI السعودية، KSA)"),
           "9400.SR": ("Saudi equity ETF (9400, since 2012)", "صندوق الأسهم السعودية المتداول (9400، منذ 2012)"),
           "2222.SR": ("Saudi Aramco", "أرامكو السعودية"), "1120.SR": ("Al Rajhi Bank", "مصرف الراجحي"), "2010.SR": ("SABIC", "سابك"),
           "7010.SR": ("STC", "اس تي سي"), "1180.SR": ("Saudi National Bank", "البنك الأهلي السعودي"),
           "BZ=F": ("Brent crude", "خام برنت"), "GC=F": ("Gold", "الذهب"), "other": ("Another Saudi company…", "شركة سعودية أخرى…")}


def seasonality(close, years):
    """-> (monthly table years x 12 in %, stats per month DataFrame, average path by trading day, this year's path)."""
    c = close.dropna()
    c = c[~c.index.duplicated()]
    start = c.index[-1] - pd.DateOffset(years=years)
    c = c[c.index >= start - pd.Timedelta(days=40)]
    m = c.resample("ME").last().pct_change().dropna() * 100
    m = m[m.index >= start]
    table = pd.DataFrame({"y": m.index.year, "m": m.index.month, "r": m.values}).pivot_table(index="y", columns="m", values="r")
    table = table.reindex(columns=range(1, 13))
    stats = pd.DataFrame({"avg": table.mean(), "med": table.median(), "win": (table > 0).sum() / table.notna().sum() * 100,
                          "best": table.max(), "worst": table.min(), "n": table.notna().sum()})
    paths = []
    this_year = c.index[-1].year
    cur = None
    for y, grp in c.groupby(c.index.year):
        prev = c[c.index < pd.Timestamp(f"{y}-01-01")]
        if prev.empty:
            continue
        base = float(prev.iloc[-1])
        p = (grp / base - 1) * 100
        p.index = range(1, len(p) + 1)
        if y == this_year:
            cur = p
        elif len(p) > 200:
            paths.append(p.iloc[:252])
    avg = pd.concat(paths, axis=1).mean(axis=1) if paths else pd.Series(dtype=float)
    return table, stats, avg, cur


def page_seasonality():
    sa = MK.is_sa()
    seas = SEAS_SA if sa else SEAS
    if sa:
        ui.header("calendar_month", "Seasonality · Saudi Market", "الموسمية · السوق السعودي",
                  "How the Saudi market, its biggest companies, oil and gold have behaved in each month of the year: average returns, how often "
                  "each month was positive, and the typical path of a year.",
                  "كيف تصرف السوق السعودي وأكبر شركاته والنفط والذهب في كل شهر من السنة: متوسط العائد، وكم مرة كان الشهر إيجابياً، والمسار المعتاد للسنة.")
    else:
        ui.header("calendar_month", "Seasonality", "الموسمية",
                  "How markets have behaved in each month of the year: average returns, how often each month was positive, and the typical path of a year.",
                  "كيف تصرفت الأسواق في كل شهر من السنة: متوسط العائد، وكم مرة كان الشهر إيجابياً، والمسار المعتاد للسنة.")
    c1, c2, c3 = st.columns([1.3, 1, 1.3], vertical_alignment="bottom")
    pick = c1.selectbox(L("Market", "السوق"), list(seas), key="se_sym_sa" if sa else "se_sym", format_func=lambda k: L(*seas[k]))
    sym = pick
    if pick == "other" and sa:
        sym = ui.sa_company(L("Company", "الشركة"), "se_other_sa", "2222.SR", container=c2) or "2222.SR"
    elif pick == "other":
        sym = (c2.text_input(L("Symbol", "الرمز"), "AAPL", key="se_other") or "AAPL").strip().upper()
    if sa:      # the Saudi histories are shorter: KSA from 2015, the biggest companies from 2010 (Aramco from its listing in Dec 2019)
        years = c3.segmented_control(L("History", "المدة"), [5, 10, 15], default=10, key="se_yrs_sa",
                                     format_func=lambda y: L(f"{y} years", f"{y} سنوات" if y <= 10 else f"{y} سنة")) or 10
    else:
        years = c3.segmented_control(L("History", "المدة"), [10, 20, 30], default=20, key="se_yrs", format_func=lambda y: L(f"{y} years", f"{y} سنة")) or 20
    with st.spinner(L("Crunching the history...", "جاري تحليل التاريخ...")):
        df = data.history(sym, "max")
    if df.empty or len(df) < 300:
        st.warning(L("Not enough price history for this symbol.", "لا يوجد تاريخ سعري كافٍ لهذا الرمز."), icon=":material/history_toggle_off:")
        ui.foot()
        return
    table, stats, avg, cur = seasonality(df["Close"], int(years))
    if table.empty:
        st.warning(L("Not enough monthly data.", "لا توجد بيانات شهرية كافية."))
        ui.foot()
        return
    mon = _months()
    now_m = df.index[-1].month
    st_ = stats.fillna(0)
    best, worst = int(st_["avg"].idxmax()), int(st_["avg"].idxmin())
    c = df["Close"].dropna()
    prev_close = c[c.index < pd.Timestamp(df.index[-1].year, now_m, 1)]
    mtd = (c.iloc[-1] / prev_close.iloc[-1] - 1) * 100 if len(prev_close) else None
    k = st.columns(4)
    k[0].markdown(T.kpi("north_east", L("Best month on average", "أفضل شهر في المتوسط"), mon[best - 1],
                        L(f"avg {st_['avg'][best]:+.2f}% · up {st_['win'][best]:.0f}% of years", f"متوسط {st_['avg'][best]:+.2f}% · إيجابي في {st_['win'][best]:.0f}% من السنوات"),
                        "pos"), unsafe_allow_html=True)
    k[1].markdown(T.kpi("south_east", L("Worst month on average", "أسوأ شهر في المتوسط"), mon[worst - 1],
                        L(f"avg {st_['avg'][worst]:+.2f}% · up {st_['win'][worst]:.0f}% of years", f"متوسط {st_['avg'][worst]:+.2f}% · إيجابي في {st_['win'][worst]:.0f}% من السنوات"),
                        "neg"), unsafe_allow_html=True)
    a_now, w_now = st_["avg"][now_m], st_["win"][now_m]
    k[2].markdown(T.kpi("event", L(f"{mon[now_m - 1]} historically", f"{mon[now_m - 1]} تاريخياً"), f"{a_now:+.2f}%",
                        L(f"positive in {w_now:.0f}% of years", f"إيجابي في {w_now:.0f}% من السنوات"), T.cls(a_now)), unsafe_allow_html=True)
    if mtd is not None:
        k[3].markdown(T.kpi("today", L(f"{mon[now_m - 1]} so far", f"{mon[now_m - 1]} حتى الآن"), f"{mtd:+.2f}%",
                            L("this month to date", "منذ بداية الشهر"), T.cls(mtd)), unsafe_allow_html=True)
    if pick != "other":
        name = L(*seas[pick])
    elif sa:
        import tasi
        name = tasi.name_of(sym, is_ar()) or sym
    else:
        name = sym
    span = (df.index[-1] - df.index[0]).days / 365.25
    if span < years - 0.5:
        st.caption(L(f"Only {span:.0f} years of history are available for {name}: the averages cover those years.",
                     f"المتاح من التاريخ لـ {name} هو {span:.0f} سنوات فقط، والمتوسطات محسوبة عليها."))
    ui.chart(charts.season_bars(mon, [float(x) for x in st_["avg"]], [float(x) for x in st_["win"]], now_m - 1,
                                L(f"{name}: average return by month (last {years} years)", f"{name}: متوسط العائد لكل شهر (آخر {years} سنة)"),
                                (L("Average return", "متوسط العائد"), L("Positive years", "السنوات الإيجابية"))), key="se_bars")
    a, b = st.columns([1, 1])
    recent = table.tail(10).iloc[::-1]          # newest year on top
    with a:
        if len(avg):
            ui.chart(charts.seasonal_path(avg, cur, L("The typical year vs this year", "السنة المعتادة مقابل هذه السنة"),
                                          (L("Average year", "السنة المتوسطة"), L("This year", "هذه السنة")), height=90 + 40 * len(recent),
                                          xlab=L("Trading day of the year", "يوم التداول في السنة")), key="se_path")
    with b:
        ui.chart(charts.monthly_heatmap(recent, L("Monthly returns, recent years", "العوائد الشهرية في السنوات الأخيرة"), months=mon), key="se_heat")
    ui.html(f'<div class="anote">{T.icon("lightbulb")}<span>{T.esc(L("Seasonality shows tendencies, not guarantees: a month that was positive 70% of the time was still negative in 3 years out of 10. Use it as context next to trend, valuation and news, never as a trading signal on its own.", "الموسمية تُظهر ميولاً وليست ضمانات: الشهر الذي كان إيجابياً 70% من الوقت كان سلبياً في 3 سنوات من كل 10. استخدمها كسياق بجانب الاتجاه والتقييم والأخبار، وليس كإشارة تداول وحدها."))}</span></div>')
    if sa:
        st.caption(L("KSA is the iShares MSCI Saudi Arabia ETF, priced in dollars; the riyal is pegged to the dollar, so its moves are the Saudi "
                     "market's. Months follow the Gregorian calendar, so Ramadan and the Eid holidays fall in a different month each year.",
                     "KSA هو صندوق iShares MSCI السعودية المتداول، مسعّر بالدولار، والريال مربوط بالدولار فحركته هي حركة السوق السعودي. الأشهر "
                     "ميلادية، لذلك رمضان والأعياد تقع في شهر مختلف كل سنة."))
    ui.foot()

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "22.5.1"
