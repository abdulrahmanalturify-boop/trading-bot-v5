"""
p_scanner.py - the Opportunity Hunter (menu: Scanner / صائد الفرص).

Top to bottom:
  * a hero in the site's colours: a radar whose blips are the best opportunities, with the totals as chips,
  * the hunt bar: what to scan (S&P 500, the 175 largest, a sector, a theme, the watchlist or your own symbols), the
    account size and the risk per trade (for the position sizes), and the Hunt button,
  * the market's mood: SPY's trend, the share of stocks above their 50 / 200-day averages, new highs vs lows, the VIX,
  * filters (setup types with their counts, grade, sector, new today only, no earnings in 5 days, price, liquidity),
  * the best opportunities as cards (click one to open it), then the opened one in detail: chart with entry / stop /
    target, why it scored what it scored, the trade plan with the position size, and how the same setup did on the same
    stock over the last five years, with links to the stock page, Catalyst Pro and the Paper Bots tester,
  * every result in one table, the sectors by strength and the opportunity map.
The rules and the score are in hunter.py.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import streamlit as st

import caldata
import charts
import data
import hunter as H
import mcal
import paperbots as PB
import playbooks as PBK
import ta
import taxonomy as X
import theme as T
import ui
import universe as U
from i18n import L, is_ar, sector_name

ss = st.session_state
_A, _V, _C, _G, _D, _U, _MU, _BD, _BG = T.ACCENT, T.VIOLET, T.CYAN, T.GOLD, T.DOWN, T.UP, "#8A94A7", T.BORDER, T.CARD2
GRADE_COLOR = {"A+": "#22C55E", "A": "#4ADE80", "B": _C, "C": _G, "D": _D}
FLAG = {"earnings": ("event", "Earnings in {d} days", "أرباح بعد {d} أيام", "gold"), "extended": ("height", "Stretched", "ممتد", "org"),
        "thin": ("water_drop", "Thin trading", "سيولة ضعيفة", "neu")}
MIN_GRADE = {"A+": 85, "A": 75, "B": 65, "C": 50, "all": 0}
N_CARDS = 8

CSS = f"""<style>
/* ---------- hero: a radar in the brand's colours ---------- */
.hnhero {{ position:relative; overflow:hidden; border-radius:22px; border:1px solid {_BD}; margin:2px 0 16px; min-height:250px;
  background:linear-gradient(120deg,#060c1c,#0c1d3f,#1c1543,#071a33); background-size:300% 300%; animation:sky 20s ease-in-out infinite; }}
.hnhero .grid {{ position:absolute; inset:0; pointer-events:none;
  background-image:linear-gradient(rgba(34,211,238,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(34,211,238,.07) 1px,transparent 1px);
  background-size:36px 36px; -webkit-mask-image:radial-gradient(ellipse at 78% 50%,#000 0%,transparent 66%);
  mask-image:radial-gradient(ellipse at 78% 50%,#000 0%,transparent 66%); }}
.hnhero .art {{ position:absolute; top:0; bottom:0; right:0; width:52%; pointer-events:none; }}
.hnhero .art svg {{ width:100%; height:100%; display:block; }}
.hnhero.rtl .art {{ right:auto; left:0; }}
.hnhero .txt {{ position:relative; z-index:2; padding:26px 30px 24px; max-width:640px;
  background:linear-gradient(90deg,rgba(10,14,23,.8) 0%,rgba(10,14,23,.35) 72%,rgba(10,14,23,0) 100%); }}
.hnhero.rtl .txt {{ margin-left:auto; background:linear-gradient(270deg,rgba(10,14,23,.8) 0%,rgba(10,14,23,.35) 72%,rgba(10,14,23,0) 100%); }}
.hnhero .eb {{ color:{_C}; font-weight:800; letter-spacing:.2em; font-size:.72rem; text-transform:uppercase; display:flex; align-items:center; gap:8px; }}
.hnhero .t {{ font-size:2.4rem; font-weight:800; line-height:1.08; margin:8px 0 6px; color:#fff; letter-spacing:-.02em; }}
.hnhero .t b {{ background:linear-gradient(90deg,{_A},{_V},{_C}); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.hnhero .tg {{ color:#C7CFDD; font-size:.94rem; line-height:1.6; max-width:540px; }}
.hnhero .chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
.hnhero .chip {{ background:rgba(17,23,35,.8); border:1px solid {_BD}; backdrop-filter:blur(6px); border-radius:10px; padding:6px 10px;
  font-size:.8rem; display:inline-flex; align-items:center; gap:7px; color:#C9D0DC; }}
.hnhero .chip b {{ color:#fff; unicode-bidi:isolate; direction:ltr; }} .hnhero .chip .ms {{ color:{_C}; font-size:1rem; }}
.hnhero .st {{ margin-top:12px; }}
.hnhero .sweep {{ transform-origin:360px 125px; animation:hnspin 5.5s linear infinite; }}
.hnhero .blip {{ transform-box:fill-box; transform-origin:center; animation:hnping 2.4s ease-out infinite; }}
@keyframes hnspin {{ to {{ transform:rotate(360deg); }} }}
@keyframes hnping {{ 0% {{ transform:scale(1); opacity:.9; }} 100% {{ transform:scale(2.6); opacity:0; }} }}
@media (max-width: 820px) {{ .hnhero .art {{ width:100%; opacity:.25; }} .hnhero .t {{ font-size:1.9rem; }} .hnhero .txt {{ background:none; }} }}

/* ---------- the hunt bar ---------- */
[class*="st-key-hnbar"] {{ position:relative; overflow:hidden; background:linear-gradient(180deg,{_BG},{T.CARD}); border:1px solid {_BD};
  border-radius:18px; padding:14px 18px 16px; box-shadow:0 10px 26px rgba(0,0,0,.18); }}
[class*="st-key-hnbar"]::before {{ content:""; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,{_A},{_V},{_C}); }}
[class*="st-key-hn_go"] button {{ min-height:44px !important; border:0 !important; border-radius:12px !important;
  background:linear-gradient(95deg,{_A} 0%,{_V} 62%,{_C} 130%) !important; box-shadow:0 10px 26px rgba(61,123,255,.35); }}
[class*="st-key-hn_go"] button:hover {{ filter:brightness(1.08); transform:translateY(-1px); }}
[class*="st-key-hn_go"] button p, [class*="st-key-hn_go"] button [data-testid="stIconMaterial"] {{ color:#fff !important; font-weight:800 !important; }}

/* ---------- market mood ---------- */
.hnreg {{ display:grid; grid-template-columns:1.5fr repeat(4,1fr); gap:10px; margin:2px 0 4px; }}
@media (max-width: 1000px) {{ .hnreg {{ grid-template-columns:1fr 1fr; }} }}
.hnreg .tl {{ background:linear-gradient(180deg,{_BG},{T.CARD}); border:1px solid {_BD}; border-radius:16px; padding:12px 14px; position:relative; overflow:hidden; }}
.hnreg .tl .l {{ color:{_MU}; font-size:.68rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; display:flex; align-items:center; gap:6px; }}
.hnreg .tl .l .ms {{ font-size:.95rem; color:{_C}; }}
.hnreg .tl .v {{ font-size:1.35rem; font-weight:800; color:#fff; margin-top:4px; direction:ltr; unicode-bidi:isolate; }}
.hnreg .tl .s {{ color:{_MU}; font-size:.74rem; margin-top:2px; }}
.hnreg .bar {{ height:6px; border-radius:6px; background:rgba(138,148,167,.18); margin-top:8px; overflow:hidden; direction:ltr; }}
.hnreg .bar i {{ display:block; height:100%; border-radius:6px; }}
.hnreg .mood {{ border-width:1.5px; }}
.hnreg .mood .v {{ font-size:1.08rem; display:flex; align-items:center; gap:8px; direction:inherit; }}
.hnreg .mood .dot {{ width:10px; height:10px; border-radius:50%; box-shadow:0 0 0 4px rgba(255,255,255,.06); flex:none; }}
.hnreg .mood .s {{ color:#C7CFDD; line-height:1.45; }}
.hnreg .mood.on {{ border-color:{_U}66; background:linear-gradient(135deg,rgba(34,197,94,.14),{T.CARD}); }}
.hnreg .mood.mixed {{ border-color:{_G}66; background:linear-gradient(135deg,rgba(245,185,74,.13),{T.CARD}); }}
.hnreg .mood.off {{ border-color:{_D}66; background:linear-gradient(135deg,rgba(239,68,68,.14),{T.CARD}); }}

/* ---------- opportunity cards ---------- */
.hnc {{ margin:0 !important; height:308px; box-sizing:border-box; display:flex; flex-direction:column; overflow:hidden; position:relative;
  transition:box-shadow .18s ease, border-color .18s ease; }}
.hnc::before {{ content:""; position:absolute; left:0; right:0; top:0; height:3px; background:linear-gradient(90deg,{_A},{_V},{_C}); opacity:.35; }}
.hnc.sel {{ border-color:{_A} !important; box-shadow:0 0 0 1px {_A}66, 0 12px 30px {_A}26; }}
.hnc.sel::before {{ opacity:1; }}
.hnc .top {{ display:flex; justify-content:space-between; align-items:center; gap:6px; margin:-2px 0 10px; }}
.hnc .su {{ display:inline-flex; align-items:center; gap:5px; font-size:.68rem; font-weight:800; color:#C9D0DC; min-width:0; }}
.hnc .su .ms {{ font-size:1rem; color:{_C}; flex:none; }}
.hnc .su .tx {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.hntag {{ display:inline-flex; align-items:center; gap:4px; font-size:.6rem; font-weight:800; letter-spacing:.05em; border-radius:6px; padding:2px 6px;
  white-space:nowrap; flex:none; }}
.hntag.fresh {{ background:{T.POS_BG}; color:{T.POS_FG}; }}
.hntag.fresh::before {{ content:""; width:6px; height:6px; border-radius:50%; background:currentColor; animation:pbtw 1.6s ease-in-out infinite; }}
.hntag.active {{ background:{T.ACC_BG}; color:{T.ACC_FG}; }}
.hntag.watch {{ background:{T.YEL_BG}; color:{T.YEL_FG}; }}
.hnc .hd {{ display:flex; align-items:center; gap:10px; }}
.hnc .hd .nm {{ display:flex; flex-direction:column; min-width:0; line-height:1.25; flex:1; }}
.hnc .hd .nm b {{ color:#fff; font-size:1.02rem; }}
.hnc .hd .nm span {{ color:{_MU}; font-size:.72rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.hnring {{ position:relative; width:48px; height:48px; flex:none; }}
.hnring svg {{ width:48px; height:48px; transform:rotate(-90deg); }}
.hnring .g {{ position:absolute; inset:0; direction:ltr; display:flex; flex-direction:column; align-items:center; justify-content:center; line-height:1; }}
.hnring .g b {{ font-size:.92rem; font-weight:800; color:#fff; }}
.hnring .g span {{ font-size:.58rem; color:{_MU}; margin-top:2px; }}
.hnc .spk {{ margin:10px -2px 6px; height:58px; }}
.hnc .spk svg {{ width:100%; height:58px; display:block; overflow:visible; }}
.hnc .lv {{ display:grid; grid-template-columns:repeat(3,1fr); gap:6px; margin-top:auto; direction:ltr; }}
.hnc .lv div {{ background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.05); border-radius:10px; padding:5px 7px; min-width:0; }}
.hnc .lv span {{ display:block; color:{_MU}; font-size:.6rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; }}
.hnc .lv b {{ display:block; color:#fff; font-size:.8rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.hnc .lv i {{ display:block; font-style:normal; font-size:.66rem; font-weight:700; line-height:1.2; }}
.hnc .mt {{ display:grid; grid-template-columns:repeat(3,1fr); gap:6px; margin:2px 0 8px; direction:ltr; }}
.hnc .mt div {{ min-width:0; }}
.hnc .mt span {{ display:block; color:{_MU}; font-size:.6rem; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.hnc .mt b {{ font-size:.8rem; font-weight:800; }}
.hnc .lv .dn {{ color:#F87171; }} .hnc .lv .up {{ color:#4ADE80; }}
.hnc .ft {{ display:flex; flex-wrap:nowrap; gap:5px; margin-top:8px; overflow:hidden; }}
.hnc .ft .c {{ display:inline-flex; align-items:center; gap:4px; font-size:.66rem; font-weight:700; color:#AEB7C6; background:rgba(138,148,167,.10);
  border:1px solid {_BD}; border-radius:999px; padding:2px 8px; white-space:nowrap; }}
.hnc .ft .c b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }}
.hnc .ft .c.w {{ color:{T.YEL_FG}; background:{T.YEL_BG}; border-color:transparent; }}
.hnc .ft .c .ms {{ font-size:.85rem; }}
[class*="st-key-hncard_"] {{ position:relative; transition:transform .18s ease; }}
[class*="st-key-hncard_"]:hover {{ transform:translateY(-4px); z-index:3; }}
[class*="st-key-hncard_"]:hover .hnc {{ box-shadow:0 14px 34px rgba(61,123,255,.22); }}
[class*="st-key-hncard_"]:hover .hnc::before {{ opacity:1; }}
[class*="st-key-hncard_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-hncard_"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
[class*="st-key-hncard_"] [class*="st-key-hn_pick_"] {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; width:auto !important; }}
[class*="st-key-hncard_"] [class*="st-key-hn_pick_"] .stButton, [class*="st-key-hncard_"] [class*="st-key-hn_pick_"] button
  {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}

/* ---------- the opened opportunity ---------- */
.hndh {{ position:relative; overflow:hidden; margin:0 !important; display:flex; align-items:center; gap:14px; flex-wrap:wrap; }}
.hndh::before {{ content:""; position:absolute; top:0; bottom:0; left:0; width:3px; background:linear-gradient(180deg,{_A},{_V},{_C}); }}
.hndh .nm {{ display:flex; flex-direction:column; line-height:1.25; }}
.hndh .nm b {{ font-size:1.3rem; color:#fff; }} .hndh .nm span {{ color:{_MU}; font-size:.8rem; }}
.hndh .bd {{ display:flex; flex-wrap:wrap; gap:4px; flex:1; min-width:240px; }}
.hndh .px {{ text-align:end; margin-inline-start:auto; }}
.hndh .px b {{ display:block; font-size:1.3rem; color:#fff; direction:ltr; }}
.hndh .hnring, .hndh .hnring svg {{ width:62px; height:62px; }}
.hndh .hnring .g b {{ font-size:1.2rem; }}
.hnparts {{ display:flex; flex-direction:column; gap:9px; }}
.hnparts .r {{ display:grid; grid-template-columns:130px 1fr 44px; gap:10px; align-items:center; font-size:.8rem; color:#C9D0DC; }}
.hnparts .r .w {{ color:{_MU}; font-size:.68rem; }}
.hnparts .r b {{ color:#fff; text-align:end; direction:ltr; }}
.hnparts .bar {{ height:8px; border-radius:8px; background:rgba(138,148,167,.16); overflow:hidden; direction:ltr; }}
.hnparts .bar i {{ display:block; height:100%; border-radius:8px; background:linear-gradient(90deg,{_A},{_V},{_C}); }}
.hnwhy {{ margin-top:12px; display:flex; flex-direction:column; gap:6px; }}
.hnwhy .w {{ display:flex; gap:8px; align-items:flex-start; font-size:.8rem; color:#DCE2EC; line-height:1.45; }}
.hnwhy .w .ms {{ font-size:1rem; flex:none; margin-top:1px; }}
.hnwhy .w.ok .ms {{ color:#4ADE80; }} .hnwhy .w.no .ms {{ color:#F87171; }} .hnwhy .w.in .ms {{ color:{_G}; }}
.hnplan {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; }}
.hnplan .p {{ background:linear-gradient(180deg,{_BG},{T.CARD}); border:1px solid {_BD}; border-radius:14px; padding:10px 12px; }}
.hnplan .p .l {{ color:{_MU}; font-size:.66rem; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }}
.hnplan .p .v {{ color:#fff; font-size:1.05rem; font-weight:800; margin-top:3px; direction:ltr; unicode-bidi:isolate; }}
.hnplan .p .s {{ color:{_MU}; font-size:.72rem; margin-top:1px; }}
.hnplan .p.en {{ border-color:{_A}66; }} .hnplan .p.sl {{ border-color:{_D}55; }} .hnplan .p.tp {{ border-color:{_U}55; }}
.hnplan .p.sl .v {{ color:#F87171; }} .hnplan .p.tp .v {{ color:#4ADE80; }}
.hnnote {{ color:#C7CFDD; font-size:.84rem; line-height:1.6; background:rgba(61,123,255,.07); border:1px solid {_A}33; border-radius:12px; padding:10px 12px; }}
.hnnote b {{ color:#fff; }}
[class*="st-key-hnsec_"] {{ margin-top:18px; }}
[class*="st-key-hnsec_"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
[class*="st-key-hnsec_"] .sec {{ margin:0 !important; }}
[class*="st-key-hnact"] button {{ border-radius:12px !important; min-height:42px !important; }}
</style>"""
RTL_CSS = """<style>
.hnhero .eb, .hnreg .tl .l, .hnc .lv span, .hnplan .p .l { letter-spacing:0; }
.hndh::before { left:auto; right:0; }
.hnparts .r { grid-template-columns:120px 1fr 44px; }
</style>"""


# ---------------------------------------------------------------- what to scan
def universes():
    """key -> (label, symbols)."""
    from sp500 import SP500
    u = {"top": (L(f"Top {len(U.US_UNIVERSE)} US stocks", f"أكبر {len(U.US_UNIVERSE)} سهم أمريكي"), list(U.US_UNIVERSE)),
         "sp500": (L("S&P 500 (all, slower)", "إس آند بي 500 (كامل، أبطأ)"), sorted(set(SP500) | set(U.STOCKS)))}
    for sec, syms in PB.sector_members().items():
        u[f"s:{sec}"] = (f"{L('Sector', 'قطاع')} · {sector_name(sec)}", syms)
    for tk, (en, ar_, _, _) in X.THEMES.items():
        u[f"t:{tk}"] = (f"{L('Theme', 'ثيم')} · {L(en, ar_)}", X.theme_tickers(tk))
    u["wl"] = (L("My watchlist", "قائمة المتابعة"), list(ss.get("watchlist", [])))
    u["custom"] = (L("My own symbols", "رموز أكتبها"), None)
    return u


def _symbols(unis):
    k = ss.get("hn_uni", "top")
    if k not in unis:
        k = "top"
    if unis[k][1] is None:
        raw = str(ss.get("hn_custom") or "").replace("،", ",").replace(" ", ",")
        return k, tuple(dict.fromkeys(s.strip().upper() for s in raw.split(",") if s.strip()))[:200]
    return k, tuple(unis[k][1])


def _names_sectors(symbols):
    from sp500 import SP500
    names, secs = {}, {}
    for s in symbols:
        names[s] = U.STOCKS[s][0] if s in U.STOCKS else (SP500[s][0] if s in SP500 else U.name_of(s))
        secs[s] = PB.sector_of(s) or U.sector_of(s)
    return names, secs


def _today_ny():
    return datetime.now(ZoneInfo("America/New_York")).date()


def _session_live():
    now = datetime.now(ZoneInfo("America/New_York"))
    kind, _ = mcal.day_status(now.date())
    close = 780 if kind == "early" else 960
    return now.weekday() < 5 and kind != "closed" and 570 <= now.hour * 60 + now.minute < close


def _earnings_map(today):
    try:
        e = caldata.earnings(today, today + timedelta(days=14), 0, 10)
        return {r.Symbol: r.Date for r in e.itertuples()} if len(e) else {}
    except Exception:
        return {}


@st.cache_data(ttl=900, show_spinner=False, max_entries=16)
def run_hunt(key, symbols, nonce=0, build=None):
    """Download the prices of the universe (two years of daily candles) and hunt. Cached 15 minutes per universe."""
    px = PB.load_prices(list(symbols), "2y")
    spy = data.history("SPY", "2y")
    vix = data.history("^VIX", "6mo")
    today = _today_ny()
    earn = _earnings_map(today)
    names, secs = _names_sectors(symbols)
    res, det = H.hunt(px, spy if not spy.empty else None, earn, today, names, secs)
    last = max((pd.Timestamp(df.index[-1]) for df in px.values() if df is not None and len(df)), default=None)
    return {"res": res, "det": det, "reg": H.regime(res, spy, vix), "sec": H.sectors(res), "n": len(res), "asked": len(symbols),
            "time": datetime.now(ZoneInfo("America/New_York")).strftime("%H:%M"), "last": last, "earn": len(earn) > 0}


# ---------------------------------------------------------------- small pieces
SHORT = {"leader": ("Leader near highs", "قائد قرب القمة"), "breakout": ("20-day breakout", "اختراق 20 يوم"),
         "dip": ("Dip in an uptrend", "تشبع في اتجاه صاعد"), "breakdown": ("Breakdown", "كسر هابط"), "golden": ("Golden cross", "التقاطع الذهبي")}


def short_name(k):
    return L(*SHORT[k]) if k in SHORT else setup_name(k)


def setup_name(k):
    s = H.SETUPS.get(k)
    return L(s[0], s[1]) if s else "—"


def status_tag(st_, age=None):
    if not st_:
        return ""
    en, ar_, _ = H.STATUS[st_]
    if st_ == "active" and age:
        en, ar_ = f"{en} · {int(age)}d", f"{ar_} · {int(age)} ي"
    return f'<span class="hntag {st_}">{T.esc(L(en, ar_))}</span>'


def ring(score, g, size=48):
    r = 20
    circ = 2 * np.pi * r
    col = GRADE_COLOR.get(g, _C)
    return (f'<div class="hnring" style="width:{size}px;height:{size}px"><svg viewBox="0 0 48 48">'
            f'<circle cx="24" cy="24" r="{r}" fill="none" stroke="rgba(138,148,167,.18)" stroke-width="4.5"/>'
            f'<circle cx="24" cy="24" r="{r}" fill="none" stroke="{col}" stroke-width="4.5" stroke-linecap="round" '
            f'stroke-dasharray="{circ * score / 100:.1f} {circ:.1f}"/></svg>'
            f'<div class="g"><b style="color:{col}">{g}</b><span>{score:.0f}</span></div></div>')


def spark(values, entry=None, stop=None, target=None, uid="x"):
    """The last three months of closes, with the entry (blue), stop (red) and target (green) as dotted lines."""
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    if len(v) < 2:
        return ""
    lv = [x for x in (entry, stop, target) if x is not None and np.isfinite(x)]
    lo, hi = min(v.min(), *lv) if lv else v.min(), max(v.max(), *lv) if lv else v.max()
    rng = (hi - lo) or 1.0
    w, h = 200.0, 58.0
    y = lambda p: h - 4 - (p - lo) / rng * (h - 8)
    xs = np.linspace(0, w, len(v))
    pts = " ".join(f"{a:.1f},{y(b):.1f}" for a, b in zip(xs, v))
    col = _U if v[-1] >= v[0] else _D
    lines = ""
    for p, c_ in ((target, _U), (entry, _A), (stop, _D)):
        if p is not None and np.isfinite(p):
            lines += (f'<line x1="0" y1="{y(p):.1f}" x2="{w:.0f}" y2="{y(p):.1f}" stroke="{c_}" stroke-width="1.2" stroke-dasharray="3 3" '
                      f'vector-effect="non-scaling-stroke" opacity=".85"/>')
    return (f'<svg viewBox="0 0 {w:.0f} {h:.0f}" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="hnsp{uid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{col}" stop-opacity=".30"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
            f'<polygon points="0,{h:.0f} {pts} {w:.0f},{h:.0f}" fill="url(#hnsp{uid})"/>{lines}'
            f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>')


def _pct(a, b):
    return (b / a - 1) * 100 if a else 0.0


def _money_px(x):
    return "$" + T.fmt_price(x)


def flags_of(r):
    out = []
    for f in [x for x in str(r.get("Flags") or "").split(",") if x]:
        ic, en, ar_, kind = FLAG[f]
        d = int(r["Earnings"]) if f == "earnings" and pd.notna(r.get("Earnings")) else 0
        out.append((ic, L(en.format(d=d), ar_.format(d=d)), kind))
    return out


# ---------------------------------------------------------------- hero
def _radar(res):
    cx, cy = 360, 125
    s = ['<svg viewBox="0 0 520 250" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" style="direction:ltr">'
         '<defs><radialGradient id="hnrg" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#22D3EE" stop-opacity=".16"/>'
         '<stop offset="1" stop-color="#22D3EE" stop-opacity="0"/></radialGradient>'
         '<linearGradient id="hnsw" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22D3EE" stop-opacity="0"/>'
         '<stop offset="1" stop-color="#22D3EE" stop-opacity=".42"/></linearGradient>'
         '<filter id="hngl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/>'
         '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
         f'<circle cx="{cx}" cy="{cy}" r="112" fill="url(#hnrg)"/>']
    for r in (28, 56, 84, 112):
        s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#22D3EE" stroke-opacity="{.10 + r / 1200:.2f}" stroke-width="1"/>')
    s.append(f'<path d="M{cx - 118} {cy} H{cx + 118} M{cx} {cy - 118} V{cy + 118}" stroke="#22D3EE" stroke-opacity=".12" stroke-width="1"/>')
    s.append(f'<g class="sweep"><path d="M{cx} {cy} L{cx + 112} {cy} A112 112 0 0 0 {cx + 112 * np.cos(np.radians(-38)):.1f} '
             f'{cy + 112 * np.sin(np.radians(-38)):.1f} Z" fill="url(#hnsw)"/>'
             f'<line x1="{cx}" y1="{cy}" x2="{cx + 112}" y2="{cy}" stroke="#22D3EE" stroke-width="2" stroke-opacity=".8" filter="url(#hngl)"/></g>')
    top = res.head(7) if res is not None and len(res) else pd.DataFrame()
    for i, r in enumerate(top.itertuples()):
        ang = np.radians(-160 + i * 53)
        rad = 32 + i * 12
        x, y = cx + rad * np.cos(ang), cy + rad * np.sin(ang)
        col = GRADE_COLOR.get(r.Grade, _C)
        s.append(f'<circle class="blip" cx="{x:.0f}" cy="{y:.0f}" r="5" fill="none" stroke="{col}" stroke-width="1.5" style="animation-delay:-{i * .35:.2f}s"/>'
                 f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4" fill="{col}" filter="url(#hngl)"/>'
                 f'<text x="{x + 8:.0f}" y="{y - 6:.0f}" font-size="11" font-weight="800" fill="#fff" font-family="{T.FONT}">{T.esc(r.Symbol)}</text>'
                 f'<text x="{x + 8:.0f}" y="{y + 7:.0f}" font-size="9.5" fill="{col}" font-family="{T.FONT}">{r.Grade} · {r.Score:.0f}</text>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="#22D3EE" filter="url(#hngl)"/>')
    return "".join(s) + "</svg>"


def hero_html(got, label):
    res = got["res"] if got else None
    chips = []
    if got and res is not None and len(res):
        opp = res[res["Score"] >= 65]
        chips.append(f'<span class="chip">{T.icon("radar")}{L("Scanned", "تم فحص")} <b>{got["n"]:,}</b> · {T.esc(label)}</span>')
        chips.append(f'<span class="chip">{T.icon("target")}{L("Opportunities", "فرص")} <b>{len(opp)}</b></span>')
        chips.append(f'<span class="chip">{T.icon("workspace_premium")}{L("Grade A or better", "درجة A فأعلى")} <b>{int((res["Score"] >= 75).sum())}</b></span>')
        chips.append(f'<span class="chip">{T.icon("bolt")}{L("New today", "جديدة اليوم")} <b>{int((res["Status"] == "fresh").sum())}</b></span>')
        chips.append(f'<span class="chip">{T.icon("schedule")}{L("Updated", "آخر تحديث")} <b>{got["time"]} ET</b></span>')
    tag = L("Every stock checked against exact setups, scored from 0 to 100 on trend, relative strength, accumulation and "
            "reward-to-risk, with a full trade plan and how the same setup did on the same stock before.",
            "كل سهم يُفحص على فرص بشروط دقيقة، ويأخذ تقييم من 100 على الاتجاه والقوة النسبية والتجميع والعائد مقابل المخاطرة، "
            "مع خطة تداول كاملة وكيف كانت نفس الفرصة على نفس السهم قبل.")
    return (f'<div class="hnhero{" rtl" if is_ar() else ""}"><div class="grid"></div><div class="art">{_radar(res)}</div>'
            f'<div class="txt"><div class="eb">{T.icon("radar")}{L("Opportunity scanner", "ماسح الفرص")}</div>'
            f'<div class="t">{L("Opportunity <b>Hunter</b>", "صائد <b>الفرص</b>")}</div><div class="tg">{T.esc(tag)}</div>'
            f'<div class="chips">{"".join(chips)}</div><div class="st">{T.market_status(is_ar())}</div></div></div>')


# ---------------------------------------------------------------- the hunt bar
def _go():
    ss["hn_ran"] = True
    ss["hn_nonce"] = ss.get("hn_nonce", 0)


def _refresh():
    ss["hn_ran"] = True
    ss["hn_nonce"] = ss.get("hn_nonce", 0) + 1


def hunt_bar(unis):
    with st.container(key="hnbar"):
        c = st.columns([2.2, 1.1, 1, 1.1, 0.8], vertical_alignment="bottom")
        c[0].selectbox(L("What to scan", "وش أفحص"), list(unis), key="hn_uni", format_func=lambda k: f"{unis[k][0]}"
                       + (f"  ({len(unis[k][1])})" if unis[k][1] is not None else ""))
        c[1].number_input(L("Account ($)", "المحفظة ($)"), 100, 100_000_000, step=1000, key="hn_acct")
        c[2].number_input(L("Risk per trade %", "المخاطرة لكل صفقة %"), 0.1, 10.0, step=0.25, key="hn_risk")
        c[3].button(L("Hunt", "ابدأ الصيد"), icon=":material/radar:", key="hn_go", on_click=_go, width="stretch")
        c[4].button(L("Refresh", "تحديث"), icon=":material/refresh:", key="hn_refresh", on_click=_refresh, help=L("Fresh prices now", "أسعار جديدة الحين"),
                    width="stretch")
        if ss.get("hn_uni") == "custom":
            st.text_input(L("Symbols (comma separated)", "الرموز (مفصولة بفاصلة)"), key="hn_custom",
                          placeholder="AAPL, MSFT, NVDA, 2222.SR")
        if ss.get("hn_uni") == "sp500":
            st.caption(L("The whole S&P 500 takes up to a minute the first time; then it is kept for 15 minutes.",
                         "إس آند بي 500 كامل ياخذ لين دقيقة أول مرة، وبعدها ينحفظ 15 دقيقة."))


# ---------------------------------------------------------------- market mood
def mood_html(reg):
    mood = reg.get("mood", "mixed")
    head = {"on": ("Risk-on: favour longs", "السوق إيجابي: الأفضلية للشراء", _U),
            "mixed": ("Mixed: be selective", "السوق متذبذب: كن انتقائي", _G),
            "off": ("Risk-off: defend", "السوق سلبي: دافع عن رأس مالك", _D)}[mood]
    tip = {"on": ("Most stocks are above their averages. Breakouts and pullbacks work best now; normal position sizes.",
                  "أغلب الأسهم فوق متوسطاتها. الاختراقات والارتدادات تشتغل أفضل الحين، وبأحجام صفقات عادية."),
           "mixed": ("Take only A-grade setups, use smaller sizes, and take profits sooner.",
                     "خذ فرص الدرجة A بس، وصغّر حجم الصفقات، واجنِ الأرباح أسرع."),
           "off": ("Most breakouts fail in weak markets. Trade less, keep stops tight, or wait for the trend to return.",
                   "أغلب الاختراقات تفشل في السوق الضعيف. قلّل التداول، وخلّ الوقف قريب، أو انتظر رجوع الاتجاه.")}[mood]

    def meter(pct, col):
        pct = 0 if not np.isfinite(pct) else pct
        return f'<div class="bar"><i style="width:{pct:.0f}%;background:{col}"></i></div>'

    p50, p200 = reg.get("pct50", np.nan), reg.get("pct200", np.nan)
    col = lambda p: _U if p >= 55 else (_G if p >= 35 else _D)
    tr = {"up": ("Uptrend", "صاعد", _U), "down": ("Downtrend", "هابط", _D), "mixed": ("Sideways", "متذبذب", _G), None: ("—", "—", _MU)}[reg.get("spy_trend")]
    vix = reg.get("vix", np.nan)
    vix_s = (L("calm", "هادئ") if vix < 16 else L("normal", "طبيعي") if vix < 22 else L("nervous", "متوتر") if vix < 30 else L("fear", "خوف")) if np.isfinite(vix) else ""
    tiles = [
        f'<div class="tl mood {mood}"><div class="l">{T.icon("explore")}{L("Market mood", "مزاج السوق")}</div>'
        f'<div class="v"><span class="dot" style="background:{head[2]}"></span>{T.esc(L(head[0], head[1]))}</div><div class="s">{T.esc(L(*tip))}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("show_chart")}S&amp;P 500</div><div class="v" style="color:{tr[2]}">{T.esc(L(tr[0], tr[1]))}</div>'
        f'<div class="s">{L("vs 50-day", "مقابل 50 يوم")} {reg.get("spy_vs50", 0):+.1f}% · {L("200-day", "200 يوم")} {reg.get("spy_vs200", 0):+.1f}%</div></div>',
        f'<div class="tl"><div class="l">{T.icon("stacked_bar_chart")}{L("Above 50-day", "فوق متوسط 50")}</div>'
        f'<div class="v">{p50:.0f}%</div>{meter(p50, col(p50))}<div class="s">{L("of the scanned stocks", "من الأسهم المفحوصة")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("landscape")}{L("Above 200-day", "فوق متوسط 200")}</div>'
        f'<div class="v">{p200:.0f}%</div>{meter(p200, col(p200))}<div class="s">{L("the long-term trend", "الاتجاه طويل المدى")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("speed")}{L("Highs / lows · VIX", "قمم / قيعان · VIX")}</div>'
        f'<div class="v"><span style="color:#4ADE80">{reg.get("highs", 0)}</span> / <span style="color:#F87171">{reg.get("lows", 0)}</span></div>'
        f'<div class="s">{L("new 52-week highs / lows", "قمم / قيعان سنوية جديدة")}{f" · VIX {vix:.1f} ({vix_s})" if np.isfinite(vix) else ""}</div></div>']
    if not np.isfinite(p50):
        tiles = tiles[:2]
    return '<div class="hnreg">' + "".join(tiles) + "</div>"


# ---------------------------------------------------------------- filters
def _init():
    for k, v in {"hn_uni": "top", "hn_acct": 100_000, "hn_risk": 1.0, "hn_grade": "B", "hn_sector": "all", "hn_fresh": False,
                 "hn_noearn": False, "hn_minpx": 5.0, "hn_minvol": 20.0, "hn_custom": "AAPL, MSFT, NVDA, AMD, TSLA, META"}.items():
        ss.setdefault(k, v)


def filters(res):
    counts = res["Setups"].str.split(",").explode().value_counts()
    keys = [k for k in H.ORDER if counts.get(k, 0)]
    fmt = lambda k: f"{setup_name(k)} · {int(counts.get(k, 0))}"
    if "hn_setups" in ss:
        ss["hn_setups"] = [k for k in ss["hn_setups"] if k in keys]
    st.pills(L("Setups (tap to filter; none = all long setups)", "الفرص (اضغط للتصفية؛ بدون اختيار = كل فرص الشراء)"), keys,
             selection_mode="multi", format_func=fmt, key="hn_setups")
    c = st.columns([1.6, 1.4, 1, 1], vertical_alignment="bottom")
    c[0].segmented_control(L("Grade at least", "الدرجة على الأقل"), list(MIN_GRADE), key="hn_grade",
                           format_func=lambda g: L("All", "الكل") if g == "all" else g)
    secs = sorted(x for x in res["Sector"].dropna().unique() if x)
    if ss.get("hn_sector") not in ["all"] + secs:
        ss["hn_sector"] = "all"
    c[1].selectbox(L("Sector", "القطاع"), ["all"] + secs, key="hn_sector", format_func=lambda s: L("All sectors", "كل القطاعات") if s == "all" else sector_name(s))
    c[2].toggle(L("New today only", "الجديدة اليوم فقط"), key="hn_fresh")
    c[3].toggle(L("No earnings in 5 days", "بدون أرباح خلال 5 أيام"), key="hn_noearn")
    with st.expander(L("Price and liquidity", "السعر والسيولة"), icon=":material/tune:"):
        a, b = st.columns(2)
        a.number_input(L("Price at least ($)", "السعر على الأقل ($)"), 0.0, 10000.0, step=1.0, key="hn_minpx")
        b.number_input(L("Traded per day at least ($ million)", "قيمة التداول اليومية على الأقل (مليون $)"), 0.0, 10000.0, step=5.0, key="hn_minvol")


def apply(res):
    v = res.copy()
    picks = ss.get("hn_setups") or []
    if picks:
        v = v[v["Setups"].apply(lambda s: any(k in str(s).split(",") for k in picks))]
    else:
        v = v[v["Side"] > 0]
    v = v[v["Score"] >= MIN_GRADE.get(ss.get("hn_grade") or "all", 0)] if not (picks and "breakdown" in picks) else v
    if ss.get("hn_sector", "all") != "all":
        v = v[v["Sector"] == ss["hn_sector"]]
    if ss.get("hn_fresh"):
        v = v[v["Status"] == "fresh"]
    if ss.get("hn_noearn"):
        v = v[~v["Flags"].str.contains("earnings", na=False)]
    v = v[(v["Price"] >= float(ss.get("hn_minpx") or 0)) & (v["$Vol"] >= float(ss.get("hn_minvol") or 0) * 1e6)]
    return v


# ---------------------------------------------------------------- cards
def card(r, det, selected):
    sym = r["Symbol"]
    k = r["Setup"]
    ic = H.SETUPS[k][2] if k in H.SETUPS else "radar"
    entry, stop, tgt = r["Entry"], r["Stop"], r["Target"]
    side = r["Side"] or 1
    top = (f'<div class="top"><span class="su">{T.icon(ic)}<span class="tx">{T.esc(short_name(k))}</span></span>'
           f'{status_tag(r["Status"], r["Age"])}</div>')
    hd = (f'<div class="hd">{T.logo_obj(sym, 36)}<div class="nm"><b>{T.esc(sym)}</b><span>{T.esc(str(r["Name"]))}</span></div>'
          f'{ring(r["Score"], r["Grade"])}</div>')
    sp = f'<div class="spk">{spark(det.get("spark", []), entry, stop, tgt, sym.replace(".", "_").replace("-", "_"))}</div>'
    watch = r["Status"] == "watch"
    lv = (f'<div class="lv"><div><span>{L("Buy above", "شراء فوق") if watch else L("Entry", "الدخول")}</span><b>{_money_px(entry)}</b></div>'
          f'<div><span>{L("Stop", "الوقف")}</span><b>{_money_px(stop)}</b><i class="dn">{_pct(entry, stop):+.1f}%</i></div>'
          f'<div><span>{L("Target", "الهدف")}</span><b>{_money_px(tgt)}</b><i class="up">{_pct(entry, tgt):+.1f}%</i></div></div>') if np.isfinite(entry) else ""
    col = lambda x: "#4ADE80" if x >= 0 else "#F87171"
    m3, fh = r["3M %"], r["From high %"]
    mt = (f'<div class="mt"><div><span>{L("3 months", "3 أشهر")}</span><b style="color:{col(m3 if np.isfinite(m3) else 0)}">'
          f'{m3:+.1f}%</b></div><div><span>{L("From 52W high", "عن القمة")}</span><b>{fh:.1f}%</b></div>'
          f'<div><span>{L("Volatility", "التذبذب")}</span><b>{r["ATR %"]:.1f}%</b></div></div>') if np.isfinite(fh) else ""
    chips = [f'<span class="c">RS <b>{int(r["RS"])}</b></span>']
    if np.isfinite(r["R:R"]):
        chips.append(f'<span class="c">R:R <b>{r["R:R"]:.1f}</b></span>')
    if pd.notna(r["RVOL"]):
        chips.append(f'<span class="c">RVOL <b>{r["RVOL"]:.1f}×</b></span>')
    for ic_, txt, kind in flags_of(r):
        chips.insert(0, f'<span class="c w">{T.icon(ic_)}{T.esc(txt)}</span>')
    ft = f'<div class="ft">{"".join(chips)}</div>'
    return f'<div class="card hnc{" sel" if selected else ""}">{top}{hd}{sp}{mt}{lv}{ft}</div>'


def _pick(sym):
    ss["hn_sel"] = sym


def cards(view, det):
    top = view.head(N_CARDS)
    if top.empty:
        return
    sel = ss.get("hn_sel")
    per_row = 4
    rows = list(top.iterrows())
    for i in range(0, len(rows), per_row):
        cols = st.columns(per_row)
        for col, (_, r) in zip(cols, rows[i:i + per_row]):
            with col:
                with st.container(key=f"hncard_{_key(r['Symbol'])}"):
                    ui.html(card(r, det.get(r["Symbol"], {}), r["Symbol"] == sel))
                    st.button(r["Symbol"], key=f"hn_pick_{_key(r['Symbol'])}", on_click=_pick, args=(r["Symbol"],), width="stretch")


def _key(sym):
    return "".join(ch if ch.isalnum() else "_" for ch in str(sym))


# ---------------------------------------------------------------- the opened opportunity
@st.cache_data(ttl=1800, show_spinner=False, max_entries=48)
def _history5(sym, build=None):
    df = data.history(sym, "5y")
    spy = data.history("SPY", "5y")
    d = H._clean(df)
    if d is None:
        return None, None
    return ta.add_all(d), (spy if not spy.empty else None)


@st.cache_data(ttl=1800, show_spinner=False, max_entries=96)
def _edge(sym, key, build=None):
    d, spy = _history5(sym, build)
    if d is None or key not in H.SETUPS or H.SETUPS[key][3] == "watch":
        return None, pd.DataFrame()
    bt = H.backtest(d, key, market=spy)
    return H.edge(bt), bt


def _why(r, det):
    """The reasons behind the score: (kind ok / no / info, text)."""
    out = []
    ok = lambda c, en, ar_: out.append(("ok" if c else "no", L(en, ar_)))
    p = r["Price"]
    s50, s200 = det.get("sma50", np.nan), det.get("sma200", np.nan)
    ok(np.isfinite(s200) and p > s200, f"Above its 200-day average (${s200:,.2f})" if np.isfinite(s200) else "No 200-day average yet",
       f"فوق متوسط 200 يوم (${s200:,.2f})" if np.isfinite(s200) else "ما فيه متوسط 200 يوم للحين")
    ok(p > s50, f"Above its 50-day average (${s50:,.2f})", f"فوق متوسط 50 يوم (${s50:,.2f})")
    rs = int(r["RS"])
    ok(rs >= 70, f"Relative strength {rs}: stronger than {rs}% of the scanned stocks over 3-12 months",
       f"القوة النسبية {rs}: أقوى من {rs}% من الأسهم المفحوصة خلال 3 إلى 12 شهر")
    ud = det.get("ud", 1.0)
    ok(ud >= 1.1, f"Volume on up days is {ud:.2f}x the volume on down days (50 days): {'buyers in control' if ud >= 1.1 else 'no accumulation'}",
       f"حجم أيام الصعود {ud:.2f} ضعف حجم أيام النزول (50 يوم): {'المشترين مسيطرين' if ud >= 1.1 else 'ما فيه تجميع'}")
    if np.isfinite(r["R:R"]):
        ok(r["R:R"] >= 2, f"Reward to risk {r['R:R']:.1f} to 1 to the target", f"العائد مقابل المخاطرة {r['R:R']:.1f} إلى 1 حتى الهدف")
    dh = r["From high %"]
    out.append(("in", L(f"{abs(dh):.1f}% under its 52-week high (${det.get('hi52', np.nan):,.2f})",
                        f"تحت قمته السنوية بـ {abs(dh):.1f}% (${det.get('hi52', np.nan):,.2f})")))
    if det.get("ext", 0) > 3:
        out.append(("no", L(f"Stretched: {det['ext']:.1f} ATR above its 20-day average; better on a pullback",
                            f"ممتد: {det['ext']:.1f} ATR فوق متوسط 20؛ الأفضل تنتظر تراجع")))
    if pd.notna(r["Earnings"]) and 0 <= r["Earnings"] <= 10:
        out.append(("no" if r["Earnings"] <= 5 else "in", L(f"Earnings in {int(r['Earnings'])} trading days: a gap can jump the stop",
                                                            f"إعلان أرباح بعد {int(r['Earnings'])} أيام تداول: الفجوة ممكن تقفز فوق الوقف")))
    return out


def detail(r, det, got):
    sym = r["Symbol"]
    k = r["Setup"]
    with st.container(key=f"hnsec_head_{_key(sym)}"):
        badges = T.badge(sector_name(r["Sector"]) if r["Sector"] else "—", "gold", "category")
        for s_ in det.get("setups", []):
            badges += T.badge(setup_name(s_["key"]) + " · " + L(*H.STATUS[s_["status"]][:2]), "down" if s_["side"] < 0 else H.STATUS[s_["status"]][2],
                              H.SETUPS[s_["key"]][2])
        for ic_, txt, kind in flags_of(r):
            badges += T.badge(txt, kind, ic_)
        ui.html(f'<div class="card hndh">{T.logo_obj(sym, 48)}<div class="nm"><b>{T.esc(sym)}</b><span>{T.esc(str(r["Name"]))}</span></div>'
                f'{ring(r["Score"], r["Grade"], 62)}<div class="bd">{badges}</div>'
                f'<div class="px"><b>{_money_px(r["Price"])}</b>{T.pill(r["Chg %"])}</div></div>')
        if k in H.SETUPS:
            ui.html(f'<div class="hnnote" style="margin-top:10px">{T.icon(H.SETUPS[k][2], _C)} <b>{T.esc(setup_name(k))}:</b> '
                    f'{T.esc(L(H.SETUPS[k][6], H.SETUPS[k][7]))}</div>')

    d, spy5 = _history5(sym, H.BUILD)
    with st.container(key=f"hnsec_body_{_key(sym)}"):
        left, right = st.columns([1.7, 1], gap="medium")
        with left:
            if d is not None and np.isfinite(r["Entry"]):
                levels = [(L("Entry", "دخول"), r["Entry"], _A, "solid"), (L("Stop", "وقف"), r["Stop"], _D, "dash"),
                          (L("Target", "هدف"), r["Target"], _U, "dash")]
                ui.chart(charts.price_chart(d.tail(190), "Candles", ["SMA 20", "SMA 50", "SMA 200"], [], False, levels=levels, height=470),
                         key=f"hn_chart_{_key(sym)}")
            elif d is not None:
                ui.chart(charts.price_chart(d.tail(190), "Candles", ["SMA 20", "SMA 50", "SMA 200"], [], False, height=470), key=f"hn_chart_{_key(sym)}")
        with right:
            ui.sec("donut_large", "Why this score", "ليش هالتقييم")
            parts = {"trend": r["Trend"], "rs": r["RS"], "volume": r["Accum"], "setup": r["SetupPts"], "risk": r["RiskPts"]}
            ui.html('<div class="hnparts">' + "".join(
                f'<div class="r"><span>{T.esc(L(*H.PARTS[p]))} <span class="w">· {int(H.WEIGHTS[p] * 100)}%</span></span>'
                f'<div class="bar"><i style="width:{float(v):.0f}%"></i></div><b>{float(v):.0f}</b></div>' for p, v in parts.items()) + "</div>")
            icons = {"ok": "check_circle", "no": "cancel", "in": "info"}
            ui.html('<div class="hnwhy">' + "".join(f'<div class="w {kd}">{T.icon(icons[kd])}<span>{T.esc(t)}</span></div>' for kd, t in _why(r, det))
                    + "</div>")

    if np.isfinite(r["Entry"]):
        with st.container(key=f"hnsec_plan_{_key(sym)}"):
            ui.sec("flag", "Trade plan", "خطة التداول")
            entry, stop, tgt = float(r["Entry"]), float(r["Stop"]), float(r["Target"])
            side = int(r["Side"] or 1)
            acct, risk = float(ss.get("hn_acct") or 100_000), float(ss.get("hn_risk") or 1.0)
            n = H.size(entry, stop, acct, risk) if side > 0 else H.size(stop, entry, acct, risk)
            mb = next((s_ for s_ in det.get("setups", []) if s_["key"] == k), None)
            max_bars = H.SETUPS[k][5] or (PBK.defaults(H.PLAYBOOK_OF[k])["max_bars"] if k in H.PLAYBOOK_OF else None)
            watch = r["Status"] == "watch"
            tiles = [("en", L("Buy above", "شراء فوق") if watch else L("Entry", "الدخول"), _money_px(entry),
                      L("on a close above it, next open", "بإغلاق فوقه، والتنفيذ عند الافتتاح التالي") if watch else
                      L("next open, near this price", "الافتتاح القادم، قرب هذا السعر")),
                     ("sl", L("Stop loss", "وقف الخسارة"), _money_px(stop), f"{_pct(entry, stop):+.1f}% · {abs(entry - stop) / max(r['ATR %'] * r['Price'] / 100, 1e-9):.1f} ATR"),
                     ("tp", L("Target", "الهدف"), _money_px(tgt), f"{_pct(entry, tgt):+.1f}%"),
                     ("", "R:R", f"{r['R:R']:.1f} : 1" if np.isfinite(r["R:R"]) else "—", L("reward for each $1 of risk", "العائد لكل 1$ مخاطرة")),
                     ("", L("Position size", "حجم الصفقة"), f"{n:,} {L('sh', 'سهم')}", f"{_money_px(n * entry)} · {n * entry / acct * 100:.0f}% {L('of the account', 'من المحفظة')}"),
                     ("", L("Max loss", "أقصى خسارة"), T.money(n * abs(entry - stop)), f"{risk:g}% {L('of', 'من')} {T.money(acct)}")]
            if max_bars:
                tiles.append(("", L("Time limit", "المدة القصوى"), L(f"{max_bars} sessions", f"{max_bars} جلسة"),
                              L("exit if the target isn't reached", "اخرج إذا ما وصل الهدف")))
            ui.html('<div class="hnplan">' + "".join(f'<div class="p {c_}"><div class="l">{T.esc(l_)}</div><div class="v">{v_}</div>'
                                                     f'<div class="s">{T.esc(s_)}</div></div>' for c_, l_, v_, s_ in tiles) + "</div>")
            if _session_live():
                st.caption(L("The market is open: today's candle is still moving, so a signal of today is confirmed only at the close.",
                             "السوق مفتوح: شمعة اليوم لسا تتحرك، فإشارة اليوم تتأكد بس عند الإغلاق."))

    if k in H.SETUPS and H.SETUPS[k][3] != "watch":
        with st.container(key=f"hnsec_edge_{_key(sym)}"):
            ui.sec("history", f"{setup_name(k)} on {sym}: the last 5 years", f"{setup_name(k)} على {sym}: آخر 5 سنوات")
            e, bt = _edge(sym, k, H.BUILD)
            if not e:
                st.caption(L("This setup didn't trigger on this stock in the last 5 years (or the trade is still open), so there is no track record yet.",
                             "هذه الفرصة ما ظهرت على هذا السهم خلال آخر 5 سنوات (أو صفقتها لسا مفتوحة)، فما فيه سجل للحين."))
            else:
                pf = "∞" if e["pf"] == np.inf else f"{e['pf']:.2f}"
                tiles = [T.kpi("receipt_long", L("Trades", "الصفقات"), f"{e['n']}", "", None),
                         T.kpi("target", L("Win rate", "نسبة النجاح"), f"{e['win']:.0f}%", "", "pos" if e["win"] >= 50 else "neg"),
                         T.kpi("functions", L("Average", "المتوسط"), f"{e['avg_r']:+.2f}R", f"{e['avg_ret']:+.1f}% {L('per trade', 'لكل صفقة')}",
                               T.cls(e["avg_r"])),
                         T.kpi("balance", L("Profit factor", "معامل الربح"), pf, "", "pos" if e["pf"] >= 1 else "neg"),
                         T.kpi("savings", L("Total", "المجموع"), f"{e['total_r']:+.1f}R", L("in risk units", "بوحدات المخاطرة"), T.cls(e["total_r"]))]
                ui.html('<div class="pbk" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px">' + "".join(tiles) + "</div>")
                show = bt.tail(12).iloc[::-1].copy()
                show["Entry Date"] = pd.to_datetime(show["Entry Date"]).dt.date
                show["Exit Date"] = pd.to_datetime(show["Exit Date"]).dt.date
                reason = {"Stop": L("Stop", "الوقف"), "Target": L("Target", "الهدف"), "Time": L("Time limit", "المدة")}
                show["Reason"] = show["Reason"].map(reason)
                N = {"Entry Date": L("Entry", "الدخول"), "Entry": L("Price", "السعر"), "Exit Date": L("Exit", "الخروج"), "Exit": L("Exit price", "سعر الخروج"),
                     "Ret %": L("Return %", "العائد %"), "Bars": L("Days", "الأيام"), "Reason": L("Exit by", "الخروج بـ")}
                show = show[["Entry Date", "Entry", "Exit Date", "Exit", "R", "Ret %", "Bars", "Reason"]].rename(columns=N)
                st.dataframe(show.style.map(T.color_style, subset=["R", N["Ret %"]]).format(
                    {N["Entry"]: "{:,.2f}", N["Exit"]: "{:,.2f}", "R": "{:+.2f}", N["Ret %"]: "{:+.1f}%"}), hide_index=True,
                    height=min(420, 38 + 35 * len(show)))
                st.caption(L("Same rule, same stop, target and time limit; entry at the next open, the stop checked first when a candle "
                             "touches both. Past results on one stock are a guide, not a promise.",
                             "نفس الشرط ونفس الوقف والهدف والمدة؛ الدخول عند الافتتاح التالي، والوقف يُفحص أول إذا لمست الشمعة الاثنين. "
                             "نتائج الماضي على سهم واحد دليل وليست ضمان."))

    with st.container(key=f"hnsec_act_{_key(sym)}"):
        with st.container(key="hnact", horizontal=True):
            if st.button(L("Stock page", "صفحة السهم"), icon=":material/candlestick_chart:", key="hn_open"):
                ui.open_stock(sym)
            if st.button("Catalyst Pro", icon=":material/bolt:", key="hn_cat"):
                ss.symbol = sym
                ui.goto("catalyst")
            if st.button(L("Test it in Paper Bots", "اختبرها في البوتات الافتراضية"), icon=":material/science:", key="hn_test"):
                ss["pb_qt_sym"], ss["pb_qt_per"], ss["pb_qt_on"] = sym, "5y", True
                if k in H.PLAYBOOK_OF:
                    ss["pb_qt_strat"] = H.PLAYBOOK_OF[k]
                ui.goto("paper")
            wl = ss.setdefault("watchlist", [])
            if sym in wl:
                st.button(L("In watchlist", "في المتابعة"), icon=":material/star:", key="hn_wl", disabled=True)
            elif st.button(L("Add to watchlist", "أضف للمتابعة"), icon=":material/star:", key="hn_wl"):
                wl.append(sym)
                st.toast(L(f"{sym} added to your watchlist", f"انضاف {sym} لقائمة المتابعة"), icon=":material/star:")


# ---------------------------------------------------------------- the table and the charts
def table(view):
    cols = ["Symbol", "Name", "Sector", "Grade", "Score", "Setup", "Status", "Price", "Chg %", "1M %", "3M %", "RS", "RVOL", "From high %",
            "Entry", "Stop", "Target", "R:R", "Earnings"]
    show = view[cols].copy()
    show["Sector"] = show["Sector"].map(lambda s: sector_name(s) if s else "—")
    show["Setup"] = show["Setup"].map(setup_name)
    show["Status"] = show["Status"].map(lambda s: L(*H.STATUS[s][:2]) if s in H.STATUS else "—")
    N = {"Symbol": L("Symbol", "الرمز"), "Name": L("Company", "الشركة"), "Sector": L("Sector", "القطاع"), "Grade": L("Grade", "الدرجة"),
         "Score": L("Score", "التقييم"), "Setup": L("Setup", "الفرصة"), "Status": L("Status", "الحالة"), "Price": L("Price", "السعر"),
         "Chg %": L("Chg %", "التغير %"), "1M %": L("1M %", "شهر %"), "3M %": L("3M %", "3 أشهر %"), "RS": "RS", "RVOL": "RVOL",
         "From high %": L("From 52W high %", "عن القمة السنوية %"), "Entry": L("Entry", "الدخول"), "Stop": L("Stop", "الوقف"),
         "Target": L("Target", "الهدف"), "R:R": "R:R", "Earnings": L("Earnings in (days)", "الأرباح بعد (أيام)")}
    show = show.rename(columns=N)
    st.dataframe(show, hide_index=True, height=min(560, 38 + 35 * len(show)),
                 column_config={N["Score"]: st.column_config.ProgressColumn(N["Score"], min_value=0, max_value=100, format="%.0f"),
                                N["Price"]: st.column_config.NumberColumn(format="%.2f"), N["Chg %"]: st.column_config.NumberColumn(format="%+.2f%%"),
                                N["1M %"]: st.column_config.NumberColumn(format="%+.1f%%"), N["3M %"]: st.column_config.NumberColumn(format="%+.1f%%"),
                                "RVOL": st.column_config.NumberColumn(format="%.1f×"), N["From high %"]: st.column_config.NumberColumn(format="%.1f%%"),
                                N["Entry"]: st.column_config.NumberColumn(format="%.2f"), N["Stop"]: st.column_config.NumberColumn(format="%.2f"),
                                N["Target"]: st.column_config.NumberColumn(format="%.2f"), "R:R": st.column_config.NumberColumn(format="%.1f"),
                                N["Earnings"]: st.column_config.NumberColumn(format="%d")})
    a, b, _ = st.columns([1, 1.3, 3])
    a.download_button(L("Export CSV", "تصدير CSV"), show.to_csv(index=False).encode("utf-8-sig"), "opportunities.csv", "text/csv",
                      icon=":material/download:", key="hn_csv", width="stretch")
    if b.button(L("Add the top 10 to my watchlist", "أضف أفضل 10 لقائمة المتابعة"), icon=":material/star:", key="hn_wl10", width="stretch"):
        wl = ss.setdefault("watchlist", [])
        new = [s for s in view["Symbol"].head(10) if s not in wl]
        wl.extend(new)
        st.toast(L(f"{len(new)} added to your watchlist", f"انضاف {len(new)} لقائمة المتابعة"), icon=":material/star:")


def sector_chart(sec):
    if sec is None or sec.empty:
        return
    top = sec.head(12).iloc[::-1]
    labels = [f"{sector_name(s)} · {int(o)}" for s, o in zip(top.index, top["opp"])]
    ui.chart(charts.hbar(labels, [float(x) for x in top["rs"]], L("Sectors by strength (average RS · opportunities)",
                                                                  "القطاعات حسب القوة (متوسط RS · عدد الفرص)"), 460, suffix=""), key="hn_sec")


# ---------------------------------------------------------------- page
def page_scanner():
    ui.html(CSS + (RTL_CSS if is_ar() else ""))
    _init()
    unis = universes()
    key, symbols = _symbols(unis)
    got = None
    if symbols:
        with st.spinner(L(f"Hunting in {len(symbols)} stocks...", f"جاري الصيد في {len(symbols)} سهم...")):
            try:
                got = run_hunt(key, symbols, ss.get("hn_nonce", 0), H.BUILD)
            except Exception:
                got = None
    ui.html(hero_html(got, unis[key][0]))
    hunt_bar(unis)
    if not symbols:
        st.info(L("Type at least one symbol.", "اكتب رمز واحد على الأقل."), icon=":material/info:")
        ui.foot()
        return
    if not got or got["res"] is None or got["res"].empty:
        st.warning(L("No price data came back. Try again in a minute, or check the symbols.",
                     "ما وصلت بيانات أسعار. حاول بعد دقيقة، أو تأكد من الرموز."), icon=":material/error:")
        ui.foot()
        return
    res, det = got["res"], got["det"]
    with st.container(key="hnsec_mood"):
        ui.safe(lambda: ui.html(mood_html(got["reg"])))
        if got["n"] < 30:
            st.caption(L("A short list: the breadth numbers and the RS rating mean more with a bigger universe (RS is measured against SPY here).",
                         "قائمة قصيرة: أرقام الاتساع وتقييم RS أدق مع نطاق أكبر (RS هنا مقاس مقابل SPY)."))
    with st.container(key="hnsec_filters"):
        ui.sec("filter_alt", "Filters", "التصفية")
        ui.safe(filters, res)
    view = apply(res)
    if view.empty:
        with st.container(key="hnsec_none"):
            st.info(L("Nothing matches these filters. Lower the grade, clear the setups, or scan a bigger universe.",
                      "ما فيه شي يطابق هالتصفية. نزّل الدرجة، أو شيل الفرص المختارة، أو افحص نطاق أكبر."), icon=":material/search_off:")
    else:
        if ss.get("hn_sel") not in set(view["Symbol"]):
            ss["hn_sel"] = view["Symbol"].iloc[0]
        with st.container(key="hnsec_cards"):
            ui.sec("target", f"Best opportunities ({len(view)})", f"أفضل الفرص ({len(view)})")
            ui.safe(cards, view, det)
        r = view[view["Symbol"] == ss["hn_sel"]].iloc[0]
        ui.safe(detail, r, det.get(r["Symbol"], {}), got)
        with st.container(key="hnsec_table"):
            ui.sec("table_rows", "Every match", "كل النتائج")
            ui.safe(table, view)
    with st.container(key="hnsec_charts"):
        c1, c2 = st.columns([1.15, 1], gap="medium")
        with c1:
            ui.safe(lambda: ui.chart(charts.hunt_map(res, L("Opportunity map: leaders sit top right", "خريطة الفرص: القادة فوق يمين"),
                                                     (L("From 52-week high %", "البعد عن القمة السنوية %"), L("RS rating (1-99)", "تقييم RS (1-99)"),
                                                      L("Score", "التقييم"))), key="hn_map"))
        with c2:
            ui.safe(sector_chart, got["sec"])
    with st.expander(L("How the hunter works", "كيف يشتغل الصائد"), icon=":material/help:"):
        ui.html('<div class="hnnote">' + L(
            "<b>Setups</b> are exact rules on the daily close (the four combined strategies of the Paper Bots, breakouts, leaders, "
            "golden crosses, oversold dips, accumulation days, gaps, squeezes and breakdowns). A setup is <b>new today</b> when it fired "
            "on the latest candle, <b>active</b> when it fired in the last 2-3 sessions and the price is still between its stop and its "
            "target, and on <b>watch</b> when it is building. <b>The score</b> (0-100): trend 25%, relative strength 25% (RS 1-99: "
            "the 3-12 month return ranked against every stock scanned), accumulation 15%, the setup 20% and reward-to-risk 15%; "
            "earnings within 5 days (-8) and thin trading (-5) cost points, and a stock without a buying setup can't pass 49. "
            "Grades: A+ from 85, A from 75, B from 65, C from 50.",
            "<b>الفرص</b> شروط دقيقة على الإغلاق اليومي (الاستراتيجيات المركّبة الأربع في البوتات الافتراضية، والاختراقات، والقادة، "
            "والتقاطع الذهبي، والتشبع البيعي، وأيام التجميع، والفجوات، والانضغاط، والكسر الهابط). الفرصة <b>جديدة اليوم</b> إذا ظهرت على آخر "
            "شمعة، و<b>نشطة</b> إذا ظهرت خلال آخر 2-3 جلسات والسعر لسا بين الوقف والهدف، و<b>مراقبة</b> إذا لسا تتكوّن. <b>التقييم</b> (من 100): "
            "الاتجاه 25%، والقوة النسبية 25% (RS من 1 إلى 99: عائد 3 إلى 12 شهر مرتب مقابل كل الأسهم المفحوصة)، والتجميع 15%، والفرصة 20%، "
            "والعائد مقابل المخاطرة 15%؛ وإعلان أرباح خلال 5 أيام (-8) وضعف السيولة (-5) ينقصون النقاط، والسهم بدون فرصة شراء ما يتعدى 49. "
            "الدرجات: A+ من 85، وA من 75، وB من 65، وC من 50.") + "</div>")
    st.caption(L("Daily prices from Yahoo Finance (may be delayed). This is a research tool, not investment advice: check the chart and the news "
                 "before any trade, and never risk more than you can afford to lose.",
                 "أسعار يومية من ياهو فاينانس (قد تكون متأخرة). هذي أداة بحث وليست نصيحة استثمارية: راجع الشارت والأخبار قبل أي صفقة، "
                 "ولا تخاطر بأكثر مما تتحمل خسارته."))
    ui.foot()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "8.4"
