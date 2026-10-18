"""
p_hunter_v3.py - Hunter V3 · Alpha Lab (menu: الصياد V3): the page of hunter_v3.py, which is untouched.

Its own look, not the hunter's: a lab in teal and cyan, the model at the centre.
Top to bottom:
  * a hero: the alpha ladder (the best-ranked stocks as bars: the rank and the forecast), the totals as chips,
  * the hunt bar: the universe, the paper capital and the risk settings, the Run button,
  * the model's board: the market mood, validation, training samples, the holdout IC and the exposure cap,
  * filters (setups with their counts, rank at least, new today, no risk flags, with a forecast only),
  * the best-ranked opportunities as cards (the rank ring, the forecast meter, the rank's three parts, the levels); click one
    to open it: the chart with entry / stop / target, why it ranked what it ranked, its line in the paper allocation,
  * the hypothetical allocation (tiles and the full table), every result with every column in a sortable table,
  * the forecast map (forecast vs V1 score) and the methodology.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import charts
import data
import hunter as H
import hunter_v3 as V3
import p_scanner as S
import paperbots as PB
import theme as T
import ui
import universe as U
from i18n import L, is_ar, sector_name
from sp500 import SP500

ss = st.session_state
_A, _V, _C, _G, _D, _U, _MU, _BD = T.ACCENT, T.VIOLET, T.CYAN, T.GOLD, T.DOWN, T.UP, "#9D97A5", T.BORDER
_E = "#2DD4BF"                                      # the lab's teal
DEFAULT = (
    "AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "META", "DIS",
    "JPM", "BAC", "WFC", "XOM", "CVX", "SLB", "UNH", "JNJ", "MRK",
    "AMZN", "HD", "MCD", "NKE", "WMT", "PG", "KO", "CAT", "DE",
    "UPS", "NEE", "DUK", "SO",
)
UNIS = {"core": ("Core 29", "الأساسية (29 سهم)"), "large": ("Largest 100", "أكبر 100 شركة"),
        "sp500": ("S&P 500 (all, slower)", "إس آند بي 500 (كامل، أبطأ)"), "custom": ("My symbols", "رموزي")}
PROFILES = {"risk_controlled": ("Risk-controlled", "مضبوط المخاطر"), "return_seeking": ("Return-seeking · higher risk", "استهداف عائد أعلى · مخاطرة أكبر")}
RISK_FLAG = {"stale_data": ("history", "Stale data", "بيانات قديمة"), "extreme_volatility": ("bolt", "Extreme volatility", "تذبذب شديد"),
             "illiquid": ("water_drop", "Illiquid", "سيولة ضعيفة"), "earnings": ("event", "Earnings soon", "أرباح قريبة"),
             "extended": ("height", "Stretched", "ممتد"), "thin": ("water_drop", "Thin trading", "سيولة ضعيفة")}
N_CARDS = 8
# The S&P 500 holds 503 shares (some companies list two classes), so the cap sits above it.
MAX_SCAN = 600

CSS = f"""<style>
/* ---------- hero: the alpha ladder, in the lab's teal ---------- */
.v3hero {{ position:relative; overflow:hidden; border-radius:22px; border:1px solid rgba(45,212,191,.28); margin:2px 0 16px; min-height:250px;
  background:linear-gradient(120deg,#07131C,#0B2230,#0E3545,#08141F); background-size:300% 300%; animation:sky 20s ease-in-out infinite; }}
.v3hero::after {{ content:""; position:absolute; left:0; right:0; top:0; height:1px; background:linear-gradient(90deg,transparent,rgba(45,212,191,.6),transparent); z-index:3; pointer-events:none; }}
.v3hero .grid {{ position:absolute; inset:0; pointer-events:none;
  background-image:linear-gradient(rgba(45,212,191,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(45,212,191,.07) 1px,transparent 1px);
  background-size:36px 36px; -webkit-mask-image:radial-gradient(ellipse at 78% 50%,#000 0%,transparent 66%); mask-image:radial-gradient(ellipse at 78% 50%,#000 0%,transparent 66%); }}
.v3hero.rtl .grid {{ -webkit-mask-image:radial-gradient(ellipse at 22% 50%,#000 0%,transparent 66%); mask-image:radial-gradient(ellipse at 22% 50%,#000 0%,transparent 66%); }}
.v3hero .art {{ position:absolute; top:0; bottom:0; right:0; width:50%; pointer-events:none; }}
.v3hero.rtl .art {{ right:auto; left:0; }}
.v3hero .art svg {{ width:100%; height:100%; display:block; }}
.v3hero .txt {{ position:relative; z-index:2; padding:26px 30px 24px; max-width:640px;
  background:linear-gradient(90deg,rgba(7,19,28,.82) 0%,rgba(7,19,28,.35) 72%,rgba(7,19,28,0) 100%); }}
.v3hero.rtl .txt {{ margin-left:auto; background:linear-gradient(270deg,rgba(7,19,28,.82) 0%,rgba(7,19,28,.35) 72%,rgba(7,19,28,0) 100%); }}
.v3hero .eb {{ color:{_E}; font-weight:600; letter-spacing:.2em; font-size:.72rem; text-transform:uppercase; display:flex; align-items:center; gap:8px; }}
.v3hero .t {{ font-size:2.7rem; font-weight:300; line-height:1.04; margin:8px 0 8px; color:#fff; letter-spacing:-.035em; }}
.v3hero .t b {{ background:linear-gradient(90deg,{_C},{_E},#A7F3D0); -webkit-background-clip:text; background-clip:text; color:transparent; font-weight:700; }}
.v3hero .tg {{ color:#CAD5D6; font-size:.94rem; line-height:1.6; max-width:540px; }}
.v3hero .chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
.v3hero .chip {{ background:rgba(7,19,28,.75); border:1px solid rgba(45,212,191,.25); backdrop-filter:blur(6px); border-radius:10px; padding:6px 10px;
  font-size:.8rem; display:inline-flex; align-items:center; gap:7px; color:#CAD5D6; }}
.v3hero .chip b {{ color:#fff; unicode-bidi:isolate; direction:ltr; }} .v3hero .chip .ms {{ color:{_E}; font-size:1rem; }}
.v3hero .st {{ margin-top:12px; }}
.v3hero .lad {{ animation:v3grow 1.1s cubic-bezier(.2,.8,.2,1) both; transform-origin:left center; }}
.v3hero.rtl .lad {{ transform-origin:right center; }}
@keyframes v3grow {{ from {{ transform:scaleX(0); }} }}
@media (max-width: 820px) {{ .v3hero .art {{ width:100%; opacity:.22; }} .v3hero .t {{ font-size:1.9rem; }} .v3hero .txt {{ background:none; }} }}
/* ---------- the model's board ---------- */
.v3reg {{ display:grid; grid-template-columns:1.5fr repeat(4,1fr); gap:10px; margin:2px 0 4px; }}
@media (max-width: 1000px) {{ .v3reg {{ grid-template-columns:1fr 1fr; }} }}
.v3reg .tl {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:12px 14px; position:relative; overflow:hidden; }}
.v3reg .tl::before {{ content:""; position:absolute; top:0; bottom:0; left:0; width:2px; background:linear-gradient(180deg,{_C},{_E}); opacity:.8; }}
.v3reg .tl .l {{ color:{_MU}; font-size:.68rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; display:flex; align-items:center; gap:6px; }}
.v3reg .tl .l .ms {{ font-size:.95rem; color:{_E}; }}
.v3reg .tl .v {{ font-size:1.35rem; font-weight:600; color:#fff; margin-top:4px; direction:ltr; unicode-bidi:isolate; }}
.v3reg .tl .s {{ color:{_MU}; font-size:.74rem; margin-top:2px; line-height:1.45; }}
.v3reg .tl.on {{ border-color:{_U}66; background:linear-gradient(135deg,rgba(34,197,94,.14),{T.CARD}); }}
.v3reg .tl.mixed {{ border-color:{_G}66; background:linear-gradient(135deg,rgba(245,185,74,.13),{T.CARD}); }}
.v3reg .tl.off {{ border-color:{_D}66; background:linear-gradient(135deg,rgba(239,68,68,.14),{T.CARD}); }}
.v3reg .tl.pass {{ border-color:{_E}66; background:linear-gradient(135deg,rgba(45,212,191,.14),{T.CARD}); }}
.v3reg .tl.fall {{ border-color:{_G}66; background:linear-gradient(135deg,rgba(245,185,74,.13),{T.CARD}); }}
.v3reg .mood .v {{ font-size:1.08rem; display:flex; align-items:center; gap:8px; direction:inherit; }}
.v3reg .mood .dot {{ width:10px; height:10px; border-radius:50%; box-shadow:0 0 0 4px rgba(255,255,255,.06); flex:none; }}
.v3reg .mood .s {{ color:#CAD5D6; }}
/* ---------- the cards: the hunter's frame with the lab's content ---------- */
.hnc.v3 {{ height:372px; }}
.hnc.v3::before {{ background:linear-gradient(90deg,transparent,rgba(45,212,191,.7),transparent); }}
.hnc.v3.sel {{ border-color:{_E} !important; box-shadow:0 0 0 1px {_E}66, 0 12px 30px rgba(45,212,191,.18); }}
[class*="st-key-hncard_v3"]:hover .hnc {{ box-shadow:0 14px 34px rgba(45,212,191,.18); }}
.hnc .su .ms {{ color:{_E}; }}
.v3al {{ margin:8px 0 2px; }}
.v3al .l {{ display:flex; justify-content:space-between; align-items:center; font-size:.62rem; font-weight:600; color:{_MU}; letter-spacing:.05em; text-transform:uppercase; }}
.v3al .l b {{ font-size:.8rem; letter-spacing:0; direction:ltr; unicode-bidi:isolate; }}
.v3al .l b.up {{ color:#4ADE80; }} .v3al .l b.dn {{ color:#F87171; }} .v3al .l b.na {{ color:{_MU}; }}
.v3al .m {{ position:relative; height:7px; border-radius:7px; background:rgba(157,151,165,.16); margin-top:4px; overflow:hidden; direction:ltr; }}
.v3al .m::before {{ content:""; position:absolute; left:50%; top:-2px; bottom:-2px; width:1px; background:rgba(255,255,255,.35); }}
.v3al .m i {{ position:absolute; top:0; bottom:0; border-radius:7px; }}
.v3al .m i.up {{ left:50%; background:linear-gradient(90deg,{_E},#4ADE80); }} .v3al .m i.dn {{ right:50%; background:linear-gradient(270deg,{_G},#F87171); }}
.v3pt {{ display:grid; grid-template-columns:repeat(3,1fr); gap:6px; margin:6px 0 6px; direction:ltr; }}
.v3pt div {{ min-width:0; }}
.v3pt span {{ display:block; color:{_MU}; font-size:.6rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.v3pt b {{ display:block; color:#fff; font-size:.78rem; font-weight:600; }}
.v3pt .bar {{ height:4px; border-radius:4px; background:rgba(157,151,165,.16); margin-top:3px; overflow:hidden; }}
.v3pt .bar i {{ display:block; height:100%; border-radius:4px; }}
.v3pt .v1 .bar i {{ background:{_A}; }} .v3pt .q .bar i {{ background:{_V}; }} .v3pt .al .bar i {{ background:{_E}; }}
.hnparts .r.al .bar i {{ background:linear-gradient(90deg,{_C},{_E}); }}
.hnparts .r.q .bar i {{ background:linear-gradient(90deg,{_V},{_C}); }}
.v3alloc {{ display:flex; flex-direction:column; gap:6px; margin-top:10px; }}
.v3alloc .check {{ display:flex; gap:9px; align-items:center; font-size:.84rem; color:#DDD9E2; padding:6px 0; border-bottom:1px solid rgba(157,151,165,.12); }}
.v3alloc .check b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }}
.v3alloc .check:last-child {{ border-bottom:0; }}
.v3tab {{ border:1px solid {_BD}; border-radius:16px; padding:8px 8px 4px; background:{T.BOX_BG}; }}
</style>"""


# ---------------------------------------------------------------- what to scan
def _symbols(choice, custom):
    if choice == "core":
        return DEFAULT
    if choice == "large":
        return tuple(dict.fromkeys(list(U.STOCKS)[:100]))
    if choice == "sp500":
        return tuple(SP500)
    out = [s.strip().upper() for s in str(custom or "").replace(";", ",").split(",")]
    return tuple(dict.fromkeys(x for x in out if x and len(x) < 12))


@st.cache_data(ttl=900, show_spinner=False, max_entries=6)
def _research(symbols):
    # All inputs on last completed daily bars, not real-time prices.
    prices = PB.load_prices(list(symbols), "3y")
    bench = data.history("SPY", "3y")
    sectors = {s: U.sector_of(s) for s in symbols}
    frame, fit, overview = V3.scan(prices, bench, sectors=sectors)
    return frame, fit, overview, prices


def _init():
    for k, v in {"v3_uni": "core", "v3_custom": "AAPL, MSFT, NVDA, AMZN", "v3_cap": 100_000.0, "v3_risk": .5, "v3_maxpos": 5,
                 "v3_seclim": 2, "v3_profile": "risk_controlled", "v3_grade": "all", "v3_clean": False, "v3_alpha": False,
                 "v3_fresh": False}.items():
        ss.setdefault(k, v)


def _go():
    ss["v3_run"] = _symbols(ss.get("v3_uni"), ss.get("v3_custom"))
    ss["v3_sel"] = None


def _alpha_txt(a):
    return f"{a:+.1f}%" if pd.notna(a) else "—"


def _alpha_cls(a):
    return "na" if pd.isna(a) else ("up" if a >= 0 else "dn")


# ---------------------------------------------------------------- hero
def _ladder(frame, rtl=False):
    """The alpha ladder: the seven best-ranked stocks as bars (the rank), each with its forecast; the lab's own picture."""
    s = ['<svg viewBox="0 0 520 250" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" style="direction:ltr">'
         '<defs><linearGradient id="v3lg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#2DB6EB"/><stop offset="1" stop-color="#2DD4BF"/></linearGradient>'
         '<filter id="v3gl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/>'
         '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>']
    top = frame.head(7) if frame is not None and len(frame) else pd.DataFrame()
    x0, w = (60, 300) if not rtl else (160, 300)
    for i, r in enumerate(top.itertuples()):
        y = 28 + i * 31
        rk = float(r.Rank)
        bw = w * rk / 100
        col = S.GRADE_COLOR.get(H.grade(rk), _C)
        al = frame.loc[r.Index, "Alpha %"]
        acol = "#4ADE80" if pd.notna(al) and al >= 0 else "#F87171" if pd.notna(al) else "#9D97A5"
        bx = x0 if not rtl else x0 + w - bw
        s.append(f'<rect x="{x0}" y="{y}" width="{w}" height="12" rx="6" fill="rgba(45,212,191,.10)"/>'
                 f'<rect class="lad" x="{bx:.0f}" y="{y}" width="{bw:.0f}" height="12" rx="6" fill="url(#v3lg)" style="animation-delay:{i * .08:.2f}s"/>'
                 f'<circle cx="{(x0 + bw) if not rtl else bx:.0f}" cy="{y + 6}" r="5" fill="{col}" filter="url(#v3gl)"/>')
        lx = x0 - 8 if not rtl else x0 + w + 8
        s.append(f'<text x="{lx}" y="{y + 10}" text-anchor="{"end" if not rtl else "start"}" font-size="11" font-weight="800" fill="#fff" '
                 f'font-family="{T.FONT}">{T.esc(T.sym_label(r.Symbol))}</text>')
        vx = x0 + w + 10 if not rtl else x0 - 10
        s.append(f'<text x="{vx}" y="{y + 10}" text-anchor="{"start" if not rtl else "end"}" font-size="10" font-weight="700" fill="{col}" '
                 f'font-family="{T.FONT}">{rk:.0f}</text>'
                 f'<text x="{vx + (26 if not rtl else -26)}" y="{y + 10}" text-anchor="{"start" if not rtl else "end"}" font-size="9.5" fill="{acol}" '
                 f'font-family="{T.FONT}">{_alpha_txt(al)}</text>')
    if len(top):
        s.append(f'<text x="{x0 if not rtl else x0 + w}" y="246" text-anchor="{"start" if not rtl else "end"}" font-size="9" fill="#7FA7AC" font-family="{T.FONT}">'
                 f'{T.esc(L("rank 0-100 · forecast 20 sessions vs SPY", "الترتيب من 100 · التوقع 20 جلسة مقابل المؤشر"))}</text>')
    return "".join(s) + "</svg>"


def hero_html(frame, fit, market, label):
    chips = []
    if frame is not None and len(frame):
        active = fit.get("status") == "active"
        chips.append(f'<span class="chip">{T.icon("radar")}{L("Scanned", "تم فحص")} <b>{market.get("universe", 0):,}</b> · {T.esc(label)}</span>')
        chips.append(f'<span class="chip">{T.icon("target")}{L("Eligible opportunities", "الفرص المؤهلة")} <b>{market.get("eligible_longs", 0)}</b></span>')
        chips.append(f'<span class="chip">{T.icon("psychology")}{L("Model", "النموذج")} <b>{L("validated", "مُعتمد") if active else L("fallback", "بديل")}</b></span>')
        chips.append(f'<span class="chip">{T.icon("bolt")}{L("New today", "جديدة اليوم")} <b>{int((frame["Status"] == "fresh").sum())}</b></span>')
        chips.append(f'<span class="chip">{T.icon("schedule")}{L("Last data", "آخر بيانات")} <b>{T.esc(str(market.get("date", "—")))}</b></span>')
    tag = L("An independent, experimental signal-ranking engine: a ridge model, validated on a purged chronological holdout, forecasts "
            "each stock's 20-session return over SPY; the rank blends the hunter's score, technical quality and that forecast, "
            "with a capped paper allocation. Research only.",
            "محرك ترتيب تجريبي مستقل: نموذج إحصائي، مُختبر على فترة تاريخية مستقلة، يتوقع عائد كل سهم الزائد على المؤشر خلال 20 جلسة، "
            "والترتيب يجمع تقييم الصياد والجودة الفنية والتوقع، مع محفظة افتراضية محدودة الانكشاف. أبحاث فقط.")
    return (f'<div class="v3hero{" rtl" if is_ar() else ""}"><div class="grid"></div><div class="art">{_ladder(frame, is_ar())}</div>'
            f'<div class="txt"><div class="eb">{T.icon("science")}{L("Alpha Lab · quant research", "مختبر ألفا · بحث كمي")}</div>'
            f'<div class="t">{L("Hunter <b>V3</b>", "الصياد <b>V3</b>")}</div><div class="tg">{T.esc(tag)}</div>'
            f'<div class="chips">{"".join(chips)}</div><div class="st">{T.market_status(is_ar(), "us")}</div></div></div>')


# ---------------------------------------------------------------- the hunt bar
def hunt_bar():
    with st.container(key="hnbar_v3"):
        c = st.columns([1.9, 2.6, 1.1], vertical_alignment="bottom")
        c[0].selectbox(L("What to scan", "وش أفحص"), list(UNIS), key="v3_uni", format_func=lambda k: L(*UNIS[k]))
        if ss.get("v3_uni") == "custom":
            c[1].text_input(L("Symbols (comma separated)", "الرموز (مفصولة بفاصلة)"), key="v3_custom", placeholder="AAPL, MSFT, NVDA")
        else:
            n = len(_symbols(ss.get("v3_uni"), ""))
            note = L(f"{n:,} US stocks · daily bars · 3 years of history.", f"{n:,} سهم أمريكي · شموع يومية · 3 سنوات تاريخ.")
            if ss.get("v3_uni") == "sp500":
                note += L(" The whole S&P 500 takes a minute or two the first time, then it is kept for 15 minutes.",
                          " إس آند بي 500 كامل ياخذ دقيقة أو دقيقتين أول مرة، وبعدها ينحفظ 15 دقيقة.")
            c[1].caption(note)
        c[2].button(L("Run V3", "شغّل V3"), icon=":material/science:", key="hn_go_v3", on_click=_go, width="stretch")
        d = st.columns([1.3, 1.2, 1, 1, 1.9], vertical_alignment="bottom")
        d[0].number_input(L("Paper capital ($)", "رأس مال افتراضي ($)"), min_value=1_000., max_value=10_000_000., step=10_000., key="v3_cap")
        d[1].slider(L("Risk budget / trade", "مخاطرة الصفقة"), min_value=.1, max_value=2.0, step=.1, format="%.1f%%", key="v3_risk")
        d[2].slider(L("Max holdings", "الحد الأقصى للمراكز"), 1, 15, key="v3_maxpos")
        d[3].slider(L("Max names / sector", "الحد الأقصى لكل قطاع"), 1, 6, key="v3_seclim")
        d[4].segmented_control(L("Paper allocation profile", "نوع المحفظة الافتراضية"), list(PROFILES), key="v3_profile",
                               format_func=lambda k: L(*PROFILES[k]))
        if not ss.get("v3_profile"):
            ss["v3_profile"] = "risk_controlled"


# ---------------------------------------------------------------- the model's board
def board_html(fit, market):
    active = fit.get("status") == "active"
    ic = fit.get("holdout_ic")
    ic_s = f"{float(ic):+.3f}" if ic is not None and np.isfinite(float(ic)) else "—"
    mood = market.get("mood", "mixed")
    head = {"on": ("Risk-on: full exposure", "السوق إيجابي: انكشاف كامل", _U), "mixed": ("Mixed: reduced exposure", "السوق متذبذب: انكشاف مخفّض", _G),
            "off": ("Risk-off: minimal exposure", "السوق سلبي: أقل انكشاف", _D)}.get(mood, ("Unknown", "غير معروف", _MU))
    tip = {"on": ("Most stocks above their averages: the allocation may use all the paper capital.", "أغلب الأسهم فوق متوسطاتها: المحفظة تقدر تستخدم كل رأس المال."),
           "mixed": ("A selective market: the allocation keeps part of the capital in cash.", "سوق انتقائي: المحفظة تبقي جزء من رأس المال نقدًا."),
           "off": ("A weak market: the allocation keeps most of the capital in cash.", "سوق ضعيف: المحفظة تبقي أغلب رأس المال نقدًا.")}.get(mood, ("", ""))
    expo = {"on": 100, "mixed": 65, "off": 25}.get(mood, 65)
    if ss.get("v3_profile") == "return_seeking":
        expo = 100 if mood in ("on", "mixed") else 70
    tiles = [
        f'<div class="tl mood {mood}"><div class="l">{T.icon("explore")}{L("Market mood", "مزاج السوق")}</div>'
        f'<div class="v"><span class="dot" style="background:{head[2]}"></span>{T.esc(L(head[0], head[1]))}</div><div class="s">{T.esc(L(*tip))}</div></div>',
        f'<div class="tl {"pass" if active else "fall"}"><div class="l">{T.icon("verified" if active else "warning")}{L("Model validation", "حالة النموذج")}</div>'
        f'<div class="v">{L("Validated", "مُعتمد") if active else L("Fallback", "ترتيب بديل")}</div>'
        f'<div class="s">{L("the forecast is on: it beat its baseline on the holdout", "التوقع شغّال: تفوق على مرجعه في فترة التحقق") if active else L("the forecast is off: a transparent rank without predictions", "التوقع متوقف: ترتيب شفاف بدون توقعات")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("dataset")}{L("Training samples", "عينات التدريب")}</div><div class="v">{int(fit.get("n", 0) or 0):,}</div>'
        f'<div class="s">{L("labeled outcomes, 20 sessions ahead", "نتائج معلومة، 20 جلسة للأمام")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("insights")}{L("Validation IC", "ارتباط التحقق")}</div><div class="v">{ic_s}</div>'
        f'<div class="s">{L("forecast vs realized, out of sample · benchmark SPY", "التوقع مقابل الفعلي خارج العينة · المؤشر SPY")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("shield")}{L("Exposure cap", "حد الانكشاف")}</div><div class="v">{expo}%</div>'
        f'<div class="s">{L("of the paper capital, from the mood and the profile", "من رأس المال الافتراضي، حسب المزاج ونوع المحفظة")}</div></div>']
    return '<div class="v3reg">' + "".join(tiles) + "</div>"


# ---------------------------------------------------------------- filters
def filters(frame, fit):
    counts = frame["Setups"].str.split(",").explode().value_counts()
    keys = [k for k in H.ORDER if counts.get(k, 0)]
    if "v3_setups" in ss:
        ss["v3_setups"] = [k for k in ss["v3_setups"] if k in keys]
    with st.container(key="hnfilt_v3"):
        ui.html(f'<div class="hnfh">{T.icon("filter_alt")}<b>{L("Filters", "التصفية")}</b>'
                f'<span>{L("Pick setups to see only them; with none picked, every eligible long shows.", "اختر فرص عشان تشوفها بس؛ وبدون اختيار تظهر كل الفرص المؤهلة.")}</span></div>')
        st.pills(L("Setups", "الفرص"), keys, selection_mode="multi", key="v3_setups", label_visibility="collapsed",
                 format_func=lambda k: f"{S.short_name(k)} · {int(counts.get(k, 0))}")
        c = st.columns([1.55, 1, 1.15, 1], vertical_alignment="bottom")
        c[0].segmented_control(L("Rank at least", "الترتيب على الأقل"), list(S.MIN_GRADE), key="v3_grade",
                               format_func=lambda g: L("All", "الكل") if g == "all" else f"{g} · {S.MIN_GRADE[g]}")
        c[1].toggle(L("New today", "الجديدة اليوم"), key="v3_fresh")
        c[2].toggle(L("No risk flags", "بدون تحذيرات"), key="v3_clean")
        c[3].toggle(L("With a forecast", "مع توقع"), key="v3_alpha", disabled=fit.get("status") != "active")


def apply(frame):
    v = frame[(frame["Side"] > 0) & (frame["Rank"] >= 50)].copy()
    picks = ss.get("v3_setups") or []
    if picks:
        v = v[v["Setups"].apply(lambda s: any(k in str(s).split(",") for k in picks))]
    v = v[v["Rank"] >= S.MIN_GRADE.get(ss.get("v3_grade") or "all", 0)]
    if ss.get("v3_fresh"):
        v = v[v["Status"] == "fresh"]
    if ss.get("v3_clean"):
        v = v[~v["Risk Flag"].astype(str).str.contains("illiquid|stale_data|extreme_volatility", na=False)]
    if ss.get("v3_alpha"):
        v = v[v["Alpha %"].notna()]
    return v.sort_values(["Rank", "V1 Score"], ascending=False)


# ---------------------------------------------------------------- cards
def _flags(r):
    out = []
    for f in [x for x in str(r.get("Risk Flag") or "").split(",") if x]:
        ic, en, ar_ = RISK_FLAG.get(f, ("flag", f, f))
        out.append((ic, L(en, ar_)))
    return out


def _spark(prices, sym):
    d = prices.get(sym)
    return d["Close"].tail(63).tolist() if d is not None and "Close" in d else []


def _parts(r, mood):
    """The rank's parts: (class, label, weight %, value 0-100), as hunter_v3.scan blends them."""
    v1, q, alpha = float(r["V1 Score"]), V3._technical_quality(r, mood), r["Alpha %"]
    if pd.notna(alpha):
        return [("v1", L("Hunter score", "تقييم الصياد"), 55, v1), ("q", L("Technical quality", "الجودة الفنية"), 20, q),
                ("al", L("Forecast", "التوقع"), 25, float(np.clip(50 + 3 * alpha, 0, 100)))]
    return [("v1", L("Hunter score", "تقييم الصياد"), 75, v1), ("q", L("Technical quality", "الجودة الفنية"), 25, q)]


def alpha_meter(alpha):
    """The forecast as a meter round zero: -15% at the left edge, +15% at the right."""
    if pd.isna(alpha):
        return (f'<div class="v3al"><div class="l"><span>{L("Forecast 20 sessions vs SPY", "التوقع 20 جلسة مقابل المؤشر")}</span><b class="na">—</b></div>'
                f'<div class="m"></div></div>')
    w = min(50.0, abs(float(alpha)) / 15 * 50)
    return (f'<div class="v3al"><div class="l"><span>{L("Forecast 20 sessions vs SPY", "التوقع 20 جلسة مقابل المؤشر")}</span><b class="{_alpha_cls(alpha)}">{alpha:+.2f}%</b></div>'
            f'<div class="m"><i class="{_alpha_cls(alpha)}" style="width:{w:.1f}%"></i></div></div>')


def card(r, prices, mood, selected):
    sym, k = r["Symbol"], r["Setup"]
    ic = H.SETUPS[k][2] if k in H.SETUPS else "radar"
    entry, stop, tgt = r["Entry"], r["Stop"], r["Target"]
    rank = float(r["Rank"])
    top = (f'<div class="top"><span class="su">{T.icon(ic)}<span class="tx">{T.esc(S.short_name(k))}</span></span>'
           f'{S.status_tag(r["Status"], r["Age"])}</div>')
    go_ = L(f"Open the {T.sym_label(sym)} page", f"افتح صفحة {T.sym_label(sym)}")
    chg = r.get("Chg %")
    px = ""
    if np.isfinite(r["Price"]):
        pill = f'<i class="{"up" if chg >= 0 else "dn"}">{chg:+.2f}%</i>' if chg is not None and np.isfinite(chg) else ""
        px = f'<div class="px"><b>{S._money_px(r["Price"])}</b>{pill}</div>'
    hd = (f'<div class="hd"><a class="co" href="{T.esc(ui.href(sym))}" target="_self" title="{T.esc(go_)}">{T.logo_obj(sym, 36)}'
          f'<div class="nm"><b>{T.esc(T.sym_label(sym))}</b><span>{T.esc(T.name_line(sym, str(r["Name"])))}</span>{px}</div></a>'
          f'{S.ring(rank, H.grade(rank))}</div>')
    sp = f'<div class="spk">{S.spark(_spark(prices, sym), entry, stop, tgt, S._key(sym))}</div>'
    pt = '<div class="v3pt">' + "".join(f'<div class="{c_}"><span>{T.esc(l_)} · {w}%</span><b>{v:.0f}</b><div class="bar"><i style="width:{v:.0f}%"></i></div></div>'
                                        for c_, l_, w, v in _parts(r, mood)) + "</div>"
    watch = r["Status"] == "watch"
    lv = (f'<div class="lv"><div><span>{L("Buy above", "شراء فوق") if watch else L("Entry", "الدخول")}</span><b>{S._money_px(entry)}</b></div>'
          f'<div><span>{L("Stop", "الوقف")}</span><b>{S._money_px(stop)}</b><i class="dn">{S._pct(entry, stop):+.1f}%</i></div>'
          f'<div><span>{L("Target", "الهدف")}</span><b>{S._money_px(tgt)}</b><i class="up">{S._pct(entry, tgt):+.1f}%</i></div></div>') if np.isfinite(entry) else ""
    chips = [f'<span class="c">RS <b>{int(r["RS"])}</b></span>']
    if np.isfinite(r["R:R"]):
        chips.append(f'<span class="c">R:R <b>{r["R:R"]:.1f}</b></span>')
    if np.isfinite(r["ATR %"]):
        chips.append(f'<span class="c">ATR <b>{r["ATR %"]:.1f}%</b></span>')
    for ic_, txt in _flags(r):
        chips.insert(0, f'<span class="c w">{T.icon(ic_)}{T.esc(txt)}</span>')
    return f'<div class="card hnc v3{" sel" if selected else ""}">{top}{hd}{sp}{alpha_meter(r["Alpha %"])}{pt}{lv}<div class="ft">{"".join(chips)}</div></div>'


def _pick(sym):
    ss["v3_sel"] = sym


def cards(view, prices, mood):
    top = view.head(N_CARDS)
    sel = ss.get("v3_sel")
    rows = list(top.iterrows())
    for i in range(0, len(rows), 4):
        cols = st.columns(4)
        for col, (_, r) in zip(cols, rows[i:i + 4]):
            with col:
                with st.container(key=f"hncard_v3_{S._key(r['Symbol'])}"):
                    ui.html(card(r, prices, mood, r["Symbol"] == sel))
                    st.button(r["Symbol"], key=f"hn_pick_v3_{S._key(r['Symbol'])}", on_click=_pick, args=(r["Symbol"],), width="stretch")


# ---------------------------------------------------------------- the opened opportunity
def detail(r, prices, market, selected):
    sym, k = r["Symbol"], r["Setup"]
    rank, v1, alpha = float(r["Rank"]), float(r["V1 Score"]), r["Alpha %"]
    with st.container(key=f"hnsec_v3_head_{S._key(sym)}"):
        badges = T.badge(sector_name(r["Sector"]) if r["Sector"] else "—", "gold", "category")
        badges += T.badge(f'{L("Hunter", "الصياد")} {H.grade(v1)} · {v1:.0f}', "acc", "radar")
        if k in H.SETUPS and r["Status"] in H.STATUS:
            badges += T.badge(S.setup_name(k) + " · " + L(*H.STATUS[r["Status"]][:2]), H.STATUS[r["Status"]][2], H.SETUPS[k][2])
        for ic_, txt in _flags(r):
            badges += T.badge(txt, "gold", ic_)
        nm_ = T.sym_label(sym)
        ui.html(f'<div class="card hndh"><a class="co" href="{T.esc(ui.href(sym))}" target="_self" title="{T.esc(L(f"Open the {nm_} page", f"افتح صفحة {nm_}"))}">'
                f'{T.logo_obj(sym, 48)}<div class="nm"><b>{T.esc(nm_)}</b><span>{T.esc(T.name_line(sym, str(r["Name"])))}</span></div></a>'
                f'{S.ring(rank, H.grade(rank), 62)}<div class="bd">{badges}</div>'
                f'<div class="px"><b>{S._money_px(r["Price"])}</b>{T.pill(r["Chg %"])}</div></div>')
        if k in H.SETUPS:
            ui.html(f'<div class="hnnote" style="margin-top:10px">{T.icon(H.SETUPS[k][2], _E)} <b>{T.esc(S.setup_name(k))}:</b> '
                    f'{T.esc(L(H.SETUPS[k][6], H.SETUPS[k][7]))}</div>')

    d = prices.get(sym)
    with st.container(key=f"hnsec_v3_body_{S._key(sym)}"):
        left, right = st.columns([1.7, 1], gap="medium")
        with left:
            if d is not None and len(d) > 20:
                levels = ([(L("Entry", "دخول"), r["Entry"], _A, "solid"), (L("Stop", "وقف"), r["Stop"], _D, "dash"),
                           (L("Target", "هدف"), r["Target"], _U, "dash")] if np.isfinite(r["Entry"]) else None)
                dd = d.dropna(subset=["Close"]).tail(190)
                ui.chart(charts.price_chart(dd, "Candles", [], [], False, levels=levels, height=430), key=f"hn_chart_v3_{S._key(sym)}")
            k4 = st.columns(4)
            k4[0].metric(L("V3 rank", "ترتيب V3"), f"{rank:.1f}/100")
            k4[1].metric(L("Hunter V1 score", "تقييم الصياد V1"), f"{v1:.1f}/100")
            k4[2].metric(L("Forecast 20d excess", "العائد الزائد المتوقع 20 جلسة"), f"{alpha:+.2f}%" if pd.notna(alpha) else "—")
            k4[3].metric(L("Reward / Risk", "العائد / المخاطرة"), f"{r['R:R']:.2f}" if pd.notna(r["R:R"]) else "—")
            if np.isfinite(r["Entry"]) and int(r["Side"] or 0) > 0:
                entry, stop, tgt = float(r["Entry"]), float(r["Stop"]), float(r["Target"])
                watch = r["Status"] == "watch"
                tiles = [("en", L("Buy above", "شراء فوق") if watch else L("Entry", "الدخول"), S._money_px(entry),
                          L("on a close above it", "بإغلاق فوقه") if watch else L("next open, near this price", "الافتتاح القادم، قرب هذا السعر")),
                         ("sl", L("Stop loss", "وقف الخسارة"), S._money_px(stop), f"{S._pct(entry, stop):+.1f}%"),
                         ("tp", L("Target", "الهدف"), S._money_px(tgt), f"{S._pct(entry, tgt):+.1f}%"),
                         ("", "ATR (14)", f"{r['ATR %']:.1f}%", L("a day", "يومياً")),
                         ("", L("Traded a day", "التداول اليومي"), T.money(r["$Vol"], short=True), L("dollar volume", "قيمة التداول")),
                         ("", L("Exposure", "الانكشاف"), f"{float(r.get('Exposure', 1)) * 100:.0f}%", L("the regime's scale", "حسب حالة السوق"))]
                ui.html('<div class="hnplan" style="margin-top:8px">' + "".join(f'<div class="p {c_}"><div class="l">{T.esc(l_)}</div><div class="v">{v_}</div>'
                                                                                 f'<div class="s">{T.esc(s_)}</div></div>' for c_, l_, v_, s_ in tiles) + "</div>")
        with right:
            ui.sec("donut_large", "Why this rank", "ليش هالترتيب")
            ui.html('<div class="hnparts">' + "".join(
                f'<div class="r {c_}"><span>{T.esc(l_)} <span class="w">· {w}%</span></span>'
                f'<div class="bar"><i style="width:{float(v):.0f}%"></i></div><b>{float(v):.0f}</b></div>' for c_, l_, w, v in _parts(r, market.get("mood", "mixed"))) + "</div>")
            if str(r["Risk Flag"] or "") or r["Side"] <= 0:
                st.caption(L("A risk flag (or no buying setup) caps the rank at 49.", "تحذير المخاطر (أو غياب فرصة شراء) يحدّ الترتيب عند 49."))
            ui.html(alpha_meter(alpha))
            line = selected[selected["Symbol"] == sym] if len(selected) else pd.DataFrame()
            if len(line):
                a = line.iloc[0]
                items = [("inventory_2", f'{L("Shares", "الأسهم")}: <b>{int(a["Shares"]):,}</b>'),
                         ("payments", f'{L("Notional", "القيمة")}: <b>{T.money(a["Notional"])}</b> · {a["Weight %"]:.1f}% {L("of the capital", "من رأس المال")}'),
                         ("shield", f'{L("Risk at the stop", "الخسارة عند الوقف")}: <b>{T.money(a["Stop Risk $"])}</b>')]
                chip = S.score_chip(L("in the plan", "ضمن الخطة"), True)
            else:
                items = [("do_not_disturb_on", L("Not in the paper allocation: the rank, a risk flag, the sector limit, the position cap or the cash left it out.",
                                                 "خارج المحفظة الافتراضية: الترتيب أو تحذير المخاطر أو حد القطاع أو حد المراكز أو النقد المتبقي استبعدوه."))]
                chip = S.score_chip(L("not in the plan", "خارج الخطة"), False)
            ui.html(f'<div class="hnbox" style="margin-top:12px"><div class="hnbt">{T.icon("account_balance_wallet")}<span>{L("Paper allocation", "المحفظة الافتراضية")}</span>{chip}</div>'
                    f'<div class="v3alloc">' + "".join(f'<div class="check">{T.ico(ic, "acc")}<div>{t}</div></div>' for ic, t in items) + "</div></div>")


# ---------------------------------------------------------------- allocation and the tables
def _cfg(**cols):
    return {k: v for k, v in cols.items() if v is not None}


def allocation(selected, allocations, profile):
    ui.sec("account_balance_wallet", "Hypothetical allocation · no live orders", "محفظة افتراضية · بدون أوامر حقيقية")
    tiles = [("en", L("Invested", "نسبة الاستثمار"), f"{allocations['invested_pct']:.1f}%", L("of the paper capital", "من رأس المال الافتراضي")),
             ("", L("Cash", "النقد"), T.money(allocations["remaining_cash"]), L("left after sizing", "المتبقي بعد التوزيع")),
             ("", L("Exposure limit", "حد الانكشاف"), f"{allocations['market_exposure_cap_pct']:.0f}%", L("from the mood and the profile", "حسب مزاج السوق ونوع المحفظة")),
             ("tp", L("Positions", "المراكز"), f"{allocations['positions']}", L(*PROFILES[profile]))]
    ui.html('<div class="hnplan">' + "".join(f'<div class="p {c_}"><div class="l">{T.esc(l_)}</div><div class="v">{v_}</div>'
                                             f'<div class="s">{T.esc(s_)}</div></div>' for c_, l_, v_, s_ in tiles) + "</div>")
    if len(selected):
        show = selected.copy()
        show["Sector"] = show["Sector"].map(lambda s: sector_name(s) if s else "—")
        N = {"Symbol": L("Symbol", "الرمز"), "Sector": L("Sector", "القطاع"), "Shares": L("Shares", "الأسهم"), "Entry": L("Entry", "الدخول"),
             "Stop": L("Stop", "الوقف"), "Notional": L("Notional ($)", "القيمة ($)"), "Weight %": L("Weight %", "الوزن %"),
             "Stop Risk $": L("Risk at stop ($)", "الخسارة عند الوقف ($)"), "Alpha %": L("Forecast %", "التوقع %"), "Rank": L("V3 rank", "ترتيب V3")}
        st.dataframe(show.rename(columns=N), hide_index=True, width="stretch",
                     column_config=_cfg(**{N["Rank"]: st.column_config.ProgressColumn(N["Rank"], min_value=0, max_value=100, format="%.1f"),
                                           N["Weight %"]: st.column_config.ProgressColumn(N["Weight %"], min_value=0, max_value=100, format="%.1f%%"),
                                           N["Alpha %"]: st.column_config.NumberColumn(N["Alpha %"], format="%+.2f%%"),
                                           N["Notional"]: st.column_config.NumberColumn(N["Notional"], format="$%,.0f"),
                                           N["Stop Risk $"]: st.column_config.NumberColumn(N["Stop Risk $"], format="$%,.0f"),
                                           N["Entry"]: st.column_config.NumberColumn(N["Entry"], format="%.2f"),
                                           N["Stop"]: st.column_config.NumberColumn(N["Stop"], format="%.2f")}))
    else:
        st.info(L("No positions meet sizing and risk constraints today.", "ما فيه مراكز تستوفي شروط الحجم والمخاطرة اليوم."), icon=":material/info:")
    if profile == "return_seeking":
        st.warning(L("Return-seeking mode can stay substantially exposed in bear markets. Higher exposure can amplify losses; it is not a higher-return guarantee.",
                     "وضع استهداف العائد قد يحتفظ بانكشاف كبير حتى بالسوق الهابط، وقد يضاعف الخسائر ولا يضمن عائدًا أعلى."), icon=":material/warning:")
    st.caption(L("Stop prices may gap through; modeled risk budgets cannot cap realized losses. Prices may be delayed. No auto orders, derivatives or leverage.",
                 "قد ينفذ وقف الخسارة بسعر أسوأ عند وجود فجوة. تحديد المخاطرة لا يضمن سقفًا للخسارة. الأسعار قد تتأخر، ولا يوجد تداول فعلي أو مشتقات أو رافعة."))


def table(frame):
    """Every result with every column of the engine's frame, sortable, in the lab's order: the V3 columns first, then the
    hunter's measurements. Hidden here: the rank's internal parts and the breadth flags (Trend, Accum, SetupPts, RiskPts,
    Above50, Above200, NewHigh, NewLow, Side, Model Active)."""
    cols = ["Symbol", "Name", "Sector", "Rank", "V1 Score", "Alpha %", "Setup", "Status", "Age", "Setups", "Price", "Chg %", "Entry", "Stop", "Target",
            "R:R", "ATR %", "$Vol", "Risk Flag", "Exposure", "RS", "RVOL", "RSI", "ADX", "1M %", "3M %", "6M %", "From high %", "Earnings", "Flags"]
    show = frame[[c for c in cols if c in frame.columns]].copy()
    show["Sector"] = show["Sector"].map(lambda s: sector_name(s) if s else "—")
    show["Setup"] = show["Setup"].map(S.setup_name)
    show["Setups"] = show["Setups"].map(lambda s: " · ".join(S.short_name(k) for k in str(s or "").split(",") if k) or "—")
    show["Status"] = show["Status"].map(lambda s: L(*H.STATUS[s][:2]) if s in H.STATUS else "—")
    show["Risk Flag"] = show["Risk Flag"].map(lambda s: " · ".join(L(*RISK_FLAG[f][1:]) if f in RISK_FLAG else f for f in str(s or "").split(",") if f) or "—")
    show["Flags"] = show["Flags"].map(lambda s: " · ".join(L(*RISK_FLAG[f][1:]) if f in RISK_FLAG else f for f in str(s or "").split(",") if f) or "—")
    show["Exposure"] = show["Exposure"].astype(float) * 100
    N = {"Symbol": L("Symbol", "الرمز"), "Name": L("Company", "الشركة"), "Sector": L("Sector", "القطاع"), "Rank": L("V3 rank", "ترتيب V3"),
         "V1 Score": L("V1 score", "تقييم الصياد"), "Alpha %": L("Forecast %", "التوقع %"), "Setup": L("Setup", "الفرصة"), "Status": L("Status", "الحالة"),
         "Age": L("Age (days)", "العمر (أيام)"), "Setups": L("All setups", "كل الفرص"), "Price": L("Price", "السعر"), "Chg %": L("Chg %", "التغير %"),
         "Entry": L("Entry", "الدخول"), "Stop": L("Stop", "الوقف"), "Target": L("Target", "الهدف"), "R:R": "R:R", "ATR %": L("ATR %", "التذبذب %"),
         "$Vol": L("Traded/day ($)", "التداول اليومي ($)"), "Risk Flag": L("Risk flags", "تحذيرات المخاطر"), "Exposure": L("Exposure %", "الانكشاف %"),
         "RS": "RS", "RVOL": "RVOL", "RSI": "RSI", "ADX": "ADX", "1M %": L("1M %", "شهر %"), "3M %": L("3M %", "3 أشهر %"), "6M %": L("6M %", "6 أشهر %"),
         "From high %": L("From 52W high %", "عن القمة السنوية %"), "Earnings": L("Earnings in (days)", "الأرباح بعد (أيام)"), "Flags": L("Hunter flags", "تنبيهات الصياد")}
    show = show.rename(columns=N)
    pct = lambda name, f="%+.1f%%": st.column_config.NumberColumn(name, format=f)
    cfg = {N["Rank"]: st.column_config.ProgressColumn(N["Rank"], min_value=0, max_value=100, format="%.1f"),
           N["V1 Score"]: st.column_config.ProgressColumn(N["V1 Score"], min_value=0, max_value=100, format="%.1f"),
           N["Alpha %"]: pct(N["Alpha %"], "%+.2f%%"), N["Chg %"]: pct(N["Chg %"], "%+.2f%%"), N["1M %"]: pct(N["1M %"]), N["3M %"]: pct(N["3M %"]),
           N["6M %"]: pct(N["6M %"]), N["From high %"]: pct(N["From high %"]), N["ATR %"]: pct(N["ATR %"], "%.1f%%"), N["Exposure"]: pct(N["Exposure"], "%.0f%%"),
           N["Price"]: pct(N["Price"], "%.2f"), N["Entry"]: pct(N["Entry"], "%.2f"), N["Stop"]: pct(N["Stop"], "%.2f"), N["Target"]: pct(N["Target"], "%.2f"),
           "R:R": pct("R:R", "%.2f"), N["$Vol"]: pct(N["$Vol"], "$%,.0f"), "RVOL": pct("RVOL", "%.2f×"), "RSI": pct("RSI", "%.0f"), "ADX": pct("ADX", "%.0f"),
           N["Earnings"]: pct(N["Earnings"], "%.0f"), N["Age"]: pct(N["Age"], "%.0f"),
           N["Symbol"]: st.column_config.TextColumn(N["Symbol"], pinned=True)}
    st.dataframe(show, hide_index=True, width="stretch", height=520, column_config=cfg)
    st.caption(L(f"{len(show)} stocks · click a column header to sort · every column of the engine's output.",
                 f"{len(show)} سهم · اضغط على عنوان العمود للترتيب · كل أعمدة مخرجات المحرك."))
    st.download_button(L("Export V3 research CSV", "تصدير نتائج V3"), data=frame.to_csv(index=False).encode("utf-8-sig"),
                       file_name="tura-hunter-v3-research.csv", mime="text/csv", icon=":material/download:", key="v3_csv")


def forecast_map(frame, fit):
    """The lab's map: the forecast (or, without a model, the technical quality) against the hunter's score; colour = the rank."""
    d = frame.dropna(subset=["V1 Score"]).copy()
    active = fit.get("status") == "active" and d["Alpha %"].notna().any()
    if active:
        y, ylab = d["Alpha %"], L("Forecast 20 sessions vs SPY %", "التوقع 20 جلسة مقابل المؤشر %")
    else:
        y, ylab = d["Rank"], L("V3 rank", "ترتيب V3")
    top = set(d.nlargest(14, "Rank")["Symbol"])
    fig = go.Figure(go.Scatter(
        x=d["V1 Score"], y=y, mode="markers+text", text=[s if s in top else "" for s in d["Symbol"]], textposition="top center",
        textfont=dict(size=9, color="#CAD5D6"), cliponaxis=False,
        customdata=np.column_stack([d["Symbol"], d["Rank"].to_numpy(), d["Alpha %"].fillna(np.nan).to_numpy()]),
        marker=dict(size=11, color=d["Rank"], cmin=20, cmax=95, colorscale=[[0, _D], [0.45, _G], [0.7, _C], [1, _E]], showscale=True,
                    colorbar=dict(title=L("V3 rank", "ترتيب V3"), thickness=10), line=dict(width=0.5, color="rgba(255,255,255,.25)"), opacity=0.9),
        hovertemplate="<b>%{customdata[0]}</b><br>" + L("V1 score", "تقييم الصياد") + ": %{x:.0f}<br>" + ylab + ": %{y:.2f}<br>"
                      + L("V3 rank", "ترتيب V3") + ": %{customdata[1]:.0f}<extra></extra>"))
    if active:
        fig.add_hline(y=0, line=dict(color=_MU, dash="dot", width=0.8))
    fig.add_vline(x=65, line=dict(color=_MU, dash="dot", width=0.8))
    charts.style(fig, 440, L("Forecast map: the model's view against the hunter's score", "خريطة التوقع: رأي النموذج مقابل تقييم الصياد"), legend=False)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(title_text=L("Hunter V1 score (0-100)", "تقييم الصياد V1 (من 100)"), showgrid=True, gridcolor=charts.GRID, range=[0, 104])
    fig.update_yaxes(title_text=ylab, side="left")
    return fig


# ---------------------------------------------------------------- page
def page_hunter_v3():
    ui.html(S.CSS + (S.RTL_CSS if is_ar() else "") + CSS)
    _init()
    symbols = ss.get("v3_run")
    got = None
    if symbols:
        if len(symbols) > MAX_SCAN:
            st.error(L(f"Limit scans to {MAX_SCAN} symbols.", f"الحد الأقصى للفحص {MAX_SCAN} سهم."))
        else:
            with st.spinner(L(f"Loading {len(symbols)} stocks and validating the alpha model...",
                              f"جاري قراءة أسعار {len(symbols)} سهم وتدريب النموذج والتحقق منه...")):
                try:
                    got = _research(symbols)
                except Exception as exc:
                    st.error(L(f"Scan failed: {type(exc).__name__}: {exc}", f"تعذّر الفحص: {type(exc).__name__}: {exc}"))
    frame, fit, market, prices = got if got else (pd.DataFrame(), {}, {}, {})
    label = L(*UNIS.get(ss.get("v3_uni"), UNIS["core"]))
    ui.html(hero_html(frame, fit, market, label))
    hunt_bar()
    if not symbols:
        st.info(L("Choose your universe, then run the V3 scan. Hunter V1 remains untouched.", "اختر الأسهم ثم شغّل الصياد V3. الصياد القديم ما يتغير."),
                icon=":material/info:")
        ui.foot()
        return
    if symbols != _symbols(ss.get("v3_uni"), ss.get("v3_custom")):
        st.caption(L("The settings changed since the last run: press Run V3 to scan the new list.",
                     "الإعدادات تغيرت بعد آخر تشغيل: اضغط «شغّل V3» عشان تفحص القائمة الجديدة."))
    if got is None:
        ui.foot()
        return
    if frame.empty:
        st.warning(L("No valid completed-bar setups for this universe.", "ما فيه فرص مكتملة مؤهلة بهذه القائمة."), icon=":material/search_off:")
        ui.foot()
        return
    if fit.get("status") != "active":
        st.warning(L("The forecasting model did not beat its historical validation baseline (or data were insufficient). "
                     "V3 uses a transparent, non-predictive ranking fallback and leaves the forecast blank.",
                     "النموذج التنبؤي ما تفوق على مرجعه في التحقق التاريخي (أو البيانات ناقصة). "
                     "V3 يستخدم ترتيبًا بديلًا بدون توقعات، ويترك خانة التوقع فارغة."), icon=":material/warning:")
    mood = market.get("mood", "mixed")
    with st.container(key="hnsec_v3_board"):
        ui.safe(lambda: ui.html(board_html(fit, market)))
        st.caption(L(f"Last market data: {market.get('date', '—')} · training samples: {fit.get('n', 0)} · validation IC: {fit.get('holdout_ic', '—')} · "
                     f"horizon: {fit.get('horizon_sessions', 20)} sessions · benchmark: SPY",
                     f"آخر بيانات: {market.get('date', '—')} · عينات التدريب: {fit.get('n', 0)} · ارتباط التحقق: {fit.get('holdout_ic', '—')} · "
                     f"الأفق: {fit.get('horizon_sessions', 20)} جلسة · المؤشر: SPY"))
    with st.container(key="hnsec_v3_filters"):
        ui.safe(filters, frame, fit)
    view = apply(frame)
    profile = ss.get("v3_profile") or "risk_controlled"
    selected, allocations = V3.allocate(frame, capital=float(ss["v3_cap"]), risk_per_trade_pct=float(ss["v3_risk"]),
                                         max_positions=int(ss["v3_maxpos"]), sector_limit=int(ss["v3_seclim"]),
                                         mode=market.get("mood", "off"), profile=profile)
    if not view.empty:
        if ss.get("v3_sel") not in set(view["Symbol"]):
            ss["v3_sel"] = view["Symbol"].iloc[0]
        with st.container(key="hnsec_v3_cards"):
            ui.sec("science", f"Highest-ranked research opportunities ({len(view)})", f"أعلى فرص البحث الكمي ({len(view)})")
            ui.safe(cards, view, prices, mood)
        r = view[view["Symbol"] == ss["v3_sel"]].iloc[0]
        ui.safe(detail, r, prices, market, selected)
    else:
        with st.container(key="hnsec_v3_none"):
            st.info(L("Nothing matches these filters. Lower the rank, clear the setups, or scan a bigger universe.",
                      "ما فيه شي يطابق هالتصفية. نزّل الترتيب، أو شيل الفرص المختارة، أو افحص نطاق أكبر."), icon=":material/search_off:")
    with st.container(key="hnsec_v3_alloc"):
        ui.safe(allocation, selected, allocations, profile)
    with st.container(key="hnsec_v3_table"):
        ui.sec("table_rows", "Every result · the full research table", "كل النتائج · جدول البحث الكامل")
        ui.safe(table, frame)
    with st.container(key="hnsec_v3_charts"):
        ui.safe(lambda: ui.chart(forecast_map(frame, fit), key="hn_map_v3"))
    with st.expander(L("Research methodology and limitations", "منهجية البحث والقيود"), icon=":material/help:"):
        ui.html('<div class="hnnote">' + L(
            "V3 scans the same deterministic long setups as V1, with a different scoring layer. The pooled ridge model predicts stock return "
            "less SPY return over the next 20 sessions, using only past-labeled outcomes, a purged chronological holdout, and a validation gate. "
            "If validation fails the predictor is deactivated. <b>The rank</b>: 55% the V1 score, 20% technical quality (reward-to-risk, "
            "volatility, distance from the high, the market mood) and 25% the forecast; without a forecast, 75% and 25%. A risk flag (stale data, "
            "extreme volatility, illiquid) or no buying setup caps it at 49. The allocation is long-only, cash-based, and scaled down in adverse "
            "regimes. No future return or win probability is guaranteed. This is NOT a verified profitable strategy and must be evaluated with a "
            "point-in-time universe and realistic walk-forward backtests before relying on it.",
            "V3 يستخدم نفس شروط فرص الشراء القديمة مع طبقة ترتيب جديدة. النموذج الإحصائي يتوقع عائد السهم الزائد على المؤشر خلال 20 جلسة، "
            "ويتدرب على نتائج معلومة تاريخيًا فقط مع فصل زمني واختبار تحقق مستقل، ويُعطّل إذا ما اجتاز الاختبار. <b>الترتيب</b>: 55% تقييم الصياد، "
            "و20% الجودة الفنية (العائد مقابل المخاطرة، والتذبذب، والبعد عن القمة، ومزاج السوق)، و25% التوقع؛ وبدون توقع 75% و25%. تحذير المخاطر "
            "(بيانات قديمة، تذبذب شديد، سيولة ضعيفة) أو غياب فرصة شراء يحدّه عند 49. المحفظة افتراضية وبدون اقتراض، وتقلل الانكشاف إذا ساءت حالة "
            "السوق. ما فيه ضمان للعائد أو دقة التنبؤ، ولازم اختبارات تاريخية أقوى قبل الاعتماد.") + "</div>")
    st.caption(L("US equities · daily bars from Yahoo Finance (may be delayed) · educational/paper research only · no brokerage execution.",
                 "أسهم أمريكية · شموع يومية من ياهو فاينانس (قد تكون متأخرة) · أبحاث وتداول افتراضي فقط · بدون تنفيذ حقيقي."))
    ui.foot()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "23.4.46"
