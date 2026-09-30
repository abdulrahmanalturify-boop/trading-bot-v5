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
import engine
import hunter as H
import mcal
import paperbots as PB
import playbooks as PBK
import ta
import taxonomy as X
import theme as T
import ui
import universe as U
from i18n import L, industry_name, is_ar, sector_name
from sp500 import gics_name

ss = st.session_state
_A, _V, _C, _G, _D, _U, _MU, _BD, _BG = T.ACCENT, T.VIOLET, T.CYAN, T.GOLD, T.DOWN, T.UP, "#9D97A5", T.BORDER, T.CARD2
GRADE_COLOR = {"A+": "#22C55E", "A": "#4ADE80", "B": _C, "C": _G, "D": _D}
FLAG = {"earnings": ("event", "Earnings in {d} days", "أرباح بعد {d} أيام", "gold"), "extended": ("height", "Stretched", "ممتد", "org"),
        "thin": ("water_drop", "Thin trading", "سيولة ضعيفة", "neu")}
MIN_GRADE = {"A+": 85, "A": 75, "B": 65, "C": 50, "all": 0}
N_CARDS = 8

CSS = f"""<style>
/* ---------- hero: a radar in the brand's colours ---------- */
.hnhero {{ position:relative; overflow:hidden; border-radius:22px; border:1px solid {_BD}; margin:2px 0 16px; min-height:250px;
  background:linear-gradient(120deg,#0E0918,#1B1430,#27184A,#130F24); background-size:300% 300%; animation:sky 20s ease-in-out infinite; }}
.hnhero::after {{ content:""; position:absolute; left:0; right:0; top:0; height:1px; background:linear-gradient(90deg,transparent,rgba(196,181,253,.5),transparent); z-index:3; pointer-events:none; }}
.hnhero .grid {{ position:absolute; inset:0; pointer-events:none;
  background-image:linear-gradient(rgba(45,182,235,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(45,182,235,.07) 1px,transparent 1px);
  background-size:36px 36px; -webkit-mask-image:radial-gradient(ellipse at 78% 50%,#000 0%,transparent 66%);
  mask-image:radial-gradient(ellipse at 78% 50%,#000 0%,transparent 66%); }}
.hnhero .art {{ position:absolute; top:0; bottom:0; right:0; width:52%; pointer-events:none; }}
.hnhero .art svg {{ width:100%; height:100%; display:block; }}
.hnhero.rtl .art {{ right:auto; left:0; }}
.hnhero.rtl .sweep {{ transform-origin:160px 125px; }}
.hnhero.rtl .grid {{ -webkit-mask-image:radial-gradient(ellipse at 22% 50%,#000 0%,transparent 66%);
  mask-image:radial-gradient(ellipse at 22% 50%,#000 0%,transparent 66%); }}
.hnhero .txt {{ position:relative; z-index:2; padding:26px 30px 24px; max-width:640px;
  background:linear-gradient(90deg,rgba(14,9,24,.8) 0%,rgba(14,9,24,.35) 72%,rgba(14,9,24,0) 100%); }}
.hnhero.rtl .txt {{ margin-left:auto; background:linear-gradient(270deg,rgba(14,9,24,.8) 0%,rgba(14,9,24,.35) 72%,rgba(14,9,24,0) 100%); }}
.hnhero .eb {{ color:{_C}; font-weight:600; letter-spacing:.2em; font-size:.72rem; text-transform:uppercase; display:flex; align-items:center; gap:8px; }}
.hnhero .t {{ font-size:2.7rem; font-weight:300; line-height:1.04; margin:8px 0 8px; color:#fff; letter-spacing:-.035em; }}
.hnhero .t b {{ background:linear-gradient(90deg,{_A},{_V},{_C}); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.hnhero .tg {{ color:#CAC5D1; font-size:.94rem; line-height:1.6; max-width:540px; }}
.hnhero .chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
.hnhero .chip {{ background:rgba(26,22,36,.8); border:1px solid {_BD}; backdrop-filter:blur(6px); border-radius:10px; padding:6px 10px;
  font-size:.8rem; display:inline-flex; align-items:center; gap:7px; color:#CCC7D3; }}
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
[class*="st-key-hnbar"]::before {{ content:""; position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg,transparent,rgba(196,181,253,.5),transparent); }}
[class*="st-key-hn_go"] button {{ min-height:44px !important; border:0 !important; border-radius:12px !important;
  background:linear-gradient(95deg,{_A} 0%,{_V} 62%,{_C} 130%) !important; box-shadow:0 10px 26px rgba(59,139,235,.35); }}
[class*="st-key-hn_go"] button:hover {{ filter:brightness(1.08); transform:translateY(-1px); }}
[class*="st-key-hn_go"] button p, [class*="st-key-hn_go"] button [data-testid="stIconMaterial"] {{ color:#fff !important; font-weight:600 !important; }}

/* ---------- market mood ---------- */
.hnreg {{ display:grid; grid-template-columns:1.5fr repeat(4,1fr); gap:10px; margin:2px 0 4px; }}
@media (max-width: 1000px) {{ .hnreg {{ grid-template-columns:1fr 1fr; }} }}
.hnreg .tl {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:12px 14px; position:relative; overflow:hidden; }}
.hnreg .tl .l {{ color:{_MU}; font-size:.68rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; display:flex; align-items:center; gap:6px; }}
.hnreg .tl .l .ms {{ font-size:.95rem; color:{_C}; }}
.hnreg .tl .v {{ font-size:1.35rem; font-weight:600; color:#fff; margin-top:4px; direction:ltr; unicode-bidi:isolate; }}
.hnreg .tl .s {{ color:{_MU}; font-size:.74rem; margin-top:2px; }}
.hnreg .bar {{ height:6px; border-radius:6px; background:rgba(157,151,165,.18); margin-top:8px; overflow:hidden; direction:ltr; }}
.hnreg .bar i {{ display:block; height:100%; border-radius:6px; }}
.hnreg .mood {{ border-width:1.5px; }}
.hnreg .mood .v {{ font-size:1.08rem; display:flex; align-items:center; gap:8px; direction:inherit; }}
.hnreg .mood .dot {{ width:10px; height:10px; border-radius:50%; box-shadow:0 0 0 4px rgba(255,255,255,.06); flex:none; }}
.hnreg .mood .s {{ color:#CAC5D1; line-height:1.45; }}
.hnreg .mood.on {{ border-color:{_U}66; background:linear-gradient(135deg,rgba(34,197,94,.14),{T.CARD}); }}
.hnreg .mood.mixed {{ border-color:{_G}66; background:linear-gradient(135deg,rgba(245,185,74,.13),{T.CARD}); }}
.hnreg .mood.off {{ border-color:{_D}66; background:linear-gradient(135deg,rgba(239,68,68,.14),{T.CARD}); }}

/* ---------- opportunity cards ---------- */
.hnc {{ margin:0 !important; height:336px; box-sizing:border-box; display:flex; flex-direction:column; overflow:hidden; position:relative;
  transition:box-shadow .18s ease, border-color .18s ease; }}
.hnc::before {{ content:""; position:absolute; left:0; right:0; top:0; height:1px; background:linear-gradient(90deg,transparent,rgba(196,181,253,.5),transparent); opacity:.35; }}
.hnc.sel {{ border-color:{_A} !important; box-shadow:0 0 0 1px {_A}66, 0 12px 30px {_A}26; }}
.hnc.sel::before {{ opacity:1; }}
.hnc .top {{ display:flex; justify-content:space-between; align-items:center; gap:6px; margin:-2px 0 10px; }}
.hnc .su {{ display:inline-flex; align-items:center; gap:5px; font-size:.68rem; font-weight:600; color:#CCC7D3; min-width:0; }}
.hnc .su .ms {{ font-size:1rem; color:{_C}; flex:none; }}
.hnc .su .tx {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.hntag {{ display:inline-flex; align-items:center; gap:4px; font-size:.6rem; font-weight:600; letter-spacing:.05em; border-radius:6px; padding:2px 6px;
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
.hnring .g b {{ font-size:.92rem; font-weight:600; color:#fff; }}
.hnring .g span {{ font-size:.58rem; color:{_MU}; margin-top:2px; }}
.hnc .spk {{ margin:10px -2px 6px; height:58px; }}
.hnc .spk svg {{ width:100%; height:58px; display:block; overflow:visible; }}
.hnc .lv {{ display:grid; grid-template-columns:repeat(3,1fr); gap:6px; margin-top:auto; direction:ltr; }}
.hnc .lv div {{ background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.05); border-radius:10px; padding:5px 7px; min-width:0; }}
.hnc .lv span {{ display:block; color:{_MU}; font-size:.6rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; }}
.hnc .lv b {{ display:block; color:#fff; font-size:.8rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.hnc .lv i {{ display:block; font-style:normal; font-size:.66rem; font-weight:600; line-height:1.2; }}
.hnc .mt {{ display:grid; grid-template-columns:repeat(3,1fr); gap:6px; margin:2px 0 8px; direction:ltr; }}
.hnc .mt div {{ min-width:0; }}
.hnc .mt span {{ display:block; color:{_MU}; font-size:.6rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.hnc .mt b {{ font-size:.8rem; font-weight:600; }}
.hnc .lv .dn {{ color:#F87171; }} .hnc .lv .up {{ color:#4ADE80; }}
.hnc .ft {{ display:flex; flex-wrap:nowrap; gap:5px; margin-top:10px; padding-bottom:2px; overflow:hidden; min-height:24px; align-items:center; }}
.hnc .ft .c {{ display:inline-flex; align-items:center; gap:4px; font-size:.68rem; font-weight:600; color:#B1ABBA; background:rgba(157,151,165,.10);
  border:1px solid {_BD}; border-radius:999px; padding:3px 9px; white-space:nowrap; line-height:1.3; flex:none; }}
.hnc .ft .c b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }}
.hnc .ft .c.w {{ color:{T.YEL_FG}; background:{T.YEL_BG}; border-color:transparent; }}
.hnc .ft .c .ms {{ font-size:.85rem; }}
[class*="st-key-hncard_"] {{ position:relative; transition:transform .18s ease; }}
[class*="st-key-hncard_"]:hover {{ transform:translateY(-4px); z-index:3; }}
[class*="st-key-hncard_"]:hover .hnc {{ box-shadow:0 14px 34px rgba(59,139,235,.22); }}
[class*="st-key-hncard_"]:hover .hnc::before {{ opacity:1; }}
[class*="st-key-hncard_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-hncard_"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
[class*="st-key-hncard_"] [class*="st-key-hn_pick_"] {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; width:auto !important; }}
[class*="st-key-hncard_"] [class*="st-key-hn_pick_"] .stButton, [class*="st-key-hncard_"] [class*="st-key-hn_pick_"] button
  {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}

/* ---------- the opened opportunity ---------- */
.hndh {{ position:relative; overflow:hidden; margin:0 !important; display:flex; align-items:center; gap:14px; flex-wrap:wrap; }}
.hndh::before {{ content:""; position:absolute; top:0; bottom:0; left:0; width:2px; background:{T.ELECTRIC}; }}
.hndh .nm {{ display:flex; flex-direction:column; line-height:1.25; }}
.hndh .nm b {{ font-size:1.3rem; color:#fff; }} .hndh .nm span {{ color:{_MU}; font-size:.8rem; }}
.hndh .bd {{ display:flex; flex-wrap:wrap; gap:4px; flex:1; min-width:240px; }}
.hndh .px {{ text-align:end; margin-inline-start:auto; }}
.hndh .px b {{ display:block; font-size:1.3rem; color:#fff; direction:ltr; }}
.hndh .hnring, .hndh .hnring svg {{ width:62px; height:62px; }}
.hndh .hnring .g b {{ font-size:1.2rem; }}
.hnparts {{ display:flex; flex-direction:column; gap:10px; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:16px 16px 14px; }}
.hnparts .r {{ display:grid; grid-template-columns:130px 1fr 44px; gap:10px; align-items:center; font-size:.82rem; color:#E5E1EB; font-weight:600; }}
.hnparts .r .w {{ color:#A59FB8; font-size:.7rem; font-weight:500; }}
.hnparts .r b {{ color:#fff; text-align:end; direction:ltr; }}
.hnparts .bar {{ height:8px; border-radius:8px; background:rgba(157,151,165,.16); overflow:hidden; direction:ltr; }}
.hnparts .bar i {{ display:block; height:100%; border-radius:8px; background:linear-gradient(90deg,{_A},{_V},{_C}); }}
.hnwhy {{ margin-top:12px; display:flex; flex-direction:column; gap:6px; }}
.hnwhy .w {{ display:flex; gap:8px; align-items:flex-start; font-size:.8rem; color:#DDD9E2; line-height:1.45; }}
.hnwhy .w .ms {{ font-size:1rem; flex:none; margin-top:1px; }}
.hnwhy .w.ok .ms {{ color:#4ADE80; }} .hnwhy .w.no .ms {{ color:#F87171; }} .hnwhy .w.in .ms {{ color:{_G}; }}
.hnplan {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; }}
.hnplan .p {{ position:relative; overflow:hidden; background:{T.TOP}, linear-gradient(160deg,rgba(59,139,235,.16),rgba(123,69,240,.08) 55%,{T.CARD});
  border:1px solid {_BD}; border-radius:14px; padding:10px 12px; transition:border-color .18s ease, box-shadow .18s ease, transform .18s ease; }}
.hnplan .p::after {{ content:""; position:absolute; inset:auto 0 0 0; height:2px; background:linear-gradient(90deg,{_A},{_V},{_C}); opacity:0;
  transition:opacity .18s ease; }}
.hnplan .p:hover {{ border-color:rgba(121,184,244,.45); box-shadow:0 12px 28px rgba(59,139,235,.16); transform:translateY(-2px); }}
.hnplan .p:hover::after {{ opacity:.9; }}
.hnplan .p .l {{ color:#CCC7D3; font-size:.66rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; }}
.hnplan .p .v {{ color:#fff; font-size:1.05rem; font-weight:600; margin-top:3px; direction:ltr; unicode-bidi:isolate; }}
.hnplan .p .s {{ color:{_MU}; font-size:.72rem; margin-top:1px; }}
.hnplan .p.sl .v {{ color:#F87171; }} .hnplan .p.tp .v {{ color:#4ADE80; }} .hnplan .p.en .v {{ color:#9DCBF7; }}
.hnnote {{ color:#CAC5D1; font-size:.84rem; line-height:1.6; background:rgba(59,139,235,.07); border:1px solid {_A}33; border-radius:12px; padding:10px 12px; }}
.hnnote b {{ color:#fff; }}
[class*="st-key-hnsec_"] {{ margin-top:18px; }}
[class*="st-key-hnsec_"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
[class*="st-key-hnsec_"] .sec {{ margin:0 !important; }}
[class*="st-key-hnact"] button {{ border-radius:12px !important; min-height:42px !important; }}
/* ---------- filters: one card, modern chips ---------- */
[class*="st-key-hnfilt"] {{ position:relative; overflow:hidden; background:linear-gradient(180deg,{_BG},{T.CARD}); border:1px solid {_BD};
  border-radius:18px; padding:14px 18px 16px; box-shadow:0 10px 26px rgba(0,0,0,.18); gap:12px !important; }}
[class*="st-key-hnfilt"]::before {{ content:""; position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg,transparent,rgba(196,181,253,.5),transparent); }}
.hnfh {{ display:flex; align-items:center; gap:9px; flex-wrap:wrap; }}
.hnfh .ms {{ color:#fff; background:{T.PANEL}; box-shadow:{T.GLOW}; border-radius:8px; padding:4px; font-size:1rem; }}
.hnfh b {{ color:#fff; font-size:.98rem; }}
.hnfh span:last-child {{ color:{_MU}; font-size:.78rem; font-weight:600; }}
[class*="st-key-hnfilt"] [data-testid="stButtonGroup"] {{ gap:8px !important; flex-wrap:wrap; }}
[class*="st-key-hnfilt"] [data-testid="stBaseButton-pills"], [class*="st-key-hnfilt"] [data-testid="stBaseButton-pillsActive"] {{
  border-radius:999px !important; min-height:34px !important; padding:4px 14px !important; transition:all .15s ease; }}
[class*="st-key-hnfilt"] [data-testid="stBaseButton-pills"] {{ background:rgba(59,139,235,.07) !important; border:1px solid rgba(59,139,235,.30) !important; }}
[class*="st-key-hnfilt"] [data-testid="stBaseButton-pills"]:hover {{ background:rgba(59,139,235,.16) !important; border-color:{_A} !important; transform:translateY(-1px); }}
[class*="st-key-hnfilt"] [data-testid="stBaseButton-pills"] p {{ color:#DCEBFA !important; font-weight:600 !important; font-size:.84rem !important; }}
[class*="st-key-hnfilt"] [data-testid="stBaseButton-pillsActive"] {{ background:linear-gradient(95deg,{_A},{_V}) !important; border:1px solid transparent !important;
  box-shadow:0 6px 18px rgba(59,139,235,.35); }}
[class*="st-key-hnfilt"] [data-testid="stBaseButton-pillsActive"] p {{ color:#fff !important; font-weight:600 !important; font-size:.84rem !important; }}
[class*="st-key-hnfilt"] [data-testid="stBaseButton-segmented_control"], [class*="st-key-hnfilt"] [data-testid="stBaseButton-segmented_controlActive"] {{
  min-height:38px !important; padding:4px 14px !important; }}
[class*="st-key-hnfilt"] [data-testid="stBaseButton-segmented_control"] {{ background:rgba(14,9,24,.55) !important; border-color:{_BD} !important; }}
[class*="st-key-hnfilt"] [data-testid="stBaseButton-segmented_control"]:hover {{ background:rgba(59,139,235,.12) !important; }}
[class*="st-key-hnfilt"] [data-testid="stBaseButton-segmented_control"] p {{ color:#CCC7D3 !important; font-weight:600 !important; }}
[class*="st-key-hnfilt"] [data-testid="stBaseButton-segmented_controlActive"] {{ background:linear-gradient(95deg,{_A},{_V}) !important; border-color:transparent !important;
  box-shadow:0 6px 16px rgba(59,139,235,.30); z-index:1; }}
[class*="st-key-hnfilt"] [data-testid="stBaseButton-segmented_controlActive"] p {{ color:#fff !important; font-weight:600 !important; }}
[class*="st-key-hnfilt"] [data-testid="stCheckbox"] {{ background:rgba(14,9,24,.55); border:1px solid {_BD}; border-radius:12px; padding:8px 12px;
  min-height:38px; display:flex; align-items:center; }}
[class*="st-key-hnfilt"] [data-testid="stCheckbox"]:hover {{ border-color:{_A}88; }}
[class*="st-key-hnfilt"] [data-testid="stCheckbox"] p {{ font-weight:600; font-size:.84rem; color:#DDD9E2; }}
.hnbox {{ position:relative; background:{T.TOP}, linear-gradient(160deg,rgba(59,139,235,.16),rgba(123,69,240,.08) 55%,{T.CARD}); border:1px solid {_BD}; border-radius:16px; padding:0 14px 4px; margin-top:12px;
  overflow:hidden; transition:border-color .18s ease, box-shadow .18s ease, transform .18s ease; }}
.hnbox:hover {{ border-color:rgba(121,184,244,.45); box-shadow:0 12px 30px rgba(59,139,235,.14); transform:translateY(-2px); }}
.hnbox .hnbt {{ margin:0 -14px 4px; padding:10px 14px 9px; border-bottom:1px solid rgba(157,151,165,.14);
  background:linear-gradient(90deg,rgba(59,139,235,.10),rgba(123,69,240,.05) 60%,transparent); }}
.hnbox .check {{ transition:background .15s ease; border-radius:8px; color:#DDD9E2; }}
.hnbox .check b {{ color:#fff; }}
.hnbox .check:hover {{ background:rgba(121,184,244,.06); }}
.hnbox .check {{ font-size:.84rem; }} .hnbox .check:last-child {{ border-bottom:0; }}
.hnbt {{ display:flex; align-items:center; gap:7px; font-weight:600; color:#CCC7D3; font-size:.74rem; letter-spacing:.09em;
  text-transform:uppercase; margin-bottom:2px; }}
.hnbt .ms {{ color:#79B8F4; font-size:1.05rem; }}
.hnbt .sc.ok {{ background:{T.POS_BG} !important; color:{T.POS_FG} !important; border-color:transparent !important; }}
.hnbt .sc.bad {{ background:{T.NEG_BG} !important; color:{T.NEG_FG} !important; border-color:transparent !important; }}
.hnbt .sc {{ margin-inline-start:auto; font-size:.72rem; font-weight:600; letter-spacing:0; text-transform:none; color:#DCEBFA; background:rgba(59,139,235,.16); border:1px solid {_A}44;
  border-radius:999px; padding:2px 9px; direction:ltr; unicode-bidi:isolate; }}
[class*="st-key-hnsec_look"] h4 {{ margin:0 !important; padding:0 !important; }}
/* ---------- analyst rating card: violet with a faint cyan glow (the brand's gradient, softly) ---------- */
.hnrate {{ position:relative; overflow:hidden; border-radius:20px; padding:18px 20px 16px; border:1px solid {_BD};
  background:linear-gradient(160deg,rgba(59,139,235,.16),rgba(123,69,240,.08) 55%,{T.CARD}); box-shadow:0 10px 26px rgba(0,0,0,.22); transition:border-color .18s ease, box-shadow .18s ease, transform .18s ease; }}
.hnrate:hover {{ border-color:rgba(121,184,244,.45); box-shadow:0 14px 34px rgba(59,139,235,.16); transform:translateY(-2px); }}
.hntgt {{ position:relative; overflow:hidden; border-radius:16px; padding:0 16px 12px; margin-top:12px; border:1px solid {_BD};
  background:{T.TOP}, linear-gradient(160deg,rgba(59,139,235,.16),rgba(123,69,240,.08) 55%,{T.CARD}); transition:border-color .18s ease, box-shadow .18s ease, transform .18s ease; }}
.hntgt:hover {{ border-color:rgba(121,184,244,.45); box-shadow:0 12px 30px rgba(59,139,235,.14); transform:translateY(-2px); }}
.hntgt .hnbt {{ margin:0 -16px 6px; padding:10px 16px 9px; border-bottom:1px solid rgba(157,151,165,.14);
  background:linear-gradient(90deg,rgba(59,139,235,.10),rgba(123,69,240,.05) 60%,transparent); }}
.hntgt .sv svg {{ width:100%; height:auto; display:block; }}
.hntgt .cs {{ display:flex; flex-wrap:wrap; gap:6px; margin-top:6px; direction:ltr; }}
.hntgt .cs .c {{ display:inline-flex; align-items:center; gap:6px; font-size:.74rem; color:#B1ABBA; background:rgba(14,9,24,.45); border:1px solid {_BD};
  border-radius:999px; padding:3px 10px; }}
.hntgt .cs .c i {{ width:8px; height:8px; border-radius:50%; }}
.hntgt .cs .c b {{ color:#fff; }} .hntgt .cs .c em {{ font-style:normal; font-weight:600; }}
.hntgt .cs .c em.up {{ color:#4ADE80; }} .hntgt .cs .c em.dn {{ color:#F87171; }}
.hnrate::before {{ content:""; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,{_V},{_A},{_C}); opacity:.9; }}
.hnrate .t {{ font-size:1.3rem; font-weight:600; color:#fff; letter-spacing:-.01em; }}
.hnrate .s {{ color:#BCB6C7; font-size:.84rem; margin-top:2px; }}
.hnrate .g {{ max-width:360px; margin:10px auto 4px; }}
.hnrate .g svg {{ width:100%; height:auto; display:block; filter:drop-shadow(0 6px 18px rgba(123,69,240,.25)); }}
.hnrate .lgs {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); grid-template-rows:repeat(3,auto); grid-auto-flow:column;
  gap:8px 22px; max-width:380px; margin:8px auto 0; }}
.hnrate .rl {{ display:flex; align-items:center; gap:9px; color:#D7D3DD; font-size:.92rem; }}
.hnrate .rl i {{ width:11px; height:11px; border-radius:50%; flex:none; box-shadow:0 0 0 3px rgba(255,255,255,.05); }}
.hnrate .rl b {{ color:#fff; font-weight:600; direction:ltr; unicode-bidi:isolate; }}
.hnrate .mr {{ text-align:center; color:#BCB6C7; font-size:.8rem; margin-top:12px; }}
.hnrate .mr b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }} .hnrate .mr span {{ color:{_MU}; }}
.hnrate .mr.ym {{ margin-top:6px; font-size:.72rem; color:{_MU}; }} .hnrate .mr.ym b {{ color:#CCC7D3; }}
/* ---------- analysts: the rating card as tall as the tiles + the targets card next to it ---------- */
.hnang {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.25fr); gap:16px; align-items:stretch; }}
@media (max-width: 900px) {{ .hnang {{ grid-template-columns:1fr; }} }}
.hnang .hnal {{ display:flex; min-width:0; }}
.hnang .hnal .hnrate {{ flex:1; display:flex; flex-direction:column; }}
.hnang .hnal .hnrate .g {{ margin-top:auto; max-width:420px; width:100%; }} .hnang .hnal .hnrate .mr {{ margin-bottom:auto; }}
.hnang .hnar {{ display:flex; flex-direction:column; gap:12px; min-width:0; }}
.hnang .hnar .hntgt {{ margin-top:0; flex:1; }}
.hnang .kts {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }}
.hnkt {{ position:relative; overflow:hidden; border-radius:14px; padding:12px 14px; border:1px solid {_BD};
  background:{T.TOP}, linear-gradient(160deg,rgba(59,139,235,.16),rgba(123,69,240,.08) 55%,{T.CARD});
  transition:border-color .18s ease, box-shadow .18s ease, transform .18s ease; }}
.hnkt::after {{ content:""; position:absolute; inset:auto 0 0 0; height:2px; background:linear-gradient(90deg,{_A},{_V},{_C}); opacity:0;
  transition:opacity .18s ease; }}
.hnkt:hover {{ border-color:rgba(121,184,244,.45); box-shadow:0 12px 28px rgba(59,139,235,.16); transform:translateY(-2px); }}
.hnkt:hover::after {{ opacity:.9; }}
.hnkt .l {{ display:flex; align-items:center; gap:7px; color:#CCC7D3; font-size:.7rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; }}
.hnkt .l .ms {{ color:#79B8F4; font-size:1.02rem; }}
.hnkt .v {{ color:#fff; font-size:1.25rem; font-weight:600; margin-top:6px; direction:ltr; unicode-bidi:isolate; white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis; }}
.hnkt .s {{ color:{_MU}; font-size:.76rem; margin-top:2px; }}
.hnkt.ok .s {{ color:#4ADE80; font-weight:600; }} .hnkt.bad .s {{ color:#F87171; font-weight:600; }}
.hnkt.ok .v {{ color:#E8FFF0; }}
.hnkts4 {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-bottom:12px; }}
@media (max-width: 900px) {{ .hnkts4 {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
</style>"""
RTL_CSS = """<style>
.hnhero .eb, .hnreg .tl .l, .hnc .lv span, .hnplan .p .l { letter-spacing:0; }
.hndh::before { left:auto; right:0; }
.hnparts .r { grid-template-columns:120px 1fr 44px; }
.hnbt, .hnkt .l { letter-spacing:0; }
</style>"""


# ---------------------------------------------------------------- what to scan
def universes():
    """key -> (label, symbols). Sectors and industries narrow any of them (the hunt bar)."""
    from sp500 import SP500
    u = {"top": (L(f"Top {len(U.US_UNIVERSE)} US stocks", f"أكبر {len(U.US_UNIVERSE)} سهم أمريكي"), list(U.US_UNIVERSE)),
         "sp500": (L("S&P 500 (all, slower)", "إس آند بي 500 (كامل، أبطأ)"), sorted(set(SP500) | set(U.STOCKS)))}
    for tk, (en, ar_, _, _) in X.THEMES.items():
        u[f"t:{tk}"] = (f"{L('Theme', 'ثيم')} · {L(en, ar_)}", X.theme_tickers(tk))
    u["wl"] = (L("My watchlist", "قائمة المتابعة"), list(ss.get("watchlist", [])))
    u["custom"] = (L("My own symbols", "رموز أكتبها"), None)
    return u


def sector_of(s):
    return PB.sector_of(s) or (U.sector_of(s) if U.known(s) else "")


def industry_of(s):
    from sp500 import SP500
    if s in SP500 and SP500[s][2]:
        return SP500[s][2]
    return U.industry_of(s) if U.known(s) else ""


def industry_label(ind):
    from sp500 import GICS_AR
    return gics_name(ind) if ind in GICS_AR else industry_name(ind)


def _base(unis):
    k = ss.get("hn_uni", "top")
    if k not in unis:
        k = "top"
    if unis[k][1] is None:
        raw = str(ss.get("hn_custom") or "").replace("،", ",").replace(" ", ",")
        return k, list(dict.fromkeys(s.strip().upper() for s in raw.split(",") if s.strip()))[:200]
    return k, list(unis[k][1])


def _narrow(base):
    """The base list narrowed to the chosen sector and industry; also the options of the two drop-downs."""
    secs = sorted({sector_of(s) for s in base} - {""})
    if ss.get("hn_sec", "all") not in ["all"] + secs:
        ss["hn_sec"] = "all"
    pool = [s for s in base if ss["hn_sec"] == "all" or sector_of(s) == ss["hn_sec"]]
    inds = sorted({industry_of(s) for s in pool} - {""})
    if ss.get("hn_ind", "all") not in ["all"] + inds:
        ss["hn_ind"] = "all"
    pool = [s for s in pool if ss["hn_ind"] == "all" or industry_of(s) == ss["hn_ind"]]
    return tuple(pool), secs, inds


def _names_sectors(symbols):
    from sp500 import SP500
    names, secs = {}, {}
    for s in symbols:
        names[s] = U.STOCKS[s][0] if s in U.STOCKS else (SP500[s][0] if s in SP500 else U.name_of(s))
        secs[s] = sector_of(s)
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
            f'<circle cx="24" cy="24" r="{r}" fill="none" stroke="rgba(157,151,165,.18)" stroke-width="4.5"/>'
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
def _radar(res, rtl=False):
    """The radar; in Arabic it sits at the left edge (the mirror of English, where it sits at the right edge)."""
    cx, cy = (160 if rtl else 360), 125
    side = -1 if rtl else 1
    s = ['<svg viewBox="0 0 520 250" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" style="direction:ltr">'
         '<defs><radialGradient id="hnrg" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#2DB6EB" stop-opacity=".16"/>'
         '<stop offset="1" stop-color="#2DB6EB" stop-opacity="0"/></radialGradient>'
         '<linearGradient id="hnsw" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#2DB6EB" stop-opacity="0"/>'
         '<stop offset="1" stop-color="#2DB6EB" stop-opacity=".42"/></linearGradient>'
         '<filter id="hngl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/>'
         '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
         f'<circle cx="{cx}" cy="{cy}" r="112" fill="url(#hnrg)"/>']
    for r in (28, 56, 84, 112):
        s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#2DB6EB" stroke-opacity="{.10 + r / 1200:.2f}" stroke-width="1"/>')
    s.append(f'<path d="M{cx - 118} {cy} H{cx + 118} M{cx} {cy - 118} V{cy + 118}" stroke="#2DB6EB" stroke-opacity=".12" stroke-width="1"/>')
    s.append(f'<g class="sweep"><path d="M{cx} {cy} L{cx + 112} {cy} A112 112 0 0 0 {cx + 112 * np.cos(np.radians(-38)):.1f} '
             f'{cy + 112 * np.sin(np.radians(-38)):.1f} Z" fill="url(#hnsw)"/>'
             f'<line x1="{cx}" y1="{cy}" x2="{cx + 112}" y2="{cy}" stroke="#2DB6EB" stroke-width="2" stroke-opacity=".8" filter="url(#hngl)"/></g>')
    top = res.head(7) if res is not None and len(res) else pd.DataFrame()
    for i, r in enumerate(top.itertuples()):
        ang = np.radians(-160 + i * 53)
        rad = 32 + i * 12
        x, y = cx + side * rad * np.cos(ang), cy + rad * np.sin(ang)
        col = GRADE_COLOR.get(r.Grade, _C)
        s.append(f'<circle class="blip" cx="{x:.0f}" cy="{y:.0f}" r="5" fill="none" stroke="{col}" stroke-width="1.5" style="animation-delay:-{i * .35:.2f}s"/>'
                 f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4" fill="{col}" filter="url(#hngl)"/>'
                 f'<text x="{x + side * 8:.0f}" y="{y - 6:.0f}" text-anchor="{"end" if rtl else "start"}" font-size="11" font-weight="800" '
                 f'fill="#fff" font-family="{T.FONT}">{T.esc(r.Symbol)}</text>'
                 f'<text x="{x + side * 8:.0f}" y="{y + 7:.0f}" text-anchor="{"end" if rtl else "start"}" font-size="9.5" fill="{col}" '
                 f'font-family="{T.FONT}">{r.Grade} · {r.Score:.0f}</text>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="#2DB6EB" filter="url(#hngl)"/>')
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
    return (f'<div class="hnhero{" rtl" if is_ar() else ""}"><div class="grid"></div><div class="art">{_radar(res, is_ar())}</div>'
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


def _look():
    sym = str(ss.get("hn_look_in") or "").strip().upper()
    ss["hn_look"] = sym or None
    if sym:
        ss["hn_sel"] = sym


def hunt_bar(unis, secs, inds, n):
    with st.container(key="hnbar"):
        c = st.columns([1.9, 1.5, 1.9, 1, 0.8], vertical_alignment="bottom")
        c[0].selectbox(L("What to scan", "وش أفحص"), list(unis), key="hn_uni", format_func=lambda k: unis[k][0])
        c[1].selectbox(L("Sector", "القطاع"), ["all"] + secs, key="hn_sec",
                       format_func=lambda s: L("All sectors", "كل القطاعات") if s == "all" else sector_name(s))
        c[2].selectbox(L("Industry", "الصناعة"), ["all"] + inds, key="hn_ind",
                       format_func=lambda s: L("All industries", "كل الصناعات") if s == "all" else industry_label(s))
        c[3].button(L("Hunt", "ابدأ الصيد"), icon=":material/radar:", key="hn_go", on_click=_go, width="stretch")
        c[4].button(L("Refresh", "تحديث"), icon=":material/refresh:", key="hn_refresh", on_click=_refresh,
                    help=L("Fresh prices now", "أسعار جديدة الحين"), width="stretch")
        if ss.get("hn_uni") == "custom":
            st.text_input(L("Symbols (comma separated)", "الرموز (مفصولة بفاصلة)"), key="hn_custom", placeholder="AAPL, MSFT, NVDA, 2222.SR")
        a, b, cap = st.columns([1.9, 1, 4.2], vertical_alignment="bottom")
        a.text_input(L("Analyze one symbol", "حلّل سهم واحد"), key="hn_look_in", placeholder="NVDA", on_change=_look)
        b.button(L("Analyze", "حلّل"), icon=":material/manage_search:", key="hn_look_go", on_click=_look, width="stretch")
        note = L(f"{n:,} stocks in this hunt.", f"{n:,} سهم في هذا الصيد.")
        if ss.get("hn_uni") == "sp500" and n > 250:
            note += L(" The whole S&P 500 takes up to a minute the first time, then it is kept for 15 minutes.",
                      " إس آند بي 500 كامل ياخذ لين دقيقة أول مرة، وبعدها ينحفظ 15 دقيقة.")
        cap.caption(note)


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
    for k, v in {"hn_uni": "top", "hn_sec": "all", "hn_ind": "all", "hn_acct": 100_000, "hn_risk": 1.0, "hn_grade": "B", "hn_fresh": False,
                 "hn_noearn": False, "hn_minpx": 5.0, "hn_minvol": 20.0, "hn_custom": "AAPL, MSFT, NVDA, AMD, TSLA, META"}.items():
        ss.setdefault(k, v)


def filters(res):
    counts = res["Setups"].str.split(",").explode().value_counts()
    keys = [k for k in H.ORDER if counts.get(k, 0)]
    if "hn_setups" in ss:
        ss["hn_setups"] = [k for k in ss["hn_setups"] if k in keys]
    with st.container(key="hnfilt"):
        ui.html(f'<div class="hnfh">{T.icon("filter_alt")}<b>{L("Filters", "التصفية")}</b>'
                f'<span>{L("Pick setups to see only them; with none picked, every buying setup shows.", "اختر فرص عشان تشوفها بس؛ وبدون اختيار تظهر كل فرص الشراء.")}</span></div>')
        st.pills(L("Setups", "الفرص"), keys, selection_mode="multi", key="hn_setups", label_visibility="collapsed",
                 format_func=lambda k: f"{short_name(k)} · {int(counts.get(k, 0))}")
        c = st.columns([1.55, 1, 1.15, 1, 1], vertical_alignment="bottom")
        c[0].segmented_control(L("Grade at least", "الدرجة على الأقل"), list(MIN_GRADE), key="hn_grade",
                               format_func=lambda g: L("All", "الكل") if g == "all" else g)
        c[1].toggle(L("New today", "الجديدة اليوم"), key="hn_fresh")
        c[2].toggle(L("No earnings ≤ 5 days", "بدون أرباح ≤ 5 أيام"), key="hn_noearn")
        c[3].number_input(L("Price from ($)", "السعر من ($)"), 0.0, 10000.0, step=1.0, key="hn_minpx")
        c[4].number_input(L("Traded/day from ($M)", "التداول اليومي من (مليون $)"), 0.0, 10000.0, step=5.0, key="hn_minvol")


def apply(res):
    v = res.copy()
    picks = ss.get("hn_setups") or []
    if picks:
        v = v[v["Setups"].apply(lambda s: any(k in str(s).split(",") for k in picks))]
    else:
        v = v[v["Side"] > 0]
    if not (picks and "breakdown" in picks):
        v = v[v["Score"] >= MIN_GRADE.get(ss.get("hn_grade") or "all", 0)]
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
    ss["hn_look"] = None


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


def tech_checks(r, det, d, spy=None):
    """One technical checklist: the Hunter's own reasons merged with the checks of the old Catalyst Pro (no repeats).
    [{'Pass', 'Check', 'Check_ar', 'Detail', 'warn'}]"""
    out = []

    def add(ok, en, ar_, detail="", warn=False):
        out.append({"Pass": bool(ok), "Check": en, "Check_ar": ar_, "Detail": detail, "warn": warn})

    p = float(r["Price"])
    last = d.iloc[-1] if d is not None and len(d) else None
    s20, s50, s200 = det.get("sma20", np.nan), det.get("sma50", np.nan), det.get("sma200", np.nan)
    add(np.isfinite(s200) and p > s200, "Primary trend up (above the 200-day average)", "الاتجاه الرئيسي صاعد (فوق متوسط 200 يوم)",
        f"{p:,.2f} vs {s200:,.2f}" if np.isfinite(s200) else "n/a")
    add(p > s50, "Above the 50-day average", "فوق متوسط 50 يوم", f"{p:,.2f} vs {s50:,.2f}")
    add(np.isfinite(s200) and s20 > s50 > s200, "Bullish average stack (20 > 50 > 200)", "ترتيب متوسطات إيجابي (20 > 50 > 200)",
        f"SMA20 {s20:,.2f} · SMA50 {s50:,.2f}")
    if last is not None:
        rsi = float(last["RSI"])
        add(50 <= rsi <= 70, "Healthy momentum (RSI 50-70)", "زخم صحي (RSI بين 50 و70)", f"RSI {rsi:.0f}")
        add(last["MACD"] > last["MACD_signal"], "MACD above its signal line", "الماكد فوق خط الإشارة", f"hist {last['MACD_hist']:.3f}")
        adx = last["ADX"]
        add(pd.notna(adx) and adx > 20 and last["DI_plus"] > last["DI_minus"], "Trend strength (ADX > 20, +DI > -DI)",
            "قوة الاتجاه (ADX > 20 و+DI فوق -DI)", f"ADX {adx:.0f}" if pd.notna(adx) else "n/a")
    rs = int(r["RS"])
    rs3 = ""
    if spy is not None and d is not None and len(spy) > 64 and len(d) > 64:
        x = (d["Close"].iloc[-1] / d["Close"].iloc[-64] - 1) - (spy["Close"].iloc[-1] / spy["Close"].iloc[-64] - 1)
        rs3 = f" · vs S&P 500 (3M) {x * 100:+.1f}%"
    add(rs >= 70, f"Relative strength: RS {rs} (stronger than {rs}% of the list)", f"القوة النسبية: RS {rs} (أقوى من {rs}% من القائمة)", rs3.strip(" ·"))
    ud = det.get("ud", 1.0)
    obv = ""
    if d is not None and "OBV" in d and len(d) > 21:
        obv = " · OBV " + ("↑" if d["OBV"].iloc[-1] > d["OBV"].iloc[-21] else "↓")
    add(ud >= 1.1, "Accumulation (volume on up days > down days, 50 days)", "تجميع (حجم أيام الصعود أكبر من أيام النزول، 50 يوم)",
        f"{ud:.2f}×{obv}")
    rv = r.get("RVOL")
    add(pd.notna(rv) and rv >= 1.5, "Volume confirmation today (≥ 1.5× average)", "تأكيد بالحجم اليوم (≥ 1.5 ضعف المتوسط)",
        f"{rv:.1f}×" if pd.notna(rv) else "n/a")
    dh = float(r["From high %"])
    add(dh >= -5, "Within 5% of the 52-week high", "ضمن 5% من القمة السنوية", f"{dh:+.1f}% · ${det.get('hi52', np.nan):,.2f}")
    bw = det.get("bw_pct", np.nan)
    add(np.isfinite(bw) and bw <= 0.2, "Volatility squeeze (coiling)", "انضغاط التذبذب (تجميع قبل حركة)",
        L("bands narrow", "النطاق ضيق") if np.isfinite(bw) and bw <= 0.2 else L("normal", "طبيعي"))
    if np.isfinite(r["R:R"]):
        add(r["R:R"] >= 2, "Reward to risk at least 2 to 1", "العائد مقابل المخاطرة 2 إلى 1 على الأقل", f"{r['R:R']:.1f} : 1")
    if det.get("ext", 0) > 3:
        add(False, "Not stretched above the 20-day average", "غير ممتد فوق متوسط 20 يوم",
            L(f"{det['ext']:.1f} ATR above: better on a pullback", f"{det['ext']:.1f} ATR فوق: الأفضل تنتظر تراجع"), warn=True)
    return out


def _checklist2(items):
    return "".join(f'<div class="check">{T.ico("check", "pos") if c_["Pass"] else T.ico("priority_high" if c_.get("warn") else "close", "gold" if c_.get("warn") else "neg")}'
                   f'<div><b>{T.esc(L(c_["Check"], c_["Check_ar"]))}</b>'
                   + (f' <span class="muted">· {T.esc(c_["Detail"])}</span>' if c_["Detail"] else "") + '</div></div>' for c_ in items)


@st.cache_data(ttl=900, show_spinner=False, max_entries=48)
def lookup(sym, build=None):
    """One symbol on its own (the 'Analyze one symbol' box, or a stock the scan didn't include): (row dict, detail) or (None, None)."""
    df = data.history(sym, "2y")
    spy = data.history("SPY", "2y")
    if df is None or df.empty:
        return None, None
    today = _today_ny()
    names, secs = _names_sectors([sym])
    res, det = H.hunt({sym: df}, spy if not spy.empty else None, _earnings_map(today), today, names, secs)
    if res.empty:
        return None, None
    return res.iloc[0].to_dict(), det.get(sym, {})


@st.cache_data(ttl=900, show_spinner=False, max_entries=48)
def catalysts(sym, build=None):
    """The fundamental checks, the events and the news of one stock (the old Catalyst Pro)."""
    inf = data.info(sym)
    f = data.fundamentals(sym)
    nws = data.news(sym, 20)
    d, _ = _history5(sym, build)
    fund = engine.fundamental_checks(inf, f["earnings_hist"])
    rr = f["ratings"]
    if isinstance(rr, pd.DataFrame) and not rr.empty:
        rr = rr[rr.index >= pd.Timestamp.now() - pd.Timedelta(days=30)]
    events = engine.event_checks(f["earnings_date"], rr, nws, inf, d) if d is not None else []
    an = {k: inf.get(k) for k in ("recommendationKey", "recommendationMean", "numberOfAnalystOpinions", "targetMeanPrice", "targetHighPrice",
                                  "targetLowPrice", "targetMedianPrice", "currentPrice", "regularMarketPrice")}
    return {"fund": fund, "events": events, "news": nws, "earn": f["earnings_date"], "short": inf.get("shortName") or "", "an": an,
            "targets": f.get("targets") or {}, "rec": f.get("rec_summary"), "ratings": f.get("ratings"), "insiders": f.get("insiders")}


def _checklist(items):
    return "".join(f'<div class="check">{T.ico("check", "pos") if c_["Pass"] else T.ico("close", "neg")}'
                   f'<div><b>{T.esc(L(c_["Check"], c_["Check_ar"]))}</b> <span class="muted">· {T.esc(c_["Detail"])}</span></div></div>'
                   for c_ in items)


def _levels(d, price):
    lv = ta.swing_levels(d) if d is not None else []
    sup = max([x for x in lv if x < price], default=float(d["Low"].tail(20).min()) if d is not None else np.nan)
    res_ = min([x for x in lv if x > price], default=float(d["High"].tail(252).max()) if d is not None else np.nan)
    return sup, res_


def plan_section(r, det, d):
    """The trade plan: the setup's entry, stop and target with the position size for your account and risk, the key levels,
    when to enter and how to exit. Without a buying setup: the plain plan (wait / avoid) from the price structure."""
    sym, k = r["Symbol"], r["Setup"]
    ui.sec("flag", "Trade plan", "خطة التداول")
    acct, risk = float(ss.get("hn_acct") or 100_000), float(ss.get("hn_risk") or 1.0)     # sized for $100,000 at 1% risk
    price = float(r["Price"])
    atr = float(r["ATR %"]) * price / 100
    sup, res_ = _levels(d, price)
    if np.isfinite(r["Entry"]) and int(r["Side"] or 0) > 0:
        entry, stop, tgt = float(r["Entry"]), float(r["Stop"]), float(r["Target"])
        watch = r["Status"] == "watch"
        max_bars = H.SETUPS[k][5] or (PBK.defaults(H.PLAYBOOK_OF[k])["max_bars"] if k in H.PLAYBOOK_OF else None)
        trig = (L(f"Buy only after a daily close above ${entry:,.2f}; the order goes in at the next open.",
                  f"اشترِ بس بعد إغلاق يومي فوق ${entry:,.2f}، والأمر يتنفذ عند الافتتاح التالي.") if watch else
                L(f"Buy at the next open near ${entry:,.2f}. Skip it if it opens under ${stop:,.2f} (the stop) or over ${tgt:,.2f} (the target).",
                  f"اشترِ عند الافتتاح القادم قرب ${entry:,.2f}. وتجاهلها إذا افتتح تحت ${stop:,.2f} (الوقف) أو فوق ${tgt:,.2f} (الهدف)."))
        exits = [L(f"Stop loss: out if the price trades at ${stop:,.2f} or lower ({_pct(entry, stop):+.1f}%).",
                   f"وقف الخسارة: اخرج إذا وصل السعر ${stop:,.2f} أو أقل ({_pct(entry, stop):+.1f}%)."),
                 L(f"Target: ${tgt:,.2f} ({_pct(entry, tgt):+.1f}%). Nearest resistance: ${res_:,.2f}.",
                   f"الهدف: ${tgt:,.2f} ({_pct(entry, tgt):+.1f}%). أقرب مقاومة: ${res_:,.2f}."),
                 L(f"After +1R (${entry + (entry - stop):,.2f}) move the stop to the entry price.",
                   f"بعد ربح 1R (${entry + (entry - stop):,.2f}) ارفع الوقف لسعر الدخول.")]
        if max_bars:
            exits.append(L(f"Time limit: out after {max_bars} sessions if the target isn't reached.",
                           f"مدة قصوى: اخرج بعد {max_bars} جلسة إذا ما وصل الهدف."))
        n = H.size(entry, stop, acct, risk)
        tiles = [("en", L("Buy above", "شراء فوق") if watch else L("Entry", "الدخول"), _money_px(entry),
                  L("on a close above it", "بإغلاق فوقه") if watch else L("next open, near this price", "الافتتاح القادم، قرب هذا السعر")),
                 ("sl", L("Stop loss", "وقف الخسارة"), _money_px(stop), f"{_pct(entry, stop):+.1f}% · {abs(entry - stop) / max(atr, 1e-9):.1f} ATR"),
                 ("tp", L("Target", "الهدف"), _money_px(tgt), f"{_pct(entry, tgt):+.1f}%"),
                 ("", "R:R", f"{r['R:R']:.1f} : 1" if np.isfinite(r["R:R"]) else "—", L("reward for each $1 of risk", "العائد لكل 1$ مخاطرة")),
                 ("", L("Position size", "حجم الصفقة"), f"{n:,} {L('sh', 'سهم')}", f"{_money_px(n * entry)} · {n * entry / acct * 100:.0f}% {L('of the account', 'من المحفظة')}"),
                 ("", L("Max loss", "أقصى خسارة"), T.money(n * abs(entry - stop)), f"{risk:g}% {L('of', 'من')} {T.money(acct)}")]
        if max_bars:
            tiles.append(("", L("Time limit", "المدة القصوى"), L(f"{max_bars} sessions", f"{max_bars} جلسة"), L("then out at the close", "بعدها خروج عند الإغلاق")))
    else:
        p = engine.trade_plan(d, acct, risk) if d is not None else None
        if p is None:
            return
        st.info(L(f"No buying setup on {sym} right now: {p['bias']} ({p['setup']}).", f"ما فيه فرصة شراء على {sym} الحين: {p['bias_ar']} ({p['setup_ar']})."),
                icon=":material/do_not_disturb_on:")
        trig = L(p["trigger"], p["trigger_ar"])
        exits = [L(e, a) for e, a in p["exits"][:3]]
        tiles = [("en", L("Watch level", "مستوى المراقبة"), _money_px(p["entry"]), L("a close above it", "إغلاق فوقه")),
                 ("sl", L("Stop if taken", "الوقف لو دخلت"), _money_px(p["stop"]), f"{_pct(p['entry'], p['stop']):+.1f}%"),
                 ("tp", L("Target 1 (2R)", "الهدف الأول (2R)"), _money_px(p["t1"]), f"{_pct(p['entry'], p['t1']):+.1f}%")]
    tiles += [("", "ATR (14)", _money_px(atr), f"{r['ATR %']:.1f}% {L('a day', 'يومياً')}"),
              ("", L("Support", "الدعم"), _money_px(sup), f"{_pct(price, sup):+.1f}%"),
              ("", L("Resistance", "المقاومة"), _money_px(res_), f"{_pct(price, res_):+.1f}%")]
    ui.html('<div class="hnplan">' + "".join(f'<div class="p {c_}"><div class="l">{T.esc(l_)}</div><div class="v">{v_}</div>'
                                             f'<div class="s">{T.esc(s_)}</div></div>' for c_, l_, v_, s_ in tiles) + "</div>")
    x, y = st.columns(2, gap="medium")
    with x:
        items = [("flag", f"<b>{L('Trigger', 'شرط الدخول')}:</b> {T.esc(trig)}"),
                 ("timer", L("<b>Best time:</b> skip the first 30 minutes after the 9:30 ET open (4:30 pm Riyadh); confirm on the daily close "
                             "or after 10:00 ET with above-average volume.",
                             "<b>أفضل وقت:</b> تجنّب أول 30 دقيقة بعد افتتاح 9:30 بتوقيت نيويورك (4:30 عصراً بتوقيت الرياض)، وأكّد على الإغلاق "
                             "اليومي أو بعد 10:00 مع حجم أعلى من المتوسط."))]
        if pd.notna(r.get("Earnings")) and 0 <= r["Earnings"] <= 10:
            items.append(("warning", L(f"<b>Earnings in {int(r['Earnings'])} trading days:</b> half size, or wait until after the report.",
                                       f"<b>أرباح بعد {int(r['Earnings'])} أيام تداول:</b> نص الحجم، أو انتظر بعد الإعلان.")))
        if _session_live():
            items.append(("schedule", L("<b>Market open:</b> today's candle is still moving; a signal of today is confirmed only at the close.",
                                        "<b>السوق مفتوح:</b> شمعة اليوم لسا تتحرك، فإشارة اليوم تتأكد بس عند الإغلاق.")))
        ui.html(f'<div class="hnbox"><div class="hnbt">{T.icon("schedule")}{L("When to enter", "متى تدخل")}</div>'
                + "".join(f'<div class="check">{T.ico(ic, "gold")}<div>{t}</div></div>' for ic, t in items) + "</div>")
    with y:
        ui.html(f'<div class="hnbox"><div class="hnbt">{T.icon("logout")}{L("How to exit", "كيف تخرج")}</div>'
                + "".join(f'<div class="check">{T.ico("logout", "acc")}<div>{T.esc(e)}</div></div>' for e in exits) + "</div>")


REC = {"strong_buy": ("Strong buy", "شراء قوي", "up"), "buy": ("Buy", "شراء", "up"), "hold": ("Hold", "احتفاظ", "gold"),
       "underperform": ("Underperform", "أداء أقل من السوق", "down"), "sell": ("Sell", "بيع", "down"), "strong_sell": ("Strong sell", "بيع قوي", "down")}
ACTION = {"up": ("Upgrade", "ترقية", "up"), "down": ("Downgrade", "تخفيض", "down"), "init": ("Initiated", "بداية تغطية", "acc"),
          "main": ("Maintained", "تثبيت", "neu"), "reit": ("Reiterated", "تأكيد", "neu")}


def score_chip(text, good):
    """A score in a box title: light green when good, light red when not (None = neutral)."""
    return f'<span class="sc {"" if good is None else ("ok" if good else "bad")}">{text}</span>'


def _event_score(events):
    es = 50.0
    for ev in events:
        es += {"pos": 12, "hot": 8, "neg": -15, "warn": -5}.get(ev["Impact"], 0)
    return max(0.0, min(100.0, es))


def fundamentals_box(sym):
    cat = catalysts(sym, H.BUILD)
    fund = cat["fund"]
    fs = sum(x["Pass"] for x in fund) / len(fund) * 100 if fund else None
    sc = "" if fs is None else score_chip(f'{fs:.0f}/100 · {sum(x["Pass"] for x in fund)}/{len(fund)}', fs >= 50)
    ui.html(f'<div class="hnbox"><div class="hnbt">{T.icon("request_quote")}<span>{L("Fundamental analysis", "التحليل الأساسي")}</span>{sc}</div>'
            + (_checklist(fund) if fund else f'<div class="muted" style="font-size:.84rem;padding:6px 0 10px">{L("No fundamental data (ETF, index or crypto).", "لا توجد بيانات مالية (صندوق أو مؤشر أو عملة رقمية).")}</div>')
            + "</div>")


def events_box(sym):
    cat = catalysts(sym, H.BUILD)
    events = cat["events"]
    es = _event_score(events)
    rows = []
    for e in events:
        en, ar_, kind, ic = engine.IMPACT[e["Impact"]]
        rows.append(f'<div class="check">{T.badge(L(en, ar_), kind, ic)}<div><b>{T.esc(L(e["Event"], e["Event_ar"]))}</b> '
                    f'<span class="muted">· {T.esc(L(e["Detail"], e["Detail_ar"]))}</span></div></div>')
    ui.html(f'<div class="hnbox"><div class="hnbt">{T.icon("event")}<span>{L("Events", "الأحداث")}</span>{score_chip(f"{es:.0f}/100", es >= 50)}</div>'
            + ("".join(rows) or f'<div class="muted" style="font-size:.84rem;padding:6px 0 10px">{L("No special events right now.", "لا توجد أحداث خاصة حالياً.")}</div>')
            + "</div>")


def target_card(price, tg):
    """12-month price targets as a modern card: a low-to-high track (red to gold to green), the low, median, mean and high
    targets and today's price, labels kept apart, and the upside of each target in chips below."""
    pts = [(k, float(tg[k])) for k in ("low", "median", "mean", "high") if tg.get(k)]
    if len(pts) < 2 or not price:
        return ""
    names = {"low": ("Low", "الأدنى", _D), "median": ("Median", "الوسيط", _G), "mean": ("Mean", "المتوسط", _A), "high": ("High", "الأعلى", _U)}
    lo = min([v for _, v in pts] + [price])
    hi = max([v for _, v in pts] + [price])
    span = (hi - lo) or 1.0
    W, pad = 640, 34
    x = lambda v: pad + (v - lo) / span * (W - 2 * pad)
    y0 = 78
    svg = [f'<svg viewBox="0 0 {W} 150" xmlns="http://www.w3.org/2000/svg" style="direction:ltr">'
           f'<defs><linearGradient id="hntg" x1="0" x2="1"><stop offset="0" stop-color="{_D}"/><stop offset=".5" stop-color="{_G}"/>'
           f'<stop offset="1" stop-color="{_U}"/></linearGradient>'
           f'<filter id="hntgl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/>'
           f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
           f'<rect x="{pad}" y="{y0 - 4}" width="{W - 2 * pad}" height="8" rx="4" fill="rgba(157,151,165,.18)"/>']
    tl, th = x(min(v for _, v in pts)), x(max(v for _, v in pts))
    svg.append(f'<rect x="{tl:.1f}" y="{y0 - 4}" width="{max(th - tl, 2):.1f}" height="8" rx="4" fill="url(#hntg)" opacity=".85"/>')
    # target labels above the track, moved up a row when two are too close
    placed = []
    for k, v in sorted(pts, key=lambda t: t[1]):
        xx = x(v)
        row = 0
        while any(abs(xx - px) < 78 and r_ == row for px, r_ in placed):
            row += 1
        placed.append((xx, row))
        en, ar_, col = names[k]
        ty = y0 - 18 - row * 30
        anchor = "start" if xx < 60 else ("end" if xx > W - 60 else "middle")
        svg.append(f'<line x1="{xx:.1f}" y1="{y0 - 7}" x2="{xx:.1f}" y2="{ty + 6}" stroke="{col}" stroke-opacity=".45" stroke-width="1"/>'
                   f'<circle cx="{xx:.1f}" cy="{y0}" r="8" fill="{col}" stroke="#0E0918" stroke-width="2.5" filter="url(#hntgl)"/>'
                   f'<text x="{xx:.1f}" y="{ty - 8}" text-anchor="{anchor}" font-size="11" fill="#A09AAB" font-family="{T.FONT}">{T.esc(L(en, ar_))}</text>'
                   f'<text x="{xx:.1f}" y="{ty + 4}" text-anchor="{anchor}" font-size="13" font-weight="800" fill="#fff" font-family="{T.FONT}">${v:,.0f}</text>')
    xp = x(price)
    anchor = "start" if xp < 60 else ("end" if xp > W - 60 else "middle")
    svg.append(f'<path d="M{xp:.1f} {y0 - 10} L{xp + 10:.1f} {y0} L{xp:.1f} {y0 + 10} L{xp - 10:.1f} {y0} Z" fill="#fff" stroke="#0E0918" stroke-width="2"/>'
               f'<text x="{xp:.1f}" y="{y0 + 30}" text-anchor="{anchor}" font-size="11" fill="#A09AAB" font-family="{T.FONT}">{L("Now", "الحالي")}</text>'
               f'<text x="{xp:.1f}" y="{y0 + 45}" text-anchor="{anchor}" font-size="13" font-weight="800" fill="#fff" font-family="{T.FONT}">${price:,.2f}</text>')
    top = min((y0 - 18 - r_ * 30 - 22 for _, r_ in placed), default=0)
    svg[0] = svg[0].replace('viewBox="0 0 {} 150"'.format(W), f'viewBox="0 {min(0, top - 4):.0f} {W} {150 - min(0, top - 4):.0f}"')
    chips = "".join(f'<span class="c"><i style="background:{names[k][2]}"></i>{T.esc(L(*names[k][:2]))} <b>${v:,.2f}</b>'
                    f'<em class="{"up" if v >= price else "dn"}">{_pct(price, v):+.1f}%</em></span>' for k, v in pts)
    return (f'<div class="hntgt"><div class="hnbt">{T.icon("flag")}<span>{L("12-month price targets", "السعر المستهدف خلال 12 شهر")}</span></div>'
            f'<div class="sv">{"".join(svg)}</svg></div><div class="cs">{chips}</div></div>')


# the rating scale of Yahoo Finance (1 = strong buy .. 5 = sell), from the left of the gauge (sell) to its right (strong buy)
RATING = [("strongSell", "Sell", "بيع", "#A62D4A"), ("sell", "Underperform", "أداء أقل", "#F06E6E"), ("hold", "Hold", "احتفاظ", "#E8A93B"),
          ("buy", "Buy", "شراء", "#6CC46A"), ("strongBuy", "Strong Buy", "شراء قوي", "#5DD3A8")]


def _num0(v):
    try:
        v = float(v)
        return int(v) if np.isfinite(v) else 0
    except (TypeError, ValueError):
        return 0


def _rating_counts(rec):
    """The latest month of the recommendations summary as {key: count} (None when there is none)."""
    if not isinstance(rec, pd.DataFrame) or rec.empty:
        return None
    row = rec[rec["period"].astype(str) == "0m"] if "period" in rec else rec.head(1)
    row = (row if len(row) else rec.head(1)).iloc[0]
    out = {k: _num0(row.get(k)) for k, *_ in RATING}
    return out if sum(out.values()) else None


def _bucket(grade):
    """A broker's grade (Overweight, Market Perform, ...) on the five-step scale; None when unknown."""
    g = str(grade or "").strip().lower()
    if not g or g == "nan":
        return None
    if any(w in g for w in ("strong buy", "top pick", "conviction buy")):
        return "strongBuy"
    if any(w in g for w in ("strong sell",)):
        return "strongSell"
    if any(w in g for w in ("underperform", "underweight", "reduce", "negative", "sector underperform", "market underperform")):
        return "sell"
    if g == "sell" or g.endswith(" sell"):
        return "strongSell"
    if any(w in g for w in ("buy", "outperform", "overweight", "positive", "accumulate", "add", "long-term buy")):
        return "buy"
    if any(w in g for w in ("hold", "neutral", "equal", "market perform", "sector perform", "in-line", "inline", "peer perform", "perform")):
        return "hold"
    return None


def _counts_from_ratings(rr):
    """Fallback when Yahoo's summary is missing: each firm's latest grade of the last 90 days."""
    if not isinstance(rr, pd.DataFrame) or rr.empty or "ToGrade" not in rr:
        return None
    latest = rr.sort_index(ascending=False)
    latest = latest[~latest["Firm"].duplicated()] if "Firm" in latest else latest
    out = {k: 0 for k, *_ in RATING}
    for g in latest["ToGrade"]:
        b_ = _bucket(g)
        if b_:
            out[b_] += 1
    return out if sum(out.values()) else None


def counts_mean(counts):
    """The average rating (1 = strong buy .. 5 = sell) of the analysts counted (None without any)."""
    tot = sum(counts.values()) if counts else 0
    return sum(w * counts[k] for w, (k, *_) in zip((5, 4, 3, 2, 1), RATING)) / tot if tot else None


def rating_label(counts, mean=None):
    """(en, ar, color) of the consensus: from the mean rating (1-5), or the weighted counts."""
    if mean is None and counts:
        mean = counts_mean(counts)
    if mean is None or not np.isfinite(mean):
        return "—", "—", _MU
    for hi, idx in ((1.5, 4), (2.5, 3), (3.5, 2), (4.5, 1), (9, 0)):
        if mean < hi:
            _, en, ar_, col = RATING[idx]
            return en, ar_, col
    return "—", "—", _MU


def rating_gauge(counts, label, color):
    """A half-ring split by the share of each rating (sell on the left, strong buy on the right), the consensus in the middle."""
    cx, cy, ro, ri = 170, 160, 132, 96
    tot = sum(counts.values()) if counts else 0
    parts, a0, gap = [], 180.0, 1.6
    segs = [(k, en, ar_, col, counts[k] / tot) for k, en, ar_, col in RATING if counts and counts[k]] if tot else []
    for n_, (k, en, ar_, col, frac) in enumerate(segs):
        a1 = a0 - frac * 180
        s_, e_ = a0 - (gap / 2 if n_ else 0), a1 + (gap / 2 if n_ < len(segs) - 1 else 0)
        if s_ - e_ <= 0.2:
            a0 = a1
            continue
        pt = lambda r_, a: (cx + r_ * np.cos(np.radians(a)), cy - r_ * np.sin(np.radians(a)))
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = pt(ro, s_), pt(ro, e_), pt(ri, e_), pt(ri, s_)
        big = 1 if s_ - e_ > 180 else 0
        parts.append(f'<path d="M{x1:.1f} {y1:.1f} A{ro} {ro} 0 {big} 1 {x2:.1f} {y2:.1f} L{x3:.1f} {y3:.1f} A{ri} {ri} 0 {big} 0 {x4:.1f} {y4:.1f} Z" '
                     f'fill="{col}"><title>{T.esc(L(en, ar_))} {frac * 100:.0f}%</title></path>')
        a0 = a1
    if not segs:
        parts.append(f'<path d="M{cx - ro} {cy} A{ro} {ro} 0 0 1 {cx + ro} {cy} L{cx + ri} {cy} A{ri} {ri} 0 0 0 {cx - ri} {cy} Z" fill="rgba(157,151,165,.25)"/>')
    return (f'<svg viewBox="0 0 340 176" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            f'<defs><radialGradient id="hnrg2" cx="50%" cy="100%" r="80%"><stop offset="0" stop-color="#7B45F0" stop-opacity=".22"/>'
            f'<stop offset="1" stop-color="#0E0918" stop-opacity=".0"/></radialGradient></defs>{"".join(parts)}'
            f'<path d="M{cx - ri + 12} {cy} A{ri - 12} {ri - 12} 0 0 1 {cx + ri - 12} {cy} Z" fill="url(#hnrg2)"/>'
            f'<text x="{cx}" y="{cy - 16}" text-anchor="middle" font-size="{min(38, 148 / max(len(label) * 0.6, 1)):.0f}" font-weight="800" '
            f'fill="{color}" font-family="{T.FONT}">{T.esc(label)}</text></svg>')


def analyst_section(sym, price):
    """Analyst rating (a half-ring gauge as on the big finance sites) in a card in the site's colours, the price targets,
    and every rating change of the last 90 days in a table (date, firm, action, from, to, price target)."""
    cat = catalysts(sym, H.BUILD)
    an, tg = cat["an"], cat["targets"] or {}
    counts = _rating_counts(cat["rec"])
    n = int(an.get("numberOfAnalystOpinions") or (sum(counts.values()) if counts else 0))
    mean_t = tg.get("mean") or an.get("targetMeanPrice")
    lo_t, hi_t = tg.get("low") or an.get("targetLowPrice"), tg.get("high") or an.get("targetHighPrice")
    rr = cat["ratings"] if isinstance(cat["ratings"], pd.DataFrame) else pd.DataFrame()
    mean_r = an.get("recommendationMean")
    try:
        mean_r = float(mean_r) if mean_r is not None and np.isfinite(float(mean_r)) else None
    except (TypeError, ValueError):
        mean_r = None
    source = "summary"
    if not counts:
        counts = _counts_from_ratings(rr)
        source = "firms" if counts else "none"
    if not n and counts:
        n = sum(counts.values())
    ui.sec("groups", "Analysts", "المحللون")
    # the verdict, the ring and the average all come from the same analysts: Yahoo's own average (recommendationMean) comes
    # from another panel and can disagree with its counts (1.37 "strong buy" over 73% buy and 18% strong buy, whose average
    # is 1.92 "buy"), so it is only the fallback when there are no counts, and a side note when it says something else
    yahoo_mean = mean_r
    if counts:
        mean_r = counts_mean(counts)
    en, ar_, color = rating_label(counts, mean_r)
    tot = sum(counts.values()) if counts else 0
    legend = "".join(f'<div class="rl"><i style="background:{col}"></i>{T.esc(L(e_, a_))} <b>{counts[k] / tot * 100:.0f}%</b></div>'
                     for k, e_, a_, col in RATING) if tot else ""
    when = _today_ny().strftime("%m/%d/%Y")
    if source == "firms":
        sub = L(f"Based on the latest rating of {n} firms (90 days). Updated on {when} ET.",
                f"بناءً على آخر توصية لـ {n} جهة (90 يوم). آخر تحديث {when} بتوقيت نيويورك.")
    elif tot or n:
        sub = L(f"Based on {tot or n} analysts. Updated on {when} ET.", f"بناءً على {tot or n} محلل. آخر تحديث {when} بتوقيت نيويورك.")
    else:
        sub = L("Yahoo Finance sent no analyst data for this stock right now; it is tried again on the next view.",
                "ياهو فاينانس ما أرسل بيانات المحللين لهذا السهم الحين، وتنطلب من جديد مع الفتح القادم.")
    mean_txt = f'<div class="mr">{L("Average rating", "متوسط التقييم")} <b>{mean_r:.2f}</b> / 5 <span>{L("(1 = strong buy, 5 = sell)", "(1 = شراء قوي، 5 = بيع)")}</span></div>' if mean_r else ""
    if counts and yahoo_mean is not None and rating_label(None, yahoo_mean)[0] != en:
        ye, ya, _ = rating_label(None, yahoo_mean)
        yt = L("Yahoo Finance's own average, from another panel of analysts:", "متوسط ياهو فاينانس نفسه، من مجموعة محللين ثانية:")
        mean_txt += f'<div class="mr ym">{T.esc(yt)} <b>{yahoo_mean:.2f}</b> <span>({T.esc(L(ye, ya))})</span></div>'
    card = (f'<div class="hnrate"><div class="t">{L("Analyst Rating", "تقييم المحللين")}</div><div class="s">{T.esc(sub)}</div>'
            f'<div class="g">{rating_gauge(counts, L(en, ar_), color)}</div><div class="lgs">{legend}</div>{mean_txt}</div>')
    ups = downs = 0
    if len(rr) and "Action" in rr:
        recent = rr[rr.index >= pd.Timestamp.now() - pd.Timedelta(days=30)]
        ups, downs = int((recent["Action"] == "up").sum()), int((recent["Action"] == "down").sum())
    def tile(ic, label, value, sub, good=None):
        cls = "" if good is None else (" ok" if good else " bad")
        return (f'<div class="hnkt{cls}"><div class="l">{T.icon(ic)}<span>{T.esc(label)}</span></div><div class="v">{value}</div>'
                f'<div class="s">{T.esc(sub)}</div></div>')
    tiles = []
    if mean_t and price:
        up = (mean_t / price - 1) * 100
        tiles.append(tile("flag", L("Mean price target", "متوسط السعر المستهدف"), _money_px(mean_t), L(f"{up:+.1f}% from now", f"\u2066{up:+.1f}%\u2069 من السعر الحالي"), up >= 0))
    if lo_t and hi_t:
        tiles.append(tile("straighten", L("Target range", "مدى الأهداف"), f"{_money_px(lo_t)} – {_money_px(hi_t)}",
                          L(f"low {_pct(price, lo_t):+.0f}% · high {_pct(price, hi_t):+.0f}%",
                            f"الأدنى \u2066{_pct(price, lo_t):+.0f}%\u2069 · الأعلى \u2066{_pct(price, hi_t):+.0f}%\u2069")))
    tiles.append(tile("swap_vert", L("Rating changes (30 days)", "تغييرات التقييم (30 يوم)"), f"↑{ups} · ↓{downs}",
                      L("upgrades · downgrades", "ترقيات · تخفيضات"), None if ups == downs else ups > downs))
    tiles.append(tile("groups", L("Analysts", "المحللون"), f"{n}", L("covering the stock", "يغطون السهم")))
    right = f'<div class="kts">{"".join(tiles)}</div>' + (target_card(price, tg) if tg and price else "")
    ui.html(f'<div class="hnang"><div class="hnal">{card}</div><div class="hnar">{right}</div></div>')
    ui.html(f'<div class="hnbt" style="margin-top:6px">{T.icon("table_rows")}{L("Analysts and their ratings (90 days)", "المحللون وتوصياتهم (90 يوم)")}</div>')
    if not len(rr):
        st.caption(L("No rating changes in the last 90 days.", "لا توجد تغييرات تقييم خلال آخر 90 يوم."))
        return
    t = rr.copy()
    act = lambda a: L(*ACTION.get(str(a), (str(a), str(a), ""))[:2])
    out = pd.DataFrame({L("Date", "التاريخ"): pd.to_datetime(t.index).date, L("Firm", "الجهة"): t.get("Firm", ""),
                        L("Action", "الإجراء"): t["Action"].map(act) if "Action" in t else "",
                        L("From", "من"): t.get("FromGrade", "").replace("", "—") if "FromGrade" in t else "—",
                        L("To", "إلى"): t.get("ToGrade", "")})
    if "currentPriceTarget" in t:
        out[L("Price target", "السعر المستهدف")] = pd.to_numeric(t["currentPriceTarget"], errors="coerce").replace(0, np.nan).values
    if "priorPriceTarget" in t:
        out[L("Prior target", "الهدف السابق")] = pd.to_numeric(t["priorPriceTarget"], errors="coerce").replace(0, np.nan).values
    fmt = {c: "${:,.2f}" for c in out.columns if c in (L("Price target", "السعر المستهدف"), L("Prior target", "الهدف السابق"))}
    ui.table(out, fmt=fmt, words={L("Action", "الإجراء"): (L("Upgrade", "ترقية"), L("Downgrade", "تخفيض"))}, height=460)


# ---------------------------------------------------------------- insiders
INS_KIND = {"buy": ("Buy", "شراء", "up"), "sell": ("Sale", "بيع", "down"), "option": ("Option exercise", "تنفيذ خيارات", "acc"),
            "award": ("Award / grant", "منحة", "vio"), "gift": ("Gift", "هدية", "neu"), "other": ("Other", "أخرى", "neu")}


def _ins_kind(text, trans=""):
    t = f"{trans} {text}".lower()
    if "purchase" in t or " buy" in f" {t}":
        return "buy"
    if "sale" in t or "sold" in t or " sell" in f" {t}":
        return "sell"
    if "option" in t or "exercise" in t or "conversion" in t:
        return "option"
    if "award" in t or "grant" in t:
        return "award"
    if "gift" in t:
        return "gift"
    return "other"


def insider_table(ins):
    """Yahoo's insider transactions, cleaned: Date, Insider, Position, Type, Shares, Value, Ownership, Details (newest first)."""
    if not isinstance(ins, pd.DataFrame) or ins.empty:
        return pd.DataFrame()
    col = lambda *names: next((ins[n] for n in names if n in ins), pd.Series([""] * len(ins), index=ins.index))
    date = pd.to_datetime(col("Start Date", "Date", "startDate"), errors="coerce")
    text = col("Text", "Transaction Text").astype(str).replace("nan", "")
    trans = col("Transaction").astype(str).replace("nan", "")
    out = pd.DataFrame({"Date": date, "Insider": col("Insider", "Filer Name").astype(str).str.title(),
                        "Position": col("Position", "Relation", "Filer Relation").astype(str).replace("nan", ""),
                        "Kind": [_ins_kind(t, tr) for t, tr in zip(text, trans)],
                        "Shares": pd.to_numeric(col("Shares"), errors="coerce"), "Value": pd.to_numeric(col("Value"), errors="coerce"),
                        "Ownership": col("Ownership").astype(str).map({"D": "Direct", "I": "Indirect"}).fillna(""),
                        "Details": text})
    return out.sort_values("Date", ascending=False, na_position="last").reset_index(drop=True)


def insider_section(sym):
    """Insider transactions: the last 6 months in four tiles (buys, sales, net, the latest) and every transaction in a table."""
    cat = catalysts(sym, H.BUILD)
    t = insider_table(cat.get("insiders"))
    ui.sec("badge", "Insider transactions", "تعاملات المطّلعين")
    if t.empty:
        st.caption(L("Yahoo Finance has no insider transactions for this stock right now.",
                     "ياهو فاينانس ما عنده تعاملات مطّلعين لهذا السهم حالياً."))
        return
    recent = t[t["Date"] >= pd.Timestamp.now() - pd.Timedelta(days=183)]
    buys, sells = recent[recent["Kind"] == "buy"], recent[recent["Kind"] == "sell"]
    bv, sv = float(buys["Value"].fillna(0).sum()), float(sells["Value"].fillna(0).sum())
    net = bv - sv

    def tile(ic, label, value, sub, good=None):
        cls = "" if good is None else (" ok" if good else " bad")
        return (f'<div class="hnkt{cls}"><div class="l">{T.icon(ic)}<span>{T.esc(label)}</span></div><div class="v">{value}</div>'
                f'<div class="s">{T.esc(sub)}</div></div>')
    last = t.iloc[0]
    lk = INS_KIND[last["Kind"]]
    tiles = [tile("shopping_cart", L("Insider buys (6 months)", "شراء المطّلعين (6 أشهر)"), T.money(bv, short=True) if bv else "$0",
                  L(f"{len(buys)} transactions · {buys['Shares'].fillna(0).sum():,.0f} shares", f"{len(buys)} عملية · {buys['Shares'].fillna(0).sum():,.0f} سهم"),
                  True if len(buys) else None),
             tile("sell", L("Insider sales (6 months)", "بيع المطّلعين (6 أشهر)"), T.money(sv, short=True) if sv else "$0",
                  L(f"{len(sells)} transactions · {sells['Shares'].fillna(0).sum():,.0f} shares", f"{len(sells)} عملية · {sells['Shares'].fillna(0).sum():,.0f} سهم"),
                  False if len(sells) else None),
             tile("balance", L("Net (buys − sales)", "الصافي (شراء − بيع)"), ("+" if net > 0 else "") + T.money(net, short=True),
                  L("insiders bought more" if net > 0 else "insiders sold more" if net < 0 else "balanced",
                    "المطّلعين اشتروا أكثر" if net > 0 else "المطّلعين باعوا أكثر" if net < 0 else "متوازن"), None if net == 0 else net > 0),
             tile("event", L("Latest", "الأحدث"), f"{last['Date']:%Y-%m-%d}" if pd.notna(last["Date"]) else "—",
                  f"{L(*lk[:2])} · {last['Insider']}", None)]
    ui.html(f'<div class="hnkts4">{"".join(tiles)}</div>')
    N = {"Date": L("Date", "التاريخ"), "Insider": L("Insider", "المطّلع"), "Position": L("Position", "المنصب"), "Kind": L("Type", "النوع"),
         "Shares": L("Shares", "الأسهم"), "Value": L("Value ($)", "القيمة ($)"), "Ownership": L("Ownership", "الملكية"), "Details": L("Details", "التفاصيل")}
    show = t.copy()
    show["Date"] = show["Date"].dt.date
    show["Kind"] = show["Kind"].map(lambda k: L(*INS_KIND[k][:2]))
    show["Ownership"] = show["Ownership"].map(lambda o: L(o, {"Direct": "مباشرة", "Indirect": "غير مباشرة"}.get(o, o)) if o else "—")
    show = show.rename(columns=N)
    ui.table(show, words={N["Kind"]: (L("Buy", "شراء"), L("Sale", "بيع"))}, fmt={N["Shares"]: "{:,.0f}", N["Value"]: "${:,.0f}"},
             wrap={N["Details"]}, height=500)
    st.download_button(L("Export CSV", "تصدير CSV"), show.to_csv(index=False).encode("utf-8-sig"), f"insiders_{sym}.csv", "text/csv",
                       icon=":material/download:", key=f"hn_ins_csv_{_key(sym)}")


def news_section(sym):
    cat = catalysts(sym, H.BUILD)
    if cat["news"]:
        ui.sec("newspaper", f"Latest news · {sym}", f"آخر الأخبار · {sym}")
        ui.news_list(cat["news"], 6)


def detail(r, det, got):
    sym = r["Symbol"]
    k = r["Setup"]
    with st.container(key=f"hnsec_head_{_key(sym)}"):
        badges = T.badge(sector_name(r["Sector"]) if r["Sector"] else "—", "gold", "category")
        ind = industry_of(sym)
        if ind:
            badges += T.badge(industry_label(ind), "neu", "factory")
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
            if d is not None:
                levels = ([(L("Entry", "دخول"), r["Entry"], _A, "solid"), (L("Stop", "وقف"), r["Stop"], _D, "dash"),
                           (L("Target", "هدف"), r["Target"], _U, "dash")] if np.isfinite(r["Entry"]) else None)
                ui.chart(charts.price_chart(d.tail(190), "Candles", ["SMA 20", "SMA 50", "SMA 200"], [], False, levels=levels, height=470),
                         key=f"hn_chart_{_key(sym)}")
            ui.safe(fundamentals_box, sym)
        with right:
            ui.sec("donut_large", "Why this score", "ليش هالتقييم")
            parts = {"trend": r["Trend"], "rs": r["RS"], "volume": r["Accum"], "setup": r["SetupPts"], "risk": r["RiskPts"]}
            ui.html('<div class="hnparts">' + "".join(
                f'<div class="r"><span>{T.esc(L(*H.PARTS[p]))} <span class="w">· {int(H.WEIGHTS[p] * 100)}%</span></span>'
                f'<div class="bar"><i style="width:{float(v):.0f}%"></i></div><b>{float(v):.0f}</b></div>' for p, v in parts.items()) + "</div>")
            tc = tech_checks(r, det, d, spy5)
            npass = sum(c_["Pass"] for c_ in tc)
            ui.html(f'<div class="hnbox" style="margin-top:12px"><div class="hnbt">{T.icon("query_stats")}<span>{L("Technical checks", "الفحص الفني")}</span>'
                    f'{score_chip(f"{npass}/{len(tc)}", npass >= len(tc) / 2)}</div>{_checklist2(tc)}</div>')
            ui.safe(events_box, sym)

    with st.container(key=f"hnsec_an_{_key(sym)}"):
        ui.safe(analyst_section, sym, float(r["Price"]))
    with st.container(key=f"hnsec_ins_{_key(sym)}"):
        ui.safe(insider_section, sym)

    with st.container(key=f"hnsec_plan_{_key(sym)}"):
        ui.safe(plan_section, r, det, d)

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
                ui.html('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px">' + "".join(tiles) + "</div>")
                show = bt.tail(12).iloc[::-1].copy()
                show["Entry Date"] = pd.to_datetime(show["Entry Date"]).dt.date
                show["Exit Date"] = pd.to_datetime(show["Exit Date"]).dt.date
                reason = {"Stop": L("Stop", "الوقف"), "Target": L("Target", "الهدف"), "Time": L("Time limit", "المدة")}
                show["Reason"] = show["Reason"].map(reason)
                N = {"Entry Date": L("Entry", "الدخول"), "Entry": L("Price", "السعر"), "Exit Date": L("Exit", "الخروج"), "Exit": L("Exit price", "سعر الخروج"),
                     "Ret %": L("Return %", "العائد %"), "Bars": L("Days", "الأيام"), "Reason": L("Exit by", "الخروج بـ")}
                show = show[["Entry Date", "Entry", "Exit Date", "Exit", "R", "Ret %", "Bars", "Reason"]].rename(columns=N)
                ui.table(show, pills={"R"}, signed={N["Ret %"]}, height=460,
                         fmt={N["Entry"]: "{:,.2f}", N["Exit"]: "{:,.2f}", "R": "{:+.2f}", N["Ret %"]: "{:+.1f}%", N["Bars"]: "{:,.0f}"})
                st.caption(L("Same rule, same stop, target and time limit; entry at the next open, the stop checked first when a candle "
                             "touches both. Past results on one stock are a guide, not a promise.",
                             "نفس الشرط ونفس الوقف والهدف والمدة؛ الدخول عند الافتتاح التالي، والوقف يُفحص أول إذا لمست الشمعة الاثنين. "
                             "نتائج الماضي على سهم واحد دليل وليست ضمان."))

    with st.container(key=f"hnsec_act_{_key(sym)}"):
        with st.container(key="hnact", horizontal=True):
            if st.button(L("Stock page", "صفحة السهم"), icon=":material/candlestick_chart:", key="hn_open"):
                ui.open_stock(sym)
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
    grade = lambda v, r: (f'<span class="xgr" style="--g:{GRADE_COLOR.get(v, _MU)}">{T.esc(v)}</span>' if isinstance(v, str) else "—")
    ui.table(show, sym=N["Symbol"], height=600, pills={N["Chg %"]}, signed={N["1M %"], N["3M %"]},
             cell={N["Score"]: lambda v, r: ui.score_bar(v), N["Grade"]: grade},
             fmt={N["Price"]: "{:,.2f}", N["Chg %"]: "{:+.2f}%", N["1M %"]: "{:+.1f}%", N["3M %"]: "{:+.1f}%", "RS": "{:,.0f}", "RVOL": "{:.1f}×",
                  N["From high %"]: "{:.1f}%", N["Entry"]: "{:,.2f}", N["Stop"]: "{:,.2f}", N["Target"]: "{:,.2f}", "R:R": "{:.1f}",
                  N["Earnings"]: "{:,.0f}"})
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
                                                                  "القطاعات حسب القوة (متوسط RS · عدد الفرص)"), 460, suffix=""), key="hn_secchart")


# ---------------------------------------------------------------- page
def _clear_look():
    ss["hn_look"] = None


def page_scanner():
    ui.html(CSS + (RTL_CSS if is_ar() else ""))
    _init()
    unis = universes()
    key, base = _base(unis)
    symbols, secs, inds = _narrow(base)
    got = None
    if symbols:
        with st.spinner(L(f"Hunting in {len(symbols)} stocks...", f"جاري الصيد في {len(symbols)} سهم...")):
            try:
                got = run_hunt(key, symbols, ss.get("hn_nonce", 0), H.BUILD)
            except Exception:
                got = None
    label = unis[key][0] + (f" · {sector_name(ss['hn_sec'])}" if ss.get("hn_sec", "all") != "all" else "")
    ui.html(hero_html(got, label))
    hunt_bar(unis, secs, inds, len(symbols))
    look = ss.get("hn_look")
    if not symbols and not look:
        st.info(L("Type at least one symbol.", "اكتب رمز واحد على الأقل."), icon=":material/info:")
        ui.foot()
        return
    res = got["res"] if got else pd.DataFrame()
    det = got["det"] if got else {}
    if (res is None or res.empty) and not look:
        st.warning(L("No price data came back. Try again in a minute, or check the symbols.",
                     "ما وصلت بيانات أسعار. حاول بعد دقيقة، أو تأكد من الرموز."), icon=":material/error:")
        ui.foot()
        return
    if got and not res.empty:
        with st.container(key="hnsec_mood"):
            ui.safe(lambda: ui.html(mood_html(got["reg"])))
            if got["n"] < 30:
                st.caption(L("A short list: the breadth numbers and the RS rating mean more with a bigger universe (RS is measured against SPY here).",
                             "قائمة قصيرة: أرقام الاتساع وتقييم RS أدق مع نطاق أكبر (RS هنا مقاس مقابل SPY)."))
        with st.container(key="hnsec_filters"):
            ui.safe(filters, res)
        view = apply(res)
    else:
        view = pd.DataFrame()
    if look:                                   # one symbol analyzed on its own (it may be outside the scan)
        row = res[res["Symbol"] == look].iloc[0].to_dict() if len(res) and look in set(res["Symbol"]) else None
        dd = det.get(look, {}) if row else None
        if row is None:
            with st.spinner(L(f"Analyzing {look}...", f"جاري تحليل {look}...")):
                row, dd = lookup(look, H.BUILD)
        with st.container(key="hnsec_look"):
            a, b = st.columns([5, 1], vertical_alignment="center")
            a.markdown(f"#### {T.icon('manage_search')} " + L(f"Analysis of {look}", f"تحليل {look}"), unsafe_allow_html=True)
            b.button(L("Close", "إغلاق"), icon=":material/close:", key="hn_look_x", on_click=_clear_look, width="stretch")
        if row is None:
            st.error(L(f"No data for {look}. Check the symbol (for example AAPL, BTC-USD, 2222.SR).",
                       f"لا توجد بيانات للرمز {look}. تأكد من الرمز (مثلاً AAPL أو BTC-USD أو 2222.SR)."))
        else:
            ui.safe(detail, pd.Series(row), dd or {}, got)
    if not view.empty:
        if ss.get("hn_sel") not in set(view["Symbol"]):
            ss["hn_sel"] = view["Symbol"].iloc[0]
        with st.container(key="hnsec_cards"):
            ui.sec("target", f"Best opportunities ({len(view)})", f"أفضل الفرص ({len(view)})")
            ui.safe(cards, view, det)
        if not look:
            r = view[view["Symbol"] == ss["hn_sel"]].iloc[0]
            ui.safe(detail, r, det.get(r["Symbol"], {}), got)
        with st.container(key="hnsec_table"):
            ui.sec("table_rows", "Every match", "كل النتائج")
            ui.safe(table, view)
    elif got and not res.empty:
        with st.container(key="hnsec_none"):
            st.info(L("Nothing matches these filters. Lower the grade, clear the setups, or scan a bigger universe.",
                      "ما فيه شي يطابق هالتصفية. نزّل الدرجة، أو شيل الفرص المختارة، أو افحص نطاق أكبر."), icon=":material/search_off:")
    if got and not res.empty:
        with st.container(key="hnsec_charts"):
            c1, c2 = st.columns([1.15, 1], gap="medium")
            with c1:
                ui.safe(lambda: ui.chart(charts.hunt_map(res, L("Opportunity map: leaders sit top right", "خريطة الفرص: القادة فوق يمين"),
                                                         (L("From 52-week high %", "البعد عن القمة السنوية %"), L("RS rating (1-99)", "تقييم RS (1-99)"),
                                                          L("Score", "التقييم"))), key="hn_map"))
            with c2:
                ui.safe(sector_chart, got["sec"])
    news_sym = look or (ss.get("hn_sel") if not view.empty else None)
    if news_sym:
        with st.container(key="hnsec_news"):
            ui.safe(news_section, news_sym)
    with st.expander(L("How the hunter works", "كيف يشتغل الصائد"), icon=":material/help:"):
        ui.html('<div class="hnnote">' + L(
            "<b>Setups</b> are exact rules on the daily close (the four combined strategies of the Paper Bots, breakouts, leaders, "
            "golden crosses, oversold dips, accumulation days, gaps, squeezes and breakdowns). A setup is <b>new today</b> when it fired "
            "on the latest candle, <b>active</b> when it fired in the last 2-3 sessions and the price is still between its stop and its "
            "target, and on <b>watch</b> when it is building. <b>The score</b> (0-100): trend 25%, relative strength 25% (RS 1-99: "
            "the 3-12 month return ranked against every stock scanned), accumulation 15%, the setup 20% and reward-to-risk 15%; "
            "earnings within 5 days (-8) and thin trading (-5) cost points, and a stock without a buying setup can't pass 49. "
            "Grades: A+ from 85, A from 75, B from 65, C from 50. <b>Catalysts</b> (fundamental checks, analyst actions, earnings, "
            "news) are shown for the opened stock; they don't change the score.",
            "<b>الفرص</b> شروط دقيقة على الإغلاق اليومي (الاستراتيجيات المركّبة الأربع في البوتات الافتراضية، والاختراقات، والقادة، "
            "والتقاطع الذهبي، والتشبع البيعي، وأيام التجميع، والفجوات، والانضغاط، والكسر الهابط). الفرصة <b>جديدة اليوم</b> إذا ظهرت على آخر "
            "شمعة، و<b>نشطة</b> إذا ظهرت خلال آخر 2-3 جلسات والسعر لسا بين الوقف والهدف، و<b>مراقبة</b> إذا لسا تتكوّن. <b>التقييم</b> (من 100): "
            "الاتجاه 25%، والقوة النسبية 25% (RS من 1 إلى 99: عائد 3 إلى 12 شهر مرتب مقابل كل الأسهم المفحوصة)، والتجميع 15%، والفرصة 20%، "
            "والعائد مقابل المخاطرة 15%؛ وإعلان أرباح خلال 5 أيام (-8) وضعف السيولة (-5) ينقصون النقاط، والسهم بدون فرصة شراء ما يتعدى 49. "
            "الدرجات: A+ من 85، وA من 75، وB من 65، وC من 50. <b>المحفزات</b> (الفحص المالي، وتحركات المحللين، والأرباح، والأخبار) تظهر "
            "للسهم المفتوح وما تغيّر التقييم.") + "</div>")
    st.caption(L("Daily prices from Yahoo Finance (may be delayed). This is a research tool, not investment advice: check the chart and the news "
                 "before any trade, and never risk more than you can afford to lose.",
                 "أسعار يومية من ياهو فاينانس (قد تكون متأخرة). هذي أداة بحث وليست نصيحة استثمارية: راجع الشارت والأخبار قبل أي صفقة، "
                 "ولا تخاطر بأكثر مما تتحمل خسارته."))
    ui.foot()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "15.1"
