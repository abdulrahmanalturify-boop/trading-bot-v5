"""
p_hunter3.py - Opportunity Hunter 3.0 (menu: Trading Bot / Hunter 3.0), in place of the Hunter V3 Alpha Lab.

Top to bottom:
  * a hero in lavender and cyan with the counts of the scan and Kuhailan, the site's robot,
  * the hunt bar: what to scan (the same universes as the Opportunity Hunter), the score to rank by (the old Hunter's score
    as the baseline, the static multi-factor score, the regime-adaptive one, and the ML ranker when its evidence allowed it),
    the account size and the risk per trade,
  * Market Intelligence: the regime, the benchmark's trend, volatility, breadth, highs and lows, risk-on against risk-off,
    correlation and dispersion, liquidity, leadership and concentration, the last six months of regimes, sector rotation,
  * Opportunity Discovery: filters (tier, setups, grade, earnings, price, liquidity) and the eight best as cards,
  * the opened opportunity: chart with entry / stop / target, "why this opportunity?" (the factor groups behind the score,
    what speaks against it, what would invalidate it, what is uncertain), the trade plan, the risk profile, how the same
    setup did on the same stock before, the fundamentals snapshot (not part of the score), the sector context,
  * Factor Breakdown: every group rank of the best twenty, side by side,
  * Comparison: the picks of every score next to each other and how much they agree,
  * Portfolio: a risk-aware paper book from the candidates (position sizes, sector and correlation limits, the regime's
    exposure cap, a stress line),
  * Strategy Research: the multi-period evidence measured on GitHub Actions (research/hunter3_backtest.py), with the verdict
    on which score the page ranks by, never a number that was not measured.
The engine is hunter3.py; the setups and the baseline score are hunter.py's.
"""
import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import brain
import charts
import data
import hunter as H
import hunter3 as H3
import markets as MK
import mascot
import p_scanner as PS
import paperbots as PB
import theme as T
import ui
from i18n import L, is_ar, sector_name

ss = st.session_state
_A, _V, _C, _G, _D, _U, _MU, _BD = T.ACCENT, T.VIOLET, T.CYAN, T.GOLD, T.DOWN, T.UP, "#9D97A5", T.BORDER
LAV, CYA = "#C4B5FD", "#7DD3FC"                                    # the page's two accents: lavender and light cyan
GROUP_COLOR = {"momentum": LAV, "trend": CYA, "volume": "#86EFAC", "risk": "#FCA5A5", "setup": "#FDE68A"}
METHOD = {"v1": ("Hunter (baseline)", "الصياد (الأساس)", "The Opportunity Hunter's own score: trend, relative strength, accumulation, the setup and reward-to-risk.",
                 "تقييم صائد الفرص نفسه: الاتجاه والقوة النسبية والتجميع والفرصة والعائد مقابل المخاطرة."),
          "quant": ("Multi-factor", "متعدد العوامل", "Five factor groups ranked across the universe with fixed weights.",
                    "خمس مجموعات عوامل مرتبة عبر النطاق بأوزان ثابتة."),
          "adaptive": ("Regime-adaptive", "متكيّف مع حالة السوق", "The same groups, weighted by what worked in each market regime on 2010-2015.",
                       "نفس المجموعات، بأوزان حسب ما نجح في كل حالة سوق على 2010-2015."),
          "ml": ("ML ranker", "مرتّب تعلم آلي", "A gradient-boosting model ranking the same inputs; on only when its walk-forward test allowed it.",
                 "نموذج تعزيز متدرج يرتب نفس المدخلات؛ يعمل فقط إذا سمح اختباره الزمني.")}
TIER_KIND = {"fresh": "up", "active": "acc", "watch": "gold"}
TIER_ICON = {"fresh": "bolt", "active": "trending_up", "watch": "visibility"}
FLAG = {"earnings": ("event", "Earnings in {d} days", "أرباح بعد {d} أيام", "gold"), "extended": ("height", "Stretched", "ممتد", "org"),
        "thin": ("water_drop", "Thin trading", "سيولة ضعيفة", "neu"), "volatile": ("waves", "Very volatile", "تذبذب عالٍ", "org"),
        "liquidity": ("trending_down", "Liquidity fading", "سيولة تتراجع", "neu"), "stale": ("history", "Stale prices", "أسعار قديمة", "neu")}
MIN_GRADE = PS.MIN_GRADE
N_CARDS = 8
EVIDENCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research", "results", "hunter3_backtest.json")

CSS = f"""<style>
/* ---------- hero ---------- */
.h3hero {{ position:relative; overflow:hidden; border-radius:22px; border:1px solid {_BD}; margin:2px 0 16px; min-height:250px;
  background:linear-gradient(120deg,#0E0918,#1A1333,#22194A,#120E24); background-size:300% 300%; animation:sky 20s ease-in-out infinite; }}
.h3hero::after {{ content:""; position:absolute; left:0; right:0; top:0; height:1px; background:linear-gradient(90deg,transparent,{LAV}99,transparent); z-index:3; pointer-events:none; }}
.h3hero .grid {{ position:absolute; inset:0; pointer-events:none;
  background-image:linear-gradient({CYA}14 1px,transparent 1px),linear-gradient(90deg,{CYA}14 1px,transparent 1px); background-size:36px 36px;
  -webkit-mask-image:radial-gradient(ellipse at 78% 50%,#000 0%,transparent 66%); mask-image:radial-gradient(ellipse at 78% 50%,#000 0%,transparent 66%); }}
.h3hero.rtl .grid {{ -webkit-mask-image:radial-gradient(ellipse at 22% 50%,#000 0%,transparent 66%); mask-image:radial-gradient(ellipse at 22% 50%,#000 0%,transparent 66%); }}
.h3hero .art {{ position:absolute; top:0; bottom:0; right:0; width:50%; pointer-events:none; }} .h3hero.rtl .art {{ right:auto; left:0; }}
.h3hero .art svg {{ width:100%; height:100%; display:block; }}
.h3hero .orb {{ transform-box:fill-box; transform-origin:center; animation:h3spin 24s linear infinite; }}
.h3hero .orb2 {{ transform-box:fill-box; transform-origin:center; animation:h3spin 38s linear infinite reverse; }}
@keyframes h3spin {{ to {{ transform:rotate(360deg); }} }}
.h3hero .node {{ transform-box:fill-box; transform-origin:center; animation:h3pulse 3.2s ease-in-out infinite; }}
@keyframes h3pulse {{ 0%,100% {{ opacity:.75; }} 50% {{ opacity:1; }} }}
.h3hero .txt {{ position:relative; z-index:2; padding:26px 30px 24px; max-width:640px;
  background:linear-gradient(90deg,rgba(14,9,24,.82) 0%,rgba(14,9,24,.35) 72%,rgba(14,9,24,0) 100%); }}
.h3hero.rtl .txt {{ margin-left:auto; background:linear-gradient(270deg,rgba(14,9,24,.82) 0%,rgba(14,9,24,.35) 72%,rgba(14,9,24,0) 100%); }}
.h3hero .eb {{ color:{CYA}; font-weight:600; letter-spacing:.2em; font-size:.72rem; text-transform:uppercase; display:flex; align-items:center; gap:8px; }}
.h3hero .t {{ font-size:2.7rem; font-weight:300; line-height:1.04; margin:8px 0 8px; color:#fff; letter-spacing:-.035em; }}
.h3hero .t b {{ background:linear-gradient(90deg,{LAV},{_V},{CYA}); -webkit-background-clip:text; background-clip:text; color:transparent; font-weight:600; }}
.h3hero .tg {{ color:#CAC5D1; font-size:.94rem; line-height:1.6; max-width:560px; }}
.h3hero .chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
.h3hero .chip {{ background:rgba(26,22,36,.8); border:1px solid {_BD}; backdrop-filter:blur(6px); border-radius:10px; padding:6px 10px; font-size:.8rem;
  display:inline-flex; align-items:center; gap:7px; color:#CCC7D3; }}
.h3hero .chip b {{ color:#fff; unicode-bidi:isolate; direction:ltr; }} .h3hero .chip .ms {{ color:{CYA}; font-size:1rem; }}
.h3hero .chip.reg b {{ color:{LAV}; }}
.h3hero .st {{ margin-top:12px; }}
@media (max-width: 820px) {{ .h3hero .art {{ width:100%; opacity:.22; }} .h3hero .t {{ font-size:1.9rem; }} .h3hero .txt {{ background:none; }} }}
/* ---------- the market intelligence strip ---------- */
.h3mi {{ display:grid; grid-template-columns:repeat(5,1fr); gap:10px; margin:2px 0 10px; }}
@media (max-width: 1100px) {{ .h3mi {{ grid-template-columns:repeat(3,1fr); }} }} @media (max-width: 700px) {{ .h3mi {{ grid-template-columns:1fr 1fr; }} }}
.h3mi .tl {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:12px 14px; position:relative; overflow:hidden; min-height:96px; }}
.h3mi .tl::before {{ content:""; position:absolute; left:0; right:0; top:0; height:2px; background:linear-gradient(90deg,{LAV},{CYA}); opacity:.55; }}
.h3mi .tl .l {{ color:{_MU}; font-size:.66rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; display:flex; align-items:center; gap:6px; }}
.h3mi .tl .l .ms {{ font-size:.95rem; color:{CYA}; }}
.h3mi .tl .v {{ font-size:1.3rem; font-weight:600; color:#fff; margin-top:4px; direction:ltr; unicode-bidi:isolate; display:flex; align-items:center; gap:8px; }}
.h3mi .tl .v small {{ font-size:.78rem; font-weight:600; color:{_MU}; }}
.h3mi .tl .s {{ color:{_MU}; font-size:.73rem; margin-top:3px; line-height:1.4; }}
.h3mi .bar {{ height:6px; border-radius:6px; background:rgba(157,151,165,.18); margin-top:8px; overflow:hidden; direction:ltr; }}
.h3mi .bar i {{ display:block; height:100%; border-radius:6px; }}
.h3mi .reg {{ grid-column:span 2; border-width:1.5px; }}
.h3mi .reg .v {{ font-size:1.15rem; direction:inherit; }}
.h3mi .reg .dot {{ width:10px; height:10px; border-radius:50%; box-shadow:0 0 0 4px rgba(255,255,255,.06); flex:none; }}
.h3mi .reg .s {{ color:#CAC5D1; }}
.h3mi .reg.bull {{ border-color:{_U}66; background:linear-gradient(135deg,rgba(34,197,94,.14),{T.CARD}); }}
.h3mi .reg.neutral {{ border-color:{_G}66; background:linear-gradient(135deg,rgba(245,185,74,.13),{T.CARD}); }}
.h3mi .reg.bear {{ border-color:{_D}66; background:linear-gradient(135deg,rgba(239,68,68,.14),{T.CARD}); }}
.h3mi .reg.stress {{ border-color:{_V}88; background:linear-gradient(135deg,rgba(123,69,240,.2),{T.CARD}); }}
@media (max-width: 700px) {{ .h3mi .reg {{ grid-column:span 2; }} }}
.h3rib {{ display:flex; gap:1px; height:14px; border-radius:7px; overflow:hidden; margin:4px 0 2px; direction:ltr; }}
.h3rib i {{ flex:1; display:block; opacity:.85; }} .h3rib i:hover {{ opacity:1; }}
.h3rib i.bull {{ background:{_U}; }} .h3rib i.neutral {{ background:{_G}; }} .h3rib i.bear {{ background:{_D}; }} .h3rib i.stress {{ background:{_V}; }}
.h3leg {{ display:flex; gap:12px; flex-wrap:wrap; color:{_MU}; font-size:.72rem; margin-top:4px; }}
.h3leg span::before {{ content:""; display:inline-block; width:8px; height:8px; border-radius:2px; margin-inline-end:5px; vertical-align:middle; }}
.h3leg .bull::before {{ background:{_U}; }} .h3leg .neutral::before {{ background:{_G}; }} .h3leg .bear::before {{ background:{_D}; }} .h3leg .stress::before {{ background:{_V}; }}
/* ---------- filters ---------- */
.h3fh {{ display:flex; align-items:center; gap:8px; margin:4px 0 2px; color:#E5E1EB; font-size:.9rem; }}
.h3fh .ms {{ color:{LAV}; }} .h3fh span {{ color:{_MU}; font-size:.78rem; }}
/* ---------- cards ---------- */
.h3c {{ margin:0 !important; height:372px; box-sizing:border-box; display:flex; flex-direction:column; overflow:hidden; position:relative; }}
.h3c::before {{ content:""; position:absolute; left:0; right:0; top:0; height:1px; background:linear-gradient(90deg,transparent,{LAV}99,transparent); opacity:.4; }}
.h3c.sel {{ border-color:{LAV} !important; box-shadow:0 0 0 1px {LAV}66, 0 12px 30px {_V}33; }} .h3c.sel::before {{ opacity:1; }}
.h3c .top {{ display:flex; justify-content:space-between; align-items:center; gap:6px; margin:-2px 0 10px; }}
.h3c .su {{ display:inline-flex; align-items:center; gap:5px; font-size:.68rem; font-weight:600; color:#CCC7D3; min-width:0; }}
.h3c .su .ms {{ font-size:1rem; color:{CYA}; flex:none; }} .h3c .su .tx {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.h3tier {{ display:inline-flex; align-items:center; gap:4px; font-size:.6rem; font-weight:600; letter-spacing:.05em; border-radius:6px; padding:2px 7px; text-transform:uppercase; flex:none; }}
.h3tier .ms {{ font-size:.8rem; }}
.h3tier.fresh {{ background:{T.POS_BG}; color:{T.POS_FG}; }} .h3tier.active {{ background:{T.ACC_BG}; color:{T.ACC_FG}; }} .h3tier.watch {{ background:{T.YEL_BG}; color:{T.YEL_FG}; }}
.h3c .hd {{ display:flex; align-items:center; gap:10px; }}
.h3c .hd a.co {{ display:flex; align-items:center; gap:10px; min-width:0; flex:1; text-decoration:none !important; color:inherit !important; }}
.h3c .hd a.co:hover .nm b {{ color:#79B8F4; text-decoration:underline; text-underline-offset:3px; }}
.h3c .hd .nm {{ display:flex; flex-direction:column; min-width:0; line-height:1.25; flex:1; }}
.h3c .hd .nm b {{ color:#fff; font-size:1.02rem; }}
.h3c .hd .nm span {{ color:{_MU}; font-size:.72rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.h3c .hd .px {{ display:flex; align-items:center; gap:7px; margin-top:4px; }}
.h3c .hd .px b {{ color:#fff; font-size:1.08rem; font-weight:800; letter-spacing:-.01em; direction:ltr; line-height:1.1; }}
.h3c .hd .px i {{ font-style:normal; font-weight:800; font-size:.78rem; padding:1px 8px; border-radius:999px; direction:ltr; }}
.h3c .hd .px i.up {{ color:#4ADE80; background:rgba(74,222,128,.14); }} .h3c .hd .px i.dn {{ color:#F87171; background:rgba(248,113,113,.14); }}
.h3c .spk {{ margin:8px -2px 4px; height:54px; }} .h3c .spk svg {{ width:100%; height:54px; display:block; overflow:visible; }}
.h3fac {{ display:grid; grid-template-columns:repeat(5,1fr); gap:5px; margin:4px 0 8px; direction:ltr; }}
.h3fac div {{ min-width:0; }} .h3fac span {{ display:block; color:{_MU}; font-size:.58rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; text-transform:uppercase; letter-spacing:.04em; }}
.h3fac .b {{ height:5px; border-radius:5px; background:rgba(157,151,165,.18); margin-top:3px; overflow:hidden; }} .h3fac .b i {{ display:block; height:100%; border-radius:5px; }}
.h3fac b {{ font-size:.72rem; font-weight:600; color:#E5E1EB; }}
.h3c .lv {{ display:grid; grid-template-columns:repeat(3,1fr); gap:6px; margin-top:auto; direction:ltr; }}
.h3c .lv div {{ background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.05); border-radius:10px; padding:5px 7px; min-width:0; }}
.h3c .lv span {{ display:block; color:{_MU}; font-size:.6rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; }}
.h3c .lv b {{ display:block; color:#fff; font-size:.8rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.h3c .lv i {{ display:block; font-style:normal; font-size:.66rem; font-weight:600; line-height:1.2; }} .h3c .lv .dn {{ color:#F87171; }} .h3c .lv .up {{ color:#4ADE80; }}
.h3c .ft {{ display:flex; flex-wrap:nowrap; gap:5px; margin-top:10px; overflow:hidden; min-height:24px; align-items:center; }}
.h3c .ft .c {{ display:inline-flex; align-items:center; gap:4px; font-size:.68rem; font-weight:600; color:#B1ABBA; background:rgba(157,151,165,.10); border:1px solid rgba(157,151,165,.14); border-radius:7px; padding:3px 7px; white-space:nowrap; }}
.h3c .ft .c b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }} .h3c .ft .c.w {{ color:{T.YEL_FG}; background:{T.YEL_BG}; border-color:transparent; }} .h3c .ft .c .ms {{ font-size:.85rem; }}
div[class*="st-key-h3card_"] .stButton button {{ width:100%; margin-top:-6px; border-radius:0 0 14px 14px; border-top:0; font-size:.78rem; padding:4px; }}
/* ---------- the opened opportunity ---------- */
.h3dh {{ position:relative; overflow:hidden; margin:0 !important; display:flex; align-items:center; gap:14px; flex-wrap:wrap; }}
.h3dh::before {{ content:""; position:absolute; top:0; bottom:0; left:0; width:2px; background:linear-gradient(180deg,{LAV},{CYA}); }}
.h3dh a.co {{ display:flex; align-items:center; gap:14px; text-decoration:none !important; color:inherit !important; }}
.h3dh .nm {{ display:flex; flex-direction:column; line-height:1.25; }} .h3dh .nm b {{ font-size:1.3rem; color:#fff; }} .h3dh .nm span {{ color:{_MU}; font-size:.8rem; }}
.h3dh .bd {{ display:flex; flex-wrap:wrap; gap:4px; flex:1; min-width:240px; }}
.h3dh .px {{ text-align:end; margin-inline-start:auto; }} .h3dh .px b {{ display:block; font-size:1.3rem; color:#fff; direction:ltr; }}
.h3dh .hnring, .h3dh .hnring svg {{ width:62px; height:62px; }} .h3dh .hnring .g b {{ font-size:1.2rem; }}
.h3box {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:14px 16px; margin-bottom:10px; }}
.h3bt {{ display:flex; align-items:center; gap:8px; font-weight:600; color:#F4F1F8; margin-bottom:8px; font-size:.95rem; }} .h3bt .ms {{ color:{LAV}; }}
.h3why {{ display:flex; flex-direction:column; gap:10px; }}
.h3why .g {{ display:grid; grid-template-columns:118px 1fr 40px 44px; gap:8px; align-items:center; font-size:.8rem; color:#E5E1EB; font-weight:600; }}
.h3why .g .w {{ color:{_MU}; font-weight:500; font-size:.7rem; }}
.h3why .bar {{ height:8px; border-radius:8px; background:rgba(157,151,165,.18); overflow:hidden; direction:ltr; }} .h3why .bar i {{ display:block; height:100%; border-radius:8px; }}
.h3why .g b {{ text-align:end; direction:ltr; }}
.h3why details {{ grid-column:1 / -1; margin:-4px 0 2px; }} .h3why summary {{ cursor:pointer; color:{_MU}; font-size:.72rem; list-style:none; }} .h3why summary::before {{ content:"▸ "; }}
.h3why details[open] summary::before {{ content:"▾ "; }}
.h3why .fx {{ display:grid; grid-template-columns:1fr 60px 44px; gap:6px; font-size:.74rem; color:#CAC5D1; padding:2px 0 2px 8px; font-weight:500; }}
.h3why .fx b {{ direction:ltr; text-align:end; color:#fff; font-weight:600; }} .h3why .fx .pr {{ height:5px; border-radius:5px; background:rgba(157,151,165,.18); margin-top:5px; }} .h3why .fx .pr i {{ display:block; height:100%; border-radius:5px; background:{CYA}; }}
.h3case {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }} @media (max-width: 760px) {{ .h3case {{ grid-template-columns:1fr; }} }}
.h3case .k {{ background:rgba(255,255,255,.025); border:1px solid rgba(255,255,255,.06); border-radius:12px; padding:10px 12px; }}
.h3case .k .t {{ display:flex; align-items:center; gap:6px; font-size:.76rem; font-weight:600; letter-spacing:.04em; text-transform:uppercase; margin-bottom:6px; }}
.h3case .k.for .t {{ color:#4ADE80; }} .h3case .k.against .t {{ color:#F87171; }} .h3case .k.inv .t {{ color:{_G}; }} .h3case .k.unc .t {{ color:{CYA}; }}
.h3case .k ul {{ margin:0; padding-inline-start:16px; color:#D9D4E0; font-size:.82rem; line-height:1.5; }}
.h3plan {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin:4px 0 10px; }} @media (max-width: 900px) {{ .h3plan {{ grid-template-columns:repeat(2,1fr); }} }}
.h3plan .p {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:14px; padding:10px 12px; position:relative; overflow:hidden; }}
.h3plan .p .l {{ color:{_MU}; font-size:.66rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; }}
.h3plan .p .v {{ color:#fff; font-size:1.12rem; font-weight:600; margin-top:3px; direction:ltr; unicode-bidi:isolate; }}
.h3plan .p .s {{ color:{_MU}; font-size:.72rem; margin-top:2px; }}
.h3plan .p.en {{ border-color:{_A}66; }} .h3plan .p.sl {{ border-color:{_D}66; }} .h3plan .p.tp {{ border-color:{_U}66; }}
.h3plan .p.en .v {{ color:#9DC4FF; }} .h3plan .p.sl .v {{ color:#F87171; }} .h3plan .p.tp .v {{ color:#4ADE80; }}
.h3note {{ background:rgba(196,181,253,.08); border:1px solid rgba(196,181,253,.25); border-radius:12px; padding:10px 12px; color:#D9D4E0; font-size:.84rem; line-height:1.55; }}
.h3note.warn {{ background:{T.YEL_BG}; border-color:transparent; color:{T.YEL_FG}; }}
/* ---------- tables ---------- */
.h3tbl {{ width:100%; border-collapse:separate; border-spacing:0; font-size:.8rem; }}
.h3tbl th {{ color:{_MU}; font-weight:600; font-size:.68rem; letter-spacing:.06em; text-transform:uppercase; padding:6px 8px; text-align:start; border-bottom:1px solid {_BD}; white-space:nowrap; }}
.h3tbl td {{ padding:7px 8px; border-bottom:1px solid rgba(157,151,165,.1); color:#E5E1EB; white-space:nowrap; vertical-align:middle; }}
.h3tbl tr:hover td {{ background:rgba(255,255,255,.03); }}
.h3tbl td.n, .h3tbl th.n {{ text-align:end; direction:ltr; font-variant-numeric:tabular-nums; }}
.h3tbl td.c {{ text-align:center; }}
.h3tbl .cell {{ display:inline-block; min-width:38px; text-align:center; border-radius:6px; padding:2px 6px; font-weight:600; color:#0E0918; direction:ltr; }}
.h3tbl .sym {{ font-weight:700; color:#fff; }} .h3tbl .sym small {{ color:{_MU}; font-weight:500; margin-inline-start:6px; }}
.h3tbl td.best {{ color:#4ADE80; font-weight:700; }} .h3tbl td.worst {{ color:#F87171; }}
.h3wrap {{ overflow-x:auto; }}
.h3cmp {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:10px; }}
.h3cmp .m {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:14px; padding:12px 14px; }}
.h3cmp .m .t {{ font-weight:600; color:#fff; display:flex; align-items:center; gap:6px; margin-bottom:6px; }} .h3cmp .m .t .ms {{ color:{LAV}; }}
.h3cmp .m .r {{ display:flex; justify-content:space-between; font-size:.8rem; padding:3px 0; border-bottom:1px solid rgba(157,151,165,.1); color:#E5E1EB; }}
.h3cmp .m .r b {{ direction:ltr; color:{CYA}; }} .h3cmp .m .r.both {{ color:#fff; }} .h3cmp .m .r.both::after {{ content:"✓"; color:#4ADE80; margin-inline-start:6px; }}
.h3cmp .m .tag {{ display:inline-block; font-size:.62rem; font-weight:600; letter-spacing:.05em; text-transform:uppercase; border-radius:6px; padding:2px 6px; margin-inline-start:auto; }}
.h3cmp .m .tag.ok {{ background:{T.POS_BG}; color:{T.POS_FG}; }} .h3cmp .m .tag.no {{ background:rgba(157,151,165,.16); color:#BBB5C3; }} .h3cmp .m .tag.rej {{ background:{T.NEG_BG}; color:{T.NEG_FG}; }}
.h3ver {{ display:flex; gap:12px; align-items:flex-start; background:linear-gradient(135deg,rgba(196,181,253,.12),rgba(125,211,252,.06)); border:1px solid rgba(196,181,253,.3); border-radius:16px; padding:14px 16px; margin-bottom:10px; }}
.h3ver .ms {{ color:{LAV}; font-size:1.6rem; flex:none; }} .h3ver b {{ color:#fff; }} .h3ver p {{ margin:4px 0 0; color:#D9D4E0; font-size:.86rem; line-height:1.55; }}
</style>"""


# ---------------------------------------------------------------- data
@st.cache_resource(ttl=900, show_spinner=False, max_entries=4)
def _scan(key, symbols, nonce=0, build=None, market="us", ar=False):
    """Prices of the universe (two years of daily candles), the scan and the market state. Kept 15 minutes per universe; the
    panel is big, so it is kept as one object (never changed by the page)."""
    sa = market == MK.SA
    px = PB.load_prices(list(symbols), "2y")
    bench = PS._bench("2y", market)
    if bench is None or bench.empty:
        return None
    vix = None if sa else data.history("^VIX", "6mo")
    today = MK.today(market)
    earn = {} if sa else PS._earnings_map(today)
    names, secs = PS._names_sectors(symbols, ar)
    res, state, groups, panel = H3.scan(px, bench, vix if vix is not None and not vix.empty else None, secs, names, earn, today, thin=10e6 if sa else 20e6)
    last = max((pd.Timestamp(df.index[-1]) for df in px.values() if df is not None and len(df)), default=None)
    methods = [m for m in METHOD if f"score_{m}" in res.columns] if len(res) else ["v1", "quant", "adaptive"]
    return {"res": res, "state": state, "groups": groups, "panel": panel, "n": len(panel.syms), "asked": len(symbols), "methods": methods,
            "time": MK.now(market).strftime("%H:%M"), "last": last, "earn": len(earn) > 0, "px": px}


@st.cache_data(ttl=600, show_spinner=False)
def evidence(build=None):
    """The research results measured on GitHub Actions (None until the first run was committed)."""
    try:
        with open(EVIDENCE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def default_method(ev):
    return (ev or {}).get("verdict", {}).get("default", "v1")


def method_status(ev, m):
    """'recommended' / 'not better' / 'rejected' / 'baseline' / None (no evidence yet)."""
    if m == "v1":
        return "baseline"
    if not ev:
        return None
    return ev.get("verdict", {}).get("methods", {}).get(m, {}).get("status")


def ranked(got, method):
    """The scan's table with Score and Grade from the chosen method, best first."""
    res = got["res"].copy()
    col = f"score_{method}" if f"score_{method}" in res else "score_v1"
    res["Score"] = res[col].astype(float)
    res["Grade"] = res["Score"].apply(H3.grade)
    return res.sort_values(["Score", "RS"], ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------- small pieces
def _px(v):
    return MK.money(v, dec=2)


def _money_px(x):
    if MK.is_sa():
        return MK.money(x, dec=2) if abs(x) >= 1 else f"{T.fmt_price(x)} {MK.cur_sign()}"
    return "$" + T.fmt_price(x)


def _pct(a, b):
    return (b / a - 1) * 100 if a else 0.0


def _f(v, fmt="{:.1f}", none="—"):
    try:
        return none if v is None or not np.isfinite(float(v)) else fmt.format(float(v))
    except (TypeError, ValueError):
        return none


def tier_tag(status, age=None):
    if status not in TIER_KIND:
        return ""
    en, ar_ = H3.TIER[status]
    if status == "active" and age and np.isfinite(age):
        en, ar_ = f"{en} · {int(age)}d", f"{ar_} · {int(age)} ي"
    return f'<span class="h3tier {status}">{T.icon(TIER_ICON[status])}{T.esc(L(en, ar_))}</span>'


def flags_of(r):
    out = []
    for f in [x for x in str(r.get("Flags") or "").split(",") if x]:
        if f not in FLAG:
            continue
        ic, en, ar_, kind = FLAG[f]
        d = int(r["Earnings"]) if f == "earnings" and pd.notna(r.get("Earnings")) else 0
        out.append((ic, L(en.format(d=d), ar_.format(d=d)), kind))
    return out


def group_bars(r, small=True):
    """The five factor groups of one row as tiny bars."""
    out = []
    for g, (en, ar_, _) in H3.GROUPS.items():
        v = r.get(f"g_{g}", np.nan)
        pct = 0 if not np.isfinite(v) else float(v)
        out.append(f'<div><span>{T.esc(L(en, ar_))}</span><div class="b"><i style="width:{pct:.0f}%;background:{GROUP_COLOR[g]}"></i></div><b>{_f(v, "{:.0f}")}</b></div>')
    return '<div class="h3fac">' + "".join(out) + "</div>"


def _method_name(m):
    return L(METHOD[m][0], METHOD[m][1]) if m in METHOD else m


# ---------------------------------------------------------------- hero
def _orbit(res, rtl=False):
    """Five factor nodes on turning rings, the strongest groups of the scan lit the most."""
    cx, cy = (150 if rtl else 370), 125
    means = {g: (float(res[f"g_{g}"].mean()) if res is not None and len(res) and f"g_{g}" in res else 50.0) for g in H3.GROUPS}
    s = [f'<svg viewBox="0 0 520 250" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" style="direction:ltr">'
         f'<defs><radialGradient id="h3rg" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{LAV}" stop-opacity=".18"/><stop offset="1" stop-color="{LAV}" stop-opacity="0"/></radialGradient></defs>'
         f'<circle cx="{cx}" cy="{cy}" r="118" fill="url(#h3rg)"/>']
    for r_, op in ((36, .5), (68, .4), (100, .3)):
        s.append(f'<circle cx="{cx}" cy="{cy}" r="{r_}" fill="none" stroke="{CYA}" stroke-opacity="{op}" stroke-width="1" stroke-dasharray="2 5"/>')
    s.append(f'<g class="orb"><circle cx="{cx + 68}" cy="{cy}" r="3" fill="{CYA}"/><circle cx="{cx - 68}" cy="{cy}" r="2" fill="{LAV}"/></g>')
    s.append(f'<g class="orb2"><circle cx="{cx}" cy="{cy - 100}" r="2.5" fill="{LAV}"/></g>')
    for i, (g, (en, ar_, _)) in enumerate(H3.GROUPS.items()):
        ang = -90 + i * 72
        rad = np.deg2rad(ang)
        x, y = cx + 68 * np.cos(rad), cy + 68 * np.sin(rad)
        r_ = 5 + means[g] / 100 * 9
        s.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{GROUP_COLOR[g]}" stroke-opacity=".35" stroke-width="1"/>')
        s.append(f'<circle class="node" cx="{x:.1f}" cy="{y:.1f}" r="{r_:.1f}" fill="{GROUP_COLOR[g]}" fill-opacity=".9" style="animation-delay:{i * .5}s"/>')
        lx, ly = cx + 104 * np.cos(rad), cy + 104 * np.sin(rad) + 4
        s.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" font-size="10" fill="#CAC5D1" font-family="{T.FONT}">{T.esc(L(en, ar_))}</text>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="9" fill="#0E0918" stroke="{LAV}" stroke-width="2"/><circle cx="{cx}" cy="{cy}" r="3.5" fill="{CYA}"/>')
    s.append("</svg>")
    return "".join(s)


def hero_html(got, view, label, method, ev):
    chips = []
    res = got["res"] if got else None
    if got and res is not None and len(res):
        tiers = res["Tier"].value_counts()
        reg = got["state"]["regime"].iloc[-1]
        chips.append(f'<span class="chip">{T.icon("radar")}{L("Scanned", "تم فحص")} <b>{got["n"]:,}</b> · {T.esc(label)}</span>')
        chips.append(f'<span class="chip">{T.icon("bolt")}{L("Actionable", "قابلة للتنفيذ")} <b>{int(tiers.get("fresh", 0))}</b></span>')
        chips.append(f'<span class="chip">{T.icon("trending_up")}{L("Developing", "تتكوّن")} <b>{int(tiers.get("active", 0))}</b></span>')
        chips.append(f'<span class="chip">{T.icon("visibility")}{L("Watchlist", "مراقبة")} <b>{int(tiers.get("watch", 0))}</b></span>')
        chips.append(f'<span class="chip reg">{T.icon("explore")}{L("Regime", "حالة السوق")} <b>{T.esc(L(*brain.REGIME_LABEL[reg]))}</b></span>')
        st_ = method_status(ev, method)
        tag = {"recommended": L("evidence: better", "الدليل: أفضل"), "not better": L("evidence: not better", "الدليل: ليس أفضل"),
               "rejected": L("rejected", "مرفوض"), "baseline": L("baseline", "الأساس"), None: L("no evidence yet", "بلا دليل بعد")}[st_]
        chips.append(f'<span class="chip">{T.icon("functions")}{L("Ranked by", "مرتّب حسب")} <b>{T.esc(_method_name(method))}</b> · {T.esc(tag)}</span>')
        tl = L("Riyadh", "الرياض") if MK.is_sa() else "ET"
        chips.append(f'<span class="chip">{T.icon("schedule")}{L("Updated", "آخر تحديث")} <b>{got["time"]} {tl}</b></span>')
    tag = L("Market regime, breadth and liquidity first; then every stock with a live setup ranked on momentum, trend, volume, risk and "
            "the setup itself, with the plan, the risk profile and the reasons, and a paper book built under sector, correlation and "
            "exposure limits. Every score is a rank out of 100, never a probability.",
            "حالة السوق واتساعه وسيولته أولاً؛ ثم كل سهم عنده فرصة حيّة يُرتّب على الزخم والاتجاه والحجم والمخاطرة والفرصة نفسها، "
            "مع الخطة وملف المخاطر والأسباب، ومحفظة افتراضية بحدود للقطاع والارتباط والتعرض. كل تقييم ترتيب من 100، وليس احتمالاً.")
    return (f'<div class="h3hero{" rtl" if is_ar() else ""}"><div class="grid"></div><div class="art">{_orbit(res, is_ar())}</div>'
            f'<div class="txt"><div class="eb">{mascot.svg(24, uid="kh3")}{L("Opportunity Hunter 3.0", "صائد الفرص 3.0")}</div>'
            f'<div class="t">{L("Institutional-grade <b>opportunity hunting</b>", "صيد الفرص <b>بمعايير المؤسسات</b>")}</div><div class="tg">{T.esc(tag)}</div>'
            f'<div class="chips">{"".join(chips)}</div><div class="st">{T.market_status(is_ar())}</div></div></div>')


# ---------------------------------------------------------------- the hunt bar
def _go():
    ss["h3_nonce"] = ss.get("h3_nonce", 0)


def _refresh():
    ss["h3_nonce"] = ss.get("h3_nonce", 0) + 1


def _init(ev):
    PS._init()                                           # the universe, sector and industry choices are shared with the Opportunity Hunter
    for k, v in {"h3_method": default_method(ev), "h3_acct": 100_000, "h3_risk": 0.75, "h3_tiers": ["fresh", "active"], "h3_grade": "C",
                 "h3_noearn": False, "h3_minpx": 5.0, "h3_minvol": 20.0 if not MK.is_sa() else 5.0}.items():
        ss.setdefault(k, v)


def hunt_bar(unis, secs, inds, n, methods, ev):
    with st.container(key="h3bar"):
        c = st.columns([1.8, 1.3, 1.6, 1.7, 0.9, 0.8], vertical_alignment="bottom")
        c[0].selectbox(L("What to scan", "وش أفحص"), list(unis), key="hn_uni", format_func=lambda k: unis[k][0])
        c[1].selectbox(L("Sector", "القطاع"), ["all"] + secs, key="hn_sec",
                       format_func=lambda s: L("All sectors", "كل القطاعات") if s == "all" else PS.sector_label(s))
        c[2].selectbox(L("Industry", "الصناعة"), ["all"] + inds, key="hn_ind",
                       format_func=lambda s: L("All industries", "كل الصناعات") if s == "all" else PS.industry_label(s))
        if ss.get("h3_method") not in methods:
            ss["h3_method"] = methods[0]
        mark = {"recommended": " ✓", "rejected": " ✕", "not better": " ·", "baseline": "", None: ""}
        c[3].selectbox(L("Rank by", "رتّب حسب"), methods, key="h3_method", format_func=lambda m: _method_name(m) + mark[method_status(ev, m)],
                       help=L("The score the cards are ranked by. ✓ beat the baseline in the historical tests, · did not, ✕ rejected.",
                              "التقييم الذي تُرتّب به البطاقات. ✓ تفوّق على الأساس في الاختبارات التاريخية، · لم يتفوق، ✕ مرفوض."))
        c[4].button(L("Hunt", "ابدأ الصيد"), icon=":material/radar:", key="h3_go", on_click=_go, width="stretch")
        c[5].button(L("Refresh", "تحديث"), icon=":material/refresh:", key="h3_refresh", on_click=_refresh, help=L("Fresh prices now", "أسعار جديدة الحين"), width="stretch")
        if ss.get("hn_uni") == "custom":
            if MK.is_sa():
                ui.sa_companies(L("Companies", "الشركات"), "hn_custom_sa", ["2222.SR", "1120.SR", "2010.SR", "7010.SR", "1211.SR"],
                                placeholder=L("Type a name: Aramco, Al Rajhi…", "اكتب اسم: أرامكو، الراجحي…"))
            else:
                st.text_input(L("Symbols (comma separated)", "الرموز (مفصولة بفاصلة)"), key="hn_custom", placeholder="AAPL, MSFT, NVDA, 2222.SR")
        a, b, cap = st.columns([1.3, 1, 4], vertical_alignment="bottom")
        a.number_input(L("Account", "رأس المال"), 1000, 100_000_000, step=5000, key="h3_acct")
        b.number_input(L("Risk per trade %", "المخاطرة لكل صفقة %"), 0.1, 5.0, step=0.25, key="h3_risk")
        note = L(f"{n:,} stocks in this hunt. {METHOD[ss['h3_method']][2]}", f"{n:,} سهم في هذا الصيد. {METHOD[ss['h3_method']][3]}")
        cap.caption(note)


# ---------------------------------------------------------------- market intelligence
def _meter(pct, col):
    pct = 0 if pct is None or not np.isfinite(pct) else float(np.clip(pct, 0, 100))
    return f'<div class="bar"><i style="width:{pct:.0f}%;background:{col}"></i></div>'


def market_html(state, got):
    s = state.iloc[-1]
    reg = s["regime"]
    tip = {"bull": ("Trend and breadth agree: full exposure allowed, breakouts and pullbacks both in play.",
                    "الاتجاه والاتساع متفقان: التعرض الكامل مسموح، والاختراقات والارتدادات كلاهما وارد."),
           "neutral": ("A sideways tape: exposure capped at 70%, take the stronger setups and the quicker targets.",
                       "سوق عرضي: التعرض محدود بـ 70%، خذ الفرص الأقوى والأهداف الأقرب."),
           "bear": ("Below its long averages with weak breadth: exposure capped at 35%, defend first.",
                    "تحت متوسطاته الطويلة باتساع ضعيف: التعرض محدود بـ 35%، الدفاع أولاً."),
           "stress": ("Panic volatility: exposure capped at 20%; most breakouts fail here.",
                      "تذبذب حاد: التعرض محدود بـ 20%؛ أغلب الاختراقات تفشل هنا.")}[reg]
    dot = {"bull": _U, "neutral": _G, "bear": _D, "stress": _V}[reg]
    col = lambda p: _U if p >= 55 else (_G if p >= 35 else _D)
    bench = L("Saudi market (KSA)", "السوق السعودي (KSA)") if MK.is_sa() else "S&P 500"
    t21, t63, t252, v200 = s["trend_21"], s["trend_63"], s["trend_252"], s["vs200"]
    vol, vp = s["vol_20"], s["vol_pct"]
    ro = s["risk_on"]
    corr, disp = s["avg_corr"], s["dispersion"]
    liq = s["liquidity"]
    lead, conc = s["leadership"], s["concentration"]
    tiles = [
        f'<div class="tl reg {reg}"><div class="l">{T.icon("explore")}{L("Market regime", "حالة السوق")}</div>'
        f'<div class="v"><span class="dot" style="background:{dot}"></span>{T.esc(L(*brain.REGIME_LABEL[reg]))}</div><div class="s">{T.esc(L(*tip))}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("show_chart")}{T.esc(bench)}</div><div class="v">{_f(t63, "{:+.1f}%")} <small>3M</small></div>'
        f'<div class="s">1M {_f(t21, "{:+.1f}%")} · 1Y {_f(t252, "{:+.1f}%")} · {L("vs 200-day", "مقابل 200 يوم")} {_f(v200, "{:+.1f}%")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("waves")}{L("Volatility", "التذبذب")}</div><div class="v">{_f(vol, "{:.0f}%")} <small>{L("annualised", "سنوي")}</small></div>'
        f'{_meter(vp, _D if (np.isfinite(vp) and vp >= 80) else CYA)}<div class="s">{L("percentile of its year", "ترتيبه خلال سنة")}: {_f(vp, "{:.0f}")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("stacked_bar_chart")}{L("Breadth", "الاتساع")}</div><div class="v">{_f(s["breadth50"], "{:.0f}%")} <small>{L("above 50-day", "فوق 50 يوم")}</small></div>'
        f'{_meter(s["breadth50"], col(s["breadth50"] if np.isfinite(s["breadth50"]) else 0))}<div class="s">{L("above 200-day", "فوق 200 يوم")}: {_f(s["breadth200"], "{:.0f}%")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("speed")}{L("Highs / lows", "قمم / قيعان")}</div>'
        f'<div class="v"><span style="color:#4ADE80">{_f(s["highs"], "{:.0f}%")}</span> / <span style="color:#F87171">{_f(s["lows"], "{:.0f}%")}</span></div>'
        f'<div class="s">{L("at a 52-week high / low today", "عند قمة / قاع 52 أسبوع اليوم")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("swap_vert")}{L("Risk-on vs risk-off", "إقبال / عزوف عن المخاطرة")}</div>'
        f'<div class="v" style="color:{"#4ADE80" if np.isfinite(ro) and ro > 0 else "#F87171" if np.isfinite(ro) else "#fff"}">{_f(ro, "{:+.1f}")} <small>pts</small></div>'
        f'<div class="s">{L("cyclicals minus defensives, 3-month return", "الدورية ناقص الدفاعية، عائد 3 أشهر")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("hub")}{L("Correlation", "الارتباط")}</div><div class="v">{_f(corr, "{:.2f}")} <small>{L("avg to index", "متوسط مع المؤشر")}</small></div>'
        f'{_meter(corr * 100 if np.isfinite(corr) else 0, LAV)}<div class="s">{L("dispersion of 1-month returns", "تشتت عوائد الشهر")}: {_f(disp, "{:.1f}")} pts</div></div>',
        f'<div class="tl"><div class="l">{T.icon("water")}{L("Liquidity", "السيولة")}</div><div class="v">{_f(liq, "{:.2f}×")}</div>'
        f'{_meter(liq * 50 if np.isfinite(liq) else 0, CYA)}<div class="s">{L("traded value against its year's median", "قيمة التداول مقابل وسيط سنتها")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("emoji_events")}{L("Leadership", "القيادة")}</div><div class="v">{_f(lead, "{:+.0f}")} <small>pts</small></div>'
        f'<div class="s">{L("top decile's lead over the average stock (3M)", "تقدم أعلى 10% على متوسط الأسهم (3 أشهر)")} · {L("concentration", "التركّز")} {_f(conc, "{:.0f}%")}</div></div>']
    if s["risk_off_flag"]:
        tiles[0] = tiles[0].replace('<div class="s">', f'<div class="s"><b style="color:#F87171">{L("Risk-off flag on. ", "تحذير عزوف عن المخاطرة. ")}</b>', 1)
    return '<div class="h3mi">' + "".join(tiles) + "</div>"


def regime_ribbon(state):
    tail = state["regime"].tail(126)
    seg = "".join(f'<i class="{r}" title="{d.strftime("%Y-%m-%d")} · {T.esc(L(*brain.REGIME_LABEL[r]))}"></i>' for d, r in tail.items())
    share = tail.value_counts(normalize=True) * 100
    leg = " ".join(f'<span class="{r}">{T.esc(L(*brain.REGIME_LABEL[r]))} {share.get(r, 0):.0f}%</span>' for r in H3.REGIMES if share.get(r, 0) > 0)
    return (f'<div class="h3box"><div class="h3bt">{T.icon("timeline")}{L("The last six months of regimes", "حالة السوق في آخر ستة أشهر")}</div>'
            f'<div class="h3rib">{seg}</div><div class="h3leg">{leg}</div></div>')


def sector_rotation(res):
    """Sectors by their 1-month and 3-month average returns and the share of their stocks above the 50-day average."""
    d = res.dropna(subset=["Sector"])
    d = d[d["Sector"].astype(str) != ""]
    if d.empty or d["Sector"].nunique() < 2:
        return
    g = d.groupby("Sector").agg(m1=("ret_21", "mean"), m3=("ret_63", "mean"), n=("Symbol", "count"), rs=("RS", "mean")).sort_values("m3", ascending=False)
    names = [sector_name(s) for s in g.index]
    fig = go.Figure()
    fig.add_bar(y=names, x=g["m3"], orientation="h", name=L("3 months", "3 أشهر"), marker_color=LAV,
                customdata=np.column_stack([g["n"], g["rs"]]), hovertemplate="%{y}<br>3M %{x:+.1f}%<br>" + L("stocks", "أسهم") + " %{customdata[0]} · RS %{customdata[1]:.0f}<extra></extra>")
    fig.add_bar(y=names, x=g["m1"], orientation="h", name=L("1 month", "شهر"), marker_color=CYA, hovertemplate="%{y}<br>1M %{x:+.1f}%<extra></extra>")
    charts.style(fig, 300 + 14 * len(g), L("Sector rotation: average return of the scanned stocks", "دوران القطاعات: متوسط عائد الأسهم المفحوصة"))
    fig.update_layout(barmode="group", yaxis=dict(autorange="reversed"), xaxis=dict(ticksuffix="%"))
    ui.chart(fig, key="h3_sectors")


# ---------------------------------------------------------------- filters
def filters(res):
    counts = res["Setups"].str.split(",").explode().value_counts()
    keys = [k for k in H.ORDER if counts.get(k, 0) and H.SETUPS[k][4] > 0]
    if "h3_setups" in ss:
        ss["h3_setups"] = [k for k in ss["h3_setups"] if k in keys]
    with st.container(key="h3filt"):
        ui.html(f'<div class="h3fh">{T.icon("filter_alt")}<b>{L("Filters", "التصفية")}</b>'
                f'<span>{L("Tiers and setups narrow the cards; with no setup picked every buying setup shows.", "المستويات والفرص تضيّق البطاقات؛ وبدون اختيار فرصة تظهر كل فرص الشراء.")}</span></div>')
        a, b = st.columns([1.2, 2.2], vertical_alignment="center")
        a.pills(L("Tier", "المستوى"), list(TIER_KIND), selection_mode="multi", key="h3_tiers", format_func=lambda k: L(*H3.TIER[k]))
        b.pills(L("Setups", "الفرص"), keys, selection_mode="multi", key="h3_setups", format_func=lambda k: f"{PS.short_name(k)} · {int(counts.get(k, 0))}")
        c = st.columns([1.55, 1.15, 1, 1], vertical_alignment="bottom")
        c[0].segmented_control(L("Grade at least", "الدرجة على الأقل"), list(MIN_GRADE), key="h3_grade", format_func=lambda g: L("All", "الكل") if g == "all" else g)
        c[1].toggle(L("No earnings ≤ 5 days", "بدون أرباح ≤ 5 أيام"), key="h3_noearn", disabled=MK.is_sa())
        cs = MK.cur_sign()
        c[2].number_input(L(f"Price from ({cs})", f"السعر من ({cs})"), 0.0, 10000.0, step=1.0, key="h3_minpx")
        c[3].number_input(L(f"Traded/day from ({cs}M)", f"التداول اليومي من (مليون {cs})"), 0.0, 10000.0, step=5.0, key="h3_minvol")


def apply(res):
    v = res[res["Side"] > 0]
    tiers = ss.get("h3_tiers") or list(TIER_KIND)
    v = v[v["Tier"].isin(tiers)]
    picks = ss.get("h3_setups") or []
    if picks:
        v = v[v["Setups"].apply(lambda s: any(k in str(s).split(",") for k in picks))]
    v = v[v["Score"] >= MIN_GRADE.get(ss.get("h3_grade") or "all", 0)]
    if ss.get("h3_noearn"):
        v = v[~v["Flags"].str.contains("earnings", na=False)]
    v = v[(v["Price"] >= float(ss.get("h3_minpx") or 0)) & (v["$Vol"] >= float(ss.get("h3_minvol") or 0) * 1e6)]
    return v


# ---------------------------------------------------------------- cards
def card(r, closes, selected):
    sym, k = r["Symbol"], r["Setup"]
    ic = H.SETUPS[k][2] if k in H.SETUPS else "radar"
    entry, stop, tgt = r["Entry"], r["Stop"], r["Target"]
    top = f'<div class="top"><span class="su">{T.icon(ic)}<span class="tx">{T.esc(PS.short_name(k))}</span></span>{tier_tag(r["Tier"], r["Age"])}</div>'
    chg = r.get("Chg %")
    pill = f'<i class="{"up" if chg >= 0 else "dn"}">{chg:+.2f}%</i>' if chg is not None and np.isfinite(chg) else ""
    px = f'<div class="px"><b>{_money_px(r["Price"])}</b>{pill}</div>' if np.isfinite(r["Price"]) else ""
    go_ = L(f"Open the {T.sym_label(sym)} page", f"افتح صفحة {T.sym_label(sym)}")
    hd = (f'<div class="hd"><a class="co" href="{T.esc(ui.href(sym))}" target="_self" title="{T.esc(go_)}">{T.logo_obj(sym, 36)}'
          f'<div class="nm"><b>{T.esc(T.sym_label(sym))}</b><span>{T.esc(T.name_line(sym, str(r["Name"])))}</span>{px}</div></a>{PS.ring(r["Score"], r["Grade"])}</div>')
    sp = f'<div class="spk">{PS.spark(closes, entry, stop, tgt, "h3" + PS._key(sym))}</div>'
    watch = r["Tier"] == "watch"
    lv = (f'<div class="lv"><div><span>{L("Buy above", "شراء فوق") if watch else L("Entry", "الدخول")}</span><b>{_money_px(entry)}</b></div>'
          f'<div><span>{L("Stop", "الوقف")}</span><b>{_money_px(stop)}</b><i class="dn">{_pct(entry, stop):+.1f}%</i></div>'
          f'<div><span>{L("Target", "الهدف")}</span><b>{_money_px(tgt)}</b><i class="up">{_pct(entry, tgt):+.1f}%</i></div></div>') if np.isfinite(entry) else ""
    chips = [f'<span class="c">RS <b>{int(r["RS"])}</b></span>']
    if np.isfinite(r["R:R"]):
        chips.append(f'<span class="c">R:R <b>{r["R:R"]:.1f}</b></span>')
    if pd.notna(r.get("Hold")):
        chips.append(f'<span class="c">{T.icon("timer")}<b>{int(r["Hold"])}</b> {L("sessions", "جلسة")}</span>')
    for ic_, txt, kind in flags_of(r):
        chips.insert(0, f'<span class="c w">{T.icon(ic_)}{T.esc(txt)}</span>')
    return f'<div class="card h3c{" sel" if selected else ""}">{top}{hd}{sp}{group_bars(r)}{lv}<div class="ft">{"".join(chips)}</div></div>'


def _pick(sym):
    ss["h3_sel"] = sym


def cards(view, panel):
    top = view.head(N_CARDS)
    if top.empty:
        return
    sel = ss.get("h3_sel")
    rows = list(top.iterrows())
    for i in range(0, len(rows), 4):
        cols = st.columns(4)
        for col, (_, r) in zip(cols, rows[i:i + 4]):
            with col:
                with st.container(key=f"h3card_{PS._key(r['Symbol'])}"):
                    closes = panel.frames[r["Symbol"]]["Close"].tail(63).to_numpy(float) if r["Symbol"] in panel.frames else []
                    ui.html(card(r, closes, r["Symbol"] == sel))
                    st.button(r["Symbol"], key=f"h3_pick_{PS._key(r['Symbol'])}", on_click=_pick, args=(r["Symbol"],), width="stretch")


# ---------------------------------------------------------------- the opened opportunity
def why_html(case, method):
    """The factor groups behind the score with their weights, and the case for, against, the invalidation and the doubts."""
    rows = []
    for e in case["groups"]:
        pct = 0 if not np.isfinite(e["rank"]) else float(e["rank"])
        facs = "".join(f'<div class="fx"><span>{T.esc(e2["label"][1 if is_ar() else 0])}<div class="pr"><i style="width:{0 if not np.isfinite(e2["rank"]) else e2["rank"]:.0f}%"></i></div></span>'
                       f'<b>{_f(e2["value"], "{:.2f}")}</b><b>{_f(e2["rank"], "{:.0f}")}</b></div>' for e2 in e["factors"])
        rows.append(f'<div class="g"><span>{T.esc(e["label"][1 if is_ar() else 0])}<br><span class="w">{L("weight", "الوزن")} {e["weight"] * 100:.0f}%</span></span>'
                    f'<div class="bar"><i style="width:{pct:.0f}%;background:{GROUP_COLOR[e["group"]]}"></i></div><b>{_f(e["rank"], "{:.0f}")}</b>'
                    f'<b style="color:{_MU}">{_f(e["contribution"], "{:.1f}")}</b>'
                    f'<details><summary>{L("the factors", "العوامل")}</summary>{facs}</details></div>')
    head = L(f"Each group is a rank out of 100 across the scanned stocks; the weights are the {_method_name(method)} score's. Value, then rank.",
             f"كل مجموعة ترتيب من 100 بين الأسهم المفحوصة؛ والأوزان أوزان تقييم {_method_name(method)}. القيمة ثم الترتيب.")
    kinds = [("for", "thumb_up", L("What speaks for it", "ما يدعمها"), case["for"]), ("against", "thumb_down", L("What speaks against it", "ما يضعفها"), case["against"]),
             ("inv", "block", L("What would invalidate it", "ما يُبطلها"), case["invalidation"]), ("unc", "help", L("What is uncertain", "ما هو غير مؤكد"), case["uncertain"])]
    boxes = "".join(f'<div class="k {c}"><div class="t">{T.icon(ic)}{T.esc(t)}</div><ul>' + "".join(f"<li>{T.esc(x)}</li>" for x in items[:5]) + (
        f'<li style="color:{_MU}">{L("nothing stands out", "لا شيء بارز")}</li>' if not items else "") + "</ul></div>" for c, ic, t, items in kinds)
    return (f'<div class="h3box"><div class="h3bt">{T.icon("psychology")}{L("Why this opportunity?", "ليش هذي الفرصة؟")}</div>'
            f'<div class="h3why">{"".join(rows)}</div><div style="color:{_MU};font-size:.72rem;margin:8px 0 10px">{T.esc(head)}</div>'
            f'<div class="h3case">{boxes}</div></div>')


def plan_html(r, edge):
    """Entry, stop, target, R:R, size, max loss, holding period and the setup's measured expectancy on this stock."""
    acct, risk = float(ss.get("h3_acct") or 100_000), float(ss.get("h3_risk") or 0.75)
    entry, stop, tgt = float(r["Entry"]), float(r["Stop"]), float(r["Target"])
    watch = r["Tier"] == "watch"
    atr = float(r["ATR %"]) * float(r["Price"]) / 100
    n = H.size(entry, stop, acct, risk)
    tiles = [("en", L("Buy above", "شراء فوق") if watch else L("Entry", "الدخول"), _money_px(entry), L("on a close above it", "بإغلاق فوقه") if watch else L("next open, near this price", "الافتتاح القادم، قرب هذا السعر")),
             ("sl", L("Stop (invalidation)", "الوقف (الإبطال)"), _money_px(stop), f"{_pct(entry, stop):+.1f}% · {abs(entry - stop) / max(atr, 1e-9):.1f} ATR"),
             ("tp", L("Target", "الهدف"), _money_px(tgt), f"{_pct(entry, tgt):+.1f}%"),
             ("", "R:R", f"{r['R:R']:.1f} : 1" if np.isfinite(r["R:R"]) else "—", L("reward for each 1 of risk", "العائد لكل 1 مخاطرة")),
             ("", L("Position size", "حجم الصفقة"), f"{n:,} {L('sh', 'سهم')}", f"{_money_px(n * entry)} · {n * entry / acct * 100:.0f}% {L('of the account', 'من المحفظة')}"),
             ("", L("Max loss", "أقصى خسارة"), T.money(n * abs(entry - stop)), f"{risk:g}% {L('of', 'من')} {T.money(acct)}"),
             ("", L("Holding period", "مدة الاحتفاظ"), L(f"≤ {int(r['Hold'])} sessions", f"≤ {int(r['Hold'])} جلسة") if pd.notna(r.get("Hold")) else "—", L("then out at the close", "بعدها خروج عند الإغلاق"))]
    if edge:
        tiles.append(("", L("Expectancy (this stock)", "التوقع (هذا السهم)"), f"{edge['avg_r']:+.2f} R",
                      L(f"{edge['n']} past trades · win {edge['win']:.0f}% · PF {edge['pf']:.2f}", f"{edge['n']} صفقة سابقة · ربح {edge['win']:.0f}% · PF {edge['pf']:.2f}")))
    else:
        tiles.append(("", L("Expectancy (this stock)", "التوقع (هذا السهم)"), "—", L("no past trades of this setup here", "لا صفقات سابقة لهذه الفرصة هنا")))
    return '<div class="h3plan">' + "".join(f'<div class="p {c_}"><div class="l">{T.esc(l_)}</div><div class="v">{v_}</div><div class="s">{T.esc(s_)}</div></div>' for c_, l_, v_, s_ in tiles) + "</div>"


def risk_html(r, state):
    reg = state["regime"].iloc[-1]
    fit = {"bull": ("fits the regime", "تناسب حالة السوق", "#4ADE80"), "neutral": ("neutral regime: smaller size", "حالة عرضية: حجم أصغر", _G),
           "bear": ("against the regime", "ضد حالة السوق", "#F87171"), "stress": ("stress regime: most setups fail", "حالة اضطراب: أغلب الفرص تفشل", "#F87171")}[reg]
    liq = float(r["$Vol"])
    tiles = [("", L("Volatility (3M)", "التذبذب (3 أشهر)"), _f(r["vol_63"], "{:.0f}%"), L("annualised", "سنوي")),
             ("", L("VaR 95% (1 day)", "القيمة المعرضة للخطر 95%"), _f(r["var_95"], "{:.1f}%"), L("worst 1-in-20 day, last year", "أسوأ يوم من 20، آخر سنة")),
             ("", L("CVaR 95%", "متوسط الذيل 95%"), _f(r["cvar_95"], "{:.1f}%"), L("average of those worst days", "متوسط تلك الأيام الأسوأ")),
             ("", L("Drawdown (6M)", "التراجع (6 أشهر)"), _f(r["mdd_126"], "{:.1f}%"), L("from its 6-month high", "من قمة 6 أشهر")),
             ("", L("Beta", "بيتا"), _f(r["beta"], "{:.2f}"), L("against the index, 1 year", "مقابل المؤشر، سنة")),
             ("", L("Correlation (3M)", "الارتباط (3 أشهر)"), _f(r["corr_63"], "{:.2f}"), L("with the index", "مع المؤشر")),
             ("", L("Liquidity", "السيولة"), T.money(liq, short=True), L("traded a day (20-day average)", "تداول يومي (متوسط 20 يوم)") + (L(" · fading", " · تتراجع") if "liquidity" in str(r["Flags"]) else "")),
             ("", L("Regime compatibility", "التوافق مع حالة السوق"), f'<span style="color:{fit[2]}">{T.esc(L(fit[0], fit[1]))}</span>', T.esc(L(*brain.REGIME_LABEL[reg])))]
    return '<div class="h3plan">' + "".join(f'<div class="p {c_}"><div class="l">{T.esc(l_)}</div><div class="v">{v_}</div><div class="s">{s_}</div></div>' for c_, l_, v_, s_ in tiles) + "</div>"


@st.cache_data(ttl=3600, show_spinner=False)
def _infos(build=None):
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "infos.json"), encoding="utf-8") as f:
            return json.load(f).get("items", {})
    except Exception:
        return {}


def fundamentals_html(sym):
    it = _infos(H3.BUILD).get(sym)
    if not it:
        return ""
    g = lambda k: it.get(k)
    rows = [(L("Forward P/E", "مكرر الربحية المتوقع"), _f(g("forwardPE"), "{:.1f}")), (L("Trailing P/E", "مكرر الربحية الحالي"), _f(g("trailingPE"), "{:.1f}")),
            (L("EV / EBITDA", "قيمة المنشأة / الأرباح التشغيلية"), _f(g("enterpriseToEbitda"), "{:.1f}")),
            (L("Revenue growth", "نمو الإيرادات"), _f((g("revenueGrowth") or np.nan) * 100, "{:+.1f}%")), (L("Earnings growth", "نمو الأرباح"), _f((g("earningsGrowth") or np.nan) * 100, "{:+.1f}%")),
            (L("Gross margin", "هامش الربح الإجمالي"), _f((g("grossMargins") or np.nan) * 100, "{:.1f}%")), (L("Operating margin", "الهامش التشغيلي"), _f((g("operatingMargins") or np.nan) * 100, "{:.1f}%")),
            (L("Return on equity", "العائد على حقوق الملكية"), _f((g("returnOnEquity") or np.nan) * 100, "{:.1f}%")), (L("Debt / equity", "الدين / حقوق الملكية"), _f(g("debtToEquity"), "{:.0f}%")),
            (L("Free cash flow", "التدفق النقدي الحر"), T.money(g("freeCashflow"), short=True) if g("freeCashflow") else "—"),
            (L("Dividend yield", "عائد التوزيعات"), _f((g("dividendYield") or np.nan) * (1 if (g("dividendYield") or 0) > 1 else 100), "{:.2f}%"))]
    asof = it.get("_asof") or ""
    body = "".join(f'<tr><td>{T.esc(a)}</td><td class="n">{b}</td></tr>' for a, b in rows)
    return (f'<div class="h3box"><div class="h3bt">{T.icon("account_balance")}{L("Fundamentals snapshot", "لقطة الأساسيات")}</div>'
            f'<div class="h3wrap"><table class="h3tbl">{body}</table></div>'
            f'<div class="h3note warn" style="margin-top:8px">{T.esc(L(f"Today's snapshot ({asof}), not point-in-time history: shown for context only and NOT part of the score or the tests.", f"لقطة اليوم ({asof}) وليست تاريخاً كما كان: للسياق فقط وليست جزءاً من التقييم أو الاختبارات."))}</div></div>')


def sector_context_html(r, res):
    sec = r["Sector"]
    if not sec:
        return ""
    peers = res[res["Sector"] == sec]
    by_sec = res.groupby("Sector")["ret_63"].mean().sort_values(ascending=False)
    rank = int(list(by_sec.index).index(sec)) + 1 if sec in by_sec.index else None
    within = int((peers["Score"] > r["Score"]).sum()) + 1
    lead = peers.sort_values("Score", ascending=False).head(5)
    items = "".join(f'<div class="r{" both" if s == r["Symbol"] else ""}"><span>{T.esc(T.sym_label(s))}</span><b>{sc:.0f}</b></div>' for s, sc in zip(lead["Symbol"], lead["Score"]))
    return (f'<div class="h3box"><div class="h3bt">{T.icon("category")}{L("Sector context", "سياق القطاع")}</div>'
            f'<div style="font-size:.84rem;color:#D9D4E0;line-height:1.55">{T.esc(sector_name(sec))}: '
            f'{T.esc(L(f"sector #{rank} of {len(by_sec)} by 3-month return ({_f(by_sec.get(sec), "{:+.1f}%")}); this stock is #{within} of {len(peers)} in its sector by score.", f"القطاع رقم {rank} من {len(by_sec)} بعائد 3 أشهر ({_f(by_sec.get(sec), "{:+.1f}%")})؛ وهذا السهم رقم {within} من {len(peers)} في قطاعه بالتقييم."))}</div>'
            f'<div class="h3cmp" style="margin-top:8px"><div class="m">{items}</div></div></div>')


def detail(r, got, method, res):
    sym, k = r["Symbol"], r["Setup"]
    state, groups, panel = got["state"], got["groups"], got["panel"]
    with st.container(key=f"h3sec_head_{PS._key(sym)}"):
        badges = T.badge(sector_name(r["Sector"]) if r["Sector"] else "—", "gold", "category")
        if k in H.SETUPS:
            badges += T.badge(PS.setup_name(k) + " · " + L(*H3.TIER[r["Tier"]]), TIER_KIND[r["Tier"]], H.SETUPS[k][2])
        for s_ in str(r["Setups"]).split(","):
            if s_ and s_ != k and s_ in H.SETUPS:
                badges += T.badge(PS.setup_name(s_), "neu", H.SETUPS[s_][2])
        for ic_, txt, kind in flags_of(r):
            badges += T.badge(txt, kind, ic_)
        nm_ = T.sym_label(sym)
        ui.html(f'<div class="card h3dh"><a class="co" href="{T.esc(ui.href(sym))}" target="_self" title="{T.esc(L(f"Open the {nm_} page", f"افتح صفحة {nm_}"))}">'
                f'{T.logo_obj(sym, 48)}<div class="nm"><b>{T.esc(nm_)}</b><span>{T.esc(T.name_line(sym, str(r["Name"])))}</span></div></a>'
                f'{PS.ring(r["Score"], r["Grade"], 62)}<div class="bd">{badges}</div><div class="px"><b>{_money_px(r["Price"])}</b>{T.pill(r["Chg %"])}</div></div>')
        if k in H.SETUPS:
            ui.html(f'<div class="h3note" style="margin-top:10px">{T.icon(H.SETUPS[k][2], CYA)} <b>{T.esc(PS.setup_name(k))}:</b> {T.esc(L(H.SETUPS[k][6], H.SETUPS[k][7]))}</div>')
    d, spy5 = PS._history5(sym, H.BUILD)
    edge, bt = PS._edge(sym, k, H.BUILD) if k else (None, pd.DataFrame())
    with st.container(key=f"h3sec_body_{PS._key(sym)}"):
        left, right = st.columns([1.6, 1], gap="medium")
        with left:
            if d is not None:
                levels = ([(L("Entry", "دخول"), r["Entry"], _A, "solid"), (L("Stop", "وقف"), r["Stop"], _D, "dash"), (L("Target", "هدف"), r["Target"], _U, "dash")]
                          if np.isfinite(r["Entry"]) else None)
                ui.chart(charts.price_chart(d.tail(190), "Candles", ["SMA 20", "SMA 50", "SMA 200"], [], False, levels=levels, height=440), key=f"h3_chart_{PS._key(sym)}")
            ui.sec("flag", "Trade plan", "خطة التداول")
            ui.html(plan_html(r, edge))
            ui.sec("shield", "Risk profile", "ملف المخاطر")
            ui.html(risk_html(r, state))
        with right:
            case = H3.why(r, panel, method, groups, state, ar=is_ar())
            ui.html(why_html(case, method))
            if edge and len(bt):
                last = bt.tail(6).iloc[::-1]
                rows = "".join(f'<tr><td>{pd.Timestamp(t["Entry Date"]).strftime("%Y-%m-%d")}</td><td class="n">{_money_px(t["Entry"])}</td><td class="n" style="color:{"#4ADE80" if t["R"] > 0 else "#F87171"}">{t["R"]:+.2f} R</td><td>{T.esc(str(t["Reason"]))}</td></tr>' for _, t in last.iterrows())
                ui.html(f'<div class="h3box"><div class="h3bt">{T.icon("history")}{L("The same setup on this stock, last 5 years", "نفس الفرصة على هذا السهم، آخر 5 سنوات")}</div>'
                        f'<div style="font-size:.82rem;color:#D9D4E0;margin-bottom:6px">{T.esc(L(f"{edge["n"]} trades · win rate {edge["win"]:.0f}% · average {edge["avg_r"]:+.2f} R · profit factor {edge["pf"]:.2f}", f"{edge["n"]} صفقة · نسبة الربح {edge["win"]:.0f}% · المتوسط {edge["avg_r"]:+.2f} R · عامل الربح {edge["pf"]:.2f}"))}</div>'
                        f'<div class="h3wrap"><table class="h3tbl"><tr><th>{L("Entered", "الدخول")}</th><th class="n">{L("Price", "السعر")}</th><th class="n">R</th><th>{L("Exit", "الخروج")}</th></tr>{rows}</table></div></div>')
            ui.html(sector_context_html(r, res))
            ui.html(fundamentals_html(sym))


# ---------------------------------------------------------------- factor breakdown, comparison, portfolio
def _heat(v, lo=0, hi=100):
    if v is None or not np.isfinite(v):
        return f'<span class="cell" style="background:rgba(157,151,165,.18);color:{_MU}">—</span>'
    t = float(np.clip((v - lo) / (hi - lo), 0, 1))
    r_, g_, b_ = (int(a + (b - a) * t) for a, b in ((248, 134), (113, 239), (113, 172)))        # red -> green
    return f'<span class="cell" style="background:rgb({r_},{g_},{b_})">{v:.0f}</span>'


def factor_table(view, methods):
    top = view.head(20)
    head = "".join(f'<th class="c">{T.esc(L(en, ar_))}</th>' for en, ar_, _ in H3.GROUPS.values())
    mh = "".join(f'<th class="n">{T.esc(_method_name(m))}</th>' for m in methods)
    rows = []
    for _, r in top.iterrows():
        cells = "".join(f'<td class="c">{_heat(r.get(f"g_{g}"))}</td>' for g in H3.GROUPS)
        ms = "".join(f'<td class="n">{_f(r.get(f"score_{m}"), "{:.0f}")}</td>' for m in methods)
        rows.append(f'<tr><td><span class="sym">{T.esc(T.sym_label(r["Symbol"]))}<small>{T.esc(str(r["Name"])[:22])}</small></span></td>'
                    f'<td>{tier_tag(r["Tier"])}</td><td>{T.esc(PS.short_name(r["Setup"]))}</td>{cells}<td class="n">{_f(r["R:R"], "{:.1f}")}</td><td class="n">{int(r["RS"])}</td>{ms}</tr>')
    ui.html(f'<div class="h3wrap"><table class="h3tbl"><tr><th>{L("Stock", "السهم")}</th><th>{L("Tier", "المستوى")}</th><th>{L("Setup", "الفرصة")}</th>{head}<th class="n">R:R</th><th class="n">RS</th>{mh}</tr>'
            + "".join(rows) + "</table></div>")


def comparison(res, methods, ev):
    """The eight best under every score next to each other, with the agreement between the scores."""
    base = res[res["Side"] > 0]
    if base.empty:
        return
    tops = {m: list(base.sort_values(f"score_{m}", ascending=False).head(N_CARDS)["Symbol"]) for m in methods}
    ref = set(tops.get("v1", []))
    boxes = []
    for m in methods:
        st_ = method_status(ev, m)
        tag = {"recommended": ("ok", L("better", "أفضل")), "not better": ("no", L("not better", "ليس أفضل")), "rejected": ("rej", L("rejected", "مرفوض")),
               "baseline": ("no", L("baseline", "الأساس")), None: ("no", L("untested", "بلا اختبار"))}[st_]
        rows = "".join(f'<div class="r{" both" if (m != "v1" and s in ref) else ""}"><span>{T.esc(T.sym_label(s))}</span><b>{base.set_index("Symbol").at[s, f"score_{m}"]:.0f}</b></div>' for s in tops[m])
        same = len(set(tops[m]) & ref)
        sub = "" if m == "v1" else f'<div style="color:{_MU};font-size:.72rem;margin-top:6px">{T.esc(L(f"{same} of {N_CARDS} also in the baseline's eight", f"{same} من {N_CARDS} موجودة أيضاً في ثمانية الأساس"))}</div>'
        boxes.append(f'<div class="m"><div class="t">{T.icon("functions")}{T.esc(_method_name(m))}<span class="tag {tag[0]}">{T.esc(tag[1])}</span></div>{rows}{sub}</div>')
    ui.html(f'<div class="h3cmp">{"".join(boxes)}</div>')
    if len(methods) > 1 and len(base) >= 8:
        sc = base[[f"score_{m}" for m in methods]]
        corr = sc.corr(method="spearman")
        pairs = ", ".join(f"{_method_name(a)} × {_method_name(b)}: {corr.iloc[i, j]:.2f}" for i, a in enumerate(methods) for j, b in enumerate(methods) if j > i)
        st.caption(L(f"Rank agreement between the scores (Spearman, {len(base)} stocks with a buying setup): {pairs}.",
                     f"توافق الترتيب بين التقييمات (سبيرمان، {len(base)} سهم بفرصة شراء): {pairs}."))


def portfolio(view, got):
    panel, state = got["panel"], got["state"]
    reg = state["regime"].iloc[-1]
    acct, risk = float(ss.get("h3_acct") or 100_000), float(ss.get("h3_risk") or 0.75)
    cands = view.head(30)
    if cands.empty:
        return
    pos, summ = H3.build_portfolio(cands, panel, capital=acct, risk_pct=risk, max_pos=8, sector_cap=2, max_corr=0.75, regime=reg)
    stress = summ["stress"]
    tiles = [("", L("Invested", "المستثمر"), f"{summ['invested_pct']:.0f}%", L(f"cap {summ['exposure_cap_pct']:.0f}% in a {brain.REGIME_LABEL[reg][0].lower()}", f"الحد {summ['exposure_cap_pct']:.0f}% في {brain.REGIME_LABEL[reg][1]}")),
             ("", L("Cash", "النقد"), T.money(summ["cash"]), L(f"of {T.money(acct)}", f"من {T.money(acct)}")),
             ("", L("Positions", "المراكز"), f"{summ['positions']}", L("max 8 · 2 per sector · correlation ≤ 0.75", "حد أقصى 8 · 2 لكل قطاع · ارتباط ≤ 0.75")),
             ("", L("Book beta", "بيتا المحفظة"), f"{summ['book_beta']:.2f}", L("weighted by position size", "موزونة بحجم المراكز")),
             ("sl", L("Risk at the stops", "المخاطرة عند الوقف"), f"{summ['risk_at_stops_pct']:.2f}%", L("of the account if every stop hits", "من المحفظة لو ضُربت كل الوقوف")),
             ("sl", L("Stress: index −10%", "ضغط: المؤشر −10%"), f"{stress['spy_10']:+.1f}%", L(f"−5%: {stress['spy_5']:+.1f}% · −20%: {stress['spy_20']:+.1f}% (beta model)", f"−5%: {stress['spy_5']:+.1f}% · −20%: {stress['spy_20']:+.1f}% (نموذج بيتا)"))]
    ui.html('<div class="h3plan">' + "".join(f'<div class="p {c_}"><div class="l">{T.esc(l_)}</div><div class="v">{v_}</div><div class="s">{T.esc(s_)}</div></div>' for c_, l_, v_, s_ in tiles) + "</div>")
    if len(pos):
        rows = "".join(f'<tr><td><span class="sym">{T.esc(T.sym_label(p["Symbol"]))}</span></td><td>{T.esc(sector_name(p["Sector"]))}</td><td class="n">{int(p["Shares"]):,}</td>'
                       f'<td class="n">{_money_px(p["Entry"])}</td><td class="n">{_money_px(p["Stop"])}</td><td class="n">{_money_px(p["Target"]) if np.isfinite(p["Target"]) else "—"}</td>'
                       f'<td class="n">{T.money(p["Notional"])}</td><td class="n">{p["Weight %"]:.1f}%</td><td class="n">{p["Risk %"]:.2f}%</td><td class="n">{_f(p["Vol %"], "{:.0f}%")}</td><td class="n">{_f(p["Beta"], "{:.2f}")}</td></tr>'
                       for _, p in pos.iterrows())
        ui.html(f'<div class="h3wrap"><table class="h3tbl"><tr><th>{L("Stock", "السهم")}</th><th>{L("Sector", "القطاع")}</th><th class="n">{L("Shares", "الأسهم")}</th><th class="n">{L("Entry", "الدخول")}</th>'
                f'<th class="n">{L("Stop", "الوقف")}</th><th class="n">{L("Target", "الهدف")}</th><th class="n">{L("Value", "القيمة")}</th><th class="n">{L("Weight", "الوزن")}</th><th class="n">{L("Risk", "المخاطرة")}</th>'
                f'<th class="n">{L("Vol", "التذبذب")}</th><th class="n">Beta</th></tr>{rows}</table></div>')
    if summ["skipped"]:
        st.caption(L("Skipped: ", "تم تخطي: ") + ", ".join(f"{s} ({why})" for s, why in summ["skipped"][:8]))
    st.caption(L("A paper book: sizes are the smaller of the risk budget, the volatility budget (18% a year split over 8) and 20% of the account; no orders are sent anywhere.",
                 "محفظة افتراضية: الحجم هو الأصغر بين ميزانية المخاطرة وميزانية التذبذب (18% سنوياً موزعة على 8) و20% من المحفظة؛ ولا تُرسل أوامر لأي مكان."))


# ---------------------------------------------------------------- strategy research
def _ic_cell(x):
    if not x or x.get("ic_mean") is None:
        return "—"
    v = x["ic_mean"]
    col = "#4ADE80" if v > 0.02 else "#F87171" if v < -0.02 else "#E5E1EB"
    return f'<span style="color:{col}">{v:+.3f}</span> <small style="color:{_MU}">t {x.get("ic_t", "—")}</small>'


def research(ev):
    if not ev:
        st.info(L("The historical tests have not been run yet (Actions > hunter 3.0 runs them on real prices and commits the results).",
                  "الاختبارات التاريخية لم تُشغّل بعد (Actions > hunter 3.0 يشغلها على أسعار حقيقية ويحفظ النتائج)."), icon=":material/science:")
        return
    run, v = ev["run"], ev.get("verdict", {})
    methods = [m for m in ev["methods"] if m != "random"]
    cost = run["cost"]
    ui.html(f'<div class="h3ver">{T.icon("gavel")}<div><b>{T.esc(L("Verdict", "الحكم"))}: {T.esc(L(f"the page ranks by {_method_name(v.get("default", "v1"))} by default.", f"الصفحة ترتب حسب {_method_name(v.get("default", "v1"))} افتراضياً."))}</b>'
            f'<p>{T.esc(L("A new score replaces the old Hunter only when it beats it on both rank IC and Sharpe in most out-of-sample periods (2020 on). ", "التقييم الجديد يحل محل الصياد القديم فقط إذا تفوق عليه في ترتيب IC وشارب معاً في أغلب الفترات خارج العينة (من 2020). "))}'
            + " ".join(f"<b>{_method_name(m)}</b>: " + T.esc({"recommended": L("better", "أفضل"), "not better": L("not better", "ليس أفضل"), "rejected": L("rejected", "مرفوض")}.get(row["status"], row["status"]))
                       + (T.esc(L(f" (IC {row['beats_v1_ic']}/{row['periods']}, Sharpe {row['beats_v1_sharpe']}/{row['periods']})", f" (IC {row['beats_v1_ic']}/{row['periods']}، شارب {row['beats_v1_sharpe']}/{row['periods']})")) if "periods" in row else "") + "."
                       for m, row in v.get("methods", {}).items())
            + f'</p><p style="color:{_MU}">{T.esc(L(f"Measured on {run["date"]} on GitHub Actions: {run["symbols"]} symbols, daily bars from 2005, costs {cost["commission_bps"] + cost["half_spread_bps"] + cost["slippage_bps"]:.0f} bps a side, fills at the next open, {run["seconds"]} s.", f"قيست في {run["date"]} على GitHub Actions: {run["symbols"]} رمز، شموع يومية من 2005، تكاليف {cost["commission_bps"] + cost["half_spread_bps"] + cost["slippage_bps"]:.0f} نقطة أساس لكل جانب، تنفيذ عند الافتتاح التالي، {run["seconds"]} ث."))}</p></div></div>')
    periods = list(ev["sim"])
    # 1) ranking quality
    ui.html(f'<div class="h3bt" style="margin-top:6px">{T.icon("leaderboard")}{L("Ranking quality: rank IC against the next month's return over the index, among stocks with a live setup", "جودة الترتيب: معامل IC مقابل عائد الشهر التالي فوق المؤشر، بين الأسهم ذات الفرصة الحية")}</div>')
    head = "".join(f'<th class="n">{T.esc(_method_name(m))}</th>' for m in methods)
    rows = "".join(f'<tr><td>{T.esc(p)}</td>' + "".join(f'<td class="n">{_ic_cell(ev["ic"]["candidates"].get(m, {}).get(p))}</td>' for m in methods) + "</tr>" for p in periods)
    ui.html(f'<div class="h3wrap"><table class="h3tbl"><tr><th>{L("Period", "الفترة")}</th>{head}</tr>{rows}</table></div>')
    st.caption(L("IC near zero means the score barely orders next month's winners; t over 2 would be a statistically clear signal. None of the scores reaches that in any period.",
                 "IC قريب من الصفر يعني أن التقييم بالكاد يرتب رابحي الشهر التالي؛ t فوق 2 كان سيكون إشارة واضحة إحصائياً. لا يصل أي تقييم لذلك في أي فترة."))
    # 2) the simulation
    ui.html(f'<div class="h3bt" style="margin-top:10px">{T.icon("candlestick_chart")}{L("Trading simulation (same portfolio rules for every score; random = the same rules on a random order, the control)", "محاكاة التداول (نفس قواعد المحفظة لكل تقييم؛ random = نفس القواعد بترتيب عشوائي، الضابط)")}</div>')
    p = st.selectbox(L("Period", "الفترة"), periods, index=len(periods) - 1, key="h3_period")
    sim = ev["sim"].get(p, {})
    cols = [("cagr", "CAGR", "{:+.1f}%"), ("sharpe", "Sharpe", "{:.2f}"), ("sortino", "Sortino", "{:.2f}"), ("max_drawdown", L("Max DD", "أقصى تراجع"), "{:.1f}%"), ("calmar", "Calmar", "{:.2f}"),
            ("profit_factor", "PF", "{:.2f}"), ("expectancy_R", L("Expect. R", "التوقع R"), "{:+.2f}"), ("win_rate", L("Win", "ربح"), "{:.0f}%"), ("trades", L("Trades", "صفقات"), "{:.0f}"),
            ("alpha_annual", "Alpha", "{:+.1f}%"), ("beta", "Beta", "{:.2f}"), ("information_ratio", "IR", "{:.2f}"), ("turnover_per_year", L("Turnover", "الدوران"), "{:.1f}"), ("exposure", L("Exposure", "التعرض"), "{:.0f}%")]
    pct = {"cagr", "max_drawdown", "win_rate", "alpha_annual", "exposure"}
    head = "".join(f'<th class="n">{T.esc(str(lab))}</th>' for _, lab, _ in cols)
    best = {k: max((d.get(k) for m, d in sim.items() if m not in ("SPY",) and d.get(k) is not None), default=None) for k in ("sharpe", "cagr")}
    rows = []
    for m, d in sim.items():
        tds = []
        for k, _, fmt in cols:
            x = d.get(k)
            x = x * 100 if (x is not None and k in pct and abs(x) <= 1.5 and k != "exposure") else x
            if k == "exposure" and x is not None and x <= 1.5:
                x = x * 100
            cls = " best" if (k in best and best[k] is not None and d.get(k) == best[k] and m != "SPY") else ""
            tds.append(f'<td class="n{cls}">{_f(x, fmt)}</td>')
        rows.append(f'<tr><td><b>{T.esc(_method_name(m) if m in METHOD else m)}</b></td>{"".join(tds)}</tr>')
    ui.html(f'<div class="h3wrap"><table class="h3tbl"><tr><th>{L("Score", "التقييم")}</th>{head}</tr>{"".join(rows)}</table></div>')
    ci = {m: d.get("cagr_ci90") for m, d in sim.items() if d.get("cagr_ci90")}
    if ci:
        st.caption(L("90% confidence intervals of the CAGR (bootstrap of monthly returns): ", "فترات ثقة 90% لمعدل النمو السنوي (إعادة عيّنة شهرية): ")
                   + " · ".join(f"{_method_name(m) if m in METHOD else m} {c[0] * 100 if abs(c[0]) <= 1.5 else c[0]:+.1f}% … {c[1] * 100 if abs(c[1]) <= 1.5 else c[1]:+.1f}%" for m, c in ci.items()))
    # 3) the equity curves
    em = ev.get("equity_monthly", {})
    if em:
        fig = go.Figure()
        start = "2016-01-01"
        spy = pd.Series(ev.get("spy_monthly", {}))
        spy.index = pd.to_datetime(spy.index)
        spy = spy.loc[start:]
        if len(spy):
            fig.add_scatter(x=spy.index, y=spy / spy.iloc[0] * 100, name=MK.get()["bench"] if not MK.is_sa() else "SPY", line=dict(color=_MU, width=1.5, dash="dot"))
        palette = {"v1": LAV, "quant": CYA, "adaptive": "#86EFAC", "ml": "#FDE68A", "random": "#FCA5A5"}
        for m, curve in em.items():
            s = pd.Series(curve)
            s.index = pd.to_datetime(s.index)
            s = s.loc[start:]
            if len(s):
                fig.add_scatter(x=s.index, y=s / s.iloc[0] * 100, name=_method_name(m) if m in METHOD else m, line=dict(color=palette.get(m, "#fff"), width=2))
        charts.style(fig, 360, L("Simulated equity from 2016, rebased to 100 (monthly points, after costs)", "رأس المال المحاكى من 2016، مُعاد ضبطه إلى 100 (نقاط شهرية، بعد التكاليف)"))
        ui.chart(fig, key="h3_equity")
    # 4) ablations and the ML model
    ab = ev.get("ablation", {})
    if ab:
        ui.html(f'<div class="h3bt" style="margin-top:6px">{T.icon("science")}{L("Ablations (one portfolio rule removed at a time, 2016 on)", "إزالة قاعدة واحدة كل مرة (من 2016)")}</div>')
        rows = "".join(f'<tr><td>{T.esc(k)}</td><td class="n">{_f(d.get("cagr", 0) * 100 if abs(d.get("cagr", 0)) <= 1.5 else d.get("cagr"), "{:+.1f}%")}</td><td class="n">{_f(d.get("sharpe"), "{:.2f}")}</td>'
                       f'<td class="n">{_f(d.get("max_drawdown", 0) * 100 if abs(d.get("max_drawdown", 0)) <= 1.5 else d.get("max_drawdown"), "{:.1f}%")}</td><td class="n">{_f(d.get("trades"), "{:.0f}")}</td></tr>' for k, d in ab.items())
        ui.html(f'<div class="h3wrap"><table class="h3tbl"><tr><th>{L("Variant", "النسخة")}</th><th class="n">CAGR</th><th class="n">Sharpe</th><th class="n">{L("Max DD", "أقصى تراجع")}</th><th class="n">{L("Trades", "صفقات")}</th></tr>{rows}</table></div>')
    ml = ev.get("ml", {})
    if ml:
        txt = (L(f"ML ranker: trained walk-forward by year from 2016 with a 21-session embargo; out-of-sample IC {ml.get('ic_2016_2024')} against the adaptive score's {ml.get('adaptive_ic_2016_2024')} → {'ACTIVE' if ml.get('active') else 'NOT USED'}.",
                 f"مرتّب التعلم الآلي: دُرّب زمنياً سنة بسنة من 2016 مع حظر 21 جلسة؛ IC خارج العينة {ml.get('ic_2016_2024')} مقابل {ml.get('adaptive_ic_2016_2024')} للتقييم المتكيف ← {'مفعّل' if ml.get('active') else 'غير مستخدم'}."))
        ui.html(f'<div class="h3note" style="margin-top:8px">{T.icon("smart_toy", LAV)} {T.esc(txt)}</div>')
    ui.html(f'<div class="h3note warn" style="margin-top:8px">{T.esc(L("What this does not show: today's constituents only (survivorship), no earnings dates in the history, fundamentals not point-in-time, prices from Yahoo. A score is a rank, never a probability: 90/100 is not a 90% chance.", "ما لا تُظهره: مكونات اليوم فقط (انحياز البقاء)، لا تواريخ أرباح في التاريخ، الأساسيات ليست كما كانت، والأسعار من ياهو. التقييم ترتيب وليس احتمالاً: 90 من 100 ليست فرصة 90%."))}</div>')


# ---------------------------------------------------------------- the page
def page_hunter3():
    ui.html(CSS)
    ev = evidence(H3.BUILD)
    _init(ev)
    unis = PS.universes()
    key, base = PS._base(unis)
    symbols, secs, inds = PS._narrow(base)
    got = None
    if symbols:
        with st.spinner(L(f"Hunting in {len(symbols)} stocks...", f"جاري الصيد في {len(symbols)} سهم...")):
            try:
                got = _scan(key, symbols, ss.get("h3_nonce", 0), H3.BUILD, MK.current(), is_ar())
            except Exception:
                got = None
    methods = got["methods"] if got else ["v1", "quant", "adaptive"]
    method = ss.get("h3_method") if ss.get("h3_method") in methods else default_method(ev)
    label = unis[key][0] + (f" · {PS.sector_label(ss['hn_sec'])}" if ss.get("hn_sec", "all") != "all" else "")
    res = ranked(got, method) if got and len(got["res"]) else pd.DataFrame()
    view = apply(res) if len(res) else pd.DataFrame()
    ui.html(hero_html(got, view, label, method, ev))
    hunt_bar(unis, secs, inds, len(symbols), methods, ev)
    if not symbols:
        st.info(L("Type at least one symbol.", "اكتب رمز واحد على الأقل."), icon=":material/info:")
        ui.foot()
        return
    if got is None or res.empty:
        st.warning(L("No price data came back. Try again in a minute, or check the symbols.", "ما وصلت بيانات أسعار. حاول بعد دقيقة، أو تأكد من الرموز."), icon=":material/error:")
        ui.foot()
        return
    if ss.get("h3_method") != method:
        ss["h3_method"] = method
    PS.LAST_HUNT[(key, MK.current())] = {"res": res, "n": got["n"], "asked": got["asked"], "time": got["time"], "last": got["last"], "earn": got["earn"]}   # the home page's card shows these picks
    # 1) market intelligence
    with st.container(key="h3sec_market"):
        ui.sec("explore", "Market Intelligence", "ذكاء السوق")
        ui.safe(lambda: ui.html(market_html(got["state"], got)))
        if got["n"] < 30:
            st.caption(L("A short list: breadth, correlation and the ranks mean more with a bigger universe.", "قائمة قصيرة: الاتساع والارتباط والترتيب أدق مع نطاق أكبر."))
        a, b = st.columns([1, 1.4], gap="medium")
        with a:
            ui.safe(lambda: ui.html(regime_ribbon(got["state"])))
        with b:
            ui.safe(sector_rotation, res)
    # 2) opportunity discovery
    with st.container(key="h3sec_filters"):
        ui.sec("target", f"Opportunity Discovery ({len(view)})", f"اكتشاف الفرص ({len(view)})")
        ui.safe(filters, res)
    if view.empty:
        st.info(L("Nothing matches these filters. Lower the grade, widen the tiers, or scan a bigger universe.", "ما فيه شي يطابق هالتصفية. نزّل الدرجة، أو وسّع المستويات، أو افحص نطاق أكبر."), icon=":material/search_off:")
    else:
        if ss.get("h3_sel") not in set(view["Symbol"]):
            ss["h3_sel"] = view["Symbol"].iloc[0]
        with st.container(key="h3sec_cards"):
            ui.safe(cards, view, got["panel"])
        r = view[view["Symbol"] == ss["h3_sel"]].iloc[0]
        with st.container(key="h3sec_detail"):
            ui.sec("manage_search", "Opportunity Detail", "تفاصيل الفرصة")
            ui.safe(detail, r, got, method, res)
        with st.container(key="h3sec_factors"):
            ui.sec("grid_view", "Factor Breakdown", "تفصيل العوامل")
            ui.safe(factor_table, view, methods)
            st.caption(L("Each cell: the stock's rank out of 100 among the scanned stocks on that factor group (green high, red low). The last columns are its score under each method.",
                         "كل خلية: ترتيب السهم من 100 بين الأسهم المفحوصة في تلك المجموعة (أخضر عالٍ، أحمر منخفض). الأعمدة الأخيرة تقييمه تحت كل طريقة."))
        with st.container(key="h3sec_portfolio"):
            ui.sec("account_balance_wallet", "Portfolio (paper, risk-aware)", "المحفظة (افتراضية، بوعي للمخاطر)")
            ui.safe(portfolio, view, got)
    with st.container(key="h3sec_compare"):
        ui.sec("compare_arrows", "Comparison of the scores", "مقارنة التقييمات")
        ui.safe(comparison, res, methods, ev)
    with st.container(key="h3sec_research"):
        ui.sec("science", "Strategy Research", "أبحاث الاستراتيجية")
        ui.safe(research, ev)
    with st.expander(L("How Hunter 3.0 works", "كيف يشتغل الصياد 3.0"), icon=":material/help:"):
        ui.html('<div class="h3note">' + L(
            "<b>Setups</b> are the Opportunity Hunter's exact rules on the daily close; a stock without a buying setup can't pass 49 under any score. "
            "<b>Tiers</b>: actionable (fired on the latest candle), developing (fired in the last sessions and the price is still between stop and target), watchlist (building). "
            "<b>Factor groups</b>: momentum (volatility-adjusted 3-12 month returns, relative and residual strength, acceleration), trend (structure, efficiency, stability, distance from the high), "
            "volume (up/down volume, accumulation, dollar-volume trend, imbalance, relative volume), risk (volatility, drawdown, tail loss, volatility shock, beta: lower is better), "
            "setup (the setup's quality and reward-to-risk). Each is ranked across the scanned stocks, 0-100. <b>Scores</b>: the baseline is the Hunter's own; the multi-factor score "
            "weights the groups 30/20/15/15/20; the adaptive score uses weights fitted per regime on 2010-2015; the ML ranker is on only when its walk-forward test beat the adaptive score. "
            "<b>Regime</b>: trend, breadth and volatility of the index; it caps the paper book's exposure (100/70/35/20%). Fundamentals are a snapshot and take no part in the scores.",
            "<b>الفرص</b> هي قواعد صائد الفرص الدقيقة على الإغلاق اليومي؛ والسهم بدون فرصة شراء ما يتعدى 49 تحت أي تقييم. "
            "<b>المستويات</b>: قابلة للتنفيذ (ظهرت على آخر شمعة)، تتكوّن (ظهرت في الجلسات الأخيرة والسعر لسا بين الوقف والهدف)، مراقبة (تتشكل). "
            "<b>مجموعات العوامل</b>: الزخم (عوائد 3-12 شهر معدلة بالتذبذب، القوة النسبية والمتبقية، التسارع)، الاتجاه (البنية، الكفاءة، الثبات، البعد عن القمة)، "
            "الحجم (حجم الصعود/الهبوط، التجميع، اتجاه قيمة التداول، الاختلال، الحجم النسبي)، المخاطرة (التذبذب، التراجع، خسارة الذيل، صدمة التذبذب، بيتا: الأقل أفضل)، "
            "الفرصة (جودة الفرصة والعائد مقابل المخاطرة). كل مجموعة تُرتّب بين الأسهم المفحوصة من 0 إلى 100. <b>التقييمات</b>: الأساس تقييم الصياد نفسه؛ متعدد العوامل يوزن المجموعات 30/20/15/15/20؛ "
            "المتكيف يستخدم أوزاناً مضبوطة لكل حالة سوق على 2010-2015؛ ومرتّب التعلم الآلي يعمل فقط إذا تفوق في اختباره الزمني على المتكيف. "
            "<b>حالة السوق</b>: اتجاه المؤشر واتساعه وتذبذبه؛ وتحدد سقف تعرض المحفظة الافتراضية (100/70/35/20%). الأساسيات لقطة ولا تدخل في التقييمات.") + "</div>")
    st.caption(L("Daily prices from Yahoo Finance (may be delayed). A research tool, not investment advice: scores are ranks, the tests are simulations, and nothing here sends an order anywhere.",
                 "أسعار يومية من ياهو فاينانس (قد تكون متأخرة). أداة بحث وليست نصيحة استثمارية: التقييمات ترتيب، والاختبارات محاكاة، ولا شيء هنا يرسل أمراً لأي مكان."))
    ui.foot()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "23.4.41"
