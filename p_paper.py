"""
p_paper.py - Paper Bots: up to 5 bots that trade with virtual money on real prices, forward from the day they start.
Each bot trades one company, a sector, an industry or all companies, with one or more Strategy Lab strategies (buying
stocks, options, or both side by side) or with "combined strategies": complete setups written as exact numeric rules
(playbooks.py), each with its own stop, target and time stop; the Opening Range Breakout trades 5-minute candles.

Page, top to bottom:
  * a hero in the site's colours: the bots as five slots on the brand's rising cyan line, with the totals as chips,
  * one card per bot (hover = zoom + a pencil to edit on the right + a red trash on the left; click = select, blue top line)
    and an "Add Bot" card of the same size,
  * for the selected bots only (Select all selects every bot): a dashboard first (KPIs, the win-rate / profit-factor cards,
    what worked by stock and by strategy), the open positions, the recent trades ("Full list below" jumps to All trades),
    the charts, the monthly returns (click a month to open its calendar) and all trades. Several selected bots also get a
    combined dashboard, the "Return since start" chart and one tab per bot.
Every bot has two phases, shown apart by the switch under the hero: its FORWARD TEST (LIVE), recorded session by session
after each close and never recalculated, and its HISTORICAL SIMULATION (SIM), a backtest from its start date up to the day
the forward test began, recalculated with the current engine (see paperbots.py).
Adding, editing and deleting open in dialogs; a password unlocks them when BOTS_PASSWORD is set.
"""
import json
from datetime import datetime, timedelta
from math import hypot
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import streamlit as st

import autotrader
import charts
import data
import engine
import mcal
import paperbots as PB
import playbooks as PBK
import lab
import mlbots as MLB
import ta
import tdash
import theme as T
import ui
from i18n import L, is_ar, sector_name
from sp500 import gics_name

ss = st.session_state
KIND_LABEL = {"company": ("One company", "شركة"), "sector": ("A sector", "قطاع"), "industry": ("An industry", "صناعة"),
              "all": ("All companies", "كل الشركات")}
KIND_ICON = {"company": "domain", "sector": "category", "industry": "factory", "all": "public"}
OVERLAYS = {"SMA Crossover": ["SMA 20", "SMA 50"], "Golden Cross (50/200)": ["SMA 50", "SMA 200"],
            "EMA Crossover": ["EMA 9", "EMA 21"], "Bollinger Breakout": ["Bollinger Bands"],
            PBK.TREND_PULLBACK: ["EMA 20", "SMA 50", "SMA 200"], PBK.BREAKOUT_RETEST: ["SMA 50"],
            PBK.SQUEEZE: ["Bollinger Bands", "SMA 50"], PBK.RANGE: ["Bollinger Bands"]}
PANELS = {"RSI Mean Reversion": ["RSI"], "MACD Crossover": ["MACD"], "OBV Trend (Volume)": ["OBV"], "MFI Money Flow (Volume)": ["MFI"],
          PBK.TREND_PULLBACK: ["RSI", "ADX"], PBK.RANGE: ["RSI", "ADX"]}
# the two ways to pick strategies in the form
MODES = {"single": ("tune", "Strategies: one, several or all", "الاستراتيجيات: وحدة أو أكثر أو الكل",
                    "The classic indicator strategies. Pick one, several or all of them; any of them can open a trade.",
                    "استراتيجيات المؤشرات الكلاسيكية. اختر وحدة أو أكثر أو كلها، وأي وحدة منها تقدر تفتح صفقة."),
         "combo": ("hub", "Combined strategies", "الاستراتيجيات المركّبة",
                   "Complete setups written as exact numbers: trend, pullback or breakout, confirmation, and their own stop, "
                   "target and time stop.",
                   "استراتيجيات كاملة مكتوبة بأرقام دقيقة: اتجاه وتراجع أو اختراق وتأكيد، ولكل وحدة وقفها وهدفها ووقفها الزمني.")}
PB_ICON = {PBK.TREND_PULLBACK: "trending_up", PBK.BREAKOUT_RETEST: "north_east", PBK.SQUEEZE: "compress", PBK.RANGE: "swap_vert",
           PBK.ORB: "timer"}
INSTR_LABEL = {"stock": ("Stocks", "أسهم"), "options": ("Options", "أوبشن"), "both": ("Both", "الاثنين")}
INSTR_CHIP = {"stock": ("show_chart", "Stocks", "أسهم"), "options": ("receipt_long", "Options · est.", "أوبشن · تقديري"),
              "both": ("layers", "Stocks + options · est.", "أسهم + أوبشن · تقديري")}
# option prices are never real quotes: Yahoo keeps no option price history, so every premium is a Black-Scholes estimate
EST = ("est.", "تقديري")
# the two phases of a bot: (icon, name en, ar, tag en, ar, line en, ar)
PHASES = {"live": ("sensors", "Forward test", "التجربة الأمامية", "LIVE", "مباشر",
                   "Recorded session by session", "تُسجَّل جلسة بجلسة"),
          "sim": ("history", "Historical simulation", "المحاكاة التاريخية", "SIM", "محاكاة",
                  "Recalculated from past prices", "تُحسب من أسعار الماضي")}
OTYPE_LABEL = {"call": ("Calls (buy signals)", "Call (إشارات الشراء)"), "put": ("Puts (sell signals)", "Put (إشارات البيع)"),
               "both": ("Calls + Puts", "Call + Put")}
STRIKE_LABEL = {-10: ("10% in the money", "داخل السعر 10%"), -5: ("5% in the money", "داخل السعر 5%"), 0: ("At the money", "عند السعر"),
                5: ("5% out of the money", "خارج السعر 5%"), 10: ("10% out of the money", "خارج السعر 10%")}
TYPE_BADGE = {"Stock": ("STOCK", "سهم", "up"), "Call": ("CALL", "CALL", "acc"), "Put": ("PUT", "PUT", "vio"),
              "Short": ("SHORT", "بيع مكشوف", "down")}
TYPE_NAME = {"Stock": ("Stocks", "الأسهم"), "Call": ("Calls", "عقود Call"), "Put": ("Puts", "عقود Put"), "Short": ("Shorts", "البيع المكشوف")}
TYPE_ONE = {"Stock": ("Stock", "سهم"), "Call": ("Call", "Call"), "Put": ("Put", "Put"), "Short": ("Short", "بيع مكشوف")}
EXIT_KIND = {"Signal": "neu", "Stop Loss": "down", "Trailing Stop": "gold", "Take Profit": "up", "Time Exit": "org", "Time Stop": "org",
             "Close of Day": "neu"}
EXIT_AR = {**engine.EXIT_REASON_AR, "Time Exit": "خروج قبل الانتهاء", "Time Stop": "وقف زمني", "Close of Day": "إغلاق اليوم"}
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DEFAULTS = {"pb_name": "", "pb_capital": 1_000_000, "pb_kind": "all", "pb_symbol": "AAPL", "pb_sector": "Technology",
            "pb_ind_sector": "Technology", "pb_industry": "Semiconductors", "pb_maxpos": 10, "pb_store": ["SMA Crossover"],
            "pb_fee": 0.05, "pb_stop": 0.0, "pb_atr": 3.0, "pb_tp": 0.0, "pb_trail": 0.0, "pb_combine": "any", "pb_instr": "stock",
            "pb_otype": "call", "pb_dte": 30, "pb_strike": 0, "pb_oalloc": 5.0, "pb_otp": 100.0, "pb_osl": 50.0,
            "pb_mode": "single", "pb_store_pb": [PBK.TREND_PULLBACK], "pb_pbmode": "any", "pb_pbwin": 5, "pb_riskpt": 0.0, "pb_regime": 0, "pb_trend": False}

_A, _V, _C, _D, _G, _BG, _BD, _MU = T.ACCENT, T.VIOLET, T.CYAN, T.DOWN, T.GOLD, T.CARD2, T.BORDER, T.MUTED
REGIME_LABEL = {0: ("Off", "إيقاف"),
                1: ("No new buys while the S&P 500 is under its 200-day average", "لا شراء جديد والسوق تحت متوسط 200 يوم"),
                2: ("No new buys under the 200-day average, and sell when the market drops under it",
                    "لا شراء جديد تحت متوسط 200 يوم، وبيع لما ينزل السوق تحته")}
TABLE_ROWS = 400            # rows shown in a long table (the CSV export has them all)
_CARD_H = 352          # every card in the leaderboard (bots and "Add Bot") has this height
PAGE_CSS = f"""<style>
/* ---------- red actions (delete dialog) ---------- */
[class*="st-key-pbred"] button {{ border-color:{_D}88 !important; }}
[class*="st-key-pbred"] button p, [class*="st-key-pbred"] button span {{ color:{_D} !important; }}
[class*="st-key-pbred"] button:hover {{ border-color:{_D} !important; background:{_D}1A !important; }}

/* ---------- hero: the bots on the brand's rising line ---------- */
.pbhero {{ position:relative; overflow:hidden; border-radius:22px; border:1px solid {_BD}; margin:2px 0 16px; min-height:258px;
  background:linear-gradient(120deg,#0E0918,#1B1430,#27184A,#130F24); background-size:300% 300%; animation:sky 20s ease-in-out infinite; }}
.pbhero::after {{ content:""; position:absolute; left:0; right:0; top:0; height:1px; background:linear-gradient(90deg,transparent,rgba(196,181,253,.5),transparent); z-index:3; pointer-events:none; }}
.pbhero .grid {{ position:absolute; inset:0; pointer-events:none;
  background-image:linear-gradient(rgba(45,182,235,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(45,182,235,.07) 1px,transparent 1px);
  background-size:36px 36px; -webkit-mask-image:radial-gradient(ellipse at 78% 45%,#000 0%,transparent 68%);
  mask-image:radial-gradient(ellipse at 78% 45%,#000 0%,transparent 68%); }}
.pbhero .art {{ position:absolute; top:0; bottom:0; right:0; width:58%; pointer-events:none; }}
.pbhero .art svg {{ width:100%; height:100%; display:block; }}
.pbhero .txt {{ position:relative; z-index:2; padding:26px 30px 24px; max-width:640px;
  background:linear-gradient(90deg,rgba(14,9,24,.78) 0%,rgba(14,9,24,.35) 70%,rgba(14,9,24,0) 100%); }}
.pbhero.rtl .art {{ right:auto; left:0; }}
.pbhero.rtl .txt {{ margin-left:auto; background:linear-gradient(270deg,rgba(14,9,24,.78) 0%,rgba(14,9,24,.35) 70%,rgba(14,9,24,0) 100%); }}
.pbhero .eb {{ color:{_C}; font-weight:600; letter-spacing:.2em; font-size:.72rem; text-transform:uppercase; display:flex; align-items:center; gap:8px; }}
.pbhero .eb .ms {{ font-size:1.05rem; }}
.pbhero .t {{ font-size:2.7rem; font-weight:300; line-height:1.04; margin:8px 0 8px; color:#fff; letter-spacing:-.035em; }}
.pbhero .t b {{ background:linear-gradient(90deg,{_A},{_V},{_C}); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.pbhero .tg {{ color:#CAC5D1; font-size:.94rem; line-height:1.6; max-width:540px; }}
.pbhero .chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
.pbhero .chip {{ background:rgba(26,22,36,.8); border:1px solid {_BD}; backdrop-filter:blur(6px); border-radius:10px; padding:6px 10px;
  font-size:.8rem; display:inline-flex; align-items:center; gap:7px; color:#CCC7D3; font-variant-numeric:tabular-nums; }}
.pbhero .chip b {{ color:#fff; unicode-bidi:isolate; direction:ltr; }} .pbhero .chip .ms {{ color:{_C}; font-size:1rem; }}
.pbhero .chip .pill {{ min-width:0; padding:2px 7px; font-size:.74rem; }}
.pbhero .st {{ margin-top:12px; }}
.pbhero .ln {{ animation:pbdraw 8s ease-in-out infinite; }}
.pbhero .halo {{ transform-box:fill-box; transform-origin:center; animation:pbpulse 2.6s ease-out infinite; }}
.pbhero .tw {{ animation:pbtw 3.8s ease-in-out infinite; }}
.pbhero .mv {{ animation:pbtravel 8s ease-in-out infinite; }}
@keyframes pbdraw {{ 0% {{ stroke-dashoffset:var(--len); }} 55%,100% {{ stroke-dashoffset:0; }} }}
@keyframes pbtravel {{ 0% {{ offset-distance:0%; }} 55%,100% {{ offset-distance:100%; }} }}
@keyframes pbpulse {{ 0% {{ transform:scale(1); opacity:.9; }} 100% {{ transform:scale(2.1); opacity:0; }} }}
@keyframes pbtw {{ 0%,100% {{ opacity:.85; }} 50% {{ opacity:.1; }} }}
@media (max-width: 820px) {{ .pbhero .art {{ width:100%; opacity:.28; }} .pbhero .t {{ font-size:1.9rem; }} .pbhero .txt {{ background:none; }} }}

/* ---------- bot cards ---------- */
.pbc {{ margin:0 !important; height:{_CARD_H}px; box-sizing:border-box; display:flex; flex-direction:column; overflow:hidden; position:relative;
  transition:box-shadow .18s ease, border-color .18s ease; }}
.pbc::before {{ content:""; position:absolute; left:0; right:0; top:0; height:1px; background:linear-gradient(90deg,transparent,rgba(196,181,253,.5),transparent);
  opacity:0; transition:opacity .18s; }}
.pbc .top {{ display:flex; justify-content:space-between; align-items:center; height:22px; margin:-4px 0 8px; gap:6px; }}
.pbc .it {{ display:inline-flex; align-items:center; gap:5px; font-size:.62rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase;
  color:{_MU}; transition:opacity .15s; white-space:nowrap; overflow:hidden; }}
.pbc .it .ms {{ font-size:.95rem; color:{_C}; }}
.pbc .rk {{ display:inline-flex; align-items:center; gap:3px; font-weight:600; color:{_MU}; transition:opacity .15s; direction:ltr; }}
.pbc .rk .ms {{ font-size:1.05rem; }}
.pbc .rk.r1 {{ color:{_G}; }} .pbc .rk.r2 {{ color:#CAC5D1; }} .pbc .rk.r3 {{ color:#D9925F; }}
.pbc .co .tk {{ display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; white-space:normal; line-height:1.25; }}
.pbc .bdg {{ margin-top:10px; max-height:64px; overflow:hidden; display:flex; flex-direction:column; align-items:flex-start; gap:4px; }}
.pbc .bdg .badge {{ max-width:100%; margin:0; white-space:nowrap; min-width:0; }}
.pbc .bdg .badge .bt {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; min-width:0; }}
.pbc .body {{ margin-top:auto; }}
.pbc .spk {{ margin:0 -2px 8px; height:52px; }}
.pbc .spk svg {{ width:100%; height:52px; display:block; overflow:visible; }}
.pbc .row {{ display:flex; justify-content:space-between; align-items:flex-end; gap:8px; }}
.pbc .row .r {{ text-align:end; white-space:nowrap; }}
.pbc .pbft {{ color:{_MU}; font-size:.74rem; margin-top:10px; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
.pbc.sel {{ border-top:3px solid {_A}; box-shadow:0 0 0 1px {_A}55, 0 12px 30px {_A}26; }}
.pbc.sel::before {{ display:none; }}
[class*="st-key-pbcard_"] {{ position:relative; transition:transform .18s ease; }}
[class*="st-key-pbcard_"]:hover {{ transform:translateY(-4px) scale(1.02); z-index:3; }}
[class*="st-key-pbcard_"]:hover .pbc {{ box-shadow:0 14px 34px rgba(59,139,235,.20); }}
[class*="st-key-pbcard_"]:hover .pbc::before {{ opacity:.95; }}
[class*="st-key-pbcard_"]:hover .pbc .rk, [class*="st-key-pbcard_"]:hover .pbc .it {{ opacity:0; }}
[class*="st-key-pbcard_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_pick_"] {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; width:auto !important; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_pick_"] .stButton, [class*="st-key-pbcard_"] [class*="st-key-pb_pick_"] button
  {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_edit_"], [class*="st-key-pbcard_"] [class*="st-key-pb_trash_"]
  {{ position:absolute !important; top:12px; z-index:6; width:auto !important; margin:0 !important; opacity:0; transition:opacity .15s ease; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_edit_"] {{ right:14px; left:auto; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_trash_"] {{ left:14px; right:auto; }}
[class*="st-key-pbcard_"]:hover [class*="st-key-pb_edit_"], [class*="st-key-pbcard_"]:hover [class*="st-key-pb_trash_"] {{ opacity:1; }}
[class*="st-key-pb_edit_"] button, [class*="st-key-pb_trash_"] button {{ min-height:0 !important; height:24px !important; width:34px !important;
  padding:0 !important; display:grid !important; place-items:center !important; border-radius:8px !important; background:{_BG} !important; }}
[class*="st-key-pb_edit_"] button [data-testid="stIconMaterial"], [class*="st-key-pb_trash_"] button [data-testid="stIconMaterial"]
  {{ font-size:16px !important; margin:0 !important; }}
[class*="st-key-pb_edit_"] button > div, [class*="st-key-pb_trash_"] button > div {{ gap:0 !important; }}
[class*="st-key-pb_edit_"] button {{ border:1.5px solid {_A} !important; }}
[class*="st-key-pb_edit_"] button span {{ color:{_A} !important; }}
[class*="st-key-pb_trash_"] button {{ border:1.5px solid {_D} !important; }}
[class*="st-key-pb_trash_"] button span {{ color:{_D} !important; }}
[class*="st-key-pb_edit_"] button p, [class*="st-key-pb_trash_"] button p {{ display:none !important; }}
@media (hover: none) {{ [class*="st-key-pbcard_"] [class*="st-key-pb_edit_"], [class*="st-key-pbcard_"] [class*="st-key-pb_trash_"] {{ opacity:1; }} }}

/* ---------- LIVE / SIM: the tag on the cards and the page switch ---------- */
.pbc .it {{ min-width:0; flex:1 1 auto; }}
.pbc .it .ms {{ flex:none; }}
.pbc .it .tx {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; min-width:0; }}
.pbc .nw {{ white-space:nowrap; }}
.pbc .rt {{ display:inline-flex; align-items:center; gap:6px; transition:opacity .15s; flex:none; }}
.phg {{ display:inline-flex; align-items:center; gap:4px; font-size:.58rem; font-weight:600; letter-spacing:.06em; border-radius:6px;
  padding:2px 5px; line-height:1.3; white-space:nowrap; }}
.phg.live {{ background:{T.POS_BG}; color:{T.POS_FG}; }}
.phg.live::before {{ content:""; width:6px; height:6px; border-radius:50%; background:currentColor; animation:pbtw 2s ease-in-out infinite; }}
.phg.sim {{ background:{T.YEL_BG}; color:{T.YEL_FG}; }}
[class*="st-key-pbcard_"]:hover .pbc .rt {{ opacity:0; }}
[class*="st-key-pbphase"] {{ margin-bottom:2px; }}
[class*="st-key-pbphase"] [data-testid="stHorizontalBlock"] {{ gap:12px !important; flex-wrap:nowrap !important; align-items:stretch !important; }}
[class*="st-key-pbphase"] [data-testid="stColumn"] {{ min-width:0 !important; }}
[class*="st-key-pbph_"] {{ position:relative; }}
[class*="st-key-pbph_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-pbph_"] [class*="st-key-pb_ph_"] {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; width:auto !important; }}
[class*="st-key-pbph_"] [class*="st-key-pb_ph_"] .stButton, [class*="st-key-pbph_"] [class*="st-key-pb_ph_"] button
  {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
.pbph {{ position:relative; overflow:hidden; display:flex; align-items:center; gap:11px; height:66px; box-sizing:border-box; border-radius:14px;
  padding:10px 16px; color:#B1ABBA; background:{T.BOX_BG}; border:1px solid {_BD}; transition:background .18s, color .18s, border-color .18s; }}
[class*="st-key-pbph_"]:hover .pbph:not(.on) {{ border-color:{_A}66; color:#fff; }}
.pbph.on {{ color:#fff; border-color:{_A}88; background:{T.TOP}, linear-gradient(135deg,rgba(59,139,235,.20),rgba(123,69,240,.14) 70%,{T.CARD});
  box-shadow:0 8px 22px rgba(59,139,235,.14); }}
.pbph .i .ms {{ font-size:1.2rem; color:{_C}; background:rgba(45,182,235,.12); border-radius:10px; padding:6px; }}
.pbph.on .i .ms {{ color:#fff; background:rgba(59,139,235,.35); }}
.pbph .nm {{ display:flex; flex-direction:column; line-height:1.25; min-width:0; }}
.pbph .nm b {{ font-weight:600; font-size:.95rem; }}
.pbph .nm span {{ font-size:.72rem; font-weight:600; opacity:.8; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.pbph .phg {{ margin-inline-start:auto; }}
.pbrec {{ display:flex; flex-wrap:wrap; gap:7px; margin:2px 0 10px; }}
.pbrec .c {{ display:inline-flex; align-items:center; gap:6px; background:rgba(157,151,165,.10); border:1px solid {_BD}; border-radius:999px;
  padding:4px 12px; font-size:.75rem; font-weight:600; color:#B1ABBA; white-space:nowrap; }}
.pbrec .c b {{ color:#fff; unicode-bidi:isolate; direction:ltr; }}
.pbrec .c .ms {{ font-size:.95rem; color:{_C}; }}

/* ---------- "Add Bot": the logo tile with a plus and the cyan trend arrow ---------- */
.pbadd {{ align-items:center; justify-content:center; gap:10px; text-align:center; border:1.5px dashed {_A}77 !important;
  background:radial-gradient(120% 80% at 50% 0%,rgba(59,139,235,.12),transparent 62%),linear-gradient(180deg,{_BG},{T.CARD}) !important; }}
[class*="st-key-pbcard_add"]:hover .pbadd {{ border-color:{_A} !important; border-style:solid !important;
  box-shadow:0 0 0 1px {_A}55, 0 16px 40px rgba(59,139,235,.28) !important; }}
.pbadd .plus {{ width:92px; height:92px; }}
.pbadd .plus svg {{ width:92px; height:92px; display:block; overflow:visible; }}
.pbadd .orbit {{ transform-box:view-box; transform-origin:46px 46px; animation:pbspin 16s linear infinite; }}
.pbadd .cross {{ transform-box:view-box; transform-origin:46px 46px; transition:transform .45s cubic-bezier(.3,1.6,.5,1); }}
.pbadd .tile {{ transform-box:view-box; transform-origin:46px 46px; transition:transform .3s ease; }}
[class*="st-key-pbcard_add"]:hover .pbadd .cross {{ transform:rotate(90deg); }}
[class*="st-key-pbcard_add"]:hover .pbadd .tile {{ transform:scale(1.06); }}
[class*="st-key-pbcard_add"]:hover .pbadd .spark {{ animation:pbspark 1s ease-out; }}
@keyframes pbspin {{ to {{ transform:rotate(360deg); }} }}
@keyframes pbspark {{ from {{ stroke-dashoffset:40; }} to {{ stroke-dashoffset:0; }} }}
.pbadd .ttl {{ font-weight:600; font-size:1.15rem; background:linear-gradient(90deg,{_A},{_V},{_C}); -webkit-background-clip:text;
  background-clip:text; color:transparent; }}
.pbadd .sub {{ color:{_MU}; font-size:.78rem; }}
.pbadd .slots {{ display:flex; gap:6px; justify-content:center; margin-top:2px; direction:ltr; }}
.pbadd .slots span {{ width:18px; height:6px; border-radius:4px; background:{_BD}; display:block; }}
.pbadd .slots span.on {{ background:linear-gradient(90deg,{_A},{_V}); }}

/* ---------- details ---------- */
.pbid {{ position:relative; overflow:hidden; margin:0 !important; }}
.pbid::before {{ content:""; position:absolute; top:0; bottom:0; left:0; width:2px; background:{T.ELECTRIC}; }}
.pbid .co .tk {{ font-size:1.12rem; }}
.pbid .bdgs {{ margin-top:10px; }}
.pbk {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; }}
.pbsub {{ display:flex; align-items:center; gap:8px; font-weight:600; font-size:.98rem; color:#fff; margin:8px 0 0; }}
/* what worked: three panels of the same size, a centred bar per row (loss to the left, gain to the right) */
.wwg {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin:10px 0 6px; }}
@media (max-width: 900px) {{ .wwg {{ grid-template-columns:1fr; }} }}
.wwc {{ position:relative; overflow:hidden; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:18px; padding:14px 14px 10px;
  height:500px; box-sizing:border-box; display:flex; flex-direction:column; }}
.wwh {{ display:flex; align-items:center; gap:10px; margin-bottom:10px; }}
.wwh .i .ms {{ font-size:1.05rem; color:#fff; background:{T.PANEL}; box-shadow:{T.GLOW}; border-radius:9px; padding:6px; }}
.wwh b {{ display:block; color:#fff; font-size:.95rem; font-weight:600; }}
.wwh span:not(.i):not(.ms) {{ display:block; color:{_MU}; font-size:.72rem; font-weight:600; }}
.wwb {{ flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:5px; padding-inline-end:2px; scrollbar-width:thin; }}
.wwr {{ display:grid; grid-template-columns:minmax(0,1.15fr) minmax(0,1fr) 62px; align-items:center; gap:8px; padding:0 9px; height:31px; flex:none;
  border-radius:11px; background:rgba(255,255,255,.028); border:1px solid rgba(255,255,255,.04); }}
.wwr:hover {{ background:rgba(59,139,235,.09); border-color:{_A}44; }}
.wwn {{ display:flex; flex-direction:column; min-width:0; line-height:1.25; }}
.wwl {{ display:inline-flex; align-items:center; gap:7px; min-width:0; color:#fff !important; text-decoration:none !important; }}
.wwl b {{ font-size:.8rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.wwl .lg {{ width:20px !important; height:20px !important; font-size:8px !important; flex:none; }}
.wwi {{ color:{_MU}; font-size:.66rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.wwt {{ display:grid; grid-template-columns:1fr 1fr; height:10px; direction:ltr; }}
.wwt .h {{ display:flex; height:10px; background:rgba(157,151,165,.10); }}
.wwt .n {{ justify-content:flex-end; border-radius:6px 0 0 6px; border-right:1px solid #514B5C; }}
.wwt .p {{ justify-content:flex-start; border-radius:0 6px 6px 0; }}
.wwt .n i {{ display:block; height:100%; border-radius:6px 0 0 6px; background:linear-gradient(270deg,#FB7185,#E11D48); }}
.wwt .p i {{ display:block; height:100%; border-radius:0 6px 6px 0; background:linear-gradient(90deg,#10B981,#34D399); }}
.wwv {{ text-align:end; font-size:.8rem; font-weight:600; font-variant-numeric:tabular-nums; direction:ltr; }}
.wwv.up {{ color:#34D399; }} .wwv.dn {{ color:#FB7185; }}
.pbsub .ms {{ color:#fff; background:{T.PANEL}; box-shadow:{T.GLOW}; border-radius:8px; padding:4px; font-size:1rem; }}
.pbsub .muted {{ font-size:.76rem; font-weight:600; }}
.pbsel {{ display:flex; flex-wrap:wrap; gap:8px; }}
.pbsel .c {{ display:inline-flex; align-items:center; gap:6px; padding:5px 10px; border-radius:10px; background:rgba(157,151,165,.12);
  border:1px solid {_BD}; font-size:.78rem; font-weight:600; color:#CCC7D3; }}
.pbsel .c .pill {{ min-width:0; padding:1px 6px; font-size:.72rem; }}
/* every part of the details is its own block: the same space between parts, the normal gap inside them */
[class*="st-key-pbsec_"] {{ margin-top:20px; }}
[class*="st-key-pbsec_"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
[class*="st-key-pbsec_"] .sec {{ margin:0 !important; }}
[class*="st-key-pbsec_"] .tdk {{ margin-bottom:0 !important; }}
[class*="st-key-pbcard_"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}

/* ---------- panels: open positions / recent trades / calendar ---------- */
.pbp {{ position:relative; overflow:hidden; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:18px;
  padding:14px 16px 10px 19px; margin:0; }}
.pbp::before {{ content:""; position:absolute; top:0; bottom:0; left:0; width:2px; background:{T.ELECTRIC}; }}
.pbp .hd {{ display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:10px; }}
.pbp .tt {{ display:flex; align-items:center; gap:8px; font-weight:600; font-size:1.02rem; color:#fff; }}
.pbp .tt .ms {{ color:#fff; background:{T.PANEL}; box-shadow:{T.GLOW}; border-radius:8px; padding:4px; font-size:1rem; }}
.pbp .tt .live {{ width:8px; height:8px; border-radius:50%; background:{_G}; box-shadow:0 0 0 3px rgba(245,185,74,.18); }}
.pbp .sum {{ display:flex; flex-wrap:wrap; gap:7px; align-items:center; }}
.pbp .sum .c {{ display:inline-flex; align-items:center; gap:7px; background:rgba(157,151,165,.10); border:1px solid {_BD}; border-radius:999px;
  padding:4px 12px; font-size:.75rem; font-weight:600; color:#B1ABBA; line-height:1.4; white-space:nowrap; }}
.pbp .sum .c b {{ color:#fff; unicode-bidi:isolate; direction:ltr; font-weight:600; }}
.pbp .sum .c .pbox {{ padding:1px 8px; font-size:.74rem; border-radius:999px; line-height:1.4; margin:0; }}
.pbempty {{ color:{_MU}; padding:10px 2px 8px; display:flex; align-items:center; gap:8px; }}
.pbscroll {{ overflow-x:auto; }}
/* modern slim tables: one line per row, rounded rows, no grid lines */
.pbt {{ width:100%; min-width:900px; border-collapse:separate !important; border-spacing:0 4px !important; font-size:.8rem; direction:ltr;
  border:none !important; margin:-4px 0 0 !important; background:none !important; }}
.pbt thead tr, .pbt tbody tr {{ background:none !important; border:none !important; }}
.pbt th {{ color:{_MU}; font-size:.6rem; letter-spacing:.09em; text-transform:uppercase; text-align:left; padding:6px 12px 2px !important;
  font-weight:600; white-space:nowrap; border:none !important; background:none !important; }}
.pbt td {{ padding:6px 12px !important; white-space:nowrap; vertical-align:middle; text-align:left; line-height:1.35; color:#DDD9E2;
  background:rgba(255,255,255,.028) !important; border:none !important; border-top:1px solid rgba(255,255,255,.045) !important;
  border-bottom:1px solid rgba(255,255,255,.045) !important; transition:background .15s ease; }}
.pbt td:first-child {{ border-left:1px solid rgba(255,255,255,.045) !important; border-radius:10px 0 0 10px; }}
.pbt td:last-child {{ border-right:1px solid rgba(255,255,255,.045) !important; border-radius:0 10px 10px 0; }}
.pbt tbody tr:hover td {{ background:rgba(59,139,235,.10) !important; }}
.pbt th.r, .pbt td.r {{ text-align:right; }}
.pbt b {{ color:#fff; font-weight:600; }}
.pbt .as {{ display:inline-flex; align-items:center; gap:8px; color:#fff !important; text-decoration:none !important; }}
.pbt .as .lg {{ width:22px !important; height:22px !important; font-size:9px !important; }}
.pbt .as b {{ font-size:.84rem; }} .pbt .as:hover b {{ color:#79B8F4; }}
.pbt .m {{ color:{_MU}; font-size:.72rem; font-weight:600; }}
.pbt .up {{ color:#4ADE80; font-weight:600; }} .pbt .dn {{ color:#F87171; font-weight:600; }}
.pbt .est {{ color:{_G}; border:1px solid {_G}55; border-radius:6px; padding:0 5px; margin-inline-start:6px; font-size:.64rem; }}
.pbt .badge {{ margin:0; padding:2px 9px; font-size:.64rem; }}
.pbt .pbox {{ padding:1px 9px; font-size:.76rem; border-radius:999px; margin-left:8px; }}
a.pblink {{ display:inline-flex; align-items:center; gap:4px; color:#79B8F4 !important; font-weight:600; font-size:.8rem;
  text-decoration:none !important; padding:4px 10px; border-radius:10px; border:1px solid {_A}55; background:{_A}14; }}
a.pblink:hover {{ color:#fff !important; border-color:{_A}; background:{_A}33; }}
a.pblink .ms {{ font-size:1rem; }}
.pbanchor {{ scroll-margin-top:96px; height:1px; }}

/* ---------- monthly returns: every month is a button that opens its calendar ---------- */
[class*="st-key-pbmg_"] {{ overflow-x:auto; overflow-y:hidden; max-width:860px; gap:5px !important; padding:10px 12px 12px;
  background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; }}
[class*="st-key-pbmg_"] [data-testid="stHorizontalBlock"] {{ min-width:680px; flex-wrap:nowrap !important; gap:4px !important;
  align-items:center !important; }}
[class*="st-key-pbmg_"] [data-testid="stColumn"] {{ min-width:0 !important; }}
[class*="st-key-pbmg_"] [data-testid="stElementContainer"], [class*="st-key-pbmg_"] .stMarkdown,
[class*="st-key-pbmg_"] [data-testid="stMarkdownContainer"] {{ margin:0 !important; }}
[class*="st-key-pbmg_"] [data-testid="stMarkdownContainer"] p {{ margin:0 !important; }}
.pbmh {{ color:{_MU}; font-size:.58rem; font-weight:600; text-align:center; letter-spacing:.06em; text-transform:uppercase; line-height:16px; }}
.pbmy {{ font-weight:600; color:#fff; font-size:.78rem; line-height:26px; }}
.pbmt {{ text-align:center; line-height:26px; }} .pbmt .pbox {{ padding:2px 6px; font-size:.68rem; border-radius:6px; }}
.pbme {{ height:26px; border-radius:6px; background:rgba(157,151,165,.06); }}
[class*="st-key-pbmo_"] button {{ min-height:26px !important; height:26px; padding:0 2px !important; border-radius:6px !important;
  border:0 !important; transition:transform .12s ease, box-shadow .12s ease; }}
[class*="st-key-pbmo_"] button p {{ font-size:.68rem !important; font-weight:600 !important; color:#F2EFF6 !important; white-space:nowrap; direction:ltr; }}
[class*="st-key-pbmo_"] button:hover {{ transform:translateY(-2px); box-shadow:0 6px 16px rgba(0,0,0,.35); }}
[class*="st-key-pbmo_"][class*="_on_"] button {{ box-shadow:0 0 0 2px {T.BG}, 0 0 0 4px {_A} !important; transform:translateY(-2px); }}
[class*="st-key-pbcalbox_"] {{ background:{T.BOX_BG}; border:1px solid {_A}66; border-radius:18px; padding:14px 16px;
  box-shadow:0 12px 30px rgba(59,139,235,.12); margin-top:6px; max-width:1100px; }}
.pbct {{ display:flex; flex-wrap:wrap; align-items:center; gap:8px; font-weight:600; font-size:1rem; color:#fff; }}
.pbct .ms {{ color:#fff; background:{T.PANEL}; box-shadow:{T.GLOW}; border-radius:8px; padding:4px; font-size:1rem; }}
.pbct .muted {{ font-size:.78rem; font-weight:600; }} .pbct .pill {{ min-width:0; padding:2px 8px; font-size:.76rem; }}
.pbct .pbox {{ padding:2px 8px; font-size:.8rem; }}

/* ---------- add / edit form: a banner in the hero's colours, then numbered cards with space between them ---------- */
.pbfb {{ position:relative; overflow:hidden; border-radius:18px; border:1px solid {_BD}; padding:16px 20px 14px; min-height:118px;
  background:linear-gradient(120deg,#0E0918,#1B1430,#27184A,#130F24); background-size:300% 300%; animation:sky 20s ease-in-out infinite; }}
.pbfb::after {{ content:""; position:absolute; left:0; right:0; top:0; height:1px; background:linear-gradient(90deg,transparent,rgba(196,181,253,.5),transparent); z-index:3; pointer-events:none; }}
.pbfb .art {{ position:absolute; top:0; bottom:0; right:0; width:34%; pointer-events:none; }}
.pbfb .art svg {{ width:100%; height:100%; display:block; }}
.pbfb .ln {{ animation:pbdraw 7s ease-in-out infinite; }}
.pbfb .tx {{ position:relative; z-index:2; max-width:76%; }}
.pbfb.rtl .art {{ right:auto; left:0; transform:scaleX(-1); }}
.pbfb.rtl .tx {{ margin-left:auto; }}
.pbfb .eb {{ color:{_C}; font-weight:600; letter-spacing:.18em; font-size:.66rem; text-transform:uppercase; display:flex; align-items:center; gap:6px; }}
.pbfb .eb .ms {{ font-size:.95rem; }}
.pbfb .t {{ font-size:1.55rem; font-weight:600; color:#fff; margin:5px 0 3px; letter-spacing:-.01em; line-height:1.15; }}
.pbfb .t b {{ background:linear-gradient(90deg,{_A},{_V},{_C}); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.pbfb .s {{ color:#CAC5D1; font-size:.84rem; line-height:1.5; }}
.pbfb .pbstp {{ display:flex; flex-wrap:wrap; gap:4px; margin-top:11px; }}
.pbfb .pbstp span {{ display:inline-flex; align-items:center; gap:5px; font-size:.7rem; font-weight:600; color:#CCC7D3; background:rgba(26,22,36,.72);
  border:1px solid rgba(255,255,255,.06); border-radius:999px; padding:2px 9px 2px 3px; white-space:nowrap; }}
.pbfb.rtl .pbstp span {{ padding:2px 3px 2px 9px; }}
.pbfb .pbstp i {{ font-style:normal; width:17px; height:17px; border-radius:50%; display:grid; place-items:center; font-size:.62rem; font-weight:600;
  color:#fff; background:{T.ELECTRIC}; }}
[class*="st-key-pbf_"] {{ position:relative; overflow:hidden; background:linear-gradient(180deg,{_BG},{T.CARD}); border:1px solid {_BD};
  border-radius:18px; padding:16px 18px 16px; margin-top:16px; box-shadow:0 10px 26px rgba(0,0,0,.18); }}
[class*="st-key-pbf_"]::before {{ content:""; position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg,transparent,rgba(196,181,253,.5),transparent); }}
[class*="st-key-pbf_"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
.pbfh {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:2px; }}
.pbfh .n {{ width:28px; height:28px; border-radius:9px; display:grid; place-items:center; font-weight:600; font-size:.84rem; color:#fff; flex:none;
  background:{T.ELECTRIC}; box-shadow:0 6px 16px rgba(107,33,239,.35); }}
.pbfh .t {{ display:flex; align-items:center; gap:7px; font-weight:600; font-size:1.03rem; color:#fff; }}
.pbfh .t .ms {{ color:{_C}; font-size:1.15rem; }}
.pbfh .h {{ color:{_MU}; font-size:.76rem; font-weight:600; margin-inline-start:auto; }}
.pbfs {{ display:flex; align-items:center; gap:6px; font-weight:600; font-size:.74rem; color:#B1ABBA; letter-spacing:.08em; text-transform:uppercase; }}
.pbfs .ms {{ color:{_C}; font-size:1rem; }}
/* the two ways to pick strategies: two separate tiles, the chosen one softly lit */
[class*="st-key-pbswitch"] [data-testid="stHorizontalBlock"] {{ gap:12px !important; flex-wrap:nowrap !important; align-items:stretch !important; }}
[class*="st-key-pbswitch"] [data-testid="stColumn"] {{ min-width:0 !important; }}
[class*="st-key-pbmode_"] {{ position:relative; }}
[class*="st-key-pbmode_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-pbmode_"] [class*="st-key-pb_mode_"] {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; width:auto !important; }}
[class*="st-key-pbmode_"] [class*="st-key-pb_mode_"] .stButton, [class*="st-key-pbmode_"] [class*="st-key-pb_mode_"] button
  {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
.pbmode {{ position:relative; overflow:hidden; display:flex; align-items:center; gap:10px; height:62px; box-sizing:border-box; border-radius:14px;
  padding:9px 15px; color:#B1ABBA; background:{T.BOX_BG}; border:1px solid {_BD}; transition:background .18s, color .18s, border-color .18s; }}
[class*="st-key-pbmode_"]:hover .pbmode:not(.on) {{ border-color:{_A}66; color:#fff; }}
.pbmode.on {{ color:#fff; border-color:{_A}88; background:{T.TOP}, linear-gradient(135deg,rgba(59,139,235,.20),rgba(123,69,240,.14) 70%,{T.CARD});
  box-shadow:0 8px 22px rgba(59,139,235,.14); }}
.pbmode .i .ms {{ font-size:1.2rem; color:{_C}; background:rgba(45,182,235,.12); border-radius:10px; padding:6px; }}
.pbmode.on .i .ms {{ color:#fff; background:rgba(59,139,235,.35); }}
.pbmode .nm {{ font-weight:600; font-size:.95rem; line-height:1.25; }}
.pbmode .ct {{ margin-inline-start:auto; font-size:.72rem; font-weight:600; min-width:26px; height:22px; padding:0 8px; border-radius:999px;
  display:inline-grid; place-items:center; background:rgba(157,151,165,.16); color:#CCC7D3; }}
.pbmode.on .ct {{ background:rgba(255,255,255,.22); color:#fff; }}
/* a '?' next to every chosen strategy (it opens the strategy's rules), and the "work together" pop-out, last */
[class*="st-key-pbq_row"] {{ flex-wrap:wrap !important; gap:8px !important; }}
[class*="st-key-pbq_row"] button {{ border-radius:999px !important; border:1px solid {_A}55 !important; background:{_A}14 !important;
  min-height:34px !important; padding:3px 14px 3px 10px !important; }}
[class*="st-key-pbq_row"] button:hover {{ border-color:{_A} !important; background:{_A}2A !important; }}
[class*="st-key-pbq_row"] button p {{ font-weight:600 !important; font-size:.84rem !important; color:#DCEBFA !important; }}
[class*="st-key-pbq_row"] button [data-testid="stIconMaterial"] {{ color:{_C} !important; }}
[class*="st-key-pbq_together"] [data-testid="stPopover"], [class*="st-key-pbq_together"] [data-testid="stPopover"] > div,
[class*="st-key-pbq_together"] button {{ width:100% !important; }}
[class*="st-key-pbq_together"] button {{ justify-content:flex-start !important; min-height:44px !important; border-radius:12px !important;
  border:1px dashed {_A}88 !important; background:rgba(59,139,235,.07) !important; }}
[class*="st-key-pbq_together"] button:hover {{ border-style:solid !important; background:rgba(59,139,235,.14) !important; }}
[class*="st-key-pbq_together"] button p {{ font-weight:600 !important; color:#DCEBFA !important; }}
[class*="st-key-pbq_together"] button [data-testid="stIconMaterial"] {{ color:{_C} !important; }}
[data-testid="stPopoverBody"] {{ min-width:min(760px, 92vw); }}
/* AI bots: five ready bots, each with its own model */
.aihd {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin:22px 0 6px; }}
.aihd .i .ms {{ font-size:1.25rem; color:#fff; background:linear-gradient(135deg,{_V},{_C}); border-radius:11px; padding:7px; }}
.aihd .t {{ font-weight:600; font-size:1.18rem; color:#fff; }}
.aihd .s {{ color:{_MU}; font-size:.8rem; font-weight:600; width:100%; margin-top:-4px; }}
[class*="st-key-aicard_"] {{ position:relative; overflow:hidden; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:18px;
  padding:14px 15px 12px; height:100%; }}
[class*="st-key-aicard_"]:has(.aic.up) {{ border-color:rgba(34,197,94,.45); }}
[class*="st-key-aicard_"]:has(.aic.down) {{ border-color:rgba(239,68,68,.40); }}
.aic .hd {{ display:flex; align-items:flex-start; gap:9px; }}
.aic .hd .i .ms {{ font-size:1.05rem; color:#fff; background:{T.PANEL}; box-shadow:{T.GLOW}; border-radius:9px; padding:5px; }}
.aic .nm {{ font-weight:600; color:#fff; font-size:.98rem; line-height:1.25; }}
.aic .sub {{ color:{_MU}; font-size:.74rem; font-weight:600; margin-top:2px; line-height:1.4; }}
.aic .hd .tx {{ flex:1; min-width:0; }}
.aic .cs .badge {{ margin:0; }}
.aic .cs {{ display:flex; flex-wrap:wrap; gap:5px; margin:9px 0 8px; }}
.aic .cs > span:not(.badge) {{ font-size:.68rem; font-weight:600; color:#CCC7D3; background:rgba(157,151,165,.10); border:1px solid {_BD}; border-radius:999px;
  padding:2px 9px; white-space:nowrap; }}
.aic table {{ width:100%; border-collapse:separate; border-spacing:0 3px; font-size:.78rem; direction:ltr; }}
.aic th {{ color:{_MU}; font-size:.6rem; letter-spacing:.07em; text-transform:uppercase; font-weight:600; text-align:right; padding:0 6px 2px; }}
.aic th:first-child, .aic td:first-child {{ text-align:left; }}
.aic td {{ background:rgba(255,255,255,.035); padding:5px 6px; text-align:right; color:#DDD9E2; font-variant-numeric:tabular-nums; }}
.aic td:first-child {{ border-radius:8px 0 0 8px; font-weight:600; color:#fff; }}
.aic td:last-child {{ border-radius:0 8px 8px 0; }}
.aic tr.ai td {{ background:linear-gradient(90deg,rgba(123,69,240,.20),rgba(45,182,235,.10)); }}
.aic .up {{ color:#4ADE80; }} .aic .dn {{ color:#F87171; }}
.aic .nt {{ color:#B1ABBA; font-size:.74rem; line-height:1.5; margin-top:7px; }}
[class*="st-key-aicard_"] button {{ border-radius:12px !important; min-height:40px !important; margin-top:4px; }}
[class*="st-key-aicard_"] [data-testid="stElementContainer"] {{ width:100%; }}
.aiday {{ display:flex; flex-wrap:wrap; gap:6px; }}
.aiday span {{ display:inline-flex; align-items:center; gap:6px; font-size:.76rem; font-weight:600; border-radius:999px; padding:3px 10px;
  border:1px solid {_BD}; background:rgba(157,151,165,.08); color:#CCC7D3; }}
.aiday span.go {{ border-color:rgba(34,197,94,.5); background:rgba(34,197,94,.12); color:#BBF7D0; }}
.aiday span b {{ color:#fff; }}
/* name ideas under the name */
[class*="st-key-pbnames"] {{ flex-wrap:wrap !important; gap:6px !important; align-items:center !important; margin-top:-4px; }}
.pbni {{ display:inline-flex; align-items:center; gap:4px; font-size:.72rem; font-weight:600; color:{_G}; }}
.pbni .ms {{ font-size:1rem; }}
[class*="st-key-pbnames"] button {{ min-height:30px !important; padding:2px 12px !important; border-radius:999px !important;
  border:1px dashed {_A}77 !important; background:rgba(59,139,235,.06) !important; }}
[class*="st-key-pbnames"] button:hover {{ border-style:solid !important; background:rgba(59,139,235,.16) !important; }}
[class*="st-key-pbnames"] button p {{ font-size:.78rem !important; font-weight:600 !important; color:#DCEBFA !important; }}
.pbfs2 {{ margin-top:12px; }}
/* the kinds of strategy: tiles; pointing at one drops down its strategies */
[class*="st-key-pbf_"] {{ overflow:visible !important; }}
[class*="st-key-pbf_"]::before {{ border-radius:18px 18px 0 0; }}
[class*="st-key-pbkinds_"] [data-testid="stHorizontalBlock"] {{ gap:8px !important; margin-bottom:8px; }}
[class*="st-key-pbkind_"] {{ position:relative; }}
.pbkd {{ display:flex; flex-direction:column; justify-content:center; gap:7px; height:74px; box-sizing:border-box; border:1px solid {_BD};
  border-radius:14px; background:{T.BOX_BG}; padding:10px 12px; cursor:default; transition:border-color .15s, background .15s; }}
.pbkd .tp {{ display:flex; align-items:center; gap:9px; min-width:0; }}
.pbkd .i {{ flex:none; display:flex; }}
.pbkd .i .ms {{ color:{_C}; background:rgba(45,182,235,.12); border-radius:9px; padding:5px; font-size:1.05rem; }}
.pbkd .nm {{ font-weight:600; font-size:.86rem; color:#fff; line-height:1.2; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.pbkd .ct {{ display:flex; align-items:center; gap:2px; font-size:.68rem; color:{_MU}; font-weight:600; padding-inline-start:2px; }}
.pbkd .ct .ms {{ font-size:1rem; transition:transform .15s; }}
.pbkd.has {{ border-color:{_A}77; background:{T.TOP_THIN}, linear-gradient(135deg,rgba(59,139,235,.14),rgba(123,69,240,.08) 70%,{T.CARD}); }}
.pbkd.has .ct {{ color:#9DCBF7; }}
[class*="st-key-pbkind_"]:hover .pbkd {{ border-color:{_A}; }}
[class*="st-key-pbkind_"]:hover .pbkd .ct .ms {{ transform:rotate(180deg); }}
[class*="st-key-pbkindl_"] {{ display:none !important; position:absolute !important; top:100%; inset-inline-start:0; z-index:80; min-width:260px;
  width:max-content !important; max-width:340px; gap:3px !important; padding:6px !important; margin-top:0 !important; background:#1A1624;
  border:1px solid {_A}55; border-radius:14px; box-shadow:0 22px 44px rgba(0,0,0,.55); }}
[class*="st-key-pbkindl_"][class*="_R"] {{ inset-inline-start:auto; inset-inline-end:0; }}
[class*="st-key-pbkind_"]:hover [class*="st-key-pbkindl_"], [class*="st-key-pbkind_"]:focus-within [class*="st-key-pbkindl_"] {{ display:flex !important; }}
[class*="st-key-pbkindl_"] button {{ justify-content:flex-start !important; min-height:36px !important; border-radius:10px !important;
  border:1px solid transparent !important; background:transparent !important; box-shadow:none !important; padding:4px 10px !important; }}
[class*="st-key-pbkindl_"] button > div {{ justify-content:flex-start !important; width:100% !important; gap:10px !important; }}
[class*="st-key-pbkindl_"] button [data-testid="stMarkdownContainer"] {{ text-align:start !important; }}
[class*="st-key-pbkindl_"] button:hover {{ background:rgba(59,139,235,.14) !important; }}
[class*="st-key-pbkindl_"] button p {{ font-size:.84rem !important; font-weight:600 !important; color:#DDD9E2 !important; text-align:start !important; }}
[class*="st-key-pbkindl_"] button [data-testid="stIconMaterial"] {{ color:{_MU} !important; flex:none; font-size:1.15rem !important; margin:0 !important; }}
[class*="st-key-pbkindl_"] button[kind="primary"], [class*="st-key-pbkindl_"] button[data-testid="stBaseButton-primary"] {{
  background:rgba(59,139,235,.18) !important; border-color:{_A}55 !important; }}
[class*="st-key-pbkindl_"] button[kind="primary"] [data-testid="stIconMaterial"],
[class*="st-key-pbkindl_"] button[data-testid="stBaseButton-primary"] [data-testid="stIconMaterial"] {{ color:{_C} !important; }}
@media (max-width: 640px) {{ [class*="st-key-pbkindl_"] {{ min-width:220px; }} }}
/* the lab panel between the strategies and what the bot buys */
[class*="st-key-pblab"] {{ margin-top:16px; }}
[class*="st-key-pblab"] .xtp {{ margin-bottom:8px; }}
[class*="st-key-pb_uselab"] button {{ min-height:42px !important; border-radius:12px !important; border:1px solid {_C}88 !important;
  background:linear-gradient(95deg,rgba(45,182,235,.16),rgba(123,69,240,.18)) !important; }}
[class*="st-key-pb_uselab"] button:hover {{ border-color:{_C} !important; filter:brightness(1.1); }}
[class*="st-key-pb_uselab"] button p {{ font-weight:600 !important; color:#fff !important; }}
[class*="st-key-pb_uselab"] button [data-testid="stIconMaterial"] {{ color:{_C} !important; }}
[class*="st-key-pblab"] [data-testid="stExpander"] details {{ background:{T.BOX_BG}; border:1px solid {_BD} !important; border-radius:14px !important; }}
/* the big button at the end of the form */
[class*="st-key-pb_create"] {{ margin-top:8px; }}
[class*="st-key-pb_create"] button {{ min-height:54px !important; border:0 !important; border-radius:14px !important;
  background:{T.CTA} !important; box-shadow:0 14px 34px -12px rgba(45,182,235,.75), inset 0 1px 0 rgba(255,255,255,.2);
  transition:transform .15s ease, box-shadow .15s ease, filter .15s ease; }}
[class*="st-key-pb_create"] button:hover {{ transform:translateY(-2px); filter:brightness(1.08); box-shadow:0 18px 40px -12px rgba(45,182,235,.9); }}
[class*="st-key-pb_create"] button p {{ font-size:1.05rem !important; font-weight:600 !important; color:#fff !important; letter-spacing:.01em; }}
[class*="st-key-pb_create"] button [data-testid="stIconMaterial"] {{ color:#fff !important; }}
/* the chosen strategies inside the drop-downs, in the brand colours */
[class*="st-key-pb_ms_"] [data-baseweb="tag"] {{ background:linear-gradient(135deg,rgba(59,139,235,.30),rgba(123,69,240,.30)) !important;
  border:1px solid {_A}66 !important; border-radius:10px !important; }}
[class*="st-key-pb_ms_"] [data-baseweb="tag"] span {{ color:#fff !important; font-weight:600; }}
[class*="st-key-pb_ms_"] [data-baseweb="select"] > div {{ border-radius:12px !important; }}
/* a combined strategy's rules */
.pbrl {{ border:1px solid {_BD}; border-radius:16px; background:{T.BOX_BG}; padding:12px 14px 13px; }}
.pbrl + .pbrl {{ margin-top:10px; }}
.pbrl .hd {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
.pbrl .hd .i .ms {{ font-size:1.1rem; color:#fff; background:{T.PANEL}; box-shadow:{T.GLOW}; border-radius:10px; padding:6px; }}
.pbrl .nm {{ display:flex; flex-direction:column; line-height:1.3; }}
.pbrl .nm b {{ color:#fff; font-size:.96rem; }}
.pbrl .nm span {{ color:{_MU}; font-size:.74rem; font-weight:600; }}
.pbrl .cs {{ display:flex; flex-wrap:wrap; gap:6px; margin-inline-start:auto; }}
.pbrl .cs .c {{ display:inline-flex; align-items:center; gap:5px; font-size:.72rem; font-weight:600; color:#CCC7D3; background:rgba(157,151,165,.10);
  border:1px solid {_BD}; border-radius:999px; padding:3px 10px; white-space:nowrap; }}
.pbrl .cs .c .ms {{ font-size:.95rem; color:{_C}; }}
.pbrl .gr {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:9px; margin-top:11px; }}
.pbrl .gr:has(> .g:nth-child(4)) {{ grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); }}
.pbrl .g {{ background:{T.TOP_THIN}, rgba(255,255,255,.028); border:1px solid rgba(255,255,255,.055); border-radius:12px; padding:9px 12px 8px; }}
.pbrl .gt {{ display:flex; align-items:center; gap:7px; font-size:.68rem; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color:#9DCBF7; }}
.pbrl .gt .k {{ width:18px; height:18px; border-radius:6px; display:grid; place-items:center; background:rgba(59,139,235,.25); color:#fff; font-size:.64rem; }}
.pbrl ul {{ margin:6px 0 0; padding-inline-start:18px; }}
.pbrl li {{ color:#DDD9E2; font-size:.8rem; line-height:1.55; margin:2px 0; }}
.pbrl li::marker {{ color:{_C}; }}

@media (prefers-reduced-motion: reduce) {{ .pbhero *, .pbadd *, .pbfb * {{ animation:none !important; }} }}
@media (max-width: 640px) {{ .pbfb .art {{ width:100%; opacity:.25; }} .pbfb .tx {{ max-width:100%; }} }}
</style>"""
# Arabic: no letter-spacing (it breaks the joined letters) and the accent bars move to the right edge
PAGE_RTL_CSS = """<style>
.pbhero .eb, .pbc .it, .pbmh, .pbt th, .pbfb .eb, .pbfs, .pbmode .ct, .pbrl .gt { letter-spacing:0; }
.pbp::before, .pbid::before { left:auto; right:0; }
.pbp { padding:14px 19px 8px 16px; }

[class*="st-key-pbq_row"] button { padding:3px 10px 3px 14px !important; }
</style>"""


def strat_name(k):
    if k == PB.COMBO:
        return L("Agreement rule", "قاعدة الاتفاق")
    return L(k, engine.STRATEGY_AR.get(k) or PBK.AR.get(k, k))


def is_combined(bot):
    """True for a bot that runs the combined strategies (playbooks)."""
    return any(PB.is_playbook(s) for s in bot["strategies"])


def is_orb(bot):
    return PBK.ORB in bot["strategies"]


def strat_short(k):
    return strat_name(k).split(" (")[0]


def universe_label(bot, count=None):
    k, v = bot["kind"], bot["value"]
    if k == "company":
        return v
    if k == "sector":
        txt = L("Sector · ", "قطاع · ") + sector_name(v)
    elif k == "industry":
        txt = L("Industry · ", "صناعة · ") + gics_name(v)
    else:
        txt = L("All companies", "كل الشركات")
    if count:
        txt += L(f" ({count} stocks)", f" ({count} سهم)")
    return txt


def combo_rule(bot):
    """'Combined: all 3 agree' / 'Combined: 2 of 3', or None when each strategy trades on its own."""
    c, n = bot.get("combine") or {}, len(bot["strategies"])
    if c.get("mode") != "combo":
        return None
    if "window" in c:                             # combined strategies: n of them within w sessions
        w = c["window"]
        return L(f"Agreement: {c['min']} of {n} within {w} sessions", f"اتفاق: {c['min']} من {n} خلال {w} جلسات")
    if c["min"] >= n:
        return L(f"Agreement: all {n} agree", f"اتفاق: لازم تتفق الـ {n} كلها")
    return L(f"Agreement: {c['min']} of {n} agree", f"اتفاق: تتفق {c['min']} من {n}")


def how_label(bot, short=False):
    rule = combo_rule(bot)
    names = list(bot["strategies"])
    if is_combined(bot):
        if short:
            return rule or (strat_short(names[0]) if len(names) == 1 else L(f"{len(names)} combined strategies", f"{len(names)} استراتيجيات مركّبة"))
        return (rule + " · " if rule else L("Combined: ", "مركّبة: ")) + " + ".join(strat_short(x) for x in names)
    if rule and short:
        return rule
    if rule:
        return rule + " · " + " + ".join(strat_short(x) for x in names)
    return strategies_label(names, short)


def strategies_label(names, short=False):
    n = len(names)
    if n == len(engine.STRATEGIES):
        return L(f"All {n} strategies", f"كل الاستراتيجيات ({n})")
    if short and n > 2:
        return L(f"{n} strategies", f"{n} استراتيجيات")
    return " + ".join(strat_short(s) for s in names) or "—"


def _params_txt(name, params):
    spec = PB.spec_of(name)[1] if name in PB.ALL_STRATEGIES else []
    labels = {k: L(lab, engine.PARAM_AR.get(lab) or PBK.PARAM_AR.get(lab, lab)) for k, lab, *_ in spec}
    return " · ".join(f"{labels.get(k, k)} {v:g}" for k, v in params.items())


def instrument(bot):
    return bot.get("instrument") if bot.get("instrument") in PB.INSTRUMENTS else "stock"


def _stock_risk(bot):
    if is_orb(bot):
        return L("Stop and target from the opening range · out by the close", "الوقف والهدف من نطاق الافتتاح · خروج قبل الإغلاق")
    if is_combined(bot):
        out = [L("Stop · target · time stop from the rules", "الوقف والهدف والوقف الزمني من الشروط")]
        if bot["trail_pct"]:
            trail = iso(f"{bot['trail_pct']:g}%")
            out.append(f"{L('Trailing', 'متحرك')} {trail}")
        return " · ".join(out)
    out = []
    for k, en, ar_, suf in (("stop_pct", "Stop", "وقف", "%"), ("atr_mult", "ATR stop ×", "وقف ATR ×", ""),
                            ("tp_pct", "Target", "هدف", "%"), ("trail_pct", "Trailing", "متحرك", "%")):
        if bot[k]:
            out.append(f"{L(en, ar_)} {iso(f'{bot[k]:g}{suf}')}")
    return " · ".join(out) or L("No stop", "بدون وقف")


def _options_txt(o):
    alloc, tp, sl = iso(f"{o['alloc']:g}%"), iso(f"+{o['tp']:g}%"), iso(f"-{o['sl']:g}%")
    return " · ".join([L(*OTYPE_LABEL[o["type"]]), L(f"{o['dte']} days", f"{o['dte']} يوم"), L(*STRIKE_LABEL[o["strike"]]),
                       L(f"{alloc} per trade", f"{alloc} لكل صفقة"),
                       L(f"target {tp}", f"هدف {tp}") if o["tp"] > 0 else L("no target", "بدون هدف"),
                       L(f"stop {sl}", f"وقف {sl}") if o["sl"] > 0 else L("no stop", "بدون وقف")])


def _session_live():
    """True while the US market is open (the latest daily candle is still moving)."""
    now = datetime.now(ZoneInfo("America/New_York"))
    kind, _ = mcal.day_status(now.date())
    close = 780 if kind == "early" else 960
    return now.weekday() < 5 and kind != "closed" and 570 <= now.hour * 60 + now.minute < close


def iso(x):
    """A date, amount or percentage kept as one left-to-right piece inside Arabic text (Unicode isolates, harmless in English)."""
    return f"\u2066{x}\u2069"


def sm(v, dec=0):
    """Signed money: +$1,234 / -$1,234."""
    return ("+" if v is not None and not pd.isna(v) and v > 0 else "") + T.money(v, dec)


def type_badge(kind):
    en, ar_, color = TYPE_BADGE.get(kind, TYPE_BADGE["Stock"])
    return T.badge(L(en, ar_), color)


def exit_badge(reason):
    return T.badge(L(reason, EXIT_AR.get(reason, reason)), EXIT_KIND.get(reason, "neu"))


def _fp(x):
    return "$" + T.fmt_price(x)


# =====================================================================
# storage messages
# =====================================================================
def setup_steps():
    steps = L(
        "<b>1.</b> Create a free account at <b>supabase.com</b> and press <b>New project</b> (any name and password, the closest region).<br>"
        "<b>2.</b> In the project open <b>SQL Editor</b>, paste the code below and press <b>Run</b>. It creates the table for the bots.<br>"
        "<b>3.</b> Open <b>Project Settings</b> and copy the <b>Project ID</b> (the URL is https://PROJECT-ID.supabase.co), then open "
        "<b>API Keys</b> and copy the <b>secret</b> key (it starts with <code>sb_secret_</code>). Never use it in a public place; "
        "it only goes into Streamlit Secrets.<br>"
        "<b>4.</b> In Streamlit open your app's <b>Settings → Secrets</b> and add the three lines below under your FRED key, then press <b>Save</b>.",
        "<b>1.</b> سجّل حساب مجاني في <b>supabase.com</b> واضغط <b>New project</b> (أي اسم وكلمة مرور، واختر أقرب منطقة).<br>"
        "<b>2.</b> داخل المشروع افتح <b>SQL Editor</b>، والصق الكود اللي تحت واضغط <b>Run</b>. هذا ينشئ جدول البوتات.<br>"
        "<b>3.</b> افتح <b>Project Settings</b> وانسخ <b>Project ID</b> (الرابط يصير https://المعرّف.supabase.co)، ثم افتح <b>API Keys</b> "
        "وانسخ المفتاح <b>secret</b> (يبدأ بـ <code>sb_secret_</code>). لا تحطه في أي مكان عام، مكانه الوحيد Secrets في Streamlit.<br>"
        "<b>4.</b> في Streamlit افتح <b>Settings ← Secrets</b> للموقع، وأضف الأسطر الثلاثة اللي تحت تحت مفتاح FRED، ثم اضغط <b>Save</b>.")
    ui.html(f'<div style="line-height:2">{steps}</div>')
    st.code(PB.SETUP_SQL, language="sql")
    st.code('SUPABASE_URL = "https://xxxx.supabase.co"\nSUPABASE_KEY = "sb_secret_..."\nBOTS_PASSWORD = "' +
            L("choose-a-password", "اختر-كلمة-مرور") + '"', language="toml")


def storage_notice(err):
    if err is not None:
        msg = {"no_table": L("Supabase is connected, but the bots table is missing. Open SQL Editor in Supabase, run this code, then refresh.",
                             "Supabase متصل، لكن جدول البوتات غير موجود. افتح SQL Editor في Supabase وشغّل هذا الكود، ثم حدّث الصفحة."),
               "auth": L("Supabase refused the key. In Secrets, SUPABASE_KEY must be the secret key (Supabase → Settings → API Keys → secret).",
                         "Supabase رفض المفتاح. لازم يكون SUPABASE_KEY في Secrets هو المفتاح السري (Supabase ← Settings ← API Keys ← secret)."),
               "network": L("Couldn't reach Supabase right now. Check SUPABASE_URL in Secrets, or try again in a minute.",
                            "تعذر الاتصال بـ Supabase حالياً. تأكد من SUPABASE_URL في Secrets، أو حاول بعد دقيقة.")}.get(
            err.kind, L("Supabase returned an error.", "Supabase رجّع خطأ."))
        st.error(msg, icon=":material/database:")
        if err.kind == "no_table":
            st.code(PB.SETUP_SQL, language="sql")
        with st.expander(L("Technical details", "تفاصيل فنية")):
            st.code(err.detail[:600] or err.kind)
    elif PB.backend() == "local":
        st.warning(L("Trial mode: bots are kept in temporary storage and are lost when the site restarts. Connect Supabase (free) to keep them for good.",
                     "وضع التجربة: البوتات محفوظة مؤقتاً وتنحذف إذا أعاد الموقع التشغيل. اربط Supabase (مجاني) عشان تنحفظ بشكل دائم."),
                   icon=":material/info:")
        with st.expander(L("How to connect Supabase (5 minutes)", "طريقة ربط Supabase (5 دقائق)"), icon=":material/database:"):
            setup_steps()


# =====================================================================
# hero: the five bot slots on the brand's rising line
# =====================================================================
_SLOTS = [(62, 196), (150, 152), (238, 166), (326, 106), (414, 64)]


def _hero_art(ranked_sims):
    """Slot 5 (top right) holds the best bot, empty slots sit at the bottom left."""
    pts = [(16, 222)] + _SLOTS + [(476, 36)]
    path = "M" + " L".join(f"{x} {y}" for x, y in pts)
    length = sum(hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(pts, pts[1:]))
    s = ['<svg viewBox="0 0 520 250" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" style="direction:ltr">'
         '<defs><linearGradient id="pbln" x1="0" x2="1"><stop offset="0" stop-color="#2DB6EB" stop-opacity="0"/>'
         '<stop offset=".3" stop-color="#2DB6EB"/><stop offset=".72" stop-color="#3B8BEB"/><stop offset="1" stop-color="#A78BFA"/></linearGradient>'
         '<linearGradient id="pbnd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3B8BEB"/><stop offset="1" stop-color="#7B45F0"/></linearGradient>'
         '<filter id="pbgl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/>'
         '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
         # the brand's "A", large and faint
         '<g transform="translate(366 66) scale(3.5)" opacity=".06"><path d="M17 48 L29.5 15.5 Q32 11 34.5 15.5 L47 48" fill="none" '
         'stroke="#fff" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/></g>']
    rng = np.random.default_rng(11)
    for _ in range(16):
        s.append(f'<circle class="tw" cx="{rng.uniform(20, 510):.0f}" cy="{rng.uniform(8, 240):.0f}" r="{rng.uniform(.6, 1.5):.1f}" '
                 f'fill="#9DCBF7" style="animation-delay:-{rng.uniform(0, 4):.1f}s"/>')
    s.append(f'<path d="{path}" fill="none" stroke="#2DB6EB" stroke-opacity=".10" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>')
    s.append(f'<path class="ln" d="{path}" fill="none" stroke="url(#pbln)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" '
             f'filter="url(#pbgl)" style="stroke-dasharray:{length:.0f};--len:{length:.0f}"/>')
    s.append('<path d="M461 35 L476.5 35.6 L475.9 51" fill="none" stroke="#A78BFA" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
    s.append(f'<circle class="mv" r="4.5" fill="#2DB6EB" filter="url(#pbgl)" style="offset-path:path(\'{path}\')"/>')
    for i, (x, y) in enumerate(_SLOTS):
        rank = PB.MAX_BOTS - i
        if rank > len(ranked_sims):
            s.append(f'<g opacity=".8"><circle cx="{x}" cy="{y}" r="14" fill="#0E0918" fill-opacity=".55" stroke="#9D97A5" stroke-width="1.6" '
                     f'stroke-dasharray="3 4"/><path d="M{x - 5} {y} H{x + 5} M{x} {y - 5} V{y + 5}" stroke="#9D97A5" stroke-width="2" '
                     f'stroke-linecap="round"/></g>')
            continue
        sim = ranked_sims[rank - 1]
        live = sim["ok"] and not sim["waiting"]
        ret = sim.get("ret") or 0.0
        ring = (T.UP if ret >= 0 else T.DOWN) if live else T.MUTED
        label = f"{ret:+.1f}%" if live else "—"
        name = sim["bot"]["name"]
        name = name[:13] + "…" if len(name) > 14 else name
        s.append(f'<g><circle class="halo" cx="{x}" cy="{y}" r="15" fill="none" stroke="{ring}" stroke-width="2" style="animation-delay:-{i * 0.5:.1f}s"/>'
                 f'<circle cx="{x}" cy="{y}" r="15" fill="url(#pbnd)" stroke="#0E0918" stroke-width="2"/>'
                 f'<text x="{x}" y="{y + 4.5}" text-anchor="middle" font-size="12.5" font-weight="800" fill="#fff" font-family="{T.FONT}">{rank}</text>'
                 f'<text x="{x}" y="{y - 36}" text-anchor="middle" font-size="13" font-weight="800" fill="{ring}" font-family="{T.FONT}">{label}</text>'
                 f'<text x="{x}" y="{y - 22}" text-anchor="middle" font-size="10.5" fill="#CAC5D1" font-family="{T.FONT}">{T.esc(name)}</text></g>')
    return "".join(s) + "</svg>"


def hero_html(sims, n_bots):
    rk = ranked(sims)
    live = [s for s in sims if s["ok"] and not s["waiting"]]
    ph = phase()
    chips = [f'<span class="chip">{T.icon("smart_toy")}<b>{n_bots}/{PB.MAX_BOTS}</b> {L("bots", "بوتات")}</span>']
    if sims:
        chips.append(f'<span class="chip">{T.icon(PHASES[ph][0])}{T.esc(L(*PHASES[ph][1:3]))} {phase_tag(ph)}</span>')
    if live:
        cap = sum(s["bot"]["capital"] for s in live)
        bal = sum(s["final"] for s in live)
        n_open = sum(s["n_open"] for s in live)
        n_orders = sum(len(s["next_buys"]) + len(s["next_sells"]) for s in live)
        chips.append(f'<span class="chip">{T.icon("account_balance_wallet")}{L("Total balance", "إجمالي الرصيد")} <b>{T.money(bal)}</b>'
                     f'{T.pill((bal / cap - 1) * 100 if cap else 0.0)}</span>')
        if ph == "live":
            chips.append(f'<span class="chip">{T.icon("swap_vert")}{L("Open trades", "صفقات مفتوحة")} <b>{n_open}</b></span>')
        if n_orders and ph == "live":
            chips.append(f'<span class="chip">{T.icon("bolt")}{L("Orders at next open", "أوامر الافتتاح القادم")} <b>{n_orders}</b></span>')
        best = rk[0]
        chips.append(f'<span class="chip">{T.icon("emoji_events")}<b>{T.esc(best["bot"]["name"])}</b>{T.pill(best["ret"])}</span>')
    else:
        chips.append(f'<span class="chip">{T.icon("payments")}{L("Virtual money", "أموال وهمية")}</span>')
        chips.append(f'<span class="chip">{T.icon("candlestick_chart")}{L("Real prices", "أسعار حقيقية")}</span>')
    title = L("Paper <b>Bots</b>", "البوتات <b>الافتراضية</b>")
    tag = L(f"Up to {PB.MAX_BOTS} bots trade with virtual money on real prices: a company, a sector, an industry or all companies, with one "
            "or more strategies or ready-made combined strategies. Each one has a forward test recorded session by session, kept apart "
            "from its historical simulation.",
            f"حتى {PB.MAX_BOTS} بوتات تتداول بأموال وهمية على أسعار حقيقية: شركة أو قطاع أو صناعة أو كل الشركات، باستراتيجية وحدة أو أكثر "
            "أو باستراتيجيات مركّبة جاهزة. لكل بوت تجربة أمامية تُسجَّل جلسة بجلسة، ومفصولة عن محاكاته التاريخية.")
    return (f'<div class="pbhero{" rtl" if is_ar() else ""}"><div class="grid"></div><div class="art">{_hero_art(rk)}</div>'
            f'<div class="txt"><div class="eb">{T.icon("robot_2")}{L("Paper trading lab", "مختبر التداول الافتراضي")}</div>'
            f'<div class="t">{title}</div><div class="tg">{T.esc(tag)}</div><div class="chips">{"".join(chips)}</div>'
            f'<div class="st">{T.market_status(is_ar())}</div></div></div>')


# =====================================================================
# cards: leaderboard with hover actions, selection and "Add Bot"
# =====================================================================
def cbadge(text, kind="neu", ic=None):
    """A badge that stays on one line (a long text ends with …; the whole text shows on hover), for the bot cards."""
    return f'<span class="badge b-{kind}" title="{T.esc(text)}">{T.icon(ic) if ic else ""}<span class="bt">{T.esc(text)}</span></span>'


def status_badge(sim, mk=T.badge):
    if not sim["ok"]:
        if sim.get("why") in ("nohist", "gone5"):
            return mk(L("No historical part", "بدون جزء تاريخي"), "neu", "history")
        return mk(L("Unavailable", "غير متاح"), "neu", "error")
    if sim["waiting"]:
        return mk(L(f"Starts {since_of(sim)}", f"يبدأ {since_of(sim)}"), "neu", "schedule")
    if sim.get("phase") == "sim":
        n = sim.get("sessions") or 0
        return mk(L(f"Backtest · {n:,} sessions", f"اختبار تاريخي · {n:,} جلسة"), "gold", "history")
    nb, ns = len(sim["next_buys"]), len(sim["next_sells"])
    if sim.get("intraday") and nb:
        return mk(L("Enters at the next 5-min candle", "يدخل مع شمعة الـ 5 دقائق القادمة"), "gold", "bolt")
    if sim["bot"]["kind"] == "company":
        if nb:
            return mk(L("Buys at next open", "يشتري عند الافتتاح القادم"), "gold", "bolt")
        if ns:
            return mk(L("Sells at next open", "يبيع عند الافتتاح القادم"), "gold", "bolt")
    elif nb + ns == 1:
        return mk(L("1 order at next open", "أمر عند الافتتاح القادم"), "gold", "bolt")
    elif nb + ns:
        return mk(L(f"{nb + ns} orders at next open", f"{nb + ns} أوامر عند الافتتاح القادم"), "gold", "bolt")
    n = sim["n_open"]
    if n == 1:
        return mk(L("In a trade", "في صفقة"), "acc", "trending_up")
    if n > 1:
        return mk(L(f"{n} open trades", f"{n} صفقات مفتوحة"), "acc", "trending_up")
    return mk(L("Waiting for a signal", "ينتظر إشارة"), "neu", "hourglass_empty")


def head_html(b, logo=None):
    if b["kind"] == "company":
        return T.company(b["value"], "", logo, 32, sub=b["name"])
    return (f'<div class="co">{T.ico(KIND_ICON[b["kind"]], "acc")}<div class="nm"><div class="tk">{T.esc(b["name"])}</div>'
            f'<div class="sub">{T.esc(universe_label(b))}</div></div></div>')


def card_chip(b):
    """(icon, English, Arabic) for the top-left corner of a bot's card."""
    if is_orb(b):
        return "timer", "5-min · long / short", "5 دقائق · شراء / بيع"
    if is_combined(b):
        return "hub", "Combined · stocks", "مركّبة · أسهم"
    return INSTR_CHIP[instrument(b)]


def since_of(sim):
    """The first day of this phase: the forward test's first session, or the bot's start date for the historical simulation
    (the Opening Range Breakout: the first day it has 5-minute prices for)."""
    if sim.get("intraday") and sim.get("start") is not None and not sim.get("waiting"):
        return pd.Timestamp(sim["start"]).strftime("%Y-%m-%d")
    if sim.get("phase") == "live":
        return max(fwd_since(sim["bot"]) or sim["bot"]["start_date"], sim["bot"]["start_date"])
    return sim["bot"]["start_date"]


def until_of(sim):
    """The last session of this phase (the historical simulation ends the day before the forward test starts)."""
    return pd.Timestamp(sim["last_date"]).strftime("%Y-%m-%d") if sim.get("ok") else ""


def fwd_since(b):
    return (b.get("fwd") or {}).get("since")


def phase():
    return ss.get("pb_phase") if ss.get("pb_phase") in PHASES else "live"


def _set_phase(p):
    ss["pb_phase"] = p


def phase_tag(ph):
    return f'<span class="phg {ph}">{T.esc(L(*PHASES[ph][3:5]))}</span>'


def phase_sims(sims, ph):
    """The bots' results in one phase: their forward tests, or their historical simulations (a bot that started on the day
    its forward test began has no historical part)."""
    if ph == "live":
        return sims
    return [s["hist"] if s.get("hist") is not None and not (s["hist"].get("ok") and s["hist"].get("waiting"))
            else {"bot": s["bot"], "ok": False, "why": "nohist", "waiting": False, "phase": "sim"} for s in sims]


def _saved_sessions(sims):
    return sum(len(((s["bot"].get("fwd") or {}).get("eq")) or {}) for s in sims)


def phase_switch(sims):
    """The page-wide switch between the forward tests (LIVE) and the historical simulations (SIM)."""
    ph = phase()
    with st.container(key="pbphase"):
        cols = st.columns(2, gap="small")
        for col, p in zip(cols, ("live", "sim")):
            ic, en, ar_, _, _, sen, sar = PHASES[p]
            with col:
                with st.container(key=f"pbph_{p}"):
                    ui.html(f'<div class="pbph{" on" if p == ph else ""}"><span class="i">{T.icon(ic)}</span>'
                            f'<span class="nm"><b>{T.esc(L(en, ar_))}</b><span>{T.esc(L(sen, sar))}</span></span>{phase_tag(p)}</div>')
                    st.button(L(en, ar_), key=f"pb_ph_{p}", on_click=_set_phase, args=(p,), width="stretch")
    if ph == "live":
        st.caption(L("Forward test: each bot starts it with its full capital on the first session after it is added (or after its trading "
                     "rules change). After every US close, the session's fills, the orders for the next open and the closing balance are "
                     "saved with the engine version; saved sessions are replayed from the record and never recalculated.",
                     "التجربة الأمامية: كل بوت يبدأها برأس ماله كامل من أول جلسة بعد إضافته (أو بعد تغيير قواعد تداوله). بعد كل إغلاق "
                     "للسوق الأمريكي تنحفظ صفقات الجلسة وأوامر الافتتاح القادم ورصيد الإغلاق مع نسخة المحرك، والجلسات المحفوظة "
                     "تنعرض من السجل وما يُعاد حسابها أبداً."))
    else:
        st.caption(L("Historical simulation: each bot's rules replayed on past prices from its start date up to the day its forward test "
                     "began. It is recalculated with the current engine whenever the page opens, so it shows how the rules would have "
                     "done, not signals the bot actually gave.",
                     "المحاكاة التاريخية: قواعد كل بوت مُعاد تشغيلها على أسعار الماضي من تاريخ بدايته إلى اليوم اللي بدأت فيه تجربته "
                     "الأمامية. تنحسب من جديد بالنسخة الحالية للمحرك كل ما تفتح الصفحة، فهي توضح كيف كانت القواعد بتسوي، "
                     "وليست إشارات أعطاها البوت فعلاً."))


def bot_card(rank, sim, logo, selected=False):
    b = sim["bot"]
    ic, en, ar_ = card_chip(b)
    medal = T.icon("emoji_events") if rank == 1 else ""
    ph = "sim" if sim.get("phase") == "sim" else "live"
    top = (f'<div class="top"><span class="it">{T.icon(ic)}<span class="tx">{T.esc(L(en, ar_))}</span></span>'
           f'<span class="rt">{phase_tag(ph)}<span class="rk r{rank}">{medal}#{rank}</span></span></div>')
    badges = f'<div class="bdg">{cbadge(how_label(b, short=True), "vio", "smart_toy")}{status_badge(sim, cbadge)}</div>'
    if sim["ok"] and not sim["waiting"]:
        ret, m = sim["ret"], sim["metrics"]
        spx = "" if sim["bench_ret"] is None else f'<div class="muted" style="font-size:.7rem;margin-top:4px;direction:ltr">S&amp;P 500 {sim["bench_ret"]:+.2f}%</div>'
        win = iso(f"{m['Win Rate %']:.0f}%")
        trades = L(f'{m["Trades"]} trades', f'{m["Trades"]} صفقة') + (f' · {L("win", "نجاح")} {win}' if m["Trades"] else "")
        watch = "" if b["kind"] == "company" else " · " + L(f'{sim["n_symbols"]} stocks', f'{sim["n_symbols"]} سهم')
        when = (f'<span class="nw">{iso(f"{since_of(sim)} → {until_of(sim)}")}</span>' if ph == "sim"
                else f'{L("since", "منذ")} <span class="nw">{iso(since_of(sim))}</span>')
        body = (f'<div class="spk">{_spark_area(sim["equity"], b["capital"], b["id"])}</div>'
                f'<div class="row"><div><div class="muted" style="font-size:.72rem">{L("Balance", "الرصيد")}</div>'
                f'<div style="font-weight:600;font-size:1.1rem;direction:ltr">{T.money(sim["final"])}</div></div>'
                f'<div class="r">{T.pbox(f"{ret:+.2f}%", ret)}{spx}</div></div>'
                f'<div class="pbft">{trades}{watch} · {when}</div>')
    elif sim["ok"]:
        body = (f'<div class="pbft">{L("The forward test starts with the US session of", "التجربة الأمامية تبدأ مع جلسة")} '
                f'{iso(since_of(sim))} · {iso(T.money(b["capital"]))}</div>')
    elif sim.get("why") == "gone5":
        why = L("The 5-minute prices before its forward test are past Yahoo's 60 days.",
                "أسعار الـ 5 دقائق قبل تجربته الأمامية تعدّت الـ 60 يوم حقت ياهو.")
        body = f'<div class="pbft">{why}</div>'
    elif sim.get("why") == "nohist":
        why = L("It started with its forward test, so it has no historical simulation.",
                "بدأ مع تجربته الأمامية، فما عنده محاكاة تاريخية.")
        body = f'<div class="pbft">{why}</div>'
    else:
        why = L("No price data right now.", "لا توجد بيانات أسعار حالياً.") if sim["why"] == "data" else L("Strategy not found.", "الاستراتيجية غير موجودة.")
        body = f'<div class="pbft">{why}</div>'
    return f'<div class="card pbc{" sel" if selected else ""}">{top}{head_html(b, logo)}{badges}<div class="body">{body}</div></div>'


def _spark_area(equity, capital, uid, n=160):
    """The balance over the last sessions as a card-wide area (green above the starting capital, red below), with the
    starting capital as a dotted line."""
    v = np.asarray(equity.tail(n).values, dtype=float)
    v = v[np.isfinite(v)]
    if len(v) < 2:
        return ""
    lo, hi = min(v.min(), capital), max(v.max(), capital)
    rng = (hi - lo) or 1.0
    w, h = 200.0, 52.0
    xs = np.linspace(0, w, len(v))
    ys = h - 3 - (v - lo) / rng * (h - 6)
    base = h - 3 - (capital - lo) / rng * (h - 6)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    col = T.UP if v[-1] >= capital else T.DOWN
    gid = f"pbsp{uid}"
    return (f'<svg viewBox="0 0 {w:.0f} {h:.0f}" preserveAspectRatio="none" aria-hidden="true">'
            f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{col}" stop-opacity=".32"/>'
            f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
            f'<polygon points="0,{h:.0f} {pts} {w:.0f},{h:.0f}" fill="url(#{gid})"/>'
            f'<line x1="0" y1="{base:.1f}" x2="{w:.0f}" y2="{base:.1f}" stroke="#9D97A5" stroke-width="1" stroke-dasharray="3 4" '
            f'vector-effect="non-scaling-stroke" opacity=".6"/>'
            f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>')


# the site's logo tile (blue-violet, rounded) with a white plus and the cyan trend arrow; a dashed orbit turns around it
PLUS_SVG = ('<svg viewBox="0 0 92 92" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            '<defs><linearGradient id="pbaddg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3B8BEB"/>'
            '<stop offset="1" stop-color="#7B45F0"/></linearGradient>'
            '<filter id="pbaddf" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="5"/></filter></defs>'
            '<g class="orbit"><circle cx="46" cy="46" r="43" fill="none" stroke="#2DB6EB" stroke-opacity=".45" stroke-width="1.4" stroke-dasharray="2 7"/>'
            '<circle cx="46" cy="3" r="3.2" fill="#2DB6EB"/><circle cx="89" cy="46" r="2" fill="#A78BFA"/></g>'
            '<g class="tile"><rect x="16" y="20" width="60" height="60" rx="17" fill="#3B8BEB" opacity=".45" filter="url(#pbaddf)"/>'
            '<rect x="16" y="16" width="60" height="60" rx="17" fill="url(#pbaddg)"/>'
            '<path d="M22 30 Q22 22 30 22 H62 Q70 22 70 30" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="2" stroke-linecap="round"/>'
            '<g class="cross"><path d="M46 32 V60 M32 46 H60" stroke="#fff" stroke-width="6.5" stroke-linecap="round"/></g>'
            '<path class="spark" d="M51 67 L57 62 L61 64 L69 56" fill="none" stroke="#2DB6EB" stroke-width="3.2" stroke-linecap="round" '
            'stroke-linejoin="round" style="stroke-dasharray:40"/>'
            '<path d="M65 55.6 L69.4 55.9 L69.1 60.3" fill="none" stroke="#2DB6EB" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>'
            '</g></svg>')


def add_card(n_bots):
    left = PB.MAX_BOTS - n_bots
    slots = "".join(f'<span class="{"on" if i < n_bots else "off"}"></span>' for i in range(PB.MAX_BOTS))
    return (f'<div class="card pbc pbadd"><div class="plus">{PLUS_SVG}</div><div class="ttl">{L("Add Bot", "أضف بوت")}</div>'
            f'<div class="sub">{L(f"{left} of {PB.MAX_BOTS} slots left", f"باقي {left} من {PB.MAX_BOTS} أماكن")}</div>'
            f'<div class="slots">{slots}</div></div>')


def ranked(sims):
    return sorted(sims, key=lambda s: (not (s["ok"] and not s["waiting"]), -(s.get("ret") or 0.0) if s["ok"] else 0.0))


def _selected(ids):
    sel = [i for i in ss.get("pb_selected", []) if i in ids]
    ss["pb_selected"] = sel
    return sel


def _toggle(bot_id):
    sel = list(ss.get("pb_selected", []))
    ss["pb_selected"] = [i for i in sel if i != bot_id] if bot_id in sel else sel + [bot_id]


def _select_all(ids):
    ss["pb_selected"] = list(ids)


def _select_none():
    ss["pb_selected"] = []


def _open(mode, bot=None):
    """Card buttons: remember which dialog to open on this run (add / edit / delete) and fill the form."""
    if mode == "add":
        _reset_form()
    elif mode == "edit":
        _load_form(bot)
    ss["pb_open"] = (mode, bot["id"] if bot else None)


def leaderboard(sims, n_bots, can_add):
    ui.sec("leaderboard", "Leaderboard", "ترتيب البوتات")
    ids = [s["bot"]["id"] for s in sims]
    sel = _selected(ids)
    if sims:
        a, b, c, _ = st.columns([1.25, 1.25, 1, 4], vertical_alignment="center")
        a.button(L("Select all", "تحديد الكل"), icon=":material/done_all:", key="pb_selall", on_click=_select_all, args=(ids,),
                 type="primary" if len(sel) < len(ids) else "secondary", width="stretch")
        b.button(L("Clear selection", "إلغاء التحديد"), icon=":material/deselect:", key="pb_selnone", on_click=_select_none,
                 disabled=not sel, width="stretch")
        if PB.admin_mode() == "password" and ss.get("pb_admin"):
            if c.button(L("Lock", "قفل"), icon=":material/lock:", key="pb_lock", width="stretch"):
                ss.pb_admin = False
                st.rerun()
    lg = data.logos([s["bot"]["value"] for s in sims if s["bot"]["kind"] == "company"])
    items = [(i, s) for i, s in enumerate(ranked(sims), 1)] + ([("add", None)] if can_add else [])
    per_row = 5
    for r in range(0, len(items), per_row):
        cols = st.columns(per_row)
        for col, (rank, sim) in zip(cols, items[r:r + per_row]):
            with col:
                if rank == "add":
                    with st.container(key="pbcard_add"):
                        ui.html(add_card(n_bots))
                        st.button(L("Add Bot", "أضف بوت"), key="pb_pick_add", on_click=_open, args=("add",), width="stretch")
                    continue
                b = sim["bot"]
                with st.container(key=f"pbcard_{b['id']}"):
                    ui.html(bot_card(rank, sim, lg.get(b["value"]), b["id"] in sel))
                    st.button(b["name"], key=f"pb_pick_{b['id']}", on_click=_toggle, args=(b["id"],), width="stretch")
                    st.button(L("Edit", "تعديل"), icon=":material/edit:", key=f"pb_edit_{b['id']}", on_click=_open, args=("edit", b),
                              help=L("Edit this bot", "تعديل البوت"))
                    st.button(L("Delete", "حذف"), icon=":material/delete:", key=f"pb_trash_{b['id']}", on_click=_open, args=("delete", b),
                              help=L("Delete this bot", "حذف البوت"))
    return sel


def compare_chart(sims, spy):
    series, seen = {}, set()
    for s in sims:
        if s["ok"] and not s["waiting"] and len(s["equity"]) >= 2:
            name = s["bot"]["name"]
            if name in seen:
                name = f'{name} (#{s["bot"]["id"]})'
            seen.add(name)
            series[name] = (s["equity"] / s["bot"]["capital"] - 1) * 100
    if not series:
        return
    if phase() == "sim":
        ui.sec("stacked_line_chart", "Return over the historical simulation", "العائد خلال المحاكاة التاريخية")
    else:
        ui.sec("stacked_line_chart", "Return since the forward test began", "العائد منذ بداية التجربة الأمامية")
    first = min(v.index[0] for v in series.values())
    spx_name = "S&P 500 (SPY)"
    if spy is not None and not spy.empty:
        sp = spy["Close"][spy.index >= first]
        if len(sp) >= 2:
            series[spx_name] = (sp / sp.iloc[0] - 1) * 100
    fig = charts.lines(series, None, suffix="%", height=380, dec=2)
    fig.update_traces(selector=dict(name=spx_name), line=dict(dash="dot", color=T.MUTED, width=1.6))
    ui.chart(fig, key="pb_cmp")
    st.caption(L("Each bot is measured from its own start date; the S&P 500 line starts with the oldest bot.",
                 "كل بوت يُقاس من تاريخ بدايته؛ وخط إس آند بي 500 يبدأ مع أقدم بوت."))


# =====================================================================
# a "view": one bot, or several bots added together (same keys, so the dashboard and panels serve both)
# =====================================================================
def _open_value(op):
    """Market value of open rows: shares x price, or contracts x 100 x premium."""
    if op.empty:
        return pd.Series(dtype=float)
    opt = op["Type"].isin(["Call", "Put"])
    return pd.Series(np.where(opt, op["Shares"] * 100 * op["Exit"], op["Shares"] * op["Stock Exit"]), index=op.index, dtype=float)


def single_view(sim, in_tab=False):
    b = sim["bot"]
    tr = sim["trades"].assign(Bot=b["name"])
    op = tr[tr["Exit Reason"] == "Open"]
    cash = sim.get("cash")
    if cash is None:
        cash = sim["final"] - float(_open_value(op).sum())
    if abs(cash) < 0.01:                     # a fully invested bot shows $0, not -$0
        cash = 0.0
    has_spy = sim["bench"] is not None
    return {"key": str(b["id"]) + ("s" if sim.get("phase") == "sim" else ""), "multi": False, "phase": sim.get("phase", "live"),
            "until": until_of(sim), "group": b["kind"] != "company", "n_bots": 1, "cap": float(b["capital"]),
            "final": float(sim["final"]), "ret": float(sim["ret"]), "bench_ret": sim["bench_ret"], "base_ret": sim["group_ret"],
            "equity": sim["equity"], "bench": sim["bench"] if has_spy else sim["group"],
            "bench_name": "S&P 500 (SPY)" if has_spy else L("Buy & Hold", "شراء واحتفاظ"), "npos": sim["npos"], "trades": tr,
            "cash": float(cash), "name": b["name"], "scope": b["name"] if in_tab else "", "sessions": sim["sessions"], "since": since_of(sim), "opts": instrument(b) != "stock",
            "last": pd.Timestamp(sim["last_date"])}


def combined_view(sims):
    """Several bots as one portfolio: balances, benchmarks and positions added up day by day (a bot holds its capital
    before its start date), trades pooled."""
    live = [s for s in sims if s["ok"] and not s["waiting"] and len(s["equity"])]
    if not live:
        return None
    idx = live[0]["equity"].index
    for s in live[1:]:
        idx = idx.union(s["equity"].index)

    def fill(x, cap):
        return x.reindex(idx).ffill().fillna(cap)

    eq = sum(fill(s["equity"], s["bot"]["capital"]) for s in live)
    bench = sum(fill(s["bench"] if s["bench"] is not None else s["group"], s["bot"]["capital"]) for s in live)
    npos = sum(s["npos"].reindex(idx).fillna(0) for s in live)
    views = [single_view(s) for s in live]
    cap = float(sum(s["bot"]["capital"] for s in live))
    final = float(eq.iloc[-1])
    frames = [v["trades"] for v in views if len(v["trades"])]
    trades = pd.concat(frames, ignore_index=True) if frames else views[0]["trades"]
    for c in ("Entry", "Exit", "Shares", "P&L $", "P&L %", "Stock Entry", "Stock Exit", "Fees", "Stop", "Target"):
        trades[c] = pd.to_numeric(trades[c], errors="coerce")        # an empty frame would turn the pooled columns into objects
    return {"key": "all" + ("s" if live[0].get("phase") == "sim" else ""), "name": "", "scope": L(f"all {len(live)} selected bots", f"كل البوتات المحددة ({len(live)})"), "multi": True, "group": True, "n_bots": len(live), "cap": cap, "final": final,
            "ret": (final / cap - 1) * 100, "bench_ret": float((bench.iloc[-1] / cap - 1) * 100), "base_ret": None,
            "equity": eq, "bench": bench, "bench_name": "S&P 500 (SPY)", "npos": npos,
            "trades": trades, "cash": float(sum(v["cash"] for v in views)),
            "sessions": max(s["sessions"] for s in live), "since": min(since_of(s) for s in live), "until": max(until_of(s) for s in live),
            "phase": live[0].get("phase", "live"),
            "opts": any(v["opts"] for v in views), "last": max(v["last"] for v in views), "sims": live}


def view_stats(v):
    tr = v["trades"]
    return autotrader.stats({"trades": tr[tr["Exit Reason"] != "Open"], "open": tr[tr["Exit Reason"] == "Open"], "equity": v["equity"],
                             "bench": v["bench"], "positions": v["npos"], "capital": v["cap"]})


def view_logos(v):
    tr = v["trades"]
    op = tr[tr["Exit Reason"] == "Open"]
    recent = tr[tr["Exit Reason"] != "Open"].sort_values("Exit Date", ascending=False).head(12)
    return data.logos(list(dict.fromkeys(list(op["Symbol"]) + list(recent["Symbol"])))[:60])


# =====================================================================
# dashboard: KPIs · win-rate / profit-factor cards · what worked
# =====================================================================
def kpi_row(v):
    tr = v["trades"]
    op = tr[tr["Exit Reason"] == "Open"]
    open_pnl = float(op["P&L $"].sum()) if len(op) else 0.0
    invested = max(v["final"] - v["cash"], 0.0)
    inv_pct = invested / v["final"] * 100 if v["final"] > 0 else 0.0
    if v["multi"]:
        ret_sub = L(f"{v['n_bots']} bots together", f"{v['n_bots']} بوتات مع بعض")
    else:
        ret_sub = (L("Group bought equally ", "المجموعة بالتساوي ") if v["group"] else L("Buy & hold ", "شراء واحتفاظ ")) + iso(f"{v['base_ret']:+.2f}%")
    diff = None if v["bench_ret"] is None else v["ret"] - v["bench_ret"]
    n_open = len(op)
    open_sub = L(f"{n_open} open positions", f"{n_open} مراكز مفتوحة") if n_open != 1 else L("1 open position", "مركز مفتوح واحد")
    tiles = [
        T.kpi("account_balance_wallet", L("Balance", "الرصيد"), T.money(v["final"]), L("start ", "البداية ") + iso(T.money(v["cap"])), T.cls(v["ret"])),
        T.kpi("trending_up", L("Return", "العائد"), f"{v['ret']:+.2f}%", ret_sub, T.cls(v["ret"])),
        T.kpi("show_chart", L("vs S&P 500", "مقابل إس آند بي"), "—" if diff is None else f"{diff:+.2f}%",
              "" if diff is None else f"S&amp;P {v['bench_ret']:+.2f}%", None if diff is None else T.cls(diff)),
        T.kpi("hourglass_top", L("Open P&L", "ربح المراكز المفتوحة"), sm(open_pnl), open_sub, T.cls(open_pnl) if n_open else None),
        T.kpi("savings", L("Cash", "الكاش"), T.money(v["cash"]), L("invested ", "مستثمر ") + iso(f"{inv_pct:.0f}%"), None),
        (T.kpi("history", L("Simulated", "مدة المحاكاة"), f"{v['sessions']:,}", L("sessions · ", "جلسة · ") + iso(f"{v['since']} → {v['until']}"), None)
         if v.get("phase") == "sim" else
         T.kpi("calendar_month", L("Forward test", "التجربة الأمامية"), f"{v['sessions']:,}", L("sessions since ", "جلسة منذ ") + iso(v["since"]), None)),
    ]
    return '<div class="pbk">' + "".join(tiles) + "</div>"


def _contrib(closed, by, cap):
    """Each group's share of the return, % of the starting capital (so the bars add up to the closed-trade return)."""
    g = closed.groupby(by).agg(pnl=("P&L $", "sum"), n=("P&L $", "size"), wins=("P&L $", lambda x: int((x > 0).sum())))
    g["pct"] = g["pnl"].astype(float) / cap * 100
    return g


def _ww_card(title, sub, icon, g, labels, logos=None, syms=None):
    """One 'what worked' panel: a row per group with a bar that grows left (loss) or right (gain) from the middle, its share of
    the return, and its trades and win rate. Best first."""
    g = g.assign(_lab=labels).sort_values("pct", ascending=False)
    top = float(g["pct"].abs().max() or 1.0)
    rows = []
    for key, r in g.iterrows():
        w = abs(float(r["pct"])) / top * 100
        pos = r["pct"] >= 0
        lead = ""
        if syms is not None:
            lead = T.logo_circle(str(key), (logos or {}).get(str(key)), 20)
        name = (f'<a class="wwl" href="{T.esc(ui.href(str(key)))}" target="_self">{lead}<b>{T.esc(r["_lab"])}</b></a>' if syms is not None
                else f'<span class="wwl"><b>{T.esc(r["_lab"])}</b></span>')
        info = L(f"{int(r['n'])} trades · win {r['wins'] / r['n'] * 100:.0f}%", f"{int(r['n'])} صفقة · نجاح {r['wins'] / r['n'] * 100:.0f}%")
        bar = f'<i style="width:{w:.1f}%"></i>'
        rows.append(f'<div class="wwr" title="{T.esc(sm(r["pnl"]) + " · " + info)}"><div class="wwn">{name}</div>'
                    f'<div class="wwt"><span class="h n">{"" if pos else bar}</span><span class="h p">{bar if pos else ""}</span></div>'
                    f'<b class="wwv {"up" if pos else "dn"}">{r["pct"]:+.2f}%</b></div>')
    return (f'<div class="wwc"><div class="wwh"><span class="i">{T.icon(icon)}</span><div><b>{T.esc(title)}</b>'
            f'<span>{T.esc(sub)}</span></div></div><div class="wwb">{"".join(rows)}</div></div>')


def what_worked(v):
    tr = v["trades"]
    closed = tr[tr["Exit Reason"] != "Open"]
    ui.html(f'<div class="pbsub">{T.icon("pie_chart")}{L("What worked", "ماذا نجح")}'
            f'<span class="muted">· {L("closed trades, share of the return in % of the starting capital", "الصفقات المغلقة، نصيبها من العائد (% من رأس المال)")}</span></div>')
    if closed.empty:
        st.caption(L("This part fills in after the first closed trade.", "هذا الجزء يمتلئ بعد أول صفقة مغلقة."))
        return
    cards = []
    if v["group"]:
        g = _contrib(closed, "Symbol", v["cap"])
        g = g.loc[list(dict.fromkeys(list(g["pct"].nlargest(6).index) + list(g["pct"].nsmallest(6).index)))]
        cards.append(_ww_card(L("By stock", "حسب السهم"), L("The 6 best and the 6 worst", "أفضل 6 وأسوأ 6"), "show_chart", g, list(g.index),
                              data.logos(list(g.index)), syms=True))
    else:
        g = _contrib(closed, "Exit Reason", v["cap"])
        cards.append(_ww_card(L("By exit reason", "حسب سبب الخروج"), L("How the trades ended", "كيف انتهت الصفقات"), "logout", g,
                              [L(x, EXIT_AR.get(x, x)) for x in g.index]))
    g = _contrib(closed, "Strategy", v["cap"])
    cards.append(_ww_card(L("By strategy", "حسب الاستراتيجية"), L("Which rules paid", "أي القواعد ربّحت"), "smart_toy", g,
                          [strat_short(k) for k in g.index]))
    g = _contrib(closed, "Type", v["cap"])
    if len(g) > 1:
        cards.append(_ww_card(L("By type", "حسب النوع"), L("Stocks and options", "أسهم وأوبشن"), "category", g,
                              [L(*TYPE_NAME.get(k, (k, k))) for k in g.index]))
    else:
        g = _contrib(closed.assign(Side=np.where(closed["P&L $"] > 0, "win", "loss")), "Side", v["cap"])
        cards.append(_ww_card(L("Wins and losses", "الرابحة والخاسرة"), L("Their share of the return", "نصيبها من العائد"), "balance", g,
                              [L("Winning trades", "صفقات رابحة") if k == "win" else L("Losing trades", "صفقات خاسرة") for k in g.index]))
    ui.html(f'<div class="wwg">{"".join(cards)}</div>')


def dashboard(v):
    if v["multi"]:
        ui.sec("space_dashboard", "Portfolio dashboard", "لوحة أداء المحفظة")
        chips = "".join(f'<span class="c">{T.icon("smart_toy")}{T.esc(s["bot"]["name"])} {T.pill(s["ret"])}</span>' for s in v["sims"])
        ui.html(f'<div class="pbsel">{chips}</div>')
    else:
        ui.sec("space_dashboard", "Dashboard", "لوحة الأداء")
    ui.html(kpi_row(v))
    if v["multi"] and v["opts"]:
        st.caption(L(OPT_EST_EN, OPT_EST_AR))
    ui.html(tdash.kpi_cards(view_stats(v), v["cap"]))
    what_worked(v)


# =====================================================================
# panels: open positions · recent trades
# =====================================================================
def _asset(r, lg):
    """Logo, symbol and a short note on one line: the contract for options, the sector for stocks."""
    sym = r["Symbol"]
    if r["Type"] in ("Call", "Put"):
        sub = " ".join(str(r["Contract"]).split(" ")[1:])            # "205C 2026-10-02"
    else:
        sec = PB.sector_of(sym)
        sub = sector_name(sec) if sec else ""
    return (f'<a class="as" href="{ui.href(sym)}" target="_self">{T.logo_circle(sym, lg.get(sym), 22)}<b>{T.esc(sym)}</b>'
            f'<span class="m">{T.esc(sub)}</span></a>')


def _chg(a, b):
    c = (float(b) / float(a) - 1) * 100 if float(a) else 0.0
    return f'<span class="{"up" if c >= 0 else "dn"}">{c:+.1f}%</span>'


def _plan(r):
    """How the open position will close, on one line: stop / target for shares, expiry + target / stop for options."""
    now = float(r["Exit"])
    if r["Type"] in ("Call", "Put"):
        exp = pd.Timestamp(r["Expiry"])
        left = max((exp - pd.Timestamp(r["Exit Date"])).days, 0)
        return (f'{exp:%Y-%m-%d} <span class="m">· {L(f"{left}d left", f"باقي {left} يوم")}</span> '
                f'<span class="up">TP {_fp(r["Target"])}</span> <span class="dn">SL {_fp(r["Stop"])}</span>')
    parts = []
    if pd.notna(r["Stop"]):
        parts.append(f'<span class="dn">SL {_fp(r["Stop"])}</span><span class="m"> {(float(r["Stop"]) / now - 1) * 100:+.1f}%</span>')
    if pd.notna(r["Target"]):
        parts.append(f'<span class="up">TP {_fp(r["Target"])}</span><span class="m"> {(float(r["Target"]) / now - 1) * 100:+.1f}%</span>')
    return " · ".join(parts) or f'<span class="m">{L("on the signal", "بالإشارة")}</span>'


def _held(bars, intra=False):
    """How long a trade was held: sessions, or minutes for 5-minute trades."""
    if intra:
        m = max(int(bars), 0) * 5
        h, mm = divmod(m, 60)
        if not h:
            return L(f"{m} min", f"{m} دقيقة")
        return L(f"{h} h {mm} min", f"{h} س {mm} د") if mm else L(f"{h} h", f"{h} ساعة")
    if bars <= 0:
        return L("today", "اليوم")
    return L("1 session", "جلسة وحدة") if bars == 1 else L(f"{bars} sessions", f"{bars} جلسة")


def _intra(r):
    """A trade of the Opening Range Breakout (5-minute candles: dates carry the time)."""
    return r["Strategy"] == PBK.ORB


def _when(ts, intra=False):
    ts = pd.Timestamp(ts)
    return f"{ts:%Y-%m-%d %H:%M}" if intra else f"{ts:%Y-%m-%d}"


def _pnl_cell(r):
    return f'<td class="r">{_chg(1, 1 + float(r["P&L %"]) / 100)}{T.pbox(sm(r["P&L $"]), r["P&L $"])}</td>'


def _chip(label, value_html):
    return f'<span class="c">{T.esc(label)}{value_html}</span>'


def _title(v, en, ar_):
    """Panel / section title; with several bots it also says whose trades these are."""
    return L(en, ar_) + (f" · {v['scope']}" if v.get("scope") else "")


def _table(heads, rows, right_last=True):
    th = "".join(f"<th>{h}</th>" for h in heads[:-1]) + f'<th class="{"r" if right_last else ""}">{heads[-1]}</th>'
    return f'<div class="pbscroll"><table class="pbt"><thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def open_panel(v, lg):
    tr = v["trades"]
    op = tr[tr["Exit Reason"] == "Open"].copy()
    val = _open_value(op)
    n, invested = len(op), float(val.sum()) if len(op) else 0.0
    open_pnl = float(op["P&L $"].sum()) if n else 0.0
    pct = invested / v["final"] * 100 if v["final"] > 0 else 0.0
    chips = (_chip(L("Positions", "المراكز"), f"<b>{n}</b>") + _chip(L("Invested", "مستثمر"), f"<b>{T.money(invested)} · {pct:.0f}%</b>")
             + _chip(L("Cash", "الكاش"), f"<b>{T.money(v['cash'])}</b>") + _chip(L("Open P&L", "الربح المفتوح"), T.pbox(sm(open_pnl), open_pnl)))
    sim_ = v.get("phase") == "sim"
    title = _title(v, "Open when the simulation ended", "المفتوحة عند نهاية المحاكاة") if sim_ else _title(v, "Open positions", "المراكز المفتوحة")
    head = (f'<div class="hd"><div class="tt">{T.icon("work")}{T.esc(title)}{"" if sim_ else "<span class=live></span>"}</div>'
            f'<div class="sum">{chips}</div></div>')
    if not n:
        empty = (L("No positions were open when the simulation ended.", "ما كان فيه مراكز مفتوحة عند نهاية المحاكاة.") if sim_ else
                 L("No open positions right now. The bot is waiting for a signal.", "لا توجد مراكز مفتوحة حالياً. البوت ينتظر إشارة."))
        ui.html(f'<div class="pbp">{head}<div class="pbempty">{T.icon("hourglass_empty")}{empty}</div></div>')
        return
    rows = []
    for i in op.assign(_v=val).sort_values("_v", ascending=False).index:
        r = op.loc[i]
        opt = r["Type"] in ("Call", "Put")
        value = float(val.loc[i])
        w = value / v["final"] * 100 if v["final"] > 0 else 0.0
        qty = L(f'{int(r["Shares"])} contracts', f'{int(r["Shares"])} عقد') if opt else L(f'{r["Shares"]:,.2f} sh', f'{r["Shares"]:,.2f} سهم')
        tip = f' title="{_est_tip(r)}"' if opt else ""
        est = f' <span class="m est">{L(*EST)}</span>' if opt else ""
        who = f'<td><span class="m">{T.esc(r["Bot"])}</span></td>' if v["multi"] else ""
        intra = _intra(r)
        rows.append(f'<tr><td>{_asset(r, lg)}</td><td>{type_badge(r["Type"])}</td>{who}<td>{T.esc(strat_short(r["Strategy"]))}</td>'
                    f'<td>{_when(r["Entry Date"], intra)} <span class="m">· {_held(int(r["Bars"]), intra)}</span></td>'
                    f'<td{tip}>{_fp(r["Entry"])} → <b>{_fp(r["Exit"])}</b> {_chg(r["Entry"], r["Exit"])}{est}</td>'
                    f'<td>{qty} <span class="m">· {T.money(value)} · {w:.1f}%</span></td><td>{_plan(r)}</td>{_pnl_cell(r)}</tr>')
    heads = ([L("Asset", "الأصل"), L("Type", "النوع")] + ([L("Bot", "البوت")] if v["multi"] else [])
             + [L("Strategy", "الاستراتيجية"), L("Opened", "الفتح"),
                (L("Entry → last", "الدخول ← الأخير") if sim_ else L("Entry → now", "الدخول ← الآن")), L("Size", "الحجم"),
                L("Exit plan", "خطة الخروج"), L("Open P&amp;L", "الربح")])
    ui.html(f'<div class="pbp">{head}{_table(heads, rows)}</div>')


def recent_panel(v, lg, n=10):
    tr = v["trades"]
    closed = tr[tr["Exit Reason"] != "Open"].sort_values("Exit Date", ascending=False, kind="stable")
    total = len(closed)
    link = f'<a class="pblink" href="#pb-all-{v["key"]}" target="_self">{L("Full list below", "القائمة الكاملة بالأسفل")}{T.icon("south")}</a>'
    chips = _chip(L("Last", "آخر"), f"<b>{min(n, total)} / {total}</b>")
    if total:
        wr = (closed["P&L $"] > 0).mean() * 100
        net = float(closed["P&L $"].sum())
        chips += _chip(L("Win rate", "نسبة النجاح"), f"<b>{wr:.0f}%</b>") + _chip(L("Closed P&L", "ربح المغلقة"), T.pbox(sm(net), net))
    head = (f'<div class="hd"><div class="tt">{T.icon("receipt_long")}{T.esc(_title(v, "Recent trades", "آخر الصفقات"))}</div>'
            f'<div class="sum">{chips}{link}</div></div>')
    if not total:
        ui.html(f'<div class="pbp">{head}<div class="pbempty">{T.icon("hourglass_empty")}'
                f'{L("No closed trades yet.", "لا توجد صفقات مغلقة بعد.")}</div></div>')
        return
    rows = []
    for _, r in closed.head(n).iterrows():
        opt = r["Type"] in ("Call", "Put")
        tip = f' title="{_est_tip(r)}"' if opt else ""
        est = f' <span class="m est">{L(*EST)}</span>' if opt else ""
        who = f'<td><span class="m">{T.esc(r["Bot"])}</span></td>' if v["multi"] else ""
        intra = _intra(r)
        span = (f'{_when(r["Entry Date"], True)} → {pd.Timestamp(r["Exit Date"]):%H:%M}' if intra
                else f'{_when(r["Entry Date"])} → {_when(r["Exit Date"])}')
        rows.append(f'<tr><td>{_asset(r, lg)}</td><td>{type_badge(r["Type"])}</td>{who}<td>{T.esc(strat_short(r["Strategy"]))}</td>'
                    f'<td>{span} <span class="m">· {_held(int(r["Bars"]), intra)}</span></td>'
                    f'<td{tip}>{_fp(r["Entry"])} → <b>{_fp(r["Exit"])}</b>{est}</td><td>{exit_badge(r["Exit Reason"])}</td>{_pnl_cell(r)}</tr>')
    heads = ([L("Asset", "الأصل"), L("Type", "النوع")] + ([L("Bot", "البوت")] if v["multi"] else [])
             + [L("Strategy", "الاستراتيجية"), L("Held", "المدة"), L("Entry → exit", "الدخول ← الخروج"), L("Exit reason", "سبب الخروج"), "P&amp;L"])
    ui.html(f'<div class="pbp">{head}{_table(heads, rows)}</div>')


# =====================================================================
# charts · monthly returns (a month opens its calendar) · all trades
# =====================================================================
def balance_chart(v):
    ui.sec("show_chart", "Balance vs the market", "الرصيد مقابل السوق")
    ui.chart(charts.equity_chart(v["equity"], v["bench"], (L("Bot", "البوت"), v["bench_name"], L("Drawdown %", "التراجع %"))),
             key=f"pb_eq_{v['key']}")


def pnl_charts(v):
    tr = v["trades"]
    daily = tdash._daily(tr[tr["Exit Reason"] != "Open"])
    if len(daily):
        ui.sec("bar_chart", "Profit of the closed trades", "ربح الصفقات المغلقة")
        c1, c2 = st.columns(2)
        ui.chart(charts.area(daily["pnl"].cumsum(), L("Cumulative P&L (closed trades)", "الربح التراكمي (الصفقات المغلقة)"), T.CYAN, 300),
                 key=f"pb_cum_{v['key']}", container=c1)
        ui.chart(charts.signed_bars(daily.index, daily["pnl"].values, L("Daily P&L", "الربح اليومي"), 300), key=f"pb_day_{v['key']}",
                 container=c2)


# the colours of the monthly heatmap: dark for small months, stronger green / red for big ones
_HEAT_STOPS = [(0.0, "#A8323F"), (0.35, "#5A1F29"), (0.5, "#2A2535"), (0.65, "#17482F"), (1.0, "#1F8A4E")]


def _heat_color(t):
    for (t0, c0), (t1, c1) in zip(_HEAT_STOPS, _HEAT_STOPS[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            a, b = (tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in (c0, c1))
            return "#" + "".join(f"{round(x + (y - x) * u):02X}" for x, y in zip(a, b))
    return _HEAT_STOPS[-1][1]


def _heat_class(x, top):
    """p1..p4 / n1..n4 by the month's size against the biggest month; z for flat."""
    if not x:
        return "z"
    return ("p" if x > 0 else "n") + str(min(4, int(abs(x) / top * 4) + 1))


HEAT_CSS = "<style>" + "".join(
    f'[class*="st-key-pbmo_{s}{k}"] button {{ background:{_heat_color(0.5 + (0.5 if s == "p" else -0.5) * (k - 0.5) / 4)} !important; }}'
    for s in "pn" for k in range(1, 5)) + '[class*="st-key-pbmo_z"] button { background:#2A2535 !important; }</style>'


def _pick_month(ck, ym):
    ss[ck] = None if ss.get(ck) == ym else ym


def _close_month(ck):
    ss[ck] = None


def month_grid(v):
    table = engine.monthly_returns(v["equity"])
    if table.empty:
        return
    key = v["key"]
    ck = f"pb_cal_{key}"
    have = {f"{y}_{m:02d}" for y, row in table.iterrows() for m, x in row.items() if pd.notna(x)}
    if ss.get(ck) not in have:
        ss[ck] = None
    cur = ss[ck]
    ui.sec("calendar_month", "Monthly returns", "العوائد الشهرية")
    st.caption(L("Click a month to open its calendar of daily results; click it again to close it.",
                 "اضغط على أي شهر يفتح لك تقويمه بنتائج كل يوم، واضغطه مرة ثانية يتقفل."))
    names = tdash.MONTHS_AR if is_ar() else MONTHS_EN
    top = float(np.nanmax(np.abs(table.to_numpy(float)))) or 1.0
    spec = [1.05] + [1] * 12 + [1.15]
    with st.container(key=f"pbmg_{key}"):
        hc = st.columns(spec, gap="small")
        hc[0].markdown(f'<div class="pbmh">{L("Year", "السنة")}</div>', unsafe_allow_html=True)
        for i in range(12):
            hc[i + 1].markdown(f'<div class="pbmh">{names[i]}</div>', unsafe_allow_html=True)
        hc[13].markdown(f'<div class="pbmh">{L("Total", "المجموع")}</div>', unsafe_allow_html=True)
        for y, row in table.iterrows():
            cols = st.columns(spec, gap="small", vertical_alignment="center")
            cols[0].markdown(f'<div class="pbmy">{y}</div>', unsafe_allow_html=True)
            for m in range(1, 13):
                x = row.get(m)
                if pd.isna(x):
                    cols[m].markdown('<div class="pbme"></div>', unsafe_allow_html=True)
                    continue
                ym = f"{y}_{m:02d}"
                x1 = round(float(x), 1)
                kind = _heat_class(x1, top)
                on = "_on" if cur == ym else ""
                cols[m].button(f"{x1:+.1f}%" if x1 else "0.0%", key=f"pbmo_{kind}{on}_{key}_{ym}", on_click=_pick_month, args=(ck, ym), width="stretch",
                               help=L(f"Open the calendar of {names[m - 1]} {y}", f"افتح تقويم {names[m - 1]} {y}"))
            tot = (np.prod(1 + row.dropna().to_numpy(float) / 100) - 1) * 100
            cols[13].markdown(f'<div class="pbmt">{T.pbox(f"{tot:+.1f}%", tot)}</div>', unsafe_allow_html=True)
    if not cur:
        return
    y, m = (int(p) for p in cur.split("_"))
    tr = v["trades"]
    closed = tr[tr["Exit Reason"] != "Open"]
    daily = tdash._daily(closed)
    mtd = daily[(daily.index.year == y) & (daily.index.month == m)] if len(daily) else daily
    pnl = float(mtd["pnl"].sum()) if len(mtd) else 0.0
    with st.container(key=f"pbcalbox_{key}"):
        a, b = st.columns([6, 1], vertical_alignment="center")
        a.markdown(f'<div class="pbct">{T.icon("calendar_month")}{tdash.month_name(y, m)}'
                   f'<span class="muted">{L("Month return", "عائد الشهر")}</span>{T.pill(table.loc[y, m])}'
                   f'<span class="muted">{L("Closed P&L", "ربح المغلقة")}</span>{T.pbox(sm(pnl), pnl)}'
                   f'<span class="muted">{len(mtd)} {L("trading days with closes", "أيام فيها إغلاق صفقات")}</span></div>',
                   unsafe_allow_html=True)
        b.button(L("Close", "إغلاق"), icon=":material/close:", key=f"pbcal_x_{key}", on_click=_close_month, args=(ck,), width="stretch")
        ui.html(tdash.calendar_html(closed, y, m))
        if not len(mtd):
            st.caption(L("No trade closed in this month; the return comes from positions that were still open.",
                         "ما انقفلت صفقات في هذا الشهر؛ العائد جاي من مراكز كانت مفتوحة."))


def price_chart_section(sim):
    """The bot's trades on one stock's chart, from a little before the start."""
    b, tr = sim["bot"], sim["trades"]
    names = list(b["strategies"])
    ui.sec("candlestick_chart", "Trades on the chart", "الصفقات على الشارت")
    left, right = st.columns([3, 1.3], vertical_alignment="bottom")
    if b["kind"] != "company":
        traded = list(dict.fromkeys(tr.sort_values("Entry Date", ascending=False)["Symbol"]))
        if not traded:
            st.caption(L("No trades yet. The chart appears after the first trade.", "لا توجد صفقات بعد. الشارت يظهر بعد أول صفقة."))
            return
        ui.valid(f"pb_chart_{b['id']}", traded)
        sym = left.selectbox(L("Stock", "السهم"), traded, key=f"pb_chart_{b['id']}")
        full = data.history(sym, PB.period_for(b["start_date"]))
    else:
        sym, full = b["value"], sim.get("frame")
    ui.valid(f"pb_ct_{b['id']}", ["Line", "Candles"])
    mode = right.segmented_control(L("Chart", "الشارت"), ["Line", "Candles"], default="Line", key=f"pb_ct_{b['id']}",
                                   format_func=lambda k: {"Line": L("Line", "خط"), "Candles": L("Candles", "شموع")}[k]) or "Line"
    if full is None or full.empty:
        return
    full = ta.add_all(full)
    start_i = int(full.index.searchsorted(pd.Timestamp(sim["equity"].index[0])))
    view = full.iloc[max(0, start_i - 30):]
    overlays = list(dict.fromkeys(o for n in names for o in OVERLAYS.get(n, [])))
    panels = list(dict.fromkeys(p for n in names for p in PANELS.get(n, [])))[:2]
    marks = tr[tr["Symbol"] == sym].copy()
    marks["Entry"], marks["Exit"] = marks["Stock Entry"], marks["Stock Exit"]     # options: marked at the stock's price
    marks["Strategy"] = marks["Strategy"].map(strat_short)
    marks["Why"] = marks["Exit Reason"].map(lambda x: L(x, EXIT_AR.get(x, x)))
    words = None if not is_ar() else {"buy": "شراء", "sell": "بيع", "win": "صفقة رابحة", "loss": "صفقة خاسرة", "open": "صفقة مفتوحة",
                                      "BUY": "شراء", "SELL": "بيع", "at": "بسعر", "stock": "السهم"}
    fig = charts.trade_chart(view, marks, overlays, panels, mode, words=words)
    try:
        first = pd.Timestamp(sim["equity"].index[0]).strftime("%Y-%m-%d")
        fig.add_vline(x=first, line=dict(color=T.GOLD, width=1.2, dash="dot"))
        fig.add_annotation(x=first, y=1, xref="x", yref="y domain", text=L("Start", "البداية"), showarrow=False, xanchor="left",
                           yanchor="bottom", font=dict(color=T.GOLD, size=11))
    except Exception:
        pass
    ui.chart(fig, key=f"pb_px_{b['id']}")
    st.caption(L("▲ green = buy, under the bar · ▼ red = sell, above the bar. The dotted line joins each trade (green = profit, "
                 "red = loss) over the days it was held; gold = still open. Options are marked at the stock's price.",
                 "▲ الأخضر = شراء تحت الشمعة · ▼ الأحمر = بيع فوق الشمعة. الخط المنقط يربط كل صفقة (أخضر = ربح، أحمر = خسارة) "
                 "على الأيام اللي انمسكت فيها، والذهبي = صفقة مفتوحة. عقود الأوبشن معلّمة على سعر السهم."))


def orb_chart_section(sim):
    """Opening Range Breakout: one trading day at a time on 5-minute candles (the range, VWAP, entry, exit, stop and target)."""
    b, tr = sim["bot"], sim["trades"]
    ui.sec("candlestick_chart", "Trades on the 5-minute chart", "الصفقات على شارت 5 دقائق")
    days = sim.get("days5") or {}
    if not days:
        st.caption(L("No trades yet. The chart appears after the first trade.", "لا توجد صفقات بعد. الشارت يظهر بعد أول صفقة."))
        return
    keys = sorted(days, key=lambda k: (k.split("|")[1], k.split("|")[0]), reverse=True)
    t_day = pd.to_datetime(tr["Entry Date"]).dt.strftime("%Y-%m-%d")
    res = {}
    for k in keys:
        sym, day = k.split("|")
        rows = tr[(tr["Symbol"] == sym) & (t_day == day)]
        res[k] = rows
    def label(k):
        sym, day = k.split("|")
        rows = res[k]
        if rows.empty:
            return f"{day} · {sym} · " + L("no trade", "بدون صفقة")
        r = rows.iloc[0]
        side = L("long", "شراء") if r["Type"] != "Short" else L("short", "بيع مكشوف")
        state = L("open", "مفتوحة") if r["Exit Reason"] == "Open" else f'{float(r["P&L %"]):+.2f}%'
        return f"{day} · {sym} · {side} · {state}"
    left, right = st.columns([3, 1.3], vertical_alignment="bottom")
    ui.valid(f"pb_orbday_{b['id']}", keys)
    key = left.selectbox(L("Trading day", "يوم التداول"), keys, key=f"pb_orbday_{b['id']}", format_func=label)
    ui.valid(f"pb_orbct_{b['id']}", ["Candles", "Line"])
    mode = right.segmented_control(L("Chart", "الشارت"), ["Candles", "Line"], default="Candles", key=f"pb_orbct_{b['id']}",
                                   format_func=lambda k: {"Line": L("Line", "خط"), "Candles": L("Candles", "شموع")}[k]) or "Candles"
    marks = res[key].copy()
    marks["Why"] = marks["Exit Reason"].map(lambda x: L(x, EXIT_AR.get(x, x)))
    words = None if not is_ar() else {"range": "نطاق الافتتاح", "high": "قمة النطاق", "low": "قاع النطاق", "long": "شراء", "short": "بيع مكشوف",
                                      "cover": "تغطية", "sell": "بيع", "stop": "الوقف", "target": "الهدف", "at": "بسعر"}
    fig = charts.orb_chart(days[key], marks, b["strategies"][PBK.ORB]["or_minutes"], mode, words)
    ui.chart(fig, key=f"pb_orb_{b['id']}")
    st.caption(L("Blue band = the opening range, with its high and low across the day · gold = the session VWAP · "
                 "▲ buy / ▼ short at the entry, the opposite arrow at the exit · dashed red = stop, dashed green = target.",
                 "الشريط الأزرق = نطاق الافتتاح مع قمته وقاعه على طول اليوم · الذهبي = VWAP الجلسة · "
                 "▲ شراء / ▼ بيع مكشوف عند الدخول، والسهم المعاكس عند الخروج · الأحمر المتقطع = الوقف، والأخضر المتقطع = الهدف."))


def all_trades(v, file_name):
    ui.html(f'<div id="pb-all-{v["key"]}" class="pbanchor"></div>')
    ui.sec("table_rows", f"All trades · {v['scope'] or v['name']}", f"كل الصفقات · {v['scope'] or v['name']}")
    st.caption(L(f"Every trade of the {v['n_bots']} selected bots together, with a column saying which bot made it.",
                 f"كل صفقات البوتات المحددة ({v['n_bots']}) مع بعض، مع عمود يوضح أي بوت سواها.") if v["multi"] else
               L("Every trade of this bot since its start.", "كل صفقات هذا البوت من بدايته."))
    tr = v["trades"]
    if tr.empty:
        st.info(L("No trades yet. The bot trades only when a strategy gives a signal.",
                  "لا توجد صفقات بعد. البوت يتداول فقط لما تعطي استراتيجية إشارة."))
        return
    opts = v["opts"]
    shorts = bool(tr["Type"].eq("Short").any())
    cols = (["Bot"] if v["multi"] else []) + PB.TRADE_COLS + (["Type", "Contract", "Stock Entry", "Stock Exit"] if opts else
                                                                (["Type"] if shorts else []))
    show = tr[cols].sort_values("Entry Date", kind="stable").reset_index(drop=True)
    show.insert(0, "#", range(1, len(show) + 1))
    intra = show["Strategy"].eq(PBK.ORB)
    show["Strategy"] = show["Strategy"].map(strat_short)
    if intra.any():                  # 5-minute trades: the time of day, and minutes instead of days
        show["Entry Date"] = [_when(t, i) for t, i in zip(show["Entry Date"], intra)]
        show["Exit Date"] = [_when(t, i) for t, i in zip(show["Exit Date"], intra)]
        show.insert(show.columns.get_loc("Bars") + 1, "Minutes", np.where(intra, show["Bars"] * 5, np.nan))
        if intra.all():
            show = show.drop(columns="Bars")
        else:
            show["Bars"] = np.where(intra, np.nan, show["Bars"])
    else:
        show["Entry Date"] = pd.to_datetime(show["Entry Date"]).dt.date
        show["Exit Date"] = pd.to_datetime(show["Exit Date"]).dt.date
    if "Type" in show:
        show["Type"] = show["Type"].map(lambda k: L(*TYPE_ONE.get(k, (k, k))))
    show["Exit Reason"] = show["Exit Reason"].map(lambda x: L(x, EXIT_AR.get(x, x)))
    only_opt = opts and tr["Type"].isin(["Call", "Put"]).all()
    N = {"Bot": L("Bot", "البوت"), "Symbol": L("Symbol", "الرمز"), "Strategy": L("Strategy", "الاستراتيجية"),
         "Entry Date": L("Entry date", "تاريخ الدخول"), "Entry": L("Entry", "سعر الدخول"), "Exit Date": L("Exit date", "تاريخ الخروج"),
         "Exit": L("Exit / now", "سعر الخروج / الحالي"), "Shares": L("Shares", "الأسهم"), "P&L $": L("P&L $", "الربح $"),
         "P&L %": L("P&L %", "الربح %"), "Bars": L("Days", "الأيام"), "Minutes": L("Minutes", "الدقائق"),
         "Exit Reason": L("Exit reason", "سبب الخروج"),
         "Type": L("Type", "النوع"), "Contract": L("Contract", "العقد"), "Stock Entry": L("Stock at entry", "السهم عند الدخول"),
         "Stock Exit": L("Stock at exit / now", "السهم عند الخروج / الحالي")}
    if only_opt:
        N.update({"Entry": L("Premium in (est.)", "سعر العقد دخول (تقديري)"), "Exit": L("Premium out / now (est.)", "سعر العقد خروج / الحالي (تقديري)"),
                  "Shares": L("Contracts", "العقود")})
    elif opts:
        N.update({"Entry": L("Entry (share / est. premium)", "الدخول (سهم / عقد تقديري)"),
                  "Exit": L("Exit / now (share / est. premium)", "الخروج / الحالي (سهم / عقد تقديري)"),
                  "Shares": L("Shares / contracts", "أسهم / عقود")})
    show = show.rename(columns=N)
    shown = show.iloc[::-1].head(TABLE_ROWS)
    ui.table(shown, sym=N["Symbol"] if N["Symbol"] in shown else None, pills={N["P&L $"]}, signed={N["P&L %"]}, height=520,
             fmt={N["Entry"]: "{:,.2f}", N["Exit"]: "{:,.2f}", N["Shares"]: "{:,.0f}" if only_opt else "{:,.2f}", N["P&L $"]: "{:+,.2f}",
                  N["P&L %"]: "{:+.2f}%", "#": "{:,.0f}", N.get("Bars"): "{:,.0f}", N.get("Minutes"): "{:,.0f}",
                  **({N["Stock Entry"]: "{:,.2f}", N["Stock Exit"]: "{:,.2f}"} if opts else {})})
    if len(show) > TABLE_ROWS:
        st.caption(L(f"The latest {TABLE_ROWS} of {len(show)} trades. Export the CSV for the whole list.",
                     f"آخر {TABLE_ROWS} صفقة من {len(show)}. صدّر ملف CSV للقائمة كاملة."))
    st.download_button(L("Export CSV", "تصدير CSV"), show.to_csv(index=False).encode("utf-8-sig"), file_name,
                       "text/csv", icon=":material/download:", key=f"pb_csv_{v['key']}")


# =====================================================================
# one bot in detail · several bots together
# =====================================================================
def _order_txt(item):
    sym, label, kind = item
    extra = "" if kind == "Stock" else f" {kind.upper()}"
    return f"{sym} ({strat_short(label)}{extra})"


def lab_check(b):
    """The lab's view of a saved bot: (a badge when it runs on the lab's pick, a note when the pick did clearly better)."""
    names = list(b.get("strategies") or {})
    if len(names) != 1 or is_orb(b) or instrument(b) == "options" or b.get("ml"):
        return "", None
    d = lab.data()
    s, combined = names[0], is_combined(b)
    if not d or not lab.cell(s, "all20", "baseline", d):
        return "", None
    keys = ("regime", "trend_filter", "trail_pct") if combined else tuple(lab.FIELDS)
    mine = lab.variant_of({k: b.get(k) or 0 for k in keys}, d)
    view = lab.view_of(b["kind"], b.get("max_pos"))
    rec = lab.recommend(s, view, filters_only=combined, lab=d)
    if not mine or not rec:
        return "", None
    if mine == rec:
        return T.badge(L("Lab-tested settings", "إعدادات مجرّبة في المختبر"), "up", "science"), None
    a, r = lab.cell(s, view, mine, d), lab.cell(s, view, rec, d)
    if not a or not r or r[3] < a[3] + 0.10:
        return "", None
    y = d["periods"][1]
    return "", L(f"Lab check: {strat_name(s)} on {L(*lab.VIEW_LABEL[view])} with this bot's settings ({_lab_label(mine)}) scored "
                 f"Sharpe {lab.sharpe(a[3])} and {lab.pct(a[4])} a year from {y.replace('-now', '')} to now; with the lab's pick "
                 f"({_lab_label(rec)}) it scored {lab.sharpe(r[3])} and {lab.pct(r[4])} a year. Edit the bot and press \"Use the lab's "
                 "pick\" to switch (that starts a new forward test and keeps the old record).",
                 f"فحص المختبر: {strat_name(s)} على {L(*lab.VIEW_LABEL[view])} بإعدادات هالبوت ({_lab_label(mine)}) سجّل شارب "
                 f"{lab.sharpe(a[3])} و{lab.pct(a[4])} سنوياً من 2020 لين اليوم؛ وباختيار المختبر ({_lab_label(rec)}) سجّل "
                 f"{lab.sharpe(r[3])} و{lab.pct(r[4])} سنوياً. عدّل البوت واضغط \"استخدم اختيار المختبر\" عشان تبدّل "
                 "(هذا يبدأ تجربة أمامية جديدة ويحفظ السجل القديم).")


def bot_header(sim):
    b = sim["bot"]
    names = list(b["strategies"])
    ins = instrument(b)
    uni = universe_label(b, sim.get("n_symbols") if sim["ok"] else None)
    ph = "sim" if sim.get("phase") == "sim" else "live"
    badges = (T.badge(L(*PHASES[ph][1:3]) + " · " + L(*PHASES[ph][3:5]), "gold" if ph == "sim" else "up", PHASES[ph][0])
              + T.badge(uni, "gold", KIND_ICON[b["kind"]]) + T.badge(how_label(b), "vio", "smart_toy"))
    if is_orb(b):
        badges += T.badge(L("5-minute candles · long and short", "شموع 5 دقائق · شراء وبيع مكشوف"), "acc", "timer")
    else:
        ic, en, ar_ = INSTR_CHIP[ins]
        badges += T.badge(L("Buys ", "يشتري ") + L(en, ar_).lower(), "acc", ic)
    if b["kind"] != "company":
        badges += T.badge(L(f"Up to {b['max_pos']} trades at once", f"حتى {b['max_pos']} صفقات في نفس الوقت")
                          + (L(" (each: stocks, options)", " (لكل من الأسهم والأوبشن)") if ins == "both" else ""), "neu", "stacks")
    if ins != "options":
        badges += T.badge(_stock_risk(b), "neu", "shield")
        if b.get("risk_pct"):
            badges += T.badge(L("Risk ", "المخاطرة ") + iso(f"{b['risk_pct']:g}%") + L(" per trade", " لكل صفقة"), "gold", "balance")
    if b.get("regime"):
        badges += T.badge(L(*REGIME_LABEL[int(b["regime"])]), "acc", "filter_alt")
    if b.get("trend_filter"):
        badges += T.badge(L("Only stocks above their 200-day average", "فقط الأسهم فوق متوسط 200 يوم"), "acc", "trending_up")
    if b.get("ml"):
        mdl = MLB.load(b["ml"]) or {}
        kp = float(mdl.get("keep") or 1.0)
        if mdl.get("kind") == "market":
            badges += T.badge(L("AI market model: sells when the market looks risky", "نموذج ذكاء للسوق: يبيع لما يكون السوق خطر"),
                              "vio", "psychology")
        else:
            badges += T.badge(L("AI model", "نموذج ذكاء اصطناعي") + (L(f" · takes the best {kp * 100:.0f}% of signals",
                                                                    f" · ياخذ أفضل {kp * 100:.0f}% من الإشارات") if kp < 1 else
                                                                  L(" · picks the best signals first", " · يختار أفضل الإشارات أول")),
                          "vio", "psychology")
    if ins != "stock":
        badges += T.badge(_options_txt(b["options"]), "neu", "receipt_long")
        badges += T.badge(L("Option prices estimated (Black-Scholes)", "أسعار الأوبشن تقديرية (بلاك-شولز)"), "gold", "info")
    badges += (T.badge(L("Start ", "البداية ") + iso(since_of(sim) if sim["ok"] or sim.get("phase") == "live" else b["start_date"]), "neu", "event")
               + T.badge(L("Capital ", "رأس المال ") + iso(T.money(b["capital"])), "neu", "account_balance_wallet"))
    if ins != "options":
        badges += T.badge(L("Fee ", "العمولة ") + iso(f"{b['fee']:g}%") + L(" / side", " لكل جهة"), "neu", "receipt")
    try:
        lab_badge, lab_note = lab_check(b)
    except Exception:                                   # the lab is a hint: never let it break the bot's page
        lab_badge, lab_note = "", None
    badges += lab_badge
    logo = data.logos([b["value"]]).get(b["value"]) if b["kind"] == "company" else None
    ui.html(f'<div class="card pbid">{head_html(b, logo)}<div class="bdgs">{badges}</div></div>')
    if lab_note:
        st.info(lab_note, icon=":material/science:")
    if b.get("ml"):
        ai_today(sim)
    with st.expander(L("How this bot trades", "طريقة تداول البوت"), icon=":material/tune:"):
        if is_combined(b):
            ui.html("".join(rules_html(n, p) for n, p in b["strategies"].items()))
            c = b.get("combine") or {}
            if c.get("mode") == "combo":
                st.caption(L(f"Agreement: a buy signal counts only when at least {c['min']} of the {len(names)} strategies gave a buy signal "
                             f"within the last {c.get('window', 5)} sessions; the trade follows the plan of the strategy whose signal it is.",
                             f"اتفاق: إشارة الشراء تنحسب فقط إذا أعطت {c['min']} على الأقل من الـ {len(names)} إشارة شراء خلال آخر "
                             f"{c.get('window', 5)} جلسات، والصفقة تمشي على خطة الاستراتيجية صاحبة الإشارة."))
            elif len(names) > 1:
                st.caption(L("Any of these strategies can open a trade; each trade follows the plan of the strategy that opened it "
                             "(its stop, target and time stop).",
                             "أي استراتيجية منها تقدر تفتح صفقة، وكل صفقة تمشي على خطة الاستراتيجية اللي فتحتها (وقفها وهدفها ووقفها الزمني)."))
            st.caption(R_CAPTION())
            return
        rows = "".join(f'<div style="margin:4px 0">{T.badge(strat_name(n), "vio", "smart_toy")} '
                       f'<span class="muted">{T.esc(_params_txt(n, p))}</span></div>' for n, p in b["strategies"].items())
        ui.html(rows or "—")
        if combo_rule(b):
            st.caption(combo_caption(b["combine"]["min"], len(names)))
        elif len(names) > 1:
            st.caption(L("Any of these strategies can open a trade. A trade closes on the exit signal of the strategy that opened it, "
                         "or by the stop loss, take profit or trailing stop.",
                         "أي استراتيجية منها تقدر تفتح صفقة، والصفقة تتقفل بإشارة الخروج من نفس الاستراتيجية اللي فتحتها، "
                         "أو بوقف الخسارة أو جني الأرباح أو الوقف المتحرك."))
        if ins == "both":
            st.caption(both_caption())
        if ins != "stock":
            st.caption(options_caption())


def next_orders(sim):
    if not (sim["next_buys"] or sim["next_sells"]):
        return
    if sim.get("intraday"):
        st.warning(L("Breakout on the latest 5-minute candle: ", "اختراق على آخر شمعة 5 دقائق: ") + ", ".join(_order_txt(x) for x in sim["next_buys"])
                   + L(". It is filled at the next candle's open.", ". يتنفذ عند افتتاح الشمعة التالية."), icon=":material/bolt:")
        return
    last = pd.Timestamp(sim["last_date"])
    parts = []
    if sim["next_buys"]:
        parts.append(L("buy ", "شراء ") + ", ".join(_order_txt(x) for x in sim["next_buys"]))
    if sim["next_sells"]:
        parts.append(L("sell ", "بيع ") + ", ".join(_order_txt(x) for x in sim["next_sells"]))
    note = L(" The latest candle is still moving, so these signals are confirmed at today's close.",
             " الشمعة الأخيرة لسا تتحرك، فالإشارات تتأكد عند إغلاق اليوم.") if _session_live() and last.date() == PB.today_ny() else ""
    day = iso(f"{last:%Y-%m-%d}")
    st.warning(L(f"Orders for the next open (signals of {day}): ", f"أوامر الافتتاح القادم (إشارات {day}): ")
               + " · ".join(parts) + "." + note, icon=":material/bolt:")


# =====================================================================
# the forward test's saved record
# =====================================================================
def _qty(e):
    q = float(e.get("q") or 0)
    if e.get("k") in ("Call", "Put"):
        return L(f"{int(q)} contracts", f"{int(q)} عقد")
    return f"{q:,.2f}"


def record_rows(rec):
    """Every saved fill and order of a forward-test record, newest first: [(session, event, symbol, type, strategy, price,
    quantity, note, engine)]."""
    rows = []
    for e in rec.get("ev") or []:
        k = str(e.get("k") or "Stock")
        typ = L(*TYPE_ONE.get(k, (k, k)))
        if e.get("a") == "T":                                  # a 5-minute trade: opened and closed the same day
            et, xt = str(e.get("et", ""))[11:16], str(e.get("xt", ""))[11:16]
            rows.append((e["d"], 1, L(f"Trade {et} → {xt}", f"صفقة {et} ← {xt}"), e["s"], typ, strat_short(PBK.ORB),
                         f'{_fp(e["p"])} → {_fp(e["xp"])}', _qty(e), L(e.get("r", ""), EXIT_AR.get(e.get("r", ""), e.get("r", ""))),
                         e.get("v", "")))
        elif e.get("a") == "B":
            if k in ("Call", "Put"):
                note = str(e.get("c") or "")
            else:
                note = " · ".join(x for x in (f'SL {_fp(e["st"])}' if e.get("st") else "",
                                                f'TP {_fp(e["tg"])}' if e.get("tg") is not None else "") if x)
            rows.append((e["d"], 0, L("Bought at the open", "شراء عند الافتتاح"), e["s"], typ, strat_short(e.get("l", "")),
                         _fp(e["p"]), _qty(e), note, e.get("v", "")))
        else:
            r = str(e.get("r") or "")
            rows.append((e["d"], 1, L("Sold", "بيع"), e["s"], typ, strat_short(e.get("l", "")), _fp(e["p"]), "",
                         L(r, EXIT_AR.get(r, r)), e.get("v", "")))
    for e in rec.get("sig") or []:
        k = str(e.get("k") or "Stock")
        buy = e.get("a") == "B"
        r = str(e.get("r") or "")
        rows.append((e["d"], 2, L("Buy order for the next open", "أمر شراء للافتتاح القادم") if buy else
                     L("Sell order for the next open", "أمر بيع للافتتاح القادم"), e["s"], L(*TYPE_ONE.get(k, (k, k))),
                     strat_short(e.get("l", "")), "", "", "" if buy or r in ("", "Signal") else L(r, EXIT_AR.get(r, r)), e.get("v", "")))
    rows.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [(d, *rest) for d, _, *rest in rows]


def record_panel(sim):
    """What the forward test saved: every fill and every order with the engine version that decided it, when each batch of
    sessions was saved, the settings the record belongs to, and the earlier forward tests of the bot."""
    b = sim["bot"]
    rec = b.get("fwd") or {}
    if not rec:
        return
    n = len(rec.get("eq") or {})
    ev, sg, log = rec.get("ev") or [], rec.get("sig") or [], rec.get("log") or []
    vers = sorted({str(x.get("v")) for x in ev + sg + log if x.get("v")}, key=lambda v: [int(p) if p.isdigit() else 0 for p in v.split(".")])
    ui.sec("fact_check", "Forward-test record", "سجل التجربة الأمامية")
    chip = lambda ic, label, val: f'<span class="c">{T.icon(ic)}{T.esc(label)} <b>{T.esc(str(val))}</b></span>'
    ui.html('<div class="pbrec">' + chip("event", L("Since", "منذ"), rec.get("since", "—"))
            + chip("event_available", L("Saved through", "محفوظ لين"), rec.get("until") or "—")
            + chip("calendar_month", L("Sessions saved", "جلسات محفوظة"), n)
            + chip("receipt_long", L("Fills", "صفقات منفذة"), len(ev)) + chip("bolt", L("Orders", "أوامر"), len(sg))
            + chip("tag", L("Settings", "الإعدادات"), rec.get("hash", "—"))
            + chip("memory", L("Engine", "المحرك"), ", ".join(vers) if vers else rec.get("v", "—")) + "</div>")
    st.caption(L("A session is saved once it has closed (30 minutes after the US close), on the first page view after that. Saved "
                 "sessions keep their fills, orders and closing balance even if the engine or the price data change later; changing "
                 "how the bot trades starts a new forward test, and the old one is kept below.",
                 "الجلسة تنحفظ بعد ما تقفل (بعد إغلاق السوق الأمريكي بـ 30 دقيقة)، مع أول فتح للصفحة بعدها. الجلسات المحفوظة تبقى "
                 "صفقاتها وأوامرها ورصيد إغلاقها مثل ما هي حتى لو تغيّر المحرك أو بيانات الأسعار بعدين؛ وتغيير طريقة تداول البوت يبدأ "
                 "تجربة أمامية جديدة، والقديمة تنحفظ تحت."))
    rows = record_rows(rec)
    if rows:
        cols = [L("Session", "الجلسة"), L("Event", "الحدث"), L("Symbol", "الرمز"), L("Type", "النوع"), L("Strategy", "الاستراتيجية"),
                L("Price", "السعر"), L("Quantity", "الكمية"), L("Note", "ملاحظة"), L("Engine", "المحرك")]
        df = pd.DataFrame(rows[:1000], columns=cols)
        ui.table(df.head(TABLE_ROWS), sym=L("Symbol", "الرمز"), height=460, wrap={L("Note", "ملاحظة")},
                 fmt={L("Price", "السعر"): "{:,.2f}", L("Quantity", "الكمية"): lambda q: f"{q:,.4g}"})
    else:
        ui.html(f'<div class="pbempty">{T.icon("hourglass_empty")}'
                f'{L("Nothing traded yet in the saved sessions.", "ما فيه تداول في الجلسات المحفوظة للحين.")}</div>')
    if sim.get("mismatch"):
        st.caption(L(f'{sim["mismatch"]} saved entries no longer match the stocks in the data (a stock left the group); they are kept in '
                     "the record and skipped when showing it.",
                     f'{sim["mismatch"]} من المدخلات المحفوظة ما عادت تطابق الأسهم في البيانات (سهم طلع من المجموعة)؛ باقية في السجل '
                     "وتنتخطى وقت العرض."))
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with st.expander(L("When each batch was saved", "متى انحفظت كل دفعة"), icon=":material/schedule:"):
            if log:
                ui.html("".join(f'<div class="muted" style="font-size:.8rem;margin:3px 0">{iso(x.get("at", "")[:16].replace("T", " "))} UTC · '
                                + L(f'sessions {x.get("from")} → {x.get("to")} ({x.get("n", 1)}) · engine {x.get("v")}',
                                    f'الجلسات {x.get("from")} ← {x.get("to")} ({x.get("n", 1)}) · المحرك {x.get("v")}') + "</div>"
                                for x in reversed(log[-60:])))
            else:
                st.caption(L("Nothing saved yet.", "ما انحفظ شي للحين."))
    with c2:
        with st.expander(L("Settings of this forward test", "إعدادات هذه التجربة الأمامية"), icon=":material/tune:"):
            st.caption(L(f"Started {str(rec.get('made', ''))[:10]} with engine {rec.get('v', '')} · settings hash {rec.get('hash', '')}",
                         f"بدأت {str(rec.get('made', ''))[:10]} بالمحرك {rec.get('v', '')} · بصمة الإعدادات {rec.get('hash', '')}"))
            st.code(json.dumps(rec.get("cfg") or {}, indent=1, ensure_ascii=False), language="json")
    prev = [x for x in b.get("fwd_prev") or [] if isinstance(x, dict)]
    if prev:
        lines = []
        for x in reversed(prev):
            eq = x.get("eq") or {}
            last = eq[max(eq)][0] if eq else None
            cap = float((x.get("cfg") or {}).get("capital") or b["capital"])
            ret = f" · {(last / cap - 1) * 100:+.2f}%" if last and cap else ""
            lines.append(f'<div class="muted" style="font-size:.8rem;margin:3px 0">{iso(str(x.get("since")) + " → " + str(x.get("until")))} · '
                         + L(f"{len(eq)} sessions", f"{len(eq)} جلسة") + (f" · {iso(T.money(last))}{iso(ret)}" if last else "")
                         + f' · {L("settings", "الإعدادات")} {T.esc(str(x.get("hash", "")))}</div>')
        with st.expander(L(f"Earlier forward tests ({len(prev)})", f"تجارب أمامية سابقة ({len(prev)})"), icon=":material/inventory_2:"):
            st.caption(L("Ended when the bot's trading settings were changed.", "انتهت لما تغيّرت إعدادات تداول البوت."))
            ui.html("".join(lines))
    blob = json.dumps({"bot": b["name"], "record": rec, "earlier": prev}, ensure_ascii=False, default=str, indent=1)
    st.download_button(L("Download the record (JSON)", "تحميل السجل (JSON)"), blob.encode("utf-8"), f"paper_bot_{b['id']}_record.json",
                       "application/json", icon=":material/download:", key=f"pb_rec_{b['id']}")


def section(name, key):
    """Every part of the details sits in its own block, so the space between parts is always the same."""
    return st.container(key=f"pbsec_{name}_{key}")


def details(sim, in_tab=False):
    """in_tab: one of several selected bots; the combined dashboard above them already covers the dashboard."""
    b = sim["bot"]
    key = str(b["id"])
    with section("head", key):
        ui.safe(_details_head, sim)
    if not sim["ok"] or sim["waiting"]:
        if sim["ok"] and sim.get("phase") == "live" and b.get("fwd_prev"):
            with section("record", key):             # a new forward test that hasn't started: the earlier ones are still here
                ui.safe(record_panel, sim)
        return
    v = single_view(sim, in_tab)
    lg = view_logos(v)
    parts = ([] if in_tab else [("dash", dashboard, (v,))]) + [
        ("open", open_panel, (v, lg)), ("recent", recent_panel, (v, lg)), ("equity", balance_chart, (v,)),
        ("price", orb_chart_section if sim.get("intraday") else price_chart_section, (sim,)), ("pnl", pnl_charts, (v,)),
        ("months", month_grid, (v,)),
        ("all", all_trades, (v, f"paper_bot_{b['id']}{'_sim' if sim.get('phase') == 'sim' else ''}.csv"))]
    if sim.get("phase") != "sim":
        parts.append(("record", record_panel, (sim,)))
    for name, fn, args in parts:
        with section(name, key):
            ui.safe(fn, *args)


def _details_head(sim):
    b = sim["bot"]
    bot_header(sim)
    if not sim["ok"]:
        uni = universe_label(b)
        if sim["why"] == "gone5":
            st.info(L("Yahoo keeps 5-minute prices for 60 days, and they no longer reach the days before this bot's forward test "
                      f"({fwd_since(b)}), so its historical simulation can't be shown any more. Its forward test is saved and goes on.",
                      "ياهو يحتفظ بأسعار الـ 5 دقائق لمدة 60 يوم، وما عادت توصل للأيام اللي قبل التجربة الأمامية لهذا البوت "
                      f"({fwd_since(b)})، فما عاد ينعرض له محاكاة تاريخية. تجربته الأمامية محفوظة ومستمرة."), icon=":material/history:")
            return
        if sim["why"] == "nohist":
            st.info(L(f"This bot started on the day its forward test began ({fwd_since(b)}), so it has no historical simulation. "
                      "Edit it and pick an earlier start date to add one; its forward test goes on.",
                      f"هذا البوت بدأ من يوم بداية تجربته الأمامية ({fwd_since(b)})، فما عنده محاكاة تاريخية. عدّله واختر تاريخ بداية "
                      "أقدم عشان تنضاف، وتجربته الأمامية تكمل."), icon=":material/history:")
            return
        if sim["why"] == "strategy":
            st.warning(L("This bot's strategy or group no longer exists on the site. Edit it or delete it.",
                         "استراتيجية هذا البوت أو مجموعته لم تعد موجودة في الموقع. عدّله أو احذفه."), icon=":material/error:")
        else:
            st.warning(L(f"No price data for {uni} right now. Check the symbol, or try again in a minute.",
                         f"لا توجد بيانات أسعار لـ {uni} حالياً. تأكد من الرمز، أو حاول بعد دقيقة."), icon=":material/error:")
        return
    if sim["waiting"]:
        d0 = since_of(sim)
        if sim.get("intraday"):
            st.info(L(f"The forward test starts with the US session of {d0} and trades during the session on 5-minute candles.",
                      f"التجربة الأمامية تبدأ مع جلسة {d0} الأمريكية وتتداول أثناء الجلسة على شموع 5 دقائق."),
                    icon=":material/schedule:")
            return
        st.info(L(f"The forward test starts with the US session of {d0}. After that session closes the bot checks its strategies, "
                  "and any order is filled at the next open.",
                  f"التجربة الأمامية تبدأ مع جلسة {d0} الأمريكية. بعد إغلاق الجلسة يفحص البوت الاستراتيجيات، وأي أمر يتنفذ عند الافتتاح التالي."),
                icon=":material/schedule:")
        return
    if sim.get("phase") == "sim":
        d0, d1, f0 = since_of(sim), until_of(sim), fwd_since(b)
        st.caption(L(f"Historical simulation from {d0} to {d1}: the bot's rules replayed on past prices, recalculated with the current "
                     f"engine whenever the page opens. It is not a record of real signals; the forward test (LIVE) starts {f0}.",
                     f"محاكاة تاريخية من {d0} إلى {d1}: قواعد البوت مُعاد تشغيلها على أسعار الماضي، وتنحسب من جديد بالنسخة الحالية للمحرك "
                     f"كل ما تفتح الصفحة. هي ليست سجل إشارات فعلية؛ والتجربة الأمامية (مباشر) تبدأ {f0}."))
    else:
        rec = b.get("fwd") or {}
        n = len(rec.get("eq") or {})
        saved = (L(f"{n} sessions saved, through {rec.get('until')}", f"{n} جلسة محفوظة لين {rec.get('until')}") if n else
                 L("the first session is saved once it closes", "أول جلسة تنحفظ أول ما تقفل"))
        st.caption(L(f"Forward test since {since_of(sim)}: {saved}. Saved sessions are replayed from the record and never recalculated; the "
                     "record (every fill, every order and the engine version) is at the bottom of this page.",
                     f"تجربة أمامية منذ {since_of(sim)}: {saved}. الجلسات المحفوظة تنعرض من السجل وما يُعاد حسابها؛ والسجل (كل صفقة وكل "
                     "أمر ونسخة المحرك) في آخر الصفحة."))
    if instrument(b) != "stock":
        st.caption(L(OPT_EST_EN, OPT_EST_AR))
    if sim.get("intraday"):
        first = iso(since_of(sim))
        st.caption(L(f"Yahoo keeps 5-minute prices for 60 days, so this bot shows its trades from {first} (the first 5 sessions only build the "
                     "relative volume). Every trade opens and closes on the same day.",
                     f"ياهو يحتفظ بأسعار الـ 5 دقائق لمدة 60 يوم، فهذا البوت يعرض صفقاته من {first} (أول 5 جلسات تبني الحجم النسبي فقط). "
                     "كل صفقة تنفتح وتتقفل في نفس اليوم."))
    if sim.get("phase") != "sim":
        next_orders(sim)


def portfolio(chosen, spy, sims):
    """Several selected bots: one combined dashboard, their open positions and recent trades together, the returns chart,
    one tab per bot, and every trade in one table."""
    v = combined_view(chosen)
    lg = view_logos(v) if v else {}
    if v:
        for name, fn, args in (("dash", dashboard, (v,)), ("open", open_panel, (v, lg)), ("recent", recent_panel, (v, lg))):
            with section(name, "all"):
                ui.safe(fn, *args)
    with section("cmp", "all"):
        ui.safe(compare_chart, chosen, spy)
    rank = {s["bot"]["id"]: i for i, s in enumerate(ranked(sims), 1)}
    with section("tabs", "all"):
        tabs = st.tabs([f'#{rank[s["bot"]["id"]]} {s["bot"]["name"]}' for s in chosen])
        for tab, s in zip(tabs, chosen):
            with tab:
                ui.safe(details, s, True)
    if v:
        with section("all", "all"):
            ui.safe(all_trades, v, "paper_bots_selected.csv")


# =====================================================================
# compare every strategy on one symbol (moved here from the Strategy Lab)
# =====================================================================
CMP_PERIODS = {"1y": (365, "5y", "1 year", "سنة"), "2y": (730, "5y", "2 years", "سنتين"), "5y": (1826, "10y", "5 years", "5 سنوات")}
CMP_METRICS = [("Total Return %", "العائد الكلي %"), ("CAGR %", "العائد السنوي المركب %"), ("Sharpe", "شارب"),
               ("Max Drawdown %", "أقصى تراجع %"), ("Win Rate %", "نسبة النجاح %")]


@st.cache_data(ttl=600, show_spinner=False)
def compare_all(sym, per, build=None):
    """Every daily strategy (the Strategy Lab ones and the combined ones) on one symbol over the period, each with its default
    settings, $100,000 and a 0.05% fee, through the same engine as the bots. Returns (rows, buy & hold %, first day) or None."""
    days, load, _, _ = CMP_PERIODS[per]
    df = data.history(sym, load)
    if df is None or df.empty or len(df) < 260:
        return None
    spy = data.history("SPY", load)
    first = pd.Timestamp(df.index[-1]).tz_localize(None).normalize() - pd.Timedelta(days=days)
    start = f"{first:%Y-%m-%d}"
    rows, bh = [], None
    for name in PB.ALL_STRATEGIES:
        if name == PBK.ORB:                          # 5-minute candles, 60 days: not comparable on daily prices
            continue
        bot = {"id": 0, "name": "cmp", "kind": "company", "value": sym, "symbol": sym, "strategies": {name: PB.clean_params(name, {})},
               "combine": {"mode": "any"}, "instrument": "stock", "options": None, "max_pos": 1, "capital": 100_000.0, "fee": 0.05,
               "stop_pct": 0.0, "atr_mult": 0.0, "tp_pct": 0.0, "trail_pct": 0.0, "start_date": start, "valid": True}
        r = PB.simulate(bot, {sym: df}, spy)
        if not r["ok"] or r["waiting"] or not r.get("metrics"):
            continue
        m = r["metrics"]
        bh = m["Buy & Hold %"] if bh is None else bh
        rows.append({"name": name, "book": PB.is_playbook(name), **{k: float(m[k]) for k, _ in CMP_METRICS}, "Trades": int(m["Trades"])})
    return (rows, bh, start) if rows else None


def compare_section(sims):
    """An expander at the bottom of the page: pick a symbol and a period, and every strategy is backtested on it."""
    one = [s["bot"]["value"] for s in sims if s["bot"]["kind"] == "company"]
    ss.setdefault("pb_cmp_sym", one[0] if one else "AAPL")
    ss.setdefault("pb_cmp_per", "2y")
    with st.expander(L("Compare all strategies on a symbol", "قارن كل الاستراتيجيات على سهم"), icon=":material/leaderboard:"):
        a, b_, c = st.columns([1.2, 1.8, 1.1], vertical_alignment="bottom")
        a.text_input(L("Symbol", "الرمز"), key="pb_cmp_sym")
        b_.segmented_control(L("Period", "المدة"), list(CMP_PERIODS), key="pb_cmp_per", format_func=lambda k: L(*CMP_PERIODS[k][2:4]))
        run = c.button(L("Run comparison", "شغّل المقارنة"), icon=":material/play_arrow:", key="pb_cmp_run", width="stretch")
        sym = str(ss.get("pb_cmp_sym") or "").strip().upper()
        per = ss.get("pb_cmp_per") or "2y"
        if run and sym:
            with st.spinner(L(f"Backtesting every strategy on {sym}...", f"جاري اختبار كل الاستراتيجيات على {sym}...")):
                ss["pb_cmp_res"] = (sym, per, compare_all(sym, per, PB.BUILD))
        got = ss.get("pb_cmp_res")
        if not got:
            st.caption(L("Every strategy with its default settings, $100,000 and a 0.05% fee per side, on the same engine as the bots "
                         "(signals on the close, orders at the next open). The Opening Range Breakout is left out: it needs 5-minute prices.",
                         "كل استراتيجية بإعداداتها الافتراضية، و100,000$ وعمولة 0.05% لكل جهة، على نفس محرك البوتات (الإشارة على الإغلاق "
                         "والتنفيذ عند الافتتاح التالي). اختراق نطاق الافتتاح مستبعد لأنه يحتاج أسعار 5 دقائق."))
            return
        sym_r, per_r, res = got
        if res is None:
            st.error(L(f"Not enough price data for {sym_r}. Check the symbol (for example AAPL, BTC-USD, 2222.SR).",
                       f"لا توجد بيانات كافية للرمز {sym_r}. تأكد من الرمز (مثلاً AAPL أو BTC-USD أو 2222.SR)."))
            return
        rows, bh, start = res
        col = {k: L(en, ar_) for k, (en, ar_) in zip([k for k, _ in CMP_METRICS], CMP_METRICS)}
        name_c, kind_c, tr_c = L("Strategy", "الاستراتيجية"), L("Kind", "النوع"), L("Trades", "الصفقات")
        comp = pd.DataFrame([{name_c: strat_name(r["name"]), kind_c: L("Combined", "مركّبة") if r["book"] else L("Classic", "كلاسيكية"),
                              **{col[k]: r[k] for k, _ in CMP_METRICS}, tr_c: r["Trades"]} for r in rows]).sort_values(col["Sharpe"], ascending=False)
        st.caption(L(f"{sym_r} · from {start} · buy & hold {bh:+.1f}% · sorted by Sharpe",
                     f"{sym_r} · من {start} · الشراء والاحتفاظ {bh:+.1f}% · مرتبة حسب شارب"))
        tr_col, cagr = col["Total Return %"], col["CAGR %"]
        ui.table(comp, pills={tr_col}, signed={cagr, col["Max Drawdown %"]}, height=600,
                 fmt={tr_col: "{:+.1f}%", cagr: "{:+.1f}%", col["Sharpe"]: "{:.2f}", col["Max Drawdown %"]: "{:.1f}%", col["Win Rate %"]: "{:.0f}%",
                      tr_c: "{:,.0f}"})
        ui.chart(charts.hbar(list(comp[name_c]), list(comp[tr_col]), L("Total return by strategy", "العائد الكلي حسب الاستراتيجية"),
                             max(320, 28 * len(comp) + 80)), key="pb_cmp_chart")
        st.caption(L("Past results on one symbol don't promise the same in the future; a strategy that tops one stock can trail on another.",
                     "نتائج الماضي على سهم واحد ما تضمن نفسها مستقبلاً، والاستراتيجية الأولى على سهم ممكن تتأخر على غيره."))


# =====================================================================
# test one strategy on one symbol + the parameter optimizer (moved here from the Strategy Lab)
# =====================================================================
QT_PERIODS = {"1y": (365, "2y", "1 year", "سنة"), "2y": (730, "5y", "2 years", "سنتين"), "5y": (1826, "10y", "5 years", "5 سنوات"),
              "10y": (3652, "max", "10 years", "10 سنوات")}
QT_METRICS = {"Total Return %": "العائد الكلي %", "Sharpe": "شارب", "Max Drawdown %": "أقصى تراجع %", "Win Rate %": "نسبة النجاح %",
              "CAGR %": "العائد السنوي المركب %"}
MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]


def _qt_names():
    return [n for n in PB.ALL_STRATEGIES if n != PBK.ORB]


def _param_label(name, label):
    return L(label, (PBK.PARAM_AR if PB.is_playbook(name) else engine.PARAM_AR).get(label, label))


def _qt_key(name, k):
    return f"pb_qt_p_{_slug(name)}_{k}"


def _qt_bot(sym, name, params, cfg, start):
    return {"id": 0, "name": "test", "kind": "company", "value": sym, "symbol": sym, "strategies": {name: PB.clean_params(name, params)},
            "combine": {"mode": "any"}, "instrument": "stock", "options": None, "max_pos": 1, "capital": float(cfg["capital"]),
            "fee": float(cfg["fee"]), "stop_pct": float(cfg["stop"]), "atr_mult": float(cfg["atr"]), "tp_pct": float(cfg["tp"]),
            "trail_pct": float(cfg["trail"]), "start_date": start, "valid": True, "risk_pct": float(cfg.get("riskpt") or 0.0)}


@st.cache_data(ttl=600, show_spinner=False)
def _qt_prices(sym, per):
    days, load, _, _ = QT_PERIODS[per]
    df = data.history(sym, load)
    if df is None or df.empty or len(df) < 260:
        return None
    spy = data.history("SPY", load)
    first = max(pd.Timestamp(df.index[-1]).tz_localize(None).normalize() - pd.Timedelta(days=days),
                pd.Timestamp(df.index[min(200, len(df) - 1)]).tz_localize(None).normalize())
    return df, spy, f"{first:%Y-%m-%d}"


def _qt_settings():
    """The inputs: symbol, period, strategy and its numbers, capital, fee and the exits."""
    names = _qt_names()
    for k, v in {"pb_qt_sym": "AAPL", "pb_qt_per": "2y", "pb_qt_strat": names[0], "pb_qt_cap": 100_000, "pb_qt_fee": 0.05,
                 "pb_qt_stop": 0.0, "pb_qt_atr": 0.0, "pb_qt_tp": 0.0, "pb_qt_trail": 0.0, "pb_qt_riskpt": 0.0}.items():
        ss.setdefault(k, v)
    if ss["pb_qt_strat"] not in names:
        ss["pb_qt_strat"] = names[0]
    c = st.columns([1, 1.5, 1.8, 1.1, 1.1, 0.9], vertical_alignment="bottom")
    c[0].text_input(L("Symbol", "الرمز"), key="pb_qt_sym")
    c[1].segmented_control(L("Period", "المدة"), list(QT_PERIODS), key="pb_qt_per", format_func=lambda k: L(*QT_PERIODS[k][2:4]))
    c[2].selectbox(L("Strategy", "الاستراتيجية"), names, key="pb_qt_strat", format_func=strat_name)
    c[3].number_input(L("Account ($)", "المحفظة ($)"), 100, 100_000_000, step=1000, key="pb_qt_cap")
    c[4].number_input(L("Risk per trade %", "المخاطرة لكل صفقة %"), 0.0, 10.0, step=0.25, key="pb_qt_riskpt",
                      help=L("0 = the whole account in each trade. Above 0: each trade is sized so that hitting its stop loses this % of "
                             "the account (it needs a stop).",
                             "0 = المحفظة كاملة في كل صفقة. أكثر من 0: حجم كل صفقة بحيث لو ضرب الوقف تخسر هالنسبة من المحفظة (يحتاج وقف)."))
    c[5].number_input(L("Fee % / side", "العمولة %"), 0.0, 1.0, step=0.01, key="pb_qt_fee")
    name = ss["pb_qt_strat"]
    spec = PB.spec_of(name)[1]
    book = PB.is_playbook(name)
    params = {}
    per_row = 5
    for r in range(0, len(spec), per_row):
        cols = st.columns(per_row)
        for col, (k, label, lo, hi, dflt, step) in zip(cols, spec[r:r + per_row]):
            key = _qt_key(name, k)
            if isinstance(step, float):
                ss.setdefault(key, float(dflt))
                params[k] = col.number_input(_param_label(name, label), float(lo), float(hi), step=float(step), key=key)
            else:
                ss.setdefault(key, int(dflt))
                params[k] = col.number_input(_param_label(name, label), int(lo), int(hi), step=int(step), key=key)
    off = L("0 = off", "0 = إيقاف")
    if book:
        cfg_risk = {"stop": 0.0, "atr": 0.0, "tp": 0.0}
        d = st.columns(4)
        d[0].number_input(L("Trailing stop %", "الوقف المتحرك %"), 0.0, 50.0, step=0.5, key="pb_qt_trail", help=_trail_help())
        st.caption(L("A combined strategy brings its own stop, target and time stop (its rules); only a trailing stop can be added.",
                     "الاستراتيجية المركّبة فيها وقفها وهدفها ووقفها الزمني (من شروطها)، وتقدر تضيف وقف متحرك بس."))
    else:
        d = st.columns(4)
        d[0].number_input(L("Stop loss %", "وقف الخسارة %"), 0.0, 50.0, step=0.5, key="pb_qt_stop", help=off)
        d[1].number_input(L("ATR stop ×", "وقف ATR ×"), 0.0, 10.0, step=0.5, key="pb_qt_atr", help=off)
        d[2].number_input(L("Take profit %", "جني الأرباح %"), 0.0, 500.0, step=1.0, key="pb_qt_tp", help=off)
        d[3].number_input(L("Trailing stop %", "الوقف المتحرك %"), 0.0, 50.0, step=0.5, key="pb_qt_trail", help=_trail_help())
        cfg_risk = {"stop": ss["pb_qt_stop"], "atr": ss["pb_qt_atr"], "tp": ss["pb_qt_tp"]}
    cfg = {"sym": str(ss.get("pb_qt_sym") or "").strip().upper(), "per": ss.get("pb_qt_per") or "2y", "name": name, "params": params,
           "capital": ss["pb_qt_cap"], "fee": ss["pb_qt_fee"], "trail": ss["pb_qt_trail"], "riskpt": ss.get("pb_qt_riskpt") or 0.0, **cfg_risk}
    return cfg


def _bad_periods(p):
    """Fast / (middle /) slow periods out of order."""
    return ("fast" in p and "slow" in p and p["fast"] >= p["slow"]) or ("mid" in p and not p["fast"] < p["mid"] < p["slow"])


def _qt_backtest(cfg, got):
    df, spy, start = got
    name = cfg["name"]
    p = PB.clean_params(name, cfg["params"])
    if _bad_periods(p):
        st.error(L("The fast period must be smaller than the slow period.", "الفترة السريعة لازم تكون أصغر من البطيئة."))
        return
    sim = PB.simulate(_qt_bot(cfg["sym"], name, p, cfg, start), {cfg["sym"]: df}, spy)
    if not sim["ok"] or sim["waiting"]:
        st.error(L("Not enough data for this test.", "البيانات ما تكفي لهذا الاختبار."))
        return
    m, tr = sim["metrics"], sim["trades"]
    op = tr[tr["Exit Reason"] == "Open"]
    if len(op):
        o = op.iloc[0]
        st.success(L(f"In a trade since {pd.Timestamp(o['Entry Date']):%Y-%m-%d} at ${o['Entry']:,.2f} · open P&L {o['P&L %']:+.2f}%",
                     f"في صفقة منذ {pd.Timestamp(o['Entry Date']):%Y-%m-%d} بسعر ${o['Entry']:,.2f} · الربح الحالي {o['P&L %']:+.2f}%"),
                   icon=":material/trending_up:")
    else:
        st.info(L("Not in a trade at the last close.", "ما فيه صفقة مفتوحة عند آخر إغلاق."), icon=":material/pause_circle:")
    pf = "∞" if m["Profit Factor"] == np.inf else f"{m['Profit Factor']:.2f}"
    kp = [("trending_up", L("Total return", "العائد الكلي"), f"{m['Total Return %']:+.1f}%", f"B&H {m['Buy & Hold %']:+.1f}%", T.cls(m["Total Return %"])),
          ("speed", L("CAGR", "العائد السنوي"), f"{m['CAGR %']:+.1f}%", "", T.cls(m["CAGR %"])),
          ("insights", L("Sharpe", "شارب"), f"{m['Sharpe']:.2f}", "", "pos" if m["Sharpe"] >= 1 else ("neg" if m["Sharpe"] < 0 else None)),
          ("south_east", L("Max drawdown", "أقصى تراجع"), f"{m['Max Drawdown %']:.1f}%", "", "neg" if m["Max Drawdown %"] < -0.05 else None),
          ("target", L("Win rate", "نسبة النجاح"), f"{m['Win Rate %']:.0f}%", L(f"{m['Trades']} trades", f"{m['Trades']} صفقة"),
           "pos" if m["Win Rate %"] >= 50 else "neg"),
          ("balance", L("Profit factor", "معامل الربح"), pf, "", "pos" if m["Profit Factor"] >= 1 else "neg")]
    ui.html('<div class="pbk">' + "".join(T.kpi(*k) for k in kp) + "</div>")
    if len(tr):
        size = (tr["Shares"] * tr["Entry"]).astype(float)
        rp = float(cfg.get("riskpt") or 0)
        txt = (L(f"Position sizing: {rp:g}% of the account at risk per trade · average position ${size.mean():,.0f} "
                 f"({size.mean() / float(cfg['capital']) * 100:.0f}% of the start)",
                 f"حجم الصفقات: مخاطرة {rp:g}% من المحفظة لكل صفقة · متوسط حجم الصفقة ${size.mean():,.0f} "
                 f"({size.mean() / float(cfg['capital']) * 100:.0f}% من البداية)") if rp else
               L(f"Position sizing: the whole account in each trade · average position ${size.mean():,.0f}",
                 f"حجم الصفقات: المحفظة كاملة في كل صفقة · متوسط حجم الصفقة ${size.mean():,.0f}"))
        if rp and not (cfg["stop"] or cfg["atr"] or PB.is_playbook(name)):
            txt += L(" · no stop is set, so the risk % can't be applied: add a stop loss or an ATR stop.",
                     " · ما فيه وقف، فنسبة المخاطرة ما تنطبق: أضف وقف خسارة أو وقف ATR.")
        st.caption(txt)
    d = ta.add_all(df[df.index >= df.index[0]])
    d = d[pd.DatetimeIndex(d.index).tz_localize(None) >= pd.Timestamp(start)] if getattr(d.index, "tz", None) is not None else d[d.index >= pd.Timestamp(start)]
    ui.chart(charts.price_chart(d, "Candles" if len(d) <= 800 else "Line", OVERLAYS.get(name, []), PANELS.get(name, []), False, trades=tr),
             key="pb_qt_price")
    ui.chart(charts.equity_chart(sim["equity"], sim["group"], (L("Strategy", "الاستراتيجية"), L("Buy & Hold", "شراء واحتفاظ"),
                                                              L("Drawdown %", "التراجع %"))), key="pb_qt_eq")
    ui.chart(charts.monthly_heatmap(engine.monthly_returns(sim["equity"]), L("Monthly returns", "العوائد الشهرية"),
                                    MONTHS_AR if is_ar() else None), key="pb_qt_month")
    if len(tr):
        show = tr[["Entry Date", "Entry", "Exit Date", "Exit", "Shares", "P&L $", "P&L %", "Bars", "Exit Reason"]].copy()
        show["Entry Date"] = pd.to_datetime(show["Entry Date"]).dt.date
        show["Exit Date"] = pd.to_datetime(show["Exit Date"]).dt.date
        show["Exit Reason"] = show["Exit Reason"].map(lambda x: L(x, EXIT_AR.get(x, x)))
        N = {"Entry Date": L("Entry date", "تاريخ الدخول"), "Entry": L("Entry", "سعر الدخول"), "Exit Date": L("Exit date", "تاريخ الخروج"),
             "Exit": L("Exit", "سعر الخروج"), "Shares": L("Shares", "الأسهم"), "P&L $": L("P&L $", "الربح $"), "P&L %": L("P&L %", "الربح %"),
             "Bars": L("Days", "الأيام"), "Exit Reason": L("Exit reason", "سبب الخروج")}
        show = show.rename(columns=N)
        ui.table(show.iloc[::-1].head(TABLE_ROWS), pills={N["P&L $"]}, signed={N["P&L %"]}, height=460,
                 fmt={N["Entry"]: "{:,.2f}", N["Exit"]: "{:,.2f}", N["Shares"]: "{:,.2f}", N["P&L $"]: "{:+,.2f}", N["P&L %"]: "{:+.2f}%",
                      N["Bars"]: "{:,.0f}"})
        st.download_button(L("Export CSV", "تصدير CSV"), show.to_csv(index=False).encode("utf-8-sig"), f"test_{cfg['sym']}.csv",
                           "text/csv", icon=":material/download:", key="pb_qt_csv")


def _qt_values(name, key):
    lo, hi, step = next((s_[2], s_[3], s_[5]) for s_ in PB.spec_of(name)[1] if s_[0] == key)
    vals = np.linspace(lo, hi, 6)
    out = [round(float(v), 2) if isinstance(step, float) else int(round(v)) for v in vals]
    return list(dict.fromkeys(out))


def _qt_optimizer(cfg, got):
    df, spy, start = got
    name = cfg["name"]
    spec = PB.spec_of(name)[1]
    keys = [s_[0] for s_ in spec]
    labels = {s_[0]: _param_label(name, s_[1]) for s_ in spec}
    if len(keys) < 2:
        st.caption(L("This strategy has fewer than two settings to try.", "هذه الاستراتيجية فيها أقل من إعدادين للتجربة."))
        return
    ss.setdefault("pb_qt_ox", keys[0])
    ss.setdefault("pb_qt_oy", keys[1])
    if ss["pb_qt_ox"] not in keys:
        ss["pb_qt_ox"] = keys[0]
    if ss["pb_qt_oy"] not in keys:
        ss["pb_qt_oy"] = keys[1]
    ss.setdefault("pb_qt_om", "Total Return %")
    o1, o2, o3, o4 = st.columns([1.3, 1.3, 1.3, 1], vertical_alignment="bottom")
    o1.selectbox(L("X setting", "المحور الأفقي"), keys, key="pb_qt_ox", format_func=labels.get)
    o2.selectbox(L("Y setting", "المحور الرأسي"), keys, key="pb_qt_oy", format_func=labels.get)
    o3.selectbox(L("Optimize", "المعيار"), list(QT_METRICS), key="pb_qt_om", format_func=lambda k: L(k, QT_METRICS[k]))
    run = o4.button(L("Run optimizer", "شغّل المحسّن"), icon=":material/play_arrow:", key="pb_qt_orun", width="stretch")
    px_, py_, metric = ss["pb_qt_ox"], ss["pb_qt_oy"], ss["pb_qt_om"]
    if run:
        if px_ == py_:
            st.warning(L("Pick two different settings.", "اختر إعدادين مختلفين."))
            return
        xs, ys = _qt_values(name, px_), _qt_values(name, py_)
        grid = pd.DataFrame(index=ys, columns=xs, dtype=float)
        with st.spinner(L(f"Running {len(xs) * len(ys)} backtests...", f"جاري تشغيل {len(xs) * len(ys)} اختبار...")):
            for y in ys:
                for x in xs:
                    p = PB.clean_params(name, dict(cfg["params"], **{px_: x, py_: y}))
                    if _bad_periods(p):
                        continue
                    r = PB.simulate(_qt_bot(cfg["sym"], name, p, cfg, start), {cfg["sym"]: df}, spy)
                    if r["ok"] and not r["waiting"] and r.get("metrics"):
                        grid.loc[y, x] = float(r["metrics"][metric])
        ss["pb_qt_grid"] = (cfg["sym"], cfg["per"], name, px_, py_, metric, grid)
    g = ss.get("pb_qt_grid")
    if g and g[:6] == (cfg["sym"], cfg["per"], name, px_, py_, metric):
        ui.chart(charts.optimizer_heatmap(g[6], labels[px_], labels[py_], L(metric, QT_METRICS[metric])), key="pb_qt_opt")
        st.caption(L("The best cell in the past is often overfit. Prefer stable regions.",
                     "أفضل خانة في الماضي غالباً تكون مبالغة؛ فضّل المناطق المستقرة."))


def test_section():
    """One strategy on one symbol, with your numbers: its results, charts and trades, and the parameter optimizer."""
    with st.expander(L("Test a strategy on a symbol", "اختبر استراتيجية على سهم"), icon=":material/science:"):
        cfg = _qt_settings()
        if st.button(L("Run the test", "شغّل الاختبار"), type="primary", icon=":material/play_arrow:", key="pb_qt_run"):
            ss["pb_qt_on"] = True                    # from then on the results follow the inputs
        if not cfg["sym"] or not ss.get("pb_qt_on"):
            return
        got = _qt_prices(cfg["sym"], cfg["per"])
        if got is None:
            st.error(L(f"Not enough price data for {cfg['sym']}. Check the symbol (for example AAPL, BTC-USD, 2222.SR).",
                       f"لا توجد بيانات كافية للرمز {cfg['sym']}. تأكد من الرمز (مثلاً AAPL أو BTC-USD أو 2222.SR)."))
            return
        st.caption(L(f"From {got[2]} · signals on the close, orders at the next open, stops checked during the day (the bots' engine).",
                     f"من {got[2]} · الإشارة على الإغلاق، والتنفيذ عند الافتتاح التالي، والوقف يُفحص خلال اليوم (محرك البوتات)."))
        t1, t2 = st.tabs([L("Backtest", "الاختبار"), L("Parameter optimizer", "محسّن الإعدادات")])
        with t1:
            ui.safe(_qt_backtest, cfg, got)
        with t2:
            ui.safe(_qt_optimizer, cfg, got)


# =====================================================================
# dialogs: unlock · add / edit · delete
# =====================================================================
def _unlock():
    if ss.get("pb_admin"):                 # typing Enter and pressing the button both call this
        return
    if PB.check_password(ss.get("pb_pw")):
        ss.pb_admin = True
        ss.pb_pw = ""
    else:
        ss.pb_bad_pw = True


def can_edit():
    mode = PB.admin_mode()
    if mode == "open" or (mode == "password" and ss.get("pb_admin")):
        return True
    if mode == "locked":
        st.info(L("To add, edit or delete bots, add BOTS_PASSWORD to your Streamlit Secrets (Settings → Secrets). Visitors can only watch the bots.",
                  "لإضافة البوتات أو تعديلها أو حذفها، أضف BOTS_PASSWORD في Secrets حق Streamlit (Settings ← Secrets). الزوار يقدرون يشاهدون البوتات فقط."),
                icon=":material/lock:")
        st.code('BOTS_PASSWORD = "' + L("choose-a-password", "اختر-كلمة-مرور") + '"', language="toml")
        return False
    st.caption(L("Visitors can watch the bots. Enter your password to add, edit or delete bots.",
                 "الزوار يقدرون يشاهدون البوتات. اكتب كلمة المرور لإضافة البوتات أو تعديلها أو حذفها."))
    a, b = st.columns([3, 1], vertical_alignment="bottom")
    a.text_input(L("Password", "كلمة المرور"), type="password", key="pb_pw", on_change=_unlock)
    b.button(L("Unlock", "دخول"), icon=":material/lock_open:", on_click=_unlock, width="stretch", key="pb_unlock")
    if ss.pop("pb_bad_pw", False):
        st.error(L("Wrong password.", "كلمة المرور غير صحيحة."))
    return False


FORM_KEYS = list(DEFAULTS) + ["pb_min", "pb_pbmin", "pb_start", "pb_edit_id", "pb_capital_txt", "pb_cap_bad", "pb_maxpos_keep"]
FORM_PREFIXES = ("pb_strats_", "pb_pp_", "pb_ms_")


def _reset_form():
    for k in [k for k in list(ss.keys()) if k in FORM_KEYS or str(k).startswith(FORM_PREFIXES)]:
        del ss[k]


def _init_form():
    if "pb_maxpos" not in ss and "pb_maxpos_keep" in ss:       # hidden while one company was chosen: bring the number back
        ss["pb_maxpos"] = ss["pb_maxpos_keep"]
    for k, v in DEFAULTS.items():
        if k not in ss:
            ss[k] = list(v) if isinstance(v, list) else v
    if not isinstance(ss.get("pb_capital"), int) or not 100 <= ss["pb_capital"] <= 100_000_000:
        ss["pb_capital"] = DEFAULTS["pb_capital"]
    if "pb_capital_txt" not in ss:
        ss["pb_capital_txt"] = f"{ss['pb_capital']:,}"
    if ss.get("pb_kind") not in PB.KINDS:          # clicking the selected option again clears it
        ss["pb_kind"] = DEFAULTS["pb_kind"]
    if ss.get("pb_mode") not in MODES:
        ss["pb_mode"] = DEFAULTS["pb_mode"]
    for k in ("pb_store", "pb_store_pb"):
        if not isinstance(ss.get(k), list):
            ss[k] = []
    today = PB.today_ny()
    if "pb_start" not in ss or ss["pb_start"] > today:
        ss["pb_start"] = today


_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def _capital_changed():
    """The capital box: read "1,000,000", "1000000" or Arabic digits, keep it between 100 and 100,000,000, show it with commas."""
    raw = str(ss.get("pb_capital_txt") or "").translate(_DIGITS)
    raw = "".join(ch for ch in raw if ch.isdigit() or ch == ".")
    try:
        v = int(round(float(raw)))
        ok = 100 <= v <= 100_000_000
    except ValueError:
        v, ok = 0, False
    if ok:
        ss["pb_capital"] = v
    ss["pb_cap_bad"] = not ok
    ss["pb_capital_txt"] = f"{ss.get('pb_capital', DEFAULTS['pb_capital']):,}" if ok else ss.get("pb_capital_txt", "")


def _keep_maxpos():
    ss["pb_maxpos_keep"] = ss.get("pb_maxpos")


def _clip(v, lo, hi, cast=float):
    return cast(min(max(cast(v), lo), hi))


def _load_form(bot):
    """Fill the form with a bot's settings (pencil on its card)."""
    _reset_form()
    k, v = bot["kind"], bot["value"]
    books = [s for s in PBK.PLAYBOOKS if s in bot["strategies"]]
    cap = _clip(round(bot["capital"]), 100, 100_000_000, int)
    ss["pb_capital_txt"] = f"{cap:,}"
    ss.update({"pb_edit_id": bot["id"], "pb_name": bot["name"], "pb_capital": cap,
               "pb_kind": k, "pb_mode": "combo" if books else "single",
               # the bot's own way keeps exactly its strategies (none when they no longer exist); the other way gets its default
               "pb_store": list(DEFAULTS["pb_store"]) if books else [s for s in engine.STRATEGIES if s in bot["strategies"]],
               "pb_store_pb": books or list(DEFAULTS["pb_store_pb"]), "pb_combine": bot["combine"]["mode"],
               "pb_maxpos": _clip(bot["max_pos"] if k != "company" else DEFAULTS["pb_maxpos"], 1, PB.MAX_POS_LIMIT, int),
               "pb_instr": instrument(bot), "pb_fee": _clip(bot["fee"], 0.0, 1.0), "pb_stop": _clip(bot["stop_pct"], 0.0, 50.0),
               "pb_atr": _clip(bot["atr_mult"], 0.0, 10.0), "pb_tp": _clip(bot["tp_pct"], 0.0, 500.0),
               "pb_trail": _clip(bot["trail_pct"], 0.0, 50.0), "pb_start": pd.Timestamp(bot["start_date"]).date(),
               "pb_riskpt": _clip(bot.get("risk_pct") or 0.0, 0.0, 10.0), "pb_regime": int(bot.get("regime") or 0),
               "pb_trend": bool(bot.get("trend_filter"))})
    for s in books:
        _pp_seed(s, bot["strategies"][s])
    if books:                                     # the agreement rule of combined strategies has its own keys
        ss.update({"pb_combine": "any", "pb_pbmode": bot["combine"]["mode"]})
        if bot["combine"]["mode"] == "combo":
            ss.update({"pb_pbmin": int(bot["combine"]["min"]), "pb_pbwin": int(bot["combine"].get("window", 5))})
    elif bot["combine"]["mode"] == "combo":
        ss["pb_min"] = int(bot["combine"]["min"])
    o = bot.get("options") or PB.OPTION_DEFAULTS
    ss.update({"pb_otype": o["type"], "pb_dte": int(o["dte"]), "pb_strike": int(o["strike"]), "pb_oalloc": float(o["alloc"]),
               "pb_otp": float(o["tp"]), "pb_osl": float(o["sl"])})
    if k == "company":
        ss["pb_symbol"] = v
    elif k == "sector":
        ss["pb_sector"] = v
    elif k == "industry":
        ss["pb_industry"], ss["pb_ind_sector"] = v, PB.industry_sector(v) or "Technology"


# ---------------------------------------------------------------- form state: the two ways to pick strategies
def _set_mode(m):
    ss["pb_mode"] = m


def _ms_changed(key, store):
    """A strategies drop-down changed: remember the choice (the drop-down itself is only drawn for its own way)."""
    ss[store] = list(ss.get(key) or [])


def _set_store(store, names):
    ss[store] = list(names)


def _slug(name):
    return "".join(ch if ch.isalnum() else "_" for ch in name.lower())


def _pp_key(name, k):
    return f"pb_pp_{_slug(name)}_{k}"


def _pp_seed(name, params=None, force=False):
    """A combined strategy's numbers in the form: the saved bot's, else the defaults (kept when already there)."""
    p = {**PBK.defaults(name), **(params or {})}
    for k, _, lo, hi, dflt, step in PBK.PLAYBOOKS[name][1]:
        key = _pp_key(name, k)
        if key in ss and not force:
            continue
        v = p[k]
        ss[key] = bool(v) if k == "shorts" else (float(v) if isinstance(step, float) else int(v))


def _pp_reset(name):
    _pp_seed(name, None, force=True)


def _pp_params(name):
    d = PBK.defaults(name)
    out = {}
    for k, *_ in PBK.PLAYBOOKS[name][1]:
        v = ss.get(_pp_key(name, k), d[k])
        out[k] = int(v) if isinstance(v, bool) else v
    return out


def R_CAPTION():
    return L("R = the trade's risk: the distance from the entry to the stop. A 2R target sits twice that distance from the entry.",
             "R = مخاطرة الصفقة: المسافة من سعر الدخول إلى الوقف. هدف 2R يعني ضعف هذي المسافة من سعر الدخول.")


def _rule_txt(x):
    return T.esc(x.replace(">=", "≥").replace("<=", "≤").replace("+/-", "±").replace(" x ", " × "))


def rules_html(name, params=None):
    """A combined strategy as a card: what it trades on, its exits as chips, and its numbered rule groups."""
    p = {**PBK.defaults(name), **(params or {})}
    tf = L(*PBK.TIMEFRAME.get(name, ("Daily candles", "شموع يومية")))
    if name == PBK.ORB:
        side = L("Long and short", "شراء وبيع مكشوف") if p["shorts"] else L("Long only", "شراء فقط")
        chips = [("schedule", L(f"Range: first {int(p['or_minutes'])} min", f"النطاق: أول {int(p['or_minutes'])} دقيقة")),
                 ("flag", L(f"Target {p['target_r']:g}R", f"الهدف {p['target_r']:g}R")),
                 ("logout", L("Out by the close", "خروج قبل الإغلاق"))]
    else:
        side = L("Long only", "شراء فقط")
        tgt = (L("Target: top zone of the range", "الهدف: منطقة أعلى النطاق") if name == PBK.RANGE
               else L(f"Target {p['target_r']:g}R", f"الهدف {p['target_r']:g}R"))
        chips = [("flag", tgt), ("hourglass_top", L(f"Time stop {int(p['max_bars'])} sessions", f"وقف زمني {int(p['max_bars'])} جلسة"))]
    chip_html = "".join(f'<span class="c">{T.icon(i)}{T.esc(t)}</span>' for i, t in chips)
    groups = "".join(
        f'<div class="g"><div class="gt"><span class="k">{i}</span>{T.esc(L(ge, ga))}</div><ul>'
        + "".join(f"<li>{_rule_txt(L(en, ar_))}</li>" for en, ar_ in items) + "</ul></div>"
        for i, (ge, ga, items) in enumerate(PBK.rules(name, p), 1))
    return (f'<div class="pbrl"><div class="hd"><span class="i">{T.icon(PB_ICON.get(name, "hub"))}</span>'
            f'<div class="nm"><b>{T.esc(strat_name(name))}</b><span>{T.esc(tf)} · {T.esc(side)}</span></div>'
            f'<div class="cs">{chip_html}</div></div><div class="gr">{groups}</div></div>')


def combo_caption(need, n):
    return L(f"A strategy agrees while it is in its buy state: from its own buy signal until its own sell signal. The bot buys on the day "
             f"at least {need} of the {n} agree, and sells when fewer than {need} agree, or by the stop loss, take profit or trailing stop.",
             f"الاستراتيجية تعتبر موافقة ما دامها في وضع شراء: من إشارة الشراء حقها لين إشارة البيع حقها. البوت يشتري في اليوم اللي توافق فيه "
             f"{need} على الأقل من الـ {n}، ويبيع إذا صار الموافق أقل من {need}، أو بوقف الخسارة أو جني الأرباح أو الوقف المتحرك.")


def options_caption():
    return L("Calls are bought on buy signals and puts on sell signals; each position is closed on the opposite signal of the same rule, at "
             "the option's take profit or stop loss (checked at the close), or 5 days before expiry. " + OPT_EST_EN,
             "عقود Call تنشرى مع إشارات الشراء، وعقود Put مع إشارات البيع. كل عقد يتقفل بالإشارة المعاكسة من نفس القاعدة، أو عند هدف الربح أو "
             "وقف الخسارة للعقد (يُفحص عند الإغلاق)، أو قبل الانتهاء بـ 5 أيام. " + OPT_EST_AR)


OPT_EST_EN = ("Option prices are ESTIMATES, not real quotes: Yahoo Finance keeps no price history for option contracts, so every premium "
              "is computed with the Black-Scholes model from the stock's own 20-day volatility (+10%), a 4% rate and $0.65 per contract. "
              "Real fills (bid/ask spreads, implied volatility) would differ.")
OPT_EST_AR = ("أسعار الأوبشن تقديرية وليست أسعار حقيقية: ياهو فاينانس ما يحتفظ بتاريخ أسعار العقود، فكل سعر عقد محسوب بنموذج بلاك-شولز "
              "من تذبذب السهم نفسه لآخر 20 يوم (+10%)، وفائدة 4%، و0.65$ لكل عقد. التنفيذ الحقيقي (فرق العرض والطلب والتذبذب الضمني) يختلف.")


def _est_tip(r):
    """Hover text of an option row: the stock's move and a reminder that the premium is an estimate."""
    return T.esc(f'{L("stock", "السهم")} {_fp(r["Stock Entry"])} → {_fp(r["Stock Exit"])} · '
                 + L("estimated premium (Black-Scholes)", "سعر عقد تقديري (بلاك-شولز)"))


def both_caption():
    return L("Both: every buy signal buys the stock and, with calls on, a call on it too; a sell signal sells them (and buys a put when "
             "puts are on). Options are bought first at the open with their % of the balance, and the stock gets its slot from the rest. "
             "Stocks follow the stop loss / take profit / trailing stop, options follow the option filters.",
             "الاثنين: كل إشارة شراء يشتري فيها السهم، ومعه عقد Call إذا كانت الـ Call مفعّلة؛ وإشارة البيع تبيعهم (وتشتري Put إذا كانت الـ Put مفعّلة). "
             "العقود تنشرى أول عند الافتتاح بنسبتها من الرصيد، والسهم ياخذ مكانه من الباقي. الأسهم تمشي على وقف الخسارة وجني الأرباح والوقف المتحرك، "
             "والعقود تمشي على فلاتر الأوبشن.")


def instrument_caption(instr):
    return {"stock": L("Shares only, with the stock exits below.", "أسهم فقط، مع إعدادات خروج الأسهم تحت."),
            "options": L("Option contracts only: calls on buy signals and / or puts on sell signals, with the option filters below.",
                         "عقود أوبشن فقط: Call مع إشارات الشراء و/أو Put مع إشارات البيع، مع فلاتر الأوبشن تحت."),
            "both": both_caption()}[instr]


NAME_IDEAS = {"trend": [("Trend Rider", "راكب الاتجاه"), ("Wave Surfer", "راكب الموجة")],
              "momentum": [("Momentum Hunter", "صياد الزخم"), ("Rocket Picks", "صواريخ السوق")],
              "volatility": [("Breakout Scout", "كشّاف الاختراقات"), ("Range Breaker", "كاسر النطاق")],
              "volume": [("Volume Tracker", "متتبع السيولة"), ("Smart Money", "الأموال الذكية")],
              "reversion": [("Dip Buyer", "قنّاص النزول"), ("Bounce Catcher", "صياد الارتداد")],
              "stat": [("Stat Arb Desk", "مكتب المراجحة"), ("Market Neutral", "محايد السوق")],
              "multi": [("Smart Blend", "المزيج الذكي"), ("Signal Council", "مجلس الإشارات")]}


def _set_name(txt):
    ss["pb_name"] = txt


def name_ideas(way):
    """A few names that fit what the form says the bot does (they update as the choices change)."""
    store = "pb_store_pb" if way == "combo" else "pb_store"
    strats = [x for x in (ss.get(store) or []) if x in PB.ALL_STRATEGIES]
    kind = ss.get("pb_kind") if ss.get("pb_kind") in PB.KINDS else DEFAULTS["pb_kind"]
    value = {"company": str(ss.get("pb_symbol") or "").strip().upper() or "AAPL", "sector": ss.get("pb_sector") or "",
             "industry": ss.get("pb_industry") or "", "all": "all"}[kind]
    where = {"company": value, "sector": sector_name(value) if value else "", "industry": gics_name(value) if value else "",
             "all": L("Market", "السوق")}[kind]
    kinds = [engine.KIND_OF.get(x) for x in strats if engine.KIND_OF.get(x)]
    main = max(set(kinds), key=kinds.count) if kinds else "trend"
    out = []
    for en, ar_ in NAME_IDEAS.get(main, NAME_IDEAS["trend"]):
        out.append(L(en, ar_))
    if where:
        out.append(f"{where} · {L(*NAME_IDEAS.get(main, NAME_IDEAS['trend'])[0])}"[:40])
    if strats:
        try:
            out.append(_default_name(kind, value, strats, None, ss.get("pb_instr") if way != "combo" else "stock"))
        except (KeyError, IndexError):
            pass
    return list(dict.fromkeys(x for x in out if x))[:4]


def name_ideas_row(way):
    ideas = name_ideas(way)
    if not ideas:
        return
    with st.container(key="pbnames", horizontal=True):
        ui.html(f'<span class="pbni">{T.icon("lightbulb")}{L("Ideas", "أفكار")}</span>')
        for i, txt in enumerate(ideas):
            st.button(txt, key=f"pb_nm_{i}", on_click=_set_name, args=(txt,))


def _default_name(kind, value, strats, need=None, instr="stock"):
    n = len(strats)
    if n > 1 and all(PB.is_playbook(s) for s in strats):
        how = L(f"{n} combined", f"{n} مركّبة")
    else:
        how = strat_short(strats[0]) if n == 1 else (L("all strategies", "كل الاستراتيجيات") if n == len(engine.STRATEGIES)
                                                      else L(f"{n} strategies", f"{n} استراتيجيات"))
    if need:
        how = L(f"agreement {need}/{n}", f"اتفاق {need}/{n}")
    what = {"company": value, "sector": sector_name(value), "industry": gics_name(value), "all": L("All companies", "كل الشركات")}[kind]
    tail = {"stock": "", "options": " · " + L("options", "أوبشن"), "both": " · " + L("stocks+options", "أسهم+أوبشن")}[instr]
    return f"{what} · {how}{tail}"[:40]


# ---------------------------------------------------------------- the form's look: a banner, then numbered cards
STEPS = [("Basics", "الأساسيات"), ("Market", "السوق"), ("Strategies", "الاستراتيجيات"), ("Buys", "الشراء"), ("Exits", "الخروج"),
         ("Start", "البداية")]
FORM_ART = ('<svg viewBox="0 0 260 120" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            '<defs><linearGradient id="pbfl" x1="0" x2="1"><stop offset="0" stop-color="#2DB6EB" stop-opacity="0"/>'
            '<stop offset=".35" stop-color="#2DB6EB"/><stop offset=".75" stop-color="#3B8BEB"/><stop offset="1" stop-color="#A78BFA"/></linearGradient>'
            '<filter id="pbfg" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
            '<g transform="translate(150 14) scale(1.9)" opacity=".07"><path d="M17 48 L29.5 15.5 Q32 11 34.5 15.5 L47 48" fill="none" '
            'stroke="#fff" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/></g>'
            '<path d="M12 104 L58 80 L96 88 L138 58 L176 64 L236 22" fill="none" stroke="#2DB6EB" stroke-opacity=".12" stroke-width="10" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
            '<path class="ln" d="M12 104 L58 80 L96 88 L138 58 L176 64 L236 22" fill="none" stroke="url(#pbfl)" stroke-width="3" '
            'stroke-linecap="round" stroke-linejoin="round" filter="url(#pbfg)" style="stroke-dasharray:290;--len:290"/>'
            '<path d="M222 21 L237 21.6 L236.4 36" fill="none" stroke="#A78BFA" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r="5" fill="#0E0918" stroke="{c}" stroke-width="2.4"/>'
                      for x, y, c in ((58, 80, "#2DB6EB"), (96, 88, "#3B8BEB"), (138, 58, "#3B8BEB"), (176, 64, "#7B45F0")))
            + '</svg>')


def form_banner(mode, bot=None):
    if mode == "add":
        title = L("Build your <b>bot</b>", "ابنِ <b>بوتك</b>")
        sub = L("Six short steps. Everything can be changed later with the pencil on its card.",
                "ست خطوات قصيرة، وتقدر تغيّر أي شي بعدين من القلم على كرت البوت.")
    else:
        title = L("Edit ", "تعديل ") + f"<b>{T.esc(bot['name'])}</b>"
        sub = L("Saving replays the bot from its start date with the new settings.", "الحفظ يعيد حساب البوت من تاريخ بدايته بالإعدادات الجديدة.")
    steps = "".join(f'<span><i>{i}</i>{T.esc(L(en, ar_))}</span>' for i, (en, ar_) in enumerate(STEPS, 1))
    return (f'<div class="pbfb{" rtl" if is_ar() else ""}"><div class="art">{FORM_ART}</div><div class="tx">'
            f'<div class="eb">{T.icon("robot_2")}{L("Paper trading lab", "مختبر التداول الافتراضي")}</div>'
            f'<div class="t">{title}</div><div class="s">{T.esc(sub)}</div><div class="pbstp">{steps}</div></div></div>')


def form_head(n, ic, en, ar_, hint_en="", hint_ar=""):
    hint = f'<span class="h">{T.esc(L(hint_en, hint_ar))}</span>' if hint_en else ""
    ui.html(f'<div class="pbfh"><span class="n">{n}</span><span class="t">{T.icon(ic)}{T.esc(L(en, ar_))}</span>{hint}</div>')


def mode_tile(m, on):
    """One half of the full-width switch between the two ways of picking strategies."""
    ic, en, ar_, _, _ = MODES[m]
    count = len(engine.STRATEGIES) if m == "single" else len(PBK.PLAYBOOKS)
    return (f'<div class="pbmode{" on" if on else ""}"><span class="i">{T.icon(ic)}</span>'
            f'<span class="nm">{T.esc(L(en, ar_))}</span><span class="ct">{count}</span></div>')


# ---------------------------------------------------------------- the "?" next to each chosen strategy
def _classic_rules(name, p):
    """(buy rule, sell rule) of a Strategy Lab strategy in words, with its numbers: [(en, ar), (en, ar)]."""
    g = lambda k: f"{p[k]:g}"
    if name in ("SMA Crossover", "Golden Cross (50/200)"):
        return [(f"SMA {g('fast')} crosses above SMA {g('slow')}", f"{iso('SMA ' + g('fast'))} يقطع فوق {iso('SMA ' + g('slow'))}"),
                (f"SMA {g('fast')} crosses below SMA {g('slow')}", f"{iso('SMA ' + g('fast'))} يقطع تحت {iso('SMA ' + g('slow'))}")]
    if name == "EMA Crossover":
        return [(f"EMA {g('fast')} crosses above EMA {g('slow')}", f"{iso('EMA ' + g('fast'))} يقطع فوق {iso('EMA ' + g('slow'))}"),
                (f"EMA {g('fast')} crosses below EMA {g('slow')}", f"{iso('EMA ' + g('fast'))} يقطع تحت {iso('EMA ' + g('slow'))}")]
    if name == "RSI Mean Reversion":
        return [(f"RSI {g('period')} crosses back above {g('buy_below')} while the close is above SMA 200",
                 f"{iso('RSI ' + g('period'))} يرجع فوق {g('buy_below')} والإغلاق فوق {iso('SMA 200')}"),
                (f"RSI {g('period')} is above {g('sell_above')}", f"{iso('RSI ' + g('period'))} فوق {g('sell_above')}")]
    if name == "MACD Crossover":
        return [(f"MACD ({g('fast')}, {g('slow')}) crosses above its {g('signal')}-day signal line",
                 f"{iso('MACD')} ({iso(g('fast') + ', ' + g('slow'))}) يقطع فوق خط الإشارة {g('signal')}"),
                ("MACD crosses below its signal line", f"{iso('MACD')} يقطع تحت خط الإشارة")]
    if name == "Bollinger Breakout":
        return [(f"The close crosses above the upper band (Bollinger {g('period')} / {g('std')})",
                 f"الإغلاق يقطع فوق النطاق العلوي (بولنجر {iso(g('period') + ' / ' + g('std'))})"),
                ("The close crosses below the middle band", "الإغلاق يقطع تحت الخط الأوسط")]
    if name == "Donchian Breakout (Turtle)":
        return [(f"The close is above the highest high of the {g('entry')} days before", f"الإغلاق فوق أعلى قمة في الـ {g('entry')} يوم اللي قبله"),
                (f"The close is under the lowest low of the {g('exit')} days before", f"الإغلاق تحت أدنى قاع في الـ {g('exit')} يوم اللي قبله")]
    if name == "OBV Trend (Volume)":
        return [(f"OBV crosses above its {g('obv_ma')}-day average while the close is above SMA {g('trend')}",
                 f"{iso('OBV')} يقطع فوق متوسطه {g('obv_ma')} يوم والإغلاق فوق {iso('SMA ' + g('trend'))}"),
                ("OBV crosses below its average", f"{iso('OBV')} يقطع تحت متوسطه")]
    if name == "Volume Breakout":
        return [(f"The close is above the {g('lookback')}-day high with volume at least {g('vol_mult')} x its {g('lookback')}-day average",
                 f"الإغلاق فوق قمة {g('lookback')} يوم والحجم {g('vol_mult')} × متوسطه أو أكثر"),
                (f"The close is under the {g('exit')}-day low", f"الإغلاق تحت قاع {g('exit')} يوم")]
    if name == "VWMA Crossover (Volume)":
        return [(f"The close crosses above VWMA {g('period')}", f"الإغلاق يقطع فوق {iso('VWMA ' + g('period'))}"),
                (f"The close crosses below VWMA {g('period')}", f"الإغلاق يقطع تحت {iso('VWMA ' + g('period'))}")]
    if name == "MFI Money Flow (Volume)":
        return [(f"MFI {g('period')} crosses back above {g('buy_below')} while the close is above SMA 200",
                 f"{iso('MFI ' + g('period'))} يرجع فوق {g('buy_below')} والإغلاق فوق {iso('SMA 200')}"),
                (f"MFI {g('period')} is above {g('sell_above')}", f"{iso('MFI ' + g('period'))} فوق {g('sell_above')}")]
    if name == "Trend Following":
        return [(f"The trend switches on: close above SMA {g('fast')}, SMA {g('fast')} above SMA {g('slow')}, and ADX above {g('adx_min')}",
                 f"الاتجاه يبدأ: الإغلاق فوق {iso('SMA ' + g('fast'))}، و{iso('SMA ' + g('fast'))} فوق {iso('SMA ' + g('slow'))}، و{iso('ADX')} فوق {g('adx_min')}"),
                (f"The close crosses below SMA {g('fast')}", f"الإغلاق يقطع تحت {iso('SMA ' + g('fast'))}")]
    if name == "Moving Average Crossover":
        return [(f"EMA {g('fast')} crosses above EMA {g('mid')} while EMA {g('mid')} is above EMA {g('slow')}",
                 f"{iso('EMA ' + g('fast'))} يقطع فوق {iso('EMA ' + g('mid'))} و{iso('EMA ' + g('mid'))} فوق {iso('EMA ' + g('slow'))}"),
                (f"EMA {g('fast')} crosses below EMA {g('mid')}", f"{iso('EMA ' + g('fast'))} يقطع تحت {iso('EMA ' + g('mid'))}")]
    if name == "Momentum Strategy":
        return [(f"The return of the last {g('lookback')} days rises above {g('min_ret')}% and the last month is up",
                 f"عائد آخر {g('lookback')} يوم يصير فوق {g('min_ret')}% وآخر شهر طالع"),
                (f"The return of the last {g('exit_lookback')} days is negative", f"عائد آخر {g('exit_lookback')} يوم سالب")]
    if name == "Breakout Strategy":
        return [(f"The close breaks above the highest high of the {g('n')} days before, above SMA 200",
                 f"الإغلاق يخترق أعلى قمة في الـ {g('n')} يوم اللي قبله، وفوق {iso('SMA 200')}"),
                (f"The close crosses below SMA {g('exit_ma')}", f"الإغلاق يقطع تحت {iso('SMA ' + g('exit_ma'))}")]
    if name == "Volatility Breakout":
        return [(f"A day closes more than {g('k')} x ATR {g('atr')} above the day before, near its high",
                 f"يوم يقفل فوق اليوم اللي قبله بأكثر من {g('k')} × {iso('ATR ' + g('atr'))}، وقريب من قمته"),
                (f"The close crosses below EMA {g('exit_ema')}", f"الإغلاق يقطع تحت {iso('EMA ' + g('exit_ema'))}")]
    if name == "Mean Reversion":
        return [(f"The close falls more than {g('z_in')} standard deviations under its {g('period')}-day average, above SMA 200",
                 f"الإغلاق ينزل أكثر من {g('z_in')} انحراف معياري تحت متوسط {g('period')} يوم، وفوق {iso('SMA 200')}"),
                (f"It comes back to the average (z above {g('z_out')})", f"يرجع للمتوسط ({iso('z')} فوق {g('z_out')})")]
    if name == "VWAP Mean Reversion":
        return [(f"The close falls more than {g('dev')}% under the {g('period')}-day VWAP, above SMA 200",
                 f"الإغلاق ينزل أكثر من {g('dev')}% تحت {iso('VWAP')} {g('period')} يوم، وفوق {iso('SMA 200')}"),
                ("The close is back at the VWAP", f"الإغلاق يرجع لـ {iso('VWAP')}")]
    if name == "VWAP Reclaim / Pullback":
        return [(f"Above SMA {g('trend')}, the price dipped under the {g('period')}-day VWAP in the last {g('lookback')} days and closes back above it",
                 f"فوق {iso('SMA ' + g('trend'))}، السعر نزل تحت {iso('VWAP')} {g('period')} يوم خلال آخر {g('lookback')} أيام ويقفل فوقه من جديد"),
                (f"The close falls {g('exit_pct')}% under the VWAP, or crosses below SMA {g('trend')}",
                 f"الإغلاق ينزل {g('exit_pct')}% تحت {iso('VWAP')}، أو يقطع تحت {iso('SMA ' + g('trend'))}")]
    if name == "Relative Strength Strategy":
        return [(f"The stock / S&P 500 line makes a new {g('lookback')}-day high while the close is above SMA 50",
                 f"خط السهم ÷ {iso('S&P 500')} يسوي قمة جديدة لـ {g('lookback')} يوم والإغلاق فوق {iso('SMA 50')}"),
                (f"The line crosses below its {g('rs_ma')}-day average", f"الخط يقطع تحت متوسطه {g('rs_ma')} يوم")]
    if name == "Pairs Trading":
        return [(f"The stock / S&P 500 ratio falls more than {g('z_in')} standard deviations under its {g('period')}-day average "
                 "(cheap against the market); this bot buys the stock only",
                 f"نسبة السهم ÷ {iso('S&P 500')} تنزل أكثر من {g('z_in')} انحراف معياري تحت متوسط {g('period')} يوم (رخيص مقابل السوق)؛ "
                 "البوت يشتري السهم بس"),
                (f"The ratio comes back to its average (z above {g('z_out')})", f"النسبة ترجع لمتوسطها ({iso('z')} فوق {g('z_out')})")]
    if name == "Statistical Arbitrage":
        return [(f"The stock's move of the last {g('lookback')} days, after what the market explains (beta x S&P 500), is under "
                 f"-{g('z_in')} standard deviations of its last {g('window')} days, above SMA 200",
                 f"حركة السهم آخر {g('lookback')} أيام، بعد شيل اللي يفسّره السوق (بيتا × {iso('S&P 500')})، تحت -{g('z_in')} انحراف معياري "
                 f"من آخر {g('window')} يوم، وفوق {iso('SMA 200')}"),
                (f"It recovers (z above 0), or after {g('hold')} sessions", f"يتعافى ({iso('z')} فوق 0)، أو بعد {g('hold')} جلسات")]
    if name == "Multi-Factor Strategy":
        return [(f"The average of four factors (momentum, trend, low volatility, small dip), each against the stock's last "
                 f"{g('window')} days, crosses above {g('entry')}",
                 f"متوسط أربع عوامل (الزخم، الاتجاه، الهدوء، النزول البسيط)، كل واحد مقابل آخر {g('window')} يوم للسهم، يقطع فوق {g('entry')}"),
                (f"The average drops under {g('exit')}", f"المتوسط ينزل تحت {g('exit')}")]
    if name == "Regime-Based Strategy":
        return [(f"Trending (ADX above {g('adx_min')}, above SMA 200): the close crosses above EMA {g('fast')}. Ranging: RSI(2) falls under 10",
                 f"اتجاه ({iso('ADX')} فوق {g('adx_min')}، وفوق {iso('SMA 200')}): الإغلاق يقطع فوق {iso('EMA ' + g('fast'))}. "
                 f"تذبذب: {iso('RSI(2)')} ينزل تحت 10"),
                (f"The close crosses below EMA {g('slow')}, a range trade's RSI(2) is above 80, or the close is under SMA 200",
                 f"الإغلاق يقطع تحت {iso('EMA ' + g('slow'))}، أو {iso('RSI(2)')} فوق 80 لصفقة تذبذب، أو الإغلاق تحت {iso('SMA 200')}")]
    if name == "Machine Learning Signal Combination":
        return [(f"Six indicators vote up or down; each vote is weighted by how often it was right on this stock over the last "
                 f"{g('window')} days ({g('horizon')} days later). The weighted vote crosses above {g('threshold')}",
                 f"ست مؤشرات تصوّت طالع أو نازل، وكل صوت يوزن بكم مرة صدق على هالسهم خلال آخر {g('window')} يوم (بعد {g('horizon')} أيام). "
                 f"التصويت الموزون يقطع فوق {g('threshold')}"),
                ("The weighted vote turns negative", "التصويت الموزون يصير سالب")]
    if name == "Portfolio-Level Strategy":
        return [(f"On the first session of the month: the {g('lookback')}-day return is positive and the close is above SMA {g('trend')} "
                 "(the bot fills its places with the strongest first)",
                 f"أول جلسة في الشهر: عائد {g('lookback')} يوم موجب والإغلاق فوق {iso('SMA ' + g('trend'))} (البوت يعبّي أماكنه بالأقوى أول)"),
                ("At a monthly check it no longer qualifies", "في الفحص الشهري ما عاد يستوفي الشرط")]
    return [("—", "—"), ("—", "—")]


def _classic_sub(name):
    k = engine.KINDS.get(engine.KIND_OF.get(name, ""), ("", ""))
    sub = L("Daily candles", "شموع يومية") + (" · " + L(k[0], k[1]) if k[0] else "")
    if name in engine.NEEDS_MARKET:
        sub += " · " + L("compared with the S&P 500 · buys only", "مقارنة بـ S&P 500 · شراء فقط")
    return sub


def classic_rules_html(name, params=None):
    """A Strategy Lab strategy as a small card: its buy rule and its sell rule, with its numbers."""
    p = PB.clean_params(name, params or {})
    (be, ba), (se, sa) = _classic_rules(name, p)
    groups = [("Buy (on the close)", "الشراء (عند الإغلاق)", [(be + "; the order is filled at the next open", ba + "، والأمر يتنفذ عند الافتتاح التالي")]),
              ("Sell", "البيع", [(se, sa), ("Or the stop loss, take profit or trailing stop you set below",
                                            "أو وقف الخسارة أو جني الأرباح أو الوقف المتحرك اللي تحطها تحت")])]
    gh = "".join(f'<div class="g"><div class="gt"><span class="k">{i}</span>{T.esc(L(ge, ga))}</div><ul>'
                 + "".join(f"<li>{_rule_txt(L(en, ar_))}</li>" for en, ar_ in items) + "</ul></div>"
                 for i, (ge, ga, items) in enumerate(groups, 1))
    return (f'<div class="pbrl"><div class="hd"><span class="i">{T.icon("insights")}</span>'
            f'<div class="nm"><b>{T.esc(strat_name(name))}</b><span>{T.esc(_classic_sub(name))}</span></div>'
            f'</div><div class="gr">{gh}</div></div>')


def help_row(strats):
    """A '?' next to every chosen strategy: it opens that strategy's rules (and, for a combined strategy, its numbers)."""
    if not strats:
        return
    with st.container(key="pbq_row", horizontal=True):
        for s in strats:
            with st.popover(strat_short(s), icon=":material/help:"):
                if PB.is_playbook(s):
                    _pp_seed(s)
                    ui.html(rules_html(s, _pp_params(s)))
                    _pp_inputs(s)
                    st.caption(R_CAPTION())
                    if s == PBK.ORB:
                        st.caption(L("5-minute candles: Yahoo keeps them for 60 days, so this bot shows about the last 60 days (the first 5 "
                                     "sessions only build the relative volume).",
                                     "شموع 5 دقائق: ياهو يحتفظ فيها 60 يوم، فهذا البوت يعرض آخر 60 يوم تقريباً (أول 5 جلسات تبني الحجم النسبي فقط)."))
                else:
                    ui.html(classic_rules_html(s))


def _pp_inputs(name):
    """The numbers of one combined strategy, editable (they are clipped to their ranges when the bot is saved)."""
    ui.html(f'<div class="pbfs">{T.icon("tune")}{L("Adjust the numbers", "عدّل الأرقام")}</div>')
    cols = st.columns(4)
    for i, (k, lab, lo, hi, dflt, step) in enumerate(PBK.PLAYBOOKS[name][1]):
        key, label, c = _pp_key(name, k), L(lab, PBK.PARAM_AR.get(lab, lab)), cols[i % 4]
        if k == "shorts":
            c.toggle(L("Short breakdowns", "بيع مكشوف عند الكسر"), key=key)
        elif k == "or_minutes":
            ui.valid(key, [15, 30])
            c.selectbox(label, [15, 30], key=key)
        elif isinstance(step, float):
            c.number_input(label, float(lo), float(hi), step=float(step), key=key, format="%.2f")
        else:
            c.number_input(label, int(lo), int(hi), step=int(step), key=key)
    st.button(L("Back to the defaults", "رجّع الأرقام الافتراضية"), key=f"pb_ppdef_{_slug(name)}", icon=":material/restart_alt:",
              on_click=_pp_reset, args=(name,))


# ---------------------------------------------------------------- how the chosen strategies work together (last, in a pop-out)
def together_label(way, n):
    if way == "combo":
        mode_, need, win = ss.get("pb_pbmode", "any"), ss.get("pb_pbmin", n), ss.get("pb_pbwin", 5)
        if mode_ == "combo":
            return L(f"Agreement: {need} of {n} within {win} sessions", f"اتفاق: {need} من {n} خلال {win} جلسات")
    else:
        mode_, need = ss.get("pb_combine", "any"), ss.get("pb_min", n)
        if mode_ == "combo":
            return L(f"Agreement: {need} of {n} agree", f"اتفاق: تتفق {need} من {n}")
    return L("Each on its own", "كل وحدة لحالها")


def together(way, strats):
    """Each strategy on its own, or an agreement rule (n must agree). Returns (mode, need, window)."""
    n = len(strats)
    if n < 2 or (way == "combo" and PBK.ORB in strats):
        return "any", None, None
    mk, nk = ("pb_pbmode", "pb_pbmin") if way == "combo" else ("pb_combine", "pb_min")
    ui.valid(mk, ["any", "combo"])
    if not isinstance(ss.get(nk), int) or not 2 <= ss[nk] <= n:
        ss[nk] = n
    with st.container(key="pbq_together"):
        with st.popover(L("How they work together", "كيف تشتغل مع بعض") + " · " + together_label(way, n), icon=":material/join_inner:",
                        width="stretch"):
            mode_ = st.segmented_control(L("How do the strategies work together?", "كيف تشتغل الاستراتيجيات مع بعض؟"), ["any", "combo"],
                                         key=mk, format_func=lambda k: {"any": L("Each on its own", "كل وحدة لحالها"),
                                                                         "combo": L("Agreement rule (custom)", "قاعدة اتفاق (مخصصة)")}[k]) or "any"
            need = win = None
            if mode_ == "combo":
                q1, q2 = st.columns(2)
                need = q1.number_input(L(f"Buy only when at least … of {n} agree", f"يشتري فقط إذا اتفقت على الأقل … من {n}"), 2, n, step=1,
                                       key=nk)
                if way == "combo":
                    win = q2.number_input(L("…within (sessions)", "…خلال (جلسات)"), 1, 20, step=1, key="pb_pbwin")
                    st.caption(L(f"A buy signal counts only when at least {need} of the {n} strategies gave a buy signal within the last {win} "
                                 "sessions (1 = the same day). The trade follows the plan of the strategy whose signal it is: its stop, target "
                                 "and time stop.",
                                 f"إشارة الشراء تنحسب فقط إذا أعطت {need} على الأقل من الـ {n} إشارة شراء خلال آخر {win} جلسات (1 = نفس اليوم). "
                                 "والصفقة تمشي على خطة الاستراتيجية صاحبة الإشارة: وقفها وهدفها ووقفها الزمني."))
                else:
                    st.caption(combo_caption(need, n))
            else:
                st.caption(L("Any of them can open a trade; each trade closes by the rules of the strategy that opened it.",
                             "أي وحدة منها تقدر تفتح صفقة، وكل صفقة تتقفل بقواعد الاستراتيجية اللي فتحتها."))
    return mode_, need, win


def _toggle_strat(store, name):
    cur = list(ss.get(store) or [])
    ss[store] = [x for x in cur if x != name] if name in cur else cur + [name]


def kind_picker(way, names, store):
    """The kinds of strategy (trend, momentum, volatility...) as tiles; pointing at one drops down its strategies, and a
    click adds or removes one."""
    chosen = set(ss.get(store) or [])
    kinds = [k for k in engine.KINDS if any(engine.KIND_OF.get(n) == k for n in names)]
    per_row = 4
    ui.html(f'<div class="pbfs">{T.icon("category")}{L("Kind of strategy", "نوع الاستراتيجية")}</div>')
    with st.container(key=f"pbkinds_{way}"):
        for r0 in range(0, len(kinds), per_row):
            row = kinds[r0:r0 + per_row]
            cols = st.columns(per_row, gap="small")
            for i, (col, k) in enumerate(zip(cols, row)):
                en, ar_, ic = engine.KINDS[k]
                items = [n for n in names if engine.KIND_OF.get(n) == k]
                n_on = sum(n in chosen for n in items)
                end = "_R" if i >= per_row // 2 else ""
                with col:
                    with st.container(key=f"pbkind_{way}_{k}"):
                        ui.html(f'<div class="pbkd{" has" if n_on else ""}"><div class="tp"><span class="i">{T.icon(ic)}</span>'
                                f'<span class="nm">{T.esc(L(en, ar_))}</span></div>'
                                f'<span class="ct">{L(f"{n_on} of {len(items)} chosen", f"{n_on} من {len(items)} مختارة") if n_on else L(f"{len(items)} strategies", f"{len(items)} استراتيجيات")}'
                                f'{T.icon("expand_more")}</span></div>')
                        with st.container(key=f"pbkindl_{way}_{k}{end}"):
                            for n in items:
                                on = n in chosen
                                st.button(strat_name(n), key=f"pb_tg_{way}_{_slug(n)}", on_click=_toggle_strat, args=(store, n),
                                          icon=":material/check_circle:" if on else ":material/add_circle_outline:",
                                          type="primary" if on else "secondary", width="stretch")


def _picker(way, kind):
    """One way of picking strategies: its drop-down, select all / clear, a '?' next to each chosen strategy, and (last) how they
    work together. Returns (strategies, mode, need, window)."""
    classic = way == "single"
    names = list(engine.STRATEGIES) if classic else list(PBK.PLAYBOOKS)
    store, wkey = ("pb_store", "pb_ms_single") if classic else ("pb_store_pb", "pb_ms_combo")
    kind_picker(way, names, store)
    ss[wkey] = [s for s in dict.fromkeys(ss.get(store, [])) if s in names]       # in the order they were picked
    st.multiselect(L("Chosen strategies", "الاستراتيجيات المختارة") if classic else L("Chosen combined strategies", "الاستراتيجيات المركّبة المختارة"),
                   names, key=wkey, format_func=strat_name, on_change=_ms_changed, args=(wkey, store),
                   placeholder=L("Point at a kind above, or type a name", "مرّر الماوس على نوع فوق، أو اكتب اسم"))
    strats = [s for s in names if s in ss.get(store, [])]
    every = names if classic else PBK.DAILY
    s1, s2, s3 = st.columns([1.2, 1, 3], vertical_alignment="center")
    s1.button(L("Select all", "تحديد الكل"), icon=":material/done_all:", on_click=_set_store, args=(store, every),
              key="pb_allstrats" if classic else "pb_allbooks", width="stretch",
              type="primary" if set(strats) != set(every) else "secondary",
              help=None if classic else L("The four daily ones. The Opening Range Breakout runs alone.", "الأربع اليومية. اختراق نطاق الافتتاح يشتغل لحاله."))
    s2.button(L("Clear", "مسح"), icon=":material/close:", on_click=_set_store, args=(store, []), key="pb_nostrats" if classic else "pb_nobooks",
              width="stretch", disabled=not strats)
    s3.caption(L(f"{len(strats)} of {len(names)} selected", f"{len(strats)} من {len(names)} مختارة"))
    if not classic and PBK.ORB in strats and len(strats) > 1:
        st.warning(L("The Opening Range Breakout runs alone. Keep it on its own, or remove it.", "اختراق نطاق الافتتاح يشتغل لحاله. خلّه لحاله أو شيله."),
                   icon=":material/error:")
    elif not classic and PBK.ORB in strats and kind == "all":
        st.warning(L("The Opening Range Breakout can't run on all companies. Pick one company, a sector or an industry.",
                     "اختراق نطاق الافتتاح ما يشتغل على كل الشركات. اختر شركة أو قطاع أو صناعة."), icon=":material/error:")
    help_row(strats)
    mode_, need, win = together(way, strats)
    return strats, mode_, need, win


def _trail_help():
    return L("0 = off. It follows the highest price up to the day before: a day's high raises the stop from the next day, because a daily candle doesn't show whether its high or its low came first.",
             "0 = إيقاف. يتبع أعلى سعر لين اليوم اللي قبل: قمة اليوم ترفع الوقف من اليوم اللي بعده، لأن الشمعة اليومية ما توضح أيهما صار أول: القمة أو القاع.")


def _form_settings(combined):
    """The form's current exit / filter settings, in the lab's terms."""
    s = {"regime": ss.get("pb_regime") or 0, "trend_filter": bool(ss.get("pb_trend")), "trail_pct": ss.get("pb_trail") or 0}
    if not combined:
        s.update({"stop_pct": ss.get("pb_stop") or 0, "atr_mult": ss.get("pb_atr") or 0, "tp_pct": ss.get("pb_tp") or 0,
                  "risk_pct": ss.get("pb_riskpt") or 0})
    return s


def _use_lab(values):
    for k, v in values.items():
        ss[k] = v


def _lab_label(v):
    return L(*lab.LABEL.get(v, (v, v)))


def _rtl(t):
    """Arabic text inside a left-to-right table cell: keep its words and numbers in reading order."""
    return f"\u2067{t}\u2069" if is_ar() else t


def lab_panel(kind, strats, combined):
    """How the chosen strategy did in the lab on real prices, with these settings and with the lab's pick, next to simply
    holding the stocks; a button puts the lab's pick into the form."""
    d = lab.data()
    tested = [s for s in strats if lab.cell(s, "all20", "baseline", d)] if d else []
    if not tested or ss.get("pb_instr") == "options" and not combined:
        return
    view = lab.view_of(kind, ss.get("pb_maxpos", DEFAULTS["pb_maxpos"]))
    mine = lab.variant_of(_form_settings(combined), d)
    y1, y2 = d["periods"]
    c_in, c_out = L(f"Sharpe {y1}", f"شارب {y1}"), L(f"Sharpe {y2}", f"شارب {y2.replace('now', 'اليوم')}")
    c_yr, c_dd, c_bt = L("Yearly", "سنوياً"), L("Max drop", "أكبر هبوط"), L("Beat holding", "تفوّق على الاحتفاظ")
    fmt = {c_in: "{:.2f}", c_out: "{:.2f}", c_yr: lambda v: f"{v * 100:+.0f}%", c_dd: lambda v: f"{v * 100:.0f}%",
           c_bt: lambda v: f"{v * 100:.0f}%"}
    chips = ui.table_chip(L("Bot", "البوت"), f"<b>{T.esc(L(*lab.VIEW_LABEL[view]))}</b>")
    per = ui.table_chip(L("Yearly and max drop", "السنوي وأكبر هبوط"), f"<b>{T.esc(L(y2.replace('-', ' → '), 'من 2020 لين اليوم'))}</b>")
    with st.container(key="pblab"):
        if len(tested) == 1:
            s = tested[0]
            rec = lab.recommend(s, view, filters_only=combined, lab=d)
            rows = []

            def row(name, r, bh=False):
                out = {L("Settings", "الإعدادات"): _rtl(name)}
                out.update({c_in: r[0] if r else None, c_out: r[3] if r else None, c_yr: r[4] if r else None, c_dd: r[5] if r else None})
                if view == "company":
                    out[c_bt] = None if bh or not r else r[9]
                rows.append(out)
            if mine and mine != rec:
                row(L("Your settings: ", "إعداداتك: ") + _lab_label(mine), lab.cell(s, view, mine, d))
            elif not mine:
                row(L("Your settings: not tested in the lab", "إعداداتك: ما انجرّبت في المختبر"), None)
            row(("★ " + L("Lab pick (your settings): ", "اختيار المختبر (إعداداتك): ") if rec == mine else
                 "★ " + L("Lab pick: ", "اختيار المختبر: ")) + _lab_label(rec), lab.cell(s, view, rec, d))
            bh = (d.get("buy_hold") or {}).get("company" if view == "company" else "all")
            row(L("Holding the 100 stocks", "الاحتفاظ بالـ 100 سهم") if view == "company" else
                L("Holding all the stocks", "الاحتفاظ بكل الأسهم"), bh, bh=True)
            chips = ui.table_chip(L("Strategy", "الاستراتيجية"), f"<b>{T.esc(strat_name(s))}</b>") + chips + per
            ui.table(pd.DataFrame(rows), fmt=fmt, signed=(c_yr, c_dd), title=L("Tested on real prices", "مجرّب على أسعار حقيقية"),
                     icon="science", chips=chips, wrap=(L("Settings", "الإعدادات"),))
            note = lab.verdict(s, view, d)
            if view == "company":
                med = (lab.cell(s, view, rec, d) or [None] * 10)[8]
                note += " " + L(f"The rows are the 100 company bots held together; one company alone swings much more (its typical "
                                f"Sharpe {y2}: {lab.sharpe(med)}).",
                                f"الأرقام لـ 100 بوت شركة مع بعض؛ الشركة الوحدة لحالها تتذبذب أكثر بكثير (الشارب المعتاد لها "
                                f"2020-اليوم: {lab.sharpe(med)}).")
            b1, b2 = st.columns([1.25, 2], vertical_alignment="center")
            if rec != mine:
                vals = lab.form_values(rec, d)
                if combined:
                    vals = {k: v for k, v in vals.items() if k in ("pb_regime", "pb_trend")}
                b1.button(L("Use the lab's pick", "استخدم اختيار المختبر"), icon=":material/science:", key="pb_uselab",
                          on_click=_use_lab, args=(vals,), width="stretch")
            else:
                b1.markdown(T.badge(L("You're on the lab's pick", "أنت على اختيار المختبر"), "up", "verified"), unsafe_allow_html=True)
            b2.caption(note.strip())
        else:
            rows = []
            for s in tested:
                rec = lab.recommend(s, view, filters_only=combined, lab=d)
                r_m, r_r = (lab.cell(s, view, mine, d) if mine else None), lab.cell(s, view, rec, d)
                rows.append({L("Strategy", "الاستراتيجية"): _rtl(strat_name(s)), L("Your settings", "إعداداتك"): r_m[3] if r_m else None,
                             L("Lab pick", "اختيار المختبر"): _rtl(_lab_label(rec)), c_out: r_r[3] if r_r else None,
                             c_yr: r_r[4] if r_r else None, c_dd: r_r[5] if r_r else None})
            ui.table(pd.DataFrame(rows), fmt={**fmt, L("Your settings", "إعداداتك"): "{:.2f}"}, signed=(c_yr, c_dd),
                     title=L("Tested on real prices", "مجرّب على أسعار حقيقية"), icon="science", chips=chips + per,
                     wrap=(L("Lab pick", "اختيار المختبر"),))
            st.caption(L(f"Each strategy was tested on its own. \"Your settings\" = its Sharpe {y2} with the settings in this form"
                         " (— when that mix wasn't tested). Pick one strategy to get a button that applies the lab's pick.",
                         "كل استراتيجية انجرّبت لحالها. \"إعداداتك\" = الشارب 2020-اليوم بالإعدادات اللي في النموذج "
                         "(— إذا ما انجرّبت). اختر استراتيجية وحدة عشان يطلع لك زر يطبّق اختيار المختبر."))
        with st.expander(L("Which strategies held up best for this kind of bot", "أي الاستراتيجيات صمدت أكثر لهالنوع من البوتات"),
                         icon=":material/leaderboard:"):
            rank = lab.ranking(view, filters_only=combined, lab=d)
            if combined:
                rank = [x for x in rank if x[0] in PBK.PLAYBOOKS]
            else:
                rank = [x for x in rank if x[0] in engine.STRATEGIES]
            ui.table(pd.DataFrame([{L("Strategy", "الاستراتيجية"): _rtl(strat_name(s)), L("Lab pick", "اختيار المختبر"): _rtl(_lab_label(v)),
                                    c_in: r[0], c_out: r[3], c_yr: r[4], c_dd: r[5]} for s, v, r in rank]),
                     fmt=fmt, signed=(c_yr, c_dd), wrap=(L("Lab pick", "اختيار المختبر"),))
            bh = (d.get("buy_hold") or {}).get("company" if view == "company" else "all") or [None] * 6
            st.caption(L(f"Every strategy went through this site's bot engine on real daily prices: {y1} (where ideas come from) and "
                         f"{y2} (the test). Holding the stocks {y2}: Sharpe {lab.sharpe(bh[3])}, {lab.pct(bh[4])} a year, max drop "
                         f"{lab.pct(bh[5])}. The lists are today's large companies, so every number is on the high side: compare rows "
                         "with each other. Past results don't promise future ones.",
                         f"كل استراتيجية مرّت على محرّك البوتات نفسه في الموقع بأسعار يومية حقيقية: {y1} (فترة الأفكار) و"
                         f"2020-اليوم (فترة الاختبار). الاحتفاظ بالأسهم 2020-اليوم: شارب {lab.sharpe(bh[3])}، و{lab.pct(bh[4])} سنوياً، "
                         f"وأكبر هبوط {lab.pct(bh[5])}. القوائم هي الشركات الكبيرة اليوم، فكل الأرقام مرتفعة شوي: قارن الصفوف ببعض. "
                         "النتائج السابقة ما تضمن اللي جاي."))


def bot_form(mode, bot=None):
    """The add / edit form (inside a dialog): a banner, then six numbered cards with space between them."""
    _init_form()
    ui.html(form_banner(mode, bot))

    way = ss["pb_mode"] if ss.get("pb_mode") in MODES else "single"
    combined = way == "combo"
    orb = combined and PBK.ORB in (ss.get("pb_store_pb") or [])

    # 1) basics
    with st.container(key="pbf_1"):
        form_head(1, "badge", "Basics", "الأساسيات", "A name and the virtual money it starts with", "الاسم والمبلغ الوهمي اللي يبدأ فيه")
        a, c = st.columns([2, 1])
        a.text_input(L("Bot name *", "اسم البوت *"), key="pb_name", max_chars=40,
                     placeholder=L("Type a name or pick an idea below", "اكتب اسم أو اختر فكرة من تحت"))
        c.text_input(L("Virtual capital ($)", "رأس المال الوهمي ($)"), key="pb_capital_txt", on_change=_capital_changed,
                     help=L("From 100 to 100,000,000. Commas are optional.", "من 100 إلى 100,000,000، والفواصل اختيارية."))
        if ss.get("pb_cap_bad"):
            c.caption(L("Type a number from 100 to 100,000,000.", "اكتب رقم من 100 إلى 100,000,000."))
        name_ideas_row(way)

    # 2) what it buys and what it trades
    with st.container(key="pbf_2"):
        form_head(2, "shopping_bag", "What does the bot buy and trade?", "وش يشتري البوت ووش يتداول؟",
                  "What it buys, then which stocks it watches", "وش يشتري، وبعدها أي أسهم يراقب")
        ui.html(f'<div class="pbfs">{T.icon("shopping_bag")}{L("What it buys", "وش يشتري")}</div>')
        if combined:
            instr = "stock"
            chips = T.badge(L("Stocks", "أسهم"), "acc", "show_chart") + (T.badge(L("Long and short", "شراء وبيع مكشوف"), "vio", "swap_vert")
                                                                         if orb else T.badge(L("Long", "شراء"), "vio", "trending_up"))
            ui.html(f'<div>{chips}</div>')
            st.caption(L("The combined strategies trade shares (each plans its own stop and target).",
                         "الاستراتيجيات المركّبة تتداول أسهم (كل وحدة تخطط وقفها وهدفها)."))
        else:
            ui.valid("pb_instr", list(PB.INSTRUMENTS))
            instr = st.segmented_control(L("What does the bot buy?", "وش يشتري البوت؟"), list(PB.INSTRUMENTS), key="pb_instr",
                                         format_func=lambda k: L(*INSTR_LABEL[k]), label_visibility="collapsed") or "stock"
            st.caption(instrument_caption(instr))
        ui.html(f'<div class="pbfs pbfs2">{T.icon("public")}{L("What it trades", "وش يتداول")}</div>')
        ui.valid("pb_kind", PB.KINDS)
        kind = st.segmented_control(L("What does the bot trade?", "وش يتداول البوت؟"), list(PB.KINDS), key="pb_kind",
                                    format_func=lambda k: L(*KIND_LABEL[k]), label_visibility="collapsed") or DEFAULTS["pb_kind"]
        sectors = PB.sector_members()
        if kind == "company":
            st.text_input(L("Symbol", "الرمز"), key="pb_symbol", max_chars=15,
                          help=L("Any Yahoo Finance symbol: AAPL, SPY, BTC-USD, 2222.SR…", "أي رمز من ياهو فاينانس: AAPL، SPY، BTC-USD، 2222.SR…"))
            count = 1
        elif kind == "sector":
            ui.valid("pb_sector", sectors)
            sec = st.selectbox(L("Sector", "القطاع"), list(sectors), key="pb_sector",
                               format_func=lambda s: f"{sector_name(s)} · {len(sectors[s])} " + L("stocks", "سهم"))
            count = len(sectors.get(sec, []))
        elif kind == "industry":
            x, y = st.columns(2)
            ui.valid("pb_ind_sector", sectors)
            isec = x.selectbox(L("Sector", "القطاع"), list(sectors), key="pb_ind_sector", format_func=sector_name)
            inds = PB.industry_members(isec)
            ui.valid("pb_industry", inds)
            ind = y.selectbox(L("Industry", "الصناعة"), list(inds), key="pb_industry",
                              format_func=lambda i: f"{gics_name(i)} · {len(inds[i])} " + L("stocks", "سهم"))
            count = len(inds.get(ind, []))
        else:
            count = len(PB.all_members())
            st.caption(L(f"{count} US companies: the S&P 500 plus the site's largest names. The first load takes longer (up to a minute) "
                         "because the history of every stock is downloaded.",
                         f"{count} شركة أمريكية: إس آند بي 500 وأكبر الشركات في الموقع. أول تحميل ياخذ وقت أطول (لين دقيقة) "
                         "لأنه يحمّل تاريخ كل الأسهم."))

    # 3) strategies: two ways; the kinds, then their strategies
    with st.container(key="pbf_3"):
        form_head(3, "filter_alt", "Stock filter strategies", "فلتر استراتيجيات الأسهم",
                  "Point at a kind to see its strategies · ? explains each one", "مرّر الماوس على النوع عشان تشوف استراتيجياته · ? يشرح كل وحدة")
        with st.container(key="pbswitch"):
            t1, t2 = st.columns(2, gap="small")
            for col, m in ((t1, "single"), (t2, "combo")):
                with col:
                    with st.container(key=f"pbmode_{m}"):
                        ui.html(mode_tile(m, m == way))
                        st.button(L(*MODES[m][1:3]), key=f"pb_mode_{m}", on_click=_set_mode, args=(m,), width="stretch")
        strats, mode_, need, win = _picker(way, kind)
    orb = combined and PBK.ORB in strats
    if not orb:
        ui.safe(lab_panel, kind, strats, combined)

    # 4) how many trades, how much each, and the filters
    with st.container(key="pbf_4"):
        form_head(4, "tune", "Trades and filters", "الصفقات والفلاتر", "How many at once, how much in each, and when not to buy",
                  "كم صفقة مع بعض، وكم في كل وحدة، ومتى ما يشتري")
        if kind != "company":
            m1, m2 = st.columns([1, 2], vertical_alignment="bottom")
            maxpos = m1.number_input(L("Max open trades", "أقصى عدد صفقات مفتوحة"), 1, PB.MAX_POS_LIMIT, step=1, key="pb_maxpos",
                                     on_change=_keep_maxpos)
            share = {"stock": L(f"1/{maxpos} of the balance", f"1/{maxpos} من الرصيد"),
                     "options": L("a set % of the balance (below)", "نسبة ثابتة من الرصيد (تحت)"),
                     "both": L(f"1/{maxpos} of the balance (stocks) or a set % (options), and stocks and options have {maxpos} places each",
                               f"1/{maxpos} من الرصيد (الأسهم) أو نسبة ثابتة (الأوبشن)، وللأسهم {maxpos} أماكن وللأوبشن {maxpos} أماكن")}[instr]
            if orb:
                m2.caption(L(f"Each trade gets {share} at the day's open. When more stocks break out than there are free slots, the "
                             "earliest breakouts are taken first (a tie goes to the higher relative volume).",
                             f"كل صفقة تاخذ {share} عند افتتاح اليوم. وإذا اخترقت أسهم أكثر من الأماكن الفاضية، ياخذ الأبكر اختراقاً أولاً "
                             "(وعند التساوي الأعلى حجماً نسبياً)."))
            else:
                m2.caption(L(f"Each trade gets {share}. After every close the bot checks all {count} stocks; "
                             "when more stocks signal than free slots, it buys the strongest of the last 3 months first (puts: the weakest).",
                             f"كل صفقة تاخذ {share}. بعد كل إغلاق يفحص البوت كل الـ {count} سهم، "
                             "وإذا أعطت أسهم إشارات أكثر من الأماكن الفاضية، يشتري الأقوى أداءً آخر 3 أشهر أولاً (والـ Put الأضعف)."))

        if instr != "options":
            r1, r2 = st.columns([1, 2], vertical_alignment="bottom")
            r1.number_input(L("Risk per trade % (0 = off)", "المخاطرة لكل صفقة % (0 = إيقاف)"), 0.0, 10.0, step=0.25, key="pb_riskpt",
                            help=L("The account is the capital above.", "المحفظة هي رأس المال فوق."))
            r2.caption(L("With a risk %, each stock trade is sized so that hitting its stop loses that % of the balance (never more than "
                         "its slot). It needs a stop: the stop loss or ATR stop (exits below) or the combined strategy's own stop. "
                         "0 = each trade simply gets its slot.",
                         "مع نسبة مخاطرة، يتحدد حجم كل صفقة أسهم بحيث لو ضرب الوقف يخسر البوت هالنسبة من رصيده (وما يتعدى مكانها). "
                         "تحتاج وقف: وقف الخسارة أو وقف ATR (في الخروج تحت) أو وقف الاستراتيجية المركّبة. "
                         "0 = كل صفقة تاخذ مكانها بالتساوي."))
        if not orb:
            f1, f2 = st.columns([1.3, 1], vertical_alignment="bottom")
            ui.valid("pb_regime", [0, 1, 2])
            f1.selectbox(L("Market filter (S&P 500 vs its 200-day average)", "فلتر السوق (S&P 500 مقابل متوسط 200 يوم)"), [0, 1, 2],
                         key="pb_regime", format_func=lambda k: L(*REGIME_LABEL[k]))
            f2.toggle(L("Buy only stocks above their own 200-day average", "اشترِ فقط الأسهم اللي فوق متوسط 200 يوم"), key="pb_trend")
            st.caption(L("Both filters only hold back new buys (calls too); the second market option also sells the shares when the "
                         "S&P 500 closes under its 200-day average. They are checked at the close, like the signals.",
                         "الفلترين يمنعون الشراء الجديد بس (والـ Call كذلك)؛ والخيار الثاني لفلتر السوق يبيع الأسهم كمان لما يقفل "
                         "S&P 500 تحت متوسط 200 يوم. ينفحصون عند الإغلاق مثل الإشارات."))
        elif kind == "company":
            st.caption(L("One company: one trade at a time, with the whole balance.", "شركة وحدة: صفقة وحدة كل مرة بكامل الرصيد."))

    # 5) exits and costs
    with st.container(key="pbf_5"):
        form_head(5, "shield", "Exits and costs", "الخروج والتكاليف")
        if combined:
            r = st.columns(3)
            r[0].number_input(L("Fee % / side", "العمولة %"), 0.0, 1.0, step=0.01, key="pb_fee")
            if not orb:
                r[1].number_input(L("Trailing stop % (optional)", "الوقف المتحرك % (اختياري)"), 0.0, 50.0, step=0.5,
                                  help=_trail_help(), key="pb_trail")
            st.caption(L("Stop, target and time stop come from each strategy (press its ?).", "الوقف والهدف والوقف الزمني من كل استراتيجية (اضغط ? جنبها).")
                       if not orb else L("Stop and target come from the opening range (press ?).", "الوقف والهدف من نطاق الافتتاح (اضغط ?)."))
        else:
            if instr != "options":
                if instr == "both":
                    ui.html(f'<div class="pbfs">{T.icon("show_chart")}{L("Stocks", "الأسهم")}</div>')
                r = st.columns(5)
                off = L("0 = off", "0 = إيقاف")
                r[0].number_input(L("Fee % / side", "العمولة %"), 0.0, 1.0, step=0.01, key="pb_fee")
                r[1].number_input(L("Stop loss %", "وقف الخسارة %"), 0.0, 50.0, step=0.5, help=off, key="pb_stop")
                r[2].number_input(L("ATR stop ×", "وقف ATR ×"), 0.0, 10.0, step=0.5, help=off, key="pb_atr")
                r[3].number_input(L("Take profit %", "جني الأرباح %"), 0.0, 500.0, step=1.0, help=off, key="pb_tp")
                r[4].number_input(L("Trailing stop %", "الوقف المتحرك %"), 0.0, 50.0, step=0.5, help=_trail_help(), key="pb_trail")
            if instr != "stock":
                ui.html(f'<div class="pbfs">{T.icon("receipt_long")}{L("Option filters", "فلاتر الأوبشن")}</div>')
                o1, o2, o3 = st.columns(3)
                ui.valid("pb_otype", list(PB.OPTION_TYPES))
                o1.selectbox(L("Option type", "نوع العقد"), list(PB.OPTION_TYPES), key="pb_otype", format_func=lambda k: L(*OTYPE_LABEL[k]))
                o2.number_input(L("Days to expiry", "أيام حتى الانتهاء"), 7, 180, step=1, key="pb_dte")
                ui.valid("pb_strike", list(PB.STRIKES))
                o3.selectbox(L("Strike", "سعر التنفيذ"), list(PB.STRIKES), key="pb_strike", format_func=lambda k: L(*STRIKE_LABEL[k]))
                o4, o5, o6 = st.columns(3)
                o4.number_input(L("Per trade (% of balance)", "لكل صفقة (% من الرصيد)"), 0.5, 50.0, step=0.5, key="pb_oalloc")
                o5.number_input(L("Take profit on the option %", "هدف ربح العقد %"), 0.0, 2000.0, step=5.0, key="pb_otp",
                                help=L("0 = off", "0 = إيقاف"))
                o6.number_input(L("Stop loss on the option %", "وقف خسارة العقد %"), 0.0, 95.0, step=1.0, key="pb_osl",
                                help=L("0 = off", "0 = إيقاف"))
                st.caption(options_caption())

    # 6) start
    today = PB.today_ny()
    with st.container(key="pbf_6"):
        form_head(6, "event", "Start", "البداية")
        low = today - timedelta(days=59) if orb else min(today - timedelta(days=5 * 365), ss["pb_start"])
        if ss["pb_start"] < low:
            ss["pb_start"] = low
        d1, d2 = st.columns([1, 2], vertical_alignment="bottom")
        start = d1.date_input(L("Start date", "تاريخ البداية"), min_value=low, max_value=today, key="pb_start")
        d2.caption(L("5-minute prices go back 60 days, so the start can be up to 59 days ago.",
                     "أسعار الـ 5 دقائق ترجع 60 يوم بس، فالبداية تكون خلال آخر 59 يوم.") if orb else
                   L("Today = a forward test only, saved session by session from the next session. An earlier date also adds a historical "
                     "simulation from that date, shown apart (SIM).",
                     "اليوم = تجربة أمامية فقط، تنحفظ جلسة بجلسة من الجلسة القادمة. التاريخ الأقدم يضيف كمان محاكاة تاريخية من ذاك التاريخ، "
                     "تنعرض لحالها (محاكاة)."))
        if mode == "edit":
            st.caption(L("Saving a change to how the bot trades (strategies, stocks, capital, risk) starts a new forward test from the next "
                         "session, and the old record is kept. A new name or start date keeps the forward test going.",
                         "حفظ أي تغيير في طريقة تداول البوت (الاستراتيجيات، الأسهم، رأس المال، المخاطرة) يبدأ تجربة أمامية جديدة من الجلسة "
                         "القادمة، والسجل القديم ينحفظ. تغيير الاسم أو تاريخ البداية ما يوقف التجربة الأمامية."))
    # the start button sits on its own under box 6
    label = L("Start the bot", "شغّل البوت") if mode == "add" else L("Save changes", "حفظ التعديلات")
    pressed = st.button(label, type="primary", icon=":material/play_arrow:" if mode == "add" else ":material/save:", key="pb_create",
                        width="stretch")
    if not pressed:
        return
    if ss.get("pb_cap_bad"):
        st.error(L("Type a capital from 100 to 100,000,000.", "اكتب رأس مال من 100 إلى 100,000,000."))
        return
    if not strats:
        st.error(L("Pick at least one strategy.", "اختر استراتيجية وحدة على الأقل."))
        return
    if combined:
        if orb and len(strats) > 1:
            st.error(L("The Opening Range Breakout runs alone. Keep it on its own, or remove it.",
                       "اختراق نطاق الافتتاح يشتغل لحاله. خلّه لحاله أو شيله."))
            return
        if orb and kind == "all":
            st.error(L("The Opening Range Breakout can't run on all companies. Pick one company, a sector or an industry.",
                       "اختراق نطاق الافتتاح ما يشتغل على كل الشركات. اختر شركة أو قطاع أو صناعة."))
            return
        params = {s: _pp_params(s) for s in strats}
        if mode_ == "combo" and len(strats) > 1:
            if not 2 <= int(need or 0) <= len(strats):
                st.error(L("Pick how many strategies must agree.", "اختر كم استراتيجية لازم تتفق."))
                return
    else:
        keep = (bot or {}).get("strategies", {})
        params = {s: keep.get(s, {}) for s in strats}                     # an edited bot keeps its own strategy settings
        for s in strats:
            p = PB.clean_params(s, params[s])
            if _bad_periods(p):
                st.error(L(f"{strat_name(s)}: the fast period must be smaller than the slow period.",
                           f"{strat_name(s)}: الفترة السريعة لازم تكون أصغر من البطيئة."))
                return
    value = {"company": str(ss.get("pb_symbol") or "").strip().upper(), "sector": ss.get("pb_sector"),
             "industry": ss.get("pb_industry"), "all": "all"}[kind]
    if not value:
        st.error(L("Type a symbol.", "اكتب رمز السهم."))
        return
    if kind == "company":
        with st.spinner(L(f"Checking {value}...", f"جاري التحقق من {value}...")):
            df = data.history(value, "2y")
        if df.empty or len(df) < 60:
            st.error(L(f"No price data for {value}. Check the symbol (for example AAPL, BTC-USD, 2222.SR).",
                       f"لا توجد بيانات للرمز {value}. تأكد من الرمز (مثلاً AAPL أو BTC-USD أو 2222.SR)."))
            return
    combo = mode_ == "combo" and len(strats) > 1 and not orb
    name = str(ss.get("pb_name") or "").strip()
    if not name:
        st.error(L("Give the bot a name (type one, or pick an idea under the name).", "اكتب اسم للبوت (أو اختر فكرة تحت خانة الاسم)."))
        return
    options = {"type": ss["pb_otype"], "dte": ss["pb_dte"], "strike": ss["pb_strike"], "alloc": ss["pb_oalloc"], "tp": ss["pb_otp"],
               "sl": ss["pb_osl"]} if instr != "stock" else None
    if combined:
        risk = (0.0, 0.0, 0.0, 0.0 if orb else ss["pb_trail"])
    else:
        risk = (0.0, 0.0, 0.0, 0.0) if instr == "options" else (ss["pb_stop"], ss["pb_atr"], ss["pb_tp"], ss["pb_trail"])
    rec = PB.make_record(name, kind, value, params, ss.get("pb_maxpos", DEFAULTS["pb_maxpos"]), ss["pb_capital"], ss["pb_fee"], *risk,
                         pd.Timestamp(start).strftime("%Y-%m-%d"),
                         ({"mode": "combo", "min": int(need), **({"window": int(win)} if combined else {})} if combo else None),
                         instrument=instr, options=options, risk_pct=0.0 if instr == "options" else float(ss.get("pb_riskpt") or 0.0),
                         regime=0 if orb else int(ss.get("pb_regime") or 0), trend_filter=0 if orb else int(bool(ss.get("pb_trend"))),
                         ml=(bot or {}).get("ml") if mode == "edit" and set(params) == set((bot or {}).get("strategies") or {}) else None)
    try:
        if mode == "add":
            PB.create_bot(rec)
        else:
            PB.update_bot(bot["id"], rec, old=bot)
    except PB.StoreError as e:
        if e.kind == "full":
            st.error(L(f"You already have {PB.MAX_BOTS} bots.", f"عندك {PB.MAX_BOTS} بوتات بالفعل."))
        else:
            storage_notice(e)
        return
    if mode == "add":
        st.toast(L(f"Bot started: {name}", f"تم تشغيل البوت: {name}"), icon=":material/rocket_launch:")
    else:
        st.toast(L(f"Saved: {name}", f"تم الحفظ: {name}"), icon=":material/save:")
    st.rerun()


def _bot_dialog_body(mode, bot, n_bots):
    if not can_edit():
        return
    if mode == "add" and n_bots >= PB.MAX_BOTS:
        st.info(L(f"You have {PB.MAX_BOTS} bots, the maximum. Delete one to add another.",
                  f"عندك {PB.MAX_BOTS} بوتات، وهذا الحد الأعلى. احذف واحد عشان تضيف غيره."), icon=":material/block:")
        return
    bot_form(mode, bot)


def _delete_body(bot):
    if not can_edit():
        return
    st.markdown(L(f"Delete **{bot['name']}** and its whole record? This can't be undone.",
                  f"حذف **{bot['name']}** وكل سجله؟ ما تقدر ترجعه بعدين."))
    y, n = st.columns(2)
    if y.button(L("Yes, delete", "نعم، احذف"), type="primary", key=f"pb_yes_{bot['id']}", icon=":material/delete_forever:", width="stretch"):
        try:
            PB.delete_bot(bot["id"])
        except PB.StoreError as e:
            storage_notice(e)
            return
        ss["pb_selected"] = [i for i in ss.get("pb_selected", []) if i != bot["id"]]
        st.toast(L("Bot deleted.", "تم حذف البوت."), icon=":material/delete:")
        st.rerun()
    with n.container(key=f"pbred_no_{bot['id']}"):
        if st.button(L("No", "لا"), key=f"pb_no_{bot['id']}", icon=":material/close:", width="stretch"):
            st.rerun()


# =====================================================================
# AI bots: five ready bots, each with a model trained in the lab (mlbots.py, research/train_ml.py)
# =====================================================================
AI_VERDICT = {"up": (("AI helped", "الذكاء حسّن"), "up", "trending_up"), "flat": (("About the same", "تقريباً نفسه"), "neu", "drag_handle"),
              "down": (("AI did worse", "الذكاء كان أضعف"), "down", "trending_down")}


def _ai_settings(c):
    out = []
    if c.get("atr_mult"):
        out.append(L(f"ATR stop ×{c['atr_mult']:g}", f"وقف ATR ×{c['atr_mult']:g}"))
    if c.get("stop_pct"):
        out.append(L(f"Stop loss {c['stop_pct']:g}%", f"وقف خسارة {c['stop_pct']:g}%"))
    if c.get("trend_filter"):
        out.append(L("Stock above its 200-day average", "السهم فوق متوسط 200 يوم"))
    if c.get("regime") == 2:
        out.append(L("Market filter: no buys, and sell", "فلتر السوق: بدون شراء ويبيع"))
    elif c.get("regime") == 1:
        out.append(L("Market filter: no new buys", "فلتر السوق: بدون شراء جديد"))
    return out


def _ai_card(mid, r, have):
    c = r.get("bot") or {}
    v = MLB.verdict(r)
    vd = ""
    if v:
        (en, ar_), kind, ic = AI_VERDICT[v]
        vd = T.badge(L(en, ar_), kind, ic)
    strats = " + ".join(strat_name(x) for x in c.get("strategies", []))
    sub = L(f"All companies · up to {c.get('max_pos', 10)} trades", f"كل الشركات · لين {c.get('max_pos', 10)} صفقة")
    chips = "".join(f"<span>{T.esc(x)}</span>" for x in [strats] + _ai_settings(c))
    t = r.get("bot_test") or {}

    def row(name, x, cls=""):
        if not x:
            return f'<tr class="{cls}"><td>{T.esc(name)}</td><td>—</td><td>—</td><td>—</td></tr>'
        return (f'<tr class="{cls}"><td>{T.esc(name)}</td><td>{x["sharpe"]:.2f}</td>'
                f'<td class="{"up" if x["cagr"] > 0 else "dn"}">{x["cagr"] * 100:+.0f}%</td><td class="dn">{x["maxdd"] * 100:.0f}%</td></tr>')
    table = (f'<table><thead><tr><th>{L("2020 → now", "من 2020 لين اليوم")}</th>'
             f'<th>{L("Sharpe", "شارب")}</th><th>{L("Yearly", "سنوياً")}</th><th>{L("Max drop", "أكبر هبوط")}</th></tr></thead><tbody>'
             + row(L("With AI", "مع الذكاء"), t.get("ai"), "ai") + row(L("Without AI", "بدون الذكاء"), t.get("plain")) + "</tbody></table>")
    sig = (r.get("signals_test") or {})
    kp, dr = sig.get("kept") or {}, sig.get("dropped") or {}
    keep = float(r.get("keep") or 1.0)
    if r.get("kind") == "market":
        rs = ((t.get("ai") or {}).get("risky_share") or 0) * 100
        note = L(f"The AI reads the whole market every day (the S&P 500 and how many of the 500+ stocks are rising) and gives the "
                 f"chance that the next month is good for stocks. When it is low, the bot buys nothing and sells what it holds. From "
                 f"2020 to now it called {rs:.0f}% of the days risky.",
                 f"الذكاء يقرأ السوق كامل كل يوم (S&P 500 وكم سهم من الـ 500 طالع) ويعطي احتمال إن الشهر الجاي زين للأسهم. إذا كان "
                 f"منخفض، البوت ما يشتري شي ويبيع اللي عنده. من 2020 لين اليوم اعتبر {rs:.0f}% من الأيام خطرة.")
    elif keep >= 1 or not dr.get("n"):
        note = L("Takes every signal of its strategy; the AI only decides which stocks to buy first when there are more signals than "
                 "free places.",
                 "ياخذ كل إشارات استراتيجيته؛ والذكاء يقرر بس أي الأسهم يشتري أول لما تكون الإشارات أكثر من الأماكن الفاضية.")
    else:
        note = L(f"Takes only the best {keep * 100:.0f}% of its strategy's signals. From 2020 to now, {kp.get('win', 0) * 100:.0f}% of the "
                 f"signals it took were winners, against {dr.get('win', 0) * 100:.0f}% of those it skipped.",
                 f"ياخذ بس أفضل {keep * 100:.0f}% من إشارات استراتيجيته. من 2020 لين اليوم، {kp.get('win', 0) * 100:.0f}% من الإشارات اللي "
                 f"أخذها ربحت، مقابل {dr.get('win', 0) * 100:.0f}% من اللي تركها.")
    if have:
        note += " " + L("Already running.", "شغّال عندك.")
    return (f'<div class="aic {v or ""}"><div class="hd"><span class="i">{T.icon("psychology")}</span><div class="tx"><div class="nm">'
            f'{T.esc(L(*r.get("name", [mid, mid])))}</div><div class="sub">{T.esc(sub)}</div></div></div>'
            f'<div class="cs">{vd}{chips}</div>{table}<div class="nt">{T.esc(note)}</div></div>')


# ---------------------------------------------------------------- ready bots: the same five, without AI, with the lab's settings
def _ready_name(r):
    en, ar_ = (r.get("name") or ["Bot", "بوت"])[:2]
    return (en.replace("AI · ", "") + " · Lab")[:40], (ar_.replace("ذكاء · ", "") + " · مختبر")[:40]


def _is_ready_bot(b, r):
    c = r.get("plain_bot") or {}
    return (not b.get("ml") and b["kind"] == "all" and set(b.get("strategies") or {}) == set(c.get("strategies") or [])
            and int(b.get("max_pos") or 0) == int(c.get("max_pos") or 0))


def _ready_card(mid, r, have):
    c = r.get("plain_bot") or {}
    t, tr = ((r.get("bot_test") or {}).get("plain") or {}), ((r.get("bot_train") or {}).get("plain") or {})
    bh = {"sharpe": t.get("bh_sharpe"), "cagr": t.get("bh_cagr"), "maxdd": t.get("bh_maxdd")} if t.get("bh_sharpe") is not None else None
    vd = ""
    if bh and t:
        v = ("down" if t["sharpe"] <= bh["sharpe"] - 0.05 else "flat" if t["sharpe"] < bh["sharpe"] + 0.05 else
             "up" if t["cagr"] >= bh["cagr"] else "calm")
        (en, ar_), kind, ic = {"up": (("Beat holding the stocks", "تفوّق على الاحتفاظ بالأسهم"), "up", "trending_up"),
                               "calm": (("Less risk than holding, lower return", "مخاطرة أقل من الاحتفاظ وعائد أقل"), "acc", "shield"),
                               "flat": (("About as good as holding", "تقريباً مثل الاحتفاظ"), "neu", "drag_handle"),
                               "down": (("Behind holding the stocks", "أقل من الاحتفاظ بالأسهم"), "down", "trending_down")}[v]
        vd = T.badge(L(en, ar_), kind, ic)
    strats = " + ".join(strat_name(x) for x in c.get("strategies", []))
    sub = L(f"All companies · up to {c.get('max_pos', 10)} trades", f"كل الشركات · لين {c.get('max_pos', 10)} صفقة")
    chips = "".join(f"<span>{T.esc(x)}</span>" for x in [strats] + (_ai_settings(c) or [L("No filter, no stop", "بدون فلتر ولا وقف")]))

    def row(name, x, cls=""):
        if not x or x.get("sharpe") is None:
            return f'<tr class="{cls}"><td>{T.esc(name)}</td><td>—</td><td>—</td><td>—</td></tr>'
        return (f'<tr class="{cls}"><td>{T.esc(name)}</td><td>{x["sharpe"]:.2f}</td>'
                f'<td class="{"up" if x["cagr"] > 0 else "dn"}">{x["cagr"] * 100:+.0f}%</td><td class="dn">{x["maxdd"] * 100:.0f}%</td></tr>')
    table = (f'<table><thead><tr><th>{L("2020 → now", "من 2020 لين اليوم")}</th><th>{L("Sharpe", "شارب")}</th>'
             f'<th>{L("Yearly", "سنوياً")}</th><th>{L("Max drop", "أكبر هبوط")}</th></tr></thead><tbody>'
             + row(L("This bot", "هالبوت"), t, "ai") + row(L("Holding all the stocks", "الاحتفاظ بكل الأسهم"), bh) + "</tbody></table>")
    note = ""
    if t.get("win") is not None:
        note = L(f"About {t.get('trades_yr', 0):.0f} trades a year, {t['win'] * 100:.0f}% of them winners.",
                 f"حوالي {t.get('trades_yr', 0):.0f} صفقة بالسنة، {t['win'] * 100:.0f}% منها رابحة.")
    if tr.get("sharpe") is not None and tr.get("bh_sharpe") is not None:
        note += " " + L(f"2012–2019: Sharpe {tr['sharpe']:.2f} (holding: {tr['bh_sharpe']:.2f}).",
                        f"2012–2019: شارب {tr['sharpe']:.2f} (الاحتفاظ: {tr['bh_sharpe']:.2f}).")
    if have:
        note += " " + L("Already running.", "شغّال عندك.")
    return (f'<div class="aic"><div class="hd"><span class="i">{T.icon("smart_toy")}</span><div class="tx"><div class="nm">'
            f'{T.esc(L(*_ready_name(r)))}</div><div class="sub">{T.esc(sub)}</div></div></div>'
            f'<div class="cs">{vd}{chips}</div>{table}<div class="nt">{T.esc(note.strip())}</div></div>')


def _open_ready(mid):
    ss["pb_open"] = ("ready", mid)


def ready_section(bots, can_add):
    """Five ready bots with the lab's best settings, and their test on real prices (2020 to now)."""
    res = MLB.results()
    ids = [m for m, r in (res or {}).get("bots", {}).items() if (r.get("bot_test") or {}).get("plain") and r.get("plain_bot")]
    if not ids:
        return
    have = {m for m in ids for b in bots if _is_ready_bot(b, res["bots"][m])}
    sub = L("The strategies that held up best in the lab, each with the settings that tested best: added with one click. The numbers "
            "are the whole bot on all companies, run by this site's bot engine on real prices from 2020 to now.",
            "الاستراتيجيات اللي صمدت أكثر في المختبر، وكل وحدة بالإعدادات اللي طلعت أفضل، وتنضاف بضغطة. الأرقام للبوت كامل على كل "
            "الشركات، محسوبة بمحرّك البوتات نفسه في الموقع على أسعار حقيقية من 2020 لين اليوم.")
    ui.html(f'<div class="aihd"><span class="i">{T.icon("smart_toy")}</span><span class="t">{L("Ready bots", "بوتات جاهزة")}</span>'
            f'<span class="s">{T.esc(sub)}</span></div>')
    order = sorted(ids, key=lambda m: -((res["bots"][m]["bot_test"]["plain"] or {}).get("sharpe") or -9))
    for i in range(0, len(order), 3):
        cols = st.columns(3)
        for col, mid in zip(cols, order[i:i + 3]):
            with col:
                with st.container(key=f"aicard_r_{mid}"):
                    ui.html(_ready_card(mid, res["bots"][mid], mid in have))
                    st.button(L("Add this bot", "أضف هالبوت"), key=f"pb_ready_{mid}", icon=":material/add:", width="stretch",
                              on_click=_open_ready, args=(mid,), disabled=not can_add or mid in have)
    st.caption(L("The stock list is today's large companies, so every number is on the high side: compare a bot with holding the "
                 "same stocks. We also trained AI models on 225,000 of these signals; none beat these settings on 2020 to now, so "
                 "none is offered. Past results don't promise future ones.",
                 "قائمة الأسهم هي الشركات الكبيرة اليوم، فكل الأرقام مرتفعة شوي: قارن البوت بالاحتفاظ بنفس الأسهم. ودرّبنا نماذج ذكاء "
                 "اصطناعي على 225 ألف من هالإشارات، وولا واحد تفوّق على هالإعدادات من 2020 لين اليوم، فما عرضناها. النتائج السابقة ما "
                 "تضمن اللي جاي."))


def _ready_body(mid, bots):
    if not can_edit():
        return
    if len(bots) >= PB.MAX_BOTS:
        st.info(L(f"You have {PB.MAX_BOTS} bots, the maximum. Delete one to add another.",
                  f"عندك {PB.MAX_BOTS} بوتات، وهذا الحد الأعلى. احذف واحد عشان تضيف غيره."), icon=":material/block:")
        return
    r = ((MLB.results() or {}).get("bots") or {}).get(mid)
    if not r or not r.get("plain_bot"):
        st.error(L("This bot isn't available.", "هالبوت غير متاح."))
        return
    ui.html(_ready_card(mid, r, False))
    c = r["plain_bot"]
    a, b = st.columns(2)
    a.number_input(L("Virtual capital ($)", "رأس المال الوهمي ($)"), 100, 100_000_000, value=1_000_000, step=10_000, key="pb_rd_cap")
    b.selectbox(L("Start", "البداية"), [0, 365], key="pb_rd_start",
                format_func=lambda d: L("Today (forward test only)", "اليوم (تجربة أمامية فقط)") if d == 0 else
                L("A year ago (adds a one-year simulation)", "قبل سنة (يضيف محاكاة سنة)"))
    if not st.button(L("Start the bot", "شغّل البوت"), type="primary", icon=":material/play_arrow:", key="pb_rd_go", width="stretch"):
        return
    start = PB.today_ny() - timedelta(days=int(ss.get("pb_rd_start") or 0))
    rec = PB.make_record(L(*_ready_name(r)), "all", "all", {x: {} for x in c["strategies"]}, c["max_pos"],
                         float(ss.get("pb_rd_cap") or 1_000_000), 0.05, c.get("stop_pct", 0.0), c.get("atr_mult", 0.0),
                         c.get("tp_pct", 0.0), c.get("trail_pct", 0.0), pd.Timestamp(start).strftime("%Y-%m-%d"), instrument="stock",
                         risk_pct=c.get("risk_pct", 0.0), regime=c.get("regime", 0), trend_filter=c.get("trend_filter", 0))
    try:
        PB.create_bot(rec)
    except PB.StoreError as e:
        storage_notice(e)
        return
    new = [x for x in PB.list_bots() if _is_ready_bot(x, r)]
    if new:
        ss["pb_selected"] = [new[-1]["id"]]
    st.toast(L("Bot started.", "بدأ البوت."), icon=":material/smart_toy:")
    st.rerun()


def _is_ai_bot(b, mid, r):
    """Is this saved bot the AI bot `mid` (same model, same strategies)?"""
    return b.get("ml") == r.get("ml", mid) and set(b.get("strategies") or {}) == set((r.get("bot") or {}).get("strategies") or [])


def _open_ai(mid):
    ss["pb_open"] = ("ai", mid)


def ai_section(bots, can_add):
    """The five AI bots with their test (2020 to now, years their models never saw) and a button to add each one."""
    res = MLB.results()
    # only the AI bots whose model beat the same bot without it on 2020 to now (years the model never saw)
    ids = [m for m, r in (res or {}).get("bots", {}).items() if MLB.load(r.get("ml", m)) is not None and MLB.verdict(r) == "up"]
    if not ids:
        return
    have = {m for m in ids for b in bots if _is_ai_bot(b, m, res["bots"][m])}
    y0, y1 = res["train"][0][:4], res["train"][1][:4]
    sub = L(f"Each one has its own model, trained on every buy signal its strategy gave on 500+ US stocks from {y0} to {y1} and how "
            "each trade ended. Tested on 2020 to now, years it never saw.",
            f"كل بوت له نموذج خاص، تدرّب على كل إشارة شراء أعطتها استراتيجيته على أكثر من 500 سهم أمريكي من {y0} لين {y1} وعلى "
            "نتيجة كل صفقة. ومختبر على 2020 لين اليوم، سنين ما شافها.")
    ui.html(f'<div class="aihd"><span class="i">{T.icon("psychology")}</span><span class="t">{L("AI bots", "بوتات الذكاء الاصطناعي")}</span>'
            f'<span class="s">{T.esc(sub)}</span></div>')
    order = sorted(ids, key=lambda m: -(((res["bots"][m].get("bot_test") or {}).get("ai") or {}).get("sharpe") or -9))
    for i in range(0, len(order), 3):
        cols = st.columns(3)
        for col, mid in zip(cols, order[i:i + 3]):
            with col:
                with st.container(key=f"aicard_{mid}"):
                    ui.html(_ai_card(mid, res["bots"][mid], mid in have))
                    st.button(L("Add this bot", "أضف هالبوت"), key=f"pb_ai_{mid}", icon=":material/add:", width="stretch",
                              on_click=_open_ai, args=(mid,), disabled=not can_add or mid in have,
                              type="primary" if MLB.verdict(res["bots"][mid]) == "up" else "secondary")
    st.caption(L("The numbers are for the whole bot on all companies, with the settings shown, run by this site's bot engine. The stock "
                 "list is today's large companies, so every number is on the high side: compare \"with\" and \"without\" AI. Past "
                 "results don't promise future ones.",
                 "الأرقام للبوت كامل على كل الشركات بالإعدادات المكتوبة، ومحسوبة بمحرّك البوتات نفسه في الموقع. قائمة الأسهم هي الشركات "
                 "الكبيرة اليوم، فكل الأرقام مرتفعة شوي: قارن \"مع\" و\"بدون\" الذكاء. النتائج السابقة ما تضمن اللي جاي."))


def _ai_body(mid, bots):
    if not can_edit():
        return
    if len(bots) >= PB.MAX_BOTS:
        st.info(L(f"You have {PB.MAX_BOTS} bots, the maximum. Delete one to add another.",
                  f"عندك {PB.MAX_BOTS} بوتات، وهذا الحد الأعلى. احذف واحد عشان تضيف غيره."), icon=":material/block:")
        return
    res = MLB.results() or {}
    r = (res.get("bots") or {}).get(mid)
    if not r or MLB.load(r.get("ml", mid)) is None:
        st.error(L("This AI bot isn't available.", "هالبوت غير متاح."))
        return
    ui.html(_ai_card(mid, r, False))
    c = r["bot"]
    a, b = st.columns(2)
    a.number_input(L("Virtual capital ($)", "رأس المال الوهمي ($)"), 100, 100_000_000, value=1_000_000, step=10_000, key="pb_ai_cap")
    today = PB.today_ny()
    b.selectbox(L("Start", "البداية"), [0, 365], key="pb_ai_start",
                format_func=lambda d: L("Today (forward test only)", "اليوم (تجربة أمامية فقط)") if d == 0 else
                L("A year ago (adds a one-year simulation)", "قبل سنة (يضيف محاكاة سنة)"))
    if not st.button(L("Start the AI bot", "شغّل بوت الذكاء"), type="primary", icon=":material/play_arrow:", key="pb_ai_go", width="stretch"):
        return
    start = today - timedelta(days=int(ss.get("pb_ai_start") or 0))
    rec = PB.make_record(L(*r["name"]), "all", "all", {x: {} for x in c["strategies"]}, c["max_pos"], float(ss.get("pb_ai_cap") or 1_000_000),
                         0.05, c.get("stop_pct", 0.0), c.get("atr_mult", 0.0), c.get("tp_pct", 0.0), c.get("trail_pct", 0.0),
                         pd.Timestamp(start).strftime("%Y-%m-%d"), instrument="stock", risk_pct=c.get("risk_pct", 0.0),
                         regime=c.get("regime", 0), trend_filter=c.get("trend_filter", 0), ml=r.get("ml", mid))
    try:
        PB.create_bot(rec)
    except PB.StoreError as e:
        storage_notice(e)
        return
    new = [x for x in PB.list_bots() if _is_ai_bot(x, mid, r)]
    if new:
        ss["pb_selected"] = [new[-1]["id"]]
    st.toast(L("AI bot started.", "بدأ بوت الذكاء."), icon=":material/psychology:")
    st.rerun()


def ai_today(sim):
    """What an AI bot's model made of the last session's buy signals (its chance of a win, and which pass)."""
    info = sim.get("ml_last")
    if not info:
        return
    with st.expander(L("What the AI sees today", "وش يشوف الذكاء اليوم"), icon=":material/psychology:"):
        if "market" in info:
            p_, thr = float(info["market"]), float(info.get("threshold") or 0)
            go = p_ >= thr
            ui.html('<div class="aiday"><span class="' + ("go" if go else "") + '">' + T.icon("check" if go else "block")
                    + f'<b>{p_ * 100:.0f}%</b> ' + T.esc(L("chance of a good month for stocks", "احتمال شهر زين للأسهم")) + '</span></div>')
            st.caption(L(f"At the close of {info['day']}. The bot holds stocks while the chance is at least {thr * 100:.0f}%; under it, it "
                         "buys nothing and sells what it holds at the next open. "
                         f"It called {info.get('risky_days', 0)} of the bot's {info.get('days', 0)} sessions risky.",
                         f"عند إغلاق {info['day']}. البوت يمسك أسهم ما دام الاحتمال {thr * 100:.0f}% أو أكثر؛ وتحته ما يشتري شي ويبيع اللي "
                         f"عنده عند الافتتاح القادم. اعتبر {info.get('risky_days', 0)} من {info.get('days', 0)} جلسة للبوت خطرة."))
            return
        sig = info.get("signals") or []
        if not sig:
            st.caption(L(f"No buy signals at the close of {info['day']}.", f"ما فيه إشارات شراء عند إغلاق {info['day']}."))
            return
        thr = float(info.get("threshold") or 0)
        ui.html('<div class="aiday">' + "".join(
            f'<span class="{"go" if p >= thr else ""}">{T.icon("check" if p >= thr else "close")}<b>{T.esc(s_)}</b> {p * 100:.0f}%</span>'
            for s_, p in sig) + "</div>")
        st.caption(L(f"The buy signals of {info['day']} with the model's chance of a winning trade. Green = at least {thr * 100:.0f}%, so "
                     "the bot may buy it at the next open if it has a free place (highest chances first).",
                     f"إشارات الشراء في {info['day']} مع احتمال نجاح الصفقة عند النموذج. الأخضر = {thr * 100:.0f}% أو أكثر، فممكن البوت يشتريه "
                     "عند الافتتاح القادم إذا عنده مكان فاضي (الأعلى احتمالاً أول)."))


def open_dialog(op, bots):
    mode, bid = op
    bot = next((b for b in bots if b["id"] == bid), None)
    if mode == "delete" and bot:
        st.dialog(L("Delete bot", "حذف البوت"))(_delete_body)(bot)
    elif mode == "edit" and bot:
        st.dialog(L("Edit bot", "تعديل البوت"), width="large")(_bot_dialog_body)("edit", bot, len(bots))
    elif mode == "add":
        st.dialog(L("Add a bot", "أضف بوت"), width="large")(_bot_dialog_body)("add", None, len(bots))
    elif mode == "ai":
        st.dialog(L("Add an AI bot", "أضف بوت ذكاء اصطناعي"), width="large")(_ai_body)(bid, bots)
    elif mode == "ready":
        st.dialog(L("Add a ready bot", "أضف بوت جاهز"), width="large")(_ready_body)(bid, bots)


# =====================================================================
# page
# =====================================================================
def page_paper_bots():
    ui.html(PAGE_CSS + HEAT_CSS + (PAGE_RTL_CSS if is_ar() else ""))
    try:
        bots, err = PB.list_bots(), None
    except PB.StoreError as e:
        bots, err = [], e

    sims, spy = [], None
    if bots:
        big = any(b["kind"] != "company" for b in bots)
        with st.spinner(L("Updating the bots with the latest prices" + (" (groups of stocks can take up to a minute)..." if big else "..."),
                          "جاري تحديث البوتات بآخر الأسعار" + (" (مجموعات الأسهم قد تاخذ لين دقيقة)..." if big else "..."))):
            sims, spy = PB.run_all(bots)
    if sims and "pb_phase" not in ss:              # the forward tests once a session has been saved, else the simulations
        ss["pb_phase"] = "live" if _saved_sessions(sims) else "sim"
    shown = phase_sims(sims, phase())
    ui.html(hero_html(shown, len(bots)))
    storage_notice(err)
    if sims:
        ui.safe(phase_switch, sims)
    sel = ui.safe(leaderboard, shown, len(bots), err is None and len(bots) < PB.MAX_BOTS) or []

    op = ss.pop("pb_open", None)
    if op and err is None:
        open_dialog(op, bots)

    if not bots and err is None:
        ui.html(f'<div class="card" style="line-height:1.9;margin-top:14px">{T.ico("smart_toy", "acc")} ' + L(
            "No bots yet. Press <b>Add Bot</b>, choose what the bot trades (a company, a sector, an industry or all companies), what it buys "
            "(stocks, options or both) and its strategies. From then on it checks its strategies after every US close and trades with virtual "
            "money at the next open.",
            "ما فيه بوتات للحين. اضغط <b>أضف بوت</b>، واختر وش يتداول (شركة أو قطاع أو صناعة أو كل الشركات)، ووش يشتري (أسهم أو أوبشن أو الاثنين)، "
            "واستراتيجياته. بعدها يفحص استراتيجياته بعد كل إغلاق للسوق الأمريكي، ويتداول بأموال وهمية عند الافتتاح التالي.") + "</div>")
    elif sims:
        chosen = [s for s in ranked(shown) if s["bot"]["id"] in sel]
        if not chosen:
            ui.html(f'<div class="card" style="line-height:1.9;margin-top:14px">{T.ico("ads_click", "acc")} ' + L(
                "Click a bot's card to see its dashboard. Select one, several, or press <b>Select all</b>.",
                "اضغط على كرت البوت عشان تشوف لوحة أدائه. تقدر تحدد واحد أو أكثر، أو تضغط <b>تحديد الكل</b>.") + "</div>")
        elif len(chosen) == 1:
            ui.safe(details, chosen[0])
        else:
            ui.safe(portfolio, chosen, spy, shown)

    ui.safe(ready_section, bots, err is None and len(bots) < PB.MAX_BOTS)
    ui.safe(ai_section, bots, err is None and len(bots) < PB.MAX_BOTS)
    ui.safe(test_section)
    ui.safe(compare_section, sims)
    st.caption(L("Virtual trading on real daily prices (dividend-adjusted, may be delayed); the Opening Range Breakout uses 5-minute prices from "
                 "the last 60 days. Forward tests are saved session by session after each US close and never recalculated; historical "
                 "simulations are recalculated whenever the page opens. No real money and no broker are involved. Past results do not "
                 "guarantee future returns.",
                 "تداول وهمي على أسعار يومية حقيقية (معدّلة بالتوزيعات وقد تكون متأخرة)، واختراق نطاق الافتتاح يستخدم أسعار 5 دقائق لآخر 60 يوم. "
                 "التجارب الأمامية تنحفظ جلسة بجلسة بعد كل إغلاق للسوق الأمريكي وما يُعاد حسابها، والمحاكاة التاريخية تنحسب من جديد كل ما "
                 "تفتح الصفحة. لا توجد أموال حقيقية ولا وسيط. النتائج السابقة لا تضمن المستقبل."))
    ui.foot()

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "12.2"
