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
Adding, editing and deleting open in dialogs; a password unlocks them when BOTS_PASSWORD is set.
"""
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
                    "The Strategy Lab strategies. Pick one, several or all of them; any of them can open a trade.",
                    "استراتيجيات مختبر الاستراتيجيات. اختر وحدة أو أكثر أو كلها، وأي وحدة منها تقدر تفتح صفقة."),
         "combo": ("hub", "Combined strategies", "الاستراتيجيات المركّبة",
                   "Complete setups written as exact numbers: trend, pullback or breakout, confirmation, and their own stop, "
                   "target and time stop.",
                   "استراتيجيات كاملة مكتوبة بأرقام دقيقة: اتجاه وتراجع أو اختراق وتأكيد، ولكل وحدة وقفها وهدفها ووقفها الزمني.")}
PB_ICON = {PBK.TREND_PULLBACK: "trending_up", PBK.BREAKOUT_RETEST: "north_east", PBK.SQUEEZE: "compress", PBK.RANGE: "swap_vert",
           PBK.ORB: "timer"}
INSTR_LABEL = {"stock": ("Stocks", "أسهم"), "options": ("Options", "أوبشن"), "both": ("Both", "الاثنين")}
INSTR_CHIP = {"stock": ("show_chart", "Stocks", "أسهم"), "options": ("receipt_long", "Options", "أوبشن"),
              "both": ("layers", "Stocks + options", "أسهم + أوبشن")}
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
            "pb_fee": 0.05, "pb_stop": 2.0, "pb_atr": 0.0, "pb_tp": 0.0, "pb_trail": 0.0, "pb_combine": "any", "pb_instr": "stock",
            "pb_otype": "call", "pb_dte": 30, "pb_strike": 0, "pb_oalloc": 5.0, "pb_otp": 100.0, "pb_osl": 50.0,
            "pb_mode": "single", "pb_store_pb": [PBK.TREND_PULLBACK], "pb_pbmode": "any", "pb_pbwin": 5}

_A, _V, _C, _D, _G, _BG, _BD, _MU = T.ACCENT, T.VIOLET, T.CYAN, T.DOWN, T.GOLD, T.CARD2, T.BORDER, T.MUTED
_CARD_H = 352          # every card in the leaderboard (bots and "Add Bot") has this height
PAGE_CSS = f"""<style>
/* ---------- red actions (delete dialog) ---------- */
[class*="st-key-pbred"] button {{ border-color:{_D}88 !important; }}
[class*="st-key-pbred"] button p, [class*="st-key-pbred"] button span {{ color:{_D} !important; }}
[class*="st-key-pbred"] button:hover {{ border-color:{_D} !important; background:{_D}1A !important; }}

/* ---------- hero: the bots on the brand's rising line ---------- */
.pbhero {{ position:relative; overflow:hidden; border-radius:22px; border:1px solid {_BD}; margin:2px 0 16px; min-height:258px;
  background:linear-gradient(120deg,#060c1c,#0c1d3f,#1c1543,#071a33); background-size:300% 300%; animation:sky 20s ease-in-out infinite; }}
.pbhero .grid {{ position:absolute; inset:0; pointer-events:none;
  background-image:linear-gradient(rgba(34,211,238,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(34,211,238,.07) 1px,transparent 1px);
  background-size:36px 36px; -webkit-mask-image:radial-gradient(ellipse at 78% 45%,#000 0%,transparent 68%);
  mask-image:radial-gradient(ellipse at 78% 45%,#000 0%,transparent 68%); }}
.pbhero .art {{ position:absolute; top:0; bottom:0; right:0; width:58%; pointer-events:none; }}
.pbhero .art svg {{ width:100%; height:100%; display:block; }}
.pbhero .txt {{ position:relative; z-index:2; padding:26px 30px 24px; max-width:640px;
  background:linear-gradient(90deg,rgba(10,14,23,.78) 0%,rgba(10,14,23,.35) 70%,rgba(10,14,23,0) 100%); }}
.pbhero.rtl .art {{ right:auto; left:0; }}
.pbhero.rtl .txt {{ margin-left:auto; background:linear-gradient(270deg,rgba(10,14,23,.78) 0%,rgba(10,14,23,.35) 70%,rgba(10,14,23,0) 100%); }}
.pbhero .eb {{ color:{_C}; font-weight:800; letter-spacing:.2em; font-size:.72rem; text-transform:uppercase; display:flex; align-items:center; gap:8px; }}
.pbhero .eb .ms {{ font-size:1.05rem; }}
.pbhero .t {{ font-size:2.4rem; font-weight:800; line-height:1.08; margin:8px 0 6px; color:#fff; letter-spacing:-.02em; }}
.pbhero .t b {{ background:linear-gradient(90deg,{_A},{_V},{_C}); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.pbhero .tg {{ color:#C7CFDD; font-size:.94rem; line-height:1.6; max-width:540px; }}
.pbhero .chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
.pbhero .chip {{ background:rgba(17,23,35,.8); border:1px solid {_BD}; backdrop-filter:blur(6px); border-radius:10px; padding:6px 10px;
  font-size:.8rem; display:inline-flex; align-items:center; gap:7px; color:#C9D0DC; font-variant-numeric:tabular-nums; }}
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
.pbc::before {{ content:""; position:absolute; left:0; right:0; top:0; height:3px; background:linear-gradient(90deg,{_A},{_V},{_C});
  opacity:0; transition:opacity .18s; }}
.pbc .top {{ display:flex; justify-content:space-between; align-items:center; height:22px; margin:-4px 0 8px; gap:6px; }}
.pbc .it {{ display:inline-flex; align-items:center; gap:5px; font-size:.62rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase;
  color:{_MU}; transition:opacity .15s; white-space:nowrap; overflow:hidden; }}
.pbc .it .ms {{ font-size:.95rem; color:{_C}; }}
.pbc .rk {{ display:inline-flex; align-items:center; gap:3px; font-weight:800; color:{_MU}; transition:opacity .15s; direction:ltr; }}
.pbc .rk .ms {{ font-size:1.05rem; }}
.pbc .rk.r1 {{ color:{_G}; }} .pbc .rk.r2 {{ color:#C7CEDB; }} .pbc .rk.r3 {{ color:#D9925F; }}
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
[class*="st-key-pbcard_"]:hover .pbc {{ box-shadow:0 14px 34px rgba(61,123,255,.20); }}
[class*="st-key-pbcard_"]:hover .pbc::before {{ opacity:.95; }}
[class*="st-key-pbcard_"]:hover .pbc .rk, [class*="st-key-pbcard_"]:hover .pbc .it {{ opacity:0; }}
[class*="st-key-pbcard_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_pick_"] {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; width:auto !important; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_pick_"] .stButton, [class*="st-key-pbcard_"] [class*="st-key-pb_pick_"] button
  {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_edit_"], [class*="st-key-pbcard_"] [class*="st-key-pb_trash_"]
  {{ position:absolute !important; top:9px; z-index:6; width:auto !important; margin:0 !important; opacity:0; transition:opacity .15s ease; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_edit_"] {{ right:9px; left:auto; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_trash_"] {{ left:9px; right:auto; }}
[class*="st-key-pbcard_"]:hover [class*="st-key-pb_edit_"], [class*="st-key-pbcard_"]:hover [class*="st-key-pb_trash_"] {{ opacity:1; }}
[class*="st-key-pb_edit_"] button, [class*="st-key-pb_trash_"] button {{ min-height:0 !important; padding:3px 8px !important; border-radius:10px !important;
  background:{_BG} !important; }}
[class*="st-key-pb_edit_"] button {{ border:1.5px solid {_A} !important; }}
[class*="st-key-pb_edit_"] button span {{ color:{_A} !important; }}
[class*="st-key-pb_trash_"] button {{ border:1.5px solid {_D} !important; }}
[class*="st-key-pb_trash_"] button span {{ color:{_D} !important; }}
[class*="st-key-pb_edit_"] button p, [class*="st-key-pb_trash_"] button p {{ display:none !important; }}
@media (hover: none) {{ [class*="st-key-pbcard_"] [class*="st-key-pb_edit_"], [class*="st-key-pbcard_"] [class*="st-key-pb_trash_"] {{ opacity:1; }} }}

/* ---------- "Add Bot": the logo tile with a plus and the cyan trend arrow ---------- */
.pbadd {{ align-items:center; justify-content:center; gap:10px; text-align:center; border:1.5px dashed {_A}77 !important;
  background:radial-gradient(120% 80% at 50% 0%,rgba(61,123,255,.12),transparent 62%),linear-gradient(180deg,{_BG},{T.CARD}) !important; }}
[class*="st-key-pbcard_add"]:hover .pbadd {{ border-color:{_A} !important; border-style:solid !important;
  box-shadow:0 0 0 1px {_A}55, 0 16px 40px rgba(61,123,255,.28) !important; }}
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
.pbadd .ttl {{ font-weight:800; font-size:1.15rem; background:linear-gradient(90deg,{_A},{_V},{_C}); -webkit-background-clip:text;
  background-clip:text; color:transparent; }}
.pbadd .sub {{ color:{_MU}; font-size:.78rem; }}
.pbadd .slots {{ display:flex; gap:6px; justify-content:center; margin-top:2px; direction:ltr; }}
.pbadd .slots span {{ width:18px; height:6px; border-radius:4px; background:{_BD}; display:block; }}
.pbadd .slots span.on {{ background:linear-gradient(90deg,{_A},{_V}); }}

/* ---------- details ---------- */
.pbid {{ position:relative; overflow:hidden; margin:0 !important; }}
.pbid::before {{ content:""; position:absolute; top:0; bottom:0; left:0; width:3px; background:linear-gradient(180deg,{_A},{_V},{_C}); }}
.pbid .co .tk {{ font-size:1.12rem; }}
.pbid .bdgs {{ margin-top:10px; }}
.pbk {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; }}
.pbsub {{ display:flex; align-items:center; gap:8px; font-weight:800; font-size:.98rem; color:#fff; margin:8px 0 0; }}
.pbsub .ms {{ color:#fff; background:linear-gradient(135deg,{_A},{_V}); border-radius:8px; padding:4px; font-size:1rem; }}
.pbsub .muted {{ font-size:.76rem; font-weight:600; }}
.pbsel {{ display:flex; flex-wrap:wrap; gap:8px; }}
.pbsel .c {{ display:inline-flex; align-items:center; gap:6px; padding:5px 10px; border-radius:10px; background:rgba(138,148,167,.12);
  border:1px solid {_BD}; font-size:.78rem; font-weight:700; color:#C9D0DC; }}
.pbsel .c .pill {{ min-width:0; padding:1px 6px; font-size:.72rem; }}
/* every part of the details is its own block: the same space between parts, the normal gap inside them */
[class*="st-key-pbsec_"] {{ margin-top:20px; }}
[class*="st-key-pbsec_"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
[class*="st-key-pbsec_"] .sec {{ margin:0 !important; }}
[class*="st-key-pbsec_"] .tdk {{ margin-bottom:0 !important; }}
[class*="st-key-pbcard_"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}

/* ---------- panels: open positions / recent trades / calendar ---------- */
.pbp {{ position:relative; overflow:hidden; background:linear-gradient(180deg,{_BG},{T.CARD}); border:1px solid {_BD}; border-radius:18px;
  padding:14px 16px 10px 19px; margin:0; }}
.pbp::before {{ content:""; position:absolute; top:0; bottom:0; left:0; width:3px; background:linear-gradient(180deg,{_A},{_V},{_C}); }}
.pbp .hd {{ display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:10px; }}
.pbp .tt {{ display:flex; align-items:center; gap:8px; font-weight:800; font-size:1.02rem; color:#fff; }}
.pbp .tt .ms {{ color:#fff; background:linear-gradient(135deg,{_A},{_V}); border-radius:8px; padding:4px; font-size:1rem; }}
.pbp .tt .live {{ width:8px; height:8px; border-radius:50%; background:{_G}; box-shadow:0 0 0 3px rgba(245,185,74,.18); }}
.pbp .sum {{ display:flex; flex-wrap:wrap; gap:7px; align-items:center; }}
.pbp .sum .c {{ display:inline-flex; align-items:center; gap:7px; background:rgba(138,148,167,.10); border:1px solid {_BD}; border-radius:999px;
  padding:4px 12px; font-size:.75rem; font-weight:700; color:#AEB7C6; line-height:1.4; white-space:nowrap; }}
.pbp .sum .c b {{ color:#fff; unicode-bidi:isolate; direction:ltr; font-weight:800; }}
.pbp .sum .c .pbox {{ padding:1px 8px; font-size:.74rem; border-radius:999px; line-height:1.4; margin:0; }}
.pbempty {{ color:{_MU}; padding:10px 2px 8px; display:flex; align-items:center; gap:8px; }}
.pbscroll {{ overflow-x:auto; }}
/* modern slim tables: one line per row, rounded rows, no grid lines */
.pbt {{ width:100%; min-width:900px; border-collapse:separate !important; border-spacing:0 4px !important; font-size:.8rem; direction:ltr;
  border:none !important; margin:-4px 0 0 !important; background:none !important; }}
.pbt thead tr, .pbt tbody tr {{ background:none !important; border:none !important; }}
.pbt th {{ color:{_MU}; font-size:.6rem; letter-spacing:.09em; text-transform:uppercase; text-align:left; padding:6px 12px 2px !important;
  font-weight:800; white-space:nowrap; border:none !important; background:none !important; }}
.pbt td {{ padding:6px 12px !important; white-space:nowrap; vertical-align:middle; text-align:left; line-height:1.35; color:#DCE2EC;
  background:rgba(255,255,255,.028) !important; border:none !important; border-top:1px solid rgba(255,255,255,.045) !important;
  border-bottom:1px solid rgba(255,255,255,.045) !important; transition:background .15s ease; }}
.pbt td:first-child {{ border-left:1px solid rgba(255,255,255,.045) !important; border-radius:10px 0 0 10px; }}
.pbt td:last-child {{ border-right:1px solid rgba(255,255,255,.045) !important; border-radius:0 10px 10px 0; }}
.pbt tbody tr:hover td {{ background:rgba(61,123,255,.10) !important; }}
.pbt th.r, .pbt td.r {{ text-align:right; }}
.pbt b {{ color:#fff; font-weight:800; }}
.pbt .as {{ display:inline-flex; align-items:center; gap:8px; color:#fff !important; text-decoration:none !important; }}
.pbt .as .lg {{ width:22px !important; height:22px !important; font-size:9px !important; }}
.pbt .as b {{ font-size:.84rem; }} .pbt .as:hover b {{ color:#7EA6FF; }}
.pbt .m {{ color:{_MU}; font-size:.72rem; font-weight:600; }}
.pbt .up {{ color:#4ADE80; font-weight:700; }} .pbt .dn {{ color:#F87171; font-weight:700; }}
.pbt .badge {{ margin:0; padding:2px 9px; font-size:.64rem; }}
.pbt .pbox {{ padding:1px 9px; font-size:.76rem; border-radius:999px; margin-left:8px; }}
a.pblink {{ display:inline-flex; align-items:center; gap:4px; color:#7EA6FF !important; font-weight:800; font-size:.8rem;
  text-decoration:none !important; padding:4px 10px; border-radius:10px; border:1px solid {_A}55; background:{_A}14; }}
a.pblink:hover {{ color:#fff !important; border-color:{_A}; background:{_A}33; }}
a.pblink .ms {{ font-size:1rem; }}
.pbanchor {{ scroll-margin-top:96px; height:1px; }}

/* ---------- monthly returns: every month is a button that opens its calendar ---------- */
[class*="st-key-pbmg_"] {{ overflow-x:auto; overflow-y:hidden; max-width:860px; gap:5px !important; padding:10px 12px 12px;
  background:linear-gradient(180deg,{_BG},{T.CARD}); border:1px solid {_BD}; border-radius:16px; }}
[class*="st-key-pbmg_"] [data-testid="stHorizontalBlock"] {{ min-width:680px; flex-wrap:nowrap !important; gap:4px !important;
  align-items:center !important; }}
[class*="st-key-pbmg_"] [data-testid="stColumn"] {{ min-width:0 !important; }}
[class*="st-key-pbmg_"] [data-testid="stElementContainer"], [class*="st-key-pbmg_"] .stMarkdown,
[class*="st-key-pbmg_"] [data-testid="stMarkdownContainer"] {{ margin:0 !important; }}
[class*="st-key-pbmg_"] [data-testid="stMarkdownContainer"] p {{ margin:0 !important; }}
.pbmh {{ color:{_MU}; font-size:.58rem; font-weight:800; text-align:center; letter-spacing:.06em; text-transform:uppercase; line-height:16px; }}
.pbmy {{ font-weight:800; color:#fff; font-size:.78rem; line-height:26px; }}
.pbmt {{ text-align:center; line-height:26px; }} .pbmt .pbox {{ padding:2px 6px; font-size:.68rem; border-radius:6px; }}
.pbme {{ height:26px; border-radius:6px; background:rgba(138,148,167,.06); }}
[class*="st-key-pbmo_"] button {{ min-height:26px !important; height:26px; padding:0 2px !important; border-radius:6px !important;
  border:0 !important; transition:transform .12s ease, box-shadow .12s ease; }}
[class*="st-key-pbmo_"] button p {{ font-size:.68rem !important; font-weight:700 !important; color:#1F2937 !important; white-space:nowrap; direction:ltr; }}
[class*="st-key-pbmo_"] button:hover {{ transform:translateY(-2px); box-shadow:0 6px 16px rgba(0,0,0,.35); }}
[class*="st-key-pbmo_"][class*="_on_"] button {{ box-shadow:0 0 0 2px {T.BG}, 0 0 0 4px {_A} !important; transform:translateY(-2px); }}
[class*="st-key-pbcalbox_"] {{ background:linear-gradient(180deg,{_BG},{T.CARD}); border:1px solid {_A}66; border-radius:18px; padding:14px 16px;
  box-shadow:0 12px 30px rgba(61,123,255,.12); margin-top:6px; max-width:1100px; }}
.pbct {{ display:flex; flex-wrap:wrap; align-items:center; gap:8px; font-weight:800; font-size:1rem; color:#fff; }}
.pbct .ms {{ color:#fff; background:linear-gradient(135deg,{_A},{_V}); border-radius:8px; padding:4px; font-size:1rem; }}
.pbct .muted {{ font-size:.78rem; font-weight:600; }} .pbct .pill {{ min-width:0; padding:2px 8px; font-size:.76rem; }}
.pbct .pbox {{ padding:2px 8px; font-size:.8rem; }}

/* ---------- add / edit form: a banner in the hero's colours, then numbered cards with space between them ---------- */
.pbfb {{ position:relative; overflow:hidden; border-radius:18px; border:1px solid {_BD}; padding:16px 20px 14px; min-height:118px;
  background:linear-gradient(120deg,#060c1c,#0c1d3f,#1c1543,#071a33); background-size:300% 300%; animation:sky 20s ease-in-out infinite; }}
.pbfb .art {{ position:absolute; top:0; bottom:0; right:0; width:34%; pointer-events:none; }}
.pbfb .art svg {{ width:100%; height:100%; display:block; }}
.pbfb .ln {{ animation:pbdraw 7s ease-in-out infinite; }}
.pbfb .tx {{ position:relative; z-index:2; max-width:76%; }}
.pbfb.rtl .art {{ right:auto; left:0; transform:scaleX(-1); }}
.pbfb.rtl .tx {{ margin-left:auto; }}
.pbfb .eb {{ color:{_C}; font-weight:800; letter-spacing:.18em; font-size:.66rem; text-transform:uppercase; display:flex; align-items:center; gap:6px; }}
.pbfb .eb .ms {{ font-size:.95rem; }}
.pbfb .t {{ font-size:1.55rem; font-weight:800; color:#fff; margin:5px 0 3px; letter-spacing:-.01em; line-height:1.15; }}
.pbfb .t b {{ background:linear-gradient(90deg,{_A},{_V},{_C}); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.pbfb .s {{ color:#C7CFDD; font-size:.84rem; line-height:1.5; }}
.pbfb .pbstp {{ display:flex; flex-wrap:wrap; gap:4px; margin-top:11px; }}
.pbfb .pbstp span {{ display:inline-flex; align-items:center; gap:5px; font-size:.7rem; font-weight:700; color:#C9D0DC; background:rgba(17,23,35,.72);
  border:1px solid rgba(255,255,255,.06); border-radius:999px; padding:2px 9px 2px 3px; white-space:nowrap; }}
.pbfb.rtl .pbstp span {{ padding:2px 3px 2px 9px; }}
.pbfb .pbstp i {{ font-style:normal; width:17px; height:17px; border-radius:50%; display:grid; place-items:center; font-size:.62rem; font-weight:800;
  color:#fff; background:linear-gradient(135deg,{_A},{_V}); }}
[class*="st-key-pbf_"] {{ position:relative; overflow:hidden; background:linear-gradient(180deg,{_BG},{T.CARD}); border:1px solid {_BD};
  border-radius:18px; padding:16px 18px 16px; margin-top:16px; box-shadow:0 10px 26px rgba(0,0,0,.18); }}
[class*="st-key-pbf_"]::before {{ content:""; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,{_A},{_V},{_C}); }}
[class*="st-key-pbf_"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
.pbfh {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:2px; }}
.pbfh .n {{ width:28px; height:28px; border-radius:9px; display:grid; place-items:center; font-weight:800; font-size:.84rem; color:#fff; flex:none;
  background:linear-gradient(135deg,{_A},{_V}); box-shadow:0 6px 16px rgba(61,123,255,.35); }}
.pbfh .t {{ display:flex; align-items:center; gap:7px; font-weight:800; font-size:1.03rem; color:#fff; }}
.pbfh .t .ms {{ color:{_C}; font-size:1.15rem; }}
.pbfh .h {{ color:{_MU}; font-size:.76rem; font-weight:600; margin-inline-start:auto; }}
.pbfs {{ display:flex; align-items:center; gap:6px; font-weight:800; font-size:.74rem; color:#AEB7C6; letter-spacing:.08em; text-transform:uppercase; }}
.pbfs .ms {{ color:{_C}; font-size:1rem; }}
/* the two ways to pick strategies: one full-width switch in the brand colours, the chosen half lit */
[class*="st-key-pbswitch"] {{ background:rgba(10,14,23,.55); border:1px solid {_BD}; border-radius:16px; padding:5px; }}
[class*="st-key-pbswitch"] [data-testid="stHorizontalBlock"] {{ gap:5px !important; flex-wrap:nowrap !important; }}
[class*="st-key-pbswitch"] [data-testid="stColumn"] {{ min-width:0 !important; }}
[class*="st-key-pbmode_"] {{ position:relative; }}
[class*="st-key-pbmode_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-pbmode_"] [class*="st-key-pb_mode_"] {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; width:auto !important; }}
[class*="st-key-pbmode_"] [class*="st-key-pb_mode_"] .stButton, [class*="st-key-pbmode_"] [class*="st-key-pb_mode_"] button
  {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
.pbmode {{ display:flex; align-items:center; gap:10px; min-height:58px; box-sizing:border-box; border-radius:12px; padding:9px 14px;
  color:#AEB7C6; transition:background .18s, color .18s, box-shadow .18s; }}
[class*="st-key-pbmode_"]:hover .pbmode:not(.on) {{ background:rgba(61,123,255,.10); color:#fff; }}
.pbmode.on {{ background:linear-gradient(100deg,{_A},{_V} 70%,#6D5CF6); color:#fff; box-shadow:0 10px 26px rgba(61,123,255,.30), inset 0 1px 0 rgba(255,255,255,.18); }}
.pbmode .i .ms {{ font-size:1.2rem; color:{_C}; background:rgba(34,211,238,.12); border-radius:10px; padding:6px; }}
.pbmode.on .i .ms {{ color:#fff; background:rgba(255,255,255,.18); }}
.pbmode .nm {{ font-weight:800; font-size:.95rem; line-height:1.25; }}
.pbmode .ct {{ margin-inline-start:auto; font-size:.72rem; font-weight:800; min-width:26px; height:22px; padding:0 8px; border-radius:999px;
  display:inline-grid; place-items:center; background:rgba(138,148,167,.16); color:#C9D0DC; }}
.pbmode.on .ct {{ background:rgba(255,255,255,.22); color:#fff; }}
/* a '?' next to every chosen strategy (it opens the strategy's rules), and the "work together" pop-out, last */
[class*="st-key-pbq_row"] {{ flex-wrap:wrap !important; gap:8px !important; }}
[class*="st-key-pbq_row"] button {{ border-radius:999px !important; border:1px solid {_A}55 !important; background:{_A}14 !important;
  min-height:34px !important; padding:3px 14px 3px 10px !important; }}
[class*="st-key-pbq_row"] button:hover {{ border-color:{_A} !important; background:{_A}2A !important; }}
[class*="st-key-pbq_row"] button p {{ font-weight:700 !important; font-size:.84rem !important; color:#DCE6FF !important; }}
[class*="st-key-pbq_row"] button [data-testid="stIconMaterial"] {{ color:{_C} !important; }}
[class*="st-key-pbq_together"] [data-testid="stPopover"], [class*="st-key-pbq_together"] [data-testid="stPopover"] > div,
[class*="st-key-pbq_together"] button {{ width:100% !important; }}
[class*="st-key-pbq_together"] button {{ justify-content:flex-start !important; min-height:44px !important; border-radius:12px !important;
  border:1px dashed {_A}88 !important; background:rgba(61,123,255,.07) !important; }}
[class*="st-key-pbq_together"] button:hover {{ border-style:solid !important; background:rgba(61,123,255,.14) !important; }}
[class*="st-key-pbq_together"] button p {{ font-weight:700 !important; color:#DCE6FF !important; }}
[class*="st-key-pbq_together"] button [data-testid="stIconMaterial"] {{ color:{_C} !important; }}
[data-testid="stPopoverBody"] {{ min-width:min(760px, 92vw); }}
/* the big button at the end of the form */
[class*="st-key-pb_create"] button {{ min-height:54px !important; border:0 !important; border-radius:14px !important;
  background:linear-gradient(95deg,{_A} 0%,{_V} 62%,{_C} 130%) !important; box-shadow:0 12px 30px rgba(61,123,255,.35), inset 0 1px 0 rgba(255,255,255,.2);
  transition:transform .15s ease, box-shadow .15s ease, filter .15s ease; }}
[class*="st-key-pb_create"] button:hover {{ transform:translateY(-2px); filter:brightness(1.08); box-shadow:0 16px 36px rgba(61,123,255,.45); }}
[class*="st-key-pb_create"] button p {{ font-size:1.05rem !important; font-weight:800 !important; color:#fff !important; letter-spacing:.01em; }}
[class*="st-key-pb_create"] button [data-testid="stIconMaterial"] {{ color:#fff !important; }}
/* the chosen strategies inside the drop-downs, in the brand colours */
[class*="st-key-pb_ms_"] [data-baseweb="tag"] {{ background:linear-gradient(135deg,rgba(61,123,255,.30),rgba(139,92,246,.30)) !important;
  border:1px solid {_A}66 !important; border-radius:10px !important; }}
[class*="st-key-pb_ms_"] [data-baseweb="tag"] span {{ color:#fff !important; font-weight:700; }}
[class*="st-key-pb_ms_"] [data-baseweb="select"] > div {{ border-radius:12px !important; }}
/* a combined strategy's rules */
.pbrl {{ border:1px solid {_BD}; border-radius:16px; background:rgba(10,14,23,.5); padding:12px 14px 13px; }}
.pbrl + .pbrl {{ margin-top:10px; }}
.pbrl .hd {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
.pbrl .hd .i .ms {{ font-size:1.1rem; color:#fff; background:linear-gradient(135deg,{_A},{_V}); border-radius:10px; padding:6px; }}
.pbrl .nm {{ display:flex; flex-direction:column; line-height:1.3; }}
.pbrl .nm b {{ color:#fff; font-size:.96rem; }}
.pbrl .nm span {{ color:{_MU}; font-size:.74rem; font-weight:600; }}
.pbrl .cs {{ display:flex; flex-wrap:wrap; gap:6px; margin-inline-start:auto; }}
.pbrl .cs .c {{ display:inline-flex; align-items:center; gap:5px; font-size:.72rem; font-weight:700; color:#C9D0DC; background:rgba(138,148,167,.10);
  border:1px solid {_BD}; border-radius:999px; padding:3px 10px; white-space:nowrap; }}
.pbrl .cs .c .ms {{ font-size:.95rem; color:{_C}; }}
.pbrl .gr {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:9px; margin-top:11px; }}
.pbrl .gr:has(> .g:nth-child(4)) {{ grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); }}
.pbrl .g {{ background:rgba(255,255,255,.028); border:1px solid rgba(255,255,255,.055); border-radius:12px; padding:9px 12px 8px; }}
.pbrl .gt {{ display:flex; align-items:center; gap:7px; font-size:.68rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; color:#9CC3FF; }}
.pbrl .gt .k {{ width:18px; height:18px; border-radius:6px; display:grid; place-items:center; background:rgba(61,123,255,.25); color:#fff; font-size:.64rem; }}
.pbrl ul {{ margin:6px 0 0; padding-inline-start:18px; }}
.pbrl li {{ color:#DCE2EC; font-size:.8rem; line-height:1.55; margin:2px 0; }}
.pbrl li::marker {{ color:{_C}; }}

@media (prefers-reduced-motion: reduce) {{ .pbhero *, .pbadd *, .pbfb * {{ animation:none !important; }} }}
@media (max-width: 640px) {{ .pbfb .art {{ width:100%; opacity:.25; }} .pbfb .tx {{ max-width:100%; }} }}
</style>"""
# Arabic: no letter-spacing (it breaks the joined letters) and the accent bars move to the right edge
PAGE_RTL_CSS = """<style>
.pbhero .eb, .pbc .it, .pbmh, .pbt th, .pbfb .eb, .pbfs, .pbmode .ct, .pbrl .gt { letter-spacing:0; }
.pbp::before, .pbid::before { left:auto; right:0; }
.pbp { padding:14px 19px 8px 16px; }
[class*="st-key-pbf_"]::before { background:linear-gradient(270deg,#3D7BFF,#8B5CF6,#22D3EE); }
.pbmode.on { background:linear-gradient(260deg,#3D7BFF,#8B5CF6 70%,#6D5CF6); }
[class*="st-key-pb_create"] button { background:linear-gradient(265deg,#3D7BFF 0%,#8B5CF6 62%,#22D3EE 130%) !important; }
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
                       L(f"{alloc} per trade", f"{alloc} لكل صفقة"), L(f"target {tp}", f"هدف {tp}"), L(f"stop {sl}", f"وقف {sl}")])


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
         '<defs><linearGradient id="pbln" x1="0" x2="1"><stop offset="0" stop-color="#22D3EE" stop-opacity="0"/>'
         '<stop offset=".3" stop-color="#22D3EE"/><stop offset=".72" stop-color="#3D7BFF"/><stop offset="1" stop-color="#A78BFA"/></linearGradient>'
         '<linearGradient id="pbnd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3D7BFF"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient>'
         '<filter id="pbgl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/>'
         '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
         # the brand's "A", large and faint
         '<g transform="translate(366 66) scale(3.5)" opacity=".06"><path d="M17 48 L29.5 15.5 Q32 11 34.5 15.5 L47 48" fill="none" '
         'stroke="#fff" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/></g>']
    rng = np.random.default_rng(11)
    for _ in range(16):
        s.append(f'<circle class="tw" cx="{rng.uniform(20, 510):.0f}" cy="{rng.uniform(8, 240):.0f}" r="{rng.uniform(.6, 1.5):.1f}" '
                 f'fill="#9CC3FF" style="animation-delay:-{rng.uniform(0, 4):.1f}s"/>')
    s.append(f'<path d="{path}" fill="none" stroke="#22D3EE" stroke-opacity=".10" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>')
    s.append(f'<path class="ln" d="{path}" fill="none" stroke="url(#pbln)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" '
             f'filter="url(#pbgl)" style="stroke-dasharray:{length:.0f};--len:{length:.0f}"/>')
    s.append('<path d="M461 35 L476.5 35.6 L475.9 51" fill="none" stroke="#A78BFA" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
    s.append(f'<circle class="mv" r="4.5" fill="#22D3EE" filter="url(#pbgl)" style="offset-path:path(\'{path}\')"/>')
    for i, (x, y) in enumerate(_SLOTS):
        rank = PB.MAX_BOTS - i
        if rank > len(ranked_sims):
            s.append(f'<g opacity=".8"><circle cx="{x}" cy="{y}" r="14" fill="#0A0E17" fill-opacity=".55" stroke="#8A94A7" stroke-width="1.6" '
                     f'stroke-dasharray="3 4"/><path d="M{x - 5} {y} H{x + 5} M{x} {y - 5} V{y + 5}" stroke="#8A94A7" stroke-width="2" '
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
                 f'<circle cx="{x}" cy="{y}" r="15" fill="url(#pbnd)" stroke="#0A0E17" stroke-width="2"/>'
                 f'<text x="{x}" y="{y + 4.5}" text-anchor="middle" font-size="12.5" font-weight="800" fill="#fff" font-family="{T.FONT}">{rank}</text>'
                 f'<text x="{x}" y="{y - 36}" text-anchor="middle" font-size="13" font-weight="800" fill="{ring}" font-family="{T.FONT}">{label}</text>'
                 f'<text x="{x}" y="{y - 22}" text-anchor="middle" font-size="10.5" fill="#C7CFDD" font-family="{T.FONT}">{T.esc(name)}</text></g>')
    return "".join(s) + "</svg>"


def hero_html(sims, n_bots):
    rk = ranked(sims)
    live = [s for s in sims if s["ok"] and not s["waiting"]]
    chips = [f'<span class="chip">{T.icon("smart_toy")}<b>{n_bots}/{PB.MAX_BOTS}</b> {L("bots", "بوتات")}</span>']
    if live:
        cap = sum(s["bot"]["capital"] for s in live)
        bal = sum(s["final"] for s in live)
        n_open = sum(s["n_open"] for s in live)
        n_orders = sum(len(s["next_buys"]) + len(s["next_sells"]) for s in live)
        chips.append(f'<span class="chip">{T.icon("account_balance_wallet")}{L("Total balance", "إجمالي الرصيد")} <b>{T.money(bal)}</b>'
                     f'{T.pill((bal / cap - 1) * 100 if cap else 0.0)}</span>')
        chips.append(f'<span class="chip">{T.icon("swap_vert")}{L("Open trades", "صفقات مفتوحة")} <b>{n_open}</b></span>')
        if n_orders:
            chips.append(f'<span class="chip">{T.icon("bolt")}{L("Orders at next open", "أوامر الافتتاح القادم")} <b>{n_orders}</b></span>')
        best = rk[0]
        chips.append(f'<span class="chip">{T.icon("emoji_events")}<b>{T.esc(best["bot"]["name"])}</b>{T.pill(best["ret"])}</span>')
    else:
        chips.append(f'<span class="chip">{T.icon("payments")}{L("Virtual money", "أموال وهمية")}</span>')
        chips.append(f'<span class="chip">{T.icon("candlestick_chart")}{L("Real prices", "أسعار حقيقية")}</span>')
    title = L("Paper <b>Bots</b>", "البوتات <b>الافتراضية</b>")
    tag = L(f"Up to {PB.MAX_BOTS} bots trade with virtual money on real prices, forward from the day they start: a company, a sector, "
            "an industry or all companies, with one or more strategies or ready-made combined strategies, buying stocks, options or both.",
            f"حتى {PB.MAX_BOTS} بوتات تتداول بأموال وهمية على أسعار حقيقية من يوم تشغيلها وللأمام: شركة أو قطاع أو صناعة أو كل الشركات، "
            "باستراتيجية وحدة أو أكثر أو باستراتيجيات مركّبة جاهزة، وتشتري أسهم أو أوبشن أو الاثنين.")
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
        return mk(L("Unavailable", "غير متاح"), "neu", "error")
    if sim["waiting"]:
        return mk(L("Starts next session", "يبدأ الجلسة القادمة"), "neu", "schedule")
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
    """The first day the bot trades: its start date (the Opening Range Breakout: the first day it has 5-minute prices for)."""
    if sim.get("intraday") and sim.get("start") is not None:
        return pd.Timestamp(sim["start"]).strftime("%Y-%m-%d")
    return sim["bot"]["start_date"]


def bot_card(rank, sim, logo, selected=False):
    b = sim["bot"]
    ic, en, ar_ = card_chip(b)
    medal = T.icon("emoji_events") if rank == 1 else ""
    top = f'<div class="top"><span class="it">{T.icon(ic)}{T.esc(L(en, ar_))}</span><span class="rk r{rank}">{medal}#{rank}</span></div>'
    badges = f'<div class="bdg">{cbadge(how_label(b, short=True), "vio", "smart_toy")}{status_badge(sim, cbadge)}</div>'
    if sim["ok"] and not sim["waiting"]:
        ret, m = sim["ret"], sim["metrics"]
        spx = "" if sim["bench_ret"] is None else f'<div class="muted" style="font-size:.7rem;margin-top:4px;direction:ltr">S&amp;P 500 {sim["bench_ret"]:+.2f}%</div>'
        win = iso(f"{m['Win Rate %']:.0f}%")
        trades = L(f'{m["Trades"]} trades', f'{m["Trades"]} صفقة') + (f' · {L("win", "نجاح")} {win}' if m["Trades"] else "")
        watch = "" if b["kind"] == "company" else " · " + L(f'{sim["n_symbols"]} stocks', f'{sim["n_symbols"]} سهم')
        body = (f'<div class="spk">{_spark_area(sim["equity"], b["capital"], b["id"])}</div>'
                f'<div class="row"><div><div class="muted" style="font-size:.72rem">{L("Balance", "الرصيد")}</div>'
                f'<div style="font-weight:800;font-size:1.1rem;direction:ltr">{T.money(sim["final"])}</div></div>'
                f'<div class="r">{T.pbox(f"{ret:+.2f}%", ret)}{spx}</div></div>'
                f'<div class="pbft">{trades}{watch} · {L("since", "منذ")} {iso(since_of(sim))}</div>')
    elif sim["ok"]:
        body = (f'<div class="pbft">{L("Starts with the first US session from", "يبدأ مع أول جلسة أمريكية من")} '
                f'{iso(b["start_date"])} · {iso(T.money(b["capital"]))}</div>')
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
            f'<line x1="0" y1="{base:.1f}" x2="{w:.0f}" y2="{base:.1f}" stroke="#8A94A7" stroke-width="1" stroke-dasharray="3 4" '
            f'vector-effect="non-scaling-stroke" opacity=".6"/>'
            f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>')


# the site's logo tile (blue-violet, rounded) with a white plus and the cyan trend arrow; a dashed orbit turns around it
PLUS_SVG = ('<svg viewBox="0 0 92 92" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            '<defs><linearGradient id="pbaddg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3D7BFF"/>'
            '<stop offset="1" stop-color="#8B5CF6"/></linearGradient>'
            '<filter id="pbaddf" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="5"/></filter></defs>'
            '<g class="orbit"><circle cx="46" cy="46" r="43" fill="none" stroke="#22D3EE" stroke-opacity=".45" stroke-width="1.4" stroke-dasharray="2 7"/>'
            '<circle cx="46" cy="3" r="3.2" fill="#22D3EE"/><circle cx="89" cy="46" r="2" fill="#A78BFA"/></g>'
            '<g class="tile"><rect x="16" y="20" width="60" height="60" rx="17" fill="#3D7BFF" opacity=".45" filter="url(#pbaddf)"/>'
            '<rect x="16" y="16" width="60" height="60" rx="17" fill="url(#pbaddg)"/>'
            '<path d="M22 30 Q22 22 30 22 H62 Q70 22 70 30" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="2" stroke-linecap="round"/>'
            '<g class="cross"><path d="M46 32 V60 M32 46 H60" stroke="#fff" stroke-width="6.5" stroke-linecap="round"/></g>'
            '<path class="spark" d="M51 67 L57 62 L61 64 L69 56" fill="none" stroke="#22D3EE" stroke-width="3.2" stroke-linecap="round" '
            'stroke-linejoin="round" style="stroke-dasharray:40"/>'
            '<path d="M65 55.6 L69.4 55.9 L69.1 60.3" fill="none" stroke="#22D3EE" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>'
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
    ui.sec("stacked_line_chart", "Return since start", "العائد منذ البداية")
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
    return {"key": str(b["id"]), "multi": False, "group": b["kind"] != "company", "n_bots": 1, "cap": float(b["capital"]),
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
    return {"key": "all", "name": "", "scope": L(f"all {len(live)} selected bots", f"كل البوتات المحددة ({len(live)})"), "multi": True, "group": True, "n_bots": len(live), "cap": cap, "final": final,
            "ret": (final / cap - 1) * 100, "bench_ret": float((bench.iloc[-1] / cap - 1) * 100), "base_ret": None,
            "equity": eq, "bench": bench, "bench_name": "S&P 500 (SPY)", "npos": npos,
            "trades": trades, "cash": float(sum(v["cash"] for v in views)),
            "sessions": max(s["sessions"] for s in live), "since": min(s["bot"]["start_date"] for s in live),
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
        T.kpi("calendar_month", L("Running", "مدة التشغيل"), f"{v['sessions']:,}", L("sessions since ", "جلسة منذ ") + iso(v["since"]), None),
    ]
    return '<div class="pbk">' + "".join(tiles) + "</div>"


def _contrib(closed, by, cap):
    """Each group's share of the return, % of the starting capital (so the bars add up to the closed-trade return)."""
    g = closed.groupby(by).agg(pnl=("P&L $", "sum"), n=("P&L $", "size"), wins=("P&L $", lambda x: int((x > 0).sum())))
    g["pct"] = g["pnl"].astype(float) / cap * 100
    return g


def _bars_from(g, labels, title, key, container):
    hover = [f"{sm(r.pnl)} · " + L(f"{int(r.n)} trades · win {r.wins / r.n * 100:.0f}%", f"{int(r.n)} صفقة · نجاح {r.wins / r.n * 100:.0f}%")
             for r in g.itertuples()]
    ui.chart(charts.pct_bars(labels, list(g["pct"].values), title, max(250, 30 * len(g) + 80), hover), key=key, container=container)


def what_worked(v):
    tr = v["trades"]
    closed = tr[tr["Exit Reason"] != "Open"]
    ui.html(f'<div class="pbsub">{T.icon("pie_chart")}{L("What worked", "ماذا نجح")}'
            f'<span class="muted">· {L("closed trades, share of the return in % of the starting capital", "الصفقات المغلقة، نصيبها من العائد (% من رأس المال)")}</span></div>')
    if closed.empty:
        st.caption(L("This part fills in after the first closed trade.", "هذا الجزء يمتلئ بعد أول صفقة مغلقة."))
        return
    c1, c2 = st.columns(2, gap="medium")
    if v["group"]:
        g = _contrib(closed, "Symbol", v["cap"])
        g = g.loc[list(dict.fromkeys(list(g["pct"].nlargest(6).index) + list(g["pct"].nsmallest(6).index)))]
        _bars_from(g, list(g.index), L("By stock, best and worst", "حسب السهم، الأفضل والأسوأ"), f"pb_ww_{v['key']}", c1)
    else:
        g = _contrib(closed, "Exit Reason", v["cap"])
        _bars_from(g, [L(x, EXIT_AR.get(x, x)) for x in g.index], L("By exit reason", "حسب سبب الخروج"), f"pb_ww_{v['key']}", c1)
    g = _contrib(closed, "Strategy", v["cap"])
    _bars_from(g, [strat_short(k) for k in g.index], L("By strategy", "حسب الاستراتيجية"), f"pb_wws_{v['key']}", c2)
    g = _contrib(closed, "Type", v["cap"])
    if len(g) > 1:
        _bars_from(g, [L(*TYPE_NAME.get(k, (k, k))) for k in g.index], L("By type", "حسب النوع"), f"pb_wwt_{v['key']}", c2)


def dashboard(v):
    if v["multi"]:
        ui.sec("space_dashboard", "Portfolio dashboard", "لوحة أداء المحفظة")
        chips = "".join(f'<span class="c">{T.icon("smart_toy")}{T.esc(s["bot"]["name"])} {T.pill(s["ret"])}</span>' for s in v["sims"])
        ui.html(f'<div class="pbsel">{chips}</div>')
    else:
        ui.sec("space_dashboard", "Dashboard", "لوحة الأداء")
    ui.html(kpi_row(v))
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
    head = (f'<div class="hd"><div class="tt">{T.icon("work")}{T.esc(_title(v, "Open positions", "المراكز المفتوحة"))}<span class="live"></span></div>'
            f'<div class="sum">{chips}</div></div>')
    if not n:
        ui.html(f'<div class="pbp">{head}<div class="pbempty">{T.icon("hourglass_empty")}'
                f'{L("No open positions right now. The bot is waiting for a signal.", "لا توجد مراكز مفتوحة حالياً. البوت ينتظر إشارة.")}</div></div>')
        return
    rows = []
    for i in op.assign(_v=val).sort_values("_v", ascending=False).index:
        r = op.loc[i]
        opt = r["Type"] in ("Call", "Put")
        value = float(val.loc[i])
        w = value / v["final"] * 100 if v["final"] > 0 else 0.0
        qty = L(f'{int(r["Shares"])} contracts', f'{int(r["Shares"])} عقد') if opt else L(f'{r["Shares"]:,.2f} sh', f'{r["Shares"]:,.2f} سهم')
        tip = f' title="{L("stock", "السهم")} {_fp(r["Stock Entry"])} → {_fp(r["Stock Exit"])}"' if opt else ""
        who = f'<td><span class="m">{T.esc(r["Bot"])}</span></td>' if v["multi"] else ""
        intra = _intra(r)
        rows.append(f'<tr><td>{_asset(r, lg)}</td><td>{type_badge(r["Type"])}</td>{who}<td>{T.esc(strat_short(r["Strategy"]))}</td>'
                    f'<td>{_when(r["Entry Date"], intra)} <span class="m">· {_held(int(r["Bars"]), intra)}</span></td>'
                    f'<td{tip}>{_fp(r["Entry"])} → <b>{_fp(r["Exit"])}</b> {_chg(r["Entry"], r["Exit"])}</td>'
                    f'<td>{qty} <span class="m">· {T.money(value)} · {w:.1f}%</span></td><td>{_plan(r)}</td>{_pnl_cell(r)}</tr>')
    heads = ([L("Asset", "الأصل"), L("Type", "النوع")] + ([L("Bot", "البوت")] if v["multi"] else [])
             + [L("Strategy", "الاستراتيجية"), L("Opened", "الفتح"), L("Entry → now", "الدخول ← الآن"), L("Size", "الحجم"),
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
        tip = f' title="{L("stock", "السهم")} {_fp(r["Stock Entry"])} → {_fp(r["Stock Exit"])}"' if opt else ""
        who = f'<td><span class="m">{T.esc(r["Bot"])}</span></td>' if v["multi"] else ""
        intra = _intra(r)
        span = (f'{_when(r["Entry Date"], True)} → {pd.Timestamp(r["Exit Date"]):%H:%M}' if intra
                else f'{_when(r["Entry Date"])} → {_when(r["Exit Date"])}')
        rows.append(f'<tr><td>{_asset(r, lg)}</td><td>{type_badge(r["Type"])}</td>{who}<td>{T.esc(strat_short(r["Strategy"]))}</td>'
                    f'<td>{span} <span class="m">· {_held(int(r["Bars"]), intra)}</span></td>'
                    f'<td{tip}>{_fp(r["Entry"])} → <b>{_fp(r["Exit"])}</b></td><td>{exit_badge(r["Exit Reason"])}</td>{_pnl_cell(r)}</tr>')
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


# the colours of the old monthly heatmap: pale for small months, deeper green / red for big ones
_HEAT_STOPS = [(0.0, "#F1AEB5"), (0.35, T.NEG_BG), (0.5, "#E2E8F0"), (0.65, T.POS_BG), (1.0, "#A3CFBB")]


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
    for s in "pn" for k in range(1, 5)) + '[class*="st-key-pbmo_z"] button { background:#E2E8F0 !important; }</style>'


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
        N.update({"Entry": L("Premium in", "سعر العقد دخول"), "Exit": L("Premium out / now", "سعر العقد خروج / الحالي"),
                  "Shares": L("Contracts", "العقود")})
    elif opts:
        N.update({"Entry": L("Entry (share / premium)", "الدخول (سهم / عقد)"), "Exit": L("Exit / now (share / premium)", "الخروج / الحالي (سهم / عقد)"),
                  "Shares": L("Shares / contracts", "أسهم / عقود")})
    show = show.rename(columns=N)
    st.dataframe(show.iloc[::-1].style.map(T.color_style, subset=[N["P&L %"], N["P&L $"]]).format(
        {N["Entry"]: "{:,.2f}", N["Exit"]: "{:,.2f}", N["Shares"]: "{:,.0f}" if only_opt else "{:,.2f}", N["P&L $"]: "{:+,.2f}",
         N["P&L %"]: "{:+.2f}%", **({N["Stock Entry"]: "{:,.2f}", N["Stock Exit"]: "{:,.2f}"} if opts else {})}),
        hide_index=True, height=min(460, 38 + 35 * len(show)))
    st.download_button(L("Export CSV", "تصدير CSV"), show.to_csv(index=False).encode("utf-8-sig"), file_name,
                       "text/csv", icon=":material/download:", key=f"pb_csv_{v['key']}")


# =====================================================================
# one bot in detail · several bots together
# =====================================================================
def _order_txt(item):
    sym, label, kind = item
    extra = "" if kind == "Stock" else f" {kind.upper()}"
    return f"{sym} ({strat_short(label)}{extra})"


def bot_header(sim):
    b = sim["bot"]
    names = list(b["strategies"])
    ins = instrument(b)
    uni = universe_label(b, sim.get("n_symbols") if sim["ok"] else None)
    badges = T.badge(uni, "gold", KIND_ICON[b["kind"]]) + T.badge(how_label(b), "vio", "smart_toy")
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
    if ins != "stock":
        badges += T.badge(_options_txt(b["options"]), "neu", "receipt_long")
    badges += (T.badge(L("Start ", "البداية ") + iso(since_of(sim) if sim["ok"] else b["start_date"]), "neu", "event")
               + T.badge(L("Capital ", "رأس المال ") + iso(T.money(b["capital"])), "neu", "account_balance_wallet"))
    if ins != "options":
        badges += T.badge(L("Fee ", "العمولة ") + iso(f"{b['fee']:g}%") + L(" / side", " لكل جهة"), "neu", "receipt")
    logo = data.logos([b["value"]]).get(b["value"]) if b["kind"] == "company" else None
    ui.html(f'<div class="card pbid">{head_html(b, logo)}<div class="bdgs">{badges}</div></div>')
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
        return
    v = single_view(sim, in_tab)
    lg = view_logos(v)
    parts = ([] if in_tab else [("dash", dashboard, (v,))]) + [
        ("open", open_panel, (v, lg)), ("recent", recent_panel, (v, lg)), ("equity", balance_chart, (v,)),
        ("price", orb_chart_section if sim.get("intraday") else price_chart_section, (sim,)), ("pnl", pnl_charts, (v,)),
        ("months", month_grid, (v,)),
        ("all", all_trades, (v, f"paper_bot_{b['id']}.csv"))]
    for name, fn, args in parts:
        with section(name, key):
            ui.safe(fn, *args)


def _details_head(sim):
    b = sim["bot"]
    bot_header(sim)
    if not sim["ok"]:
        uni = universe_label(b)
        if sim["why"] == "strategy":
            st.warning(L("This bot's strategy or group no longer exists on the site. Edit it or delete it.",
                         "استراتيجية هذا البوت أو مجموعته لم تعد موجودة في الموقع. عدّله أو احذفه."), icon=":material/error:")
        else:
            st.warning(L(f"No price data for {uni} right now. Check the symbol, or try again in a minute.",
                         f"لا توجد بيانات أسعار لـ {uni} حالياً. تأكد من الرمز، أو حاول بعد دقيقة."), icon=":material/error:")
        return
    if sim["waiting"]:
        if sim.get("intraday"):
            st.info(L(f"The bot starts with the first US session on or after {b['start_date']} and trades during the session on 5-minute candles.",
                      f"البوت يبدأ مع أول جلسة أمريكية من تاريخ {b['start_date']} ويتداول أثناء الجلسة على شموع 5 دقائق."),
                    icon=":material/schedule:")
            return
        st.info(L(f"The bot starts with the first US session on or after {b['start_date']}. After that session closes it checks its "
                  "strategies, and any order is filled at the next open.",
                  f"البوت يبدأ مع أول جلسة أمريكية من تاريخ {b['start_date']}. بعد إغلاق الجلسة يفحص الاستراتيجيات، وأي أمر يتنفذ عند الافتتاح التالي."),
                icon=":material/schedule:")
        return
    if sim.get("intraday"):
        first = iso(since_of(sim))
        st.caption(L(f"Yahoo keeps 5-minute prices for 60 days, so this bot shows its trades from {first} (the first 5 sessions only build the "
                     "relative volume). Every trade opens and closes on the same day.",
                     f"ياهو يحتفظ بأسعار الـ 5 دقائق لمدة 60 يوم، فهذا البوت يعرض صفقاته من {first} (أول 5 جلسات تبني الحجم النسبي فقط). "
                     "كل صفقة تنفتح وتتقفل في نفس اليوم."))
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


FORM_KEYS = list(DEFAULTS) + ["pb_min", "pb_pbmin", "pb_start", "pb_edit_id"]
FORM_PREFIXES = ("pb_strats_", "pb_pp_", "pb_ms_")


def _reset_form():
    for k in [k for k in list(ss.keys()) if k in FORM_KEYS or str(k).startswith(FORM_PREFIXES)]:
        del ss[k]


def _init_form():
    for k, v in DEFAULTS.items():
        if k not in ss:
            ss[k] = list(v) if isinstance(v, list) else v
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


def _clip(v, lo, hi, cast=float):
    return cast(min(max(cast(v), lo), hi))


def _load_form(bot):
    """Fill the form with a bot's settings (pencil on its card)."""
    _reset_form()
    k, v = bot["kind"], bot["value"]
    books = [s for s in PBK.PLAYBOOKS if s in bot["strategies"]]
    ss.update({"pb_edit_id": bot["id"], "pb_name": bot["name"], "pb_capital": _clip(round(bot["capital"]), 100, 100_000_000, int),
               "pb_kind": k, "pb_mode": "combo" if books else "single",
               # the bot's own way keeps exactly its strategies (none when they no longer exist); the other way gets its default
               "pb_store": list(DEFAULTS["pb_store"]) if books else [s for s in engine.STRATEGIES if s in bot["strategies"]],
               "pb_store_pb": books or list(DEFAULTS["pb_store_pb"]), "pb_combine": bot["combine"]["mode"],
               "pb_maxpos": _clip(bot["max_pos"] if k != "company" else DEFAULTS["pb_maxpos"], 1, PB.MAX_POS_LIMIT, int),
               "pb_instr": instrument(bot), "pb_fee": _clip(bot["fee"], 0.0, 1.0), "pb_stop": _clip(bot["stop_pct"], 0.0, 50.0),
               "pb_atr": _clip(bot["atr_mult"], 0.0, 10.0), "pb_tp": _clip(bot["tp_pct"], 0.0, 500.0),
               "pb_trail": _clip(bot["trail_pct"], 0.0, 50.0), "pb_start": pd.Timestamp(bot["start_date"]).date()})
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
             "the option's take profit or stop loss (checked at the close), or 5 days before expiry. Option prices are estimated with the "
             "Black-Scholes model from each stock's own volatility, plus $0.65 per contract, so real prices will differ.",
             "عقود Call تنشرى مع إشارات الشراء، وعقود Put مع إشارات البيع. كل عقد يتقفل بالإشارة المعاكسة من نفس القاعدة، أو عند هدف الربح أو "
             "وقف الخسارة للعقد (يُفحص عند الإغلاق)، أو قبل الانتهاء بـ 5 أيام. أسعار العقود تقديرية بنموذج بلاك-شولز من تذبذب السهم نفسه، "
             "مع 0.65$ لكل عقد، فالأسعار الحقيقية تختلف.")


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
            '<defs><linearGradient id="pbfl" x1="0" x2="1"><stop offset="0" stop-color="#22D3EE" stop-opacity="0"/>'
            '<stop offset=".35" stop-color="#22D3EE"/><stop offset=".75" stop-color="#3D7BFF"/><stop offset="1" stop-color="#A78BFA"/></linearGradient>'
            '<filter id="pbfg" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
            '<g transform="translate(150 14) scale(1.9)" opacity=".07"><path d="M17 48 L29.5 15.5 Q32 11 34.5 15.5 L47 48" fill="none" '
            'stroke="#fff" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/></g>'
            '<path d="M12 104 L58 80 L96 88 L138 58 L176 64 L236 22" fill="none" stroke="#22D3EE" stroke-opacity=".12" stroke-width="10" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
            '<path class="ln" d="M12 104 L58 80 L96 88 L138 58 L176 64 L236 22" fill="none" stroke="url(#pbfl)" stroke-width="3" '
            'stroke-linecap="round" stroke-linejoin="round" filter="url(#pbfg)" style="stroke-dasharray:290;--len:290"/>'
            '<path d="M222 21 L237 21.6 L236.4 36" fill="none" stroke="#A78BFA" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r="5" fill="#0A0E17" stroke="{c}" stroke-width="2.4"/>'
                      for x, y, c in ((58, 80, "#22D3EE"), (96, 88, "#3D7BFF"), (138, 58, "#3D7BFF"), (176, 64, "#8B5CF6")))
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
    return [("—", "—"), ("—", "—")]


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
            f'<div class="nm"><b>{T.esc(strat_name(name))}</b><span>{T.esc(L("Daily candles · Strategy Lab", "شموع يومية · مختبر الاستراتيجيات"))}</span></div>'
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
        with st.popover(L("How they work together", "كيف تشتغل مع بعض") + " · " + together_label(way, n), icon=":material/join_inner:"):
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


def _picker(way, kind):
    """One way of picking strategies: its drop-down, select all / clear, a '?' next to each chosen strategy, and (last) how they
    work together. Returns (strategies, mode, need, window)."""
    classic = way == "single"
    names = list(engine.STRATEGIES) if classic else list(PBK.PLAYBOOKS)
    store, wkey = ("pb_store", "pb_ms_single") if classic else ("pb_store_pb", "pb_ms_combo")
    ss[wkey] = [s for s in dict.fromkeys(ss.get(store, [])) if s in names]       # in the order they were picked
    st.multiselect(L("Strategies", "الاستراتيجيات") if classic else L("Combined strategies", "الاستراتيجيات المركّبة"), names, key=wkey,
                   format_func=strat_name, on_change=_ms_changed, args=(wkey, store),
                   placeholder=L("Choose one or more strategies", "اختر استراتيجية أو أكثر"))
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


def bot_form(mode, bot=None):
    """The add / edit form (inside a dialog): a banner, then six numbered cards with space between them."""
    _init_form()
    ui.html(form_banner(mode, bot))

    # 1) basics
    with st.container(key="pbf_1"):
        form_head(1, "badge", "Basics", "الأساسيات", "A name and the virtual money it starts with", "الاسم والمبلغ الوهمي اللي يبدأ فيه")
        a, c = st.columns([2, 1])
        a.text_input(L("Bot name (optional)", "اسم البوت (اختياري)"), key="pb_name", max_chars=40,
                     placeholder=L("e.g. Tech momentum", "مثال: بوت التقنية"))
        c.number_input(L("Virtual capital ($)", "رأس المال الوهمي ($)"), 100, 100_000_000, step=10_000, key="pb_capital")

    # 2) what it trades
    with st.container(key="pbf_2"):
        form_head(2, "public", "What does the bot trade?", "وش يتداول البوت؟", "One company or a whole group of stocks",
                  "شركة وحدة أو مجموعة أسهم كاملة")
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

    # 3) strategies: two ways, each a drop-down
    with st.container(key="pbf_3"):
        form_head(3, "filter_alt", "Stock filter strategies", "فلتر استراتيجيات الأسهم", "Press ? next to a strategy to see how it works",
                  "اضغط ? جنب الاستراتيجية عشان تشوف طريقتها")
        way = ss["pb_mode"] if ss.get("pb_mode") in MODES else "single"
        with st.container(key="pbswitch"):
            t1, t2 = st.columns(2, gap="small")
            for col, m in ((t1, "single"), (t2, "combo")):
                with col:
                    with st.container(key=f"pbmode_{m}"):
                        ui.html(mode_tile(m, m == way))
                        st.button(L(*MODES[m][1:3]), key=f"pb_mode_{m}", on_click=_set_mode, args=(m,), width="stretch")
        strats, mode_, need, win = _picker(way, kind)
    combined = way == "combo"
    orb = combined and PBK.ORB in strats

    # 4) what it buys and how much per trade
    with st.container(key="pbf_4"):
        form_head(4, "shopping_bag", "What does the bot buy?", "وش يشتري البوت؟", "And how much goes into each trade",
                  "وكم يحط في كل صفقة")
        if combined:
            instr = "stock"
            chips = T.badge(L("Stocks", "أسهم"), "acc", "show_chart") + (T.badge(L("Long and short", "شراء وبيع مكشوف"), "vio", "swap_vert")
                                                                         if orb else T.badge(L("Long", "شراء"), "vio", "trending_up"))
            ui.html(f'<div>{chips}</div>')
        else:
            ui.valid("pb_instr", list(PB.INSTRUMENTS))
            instr = st.segmented_control(L("What does the bot buy?", "وش يشتري البوت؟"), list(PB.INSTRUMENTS), key="pb_instr",
                                         format_func=lambda k: L(*INSTR_LABEL[k]), label_visibility="collapsed") or "stock"
            st.caption(instrument_caption(instr))
        if kind != "company":
            m1, m2 = st.columns([1, 2], vertical_alignment="bottom")
            maxpos = m1.number_input(L("Max open trades", "أقصى عدد صفقات مفتوحة"), 1, PB.MAX_POS_LIMIT, step=1, key="pb_maxpos")
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

    # 5) exits and costs
    with st.container(key="pbf_5"):
        form_head(5, "shield", "Exits and costs", "الخروج والتكاليف")
        if combined:
            r = st.columns(3)
            r[0].number_input(L("Fee % / side", "العمولة %"), 0.0, 1.0, step=0.01, key="pb_fee")
            if not orb:
                r[1].number_input(L("Trailing stop % (optional)", "الوقف المتحرك % (اختياري)"), 0.0, 50.0, step=0.5,
                                  help=L("0 = off", "0 = إيقاف"), key="pb_trail")
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
                r[4].number_input(L("Trailing stop %", "الوقف المتحرك %"), 0.0, 50.0, step=0.5, help=off, key="pb_trail")
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
                o5.number_input(L("Take profit on the option %", "هدف ربح العقد %"), 5.0, 2000.0, step=5.0, key="pb_otp")
                o6.number_input(L("Stop loss on the option %", "وقف خسارة العقد %"), 5.0, 95.0, step=5.0, key="pb_osl")
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
                   L("Today = the bot trades live from now on. An earlier date replays the past first, like the Strategy Lab, then carries on live.",
                     "اليوم = البوت يتداول مباشرة من الحين وللأمام. التاريخ الأقدم يعيد تشغيل الفترة الماضية أولاً مثل مختبر الاستراتيجيات، ثم يكمل مباشرة."))
        label = L("Start the bot", "شغّل البوت") if mode == "add" else L("Save changes", "حفظ التعديلات")
        pressed = st.button(label, type="primary", icon=":material/play_arrow:" if mode == "add" else ":material/save:", key="pb_create",
                            width="stretch")
    if not pressed:
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
            if "fast" in p and "slow" in p and p["fast"] >= p["slow"]:
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
    name = str(ss.get("pb_name") or "").strip() or _default_name(kind, value, strats, need if combo else None, instr)
    options = {"type": ss["pb_otype"], "dte": ss["pb_dte"], "strike": ss["pb_strike"], "alloc": ss["pb_oalloc"], "tp": ss["pb_otp"],
               "sl": ss["pb_osl"]} if instr != "stock" else None
    if combined:
        risk = (0.0, 0.0, 0.0, 0.0 if orb else ss["pb_trail"])
    else:
        risk = (0.0, 0.0, 0.0, 0.0) if instr == "options" else (ss["pb_stop"], ss["pb_atr"], ss["pb_tp"], ss["pb_trail"])
    rec = PB.make_record(name, kind, value, params, ss.get("pb_maxpos", DEFAULTS["pb_maxpos"]), ss["pb_capital"], ss["pb_fee"], *risk,
                         pd.Timestamp(start).strftime("%Y-%m-%d"),
                         ({"mode": "combo", "min": int(need), **({"window": int(win)} if combined else {})} if combo else None),
                         instrument=instr, options=options)
    try:
        if mode == "add":
            PB.create_bot(rec)
        else:
            PB.update_bot(bot["id"], rec)
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


def open_dialog(op, bots):
    mode, bid = op
    bot = next((b for b in bots if b["id"] == bid), None)
    if mode == "delete" and bot:
        st.dialog(L("Delete bot", "حذف البوت"))(_delete_body)(bot)
    elif mode == "edit" and bot:
        st.dialog(L("Edit bot", "تعديل البوت"), width="large")(_bot_dialog_body)("edit", bot, len(bots))
    elif mode == "add":
        st.dialog(L("Add a bot", "أضف بوت"), width="large")(_bot_dialog_body)("add", None, len(bots))


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
    ui.html(hero_html(sims, len(bots)))
    storage_notice(err)
    sel = ui.safe(leaderboard, sims, len(bots), err is None and len(bots) < PB.MAX_BOTS) or []

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
        chosen = [s for s in ranked(sims) if s["bot"]["id"] in sel]
        if not chosen:
            ui.html(f'<div class="card" style="line-height:1.9;margin-top:14px">{T.ico("ads_click", "acc")} ' + L(
                "Click a bot's card to see its dashboard. Select one, several, or press <b>Select all</b>.",
                "اضغط على كرت البوت عشان تشوف لوحة أدائه. تقدر تحدد واحد أو أكثر، أو تضغط <b>تحديد الكل</b>.") + "</div>")
        elif len(chosen) == 1:
            ui.safe(details, chosen[0])
        else:
            ui.safe(portfolio, chosen, spy, sims)

    st.caption(L("Virtual trading on real daily prices (dividend-adjusted, may be delayed); the Opening Range Breakout uses 5-minute prices from "
                 "the last 60 days. Results are recalculated from each bot's start date whenever the page opens. No real money and no broker are "
                 "involved. Past results do not guarantee future returns.",
                 "تداول وهمي على أسعار يومية حقيقية (معدّلة بالتوزيعات وقد تكون متأخرة)، واختراق نطاق الافتتاح يستخدم أسعار 5 دقائق لآخر 60 يوم. "
                 "النتائج تُحسب من جديد من تاريخ بداية كل بوت كل ما تفتح الصفحة. لا توجد أموال حقيقية ولا وسيط. النتائج السابقة لا تضمن المستقبل."))
    ui.foot()

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.7"
