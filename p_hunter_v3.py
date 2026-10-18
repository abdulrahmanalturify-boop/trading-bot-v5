"""
p_hunter_v3.py - Hunter V3 · Alpha Lab (menu: الصياد V3): the page of hunter_v3.py, which is untouched.

A modern lab in teal and cyan, research only (no paper allocation on this page). The rank is fully quantitative
(hunter_v3.scan: four cross-sectional factors and the validated forecast); the hunter's score, setups and levels are information.
Top to bottom:
  * a hero: the title, the totals as chips, the top pick in a spotlight and the alpha ladder (the five best ranks),
  * the hunt bar: the universe and the Run button,
  * the model's board: the market mood, validation, training samples and the holdout IC,
  * four tabs:
      - opportunities: filters (setups with their counts, rank at least, new today, no risk flags, with a forecast),
        a toolbar (search, sort, how many cards), the cards (the rank ring, the forecast meter, the four factors, the levels);
        click one to open it: the chart with entry / stop / target, its plan and why it ranked what it ranked,
      - the full table: every result with every column of the engine's output, sortable, with a CSV export,
      - the forecast map (forecast vs the quant score),
      - the methodology and limitations.
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
RISK_FLAG = {"stale_data": ("history", "Stale data", "بيانات قديمة"), "extreme_volatility": ("bolt", "Extreme volatility", "تذبذب شديد"),
             "illiquid": ("water_drop", "Illiquid", "سيولة ضعيفة"), "earnings": ("event", "Earnings soon", "أرباح قريبة"),
             "extended": ("height", "Stretched", "ممتد"), "thin": ("water_drop", "Thin trading", "سيولة ضعيفة")}
SORTS = {"rank": ("Rank", "الترتيب"), "alpha": ("Forecast", "التوقع"), "rr": ("Reward / risk", "العائد للمخاطرة"), "fresh": ("Newest", "الأحدث")}
COUNTS = (8, 12, 20)
# The S&P 500 holds 503 shares (some companies list two classes), so the cap sits above it.
MAX_SCAN = 600

# Each <style> goes to the page in its own st.markdown call: two style blocks joined on one line ("</style><style>") end
# Markdown's HTML block early and the rest of the CSS shows on the page as text.
CSS = f"""<style>
/* hero */
.v3hero {{ position:relative; overflow:hidden; border-radius:24px; margin:2px 0 16px; padding:26px 28px; isolation:isolate;
  border:1px solid rgba(45,212,191,.26); background:radial-gradient(1200px 400px at 85% -20%,rgba(45,212,191,.20),transparent 60%),
  radial-gradient(900px 380px at 0% 120%,rgba(45,182,235,.18),transparent 60%),linear-gradient(135deg,#06111A,#0A1E2B 55%,#071621);
  box-shadow:0 20px 60px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.05); }}
.v3hero::before {{ content:""; position:absolute; inset:0; z-index:-1; pointer-events:none; opacity:.55;
  background-image:linear-gradient(rgba(45,212,191,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(45,212,191,.06) 1px,transparent 1px);
  background-size:34px 34px; -webkit-mask-image:linear-gradient(180deg,#000,transparent 85%); mask-image:linear-gradient(180deg,#000,transparent 85%); }}
.v3hero::after {{ content:""; position:absolute; width:340px; height:340px; border-radius:50%; z-index:-1; pointer-events:none;
  background:radial-gradient(circle,rgba(45,212,191,.22),transparent 65%); top:-120px; inset-inline-end:-80px; animation:v3pulse 7s ease-in-out infinite; }}
@keyframes v3pulse {{ 0%,100% {{ transform:scale(1); opacity:.75; }} 50% {{ transform:scale(1.15); opacity:1; }} }}
.v3hero .wrap {{ display:grid; grid-template-columns:minmax(0,1.25fr) minmax(0,1fr); gap:26px; align-items:center; }}
.v3hero .eb {{ display:inline-flex; align-items:center; gap:7px; color:{_E}; font-weight:700; font-size:.74rem; letter-spacing:.14em;
  background:rgba(45,212,191,.10); border:1px solid rgba(45,212,191,.28); border-radius:999px; padding:5px 12px; }}
.v3hero .eb .ms {{ font-size:1rem; }}
.v3hero .t {{ font-size:2.9rem; font-weight:300; line-height:1.05; margin:14px 0 10px; color:#fff; letter-spacing:-.03em; }}
.v3hero .t b {{ font-weight:800; background:linear-gradient(90deg,{_C},{_E},#A7F3D0); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.v3hero .tg {{ color:#C4D2D4; font-size:.95rem; line-height:1.75; max-width:560px; }}
.v3hero .chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }}
.v3hero .chip {{ display:inline-flex; align-items:center; gap:7px; font-size:.8rem; color:#C4D2D4; border-radius:12px; padding:7px 11px;
  background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); }}
.v3hero .chip b {{ color:#fff; unicode-bidi:isolate; }} .v3hero .chip .ms {{ color:{_E}; font-size:1rem; }}
.v3hero .st {{ margin-top:14px; }}
/* the spotlight: the top pick and the ladder */
.v3spot {{ border-radius:20px; padding:16px; background:linear-gradient(160deg,rgba(255,255,255,.07),rgba(255,255,255,.02));
  border:1px solid rgba(45,212,191,.22); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); box-shadow:0 10px 40px rgba(0,0,0,.25); }}
.v3spot .lb {{ display:flex; align-items:center; gap:6px; color:{_E}; font-size:.72rem; font-weight:700; letter-spacing:.06em; margin-bottom:10px; }}
.v3spot .lb .ms {{ font-size:1rem; }}
.v3spot .best {{ display:flex; align-items:center; gap:12px; padding-bottom:12px; border-bottom:1px solid rgba(255,255,255,.07); }}
.v3spot .best .nm {{ flex:1; min-width:0; display:flex; flex-direction:column; line-height:1.3; }}
.v3spot .best .nm b {{ color:#fff; font-size:1.25rem; }}
.v3spot .best .nm span {{ color:{_MU}; font-size:.76rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.v3spot .best .nm em {{ font-style:normal; font-size:.74rem; color:#C4D2D4; margin-top:3px; }}
.v3spot .best .nm em i {{ font-style:normal; font-weight:700; unicode-bidi:isolate; direction:ltr; }}
.v3lad {{ display:flex; flex-direction:column; gap:8px; margin-top:12px; }}
.v3lad .row {{ display:grid; grid-template-columns:18px 54px minmax(0,1fr) 28px 56px; gap:8px; align-items:center; font-size:.78rem; }}
.v3lad .row .n {{ color:{_MU}; font-weight:700; text-align:center; }}
.v3lad .row .sy {{ color:#fff; font-weight:800; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.v3lad .row .bar {{ height:8px; border-radius:8px; background:rgba(45,212,191,.10); overflow:hidden; }}
.v3lad .row .bar i {{ display:block; height:100%; border-radius:8px; background:linear-gradient(90deg,{_C},{_E}); animation:v3grow 1s cubic-bezier(.2,.8,.2,1) both; }}
.v3lad .row b {{ font-weight:800; text-align:center; }}
.v3lad .row em {{ font-style:normal; font-weight:700; font-size:.74rem; text-align:end; direction:ltr; unicode-bidi:isolate; }}
.v3lad .row em.up {{ color:#4ADE80; }} .v3lad .row em.dn {{ color:#F87171; }} .v3lad .row em.na {{ color:{_MU}; }}
.v3lad .ft {{ color:#7FA7AC; font-size:.68rem; margin-top:2px; }}
@keyframes v3grow {{ from {{ width:0; }} }}
/* the empty state: three steps */
.v3steps {{ display:flex; flex-direction:column; gap:10px; }}
.v3steps .s {{ display:flex; gap:12px; align-items:flex-start; padding:12px 14px; border-radius:16px; background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.07); }}
.v3steps .s .k {{ flex:none; width:30px; height:30px; border-radius:10px; display:grid; place-items:center; font-weight:800; color:#06111A;
  background:linear-gradient(135deg,{_C},{_E}); }}
.v3steps .s b {{ color:#fff; font-size:.9rem; display:block; }} .v3steps .s span {{ color:{_MU}; font-size:.78rem; line-height:1.5; }}
@media (max-width: 860px) {{
  .v3hero {{ padding:20px 16px; border-radius:20px; }}
  .v3hero .wrap {{ grid-template-columns:1fr; gap:18px; }}
  .v3hero .t {{ font-size:2.1rem; margin:12px 0 8px; }}
  .v3hero .tg {{ font-size:.88rem; }}
  .v3hero .chip {{ font-size:.74rem; padding:6px 9px; }}
}}
/* the hunt bar */
[class*="st-key-hnbar_v3"] {{ border-color:rgba(45,212,191,.22) !important; border-radius:20px !important; }}
[class*="st-key-hn_go_v3"] button {{ background:linear-gradient(135deg,{_C},{_E}) !important; box-shadow:0 8px 24px rgba(45,212,191,.28) !important; }}
[class*="st-key-hn_go_v3"] button p, [class*="st-key-hn_go_v3"] button [data-testid="stIconMaterial"] {{ color:#04131B !important; font-weight:800 !important; }}
/* the model's board */
.v3reg {{ display:grid; grid-template-columns:1.6fr repeat(3,1fr); gap:10px; margin:2px 0 4px; }}
@media (max-width: 1000px) {{ .v3reg {{ grid-template-columns:1fr 1fr; }} .v3reg .mood {{ grid-column:1 / -1; }} }}
.v3reg .tl {{ background:linear-gradient(160deg,rgba(255,255,255,.05),rgba(255,255,255,.015)); border:1px solid rgba(255,255,255,.08); border-radius:18px;
  padding:14px 16px; position:relative; overflow:hidden; transition:transform .18s ease, border-color .18s ease; }}
.v3reg .tl:hover {{ transform:translateY(-2px); border-color:rgba(45,212,191,.35); }}
.v3reg .tl .l {{ color:{_MU}; font-size:.72rem; font-weight:700; display:flex; align-items:center; gap:6px; }}
.v3reg .tl .l .ms {{ font-size:1rem; color:{_E}; }}
.v3reg .tl .v {{ font-size:1.45rem; font-weight:700; color:#fff; margin-top:6px; unicode-bidi:isolate; }}
.v3reg .tl .s {{ color:{_MU}; font-size:.75rem; margin-top:3px; line-height:1.5; }}
.v3reg .tl.on {{ border-color:{_U}55; background:linear-gradient(135deg,rgba(34,197,94,.16),rgba(255,255,255,.02)); }}
.v3reg .tl.mixed {{ border-color:{_G}55; background:linear-gradient(135deg,rgba(245,185,74,.15),rgba(255,255,255,.02)); }}
.v3reg .tl.off {{ border-color:{_D}55; background:linear-gradient(135deg,rgba(239,68,68,.16),rgba(255,255,255,.02)); }}
.v3reg .tl.pass {{ border-color:{_E}55; background:linear-gradient(135deg,rgba(45,212,191,.16),rgba(255,255,255,.02)); }}
.v3reg .tl.fall {{ border-color:{_G}55; background:linear-gradient(135deg,rgba(245,185,74,.15),rgba(255,255,255,.02)); }}
.v3reg .mood .v {{ font-size:1.12rem; display:flex; align-items:center; gap:9px; }}
.v3reg .mood .dot {{ width:10px; height:10px; border-radius:50%; flex:none; animation:v3blink 2.4s ease-in-out infinite; }}
@keyframes v3blink {{ 0%,100% {{ box-shadow:0 0 0 0 rgba(255,255,255,.18); }} 50% {{ box-shadow:0 0 0 6px rgba(255,255,255,0); }} }}
.v3reg .mood .s {{ color:#C4D2D4; }}
/* the tabs */
[class*="st-key-v3tabs"] [data-baseweb="tab-list"] {{ gap:6px; padding:5px; border-radius:16px; background:rgba(255,255,255,.035);
  border:1px solid rgba(255,255,255,.07); overflow-x:auto; scrollbar-width:none; }}
[class*="st-key-v3tabs"] [data-baseweb="tab-list"]::-webkit-scrollbar {{ display:none; }}
[class*="st-key-v3tabs"] [data-baseweb="tab"] {{ border-radius:12px !important; padding:8px 14px !important; height:auto !important; white-space:nowrap; }}
[class*="st-key-v3tabs"] [data-baseweb="tab"][aria-selected="true"] {{ background:linear-gradient(135deg,rgba(45,182,235,.22),rgba(45,212,191,.22)); }}
[class*="st-key-v3tabs"] [data-baseweb="tab"][aria-selected="true"] p {{ color:#fff !important; font-weight:700 !important; }}
[class*="st-key-v3tabs"] [data-baseweb="tab-highlight"], [class*="st-key-v3tabs"] [data-baseweb="tab-border"] {{ display:none; }}
/* the cards: the hunter's frame with the lab's content */
.hnc.v3 {{ height:372px; border-radius:20px !important; background:linear-gradient(165deg,rgba(255,255,255,.06),rgba(255,255,255,.015)) !important;
  border:1px solid rgba(255,255,255,.08) !important; }}
.hnc.v3::before {{ background:linear-gradient(90deg,transparent,rgba(45,212,191,.8),transparent); }}
.hnc.v3.sel {{ border-color:{_E} !important; box-shadow:0 0 0 1px {_E}66, 0 14px 34px rgba(45,212,191,.22); }}
.hnc.v3 .no {{ position:absolute; top:10px; inset-inline-end:12px; font-size:.66rem; font-weight:800; color:{_E}; opacity:.75; }}
[class*="st-key-hncard_v3"]:hover .hnc {{ box-shadow:0 16px 38px rgba(45,212,191,.22); border-color:rgba(45,212,191,.45) !important; }}
.hnc .su .ms {{ color:{_E}; }}
.v3al {{ margin:8px 0 2px; }}
.v3al .l {{ display:flex; justify-content:space-between; align-items:center; font-size:.66rem; font-weight:700; color:{_MU}; }}
.v3al .l b {{ font-size:.82rem; direction:ltr; unicode-bidi:isolate; }}
.v3al .l b.up {{ color:#4ADE80; }} .v3al .l b.dn {{ color:#F87171; }} .v3al .l b.na {{ color:{_MU}; }}
.v3al .m {{ position:relative; height:7px; border-radius:7px; background:rgba(157,151,165,.16); margin-top:4px; overflow:hidden; direction:ltr; }}
.v3al .m::before {{ content:""; position:absolute; left:50%; top:-2px; bottom:-2px; width:1px; background:rgba(255,255,255,.35); }}
.v3al .m i {{ position:absolute; top:0; bottom:0; border-radius:7px; }}
.v3al .m i.up {{ left:50%; background:linear-gradient(90deg,{_E},#4ADE80); }} .v3al .m i.dn {{ right:50%; background:linear-gradient(270deg,{_G},#F87171); }}
.v3pt {{ display:grid; grid-template-columns:repeat(4,1fr); gap:6px; margin:6px 0 6px; }}
.v3pt div {{ min-width:0; }}
.v3pt span {{ display:block; color:{_MU}; font-size:.62rem; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.v3pt b {{ display:block; color:#fff; font-size:.8rem; font-weight:700; }}
.v3pt .bar {{ height:4px; border-radius:4px; background:rgba(157,151,165,.16); margin-top:3px; overflow:hidden; }}
.v3pt .bar i {{ display:block; height:100%; border-radius:4px; }}
.v3pt .fmo .bar i, .hnparts .r.fmo .bar i {{ background:linear-gradient(90deg,{_C},{_E}); }} .v3pt .ftr .bar i, .hnparts .r.ftr .bar i {{ background:{_A}; }}
.v3pt .flr .bar i, .hnparts .r.flr .bar i {{ background:#4ADE80; }} .v3pt .frv .bar i, .hnparts .r.frv .bar i {{ background:{_V}; }}
.hnparts .r.al .bar i {{ background:linear-gradient(90deg,{_C},{_E}); }}
.hnparts .r.q .bar i {{ background:linear-gradient(90deg,{_V},{_C}); }}
.v3fl {{ display:flex; flex-direction:column; gap:6px; margin-top:10px; }}
.v3fl .check {{ display:flex; gap:9px; align-items:center; font-size:.84rem; color:#DDD9E2; padding:6px 0; border-bottom:1px solid rgba(157,151,165,.12); }}
.v3fl .check:last-child {{ border-bottom:0; }}
.v3cnt {{ color:{_MU}; font-size:.78rem; margin:2px 0 8px; }} .v3cnt b {{ color:#fff; }}
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
    for k, v in {"v3_uni": "core", "v3_custom": "AAPL, MSFT, NVDA, AMZN", "v3_grade": "all", "v3_clean": False, "v3_alpha": False,
                 "v3_fresh": False, "v3_sort": "rank", "v3_count": 8, "v3_q": ""}.items():
        ss.setdefault(k, v)


def _go():
    ss["v3_run"] = _symbols(ss.get("v3_uni"), ss.get("v3_custom"))
    ss["v3_sel"] = None


def _alpha_txt(a):
    return f"{a:+.1f}%" if pd.notna(a) else "—"


def _alpha_cls(a):
    return "na" if pd.isna(a) else ("up" if a >= 0 else "dn")


# ---------------------------------------------------------------- hero
def _spotlight(frame):
    """The top pick (the best-ranked long) and the alpha ladder: the five best ranks as bars, each with its forecast."""
    longs = frame.sort_values(["Rank", "Quant Score"], ascending=False)
    b = longs.iloc[0]
    sym, rank = b["Symbol"], float(b["Rank"])
    setup = S.short_name(b["Setup"]) if b["Setup"] in H.SETUPS else L("No chart setup", "بدون نمط فني")
    best = (f'<div class="best">{T.logo_obj(sym, 46)}<div class="nm"><b>{T.esc(T.sym_label(sym))}</b>'
            f'<span>{T.esc(T.name_line(sym, str(b["Name"])))}</span>'
            f'<em>{T.esc(setup)} · {L("forecast", "التوقع")} <i class="{_alpha_cls(b["Alpha %"])}">{_alpha_txt(b["Alpha %"])}</i></em></div>'
            f'{S.ring(rank, H.grade(rank), 62)}</div>')
    rows = []
    for i, (_, r) in enumerate(longs.head(5).iterrows(), 1):
        rk = float(r["Rank"])
        col = S.GRADE_COLOR.get(H.grade(rk), _C)
        rows.append(f'<div class="row"><span class="n">{i}</span><span class="sy">{T.esc(T.sym_label(r["Symbol"]))}</span>'
                    f'<div class="bar"><i style="width:{rk:.0f}%;animation-delay:{i * .08:.2f}s"></i></div>'
                    f'<b style="color:{col}">{rk:.0f}</b><em class="{_alpha_cls(r["Alpha %"])}">{_alpha_txt(r["Alpha %"])}</em></div>')
    return (f'<div class="v3spot"><div class="lb">{T.icon("workspace_premium")}{L("Top pick today", "أفضل فرصة اليوم")}</div>{best}'
            f'<div class="v3lad">{"".join(rows)}<div class="ft">{L("rank out of 100 · forecast for 20 sessions over the index", "الترتيب من 100 · التوقع لـ 20 جلسة مقابل المؤشر")}</div></div></div>')


def _steps():
    steps = [(L("Choose the stocks", "اختر الأسهم"), L("The core list, the largest 100, the whole S&P 500 or your own symbols.",
                                                       "القائمة الأساسية، أو أكبر 100 شركة، أو إس آند بي 500 كامل، أو رموزك الخاصة.")),
             (L("Run the lab", "شغّل المختبر"), L("The model trains, validates itself on an unseen period, then ranks every stock.",
                                                 "النموذج يتدرب ويختبر نفسه على فترة ما شافها، ثم يرتب كل الأسهم.")),
             (L("Explore the results", "استكشف النتائج"), L("Cards, a full table, a forecast map, and every opportunity's chart and plan.",
                                                          "بطاقات وجدول كامل وخريطة توقع، ولكل فرصة رسمها وخطتها."))]
    return ('<div class="v3spot"><div class="v3steps">' + "".join(
        f'<div class="s"><div class="k">{i}</div><div><b>{T.esc(t)}</b><span>{T.esc(d)}</span></div></div>' for i, (t, d) in enumerate(steps, 1))
        + "</div></div>")


def hero_html(frame, fit, market, label):
    chips = []
    has = frame is not None and len(frame)
    if has:
        active = fit.get("status") == "active"
        chips.append(f'<span class="chip">{T.icon("radar")}{L("Scanned", "تم فحص")} <b>{market.get("universe", 0):,}</b> · {T.esc(label)}</span>')
        chips.append(f'<span class="chip">{T.icon("target")}{L("Eligible", "الفرص المؤهلة")} <b>{market.get("eligible_longs", 0)}</b></span>')
        chips.append(f'<span class="chip">{T.icon("psychology")}{L("Model", "النموذج")} <b>{L("validated", "مُعتمد") if active else L("fallback", "بديل")}</b></span>')
        chips.append(f'<span class="chip">{T.icon("bolt")}{L("New today", "جديدة اليوم")} <b>{int((frame["Status"] == "fresh").sum())}</b></span>')
        chips.append(f'<span class="chip">{T.icon("schedule")}{L("Last data", "آخر بيانات")} <b>{T.esc(str(market.get("date", "—")))}</b></span>')
    tag = L("A fully quantitative ranking engine: four statistical factors (momentum, trend, low risk, short-term reversal) ranked "
            "across the scanned stocks, plus a statistical model, validated on an unseen period, that forecasts each stock's excess return "
            "over the index for the next 20 sessions. Research only.",
            "محرك ترتيب كمي بالكامل: أربعة عوامل إحصائية (الزخم، والاتجاه، وانخفاض المخاطر، والارتداد القصير) مرتبة بين الأسهم المفحوصة، "
            "مع نموذج إحصائي مُختبر على فترة لم يرها يتوقع عائد كل سهم الزائد على المؤشر خلال 20 جلسة. للأبحاث فقط.")
    side = _spotlight(frame) if has else _steps()
    return (f'<div class="v3hero"><div class="wrap"><div class="txt">'
            f'<span class="eb">{T.icon("science")}{L("Alpha Lab · quant research", "مختبر ألفا · بحث كمي")}</span>'
            f'<div class="t">{L("Hunter <b>V3</b>", "الصياد <b>V3</b>")}</div><div class="tg">{T.esc(tag)}</div>'
            f'<div class="chips">{"".join(chips)}</div><div class="st">{T.market_status(is_ar(), "us")}</div></div>'
            f'<div class="side">{side}</div></div></div>')


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


# ---------------------------------------------------------------- the model's board
def board_html(fit, market):
    active = fit.get("status") == "active"
    ic = fit.get("holdout_ic")
    ic_s = f"{float(ic):+.3f}" if ic is not None and np.isfinite(float(ic)) else "—"
    mood = market.get("mood", "mixed")
    head = {"on": ("Risk-on", "السوق إيجابي", _U), "mixed": ("Mixed", "السوق متذبذب", _G),
            "off": ("Risk-off", "السوق سلبي", _D)}.get(mood, ("Unknown", "غير معروف", _MU))
    tip = {"on": ("Most stocks are above their averages: a friendly backdrop for buying setups.", "أغلب الأسهم فوق متوسطاتها: بيئة مناسبة لفرص الشراء."),
           "mixed": ("A selective market: favour the strongest setups only.", "سوق انتقائي: الأفضل التركيز على أقوى الفرص فقط."),
           "off": ("A weak market: caution first, and smaller risk.", "سوق ضعيف: الحذر أولًا وتقليل المخاطرة.")}.get(mood, ("", ""))
    tiles = [
        f'<div class="tl mood {mood}"><div class="l">{T.icon("explore")}{L("Market mood", "مزاج السوق")}</div>'
        f'<div class="v"><span class="dot" style="background:{head[2]}"></span>{T.esc(L(head[0], head[1]))}</div><div class="s">{T.esc(L(*tip))}</div></div>',
        f'<div class="tl {"pass" if active else "fall"}"><div class="l">{T.icon("verified" if active else "warning")}{L("Model validation", "حالة النموذج")}</div>'
        f'<div class="v">{L("Validated", "مُعتمد") if active else L("Fallback", "ترتيب بديل")}</div>'
        f'<div class="s">{L("the forecast is on: it beat its baseline on the holdout", "التوقع شغّال: تفوق على مرجعه في فترة التحقق") if active else L("the forecast is off: a transparent rank without predictions", "التوقع متوقف: ترتيب شفاف بدون توقعات")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("dataset")}{L("Training samples", "عينات التدريب")}</div><div class="v">{int(fit.get("n", 0) or 0):,}</div>'
        f'<div class="s">{L("labeled outcomes, 20 sessions ahead", "نتائج معلومة، 20 جلسة للأمام")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("insights")}{L("Validation IC", "ارتباط التحقق")}</div><div class="v">{ic_s}</div>'
        f'<div class="s">{L("forecast vs realized, out of sample", "التوقع مقابل الفعلي خارج العينة")}</div></div>']
    return '<div class="v3reg">' + "".join(tiles) + "</div>"


# ---------------------------------------------------------------- filters and the toolbar
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
        t = st.columns([1.4, 1.6, 1], vertical_alignment="bottom")
        t[0].text_input(L("Search", "بحث"), key="v3_q", placeholder=L("Symbol or company", "الرمز أو اسم الشركة"), icon=":material/search:")
        t[1].segmented_control(L("Sort by", "رتّب حسب"), list(SORTS), key="v3_sort", format_func=lambda k: L(*SORTS[k]))
        t[2].segmented_control(L("Cards", "عدد البطاقات"), list(COUNTS), key="v3_count")


def apply(frame):
    v = frame[frame["Rank"] >= 50].copy()
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
    q = str(ss.get("v3_q") or "").strip().upper()
    if q:
        v = v[v["Symbol"].astype(str).str.upper().str.contains(q, regex=False) | v["Name"].astype(str).str.upper().str.contains(q, regex=False)]
    how = ss.get("v3_sort") or "rank"
    if how == "alpha":
        return v.sort_values(["Alpha %", "Rank"], ascending=False, na_position="last")
    if how == "rr":
        return v.sort_values(["R:R", "Rank"], ascending=False, na_position="last")
    if how == "fresh":
        return v.assign(_f=(v["Status"] == "fresh")).sort_values(["_f", "Age", "Rank"], ascending=[False, True, False]).drop(columns="_f")
    return v.sort_values(["Rank", "Quant Score"], ascending=False)


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


FACTOR_NAMES = {"Q Momentum": ("fmo", "Momentum", "الزخم", "Momentum", "الزخم"), "Q Trend": ("ftr", "Trend", "الاتجاه", "Trend", "الاتجاه"),
                "Q Low Risk": ("flr", "Low risk", "انخفاض المخاطر", "Low risk", "الأمان"),
                "Q Reversal": ("frv", "Reversal", "الارتداد القصير", "Reversal", "الارتداد")}


def _factors(r, short=False):
    """The four quant factors: (class, label, weight %, value 0-100), as hunter_v3.quant_scores blends them."""
    tot = sum(w for *_, w in V3.FACTORS)
    return [(FACTOR_NAMES[n][0], L(*(FACTOR_NAMES[n][3:5] if short else FACTOR_NAMES[n][1:3])), round(100 * w / tot), float(r[n]))
            for n, _, w in V3.FACTORS]


def _parts(r):
    """The rank's parts: (class, label, weight %, value 0-100), as hunter_v3.scan blends them."""
    if pd.notna(r.get("Forecast Pctl")):
        fw = round(100 * V3.FORECAST_WEIGHT)
        return [("al", L("Forecast percentile", "ترتيب التوقع"), fw, float(r["Forecast Pctl"])),
                ("q", L("Quant score", "التقييم الكمي"), 100 - fw, float(r["Quant Score"]))]
    return [("q", L("Quant score", "التقييم الكمي"), 100, float(r["Quant Score"]))]


def alpha_meter(alpha):
    """The forecast as a meter round zero: -15% at the left edge, +15% at the right."""
    lab = L("Forecast · 20 sessions over the index", "التوقع · 20 جلسة مقابل المؤشر")
    if pd.isna(alpha):
        return f'<div class="v3al"><div class="l"><span>{lab}</span><b class="na">—</b></div><div class="m"></div></div>'
    w = min(50.0, abs(float(alpha)) / 15 * 50)
    return (f'<div class="v3al"><div class="l"><span>{lab}</span><b class="{_alpha_cls(alpha)}">{alpha:+.2f}%</b></div>'
            f'<div class="m"><i class="{_alpha_cls(alpha)}" style="width:{w:.1f}%"></i></div></div>')


def card(r, prices, mood, selected, no=None):
    sym, k = r["Symbol"], r["Setup"]
    ic = H.SETUPS[k][2] if k in H.SETUPS else "radar"
    entry, stop, tgt = r["Entry"], r["Stop"], r["Target"]
    rank = float(r["Rank"])
    top = (f'<div class="top"><span class="su">{T.icon(ic)}<span class="tx">{T.esc(S.short_name(k) if k in H.SETUPS else L("No chart setup", "بدون نمط فني"))}</span></span>'
           f'{S.status_tag(r["Status"] if r["Status"] in H.STATUS else None, r["Age"])}</div>')
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
    pt = '<div class="v3pt">' + "".join(f'<div class="{c_}"><span>{T.esc(l_)}</span><b>{v:.0f}</b><div class="bar"><i style="width:{v:.0f}%"></i></div></div>'
                                        for c_, l_, w, v in _factors(r, short=True)) + "</div>"
    watch = r["Status"] == "watch"
    lv = (f'<div class="lv"><div><span>{L("Buy above", "شراء فوق") if watch else L("Entry", "الدخول")}</span><b>{S._money_px(entry)}</b></div>'
          f'<div><span>{L("Stop", "الوقف")}</span><b>{S._money_px(stop)}</b><i class="dn">{S._pct(entry, stop):+.1f}%</i></div>'
          f'<div><span>{L("Target", "الهدف")}</span><b>{S._money_px(tgt)}</b><i class="up">{S._pct(entry, tgt):+.1f}%</i></div></div>') if np.isfinite(entry) else ""
    chips = [f'<span class="c">RS <b>{int(r["RS"])}</b></span>'] if pd.notna(r.get("RS")) else []
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
    top = view.head(int(ss.get("v3_count") or COUNTS[0]))
    sel = ss.get("v3_sel")
    rows = list(top.iterrows())
    shown = L(f"Showing <b>{len(rows)}</b> of <b>{len(view)}</b> · tap a card to open it",
              f"معروض <b>{len(rows)}</b> من <b>{len(view)}</b> · اضغط على أي بطاقة لفتح تفاصيلها")
    ui.html(f'<div class="v3cnt">{shown}</div>')
    for i in range(0, len(rows), 4):
        cols = st.columns(4)
        for col, (_, r) in zip(cols, rows[i:i + 4]):
            with col:
                with st.container(key=f"hncard_v3_{S._key(r['Symbol'])}"):
                    ui.html(card(r, prices, mood, r["Symbol"] == sel))
                    st.button(r["Symbol"], key=f"hn_pick_v3_{S._key(r['Symbol'])}", on_click=_pick, args=(r["Symbol"],), width="stretch")


# ---------------------------------------------------------------- the opened opportunity
def detail(r, prices, market):
    sym, k = r["Symbol"], r["Setup"]
    rank, v1, alpha, qs = float(r["Rank"]), float(r["V1 Score"]), r["Alpha %"], float(r["Quant Score"])
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
            k4[1].metric(L("Quant score", "التقييم الكمي"), f"{qs:.1f}/100")
            k4[2].metric(L("Forecast 20d excess", "العائد الزائد المتوقع 20 جلسة"), f"{alpha:+.2f}%" if pd.notna(alpha) else "—")
            k4[3].metric(L("Reward / Risk", "العائد / المخاطرة"), f"{r['R:R']:.2f}" if pd.notna(r["R:R"]) else "—")
            if np.isfinite(r["Entry"]) and int(r["Side"] or 0) > 0:
                entry, stop, tgt = float(r["Entry"]), float(r["Stop"]), float(r["Target"])
                watch = r["Status"] == "watch"
                tiles = [("en", L("Buy above", "شراء فوق") if watch else L("Entry", "الدخول"), S._money_px(entry),
                          L("on a close above it", "بإغلاق فوقه") if watch else L("next open, near this price", "الافتتاح القادم، قرب هذا السعر")),
                         ("sl", L("Stop loss", "وقف الخسارة"), S._money_px(stop), f"{S._pct(entry, stop):+.1f}%"),
                         ("tp", L("Target", "الهدف"), S._money_px(tgt), f"{S._pct(entry, tgt):+.1f}%"),
                         ("", L("ATR (14)", "متوسط المدى (14)"), f"{r['ATR %']:.1f}%", L("a day", "يومياً")),
                         ("", L("Traded a day", "التداول اليومي"), T.money(r["$Vol"], short=True), L("dollar volume", "قيمة التداول")),
                         ("", L("Exposure", "الانكشاف"), f"{float(r.get('Exposure', 1)) * 100:.0f}%", L("the regime's scale", "حسب حالة السوق"))]
                ui.html('<div class="hnplan" style="margin-top:8px">' + "".join(f'<div class="p {c_}"><div class="l">{T.esc(l_)}</div><div class="v">{v_}</div>'
                                                                                 f'<div class="s">{T.esc(s_)}</div></div>' for c_, l_, v_, s_ in tiles) + "</div>")
        with right:
            ui.sec("donut_large", "Why this rank", "ليش هالترتيب")
            bars = lambda parts: '<div class="hnparts">' + "".join(
                f'<div class="r {c_}"><span>{T.esc(l_)} <span class="w">· {w}%</span></span>'
                f'<div class="bar"><i style="width:{float(v):.0f}%"></i></div><b>{float(v):.0f}</b></div>' for c_, l_, w, v in parts) + "</div>"
            ui.html(bars(_parts(r)))
            ui.html(f'<div class="v3cnt" style="margin:12px 0 4px">{L("Inside the quant score (percentile among the scanned stocks)", "مكونات التقييم الكمي (ترتيبه المئوي بين الأسهم المفحوصة)")}</div>')
            ui.html(bars(_factors(r)))
            if any(f in str(r["Risk Flag"] or "") for f in ("stale_data", "extreme_volatility", "illiquid")):
                st.caption(L("A data risk flag (stale data, extreme volatility, illiquid) caps the rank at 49.",
                             "تحذير بيانات (بيانات قديمة، تذبذب شديد، سيولة ضعيفة) يحدّ الترتيب عند 49."))
            ui.html(alpha_meter(alpha))
            flags = _flags(r)
            items = [(ic, t) for ic, t in flags] or [("verified", L("No risk flags on this stock.", "ما فيه تحذيرات مخاطر على هالسهم."))]
            setups = [S.short_name(x) for x in str(r.get("Setups") or "").split(",") if x]
            if len(setups) > 1:
                items.append(("layers", L("Other setups too: ", "فرص ثانية بنفس السهم: ") + " · ".join(setups[1:])))
            ui.html(f'<div class="hnbox" style="margin-top:12px"><div class="hnbt">{T.icon("fact_check")}<span>{L("Checks", "الفحوصات")}</span></div>'
                    f'<div class="v3fl">' + "".join(f'<div class="check">{T.ico(ic, "acc")}<div>{T.esc(t)}</div></div>' for ic, t in items) + "</div></div>")


# ---------------------------------------------------------------- the table and the map
def table(frame):
    """Every result with every column of the engine's frame, sortable, in the lab's order: the V3 columns first, then the
    hunter's measurements (for information). Hidden here: the rank's internal parts and the breadth flags (Trend, Accum, SetupPts, RiskPts,
    Above50, Above200, NewHigh, NewLow, Side, Model Active)."""
    cols = ["Symbol", "Name", "Sector", "Rank", "Quant Score", "Forecast Pctl", "Alpha %", "Q Momentum", "Q Trend", "Q Low Risk", "Q Reversal", "V1 Score", "Setup", "Status", "Age", "Setups", "Price", "Chg %", "Entry", "Stop", "Target",
            "R:R", "ATR %", "$Vol", "Risk Flag", "Exposure", "RS", "RVOL", "RSI", "ADX", "1M %", "3M %", "6M %", "From high %", "Earnings", "Flags"]
    show = frame[[c for c in cols if c in frame.columns]].copy()
    show["Sector"] = show["Sector"].map(lambda s: sector_name(s) if s else "—")
    show["Setup"] = show["Setup"].map(S.setup_name)
    show["Setups"] = show["Setups"].map(lambda s: " · ".join(S.short_name(k) for k in str(s or "").split(",") if k) or "—")
    show["Status"] = show["Status"].map(lambda s: L(*H.STATUS[s][:2]) if s in H.STATUS else "—")
    show["Risk Flag"] = show["Risk Flag"].map(lambda s: " · ".join(L(*RISK_FLAG[f][1:]) if f in RISK_FLAG else f for f in str(s or "").split(",") if f) or "—")
    if "Flags" in show:
        show["Flags"] = show["Flags"].map(lambda s: " · ".join(L(*RISK_FLAG[f][1:]) if f in RISK_FLAG else f for f in str(s or "").split(",") if f) or "—")
    show["Exposure"] = show["Exposure"].astype(float) * 100
    N = {"Symbol": L("Symbol", "الرمز"), "Name": L("Company", "الشركة"), "Sector": L("Sector", "القطاع"), "Rank": L("V3 rank", "ترتيب V3"),
         "Quant Score": L("Quant score", "التقييم الكمي"), "Forecast Pctl": L("Forecast percentile", "ترتيب التوقع"),
         "Q Momentum": L("Momentum", "الزخم"), "Q Trend": L("Trend", "الاتجاه"), "Q Low Risk": L("Low risk", "انخفاض المخاطر"),
         "Q Reversal": L("Reversal", "الارتداد القصير"), "V1 Score": L("Hunter score (info)", "تقييم الصياد (للاطلاع)"), "Alpha %": L("Forecast %", "التوقع %"), "Setup": L("Setup", "الفرصة"), "Status": L("Status", "الحالة"),
         "Age": L("Age (days)", "العمر (أيام)"), "Setups": L("All setups", "كل الفرص"), "Price": L("Price", "السعر"), "Chg %": L("Chg %", "التغير %"),
         "Entry": L("Entry", "الدخول"), "Stop": L("Stop", "الوقف"), "Target": L("Target", "الهدف"), "R:R": "R:R", "ATR %": L("ATR %", "التذبذب %"),
         "$Vol": L("Traded/day ($)", "التداول اليومي ($)"), "Risk Flag": L("Risk flags", "تحذيرات المخاطر"), "Exposure": L("Exposure %", "الانكشاف %"),
         "RS": "RS", "RVOL": "RVOL", "RSI": "RSI", "ADX": "ADX", "1M %": L("1M %", "شهر %"), "3M %": L("3M %", "3 أشهر %"), "6M %": L("6M %", "6 أشهر %"),
         "From high %": L("From 52W high %", "عن القمة السنوية %"), "Earnings": L("Earnings in (days)", "الأرباح بعد (أيام)"), "Flags": L("Hunter flags", "تنبيهات الصياد")}
    show = show.rename(columns=N)
    pct = lambda name, f="%+.1f%%": st.column_config.NumberColumn(name, format=f)
    cfg = {N["Rank"]: st.column_config.ProgressColumn(N["Rank"], min_value=0, max_value=100, format="%.1f"),
           N["V1 Score"]: st.column_config.ProgressColumn(N["V1 Score"], min_value=0, max_value=100, format="%.1f"),
           **{N[c]: st.column_config.ProgressColumn(N[c], min_value=0, max_value=100, format="%.0f")
              for c in ("Quant Score", "Forecast Pctl", "Q Momentum", "Q Trend", "Q Low Risk", "Q Reversal")},
           N["Alpha %"]: pct(N["Alpha %"], "%+.2f%%"), N["Chg %"]: pct(N["Chg %"], "%+.2f%%"), N["1M %"]: pct(N["1M %"]), N["3M %"]: pct(N["3M %"]),
           N["6M %"]: pct(N["6M %"]), N["From high %"]: pct(N["From high %"]), N["ATR %"]: pct(N["ATR %"], "%.1f%%"), N["Exposure"]: pct(N["Exposure"], "%.0f%%"),
           N["Price"]: pct(N["Price"], "%.2f"), N["Entry"]: pct(N["Entry"], "%.2f"), N["Stop"]: pct(N["Stop"], "%.2f"), N["Target"]: pct(N["Target"], "%.2f"),
           "R:R": pct("R:R", "%.2f"), N["$Vol"]: pct(N["$Vol"], "$%,.0f"), "RVOL": pct("RVOL", "%.2f×"), "RSI": pct("RSI", "%.0f"), "ADX": pct("ADX", "%.0f"),
           N["Earnings"]: pct(N["Earnings"], "%.0f"), N["Age"]: pct(N["Age"], "%.0f"),
           N["Symbol"]: st.column_config.TextColumn(N["Symbol"], pinned=True)}
    st.dataframe(show, hide_index=True, width="stretch", height=520, column_config={k: v for k, v in cfg.items() if k in show.columns})
    st.caption(L(f"{len(show)} stocks · click a column header to sort · every column of the engine's output.",
                 f"{len(show)} سهم · اضغط على عنوان العمود للترتيب · كل أعمدة مخرجات المحرك."))
    st.download_button(L("Export V3 research CSV", "تصدير نتائج V3"), data=frame.to_csv(index=False).encode("utf-8-sig"),
                       file_name="tura-hunter-v3-research.csv", mime="text/csv", icon=":material/download:", key="v3_csv")


def forecast_map(frame, fit):
    """The lab's map: the forecast (or, without a model, the rank) against the quant score; colour = the rank."""
    d = frame.dropna(subset=["Quant Score"]).copy()
    active = fit.get("status") == "active" and d["Alpha %"].notna().any()
    if active:
        y, ylab = d["Alpha %"], L("Forecast 20 sessions over the index %", "التوقع 20 جلسة مقابل المؤشر %")
    else:
        y, ylab = d["Rank"], L("V3 rank", "ترتيب V3")
    top = set(d.nlargest(14, "Rank")["Symbol"])
    fig = go.Figure(go.Scatter(
        x=d["Quant Score"], y=y, mode="markers+text", text=[s if s in top else "" for s in d["Symbol"]], textposition="top center",
        textfont=dict(size=9, color="#CAD5D6"), cliponaxis=False,
        customdata=np.column_stack([d["Symbol"], d["Rank"].to_numpy(), d["Alpha %"].fillna(np.nan).to_numpy()]),
        marker=dict(size=11, color=d["Rank"], cmin=20, cmax=95, colorscale=[[0, _D], [0.45, _G], [0.7, _C], [1, _E]], showscale=True,
                    colorbar=dict(title=L("V3 rank", "ترتيب V3"), thickness=10), line=dict(width=0.5, color="rgba(255,255,255,.25)"), opacity=0.9),
        hovertemplate="<b>%{customdata[0]}</b><br>" + L("Quant score", "التقييم الكمي") + ": %{x:.0f}<br>" + ylab + ": %{y:.2f}<br>"
                      + L("V3 rank", "ترتيب V3") + ": %{customdata[1]:.0f}<extra></extra>"))
    if active:
        fig.add_hline(y=0, line=dict(color=_MU, dash="dot", width=0.8))
    fig.add_vline(x=50, line=dict(color=_MU, dash="dot", width=0.8))
    charts.style(fig, 460, L("Forecast map: the model's view against the quant score", "خريطة التوقع: رأي النموذج مقابل التقييم الكمي"), legend=False)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(title_text=L("Quant score (0-100)", "التقييم الكمي (من 100)"), showgrid=True, gridcolor=charts.GRID, range=[0, 104])
    fig.update_yaxes(title_text=ylab, side="left")
    return fig


def methodology():
    ui.html('<div class="hnnote">' + L(
        "<b>The rank is fully quantitative.</b> Four factors are measured for every scanned stock from its daily prices and the index: "
        "<b>momentum</b> (its excess return over the index across 1 and 3 months, 35%), <b>trend</b> (its distance from the 100-day average "
        "and the 20/50-day average spread, 25%), <b>low risk</b> (lower 20-day volatility and a smaller 3-month drawdown, 25%) and "
        "<b>short-term reversal</b> (a weak last week, 15%). Each is a percentile among the scanned stocks (50 = the middle), and their "
        "weighted blend is the quant score. A pooled ridge model forecasts each stock's return over the index for the next 20 sessions, "
        "trained only on outcomes already known, with a purged chronological holdout; if it does not beat its baseline there it is switched "
        "off. With the model on, the rank is half the forecast's percentile and half the quant score; with it off, the quant score alone. "
        "A data risk flag (stale data, extreme volatility, illiquid) caps it at 49. The factor weights are fixed, not fitted, and this "
        "ranking has not been shown to beat the hunter out of sample. Measured on today's S&P 500 members from 2013 (training "
        "2013-2019, testing 2020 on), none of these factors, nor value or financial quality from SEC filings, ranked stocks reliably "
        "over the next 20, 60 or 120 sessions; treat the rank as a research view, not a forecast. The hunter's score, setups and levels stay on the page for information "
        "only. No future return or win probability is guaranteed.",
        "<b>الترتيب كمي بالكامل.</b> لكل سهم مفحوص تُقاس أربعة عوامل من أسعاره اليومية ومن المؤشر: <b>الزخم</b> (عائده الزائد على المؤشر "
        "خلال شهر و3 أشهر، 35%)، و<b>الاتجاه</b> (بعده عن متوسط 100 يوم والفرق بين متوسطي 20 و50 يوم، 25%)، و<b>انخفاض المخاطر</b> "
        "(تذبذب أقل خلال 20 يوم وتراجع أصغر خلال 3 أشهر، 25%)، و<b>الارتداد القصير</b> (أسبوع أخير ضعيف، 15%). كل عامل يُحوَّل إلى ترتيب "
        "مئوي بين الأسهم المفحوصة (50 = المنتصف)، ومجموعها الموزون هو التقييم الكمي. ونموذج إحصائي يتوقع عائد السهم الزائد على المؤشر "
        "خلال 20 جلسة، ويتدرب على نتائج معلومة فقط مع فصل زمني واختبار تحقق مستقل، ويُعطّل إذا ما تفوق على مرجعه. إذا كان النموذج شغّالًا "
        "فالترتيب نصفه ترتيب التوقع ونصفه التقييم الكمي، وإذا تعطّل فالتقييم الكمي وحده. تحذير البيانات (بيانات قديمة، تذبذب شديد، سيولة "
        "ضعيفة) يحدّه عند 49. أوزان العوامل ثابتة وليست مُدرّبة، ولم يثبت بعد أن هذا الترتيب يتفوق على الصياد الأول في اختبار خارج العينة. "
        "وفي اختبار على أسهم إس آند بي 500 الحالية من 2013 (التدريب حتى 2019، والاختبار من 2020)، ما رتّب أي عامل من هذه "
        "العوامل، ولا القيمة ولا الجودة المالية من تقارير الشركات، الأسهم بشكل يعتمد عليه خلال 20 أو 60 أو 120 جلسة؛ فتعامل مع "
        "الترتيب كرأي بحثي وليس توقعًا. "
        "تقييم الصياد وفرصه ومستوياته باقية في الصفحة للاطلاع فقط. ما فيه ضمان للعائد أو دقة التنبؤ.") + "</div>")
    st.caption(L("Stop prices may gap through. Prices may be delayed. No auto orders, derivatives or leverage.",
                 "قد ينفذ وقف الخسارة بسعر أسوأ عند وجود فجوة. الأسعار قد تتأخر، ولا يوجد تداول فعلي أو مشتقات أو رافعة."))


# ---------------------------------------------------------------- page
def page_hunter_v3():
    ui.html(S.CSS)
    if is_ar():
        ui.html(S.RTL_CSS)
    ui.html(CSS)
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
        st.info(L("Choose your universe, then run the V3 scan. Hunter V1 remains untouched.", "اختر الأسهم ثم شغّل الصياد V3. الصياد الأول ما يتغير."),
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
                     "الصياد V3 يستخدم ترتيبًا بديلًا بدون توقعات، ويترك خانة التوقع فارغة."), icon=":material/warning:")
    mood = market.get("mood", "mixed")
    with st.container(key="hnsec_v3_board"):
        ui.safe(lambda: ui.html(board_html(fit, market)))
        st.caption(L(f"Last market data: {market.get('date', '—')} · training samples: {fit.get('n', 0)} · validation IC: {fit.get('holdout_ic', '—')} · "
                     f"horizon: {fit.get('horizon_sessions', 20)} sessions · benchmark: SPY",
                     f"آخر بيانات: {market.get('date', '—')} · عينات التدريب: {fit.get('n', 0)} · ارتباط التحقق: {fit.get('holdout_ic', '—')} · "
                     f"الأفق: {fit.get('horizon_sessions', 20)} جلسة · المؤشر: إس آند بي 500"))
    view_all = frame[frame["Rank"] >= 50]
    with st.container(key="v3tabs"):
        t_op, t_tb, t_map, t_how = st.tabs([f":material/target: {L('Opportunities', 'الفرص')} ({len(view_all)})",
                                            f":material/table_rows: {L('Full table', 'الجدول الكامل')} ({len(frame)})",
                                            f":material/scatter_plot: {L('Forecast map', 'خريطة التوقع')}",
                                            f":material/help: {L('Methodology', 'المنهجية')}"])
    with t_op:
        with st.container(key="hnsec_v3_filters"):
            ui.safe(filters, frame, fit)
        view = apply(frame)
        if not view.empty:
            if ss.get("v3_sel") not in set(view["Symbol"]):
                ss["v3_sel"] = view["Symbol"].iloc[0]
            with st.container(key="hnsec_v3_cards"):
                ui.sec("science", "Highest-ranked research opportunities", "أعلى فرص البحث الكمي")
                ui.safe(cards, view, prices, mood)
            r = view[view["Symbol"] == ss["v3_sel"]].iloc[0]
            ui.safe(detail, r, prices, market)
        else:
            with st.container(key="hnsec_v3_none"):
                st.info(L("Nothing matches these filters. Lower the rank, clear the setups or the search, or scan a bigger universe.",
                          "ما فيه شي يطابق هالتصفية. نزّل الترتيب، أو امسح الفرص المختارة أو البحث، أو افحص نطاق أكبر."), icon=":material/search_off:")
    with t_tb:
        with st.container(key="hnsec_v3_table"):
            ui.safe(table, frame)
    with t_map:
        with st.container(key="hnsec_v3_charts"):
            ui.safe(lambda: ui.chart(forecast_map(frame, fit), key="hn_map_v3"))
    with t_how:
        methodology()
    st.caption(L("US equities · daily bars from Yahoo Finance (may be delayed) · educational research only · no brokerage execution.",
                 "أسهم أمريكية · شموع يومية من ياهو فاينانس (قد تكون متأخرة) · أبحاث تعليمية فقط · بدون تنفيذ حقيقي."))
    ui.foot()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "23.4.51"
