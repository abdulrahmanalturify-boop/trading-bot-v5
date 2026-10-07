"""
p_portfolio.py - Paper Portfolio (top bar): Dashboard, Trade, Analytics, Orders & History.

A margin account traded by hand with virtual money on real prices (portfolio.py does the bookkeeping): buy, sell, SELL
SHORT and cover, with market / limit / stop / trailing-stop orders and a stop loss + take profit attached to new positions.
Everyone has a portfolio of their own, with no password: new on the first visit and kept for them. A random code is written
into their browser (a cookie for a year) and their account is saved under it, so the next visit opens the same portfolio; the
code is also shown to them (Account settings), to open the portfolio on another device. Nobody sees anyone else's portfolio.
The site owner's own portfolio opens on the owner's devices: a device becomes one once (the Paper Bots password, here or on the
Paper Bots page), then opens it directly every time, with nothing to type.
"""
import math
import re
import secrets
from datetime import date, timedelta
from types import SimpleNamespace

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import charts as C
import data
import paperbots as PB
import portfolio as PF
import theme as T
import ui
from i18n import L, is_ar, sector_name

ss = st.session_state
_A, _V, _C, _G, _MU, _BD = T.ACCENT, T.VIOLET, T.CYAN, T.GOLD, "#9D97A5", T.BORDER
SIDE = {"buy": ("Buy", "شراء", "pos", "add_shopping_cart"), "sell": ("Sell", "بيع", "neg", "sell"),
        "short": ("Sell short", "بيع على المكشوف", "sh", "trending_down"), "cover": ("Buy to cover", "شراء للتغطية", "cv", "shield")}
TYPE = {"market": ("Market", "سوق"), "limit": ("Limit", "محدد"), "stop": ("Stop", "وقف"), "trail": ("Trailing stop", "وقف متحرك")}
STATUS = {"open": ("Working", "قيد التنفيذ", "acc"), "held": ("Waiting", "بانتظار", "neu"), "filled": ("Filled", "منفذ", "pos"),
          "cancelled": ("Cancelled", "ملغي", "neu"), "expired": ("Expired", "منتهي", "neu"), "rejected": ("Rejected", "مرفوض", "neg")}
NOTE = {"oco": ("the other leg filled", "تنفذ الطرف الثاني"), "closed": ("position closed", "تسكّر المركز"), "user": ("by you", "ألغيته أنت"),
        "tif": ("end of its time", "انتهت مدته"), "parent": ("its entry did not fill", "ما تنفذ أمر الدخول"),
        "no_long": ("no shares to sell", "ما فيه أسهم للبيع"), "no_short": ("no short to cover", "ما فيه مركز مكشوف للتغطية"),
        "is_short": ("the position is short: cover first", "المركز مكشوف: غطّه أول"), "is_long": ("the position is long: sell first", "المركز شراء: بعه أول")}
ERR = {"bad": ("Choose an action and an order type.", "اختر الإجراء ونوع الأمر."),
       "bad_symbol": ("No price found for this symbol. Check the ticker (US stocks and ETFs).", "ما لقينا سعر لهالرمز. تأكد من الرمز (أسهم وصناديق أمريكية)."),
       "qty": ("Enter a quantity of at least 1 share.", "اكتب كمية سهم واحد على الأقل."),
       "no_long": ("You don't hold this stock, so there is nothing to sell. To bet on a fall, use Sell short.",
                   "ما عندك هالسهم فما فيه شي تبيعه. إذا تبي تراهن على النزول استخدم البيع على المكشوف."),
       "no_short": ("You have no short position in this stock to cover.", "ما عندك مركز مكشوف في هالسهم عشان تغطيه."),
       "too_many": ("That is more shares than you hold.", "هذا أكثر من الأسهم اللي عندك."),
       "is_short": ("You are short this stock: buy to cover first, then buy.", "عندك مركز مكشوف في هالسهم: غطّه أول وبعدين اشترِ."),
       "is_long": ("You hold this stock: sell it first before selling it short.", "عندك هالسهم: بعه أول قبل البيع على المكشوف."),
       "short_off": ("Short selling is turned off in the account settings.", "البيع على المكشوف مقفل من إعدادات الحساب."),
       "short_price": ("Brokers don't lend shares under $5, so they can't be sold short.", "الوسطاء ما يقرضون أسهم سعرها أقل من 5 دولار، فما تنباع على المكشوف."),
       "price": ("Enter the order's price.", "اكتب سعر الأمر."),
       "stop_side": ("A buy stop goes above the price and a sell stop below it (otherwise use a limit order).",
                     "أمر الوقف للشراء يكون فوق السعر، وللبيع تحت السعر (غير كذا استخدم الأمر المحدد)."),
       "trail_entry": ("A trailing stop protects a position: use it to sell a long or cover a short.", "الوقف المتحرك يحمي مركز: استخدمه لبيع سهم عندك أو تغطية مكشوف."),
       "bp": ("Not enough buying power.", "القوة الشرائية ما تكفي."),
       "bracket": ("The stop loss must be on the losing side and the take profit on the winning side of the price.",
                   "وقف الخسارة لازم يكون في جهة الخسارة وجني الأرباح في جهة الربح من السعر."),
       "margin_call": ("The account is in a margin call: close or cover positions before opening new ones.",
                       "الحساب في نداء هامش: سكّر أو غطِّ مراكز قبل ما تفتح جديدة.")}
CSS = f"""<style>
/* ---------- the account hero ---------- */
.pfhero {{ position:relative; overflow:hidden; border-radius:22px; border:1px solid {_BD}; padding:22px 26px 18px; margin:2px 0 14px;
  background:radial-gradient(120% 140% at 100% 0%, rgba(123,69,240,.28), transparent 55%), radial-gradient(90% 120% at 0% 100%, rgba(45,182,235,.14), transparent 60%),
  linear-gradient(135deg,#130E22,#1A1430 55%,#120D20); box-shadow:0 18px 40px rgba(0,0,0,.28), {T.GLOW}; }}
.pfhero::before {{ content:""; position:absolute; left:0; right:0; top:0; height:3px; background:linear-gradient(90deg,{_A},{_V},{_C}); opacity:.95; }}
.pfhero .grid {{ position:absolute; inset:0; pointer-events:none; opacity:.55;
  background-image:linear-gradient(rgba(45,182,235,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(45,182,235,.06) 1px,transparent 1px);
  background-size:34px 34px; -webkit-mask-image:radial-gradient(ellipse at 80% 40%,#000,transparent 70%); mask-image:radial-gradient(ellipse at 80% 40%,#000,transparent 70%); }}
.pfhero .top {{ position:relative; display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }}
.pfhero .eb {{ color:{_C}; font-weight:600; letter-spacing:.18em; font-size:.7rem; text-transform:uppercase; display:flex; align-items:center; gap:8px; }}
.pfhero .mid {{ position:relative; display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.05fr); gap:18px; align-items:center; margin-top:10px; }}
.pfhero .eql {{ color:{_MU}; font-size:.78rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; }}
.pfhero .eq {{ font-size:2.9rem; font-weight:700; color:#fff; letter-spacing:-.03em; line-height:1.05; margin:2px 0 8px; }}
.pfhero .eq > span, .pfk .v > span, .pfq .g .v > span {{ display:inline-block; direction:ltr; unicode-bidi:isolate; }}
.pfhero .eq small {{ font-size:1.4rem; color:#CFC8DA; font-weight:600; }}
.pfhero .pls {{ display:flex; flex-wrap:wrap; gap:8px; }}
.pfhero .pl {{ display:inline-flex; align-items:center; gap:6px; border-radius:11px; padding:6px 11px; font-weight:600; font-size:.88rem; border:1px solid; }}
.pfhero .pl.pos {{ background:{T.POS_BG}; color:{T.POS_FG}; border-color:{T.POS_BD}; }} .pfhero .pl.neg {{ background:{T.NEG_BG}; color:{T.NEG_FG}; border-color:{T.NEG_BD}; }}
.pfhero .pl.neu {{ background:{T.NEU_BG}; color:{T.NEU_FG}; border-color:{_BD}; }}
.pfhero .pl bdi {{ direction:ltr; unicode-bidi:isolate; }} .pfhero .pl em {{ font-style:normal; font-weight:500; opacity:.75; font-size:.78rem; }}
.pfhero .sp {{ height:120px; }} .pfhero .sp svg {{ width:100%; height:100%; display:block; overflow:visible; }}
.pfhero .chips {{ position:relative; display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
.pfhero .chip {{ background:rgba(26,22,36,.78); border:1px solid {_BD}; backdrop-filter:blur(6px); border-radius:10px; padding:6px 10px;
  font-size:.79rem; display:inline-flex; align-items:center; gap:7px; color:#CCC7D3; }}
.pfhero .chip b {{ color:#fff; unicode-bidi:isolate; direction:ltr; }} .pfhero .chip .ms {{ color:{_C}; font-size:1rem; }}
.pfhero .chip.warn {{ border-color:{T.NEG_BD}; background:{T.NEG_BG}; color:{T.NEG_FG}; }} .pfhero .chip.warn .ms, .pfhero .chip.warn b {{ color:{T.NEG_FG}; }}
.pfhero .st {{ position:relative; margin-top:10px; }}
.pfmode {{ display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:4px 11px; font-size:.74rem; font-weight:600; border:1px solid; }}
.pfmode .ms {{ font-size:.95rem; }}
.pfmode.saved {{ color:#C4F1D8; background:rgba(34,197,94,.12); border-color:rgba(74,222,128,.35); }}
.pfmode.view {{ color:#D9D4E2; background:rgba(157,151,165,.12); border-color:rgba(157,151,165,.35); }}
.pfmode.mine {{ color:#CFE3FF; background:rgba(59,139,235,.13); border-color:rgba(121,184,244,.4); }}
.pfcode {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; color:#CFC8DA; font-size:.86rem; line-height:1.5; }}
.pfcode b {{ color:#fff; }}
.pfmode.prac {{ color:#FDE7B0; background:rgba(245,185,74,.12); border-color:rgba(245,185,74,.4); }}
@media (max-width: 820px) {{ .pfhero {{ padding:18px 16px 14px; }} .pfhero .mid {{ grid-template-columns:1fr; }} .pfhero .sp {{ height:84px; }}
  .pfhero .eq {{ font-size:2.2rem; }} }}

/* ---------- KPI tiles ---------- */
.pfk {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(168px,1fr)); gap:10px; margin:4px 0 12px; }}
.pfk.c4 {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
@media (max-width: 760px) {{ .pfk, .pfk.c4 {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
.pfk .k {{ position:relative; overflow:hidden; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:12px 14px 12px; min-height:96px;
  transition:transform .18s, border-color .18s, box-shadow .18s; }}
.pfk .k:hover {{ transform:translateY(-2px); border-color:rgba(121,184,244,.45); box-shadow:0 12px 26px rgba(59,139,235,.14); }}
.pfk .k::after {{ content:""; position:absolute; inset:auto -30% -60% auto; width:120px; height:120px; border-radius:50%;
  background:radial-gradient(circle, rgba(123,69,240,.18), transparent 70%); pointer-events:none; }}
.pfk .l {{ color:{_MU}; font-size:.68rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; display:flex; align-items:center; gap:6px; }}
.pfk .l .ms {{ font-size:1rem; color:{_C}; }}
.pfk .v {{ font-size:1.42rem; font-weight:700; color:#fff; margin-top:6px; }}
.pfk .v.up {{ color:{T.POS_FG}; }} .pfk .v.dn {{ color:{T.NEG_FG}; }}
.pfk .s {{ color:{_MU}; font-size:.74rem; margin-top:3px; line-height:1.4; }} .pfk .s b {{ color:#DCD7E3; direction:ltr; unicode-bidi:isolate; }}
.pfk .bar {{ height:6px; border-radius:6px; background:rgba(157,151,165,.18); margin-top:9px; overflow:hidden; direction:ltr; }}
.pfk .bar i {{ display:block; height:100%; border-radius:6px; }}

/* ---------- portfolio health: the score ring, its five factors, the next steps ---------- */
.pfhs {{ display:grid; grid-template-columns:230px minmax(0,1fr) minmax(0,1.1fr); gap:14px; margin:4px 0 14px; }}
@media (max-width: 1100px) {{ .pfhs {{ grid-template-columns:210px minmax(0,1fr); }} .pfhs .tips {{ grid-column:1 / -1; }} }}
@media (max-width: 640px) {{ .pfhs {{ grid-template-columns:1fr; }} }}
.pfhs > div {{ position:relative; overflow:hidden; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:18px; padding:16px; }}
.pfhs .sc {{ display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center;
  background:radial-gradient(120% 90% at 50% 0%, var(--hg, rgba(45,182,235,.16)), transparent 70%), {T.BOX_BG}; }}
.pfhs .ring {{ position:relative; width:150px; height:150px; }}
.pfhs .ring svg {{ width:100%; height:100%; transform:rotate(-90deg); overflow:visible; }}
.pfhs .ring .tr {{ fill:none; stroke:rgba(157,151,165,.16); stroke-width:11; }}
.pfhs .ring .vl {{ fill:none; stroke-width:11; stroke-linecap:round; animation:pfring 1.2s cubic-bezier(.2,.8,.2,1) both;
  filter:drop-shadow(0 0 8px var(--hc, rgba(45,182,235,.55))); }}
@keyframes pfring {{ from {{ stroke-dashoffset:var(--c0); }} }}
.pfhs .ring .num {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }}
.pfhs .ring .num b {{ font-size:2.6rem; font-weight:800; color:#fff; line-height:1; letter-spacing:-.03em; }}
.pfhs .ring .num span {{ color:{_MU}; font-size:.75rem; margin-top:3px; }}
.pfhs .gr {{ margin-top:10px; display:inline-flex; align-items:center; gap:8px; font-weight:700; color:#fff; font-size:.95rem; }}
.pfhs .gr i {{ font-style:normal; border-radius:8px; padding:2px 9px; font-size:.82rem; color:#0E0918; background:var(--hc2, #2DB6EB); }}
.pfhs .cap {{ color:{_MU}; font-size:.74rem; margin-top:6px; line-height:1.45; }}
.pfhs .hd {{ display:flex; align-items:center; gap:8px; color:#fff; font-weight:700; font-size:.92rem; margin-bottom:10px; }}
.pfhs .hd .ms {{ color:{_C}; }}
.pfhs .f {{ padding:7px 0; border-top:1px solid rgba(44,39,56,.7); }} .pfhs .f:first-of-type {{ border-top:0; }}
.pfhs .f .t {{ display:flex; align-items:center; gap:8px; font-size:.84rem; color:#E7E3EB; font-weight:600; }}
.pfhs .f .t .ms {{ font-size:1.05rem; color:{_MU}; }} .pfhs .f .t b {{ margin-inline-start:auto; color:#fff; unicode-bidi:isolate; }}
.pfhs .f .t b.na {{ color:{_MU}; font-weight:500; }}
.pfhs .f .bar {{ height:6px; border-radius:6px; background:rgba(157,151,165,.16); margin:6px 0 4px; overflow:hidden; direction:ltr; }}
.pfhs .f .bar i {{ display:block; height:100%; border-radius:6px; animation:pfgrow 1s cubic-bezier(.2,.8,.2,1) both; }}
@keyframes pfgrow {{ from {{ width:0; }} }}
.pfhs .f .d {{ color:{_MU}; font-size:.74rem; }}
.pfhs .tip {{ display:flex; gap:10px; align-items:flex-start; border-radius:12px; padding:10px 12px; margin-top:8px; font-size:.84rem; line-height:1.5;
  color:#E2DDE8; border:1px solid; }}
.pfhs .tip .ms {{ font-size:1.15rem; margin-top:1px; }}
.pfhs .tip.warn {{ background:rgba(245,185,74,.08); border-color:rgba(245,185,74,.32); }} .pfhs .tip.warn .ms {{ color:#F5B94A; }}
.pfhs .tip.info {{ background:rgba(59,139,235,.08); border-color:rgba(121,184,244,.3); }} .pfhs .tip.info .ms {{ color:#79B8F4; }}
.pfhs .tip.good {{ background:rgba(34,197,94,.08); border-color:rgba(74,222,128,.32); }} .pfhs .tip.good .ms {{ color:#4ADE80; }}
.pfhs .tip p {{ margin:0; }}
.memo {{ display:flex; align-items:flex-start; gap:6px; margin-top:4px; color:#CFC3F5; font-size:.76rem; font-style:italic; line-height:1.4; }}
.memo .ms {{ font-size:.95rem; color:#A78BFA; font-style:normal; }}
.pfhs .bdg {{ margin-top:12px; padding-top:10px; border-top:1px solid rgba(44,39,56,.7); display:flex; align-items:center; gap:10px; flex-wrap:wrap;
  color:{_MU}; font-size:.78rem; }}
.pfhs .bdg .row {{ display:flex; gap:5px; flex-wrap:wrap; }}
.pfhs .bdg .b {{ width:26px; height:26px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-size:.9rem;
  background:rgba(157,151,165,.12); color:#5E586A; border:1px solid rgba(157,151,165,.18); }}
.pfhs .bdg .b.on {{ background:linear-gradient(135deg,#F5B94A,#7B45F0); color:#fff; border-color:transparent; box-shadow:0 0 10px rgba(245,185,74,.35); }}
.pfhs .bdg b {{ color:#fff; }}
/* ---------- achievements ---------- */
.pfach .top {{ display:flex; align-items:center; gap:14px; flex-wrap:wrap; margin:2px 0 12px; color:{_MU}; font-size:.85rem; }}
.pfach .top b {{ color:#fff; font-size:1.1rem; }}
.pfach .top .tb {{ flex:1; min-width:160px; height:8px; border-radius:8px; background:rgba(157,151,165,.16); overflow:hidden; direction:ltr; }}
.pfach .top .tb i {{ display:block; height:100%; background:linear-gradient(90deg,#F5B94A,#A78BFA,#2DB6EB); border-radius:8px; }}
.pfach .gr {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(190px,1fr)); gap:10px; }}
.pfach .a {{ position:relative; overflow:hidden; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:14px; transition:transform .18s, border-color .18s; }}
.pfach .a:hover {{ transform:translateY(-2px); }}
.pfach .a .md {{ width:46px; height:46px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.45rem;
  background:rgba(157,151,165,.10); color:#6E6879; border:1px dashed rgba(157,151,165,.3); }}
.pfach .a.on {{ border-color:rgba(245,185,74,.35); background:radial-gradient(120% 90% at 0% 0%, rgba(245,185,74,.12), transparent 60%), {T.BOX_BG}; }}
.pfach .a.on .md {{ background:conic-gradient(from 200deg,#F5B94A,#A78BFA,#2DB6EB,#F5B94A); color:#fff; border:0;
  box-shadow:0 0 0 3px rgba(18,14,30,.9) inset, 0 6px 18px rgba(245,185,74,.28); }}
.pfach .a.on::after {{ content:"verified"; font-family:'Material Symbols Rounded'; position:absolute; top:10px; inset-inline-end:12px; color:#F5B94A; font-size:1.1rem; }}
.pfach .a .t {{ color:#fff; font-weight:700; font-size:.9rem; margin-top:10px; }}
.pfach .a:not(.on) .t {{ color:#CFC8DA; }}
.pfach .a .d {{ color:{_MU}; font-size:.75rem; margin-top:3px; line-height:1.4; min-height:2.1em; }}
.pfach .a .pb {{ height:5px; border-radius:5px; background:rgba(157,151,165,.16); margin-top:9px; overflow:hidden; direction:ltr; }}
.pfach .a .pb i {{ display:block; height:100%; border-radius:5px; background:linear-gradient(90deg,{_A},{_V}); }}
.pfach .a.on .pb i {{ background:linear-gradient(90deg,#F5B94A,#4ADE80); }}
.pfach .a .pt {{ color:{_MU}; font-size:.7rem; margin-top:4px; direction:ltr; unicode-bidi:isolate; text-align:end; }}
/* ---------- the P&L calendar ---------- */
.pfcal {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:12px; margin:4px 0 12px; }}
.pfcal .m {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:12px; }}
.pfcal .mh {{ display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:8px; }}
.pfcal .mh b {{ color:#fff; font-size:.92rem; }} .pfcal .mh span {{ font-weight:700; font-size:.85rem; direction:ltr; unicode-bidi:isolate; }}
.pfcal .ms2 {{ color:{_MU}; font-size:.72rem; margin:-4px 0 8px; }}
.pfcal .g {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:4px; }}
.pfcal .wd {{ color:{_MU}; font-size:.66rem; text-align:center; font-weight:600; }}
.pfcal .c {{ border-radius:8px; min-height:42px; padding:3px 4px; display:flex; flex-direction:column; justify-content:space-between;
  background:rgba(157,151,165,.07); border:1px solid rgba(157,151,165,.08); }}
.pfcal .c i {{ font-style:normal; color:{_MU}; font-size:.62rem; }}
.pfcal .c em {{ font-style:normal; font-weight:700; font-size:.68rem; color:#fff; text-align:center; white-space:nowrap; direction:ltr; unicode-bidi:isolate; }}
.pfcal .c.x {{ background:transparent; border-color:transparent; }}
.pfcal .c.h {{ background:rgba(157,151,165,.04); }}
.pflg {{ display:flex; gap:6px; align-items:center; color:{_MU}; font-size:.72rem; margin-top:2px; }}
.pflg span {{ width:14px; height:10px; border-radius:3px; display:inline-block; }}
/* ---------- holdings map ---------- */
.pfmap .hmwrap {{ border-radius:18px; }}
.pfmapcap {{ display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; color:{_MU}; font-size:.78rem; margin:6px 2px 12px; }}
.spk {{ display:block; width:96px; height:28px; direction:ltr; }}

/* ---------- positions ---------- */
.pfpos {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:18px; overflow:hidden; margin:2px 0 10px; }}
.pfpos .hd {{ display:flex; align-items:center; justify-content:space-between; gap:10px; padding:12px 16px; border-bottom:1px solid {_BD}; flex-wrap:wrap; }}
.pfpos .hd .tt {{ display:flex; align-items:center; gap:8px; color:#fff; font-weight:600; }} .pfpos .hd .tt .ms {{ color:{_C}; }}
.pfpos .hd .sum {{ display:flex; gap:8px; flex-wrap:wrap; }}
.pfpos .sc {{ overflow-x:auto; }}
.pfpos table {{ width:100%; border-collapse:separate; border-spacing:0; min-width:980px; font-size:.86rem; }}
.pfpos th {{ color:{_MU}; font-weight:600; font-size:.68rem; letter-spacing:.07em; text-transform:uppercase; text-align:start; padding:9px 12px; white-space:nowrap; }}
.pfpos th.r, .pfpos td.r {{ text-align:end; }}
.pfpos td {{ padding:10px 12px; border-top:1px solid rgba(44,39,56,.75); color:#E7E3EB; white-space:nowrap; vertical-align:middle; }}
.pfpos tr:hover td {{ background:rgba(59,139,235,.06); }}
.pfpos td .n {{ direction:ltr; unicode-bidi:isolate; }}
.pfpos a.as {{ display:inline-flex; align-items:center; gap:8px; color:#fff !important; text-decoration:none !important; }}
.pfpos td .sub {{ display:block; color:{_MU}; font-size:.72rem; margin-top:1px; }}
.pfpos .up {{ color:{T.POS_FG}; }} .pfpos .dn {{ color:{T.NEG_FG}; }}
.sd {{ display:inline-flex; align-items:center; gap:4px; border-radius:7px; padding:3px 8px; font-size:.7rem; font-weight:700; letter-spacing:.05em; border:1px solid; }}
.sd.long {{ color:{T.POS_FG}; background:{T.POS_BG}; border-color:{T.POS_BD}; }}
.sd.short {{ color:#FDBA74; background:{T.ORG_BG}; border-color:rgba(249,115,22,.45); }}
.wb {{ display:inline-block; width:64px; height:6px; border-radius:6px; background:rgba(157,151,165,.18); overflow:hidden; vertical-align:middle;
  margin-inline-end:6px; direction:ltr; }}
.wb i {{ display:block; height:100%; border-radius:6px; background:linear-gradient(90deg,{_A},{_C}); }}
.wb.s i {{ background:linear-gradient(90deg,#F97316,#F87171); }}
.prot {{ display:inline-flex; gap:5px; flex-wrap:wrap; }}
.prot span {{ border-radius:6px; padding:2px 6px; font-size:.72rem; border:1px solid {_BD}; color:#D8D3DE; }} .prot bdi {{ direction:ltr; unicode-bidi:isolate; }}
.prot .sl {{ border-color:{T.NEG_BD}; color:{T.NEG_FG}; }} .prot .tp {{ border-color:{T.POS_BD}; color:{T.POS_FG}; }}
.prot .no {{ border-color:rgba(249,115,22,.5); color:#FDBA74; }}

/* ---------- orders, activity, empty states ---------- */
.pfo {{ display:flex; align-items:center; gap:12px; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:14px; padding:10px 14px; min-height:58px; }}
.pfo .ic {{ width:36px; height:36px; border-radius:11px; display:flex; align-items:center; justify-content:center; flex:none; }}
.pfo .ic.pos {{ background:{T.POS_BG}; color:{T.POS_FG}; }} .pfo .ic.neg {{ background:{T.NEG_BG}; color:{T.NEG_FG}; }}
.pfo .ic.sh {{ background:{T.ORG_BG}; color:#FDBA74; }} .pfo .ic.cv {{ background:{T.ACC_BG}; color:{T.ACC_FG}; }}
.pfo .tx {{ min-width:0; flex:1; }} .pfo .t1 {{ color:#fff; font-weight:600; font-size:.9rem; }} .pfo .t1 bdi {{ direction:ltr; unicode-bidi:isolate; }}
.pfo .t2 {{ color:{_MU}; font-size:.74rem; margin-top:2px; }} .pfo .t2 bdi {{ direction:ltr; unicode-bidi:isolate; }}
.pfact {{ position:relative; padding-inline-start:18px; }}
.pfact::before {{ content:""; position:absolute; inset-inline-start:6px; top:6px; bottom:6px; width:2px; background:linear-gradient({_V},{_C}); opacity:.4; border-radius:2px; }}
.pfact .it {{ position:relative; padding:7px 0 9px; }}
.pfact .it::before {{ content:""; position:absolute; inset-inline-start:-16px; top:12px; width:10px; height:10px; border-radius:50%; background:{_C};
  box-shadow:0 0 0 3px rgba(45,182,235,.18); }}
.pfact .it.dn::before {{ background:{T.NEG_FG}; box-shadow:0 0 0 3px rgba(248,113,113,.18); }}
.pfact .it.sh::before {{ background:#F97316; box-shadow:0 0 0 3px rgba(249,115,22,.18); }}
.pfact .a {{ color:#E7E3EB; font-size:.86rem; }} .pfact .a b {{ color:#fff; }} .pfact .a bdi {{ direction:ltr; unicode-bidi:isolate; }}
.pfact .w {{ color:{_MU}; font-size:.72rem; margin-top:2px; }}
.pfempty {{ text-align:center; padding:26px 18px; border:1px dashed rgba(157,151,165,.35); border-radius:18px; color:#BCB6C7; margin:4px 0 10px;
  background:rgba(26,22,36,.45); }}
.pfempty .ms {{ font-size:2.2rem; color:{_C}; display:block; margin-bottom:6px; }} .pfempty b {{ color:#fff; display:block; font-size:1.02rem; margin-bottom:4px; }}

/* ---------- trade ticket ---------- */
.pfq {{ position:relative; overflow:hidden; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:18px; padding:16px 18px; margin:2px 0 10px; }}
.pfq::before {{ content:""; position:absolute; left:0; right:0; top:0; height:2px; background:linear-gradient(90deg,{_A},{_V},{_C}); opacity:.8; }}
.pfq .row1 {{ display:flex; align-items:center; gap:12px; }}
.pfq .nm {{ color:#fff; font-weight:700; font-size:1.15rem; }} .pfq .nm small {{ display:block; color:{_MU}; font-weight:500; font-size:.78rem; }}
.pfq .px {{ margin-inline-start:auto; text-align:end; }} .pfq .px b {{ display:block; font-size:1.6rem; color:#fff; direction:ltr; unicode-bidi:isolate; }}
.pfq .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:8px; margin-top:12px; }}
.pfq .g {{ background:rgba(14,9,24,.35); border:1px solid rgba(44,39,56,.9); border-radius:11px; padding:8px 10px; }}
.pfq .g .l {{ color:{_MU}; font-size:.66rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; }}
.pfq .g .v {{ color:#fff; font-weight:600; font-size:.92rem; margin-top:2px; }}
.pfq .rng {{ margin-top:12px; }} .pfq .rng .lb {{ display:flex; justify-content:space-between; color:{_MU}; font-size:.72rem; direction:ltr; }}
.pfq .rng .tr {{ position:relative; height:8px; border-radius:8px; background:linear-gradient(90deg,{T.NEG_BD},#3E3A46,{T.POS_BD}); margin:5px 0 2px; direction:ltr; }}
.pfq .rng .tr i {{ position:absolute; top:50%; width:14px; height:14px; border-radius:50%; background:#fff; border:3px solid {_A}; transform:translate(-50%,-50%);
  box-shadow:0 0 0 4px rgba(59,139,235,.22); }}
/* buying power, inside the ticket: what's available, the most shares it buys, and how much of it this order takes */
.pfbp {{ position:relative; overflow:hidden; border-radius:16px; padding:12px 14px; margin:2px 0 6px; border:1px solid rgba(121,184,244,.3);
  background:radial-gradient(120% 140% at 100% 0%, rgba(45,182,235,.16), transparent 60%), linear-gradient(135deg, rgba(59,139,235,.10), rgba(123,69,240,.08)); }}
.pfbp.sh {{ border-color:rgba(249,115,22,.35); background:radial-gradient(120% 140% at 100% 0%, rgba(249,115,22,.14), transparent 60%),
  linear-gradient(135deg, rgba(249,115,22,.08), rgba(123,69,240,.06)); }}
.pfbp .t {{ display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; }}
.pfbp .l {{ display:flex; align-items:center; gap:7px; color:#CFC8DA; font-size:.74rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }}
.pfbp .l .ms {{ color:{_C}; font-size:1.1rem; }} .pfbp.sh .l .ms {{ color:#FB923C; }}
.pfbp .v {{ color:#fff; font-size:1.55rem; font-weight:800; letter-spacing:-.02em; direction:ltr; unicode-bidi:isolate; }}
.pfbp .s {{ color:{_MU}; font-size:.76rem; margin-top:2px; line-height:1.5; }} .pfbp .s b {{ color:#E7E3EB; direction:ltr; unicode-bidi:isolate; }}
.pfbp .mx {{ display:inline-flex; align-items:center; gap:6px; margin-top:8px; border-radius:9px; padding:4px 9px; font-size:.78rem; color:#DCEBFA;
  background:rgba(59,139,235,.14); border:1px solid rgba(121,184,244,.3); }} .pfbp .mx b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }}
.pfbp .u {{ margin-top:10px; }}
.pfbp .u .bar {{ height:8px; border-radius:8px; background:rgba(157,151,165,.18); overflow:hidden; direction:ltr; }}
.pfbp .u .bar i {{ display:block; height:100%; border-radius:8px; transition:width .3s; }}
.pfbp .u .cap {{ display:flex; justify-content:space-between; gap:8px; color:{_MU}; font-size:.74rem; margin-top:4px; }}
.pfbp .u .cap b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }} .pfbp .u .cap b.dn {{ color:{T.NEG_FG}; }}
.pfprev {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:18px; padding:14px 16px; margin:6px 0 8px; }}
.pfprev .h {{ display:flex; align-items:center; gap:8px; color:#fff; font-weight:600; margin-bottom:8px; }} .pfprev .h .ms {{ color:{_C}; }}
.pfprev .r {{ display:flex; justify-content:space-between; gap:10px; padding:6px 0; border-top:1px solid rgba(44,39,56,.7); font-size:.86rem; color:#CFC8DA; }}
.pfprev .r b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }} .pfprev .r b.up {{ color:{T.POS_FG}; }} .pfprev .r b.dn {{ color:{T.NEG_FG}; }}
.pfprev .rr {{ display:flex; height:10px; border-radius:8px; overflow:hidden; margin:10px 0 2px; direction:ltr; }}
.pfprev .rr i {{ display:block; height:100%; }} .pfprev .rr .ls {{ background:linear-gradient(90deg,#B4364A,#F26B6B); }}
.pfprev .rr .gn {{ background:linear-gradient(90deg,#34D27A,#1C9E58); }}
.pfwarn {{ display:flex; gap:10px; align-items:flex-start; border-radius:14px; padding:10px 12px; margin:8px 0 2px; font-size:.82rem; line-height:1.5;
  background:{T.ORG_BG}; border:1px solid rgba(249,115,22,.4); color:#FED7AA; }}
.pfwarn .ms {{ color:#FB923C; font-size:1.2rem; flex:none; }} .pfwarn b {{ color:#FFEDD5; }}
.pfinfo {{ display:flex; gap:10px; align-items:flex-start; border-radius:14px; padding:10px 12px; margin:6px 0 2px; font-size:.8rem; line-height:1.5;
  background:{T.ACC_BG}; border:1px solid rgba(121,184,244,.3); color:#CFE3F8; }} .pfinfo .ms {{ color:{T.ACC_FG}; font-size:1.15rem; flex:none; }}
[class*="st-key-pf_submit"] button {{ min-height:50px !important; border:0 !important; border-radius:14px !important;
  background:linear-gradient(95deg,{_A} 0%,{_V} 62%,{_C} 130%) !important; box-shadow:0 10px 26px rgba(59,139,235,.35); }}
[class*="st-key-pf_submit"].pfsh button, .st-key-pf_submit_short button {{ background:linear-gradient(95deg,#C2410C 0%,#EA580C 55%,#F59E0B 130%) !important;
  box-shadow:0 10px 26px rgba(234,88,12,.3); }}
[class*="st-key-pf_submit"] button:hover {{ filter:brightness(1.08); transform:translateY(-1px); }}
[class*="st-key-pf_submit"] button p, [class*="st-key-pf_submit"] button [data-testid="stIconMaterial"] {{ color:#fff !important; font-weight:700 !important; font-size:1rem !important; }}
[class*="st-key-pfticket"] {{ position:relative; background:linear-gradient(180deg,{T.CARD2},{T.CARD}); border:1px solid {_BD}; border-radius:20px; padding:16px 16px 14px;
  box-shadow:0 14px 32px rgba(0,0,0,.2); }}
[class*="st-key-pfticket"]::before {{ content:""; position:absolute; top:0; left:16px; right:16px; height:1px; background:linear-gradient(90deg,transparent,rgba(196,181,253,.55),transparent); }}
[class*="st-key-pfbar"] {{ background:linear-gradient(180deg,{T.CARD2},{T.CARD}); border:1px solid {_BD}; border-radius:16px; padding:10px 14px 12px; }}

/* ---------- analytics ---------- */
.pfls {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:4px 0 10px; }}
@media (max-width: 760px) {{ .pfls {{ grid-template-columns:1fr; }} }}
.pfls .c {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:14px 16px; }}
.pfls .c .h {{ display:flex; align-items:center; gap:8px; font-weight:700; color:#fff; margin-bottom:8px; }}
.pfls .c .r {{ display:flex; justify-content:space-between; padding:5px 0; border-top:1px solid rgba(44,39,56,.7); font-size:.85rem; color:#CFC8DA; }}
.pfls .c .r b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }} .pfls .c .r b.up {{ color:{T.POS_FG}; }} .pfls .c .r b.dn {{ color:{T.NEG_FG}; }}
</style>"""


# =====================================================================
# the account behind the page
# =====================================================================
COOKIE = "alt_pf"                                    # the browser cookie that holds a visitor's portfolio code
_CODE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
# the site owner's portfolio from before every visitor had their own (the row "__portfolio__"): it now opens like any other
# portfolio, with its own code. Only the code's SHA-256 is here (the repository is public); the owner has the code itself.
_LEGACY = "885f9c44e9287b4bce07e2588eb061108ea64ac8b01f1438a88e1bbea373a7ab"


def is_owner(code):
    """True for the site owner's device code (or the owner's code from 18.9)."""
    import hashlib
    import hmac
    oc = PF.owner_code()
    return bool(code) and ((oc is not None and hmac.compare_digest(str(code), oc))
                           or hashlib.sha256(str(code).encode()).hexdigest() == _LEGACY)


def key_of(code):
    """The stored row of a portfolio code: the owner's own portfolio on the owner's devices, else that visitor's own row."""
    return PF.KEY if is_owner(code) else PF.visitor_key(code)


def _from_link():
    """A link with ?pf=<code> opens that portfolio on this device (then the code leaves the address bar)."""
    try:
        v = st.query_params.get("pf")
    except Exception:
        return None
    if v is None:
        return None
    try:
        del st.query_params["pf"]
    except Exception:
        pass
    v = str(v).strip()
    if not _CODE.match(v):
        return None
    try:
        _, row = PF.load(key_of(v))
    except PB.StoreError:
        return None
    return v if row is not None else None


def _vid():
    """This visitor's portfolio code: from a ?pf= link, else the one already open, else the one their browser sent (cookie),
    else a new random one (a new portfolio)."""
    v = _from_link()
    if v:
        ss["pf_vid"] = v
        ss["pf_flash"] = L("Your portfolio is open on this device", "انفتحت محفظتك على هالجهاز")
        return v
    v = ss.get("pf_vid")
    if isinstance(v, str) and _CODE.match(v):
        return v
    try:
        v = st.context.cookies.get(COOKIE)
    except Exception:
        v = None
    if not (isinstance(v, str) and _CODE.match(v)):
        v = secrets.token_urlsafe(18)
    ss["pf_vid"] = v
    return v


def _remember(code):
    """Writes the code into this browser for a year (renewed at every visit), so the next visit opens the same portfolio."""
    try:
        import streamlit.components.v1 as components
        components.html("<script>try{var w=window.parent,d=w.document;d.cookie='" + COOKIE + "=" + code + "; path=/; max-age=31536000; "
                        "SameSite=Lax'+(w.location.protocol==='https:'?'; Secure':'');}catch(e){}</script>", height=0)
    except Exception:
        pass


def ctx():
    """The account of this page view (this visitor's own portfolio): its open orders checked against the real prices, then
    rebuilt day by day."""
    mode = "mine"
    if ss.get("pb_admin") and PF.owner_code() and not is_owner(ss.get("pf_vid")):
        ss["pf_vid"] = PF.owner_code()       # the owner unlocked the Paper Bots on this device: it opens the owner's portfolio from now on
    code = _vid()
    key = key_of(code)
    _remember(code)
    mkt = PF.Market()
    err, row = None, None
    try:
        state, row = PF.load(key)
    except PB.StoreError as e:               # the store can't be reached: this visit's own copy meanwhile (not saved)
        err = e
        if not isinstance(ss.get("pf_practice"), dict):
            ss["pf_practice"] = PF.new_state()
        state = ss["pf_practice"]
    rev0 = state.get("rev")
    mark = lambda: (len(state["fills"]), tuple(o["status"] for o in state["orders"]))
    before = mark()
    try:
        moved = PF.process(state, mkt)
    except Exception:
        moved = False
    # fills and expiries are kept at once; a mere "checked up to" mark (and a trailing stop's high) at most once an hour,
    # since they are found again from the bars anyway
    stale = (PF.utcnow() - PF.parse(state.get("ck_saved") or "2000-01-01T00:00:00Z")).total_seconds() > 3600
    if err is None and (mark() != before or (moved and stale)) and row:
        try:
            state["ck_saved"] = PF.iso(PF.utcnow())
            PF.save(state, row, expect=rev0, key=key)
            rev0 = state.get("rev")
        except Exception:
            pass
    view = PF.rebuild(state, mkt)
    acct = PF.account(view, state["settings"])
    return SimpleNamespace(state=state, row=row, mode=mode, key=key, code=code, can_trade=True, mkt=mkt,
                           view=view, acct=acct, err=err, rev=rev0)


def commit(c, flash=None):
    """Keeps a change (this visitor's portfolio in Supabase; this visit's copy while the store is down) and reloads the page.
    If the portfolio changed meanwhile (another tab saved a fill first), nothing is overwritten: the page reloads with the new copy."""
    if c.err is not None:
        ss["pf_practice"] = c.state
    else:
        try:
            PF.save(c.state, c.row, expect=c.rev, key=c.key)
        except PF.Conflict:
            ss["pf_flash"] = L("The portfolio changed a moment ago (an order filled). Check it and send again.",
                               "المحفظة تغيرت قبل لحظات (تنفذ أمر). راجعها وأرسل من جديد.")
            st.rerun()
    if flash:
        ss["pf_flash"] = flash
    st.rerun()


def _flash():
    msg = ss.pop("pf_flash", None)
    if msg:
        st.toast(msg, icon=":material/task_alt:")


# =====================================================================
# small pieces
# =====================================================================
def _n(v, dec=2):
    return f"{v:,.{dec}f}"


def _m(v, dec=2, sign=False):
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "—"
    s = ("+" if v > 0 else "-" if v < 0 else "") if sign else ("-" if v < 0 else "")
    return f"{s}${abs(v):,.{dec}f}"


def _p(v, dec=2, sign=True):
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "—"
    return f"{v:+.{dec}f}%" if sign else f"{v:.{dec}f}%"


def _k(v):
    return "pos" if v is not None and v > 0 else "neg" if v is not None and v < 0 else "neu"


def _bdi(s):
    return f"<bdi>{s}</bdi>"


def _when(ts):
    try:
        t = PF.parse(ts).astimezone(PF.ET)
    except Exception:
        return str(ts)[:16]
    return t.strftime("%m/%d %H:%M") + " ET"


def _ago(ts):
    try:
        return T.time_ago(pd.Timestamp(PF.parse(ts)), is_ar())
    except Exception:
        return ""


def _side(s):
    en, ar, k, ic = SIDE[s]
    return L(en, ar), k, ic


def _otext(o):
    """'Limit 182.50 · Day' for an order."""
    t = L(*TYPE[o["type"]])
    if o["type"] == "limit":
        t += f" {_bdi(_m(o['limit']))}"
    elif o["type"] == "stop":
        t += f" {_bdi(_m(o['stop']))}"
    elif o["type"] == "trail":
        t += f" {_bdi(_p(o['trail'], 1, False))}"
    tif = L("Day", "اليوم") if o.get("tif") != "gtc" else L("Until cancelled", "حتى الإلغاء")
    return f"{t} · {tif}"


def _spark(eq, w=520, h=120):
    """The equity line of the hero (an area with its last point lit)."""
    vals = [float(x) for x in (eq.values if hasattr(eq, "values") else eq) if x == x]
    if len(vals) < 2:
        vals = (vals or [1.0]) * 2
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or max(abs(hi) * 0.01, 1.0)
    pts = [(i / (len(vals) - 1) * w, h - 10 - (v - lo) / span * (h - 26)) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    up = vals[-1] >= vals[0]
    col = "#34D27A" if up else "#F26B6B"
    x, y = pts[-1]
    return (f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg" style="direction:ltr">'
            f'<defs><linearGradient id="pfsg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{col}" stop-opacity=".35"/>'
            f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
            f'<polygon points="0,{h} {line} {w},{h}" fill="url(#pfsg)"/>'
            f'<polyline points="{line}" fill="none" stroke="{col}" stroke-width="2.4" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{col}" stroke="#fff" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>')


def mode_badge(c):
    if c.err is not None:
        return f'<span class="pfmode prac">{T.icon("science")}{L("This visit only (not saved)", "لهالزيارة فقط (ما ينحفظ)")}</span>'
    if is_owner(c.code):
        return f'<span class="pfmode saved">{T.icon("verified_user")}{L("Your portfolio", "محفظتك")}</span>'
    return f'<span class="pfmode mine">{T.icon("person")}{L("Your own portfolio", "محفظتك الخاصة")}</span>'


def day_label(v):
    """'Today' while today's session counts, else 'Last session' (a weekend, before the open)."""
    today = PF.utcnow().astimezone(PF.ET).date().isoformat()
    return L("Today", "اليوم") if v.get("end_day") == today else L("Last session", "آخر جلسة")


def hero(c, title_en="Paper Portfolio", title_ar="المحفظة الافتراضية"):
    v, a = c.view, c.acct
    eq = v["equity"]
    whole, cents = f"{eq:,.2f}".split(".")
    day, tot = v["day_pnl"], v["pnl"]
    arrow = lambda x: "▲" if x > 0 else "▼" if x < 0 else "•"
    lev = a["leverage"]
    chips = [f'<span class="chip">{T.icon("payments")}{L("Cash", "الكاش")} <b>{_m(a["cash"])}</b></span>',
             f'<span class="chip">{T.icon("bolt")}{L("Buying power", "القوة الشرائية")} <b>{_m(a["bp_long"], 0)}</b></span>',
             f'<span class="chip">{T.icon("trending_up")}{L("Long", "شراء")} <b>{_m(a["lmv"], 0)}</b></span>',
             f'<span class="chip">{T.icon("trending_down")}{L("Short", "مكشوف")} <b>{_m(a["smv"], 0)}</b></span>',
             f'<span class="chip">{T.icon("speed")}{L("Leverage", "الرافعة")} <b>{lev:.2f}×</b></span>']
    if a["margin_call"]:
        chips.append(f'<span class="chip warn">{T.icon("warning")}{L("Margin call", "نداء هامش")} <b>{_m(a["maint"] - a["equity"], 0)}</b></span>')
    curve = v["curve"]["equity"] if len(v["curve"]) else pd.Series([eq])
    rtl = " rtl" if is_ar() else ""
    return (f'<div class="pfhero{rtl}"><div class="grid"></div><div class="top"><div class="eb">{T.icon("account_balance_wallet")}'
            f'{T.esc(L(title_en, title_ar))} · {L("Margin account", "حساب هامش")}</div>{mode_badge(c)}</div>'
            f'<div class="mid"><div><div class="eql">{L("Total equity", "إجمالي قيمة الحساب")}</div>'
            f'<div class="eq"><span dir="ltr">${whole}<small>.{cents}</small></span></div><div class="pls">'
            f'<span class="pl {_k(day)}">{arrow(day)} {_bdi(_m(day, 2, True))} {_bdi("(" + _p(v["day_pct"]) + ")")} <em>{day_label(v)}</em></span>'
            f'<span class="pl {_k(tot)}">{arrow(tot)} {_bdi(_m(tot, 2, True))} {_bdi("(" + _p(v["ret"]) + ")")} <em>{L("All time", "من البداية")}</em></span>'
            f'</div></div><div class="sp">{_spark(curve)}</div></div><div class="chips">{"".join(chips)}</div>'
            f'<div class="st">{T.market_status(is_ar())}</div></div>')


def kpis(items, cls=""):
    """[(icon, label, value_html, sub_html, kind, bar)]: bar = (pct, colour) or None. cls "c4": four to a row."""
    out = []
    for ic, lab, val, sub, kind, bar in items:
        b = f'<div class="bar"><i style="width:{min(max(bar[0], 0), 100):.0f}%;background:{bar[1]}"></i></div>' if bar else ""
        kc = {"pos": "up", "neg": "dn"}.get(kind, "")
        out.append(f'<div class="k"><div class="l">{T.icon(ic)}{T.esc(lab)}</div><div class="v {kc}"><span dir="ltr">{val}</span></div>'
                   f'<div class="s">{sub}</div>{b}</div>')
    return f'<div class="pfk {cls}">{"".join(out)}</div>'


def empty(ic, title, text):
    return f'<div class="pfempty"><span class="ms">{ic}</span><b>{T.esc(title)}</b>{T.esc(text)}</div>'


def access_bar(c):
    """Whose portfolio this is: the visitor's own (no password)."""
    if c.err is not None:
        st.warning(L("Your portfolio can't be reached right now (Supabase). You can keep trading; what you do in this visit isn't saved.",
                     "ما نقدر نوصل لمحفظتك الحين (Supabase). تقدر تكمل تداول، بس اللي تسويه بهالزيارة ما ينحفظ."), icon=":material/database:")
    if PB.backend() == "local":
        st.warning(L("Trial mode: portfolios are kept in temporary storage and are lost when the site restarts. Connect Supabase (as for the "
                     "Paper Bots) to keep them for good.",
                     "وضع التجربة: المحافظ محفوظة مؤقتاً وتنحذف إذا أعاد الموقع التشغيل. اربط Supabase (مثل البوتات الافتراضية) عشان تنحفظ بشكل دائم."),
                   icon=":material/info:")
    with st.container(key="pfbar"):
        if is_owner(c.code):
            txt = L("Your portfolio (site owner). This device opens it directly, with nothing to type; visitors each have their own.",
                    "محفظتك (مالك الموقع). هالجهاز يفتحها مباشرة بدون ما تكتب شي، وكل زائر له محفظته الخاصة.")
            st.markdown(f'<div class="pfinfo">{T.icon("verified_user")}<div>{T.esc(txt)}</div></div>', unsafe_allow_html=True)
            return
        a, b = st.columns([1.6, 1], vertical_alignment="center")
        with a:
            txt = L("Your own portfolio: it starts with $100,000 of virtual money, only you see it, and it is kept for you in this "
                    "browser. To open it on another device, use your portfolio code (Account settings).",
                    "محفظتك الخاصة: تبدأ بـ 100,000$ افتراضية، ما يشوفها غيرك، وتنحفظ لك في هالمتصفح. "
                    "عشان تفتحها من جهاز ثاني استخدم رمز محفظتك (إعدادات الحساب).")
            st.markdown(f'<div class="pfinfo">{T.icon("person")}<div>{T.esc(txt)}</div></div>', unsafe_allow_html=True)
        with b:
            if PF.owner_code():
                # once per device: the owner's password makes this device open the owner's portfolio from then on
                with st.popover(L("Site owner?", "مالك الموقع؟"), icon=":material/admin_panel_settings:", width="stretch"):
                    st.caption(L("Once on each device: after this, it opens your portfolio directly, with nothing to type.",
                                 "مرة وحدة لكل جهاز: بعدها يفتح محفظتك مباشرة بدون ما تكتب شي."))
                    st.text_input(L("Paper Bots password", "كلمة مرور البوتات"), type="password", key="pf_pw")
                    if st.button(L("This is my device", "هذا جهازي"), icon=":material/devices:", key="pf_claim", width="stretch"):
                        if PB.check_password(ss.get("pf_pw")):
                            ss["pb_admin"] = True
                            ss["pf_vid"] = PF.owner_code()
                            ss["pf_flash"] = L("Your portfolio is open, and this device will open it directly from now on",
                                               "انفتحت محفظتك، وهالجهاز بيفتحها مباشرة من الحين")
                            st.rerun()
                        st.error(L("Wrong password.", "كلمة المرور غلط."))


def code_box(c):
    """A visitor's portfolio code: copy it to open the same portfolio on another device, or paste one here."""
    if c.mode != "mine" or not c.code:
        return
    if is_owner(c.code):                    # the owner's devices: nothing to copy (another device: "Site owner?" once)
        st.markdown(f'<div class="pfcode">{T.icon("verified_user")}<div>'
                    + T.esc(L("This device opens your portfolio directly. On another device, tap “Site owner?” once.",
                              "هالجهاز يفتح محفظتك مباشرة. على جهاز ثاني اضغط «مالك الموقع؟» مرة وحدة."))
                    + "</div></div>", unsafe_allow_html=True)
        return
    st.markdown(f'<div class="pfcode">{T.icon("key")}<div><b>{T.esc(L("Your portfolio code", "رمز محفظتك"))}</b> · '
                + T.esc(L("It opens this portfolio on any device. Keep it to yourself: whoever has it can trade your portfolio.",
                          "يفتح هالمحفظة من أي جهاز. لا تعطيه أحد: اللي معه الرمز يقدر يتداول بمحفظتك."))
                + "</div></div>", unsafe_allow_html=True)
    st.code(c.code, language=None)
    o1, o2 = st.columns([2, 1], vertical_alignment="bottom")
    o1.text_input(L("Open a portfolio with its code", "افتح محفظة برمزها"), key="pf_code_in", placeholder=L("Paste a code", "الصق الرمز"))
    if o2.button(L("Open", "افتح"), icon=":material/login:", key="pf_code_go", width="stretch"):
        v = str(ss.get("pf_code_in") or "").strip()
        if not _CODE.match(v):
            st.error(L("That isn't a portfolio code.", "هذا مو رمز محفظة."))
        else:
            try:
                _, row = PF.load(key_of(v))
            except PB.StoreError:
                row = "?"
            if row is None:
                st.error(L("No portfolio has this code yet.", "ما فيه محفظة بهالرمز."))
            else:
                ss["pf_vid"] = v
                ss["pf_flash"] = L("Your portfolio is open on this device", "انفتحت محفظتك على هالجهاز")
                st.rerun()


# =====================================================================
# the positions and the orders
# =====================================================================
def _protection(c, sym, side):
    """The stop / target / trailing orders working on a position."""
    out = []
    for o in c.state["orders"]:
        if o["sym"] != sym or o["status"] != "open" or o["side"] not in ("sell", "cover"):
            continue
        if o["type"] == "stop":
            out.append(f'<span class="sl">{L("SL", "وقف")} {_bdi(_m(o["stop"]))}</span>')
        elif o["type"] == "limit":
            out.append(f'<span class="tp">{L("TP", "هدف")} {_bdi(_m(o["limit"]))}</span>')
        elif o["type"] == "trail":
            out.append(f'<span class="sl">{L("Trail", "متحرك")} {_bdi(_p(o["trail"], 1, False))}</span>')
    if not out:
        out.append(f'<span class="no">{L("No stop", "بدون وقف")}</span>' if side == "short" else f'<span>{L("None", "لا يوجد")}</span>')
    return f'<span class="prot">{"".join(out)}</span>'


def positions_html(c):
    v = c.view
    pos = v["positions"]
    if not pos:
        return empty("inventory_2", L("No open positions", "ما فيه مراكز مفتوحة"),
                     L("Open the Trade page to buy a stock, or sell one short if you expect it to fall.",
                       "افتح صفحة التداول واشترِ سهم، أو بعه على المكشوف إذا تتوقع ينزل."))
    try:
        lg = data.logos([p["sym"] for p in pos])
    except Exception:
        lg = {}
    head = [L("Symbol", "الرمز"), L("Side", "الاتجاه"), L("Shares", "الأسهم"), L("Avg cost", "متوسط التكلفة"), L("Price", "السعر"),
            L("Market value", "القيمة السوقية"), L("Unrealized P&L", "الربح غير المحقق"), L("Today", "اليوم"), L("Weight", "الوزن"),
            L("Trend", "الاتجاه"), L("Protection", "الحماية"), L("Held", "المدة")]
    num = {2, 3, 4, 5, 6, 7}
    th = "".join(f'<th class="{"r" if i in num else ""}">{T.esc(h)}</th>' for i, h in enumerate(head))
    rows = []
    for p in pos:
        sd = "long" if p["qty"] > 0 else "short"
        side_b = f'<span class="sd {sd}">{L("LONG", "شراء") if sd == "long" else L("SHORT", "مكشوف")}</span>'
        days = (pd.Timestamp.now(tz="UTC") - pd.Timestamp(PF.parse(p["opened"]))).days if p.get("opened") else 0
        held = L(f"{days} d", f"{days} يوم")
        cls_u = "up" if p["upnl"] > 0 else "dn" if p["upnl"] < 0 else ""
        cls_d = "up" if p["day_pnl"] > 0 else "dn" if p["day_pnl"] < 0 else ""
        extra = ""
        if sd == "short" and p.get("borrow"):
            extra = f'<span class="sub">{L("Borrow fees", "رسوم الاقتراض")} <span class="n">{_m(-p["borrow"])}</span></span>'
        rows.append(
            f'<tr><td><a class="as" href="{T.esc(ui.href(p["sym"]))}" target="_self">{T.logo_circle(p["sym"], lg.get(p["sym"]), 24)}<b>{T.esc(p["sym"])}</b></a></td>'
            f'<td>{side_b}</td><td class="r"><span class="n">{abs(p["qty"]):,.0f}</span></td><td class="r"><span class="n">{_m(p["avg"])}</span></td>'
            f'<td class="r"><span class="n">{_m(p["last"])}</span><span class="sub n {cls_d}">{_p(p["day_pct"])}</span></td>'
            f'<td class="r"><span class="n">{_m(p["mv"], 0)}</span></td>'
            f'<td class="r"><span class="n {cls_u}">{_m(p["upnl"], 2, True)}</span><span class="sub n {cls_u}">{_p(p["upnl_pct"])}</span>{extra}</td>'
            f'<td class="r"><span class="n {cls_d}">{_m(p["day_pnl"], 0, True)}</span></td>'
            f'<td><span class="wb{" s" if sd == "short" else ""}"><i style="width:{min(p["weight"], 100):.0f}%"></i></span><span class="n">{p["weight"]:.1f}%</span></td>'
            f'<td>{_mini(_trend(c, p["sym"]))}</td><td>{_protection(c, p["sym"], sd)}</td><td>{T.esc(held)}</td></tr>')
    n_l = sum(1 for p in pos if p["qty"] > 0)
    n_s = len(pos) - n_l
    u = v["unrealized"]
    sums = (ui.table_chip(L("Long", "شراء"), f"<b>{n_l}</b>") + ui.table_chip(L("Short", "مكشوف"), f"<b>{n_s}</b>")
            + ui.table_chip(L("Unrealized", "غير محقق"), T.pbox(_m(u, 0, True), u)))
    return (f'<div class="pfpos"><div class="hd"><div class="tt">{T.icon("inventory_2")}{L("Open positions", "المراكز المفتوحة")}</div>'
            f'<div class="sum">{sums}</div></div><div class="sc"><table><thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table></div></div>')


def order_card(o):
    lab, k, ic = _side(o["side"])
    st_en, st_ar, st_k = STATUS[o["status"]]
    extra = ""
    if o.get("sl") or o.get("tp"):
        parts = []
        if o.get("sl"):
            parts.append(f'{L("stop loss", "وقف خسارة")} {_bdi(_m(o["sl"]))}')
        if o.get("tp"):
            parts.append(f'{L("take profit", "جني أرباح")} {_bdi(_m(o["tp"]))}')
        extra = " · " + " · ".join(parts)
    if o.get("parent"):
        extra += " · " + L("bracket leg", "جزء من أمر مرفق")
    when = _ago(o.get("filled_at") or o["placed"])
    fill = f' · {L("at", "بسعر")} {_bdi(_m(o["fill_px"]))}' if o.get("fill_px") else ""
    note = f' · {T.esc(L(*NOTE[o["note"]]))}' if o.get("note") in NOTE else ""
    memo = f'<div class="memo">{T.icon("edit_note")}{T.esc(o["note_user"])}</div>' if o.get("note_user") else ""
    qn = _bdi(f"{int(o['qty']):,}")
    return (f'<div class="pfo"><div class="ic {k}">{T.icon(ic)}</div><div class="tx"><div class="t1">{T.esc(lab)} {qn} '
            f'<b>{T.esc(o["sym"])}</b> {T.badge(L(st_en, st_ar), st_k)}</div>'
            f'<div class="t2">{_otext(o)}{extra}{fill}{note} · {T.esc(when)}</div>{memo}</div></div>')


def open_orders(c, sym=None, key="pfo", limit=12):
    live = [o for o in c.state["orders"] if o["status"] == "open" and (sym is None or o["sym"] == sym)]
    live.sort(key=lambda o: o["placed"], reverse=True)
    if not live:
        st.markdown(empty("pending_actions", L("No working orders", "ما فيه أوامر قيد التنفيذ"),
                          L("Limit, stop and trailing orders wait here until they fill, expire or you cancel them.",
                            "الأوامر المحددة والوقف والمتحرك تنتظر هنا لين تتنفذ أو تنتهي مدتها أو تلغيها.")), unsafe_allow_html=True)
        return
    for o in live[:limit]:
        a, b = st.columns([6, 1.1], vertical_alignment="center")
        a.markdown(order_card(o), unsafe_allow_html=True)
        if c.can_trade and b.button(L("Cancel", "إلغاء"), key=f"{key}_cx_{o['id']}", icon=":material/close:", width="stretch"):
            PF.cancel(c.state, o["id"])
            commit(c, L(f"Order #{o['id']} cancelled", f"تم إلغاء الأمر رقم {o['id']}"))


def activity_html(c, n=8):
    fills = sorted(c.state["fills"], key=lambda f: (f["time"], f["id"]), reverse=True)[:n]
    if not fills:
        return empty("history", L("No trades yet", "ما فيه صفقات للحين"), L("Your fills will show here.", "تنفيذات أوامرك بتظهر هنا."))
    memo = {o["id"]: o.get("note_user") for o in c.state["orders"] if o.get("note_user")}
    out = []
    for f in fills:
        lab, k, _ = _side(f["side"])
        cls = "dn" if f["side"] == "sell" else "sh" if f["side"] == "short" else ""
        qn = _bdi(f"{int(f['qty']):,}")
        m_ = memo.get(f.get("order"))
        mh = f'<div class="memo">{T.icon("edit_note")}{T.esc(m_)}</div>' if m_ else ""
        out.append(f'<div class="it {cls}"><div class="a">{T.esc(lab)} {qn} <b>{T.esc(f["sym"])}</b> '
                   f'{L("at", "بسعر")} {_bdi(_m(f["px"]))} · {_bdi(_m(f["qty"] * f["px"], 0))}</div>'
                   f'<div class="w">{T.esc(_when(f["time"]))} · {T.esc(_ago(f["time"]))}</div>{mh}</div>')
    return f'<div class="pfact">{"".join(out)}</div>'


# =====================================================================
# charts
# =====================================================================
@st.cache_data(ttl=900, show_spinner=False)
def _spy(start):
    d = data.history("SPY", "5y")
    if d is None or d.empty:
        return pd.Series(dtype=float)
    s = d["Close"].copy()
    s.index = pd.to_datetime(s.index).tz_localize(None) if getattr(s.index, "tz", None) is not None else pd.to_datetime(s.index)
    s.index = s.index.normalize()
    return s[s.index >= pd.Timestamp(start) - pd.Timedelta(days=7)]


def bench(view):
    curve = view["curve"]
    if not len(curve):
        return pd.Series(dtype=float)
    s = _spy(str(curve.index[0].date()))
    return s.reindex(curve.index).ffill() if len(s) else s


def equity_fig(view, rng="all"):
    curve = view["curve"]
    eq = curve["equity"].copy()
    flows = curve["flow"].cumsum()
    b = bench(view)
    if rng != "all" and len(eq):
        end = eq.index[-1]
        start = {"1m": end - pd.Timedelta(days=31), "3m": end - pd.Timedelta(days=92), "1y": end - pd.Timedelta(days=366),
                 "ytd": pd.Timestamp(end.year, 1, 1)}.get(rng, eq.index[0])
        keep = eq.index >= start
        eq, flows = eq[keep], flows[keep]
        b = b[b.index >= start] if len(b) else b
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.72, 0.28])
    tr = go.Scatter(x=eq.index, y=eq, name=L("Portfolio", "المحفظة"), line=dict(color=C.CYAN, width=2.6), fill="tozeroy",
                    hovertemplate="%{x|%b %d, %Y}: $%{y:,.0f}<extra></extra>")
    try:
        tr.fillgradient = dict(type="vertical", colorscale=[[0, C.rgba(C.CYAN, 0.0)], [1, C.rgba(C.CYAN, 0.26)]])
    except (ValueError, AttributeError):
        tr.fillcolor = C.rgba(C.CYAN, 0.12)
    fig.add_trace(tr, 1, 1)
    same = None
    if len(b.dropna()) >= 2 and len(eq):
        bb = b.reindex(eq.index).ffill().bfill()
        base = float(eq.iloc[0]) - float(flows.iloc[0])
        same = bb / float(bb.iloc[0]) * base + (flows - float(flows.iloc[0]))
        fig.add_trace(go.Scatter(x=same.index, y=same, name=L("Same money in the S&P 500", "نفس المبلغ في S&P 500"),
                                 line=dict(color=C.GOLD, width=1.7, dash="dot"), hovertemplate="%{x|%b %d, %Y}: $%{y:,.0f}<extra></extra>"), 1, 1)
    idx = (1 + PF.daily_returns(curve.loc[eq.index] if len(eq) else curve)).cumprod()
    dd = (idx / idx.cummax() - 1) * 100 if len(idx) else pd.Series(dtype=float)
    fig.add_trace(go.Scatter(x=dd.index, y=dd, name=L("Drawdown %", "الهبوط %"), fill="tozeroy", line=dict(color=C.DOWN, width=1),
                             fillcolor=C.rgba(C.DOWN, 0.22), hovertemplate="%{x|%b %d}: %{y:.1f}%<extra></extra>"), 2, 1)
    ys = [float(x) for x in eq.values] + ([float(x) for x in same.values if x == x] if same is not None else [])
    lo, hi = (min(ys), max(ys)) if ys else (0, 1)
    pad = max((hi - lo) * 0.12, hi * 0.004, 1)
    fig.update_yaxes(range=[lo - pad, hi + pad], tickprefix="$", row=1, col=1)
    fig.update_yaxes(ticksuffix="%", row=2, col=1)
    return C.style(fig, 430, L("Account value vs the S&P 500", "قيمة الحساب مقابل S&P 500"))


def exposure_fig(c):
    v, a = c.view, c.acct
    eq = max(a["equity"], 1e-9)
    labels = [L("Long", "شراء"), L("Short", "مكشوف"), L("Net", "الصافي"), L("Gross", "الإجمالي")]
    vals = [a["lmv"] / eq * 100, -a["smv"] / eq * 100, a["net"] / eq * 100, a["gross"] / eq * 100]
    fill, line, txt, out = C.pastel(vals)
    fig = go.Figure(go.Bar(x=vals, y=labels, orientation="h", marker=dict(color=fill, line=dict(color=line, width=1)),
                           text=[f"{x:+.0f}%" for x in vals], textposition="outside", textfont=dict(color=C.MUTED),
                           hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
    fig.add_vline(x=0, line=dict(color="#3A3545", width=1))
    C.style(fig, 260, L("Exposure (% of equity)", "الانكشاف (% من قيمة الحساب)"), legend=False)
    lo, hi = min(vals + [0]), max(vals + [0])
    span = max(hi - lo, 10)
    fig.update_xaxes(ticksuffix="%", zeroline=False, range=[lo - span * 0.22 if lo < 0 else -span * 0.04, hi + span * 0.2])
    fig.update_layout(margin=dict(l=70, r=20))
    fig.update_yaxes(side="left", autorange="reversed")
    return C._bars(fig)


def _sector(sym):
    try:
        if PB.sector_of(sym):
            return PB.sector_of(sym)
    except Exception:
        pass
    try:
        return data.info(sym).get("sector") or L("Other", "أخرى")
    except Exception:
        return L("Other", "أخرى")


def sector_fig(c):
    rows = {}
    for p in c.view["positions"]:
        s = _sector(p["sym"])
        r = rows.setdefault(s, [0.0, 0.0])
        r[0 if p["qty"] > 0 else 1] += abs(p["mv"])
    if not rows:
        return None
    names = sorted(rows, key=lambda s: -(rows[s][0] + rows[s][1]))[:10]
    lab = [sector_name(s) if s else s for s in names]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=lab, x=[rows[s][0] for s in names], name=L("Long", "شراء"), orientation="h",
                         marker=dict(color=C.rgba(C.UP, 0.75), line=dict(color=C.UP, width=1)), hovertemplate="%{y}: $%{x:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(y=lab, x=[-rows[s][1] for s in names], name=L("Short", "مكشوف"), orientation="h",
                         marker=dict(color=C.rgba(C.ORANGE, 0.75), line=dict(color=C.ORANGE, width=1)), customdata=[rows[s][1] for s in names],
                         hovertemplate="%{y}: -$%{customdata:,.0f}<extra></extra>"))
    C.style(fig, 300, L("Sectors: long vs short", "القطاعات: شراء مقابل مكشوف"))
    fig.update_layout(barmode="relative", bargap=0.3)
    fig.add_vline(x=0, line=dict(color="#3A3545", width=1))
    fig.update_xaxes(tickprefix="$")
    fig.update_yaxes(side="left", autorange="reversed")
    return C._bars(fig)


def alloc_fig(c):
    pos = c.view["positions"]
    if not pos:
        return None
    labels = [p["sym"] + (" ▼" if p["qty"] < 0 else "") for p in pos[:9]]
    vals = [abs(p["mv"]) for p in pos[:9]]
    if len(pos) > 9:
        labels.append(L("Others", "أخرى"))
        vals.append(sum(abs(p["mv"]) for p in pos[9:]))
    if c.acct["cash"] > 0 and c.acct["smv"] == 0:
        labels.append(L("Cash", "الكاش"))
        vals.append(c.acct["cash"])
    return C.share_donut(labels, vals, L("Where the money is (▼ = short)", "وين الفلوس (▼ = مكشوف)"),
                         center=f"<b>{len(pos)}</b><br>{L('positions', 'مراكز')}")


# =====================================================================
# DASHBOARD
# =====================================================================
def page_dashboard():
    ui.html(CSS)
    c = ctx()
    _flash()
    ui.html(hero(c))
    access_bar(c)
    a, v = c.acct, c.view
    if a["margin_call"]:
        st.error(L(f"Margin call: equity {_m(a['equity'], 0)} is under the maintenance requirement {_m(a['maint'], 0)}. "
                   "Close or cover positions (a real broker would start closing them for you).",
                   f"نداء هامش: قيمة الحساب {_m(a['equity'], 0)} أقل من الحد الأدنى المطلوب {_m(a['maint'], 0)}. "
                   "سكّر أو غطِّ مراكز (الوسيط الحقيقي يبدأ يسكّرها عنك)."), icon=":material/warning:")
    st_ = PF.stats(v, bench(v))
    used = a["used"]
    used_col = T.POS_FG if used < 50 else T.GOLD if used < 80 else T.NEG_FG
    bret = st_.get("bench_ret")
    vs = f'{L("S&P 500", "S&P 500")} <b>{_p(bret)}</b>' if bret is not None else L("since the first session", "من أول جلسة")
    n_l = sum(1 for p in v["positions"] if p["qty"] > 0)
    n_s = len(v["positions"]) - n_l
    n_open = sum(1 for o in c.state["orders"] if o["status"] == "open")
    ui.html(kpis([
        ("account_balance", L("Equity", "قيمة الحساب"), _m(a["equity"]), f'{L("Started with", "بدأ بـ")} <b>{_m(v["invested"], 0)}</b>', None, None),
        ("today", L("P&L · ", "الربح · ") + day_label(v), _m(v["day_pnl"], 2, True), f'<b>{_p(v["day_pct"])}</b>', _k(v["day_pnl"]), None),
        ("show_chart", L("Total return", "العائد الكلي"), _p(st_.get("twr", v["ret"])), vs, _k(st_.get("twr", v["ret"])), None),
        ("bolt", L("Buying power", "القوة الشرائية"), _m(a["bp_long"], 0),
         f'{L("Short", "للمكشوف")} <b>{_m(a["bp_short"], 0)}</b> · {L("cash", "كاش")} <b>{_m(a["cash"], 0)}</b>', None, None),
        ("shield", L("Margin used", "الهامش المستخدم"), _p(used, 1, False),
         f'{L("Cushion", "الهامش الآمن")} <b>{_p(a["cushion"], 1, False)}</b>', None, (used, used_col)),
        ("inventory_2", L("Positions", "المراكز"), f"{len(v['positions'])}",
         f'{L("Long", "شراء")} <b>{n_l}</b> · {L("Short", "مكشوف")} <b>{n_s}</b> · {L("orders", "أوامر")} <b>{n_open}</b>', None, None),
    ]))
    ui.sec("health_and_safety", "Portfolio health", "صحة المحفظة")
    ui.html(health_html(health_of(c, st_), badges_of(c, st_)))
    ui.sec("monitoring", "Performance", "الأداء")
    if len(v["curve"]) >= 2:
        rng = st.segmented_control(L("Range", "المدة"), ["1m", "3m", "ytd", "1y", "all"], default="all", key="pf_rng", label_visibility="collapsed",
                                   format_func=lambda k: {"1m": L("1M", "شهر"), "3m": L("3M", "3 أشهر"), "ytd": L("YTD", "من بداية السنة"),
                                                          "1y": L("1Y", "سنة"), "all": L("All", "الكل")}[k]) or "all"
        ui.chart(equity_fig(v, rng), key="pf_eq")
    else:
        ui.html(empty("insights", L("The chart starts after the first session", "الرسم يبدأ بعد أول جلسة"),
                      L("The account value is recorded at every close; come back after the market closes.",
                        "قيمة الحساب تنسجل مع كل إغلاق، ارجع بعد ما يسكّر السوق.")))
    ui.sec("inventory_2", "Positions", "المراكز")
    ui.html(positions_html(c))
    if v["positions"] and c.can_trade:
        quick_actions(c)
    if v["positions"]:
        ui.sec("grid_view", "Holdings map", "خريطة المراكز")
        holdings_map(c)
        g1, g2 = st.columns([1, 1])
        with g1:
            ui.chart(exposure_fig(c), key="pf_expo")
        with g2:
            fig = sector_fig(c)
            if fig:
                ui.chart(fig, key="pf_sect")
    o1, o2 = st.columns([1.35, 1])
    with o1:
        ui.sec("pending_actions", "Working orders", "الأوامر قيد التنفيذ")
        open_orders(c, key="pfd")
    with o2:
        ui.sec("history", "Recent activity", "آخر النشاطات")
        ui.html(activity_html(c))
    if c.can_trade:
        settings_box(c)
    ui.foot()


def health_html(h, bdg=None):
    """The health card: the score ring (it fills up as the page opens), the five factors with a bar each, the next steps, and
    a strip of the achievements (lit when earned)."""
    sc = h["score"]
    col = (lambda x: T.POS_FG if x >= 75 else "#2DB6EB" if x >= 55 else T.GOLD if x >= 40 else T.NEG_FG)
    r, circ = 52, 2 * math.pi * 52
    if sc is None:
        ring_c, glow, val, num = "#9D97A5", "rgba(157,151,165,.18)", 0.0, "—"
        gr = f'<div class="gr">{T.esc(L("Not rated yet", "بدون تقييم للحين"))}</div>'
    else:
        ring_c = col(sc)
        glow = C.rgba(ring_c, 0.22) if ring_c.startswith("#") else "rgba(45,182,235,.2)"
        val, num = sc / 100, f"{sc}"
        gr = f'<div class="gr"><i>{T.esc(h["grade"])}</i>{T.esc(L(*h["name"]))}</div>'
    off = circ * (1 - val)
    ring = (f'<div class="ring"><svg viewBox="0 0 120 120"><defs><linearGradient id="pfhg" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{ring_c}"/><stop offset="1" stop-color="#7B45F0"/></linearGradient></defs>'
            f'<circle class="tr" cx="60" cy="60" r="{r}"/>'
            f'<circle class="vl" cx="60" cy="60" r="{r}" stroke="url(#pfhg)" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{off:.1f}" '
            f'style="--c0:{circ:.1f}"/></svg><div class="num"><b>{num}</b><span>/ 100</span></div></div>')
    cap = L("Diversification, concentration, stops, risk and the result against the market, scored together.",
            "التنويع والتركيز والوقف والمخاطرة والأداء مقابل السوق، في تقييم واحد.")
    left = (f'<div class="sc" style="--hg:{glow};--hc:{glow};--hc2:{ring_c}">{ring}{gr}<div class="cap">{T.esc(cap)}</div></div>')
    rows = []
    for f in h["factors"]:
        v = f["score"]
        bar = (f'<div class="bar"><i style="width:{max(v, 3):.0f}%;background:linear-gradient(90deg,{col(v)},{C.rgba(col(v), .55) if col(v).startswith("#") else col(v)})"></i></div>'
               if v is not None else '<div class="bar"></div>')
        b = f'<b>{v:.0f}</b>' if v is not None else f'<b class="na">{T.esc(L("n/a", "—"))}</b>'
        rows.append(f'<div class="f"><div class="t">{T.icon(f["icon"])}{T.esc(L(*f["name"]))}{b}</div>{bar}'
                    f'<div class="d">{T.esc(L(*f["detail"]))}</div></div>')
    mid = f'<div><div class="hd">{T.icon("analytics")}{T.esc(L("What makes the score", "مكونات التقييم"))}</div>{"".join(rows)}</div>'
    tips = "".join(f'<div class="tip {t["kind"]}">{T.icon(t["icon"])}<p>{T.esc(L(*t["text"]))}</p></div>' for t in h["tips"])
    strip = ""
    if bdg:
        n_on = sum(1 for b in bdg if b["earned"])
        dots = "".join(f'<span class="b{" on" if b["earned"] else ""}" title="{T.esc(L(*b["name"]))}">{T.icon(b["icon"])}</span>' for b in bdg)
        strip = (f'<div class="bdg"><span>{T.esc(L("Achievements", "الإنجازات"))} <b>{n_on}</b> / {len(bdg)}</span><div class="row">{dots}</div>'
                 f'<span>{T.esc(L("all of them on the Analytics page", "كلها في صفحة التحليلات"))}</span></div>')
    right = f'<div class="tips"><div class="hd">{T.icon("tips_and_updates")}{T.esc(L("Next steps", "الخطوات الجاية"))}</div>{tips}{strip}</div>'
    return f'<div class="pfhs">{left}{mid}{right}</div>'


def health_of(c, stats):
    import pfinsight as PI
    return PI.health(c.view, c.acct, stats, c.state["orders"], _sector, sec_name=sector_name)


def badges_of(c, stats):
    import pfinsight as PI
    return PI.badges(c.view, stats, c.state, _sector)


def achievements_html(bdg):
    """The achievements wall: earned medals lit (gold), the others with how far along they are."""
    n_on = sum(1 for b in bdg if b["earned"])
    pct = n_on / max(len(bdg), 1) * 100
    tiles = []
    for b in sorted(bdg, key=lambda b: (not b["earned"], -b["prog"])):
        tiles.append(f'<div class="a{" on" if b["earned"] else ""}"><div class="md">{T.icon(b["icon"] if b["earned"] else "lock")}</div>'
                     f'<div class="t">{T.esc(L(*b["name"]))}</div><div class="d">{T.esc(L(*b["desc"]))}</div>'
                     f'<div class="pb"><i style="width:{b["prog"] * 100:.0f}%"></i></div><div class="pt">{T.esc(L(*b["txt"]))}</div></div>')
    head = (f'<div class="top">{T.icon("military_tech")}<span><b>{n_on}</b> / {len(bdg)} {T.esc(L("earned", "محققة"))}</span>'
            f'<div class="tb"><i style="width:{pct:.0f}%"></i></div></div>')
    return f'<div class="pfach">{head}<div class="gr">{"".join(tiles)}</div></div>'


def calendar_html(c, n_months=3):
    """The P&L calendar: the last months, one card each, a cell per session coloured by the day's profit or loss."""
    import calendar as _cal
    import pfinsight as PI
    d = PI.pnl_days(c.view["curve"], c.state["start_cash"])
    if d.empty:
        return None
    first_d, last_d = d.index.min().date(), d.index.max().date()
    mx = float(d.abs().max()) or 1.0
    wds = [L("Mon", "إثنين"), L("Tue", "ثلاثاء"), L("Wed", "أربعاء"), L("Thu", "خميس"), L("Fri", "جمعة")]
    months_en = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    cards = []
    for y, m in sorted({(t.year, t.month) for t in d.index})[-n_months:]:
        sub = d[(d.index.year == y) & (d.index.month == m)]
        by = {t.date(): float(v) for t, v in sub.items()}
        tot = float(sub.sum())
        up, dn = int((sub > 0).sum()), int((sub < 0).sum())
        cells = [f'<div class="wd">{T.esc(w)}</div>' for w in wds]
        start = date(y, m, 1)
        start -= timedelta(days=start.weekday())                   # the Monday of the first week
        end = date(y, m, _cal.monthrange(y, m)[1])
        day = start
        while day <= end:
            if day.weekday() < 5:
                if day.month != m:
                    cells.append('<div class="c x"></div>')
                elif day in by:
                    v = by[day]
                    a = 0.16 + 0.6 * min(abs(v) / mx, 1.0)
                    bg = f"rgba(34,197,94,{a:.2f})" if v > 0 else f"rgba(239,68,68,{a:.2f})" if v < 0 else "rgba(157,151,165,.14)"
                    cells.append(f'<div class="c" style="background:{bg};border-color:transparent" title="{day.isoformat()} · {_m(v, 2, True)}">'
                                 f'<i>{day.day}</i><em>{PI.short_money(v)}</em></div>')
                elif first_d <= day <= last_d:
                    cells.append(f'<div class="c h" title="{T.esc(L("Market closed", "السوق مقفل"))}"><i>{day.day}</i><em>·</em></div>')
                else:
                    cells.append(f'<div class="c h"><i>{day.day}</i><em></em></div>')
            day += timedelta(days=1)
        name = (MONTHS_AR[m - 1] if is_ar() else months_en[m - 1]) + f" {y}"
        col = T.POS_FG if tot > 0 else T.NEG_FG if tot < 0 else _MU
        cards.append(f'<div class="m"><div class="mh"><b>{T.esc(name)}</b><span style="color:{col}">{_m(tot, 0, True)}</span></div>'
                     f'<div class="ms2">{T.esc(L(f"{up} up · {dn} down", f"{up} صاعد · {dn} نازل"))}</div><div class="g">{"".join(cells)}</div></div>')
    lg = (f'<div class="pflg"><span style="background:rgba(239,68,68,.7)"></span>{T.esc(L("loss", "خسارة"))}'
          f'<span style="background:rgba(157,151,165,.14)"></span>{T.esc(L("flat / closed", "ثابت / مقفل"))}'
          f'<span style="background:rgba(34,197,94,.7)"></span>{T.esc(L("profit", "ربح"))} · {T.esc(L("darker = bigger day", "اللون الأغمق = يوم أكبر"))}</div>')
    return f'<div class="pfcal">{"".join(cards)}</div>{lg}'


def holdings_map(c):
    """The positions as a heat map: each tile sized by its money, coloured by its result (since bought or today); longs and
    shorts in their own groups. A tile opens the stock."""
    import heatmap as HM
    pos = c.view["positions"]
    mode = st.segmented_control(L("Colour by", "اللون حسب"), ["total", "today"], default="total", key="pf_hm_mode", label_visibility="collapsed",
                                format_func=lambda k: L("Since bought", "من الشراء") if k == "total" else L("Today", "اليوم")) or "total"
    rows = []
    for p in pos:
        sgn = 1 if p["qty"] > 0 else -1
        val = p["upnl_pct"] if mode == "total" else p["day_pct"] * sgn
        rows.append({"Symbol": p["sym"], "Group": "long" if sgn > 0 else "short", "Size": abs(p["mv"]), "Val": val,
                     "P&L": p["upnl"] if mode == "total" else p["day_pnl"], "W": p["weight"]})
    df = pd.DataFrame(rows)
    rng = 20.0 if mode == "total" else 3.0
    W_, H_ = 1200, 520 if len(pos) > 3 else 380
    tiles, groups = HM.layout(df, "Group", "Size", W_, H_)
    try:
        lg = {k: u for k, u in data.logos([t["Symbol"] for t in tiles]).items() if u}
    except Exception:
        lg = {}
    label = lambda g: L("Long", "شراء") if g == "long" else L("Short ▼", "مكشوف ▼")

    def tip(t):
        side = L("long", "شراء") if t["Group"] == "long" else L("short", "مكشوف")
        return f'{t["Symbol"]} · {side} · {t["Val"]:+.2f}% · {_m(t["P&L"], 0, True)} · {t["W"]:.1f}%'
    ui.html('<div class="pfmap">' + HM.render(tiles, groups, lg, rng, "ar" if is_ar() else "en", label, tip, rtl=is_ar(), width=W_, height=H_, uid="pfm")
            + "</div>" + HM.legend(rng))
    best = max(pos, key=lambda p: p["upnl_pct"] if mode == "total" else p["day_pct"] * (1 if p["qty"] > 0 else -1))
    worst = min(pos, key=lambda p: p["upnl_pct"] if mode == "total" else p["day_pct"] * (1 if p["qty"] > 0 else -1))
    if len(pos) > 1:
        bv = best["upnl_pct"] if mode == "total" else best["day_pct"] * (1 if best["qty"] > 0 else -1)
        wv = worst["upnl_pct"] if mode == "total" else worst["day_pct"] * (1 if worst["qty"] > 0 else -1)
        ui.html(f'<div class="pfmapcap"><span>{T.esc(L("Size = money in the position · colour = its result", "الحجم = فلوس المركز · اللون = نتيجته"))}</span>'
                f'<span>{T.esc(L("Best", "الأفضل"))} <b style="color:{_col(bv)}">{T.esc(best["sym"])} {_bdi(_p(bv))}</b> · '
                f'{T.esc(L("Weakest", "الأضعف"))} <b style="color:{_col(wv)}">{T.esc(worst["sym"])} {_bdi(_p(wv))}</b></span></div>')


def _col(v):
    return T.POS_FG if v > 0 else T.NEG_FG if v < 0 else _MU


def _mini(vals, w=96, h=28):
    """A small trend line for a position (its last month of closes), filled under the line."""
    vals = [float(x) for x in vals if x == x]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or max(abs(hi) * 0.01, 1e-6)
    pts = [(i / (len(vals) - 1) * w, h - 3 - (v - lo) / span * (h - 6)) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    col = "#34D27A" if vals[-1] >= vals[0] else "#F26B6B"
    return (f'<svg class="spk" viewBox="0 0 {w} {h}" preserveAspectRatio="none"><polygon points="0,{h} {line} {w},{h}" fill="{col}" fill-opacity=".14"/>'
            f'<polyline points="{line}" fill="none" stroke="{col}" stroke-width="1.6" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
            f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="2.2" fill="{col}"/></svg>')


def _trend(c, sym):
    """The last ~month of closes of a held stock (the same daily prices the account is built from)."""
    try:
        fills = c.state["fills"]
        first = min([PF.et_date(c.state["created"])] + [PF.et_date(f["time"]) for f in fills])
        d = c.mkt.daily(sym, (first - timedelta(days=7)).isoformat())
        return list(d["Close"].tail(22)) if d is not None and len(d) else []
    except Exception:
        return []


def quick_actions(c):
    """One position picked, one tap: close it, close half, protect it, or open the ticket."""
    pos = c.view["positions"]
    syms = [p["sym"] for p in pos]
    by = {p["sym"]: p for p in pos}
    with st.container(key="pfbar_quick"):
        a, b = st.columns([1.2, 2], vertical_alignment="bottom")
        ui.valid("pf_qsym", syms)
        sym = a.selectbox(L("Quick action on", "إجراء سريع على"), syms, key="pf_qsym",
                          format_func=lambda s: f"{s} · {L('LONG', 'شراء') if by[s]['qty'] > 0 else L('SHORT', 'مكشوف')} {abs(by[s]['qty']):,.0f}")
        p = by.get(sym)
        if not p:
            return
        short = p["qty"] < 0
        x1, x2, x3, x4 = b.columns(4)
        try:
            if x1.button(L("Cover all", "غطِّ الكل") if short else L("Sell all", "بع الكل"), key="pf_q_all", icon=":material/close_fullscreen:", width="stretch"):
                o = PF.close_position(c.state, c.view, c.mkt, sym)
                commit(c, _done(o))
            if x2.button(L("Close half", "سكّر النص"), key="pf_q_half", icon=":material/vertical_align_center:", width="stretch",
                         disabled=abs(p["qty"]) < 2):
                o = PF.close_position(c.state, c.view, c.mkt, sym, qty=int(abs(p["qty"]) // 2))
                commit(c, _done(o))
            if x3.button(L("Trail 5%", "متحرك 5%"), key="pf_q_trail", icon=":material/shield:", width="stretch"):
                o = PF.place(c.state, c.view, c.mkt, {"sym": sym, "side": "cover" if short else "sell", "qty": int(abs(p["qty"])), "type": "trail",
                                                     "trail": 5.0, "tif": "gtc"})
                commit(c, _done(o))
        except PF.OrderError as e:
            st.error(_err(e))
        if x4.button(L("Trade", "تداول"), key="pf_q_trade", icon=":material/swap_horiz:", width="stretch"):
            ss["pf_sym"] = sym
            ui.goto("pf_trade")


def _done(o):
    lab, _, _ = _side(o["side"])
    if o["status"] == "filled":
        return L(f"{lab} {o['filled_qty']:,} {o['sym']} at ${o['fill_px']:,.2f}", f"{lab} {o['filled_qty']:,} {o['sym']} بسعر {o['fill_px']:,.2f}$")
    if o["status"] == "rejected":
        return L(f"Order rejected: {L(*NOTE.get(o.get('note'), ('', '')))}", f"الأمر مرفوض: {L(*NOTE.get(o.get('note'), ('', '')))}")
    return L(f"Order sent: {lab} {o['qty']:,} {o['sym']}", f"تم إرسال الأمر: {lab} {o['qty']:,} {o['sym']}")


def _err(e):
    msg = L(*ERR.get(e.code, ERR["bad"]))
    if e.code == "bp":
        msg += " " + L(f"At most {e.info.get('max_qty', 0):,} shares.", f"الحد الأقصى {e.info.get('max_qty', 0):,} سهم.")
    if e.code == "too_many":
        msg += " " + L(f"You hold {e.info.get('have', 0):,}.", f"عندك {e.info.get('have', 0):,}.")
    return msg


def settings_box(c):
    s = c.state["settings"]
    with st.expander(L("Account settings, deposits and reset", "إعدادات الحساب والإيداع وإعادة الضبط"), icon=":material/settings:"):
        if c.mode == "mine":
            code_box(c)
            st.divider()
        a, b, d = st.columns(3)
        lev = a.segmented_control(L("Leverage on longs", "الرافعة على الشراء"), [1.0, 2.0], default=float(s.get("leverage") or 1), key="pf_set_lev",
                                  format_func=lambda x: L("1× (cash)", "1× (كاش)") if x == 1 else L("2× (Reg T margin)", "2× (هامش Reg T)"))
        com = b.number_input(L("Commission per order ($)", "العمولة لكل أمر ($)"), 0.0, 50.0, float(s.get("commission") or 0), 0.5, key="pf_set_com")
        slp = d.number_input(L("Slippage (bps)", "الانزلاق (نقطة أساس)"), 0.0, 100.0, float(s.get("slippage_bps") or 0), 1.0, key="pf_set_slp")
        a2, b2, d2 = st.columns(3)
        bor = a2.number_input(L("Borrow fee for shorts (% / year)", "رسوم اقتراض المكشوف (% سنوياً)"), 0.0, 100.0, float(s.get("borrow_rate") or 0), 0.1,
                              key="pf_set_bor")
        mar = b2.number_input(L("Margin interest (% / year)", "فائدة الهامش (% سنوياً)"), 0.0, 30.0, float(s.get("margin_rate") or 0), 0.25, key="pf_set_mar")
        sho = d2.toggle(L("Allow short selling", "السماح بالبيع على المكشوف"), value=bool(s.get("allow_short", True)), key="pf_set_sho")
        if st.button(L("Save settings", "احفظ الإعدادات"), icon=":material/save:", key="pf_set_save"):
            s.update({"leverage": float(lev or 1), "commission": float(com), "slippage_bps": float(slp), "borrow_rate": float(bor),
                      "margin_rate": float(mar), "allow_short": bool(sho)})
            commit(c, L("Settings saved", "تم حفظ الإعدادات"))
        st.divider()
        f1, f2, f3 = st.columns([1.2, 1, 1], vertical_alignment="bottom")
        amt = f1.number_input(L("Amount ($)", "المبلغ ($)"), 0.0, 10_000_000.0, 10000.0, 1000.0, key="pf_flow_amt")
        try:
            if f2.button(L("Deposit", "إيداع"), icon=":material/add_card:", key="pf_dep", width="stretch"):
                PF.flow(c.state, "deposit", amt)
                commit(c, L(f"Deposited ${amt:,.0f}", f"تم إيداع {amt:,.0f}$"))
            if f3.button(L("Withdraw", "سحب"), icon=":material/payments:", key="pf_wd", width="stretch"):
                if amt > max(c.acct["excess"], 0):
                    st.error(L("You can only withdraw cash that isn't holding up your positions.", "تقدر تسحب بس الكاش اللي ما يغطي مراكزك."))
                else:
                    PF.flow(c.state, "withdraw", amt)
                    commit(c, L(f"Withdrew ${amt:,.0f}", f"تم سحب {amt:,.0f}$"))
        except PF.OrderError:
            st.error(L("Enter an amount above zero.", "اكتب مبلغ أكبر من صفر."))
        st.divider()
        r1, r2, r3 = st.columns([1.2, 1.2, 1], vertical_alignment="bottom")
        start = r1.number_input(L("Start again with ($)", "ابدأ من جديد بـ ($)"), 1000.0, 100_000_000.0, float(c.state.get("start_cash") or 100000), 10000.0,
                                key="pf_reset_cash")
        sure = r2.toggle(L("Yes, erase every order and trade", "أيوه، امسح كل الأوامر والصفقات"), key=f"pf_reset_ok_{c.state['created']}")
        if r3.button(L("Reset account", "إعادة ضبط الحساب"), icon=":material/restart_alt:", key="pf_reset", width="stretch", disabled=not sure):
            c.state.clear()
            c.state.update(PF.new_state(start, settings=s))
            commit(c, L("A fresh account is ready", "الحساب الجديد جاهز"))


# =====================================================================
# TRADE
# =====================================================================
POPULAR = ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "META", "SPY", "QQQ"]


def quote_card(sym, q, inf, held):
    price, prev = q
    chg = (price / prev - 1) * 100 if prev else 0.0
    name = inf.get("shortName") or inf.get("longName") or sym
    lo, hi = inf.get("dayLow"), inf.get("dayHigh")
    lo52, hi52 = inf.get("fiftyTwoWeekLow"), inf.get("fiftyTwoWeekHigh")

    def rng(a, b, label):
        if not a or not b or b <= a:
            return ""
        x = min(max((price - a) / (b - a) * 100, 0), 100)
        return (f'<div class="rng"><div class="lb"><span>{_m(a)}</span><span>{T.esc(label)}</span><span>{_m(b)}</span></div>'
                f'<div class="tr"><i style="left:{x:.1f}%"></i></div></div>')
    cells = []

    def cell(lab, val):
        cells.append(f'<div class="g"><div class="l">{T.esc(lab)}</div><div class="v"><span dir="ltr">{val}</span></div></div>')
    vol, avg = inf.get("volume") or inf.get("regularMarketVolume"), inf.get("averageVolume")
    if vol:
        cell(L("Volume", "الحجم"), T.fmt_big(vol) + (f' <span style="color:{_MU};font-size:.75rem">({vol / avg:.1f}×)</span>' if avg else ""))
    if inf.get("marketCap"):
        cell(L("Market cap", "القيمة السوقية"), T.fmt_big(inf["marketCap"]))
    if inf.get("beta") is not None:
        cell(L("Beta", "بيتا"), f'{float(inf["beta"]):.2f}')
    sp = inf.get("shortPercentOfFloat")
    if sp:
        cell(L("Short % of float", "نسبة المكشوف من الأسهم المتاحة"), f"{float(sp) * 100:.1f}%")
    if inf.get("shortRatio"):
        cell(L("Days to cover", "أيام التغطية"), f'{float(inf["shortRatio"]):.1f}')
    if inf.get("dividendYield"):
        dy = float(inf["dividendYield"])
        cell(L("Dividend yield", "عائد التوزيعات"), f"{dy if dy > 1 else dy * 100:.2f}%")
    hold = ""
    if held:
        hold = (f'<div style="margin-top:10px">{T.badge(L(f"You are long {held:,.0f}", f"عندك {held:,.0f} سهم") if held > 0 else L(f"You are short {-held:,.0f}", f"عليك {-held:,.0f} سهم مكشوف"), "pos" if held > 0 else "org", "inventory_2")}</div>')
    try:
        logo = T.logo_circle(sym, data.logos([sym]).get(sym), 44)
    except Exception:
        logo = T.logo_circle(sym, None, 44)
    return (f'<div class="pfq"><div class="row1">{logo}<div class="nm">{T.esc(sym)}<small>{T.esc(name)}</small></div>'
            f'<div class="px"><b>{_m(price)}</b>{T.pill(chg)}</div></div>{rng(lo, hi, L("Day range", "مدى اليوم"))}'
            f'{rng(lo52, hi52, L("52-week range", "مدى 52 أسبوع"))}<div class="grid">{"".join(cells)}</div>{hold}</div>')


def trade_chart(sym, c, spec=None, span="6mo"):
    """Price with your average cost and the prices of your orders on it."""
    if span == "1d":
        d = PF.Market().intraday(sym)
        if not d.empty:
            d = d[d.index.date == d.index[-1].date()]
        x = d.index if not d.empty else []
    else:
        d = data.history(sym, span)
        x = d.index if d is not None and not d.empty else []
    if d is None or d.empty:
        return None
    close = d["Close"]
    up = float(close.iloc[-1]) >= float(close.iloc[0])
    col = C.UP if up else C.DOWN
    fig = go.Figure()
    tr = go.Scatter(x=x, y=close, mode="lines", line=dict(color=col, width=2.2), fill="tozeroy", name=sym,
                    hovertemplate="%{x|%b %d %H:%M}: $%{y:,.2f}<extra></extra>" if span == "1d" else "%{x|%b %d, %Y}: $%{y:,.2f}<extra></extra>")
    try:
        tr.fillgradient = dict(type="vertical", colorscale=[[0, C.rgba(col, 0.0)], [1, C.rgba(col, 0.22)]])
    except (ValueError, AttributeError):
        tr.fillcolor = C.rgba(col, 0.1)
    fig.add_trace(tr)
    lines = []
    p = next((x_ for x_ in c.view["positions"] if x_["sym"] == sym), None)
    if p:
        lines.append((p["avg"], L("Your average", "متوسطك"), C.ACCENT))
    for o in c.state["orders"]:
        if o["sym"] == sym and o["status"] == "open":
            lvl = o.get("limit") or o.get("stop")
            if lvl:
                lines.append((lvl, f'{L(*TYPE[o["type"]])} #{o["id"]}', C.NEG_BD if o["type"] == "stop" else C.POS_BD))
    if spec:
        for k, lab, colr in (("sl", L("New stop loss", "وقف الخسارة الجديد"), C.NEG_BD), ("tp", L("New take profit", "جني الأرباح الجديد"), C.POS_BD),
                             ("limit", L("Limit", "المحدد"), C.GOLD), ("stop", L("Stop", "الوقف"), C.GOLD)):
            if spec.get(k):
                lines.append((spec[k], lab, colr))
    for lvl, lab, colr in lines:
        fig.add_hline(y=lvl, line=dict(color=colr, width=1.4, dash="dash"),
                      annotation=dict(text=f"{lab} ${lvl:,.2f}", font=dict(size=10, color=colr), bgcolor="rgba(14,9,24,.7)"),
                      annotation_position="top left")
    vals = list(close.values) + [l_[0] for l_ in lines]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.08 or hi * 0.02
    C.style(fig, 330, None, legend=False)
    fig.update_yaxes(range=[lo - pad, hi + pad], tickprefix="$")
    fig.update_layout(hovermode="x")
    return fig


def _actions(held):
    if held > 0:
        return ["buy", "sell"]
    if held < 0:
        return ["short", "cover"]
    return ["buy", "short"]


def _pick():
    """A quick-pick chip was pressed: open the ticket on that stock (runs before the page, so the inputs can change)."""
    v = ss.get("pf_pick")
    if v:
        ss["pf_sym"] = ss["pf_sym_in"] = ss["pf_sym_last"] = v
    ss["pf_pick"] = None


def page_trade():
    ui.html(CSS)
    c = ctx()
    _flash()
    ui.html(hero(c, "Trade", "التداول"))
    access_bar(c)
    held_map = {p["sym"]: p["qty"] for p in c.view["positions"]}
    default = ss.get("pf_sym") or (c.view["positions"][0]["sym"] if c.view["positions"] else "AAPL")
    if "pf_sym_in" not in ss:
        ss["pf_sym_in"] = default
    if ss.get("pf_sym") and ss.get("pf_sym") != ss.get("pf_sym_last"):
        ss["pf_sym_in"] = ss["pf_sym"]
        ss["pf_sym_last"] = ss["pf_sym"]
    left, right = st.columns([1.25, 1], gap="medium")
    with left:
        s1, s2 = st.columns([1, 2], vertical_alignment="bottom")
        sym = (s1.text_input(L("Symbol", "الرمز"), key="pf_sym_in", placeholder="AAPL") or "").strip().upper()
        picks = list(dict.fromkeys(list(held_map) + POPULAR))[:8]
        ui.valid("pf_pick", picks + [None])
        s2.pills(L("Quick pick", "اختيار سريع"), picks, key="pf_pick", on_change=_pick)
        q = c.mkt.quotes([sym]).get(sym) if sym else None
        if not q:
            ui.html(empty("search_off", L("No price for this symbol", "ما فيه سعر لهالرمز"),
                          L("Type a US stock or ETF ticker, e.g. AAPL, NVDA or SPY.", "اكتب رمز سهم أو صندوق أمريكي، مثل AAPL أو NVDA أو SPY.")))
            ui.foot()
            return
        inf = c.mkt.info(sym)
        held = held_map.get(sym, 0)
        ui.html(quote_card(sym, q, inf, held))
    with right:
        spec, pv = ticket(c, sym, q, inf, held)
    with left:
        span = st.segmented_control(L("Chart", "الرسم"), ["1d", "1mo", "6mo", "1y"], default="6mo", key="pf_span",
                                    format_func=lambda k: {"1d": L("Today", "اليوم"), "1mo": L("1M", "شهر"), "6mo": L("6M", "6 أشهر"), "1y": L("1Y", "سنة")}[k]) or "6mo"
        fig = trade_chart(sym, c, spec, span)
        if fig is not None:
            ui.chart(fig, key="pf_tchart")
        ui.sec("pending_actions", f"Working orders · {sym}", f"الأوامر قيد التنفيذ · {sym}")
        open_orders(c, sym, key="pft")
    ui.foot()


def ticket(c, sym, q, inf, held):
    """The order ticket: action, type, size, prices, time in force, bracket; then the preview and the send button."""
    price = q[0]
    with st.container(key="pfticket"):
        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;font-weight:700;color:#fff;margin-bottom:4px">{T.icon("receipt_long")}'
                    f'{L("Order ticket", "تذكرة الأمر")}</div>', unsafe_allow_html=True)
        acts = _actions(held)
        ui.valid(f"pf_side_{'l' if held > 0 else 's' if held < 0 else 'f'}", acts + [None])
        side = st.segmented_control(L("Action", "الإجراء"), acts, default=acts[0], key=f"pf_side_{'l' if held > 0 else 's' if held < 0 else 'f'}",
                                    format_func=lambda k: L(*SIDE[k][:2])) or acts[0]
        types = ["market", "limit", "stop"] + (["trail"] if side in ("sell", "cover") else [])
        typ = st.segmented_control(L("Order type", "نوع الأمر"), types, default="market", key=f"pf_type_{side}",
                                   format_func=lambda k: L(*TYPE[k])) or "market"
        bp_slot = st.empty()                    # buying power: drawn here once the size of the order is known
        spec = {"sym": sym, "side": side, "type": typ}
        if typ == "limit":
            spec["limit"] = st.number_input(L("Limit price ($)", "السعر المحدد ($)"), 0.01, 1e6, round(price * (0.99 if side in ("buy", "cover") else 1.01), 2),
                                            0.01, key=f"pf_lim_{sym}_{side}", format="%.2f")
        elif typ == "stop":
            spec["stop"] = st.number_input(L("Stop price ($)", "سعر الوقف ($)"), 0.01, 1e6, round(price * (1.02 if side in ("buy", "cover") else 0.98), 2),
                                           0.01, key=f"pf_stp_{sym}_{side}", format="%.2f")
        elif typ == "trail":
            spec["trail"] = st.number_input(L("Trail (%)", "المسافة (%)"), 0.5, 40.0, 5.0, 0.5, key=f"pf_trl_{side}")
        ref = spec.get("limit") or spec.get("stop") or price
        entry = side in PF.ENTRY
        # bracket first (risk sizing needs the stop)
        if entry:
            b1, b2 = st.columns(2)
            use_sl = b1.toggle(L("Stop loss", "وقف الخسارة"), value=side == "short", key=f"pf_usl_{side}")
            use_tp = b2.toggle(L("Take profit", "جني الأرباح"), value=False, key=f"pf_utp_{side}")
            if use_sl:
                slp = b1.number_input(L("Stop loss (%)", "وقف الخسارة (%)"), 0.5, 50.0, 5.0 if side == "buy" else 8.0, 0.5, key=f"pf_slp_{side}")
                spec["sl"] = round(ref * (1 - slp / 100) if side == "buy" else ref * (1 + slp / 100), 2)
                b1.caption(f"= {_m(spec['sl'])}")
            if use_tp:
                tpp = b2.number_input(L("Take profit (%)", "جني الأرباح (%)"), 0.5, 500.0, 10.0, 0.5, key=f"pf_tpp_{side}")
                spec["tp"] = round(ref * (1 + tpp / 100) if side == "buy" else ref * (1 - tpp / 100), 2)
                b2.caption(f"= {_m(spec['tp'])}")
        modes = ["shares", "dollars", "pct"] + (["risk"] if entry and spec.get("sl") else [])
        ui.valid(f"pf_mode_{side}", modes + [None])
        mode = st.segmented_control(L("Size by", "الكمية حسب"), modes, default="shares", key=f"pf_mode_{side}",
                                    format_func=lambda k: {"shares": L("Shares", "أسهم"), "dollars": L("Dollars", "دولار"),
                                                           "pct": L("% of equity", "% من الحساب"), "risk": L("Risk %", "مخاطرة %")}[k]) or "shares"
        eq = max(c.acct["equity"], 0)
        if side in ("sell", "cover"):
            maxq = int(abs(held))
            qty = st.number_input(L("Shares", "الأسهم"), 1, max(maxq, 1), maxq or 1, 1, key=f"pf_q_{sym}_{side}_{maxq}")
        elif mode == "shares":
            qk = f"pf_q_{sym}_{side}"
            a_ = c.acct
            room_ = max(a_["excess"] - PF.reserved(c.state, a_), 0.0)
            r_ = PF.SHORT_INIT if side == "short" else a_["r_long"]
            mq = int(max(room_ - PF.fee_of(c.state["settings"], 1), 0) / (r_ * ref)) if ref and r_ else 0
            q1, q2 = st.columns([3, 1], vertical_alignment="bottom")
            with q1:
                qty = st.number_input(L("Shares", "الأسهم"), 1, 10_000_000, 10, 1, key=qk)
            with q2:
                st.button(L(f"Max {mq:,}", f"الأقصى {mq:,}"), key=f"pf_max_{side}", width="stretch", disabled=mq < 1,
                          on_click=lambda k=qk, v=max(mq, 1): ss.__setitem__(k, v),
                          help=L("The most shares your buying power covers at this price", "أكثر عدد أسهم تغطيه قوتك الشرائية بهالسعر"))
        elif mode == "dollars":
            amt = st.number_input(L("Amount ($)", "المبلغ ($)"), 1.0, 1e9, 5000.0, 500.0, key=f"pf_amt_{side}")
            qty = int(amt // ref) if ref else 0
            st.caption(L(f"= {qty:,} shares", f"= {qty:,} سهم"))
        elif mode == "pct":
            pct = st.number_input(L("Share of equity (%)", "النسبة من الحساب (%)"), 0.5, 200.0, 10.0, 0.5, key=f"pf_pct_{side}")
            qty = int(eq * pct / 100 // ref) if ref else 0
            st.caption(L(f"= {qty:,} shares", f"= {qty:,} سهم"))
        else:
            rk = st.number_input(L("Risk per trade (% of equity)", "المخاطرة بالصفقة (% من الحساب)"), 0.1, 10.0, 1.0, 0.1, key=f"pf_rk_{side}")
            dist = abs(ref - spec["sl"])
            qty = int(eq * rk / 100 // dist) if dist > 0 else 0
            st.caption(L(f"= {qty:,} shares: a stop-out loses about {_m(qty * dist, 0)}", f"= {qty:,} سهم: لو ضرب الوقف تخسر تقريباً {_m(qty * dist, 0)}"))
        spec["qty"] = int(qty or 0)
        bp_slot.markdown(bp_html(c, side, sym, ref, spec["qty"], held), unsafe_allow_html=True)
        if typ != "market":
            spec["tif"] = st.segmented_control(L("Time in force", "مدة الأمر"), ["day", "gtc"], default="gtc" if typ == "trail" else "day",
                                               key=f"pf_tif_{typ}", format_func=lambda k: L("Day", "اليوم") if k == "day" else L("Until cancelled", "حتى الإلغاء")) or "day"
        # the trade journal: why this trade (kept with the order, shown in the activity and the history)
        note = st.text_input(L("Note for your journal (optional)", "ملاحظة لسجلك (اختياري)"), key=f"pf_note_{ss.get('pf_note_n', 0)}", max_chars=120,
                             placeholder=L("Why this trade? e.g. breakout above $200, earnings next week",
                                           "ليش هالصفقة؟ مثلاً اختراق فوق 200$، والنتائج الأسبوع الجاي"))
        if str(note or "").strip():
            spec["note"] = str(note).strip()
        pv, err = None, None
        try:
            pv = PF.preview(c.state, c.view, c.mkt, spec)
        except PF.OrderError as e:
            err = e
        if pv:
            ui.html(preview_html(pv, c))
            for w in short_warnings(pv) if side == "short" else []:
                ui.html(w)
        elif err is not None:
            st.error(_err(err), icon=":material/block:")
        lab = L(*SIDE[side][:2])
        if c.can_trade:
            with st.container(key="pf_submit_short" if side == "short" else "pf_submit"):
                go_ = st.button(f"{lab} {spec['qty']:,} {sym}", key="pf_send", icon=":material/send:", width="stretch", disabled=pv is None)
            if go_ and pv is not None:
                try:
                    o = PF.place(c.state, c.view, c.mkt, spec)
                    ss["pf_sym"] = sym
                    ss["pf_note_n"] = ss.get("pf_note_n", 0) + 1        # a fresh, empty note box for the next order
                    commit(c, _done(o))
                except PF.OrderError as e:
                    st.error(_err(e))
        if not pv or not pv.get("open"):
            ui.html(f'<div class="pfinfo">{T.icon("schedule")}<div>{T.esc(L("The market is closed: market orders fill at the next open, limit and stop orders when their price is reached during the session.", "السوق مسكّر: أوامر السوق تتنفذ مع الافتتاح القادم، والمحددة والوقف لما يوصل السعر لها خلال الجلسة."))}</div></div>')
    return spec, pv


def bp_html(c, side, sym, ref, qty, held):
    """Buying power inside the ticket: what's free now (after what open orders hold), the most shares it buys at this price,
    and how much of it this order takes. A sale or a cover shows what it gives back."""
    a, s_ = c.acct, c.state["settings"]
    held_for = PF.reserved(c.state, a)
    room = max(a["excess"] - held_for, 0.0)
    short = side == "short"
    r = PF.SHORT_INIT if short else a["r_long"]
    bp = room / r if r else 0.0
    fee = PF.fee_of(s_, max(int(qty or 0), 1))
    maxq = int(max(room - fee, 0) / (r * ref)) if ref and r else 0
    lab = L("Short buying power", "القوة الشرائية للمكشوف") if short else L("Buying power", "القوة الشرائية")
    sub = [f'{L("Cash", "الكاش")} <b>{_m(a["cash"], 0)}</b>']
    if held_for > 0.5:
        sub.append(f'{L("held for open orders", "محجوز لأوامر مفتوحة")} <b>{_m(held_for / r if r else held_for, 0)}</b>')
    if not short and a["r_long"] < 1:
        sub.append(L("2× margin on", "هامش 2× مفعّل"))
    if short:
        sub.append(L("a short needs 50% of its value as margin", "المكشوف يحتاج 50% من قيمته هامش"))
    head = (f'<div class="t"><div class="l">{T.icon("bolt")}{T.esc(lab)}</div><div class="v">{_m(bp, 0)}</div></div>'
            f'<div class="s">{" · ".join(sub)}</div>')
    if side in ("sell", "cover"):
        free = (a["r_long"] if side == "sell" else PF.SHORT_INIT) * qty * ref
        body = (f'<div class="mx">{T.icon("inventory_2")}{T.esc(L("You hold", "عندك"))} <b>{abs(int(held)):,}</b> {T.esc(sym)} · '
                f'{T.esc(L("this order frees about", "هالأمر يحرر تقريباً"))} <b>{_m(free / (a["r_long"] or 1), 0)}</b></div>')
        return f'<div class="pfbp">{head}{body}</div>'
    body = (f'<div class="mx">{T.icon("calculate")}{T.esc(L("Max now", "الحد الأعلى الحين"))} <b>{maxq:,}</b> {T.esc(sym)} '
            f'{T.esc(L("at", "بسعر"))} <b>{_m(ref)}</b></div>')
    need = r * qty * ref + fee if qty else 0.0
    if qty:
        pct = need / room * 100 if room > 0 else 999.0
        col = T.POS_FG if pct < 50 else T.GOLD if pct < 90 else T.ORANGE if pct <= 100 else T.NEG_FG
        over = pct > 100
        body += (f'<div class="u"><div class="bar"><i style="width:{min(pct, 100):.0f}%;background:{col}"></i></div>'
                 f'<div class="cap"><span>{T.esc(L("This order uses", "هالأمر يستخدم"))} <b>{_m(need / r if r else need, 0)}</b></span>'
                 f'<span><b class="{"dn" if over else ""}">{min(pct, 999):.1f}%</b> '
                 f'{T.esc(L("— more than you have" if over else "of it", "— أكثر من المتاح" if over else "منها"))}</span></div></div>')
    return f'<div class="pfbp{" sh" if short else ""}">{head}{body}</div>'


def preview_html(pv, c):
    rows = [(L("Estimated price", "السعر التقريبي"), _m(pv["ref"]), ""), (L("Shares", "الأسهم"), f"{pv['qty']:,}", ""),
            (L("Order value", "قيمة الأمر"), _m(pv["value"]), ""), (L("Commission", "العمولة"), _m(pv["fee"]), "")]
    if pv["side"] in PF.ENTRY:
        rows.append((L("Margin it uses", "الهامش اللي يستخدمه"), _m(pv["need"]), ""))
        rows.append((L("Buying power left", "القوة الشرائية المتبقية") if pv["side"] == "buy" else L("Short buying power left", "القوة الشرائية للمكشوف المتبقية"),
                     _m(pv["bp_after"], 0), ""))
        if pv.get("weight_after") is not None:
            rows.append((L("Weight in the account", "الوزن في الحساب"), _p(pv["weight_after"], 1, False), ""))
        if pv.get("risk") is not None:
            rows.append((L("Loss at the stop", "الخسارة عند الوقف"), _m(-pv["risk"], 0), "dn"))
            if pv.get("risk_pct") is not None:
                rows.append((L("…of the account", "…من الحساب"), _p(pv["risk_pct"], 2, False), "dn"))
        if pv.get("reward") is not None:
            rows.append((L("Gain at the target", "الربح عند الهدف"), _m(pv["reward"], 0, True), "up"))
    else:
        held = next((p for p in c.view["positions"] if p["sym"] == pv["sym"]), None)
        if held:
            per = (pv["ref"] - held["avg"]) if held["qty"] > 0 else (held["avg"] - pv["ref"])
            pnl = per * pv["qty"] - pv["fee"]
            rows.append((L("P&L on these shares", "ربح هالأسهم"), _m(pnl, 2, True), "up" if pnl > 0 else "dn"))
    body = "".join(f'<div class="r"><span>{T.esc(a)}</span><b class="{k}">{b}</b></div>' for a, b, k in rows)
    rr = ""
    if pv.get("risk") and pv.get("reward"):
        tot = pv["risk"] + max(pv["reward"], 0)
        lw = pv["risk"] / tot * 100 if tot else 50
        rr = (f'<div class="rr"><i class="ls" style="width:{lw:.0f}%"></i><i class="gn" style="width:{100 - lw:.0f}%"></i></div>'
              f'<div style="display:flex;justify-content:space-between;font-size:.74rem;color:{_MU}"><span>{L("Risk", "المخاطرة")}</span>'
              f'<span>{L("Reward / risk", "العائد / المخاطرة")} <b style="color:#fff">{pv["rr"]:.2f}</b></span><span>{L("Reward", "العائد")}</span></div>')
    return f'<div class="pfprev"><div class="h">{T.icon("fact_check")}{L("Order preview", "معاينة الأمر")}</div>{body}{rr}</div>'


def short_warnings(pv):
    """What a short seller must know before sending the order."""
    out = []
    inf = pv.get("info") or {}
    out.append(f'<div class="pfwarn">{T.icon("warning")}<div>{L("<b>A short can lose more than it was worth</b>: the price can rise without limit. Keep a stop loss.", "<b>المكشوف ممكن يخسر أكثر من قيمته</b>: السعر يقدر يرتفع بلا حد. خلك دايم بوقف خسارة.")}</div></div>')
    rate = pv.get("borrow")
    if rate is not None:
        day = pv.get("borrow_day") or 0
        out.append(f'<div class="pfinfo">{T.icon("percent")}<div>{L(f"Borrow fee: about <b>{rate:.2f}% a year</b> ({_m(day)} a day, {_m(day * 30, 0)} a month at this size), charged every night the short is open.", f"رسوم الاقتراض: تقريباً <b>{rate:.2f}% سنوياً</b> ({_m(day)} باليوم، {_m(day * 30, 0)} بالشهر بهالحجم)، وتنخصم كل ليلة والمركز مفتوح.")}</div></div>')
    sp = inf.get("shortPercentOfFloat")
    dtc = inf.get("shortRatio")
    if sp and float(sp) >= 0.15:
        out.append(f'<div class="pfwarn">{T.icon("local_fire_department")}<div>{L(f"<b>Squeeze risk</b>: {float(sp) * 100:.1f}% of the float is already sold short" + (f" ({float(dtc):.1f} days to cover)" if dtc else "") + ". A jump in price can force shorts to buy back all at once.", f"<b>خطر الضغط القسري</b>: {float(sp) * 100:.1f}% من الأسهم المتاحة مبيوعة على المكشوف" + (f" ({float(dtc):.1f} أيام تغطية)" if dtc else "") + ". أي قفزة بالسعر ممكن تجبر البائعين يشترون كلهم مرة وحدة.")}</div></div>')
    dy = inf.get("dividendRate")
    if dy:
        out.append(f'<div class="pfinfo">{T.icon("payments")}<div>{L(f"A short pays the dividends of the shares it owes (about ${float(dy):.2f} a share a year).", f"المكشوف يدفع توزيعات الأسهم اللي عليه (تقريباً {float(dy):.2f}$ للسهم بالسنة).")}</div></div>')
    return out


# =====================================================================
# ANALYTICS
# =====================================================================
MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]


def _monthly(r):
    if not len(r):
        return None
    m = (1 + r).groupby([r.index.year, r.index.month]).prod() - 1
    tab = pd.DataFrame(index=sorted({y for y, _ in m.index}), columns=range(1, 13), dtype=float)
    for (y, mo), v in m.items():
        tab.loc[y, mo] = v * 100
    return tab


@st.cache_data(ttl=1800, show_spinner=False)
def _rets(syms):
    h = data.history_many(syms + ("SPY",), "1y")
    out = {}
    for s, d in h.items():
        if d is not None and len(d) > 30:
            out[s] = d["Close"].pct_change()
    return pd.DataFrame(out).dropna(how="all")


def risk_now(c):
    """Today's holdings measured on their last year: 1-day VaR (95%), beta to the S&P 500, correlations."""
    pos = c.view["positions"]
    if not pos:
        return None
    r = _rets(tuple(sorted(p["sym"] for p in pos)))
    if r.empty:
        return None
    w = {p["sym"]: p["mv"] for p in pos if p["sym"] in r}
    if not w:
        return None
    pnl = sum(r[s].fillna(0) * v for s, v in w.items())
    out = {"var": float(-np.percentile(pnl.dropna(), 5)) if len(pnl.dropna()) > 30 else None}
    if "SPY" in r and r["SPY"].var() > 0:
        eq = max(c.acct["equity"], 1e-9)
        out["beta"] = float(sum(v / eq * r[s].cov(r["SPY"]) / r["SPY"].var() for s, v in w.items()))
    syms = [s for s in w]
    if len(syms) >= 2:
        out["corr"] = r[syms].corr()
    return out


def page_analytics():
    ui.html(CSS)
    c = ctx()
    _flash()
    ui.html(hero(c, "Analytics", "التحليلات"))
    v, a = c.view, c.acct
    b = bench(v)
    s = PF.stats(v, b)
    f = lambda x, fn: fn(x) if x is not None else "—"
    ui.sec("query_stats", "Return and risk", "العائد والمخاطرة")
    ui.html(kpis([
        ("show_chart", L("Return (time-weighted)", "العائد (موزون بالوقت)"), f(s.get("twr"), _p), f'{L("S&P 500", "S&P 500")} <b>{f(s.get("bench_ret"), _p)}</b>', _k(s.get("twr")), None),
        ("calendar_month", L("Yearly (CAGR)", "سنوياً (CAGR)"), f(s.get("cagr"), _p), L("shown after 6 months", "يظهر بعد 6 أشهر"), _k(s.get("cagr")), None),
        ("ssid_chart", L("Volatility (yearly)", "التذبذب (سنوي)"), f(s.get("vol"), lambda x: _p(x, 1, False)), L("how much it swings", "قد إيش يتذبذب"), None, None),
        ("star", L("Sharpe ratio", "نسبة شارب"), f(s.get("sharpe"), lambda x: f"{x:.2f}"), f'{L("Sortino", "سورتينو")} <b>{f(s.get("sortino"), lambda x: f"{x:.2f}")}</b>', None, None),
        ("trending_down", L("Max drawdown", "أكبر هبوط"), f(s.get("maxdd"), lambda x: _p(x, 1)), f'{L("now", "الحين")} <b>{f(s.get("dd_now"), lambda x: _p(x, 1))}</b>', "neg" if (s.get("maxdd") or 0) < 0 else None, None),
        ("hub", L("Beta to the S&P 500", "بيتا مقابل S&P 500"), f(s.get("beta"), lambda x: f"{x:.2f}"), f'{L("alpha", "ألفا")} <b>{f(s.get("alpha"), lambda x: _p(x, 1))}</b> · {L("corr.", "ارتباط")} <b>{f(s.get("corr"), lambda x: f"{x:.2f}")}</b>', None, None),
        ("calendar_view_day", L("Best / worst day", "أفضل / أسوأ يوم"), f'{f(s.get("best_day"), lambda x: _p(x, 1))} / {f(s.get("worst_day"), lambda x: _p(x, 1))}',
         f'{L("up days", "أيام صاعدة")} <b>{f(s.get("pos_days"), lambda x: _p(x, 0, False))}</b>', None, None),
        ("gpp_maybe", L("1-day VaR (95%)", "القيمة المعرضة للخطر ليوم (95%)"), f(s.get("var95"), lambda x: _p(x, 2, False)), L("a bad day, 1 in 20", "يوم سيء، مرة من 20"), None, None),
    ], "c4"))
    r = PF.daily_returns(v["curve"])
    if len(r) >= 2:
        g1, g2 = st.columns(2)
        with g1:
            cum = ((1 + r).cumprod() - 1) * 100
            series = {L("Portfolio", "المحفظة"): cum}
            if len(b.dropna()) > 2:
                bb = b.reindex(r.index).ffill()
                series[L("S&P 500", "S&P 500")] = (bb / float(b.reindex(v["curve"].index).ffill().iloc[0]) - 1) * 100
            ui.chart(C.lines(series, L("Cumulative return", "العائد التراكمي"), height=320, colors=[C.CYAN, C.GOLD]), key="pf_cum")
        with g2:
            idx = (1 + r).cumprod()
            ui.chart(C.drawdown((idx / idx.cummax() - 1) * 100, L("Drawdown from the high", "الهبوط من القمة"), height=320), key="pf_dd")
        tab = _monthly(r)
        g3, g4 = st.columns([1.3, 1])
        with g3:
            if tab is not None:
                ui.chart(C.monthly_heatmap(tab, L("Monthly returns", "العائد الشهري"), months=MONTHS_AR if is_ar() else None), key="pf_mh")
        with g4:
            ui.chart(C.histogram(r * 100, L("Daily returns (%)", "العائد اليومي (%)")), key="pf_hist")
        cal = calendar_html(c)
        if cal:
            ui.sec("calendar_month", "P&L calendar", "تقويم الأرباح والخسائر")
            ui.html(cal)
    else:
        ui.html(empty("insights", L("Return charts need a few sessions", "رسوم العائد تحتاج كم جلسة"),
                      L("They fill in after the account has lived through a few market closes.", "تتعبى بعد ما يمر الحساب بكم إغلاق.")))
    ui.sec("swap_vert", "Trading statistics", "إحصائيات التداول")
    if s.get("n_trades"):
        ui.html(kpis([
            ("tag", L("Closed trades", "الصفقات المغلقة"), f'{s["n_trades"]}', f'{L("realized", "محقق")} <b>{_m(s["realized"], 0, True)}</b>', _k(s["realized"]), None),
            ("emoji_events", L("Win rate", "نسبة الفوز"), _p(s["win_rate"], 1, False), "", None, (s["win_rate"], T.POS_FG if s["win_rate"] >= 50 else T.GOLD)),
            ("balance", L("Profit factor", "معامل الربح"), f(s.get("profit_factor"), lambda x: f"{x:.2f}"), L("gains ÷ losses", "الأرباح ÷ الخسائر"), None, None),
            ("functions", L("Expectancy", "متوسط الصفقة"), _m(s["expectancy"], 2, True), f'{L("payoff", "نسبة الربح للخسارة")} <b>{f(s.get("payoff"), lambda x: f"{x:.2f}")}</b>', _k(s["expectancy"]), None),
            ("arrow_upward", L("Average win", "متوسط الربح"), _m(s["avg_win"], 2, True), f'{L("best", "الأفضل")} <b>{_m(s["best_trade"], 0, True)}</b>', "pos", None),
            ("arrow_downward", L("Average loss", "متوسط الخسارة"), _m(s["avg_loss"], 2, True), f'{L("worst", "الأسوأ")} <b>{_m(s["worst_trade"], 0, True)}</b>', "neg", None),
            ("schedule", L("Average holding", "متوسط مدة الصفقة"), L(f"{s['avg_days']:.1f} days", f"{s['avg_days']:.1f} يوم"), "", None, None),
        ]))
        ui.html(long_short_html(s))
        t = pd.DataFrame(v["trades"])
        g1, g2 = st.columns(2)
        with g1:
            by = t.groupby("sym")["pnl"].sum().sort_values()
            ui.chart(C.signed_bars(list(by.index), list(by.values), L("Realized P&L by stock", "الربح المحقق حسب السهم"), height=320), key="pf_bysym")
        with g2:
            tt = t.tail(40)
            ui.chart(C.signed_bars([f"#{i + 1} {x}" for i, x in enumerate(tt["sym"])], list(tt["pnl"]), L("P&L of each trade", "ربح كل صفقة"), height=320),
                     key="pf_bytrade")
    else:
        ui.html(empty("tag", L("No closed trades yet", "ما فيه صفقات مغلقة للحين"),
                      L("Win rate, profit factor and the long vs short comparison appear once trades are closed.",
                        "نسبة الفوز ومعامل الربح ومقارنة الشراء بالمكشوف تطلع بعد ما تتسكر صفقات.")))
    ui.sec("military_tech", "Achievements", "الإنجازات")
    ui.html(achievements_html(badges_of(c, s)))
    ui.sec("shield", "Risk now", "المخاطرة الحين")
    rk = risk_now(c) if v["positions"] else None
    ui.html(kpis([
        ("stacked_bar_chart", L("Gross exposure", "الانكشاف الإجمالي"), _p(a["gross"] / max(a["equity"], 1e-9) * 100, 0, False), f'{L("net", "الصافي")} <b>{_p(a["net"] / max(a["equity"], 1e-9) * 100, 0)}</b>', None, None),
        ("speed", L("Leverage", "الرافعة"), f'{a["leverage"]:.2f}×', f'{L("limit", "الحد")} <b>{1 / a["r_long"]:.0f}×</b> {L("on longs", "للشراء")}', None, None),
        ("hub", L("Holdings beta", "بيتا المراكز"), f((rk or {}).get("beta"), lambda x: f"{x:.2f}"), L("1 = moves like the S&P 500", "1 = يتحرك مثل S&P 500"), None, None),
        ("gpp_maybe", L("1-day VaR (95%) now", "القيمة المعرضة للخطر ليوم الحين"), f((rk or {}).get("var"), lambda x: _m(-x, 0)), L("from the last year of these holdings", "من آخر سنة لهالمراكز"), "neg" if (rk or {}).get("var") else None, None),
        ("pie_chart", L("Largest position", "أكبر مركز"), _p(max((p["weight"] for p in v["positions"]), default=0), 1, False),
         f'{L("top 3", "أكبر 3")} <b>{_p(sum(sorted((p["weight"] for p in v["positions"]), reverse=True)[:3]), 1, False)}</b>', None, None),
    ]))
    if rk and rk.get("corr") is not None:
        cm = rk["corr"]
        z = cm.values.astype(float).copy()
        np.fill_diagonal(z, np.nan)                    # a stock with itself says nothing
        fig = go.Figure(go.Heatmap(z=z, x=list(cm.columns), y=list(cm.index), zmin=-1, zmax=1, zmid=0, xgap=3, ygap=3,
                                   colorscale=[[0, "#1F8A4E"], [0.5, C.NEU_FILL], [1, "#A8323F"]],
                                   text=[["" if i == j else f"{x:.2f}" for j, x in enumerate(row)] for i, row in enumerate(cm.values)],
                                   texttemplate="%{text}", showscale=False, hovertemplate="%{y} · %{x}: %{z:.2f}<extra></extra>"))
        C.style(fig, 120 + 34 * len(cm), L("How your holdings move together (1 year)", "كيف تتحرك مراكزك مع بعض (سنة)"), legend=False)
        fig.update_yaxes(side="left", autorange="reversed")
        g1, g2 = st.columns([1.1, 1])
        with g1:
            ui.chart(fig, key="pf_corr")
        with g2:
            sf = sector_fig(c)
            if sf:
                ui.chart(sf, key="pf_sect2")
    ui.sec("receipt_long", "Costs and income", "التكاليف والدخل")
    tot = v["totals"]
    items = [(L("Commissions", "العمولات"), -tot["fees"]), (L("Borrow fees", "رسوم الاقتراض"), -tot["borrow"]),
             (L("Margin interest", "فائدة الهامش"), -tot["interest"]), (L("Dividends (net)", "التوزيعات (صافي)"), tot["divs"])]
    ui.chart(C.signed_bars([x for x, _ in items], [y for _, y in items], L("What the account paid and received", "اللي دفعه الحساب واللي استلمه"), height=280), key="pf_costs")
    ui.foot()


def long_short_html(s):
    def card(side, ic, title):
        x = s.get(side) or {}
        if not x.get("n"):
            rows = f'<div class="r"><span>{L("No closed trades", "ما فيه صفقات مغلقة")}</span><b>—</b></div>'
        else:
            pnl = x["pnl"]
            rows = (f'<div class="r"><span>{L("Trades", "الصفقات")}</span><b>{x["n"]}</b></div>'
                    f'<div class="r"><span>{L("Win rate", "نسبة الفوز")}</span><b>{_p(x["win"], 1, False)}</b></div>'
                    f'<div class="r"><span>{L("Average return", "متوسط العائد")}</span><b class="{"up" if (x["avg_ret"] or 0) > 0 else "dn"}">{_p(x["avg_ret"])}</b></div>'
                    f'<div class="r"><span>{L("Realized P&L", "الربح المحقق")}</span><b class="{"up" if pnl > 0 else "dn"}">{_m(pnl, 2, True)}</b></div>')
        return f'<div class="c"><div class="h">{T.icon(ic)}{T.esc(title)}</div>{rows}</div>'
    return (f'<div class="pfls">{card("long", "trending_up", L("Long trades", "صفقات الشراء"))}'
            f'{card("short", "trending_down", L("Short trades", "صفقات المكشوف"))}</div>')


# =====================================================================
# ORDERS & HISTORY
# =====================================================================
def page_history():
    ui.html(CSS)
    c = ctx()
    _flash()
    ui.html(hero(c, "Orders & History", "الأوامر والسجل"))
    access_bar(c)
    st_ = c.state
    syms = sorted({o["sym"] for o in st_["orders"]})
    pick = st.multiselect(L("Stocks", "الأسهم"), syms, key="pf_h_syms", placeholder=L("All stocks", "كل الأسهم")) if syms else []
    keep = (lambda s: s in pick) if pick else (lambda s: True)
    tabs = st.tabs([L(":material/pending_actions: Working orders", ":material/pending_actions: الأوامر قيد التنفيذ"),
                    L(":material/list_alt: All orders", ":material/list_alt: كل الأوامر"),
                    L(":material/done_all: Fills", ":material/done_all: التنفيذات"),
                    L(":material/flag: Closed trades", ":material/flag: الصفقات المغلقة"),
                    L(":material/account_balance: Cash ledger", ":material/account_balance: سجل الكاش")])
    with tabs[0]:
        open_orders(c, key="pfh", limit=50)
        live = [o for o in st_["orders"] if o["status"] == "open" and keep(o["sym"])]
        if c.can_trade and len(live) > 1 and st.button(L("Cancel all working orders", "ألغِ كل الأوامر قيد التنفيذ"), icon=":material/cancel:", key="pf_cx_all"):
            for o in live:
                PF.cancel(st_, o["id"])
            commit(c, L(f"{len(live)} orders cancelled", f"تم إلغاء {len(live)} أوامر"))
    with tabs[1]:
        rows = [o for o in sorted(st_["orders"], key=lambda o: o["placed"], reverse=True) if keep(o["sym"])]
        if not rows:
            ui.html(empty("list_alt", L("No orders yet", "ما فيه أوامر للحين"), L("Your orders will be listed here.", "أوامرك بتنعرض هنا.")))
        else:
            df = pd.DataFrame([{"#": o["id"], L("Placed", "وقت الإرسال"): _when(o["placed"]), L("Symbol", "الرمز"): o["sym"],
                                L("Action", "الإجراء"): L(*SIDE[o["side"]][:2]), L("Shares", "الأسهم"): int(o["qty"]),
                                L("Type", "النوع"): L(*TYPE[o["type"]]), L("Price", "السعر"): o.get("limit") or o.get("stop") or (f'{o["trail"]}%' if o.get("trail") else "—"),
                                L("Time in force", "المدة"): L("Day", "اليوم") if o.get("tif") != "gtc" else L("GTC", "حتى الإلغاء"),
                                L("Status", "الحالة"): L(*STATUS[o["status"]][:2]), L("Fill", "التنفيذ"): o.get("fill_px"),
                                L("Note", "ملاحظة"): L(*NOTE[o["note"]]) if o.get("note") in NOTE else "",
                                L("Your journal", "سجلك"): o.get("note_user") or ""} for o in rows])
            ui.table(df, sym=L("Symbol", "الرمز"), height=520, fmt={L("Fill", "التنفيذ"): "{:,.2f}"},
                     words={L("Status", "الحالة"): (L("Filled", "منفذ"), L("Rejected", "مرفوض"))})
            st.download_button(L("Download CSV", "تحميل CSV"), df.to_csv(index=False).encode("utf-8-sig"), "paper_orders.csv", "text/csv",
                               icon=":material/download:", key="pf_dl_orders")
    with tabs[2]:
        fills = [f_ for f_ in sorted(st_["fills"], key=lambda f_: (f_["time"], f_["id"]), reverse=True) if keep(f_["sym"])]
        if not fills:
            ui.html(empty("done_all", L("No fills yet", "ما فيه تنفيذات للحين"), L("Every executed order shows here with its price.", "كل أمر تنفذ يطلع هنا بسعره.")))
        else:
            df = pd.DataFrame([{L("Time", "الوقت"): _when(f_["time"]), L("Symbol", "الرمز"): f_["sym"], L("Action", "الإجراء"): L(*SIDE[f_["side"]][:2]),
                                L("Shares", "الأسهم"): int(f_["qty"]), L("Price", "السعر"): f_["px"], L("Value", "القيمة"): f_["qty"] * f_["px"],
                                L("Fee", "العمولة"): f_.get("fee", 0.0), L("Order", "الأمر"): f'#{f_["order"]}'} for f_ in fills])
            ui.table(df, sym=L("Symbol", "الرمز"), height=520, fmt={L("Price", "السعر"): "${:,.2f}", L("Value", "القيمة"): "${:,.0f}", L("Fee", "العمولة"): "${:,.2f}"})
            st.download_button(L("Download CSV", "تحميل CSV"), df.to_csv(index=False).encode("utf-8-sig"), "paper_fills.csv", "text/csv",
                               icon=":material/download:", key="pf_dl_fills")
    with tabs[3]:
        tr = [t for t in reversed(c.view["trades"]) if keep(t["sym"])]
        if not tr:
            ui.html(empty("flag", L("No closed trades yet", "ما فيه صفقات مغلقة للحين"), L("A trade closes when you sell a long or cover a short.", "الصفقة تتسكر لما تبيع سهم عندك أو تغطي مكشوف.")))
        else:
            df = pd.DataFrame([{L("Closed", "الإغلاق"): _when(t["closed"]), L("Symbol", "الرمز"): t["sym"],
                                L("Side", "الاتجاه"): L("Long", "شراء") if t["dir"] == "long" else L("Short", "مكشوف"), L("Shares", "الأسهم"): int(t["qty"]),
                                L("Entry", "الدخول"): t["entry"], L("Exit", "الخروج"): t["exit"], L("P&L", "الربح"): t["pnl"], L("Return", "العائد"): t["ret"],
                                L("Fees", "العمولات"): t["fees"], L("Borrow", "الاقتراض"): t["borrow"], L("Days", "الأيام"): t["days"]} for t in tr])
            ui.table(df, sym=L("Symbol", "الرمز"), height=520, signed={L("P&L", "الربح"), L("Return", "العائد")},
                     words={L("Side", "الاتجاه"): (L("Long", "شراء"), L("Short", "مكشوف"))},
                     fmt={L("Entry", "الدخول"): "${:,.2f}", L("Exit", "الخروج"): "${:,.2f}", L("P&L", "الربح"): "${:+,.2f}", L("Return", "العائد"): "{:+.2f}%",
                          L("Fees", "العمولات"): "${:,.2f}", L("Borrow", "الاقتراض"): "${:,.2f}", L("Days", "الأيام"): "{:.1f}"})
            st.download_button(L("Download CSV", "تحميل CSV"), df.to_csv(index=False).encode("utf-8-sig"), "paper_trades.csv", "text/csv",
                               icon=":material/download:", key="pf_dl_trades")
    with tabs[4]:
        kinds = {"deposit": L("Deposit", "إيداع"), "withdraw": L("Withdrawal", "سحب"), "dividend": L("Dividend received", "توزيعات مستلمة"),
                 "dividend_short": L("Dividend paid (short)", "توزيعات مدفوعة (مكشوف)"), "split": L("Stock split", "تقسيم سهم"),
                 "borrow": L("Borrow fees", "رسوم الاقتراض"), "interest": L("Margin interest", "فائدة الهامش")}
        led = [x for x in c.view["ledger"] if not x.get("sym") or keep(x["sym"])]
        start = {"time": c.state["created"][:10], "kind": "start", "sym": "", "amount": float(c.state["start_cash"]), "note": ""}
        led = led + [start]
        df = pd.DataFrame([{L("Date", "التاريخ"): str(x["time"])[:10], L("Entry", "البند"): kinds.get(x["kind"], L("Starting cash", "الكاش الأولي")),
                            L("Symbol", "الرمز"): x.get("sym") or "", L("Amount", "المبلغ"): x["amount"], L("Note", "ملاحظة"): x.get("note") or ""} for x in led])
        ui.table(df, height=520, signed={L("Amount", "المبلغ")}, fmt={L("Amount", "المبلغ"): "${:+,.2f}"})
    ui.foot()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "20.5"
