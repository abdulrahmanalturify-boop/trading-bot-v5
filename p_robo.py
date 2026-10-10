"""
p_robo.py - Portfolio > Robo Advisor: an Investment Policy Statement from a short questionnaire, a portfolio of ETFs that fits
it, and its management on autopilot (robo.py does the work).

Four screens: the introduction; the questionnaire (one question at a time, tiles to tap, a live risk meter); the plan (the
risk profile, the allocation, what to expect, a projection, the last five years, the IPS, the level can be moved by hand);
and, once invested, the dashboard (value against the money invested and the benchmark, target against current weights, the
holdings, everything the robo did, the IPS, and the controls: monthly deposit, add or withdraw, risk level, questionnaire,
close). Virtual money, like the paper portfolio, kept under the same visitor code.
"""
import html as _html
import math
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import charts as C
import markets as MK
import p_portfolio as PP
import paperbots as PB
import portfolio as PF
import robo as R
import robobot as RB
import theme as T
import ui
from i18n import L, is_ar

ss = st.session_state
_MU, _BD = "#9D97A5", T.BORDER
LEVEL_COLORS = ["#34D399", "#2DD4BF", "#22D3EE", "#38BDF8", "#60A5FA", "#818CF8", "#A78BFA", "#F5B94A", "#F97316", "#F87171"]
MONTHS_AR = PP.MONTHS_AR

CSS = f"""<style>
/* ---------- introduction ---------- */
.rbhero {{ position:relative; overflow:hidden; border-radius:24px; border:1px solid {_BD}; padding:30px 30px 26px; margin:2px 0 16px;
  display:grid; grid-template-columns:minmax(0,1.25fr) minmax(0,.9fr); gap:22px; align-items:center;
  background:radial-gradient(110% 130% at 100% 0%, rgba(123,69,240,.32), transparent 55%), radial-gradient(90% 120% at 0% 100%, rgba(45,182,235,.18), transparent 60%),
  linear-gradient(135deg,#130E22,#1A1430 55%,#120D20); box-shadow:0 18px 40px rgba(0,0,0,.28), {T.GLOW}; }}
.rbhero::before {{ content:""; position:absolute; left:0; right:0; top:0; height:3px; background:linear-gradient(90deg,{T.ACCENT},{T.VIOLET},{T.CYAN}); }}
.rbhero .eb {{ color:{T.CYAN}; font-weight:700; letter-spacing:.18em; font-size:.7rem; text-transform:uppercase; display:flex; align-items:center; gap:8px; }}
.rbhero h1 {{ font-size:2.05rem; line-height:1.15; color:#fff; margin:10px 0 10px; padding:0; font-weight:800; letter-spacing:-.02em; }}
.rbhero h1 em {{ font-style:normal; background:linear-gradient(90deg,#7DD3FC,#A78BFA); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.rbhero p {{ color:#CFC8DA; font-size:.95rem; line-height:1.65; margin:0 0 14px; }}
.rbchips {{ display:flex; flex-wrap:wrap; gap:8px; }}
.rbchip {{ display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:5px 11px; font-size:.76rem; font-weight:600; color:#DCD7E3;
  background:rgba(26,22,36,.78); border:1px solid {_BD}; }}
.rbchip .ms {{ font-size:1rem; color:{T.CYAN}; }}
.rbchip.gold {{ color:#FCE3A6; border-color:rgba(245,185,74,.4); background:rgba(245,185,74,.1); }} .rbchip.gold .ms {{ color:{T.GOLD}; }}
.rbchip.warn {{ color:#FDBA74; border-color:rgba(249,115,22,.45); background:rgba(249,115,22,.1); }} .rbchip.warn .ms {{ color:#F97316; }}
.rbart {{ position:relative; width:100%; max-width:300px; aspect-ratio:1; margin:0 auto; }}
.rbart svg {{ width:100%; height:100%; overflow:visible; }}
.rbart .core {{ position:absolute; inset:34%; border-radius:50%; display:flex; align-items:center; justify-content:center;
  background:radial-gradient(circle at 35% 30%, #4B3A8C, #1B1433 70%); box-shadow:0 0 0 1px rgba(167,139,250,.35), 0 0 46px rgba(123,69,240,.55);
  animation:rbfloat 4s ease-in-out infinite; }}
.rbart .core .ms {{ font-size:3.1rem; color:#fff; }}
@keyframes rbfloat {{ 50% {{ transform:translateY(-6px); }} }}
.rbsteps {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:0 0 14px; }}
.rbstep {{ position:relative; overflow:hidden; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:18px; padding:16px 16px 14px;
  animation:rbup .5s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--i) * 90ms); }}
.rbstep .n {{ width:34px; height:34px; border-radius:11px; display:flex; align-items:center; justify-content:center; color:#fff;
  background:linear-gradient(140deg,{T.CYAN},{T.VIOLET}); box-shadow:0 8px 18px -8px rgba(123,69,240,.7); margin-bottom:10px; }}
.rbstep .n .ms {{ font-size:1.2rem; color:#fff; }}
.rbstep b {{ display:block; color:#fff; font-size:.98rem; margin-bottom:4px; }}
.rbstep span {{ color:#A8A2B3; font-size:.8rem; line-height:1.5; }}
.rbstep::after {{ content:attr(data-k); position:absolute; inset-inline-end:12px; top:6px; font-size:2.6rem; font-weight:800; color:rgba(255,255,255,.05); }}
@keyframes rbup {{ from {{ opacity:0; transform:translateY(14px); }} }}
.rbfeat {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:6px 0 14px; }}
.rbfeat > div {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:13px 14px; }}
.rbfeat .ms {{ color:{T.CYAN}; font-size:1.3rem; }}
.rbfeat b {{ display:block; color:#F4F1F8; font-size:.86rem; margin:6px 0 3px; }}
.rbfeat span:not(.ms) {{ color:#A8A2B3; font-size:.76rem; line-height:1.45; }}
.rbnote {{ display:flex; gap:10px; align-items:flex-start; color:#A8A2B3; font-size:.78rem; line-height:1.55; border:1px dashed rgba(157,151,165,.35);
  border-radius:14px; padding:10px 13px; margin:10px 0 4px; }}
.rbnote .ms {{ color:{T.GOLD}; font-size:1.1rem; }}
@media (max-width: 820px) {{ .rbhero {{ grid-template-columns:1fr; padding:22px 18px 18px; }} .rbhero h1 {{ font-size:1.6rem; }}
  .rbart {{ max-width:210px; order:-1; }} .rbsteps {{ grid-template-columns:1fr; }} .rbfeat {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}

/* ---------- the questionnaire: progress, question, tiles ---------- */
.rbprog {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:18px; padding:14px 16px 12px; margin:2px 0 12px; }}
.rbprog .top {{ display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; }}
.rbprog .qn {{ color:#DCD7E3; font-weight:700; font-size:.86rem; }} .rbprog .qn em {{ font-style:normal; color:{_MU}; font-weight:500; }}
.rbmeter {{ display:inline-flex; align-items:center; gap:9px; color:{_MU}; font-size:.76rem; font-weight:600; }}
.rbmeter b {{ color:#fff; font-size:.9rem; }}
.rbmeter .segs {{ display:inline-flex; gap:3px; direction:ltr; }}
.rbmeter .segs i {{ width:9px; height:14px; border-radius:3px; background:rgba(157,151,165,.18); transition:background .4s; }}
.rbprog .bar {{ position:relative; height:7px; border-radius:7px; background:rgba(157,151,165,.16); margin:11px 0 10px; overflow:hidden; }}
.rbprog .bar i {{ position:absolute; inset-block:0; inset-inline-start:0; border-radius:7px; background:linear-gradient(90deg,{T.CYAN},{T.VIOLET});
  box-shadow:0 0 12px rgba(45,182,235,.6); animation:rbgrow .6s cubic-bezier(.2,.8,.2,1) both; }}
@keyframes rbgrow {{ from {{ width:var(--w0); }} }}
.rbprog .secs {{ display:flex; gap:6px; flex-wrap:wrap; }}
.rbprog .secs span {{ display:inline-flex; align-items:center; gap:5px; border-radius:999px; padding:4px 10px; font-size:.72rem; font-weight:600;
  color:{_MU}; border:1px solid rgba(157,151,165,.22); }}
.rbprog .secs span .ms {{ font-size:.95rem; }}
.rbprog .secs span.done {{ color:#86EFAC; border-color:rgba(74,222,128,.35); background:rgba(34,197,94,.08); }}
.rbprog .secs span.cur {{ color:#fff; border-color:rgba(45,182,235,.6); background:linear-gradient(90deg,rgba(45,182,235,.22),rgba(123,69,240,.18)); }}
.rbprog .secs span.cur .ms {{ color:{T.CYAN}; }}
@media (max-width: 640px) {{ .rbprog .secs {{ gap:4px; flex-wrap:nowrap; }} .rbprog .secs span:not(.cur) {{ padding:4px 6px; }} .rbprog .secs span:not(.cur) em {{ display:none; }} }}
.rbprog .secs em {{ font-style:normal; }}
.rbq {{ position:relative; overflow:hidden; border-radius:20px; border:1px solid {_BD}; padding:20px 22px 18px; margin:0 0 14px;
  background:radial-gradient(90% 140% at 100% 0%, rgba(123,69,240,.16), transparent 60%), {T.BOX_BG}; animation:rbup .45s cubic-bezier(.2,.8,.2,1) both; }}
.rbq .k {{ display:flex; align-items:center; gap:7px; color:{T.CYAN}; font-size:.7rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; }}
.rbq .k .ms {{ font-size:1rem; }}
.rbq h2 {{ color:#fff; font-size:1.45rem; font-weight:800; line-height:1.3; margin:8px 0 8px; padding:0; letter-spacing:-.01em; }}
.rbq .why {{ display:flex; gap:8px; align-items:flex-start; color:#B9B3C4; font-size:.84rem; line-height:1.55; }}
.rbq .why .ms {{ color:{T.GOLD}; font-size:1.05rem; margin-top:1px; }}
.rbq .viz {{ margin-top:12px; }}
.rbdrop {{ display:block; width:100%; max-width:520px; height:96px; direction:ltr; }}
.rbdrop .ln {{ stroke-dasharray:600; stroke-dashoffset:600; animation:rbdraw 1.6s .2s ease-out forwards; }}
.rbdrop .tg {{ opacity:0; animation:rbfade .5s 1.5s forwards; }}
@keyframes rbdraw {{ to {{ stroke-dashoffset:0; }} }}
@keyframes rbfade {{ to {{ opacity:1; }} }}
[class*="st-key-rbt_"] {{ position:relative; gap:0 !important; }}
[class*="st-key-rbt_"] [data-testid="stElementContainer"] {{ position:static !important; margin:0 !important; }}
[class*="st-key-rbt_"] .stButton {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; }}
[class*="st-key-rbt_"] .stButton > div, [class*="st-key-rbt_"] [data-testid="stTooltipHoverTarget"] {{ width:100% !important; height:100% !important; }}
[class*="st-key-rbt_"] .stButton button {{ width:100% !important; height:100% !important; min-height:0 !important; padding:0 !important;
  opacity:0; cursor:pointer; border-radius:18px !important; }}
.rbo {{ position:relative; overflow:hidden; isolation:isolate; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; gap:9px;
  min-height:150px; padding:20px 12px 16px; border-radius:18px; border:1px solid transparent; box-sizing:border-box; color:#E9E5F0;
  background:linear-gradient(rgba(19,14,34,.92),rgba(19,14,34,.92)) padding-box,
             linear-gradient(140deg,rgba(121,184,244,.26),rgba(255,255,255,.06) 45%,rgba(123,69,240,.28)) border-box;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.05), 0 10px 26px -18px rgba(0,0,0,.8);
  transition:transform .25s cubic-bezier(.2,.8,.2,1), box-shadow .3s;
  animation:rbtile .45s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--i) * 55ms); }}
.rbo.tall {{ min-height:164px; }}
@keyframes rbtile {{ from {{ opacity:0; transform:translateY(14px) scale(.97); }} }}
.rbo::before {{ content:""; position:absolute; inset:0; z-index:-1; pointer-events:none; opacity:0; transition:opacity .35s;
  background:radial-gradient(120% 80% at 50% 0%, rgba(45,182,235,.22), transparent 65%); }}
.rbo .ic {{ flex:none; width:48px; height:48px; border-radius:15px; display:flex; align-items:center; justify-content:center; color:#7DD3FC;
  background:rgba(45,182,235,.1); box-shadow:inset 0 0 0 1px rgba(45,182,235,.28); transition:transform .4s cubic-bezier(.3,1.6,.5,1), background .3s; }}
.rbo .ic .ms {{ font-size:1.55rem; }}
.rbo .big {{ font-size:1.7rem; font-weight:800; color:#fff; line-height:1; direction:ltr; unicode-bidi:isolate; }}
.rbo .tx {{ display:flex; flex-direction:column; gap:4px; min-width:0; }}
.rbo .tx b {{ font-size:.98rem; font-weight:700; color:#F4F1F8; line-height:1.3; }}
.rbo .tx span {{ font-size:.76rem; color:#A8A2B3; line-height:1.4; }}
.rbo .ck {{ position:absolute; top:10px; inset-inline-end:10px; width:22px; height:22px; border-radius:50%; display:flex; align-items:center;
  justify-content:center; border:1.5px solid rgba(157,151,165,.42); transition:background .25s, border-color .25s; }}
.rbo .ck .ms {{ font-size:.9rem; color:#fff; opacity:0; }}
.rbo .dep {{ width:54px; height:44px; border-radius:9px; position:relative; overflow:hidden; background:rgba(157,151,165,.13); direction:ltr; }}
.rbo .dep i {{ position:absolute; left:0; right:0; top:0; background:linear-gradient(180deg,rgba(248,113,113,.25),rgba(248,113,113,.85));
  border-bottom:2px solid #F87171; animation:rbdepth .9s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--i) * 70ms + .2s); }}
@keyframes rbdepth {{ from {{ height:0; }} }}
.rbo .tx .mixw {{ display:flex; align-items:center; justify-content:center; gap:7px; margin-top:4px; }}
.rbo .tx .mix {{ display:block; width:64px; height:7px; border-radius:6px; overflow:hidden; background:rgba(52,211,153,.4); direction:ltr; }}
.rbo .tx .mix i {{ display:block; height:100%; background:linear-gradient(90deg,#3B8BEB,#60A5FA); animation:rbbar .8s cubic-bezier(.2,.8,.2,1) both;
  animation-delay:calc(var(--i) * 70ms + .2s); }}
.rbo .tx .mixw em {{ font-style:normal; font-size:.72rem; font-weight:700; color:#B9B3C4; }}
.rbo .rng {{ width:100%; max-width:200px; direction:ltr; }}
.rbo .rng .tr {{ display:block; position:relative; height:12px; border-radius:6px; background:rgba(157,151,165,.13); }}
.rbo .rng .tr::after {{ content:""; position:absolute; left:50%; top:-3px; bottom:-3px; width:2px; margin-left:-1px; background:rgba(255,255,255,.55); border-radius:2px; }}
.rbo .rng .lo, .rbo .rng .hi {{ position:absolute; top:0; bottom:0; animation:rbbar .8s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--i) * 70ms + .2s); }}
.rbo .rng .lo {{ right:50%; border-radius:6px 0 0 6px; background:linear-gradient(270deg,rgba(248,113,113,.45),#F87171); }}
.rbo .rng .hi {{ left:50%; border-radius:0 6px 6px 0; background:linear-gradient(90deg,rgba(74,222,128,.45),#4ADE80); }}
@keyframes rbbar {{ from {{ width:0; }} }}
.rbo .rng .lb {{ display:flex; justify-content:space-between; margin-top:6px; font-size:.82rem; font-weight:700; }}
.rbo .rng .lb .d {{ color:#F87171; }} .rbo .rng .lb .u {{ color:#4ADE80; }}
@media (hover:hover) {{
  [class*="st-key-rbt_"]:hover .rbo {{ transform:translateY(-3px); box-shadow:0 18px 34px -18px rgba(45,182,235,.6), inset 0 1px 0 rgba(255,255,255,.08); }}
  [class*="st-key-rbt_"]:hover .rbo::before {{ opacity:1; }}
  [class*="st-key-rbt_"]:hover .rbo .ic {{ transform:rotate(-8deg) scale(1.08); }}
  [class*="st-key-rbt_"]:hover .rbo .ck {{ border-color:{T.CYAN}; }}
}}
[class*="st-key-rbt_"]:has(button:active) .rbo {{ transform:scale(.97); transition-duration:.08s; }}
[class*="st-key-rbt_"]:has(button:focus-visible) .rbo {{ box-shadow:0 0 0 3px rgba(45,182,235,.55); }}
.rbo.on {{ background:linear-gradient(160deg,rgba(45,182,235,.22),rgba(123,69,240,.16) 70%) padding-box,
             linear-gradient(rgba(19,14,34,.9),rgba(19,14,34,.9)) padding-box, linear-gradient(135deg,{T.CYAN},{T.VIOLET}) border-box;
  box-shadow:0 14px 34px -18px rgba(45,182,235,.75); }}
.rbo.on .ic {{ background:linear-gradient(140deg,{T.CYAN},{T.VIOLET}); color:#fff; box-shadow:0 8px 18px -8px rgba(123,69,240,.8); }}
.rbo.on .ck {{ background:linear-gradient(140deg,{T.CYAN},{T.VIOLET}); border-color:transparent; }}
.rbo.on .ck .ms {{ opacity:1; animation:rbpop .5s cubic-bezier(.3,1.6,.5,1); }}
@keyframes rbpop {{ 0% {{ transform:scale(.3); }} 70% {{ transform:scale(1.25); }} 100% {{ transform:scale(1); }} }}
@media (max-width: 640px) {{
  .rbo, .rbo.tall {{ flex-direction:row; justify-content:flex-start; text-align:start; min-height:0; padding-block:12px; padding-inline:12px 44px; gap:12px; }}
  .rbo .ic {{ width:42px; height:42px; border-radius:13px; }} .rbo .ic .ms {{ font-size:1.35rem; }}
  .rbo .ck {{ top:50%; margin-top:-11px; }}
  .rbo .big {{ font-size:1.35rem; min-width:64px; }}
  .rbo .dep {{ order:3; width:34px; height:30px; margin-inline-start:auto; }}
  .rbo .rng {{ max-width:none; flex:1; }}
  .rbo .tx .mixw {{ justify-content:flex-start; }}
  .rbq {{ padding:16px 16px 14px; }} .rbq h2 {{ font-size:1.2rem; }}
}}
.rbfund {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:2px 0 12px; }}
.rbfund > div {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:12px 14px; }}
.rbfund .l {{ color:{_MU}; font-size:.7rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; display:flex; gap:6px; align-items:center; }}
.rbfund .l .ms {{ color:{T.CYAN}; font-size:1rem; }}
.rbfund .v {{ color:#fff; font-size:1.35rem; font-weight:800; margin-top:5px; direction:ltr; unicode-bidi:isolate; display:inline-block; }}
.rbfund .s {{ color:{_MU}; font-size:.74rem; margin-top:2px; }}
@media (max-width: 640px) {{ .rbfund {{ grid-template-columns:1fr; }} }}

/* ---------- the plan: profile, gauge, allocation ---------- */
.rbres {{ position:relative; overflow:hidden; display:grid; grid-template-columns:250px minmax(0,1fr); gap:22px; align-items:center; border-radius:22px;
  border:1px solid {_BD}; padding:20px 24px; margin:2px 0 12px;
  background:radial-gradient(100% 140% at 0% 0%, var(--lg, rgba(45,182,235,.2)), transparent 60%), linear-gradient(135deg,#130E22,#1A1430 60%,#120D20);
  box-shadow:0 18px 40px rgba(0,0,0,.26), {T.GLOW}; animation:rbup .5s cubic-bezier(.2,.8,.2,1) both; }}
.rbres::before {{ content:""; position:absolute; left:0; right:0; top:0; height:3px; background:linear-gradient(90deg,#34D399,#60A5FA,#A78BFA,#F5B94A,#F87171); }}
.rbg {{ width:100%; max-width:250px; margin:0 auto; direction:ltr; }}
.rbg svg {{ width:100%; height:auto; overflow:visible; display:block; }}
.rbg .seg {{ animation:rbfade .4s both; }}
.rbres .eb {{ color:{T.CYAN}; font-size:.7rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase; }}
.rbres h2 {{ color:#fff; font-size:1.75rem; font-weight:800; margin:6px 0 6px; padding:0; display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
.rbres h2 .lv {{ font-size:.8rem; font-weight:700; border-radius:999px; padding:4px 11px; color:#0E0918; background:var(--lc,#60A5FA); }}
.rbres p {{ color:#CFC8DA; font-size:.9rem; line-height:1.6; margin:0 0 10px; }}
.rbtier {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:5px; margin:2px 0 10px; }}
.rbtier span {{ position:relative; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:2px; min-height:34px;
  padding:5px 4px; border-radius:10px; text-align:center; background:rgba(157,151,165,.1); border:1px solid rgba(157,151,165,.2);
  animation:rbup .4s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--i) * 50ms); }}
.rbtier span::before {{ content:""; position:absolute; left:8px; right:8px; top:-1px; height:3px; border-radius:3px; background:var(--c); opacity:.55; }}
.rbtier b {{ color:#B9B3C4; font-size:.72rem; font-weight:700; line-height:1.25; }}
.rbtier em {{ font-style:normal; font-size:.62rem; font-weight:700; color:var(--c); }}
.rbtier span.on {{ background:linear-gradient(160deg, color-mix(in srgb, var(--c) 30%, transparent), rgba(19,14,34,.4)); border-color:var(--c);
  box-shadow:0 8px 20px -12px var(--c); }}
.rbtier span.on::before {{ opacity:1; }}
.rbtier span.on b {{ color:#fff; }}
.rbtier span.you:not(.on) {{ border-style:dashed; border-color:var(--c); }}
@media (max-width: 640px) {{ .rbtier {{ gap:3px; }} .rbtier b {{ font-size:.62rem; }} .rbtier span {{ padding:5px 2px; }} }}
.rbsc {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px 18px; margin:4px 0 10px; }}
.rbsc .h {{ display:flex; justify-content:space-between; color:#CFC8DA; font-size:.78rem; font-weight:600; }}
.rbsc .h b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }}
.rbsc .t {{ position:relative; height:8px; border-radius:8px; background:rgba(157,151,165,.16); margin-top:6px; overflow:hidden; direction:ltr; }}
.rbsc .t i {{ position:absolute; left:0; top:0; bottom:0; border-radius:8px; animation:rbbar 1s cubic-bezier(.2,.8,.2,1) both; }}
@media (max-width: 760px) {{ .rbres {{ grid-template-columns:1fr; padding:18px 16px; gap:10px; }} .rbg {{ max-width:210px; }} .rbres h2 {{ font-size:1.4rem; }} }}
.rbal {{ display:grid; grid-template-columns:240px minmax(0,1fr); gap:20px; align-items:center; background:{T.BOX_BG}; border:1px solid {_BD};
  border-radius:20px; padding:18px 20px; margin:2px 0 12px; }}
.rbdon {{ width:100%; max-width:240px; margin:0 auto; direction:ltr; }}
.rbdon svg {{ width:100%; height:auto; display:block; overflow:visible; }}
.rbdon .sg {{ animation:rbseg 1s cubic-bezier(.2,.8,.2,1) both; }}
@keyframes rbseg {{ from {{ stroke-dasharray:0 100; }} }}
.rbgrp {{ display:flex; height:12px; border-radius:7px; overflow:hidden; gap:2px; direction:ltr; margin:0 0 6px; }}
.rbgrp i {{ display:block; height:100%; animation:rbbar 1s cubic-bezier(.2,.8,.2,1) both; }}
.rbgl {{ display:flex; flex-wrap:wrap; gap:6px 14px; color:#CFC8DA; font-size:.76rem; margin-bottom:12px; }}
.rbgl span {{ display:inline-flex; align-items:center; gap:6px; }} .rbgl i {{ width:9px; height:9px; border-radius:3px; display:inline-block; }}
.rbgl b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }}
.rbleg {{ display:flex; flex-direction:column; gap:2px; }}
.rbleg .r {{ display:grid; grid-template-columns:auto minmax(0,1fr) auto; gap:10px; align-items:center; padding:7px 8px; border-radius:11px;
  transition:background .2s; animation:rbup .45s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--i) * 45ms); }}
.rbleg .r:hover {{ background:rgba(157,151,165,.08); }}
.rbleg .tk {{ min-width:52px; text-align:center; border-radius:8px; padding:3px 7px; font-size:.74rem; font-weight:800; color:#0E0918; background:var(--c); }}
.rbleg .nm b {{ display:block; color:#F4F1F8; font-size:.85rem; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.rbleg .nm span {{ display:block; color:{_MU}; font-size:.72rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.rbleg .w {{ color:#fff; font-weight:800; font-size:.95rem; direction:ltr; unicode-bidi:isolate; }}
.rbleg .w small {{ color:{_MU}; font-weight:600; font-size:.7rem; margin-inline-start:4px; }}
@media (max-width: 760px) {{ .rbal {{ grid-template-columns:1fr; padding:14px; }} .rbdon {{ max-width:200px; }} }}

/* ---------- the IPS document ---------- */
.rbips {{ position:relative; overflow:hidden; border-radius:20px; padding:22px 24px 18px; margin:2px 0 10px;
  background:linear-gradient(180deg,#18122A,#140F23); border:1px solid rgba(167,139,250,.32);
  box-shadow:0 20px 44px -26px rgba(123,69,240,.6), inset 0 1px 0 rgba(255,255,255,.05); }}
.rbips::before {{ content:""; position:absolute; inset:0; pointer-events:none; opacity:.5;
  background-image:repeating-linear-gradient(0deg, rgba(167,139,250,.05) 0 1px, transparent 1px 28px); }}
.rbips .hd {{ position:relative; display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; border-bottom:1px solid rgba(167,139,250,.25);
  padding-bottom:12px; margin-bottom:14px; }}
.rbips .hd .t {{ display:flex; align-items:center; gap:12px; }}
.rbips .seal {{ width:46px; height:46px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff;
  background:conic-gradient(from 0deg,{T.CYAN},{T.VIOLET},{T.GOLD},{T.CYAN}); box-shadow:0 0 0 4px rgba(123,69,240,.18); }}
.rbips .seal .ms {{ font-size:1.4rem; color:#fff; background:#18122A; border-radius:50%; width:36px; height:36px; display:flex; align-items:center; justify-content:center; }}
.rbips .hd b {{ display:block; color:#fff; font-size:1.08rem; font-weight:800; }}
.rbips .hd span {{ color:{_MU}; font-size:.76rem; }}
.rbips .grid {{ position:relative; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px 22px; }}
.rbips .sx h4 {{ display:flex; align-items:center; gap:8px; color:#C4B5FD; font-size:.8rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase;
  margin:0 0 7px; padding:0; }}
.rbips .sx h4 .ms {{ font-size:1.05rem; }}
.rbips .sx h4 i {{ font-style:normal; color:{_MU}; font-weight:700; }}
.rbips .it {{ display:flex; justify-content:space-between; gap:12px; padding:5px 0; border-bottom:1px dashed rgba(157,151,165,.18); font-size:.82rem; }}
.rbips .it span {{ color:{_MU}; }} .rbips .it b {{ color:#F4F1F8; text-align:end; font-weight:600; }}
.rbips .pol {{ color:#CFC8DA; font-size:.82rem; line-height:1.6; margin:0; padding-inline-start:18px; }}
.rbips .pol li {{ margin:2px 0; }}
.rbips table {{ width:100%; border-collapse:collapse; font-size:.8rem; }}
.rbips th {{ color:{_MU}; font-weight:700; text-align:start; padding:4px 6px; border-bottom:1px solid rgba(157,151,165,.25); }}
.rbips td {{ color:#E9E5F0; padding:5px 6px; border-bottom:1px dashed rgba(157,151,165,.15); }}
.rbips td.n {{ direction:ltr; unicode-bidi:isolate; text-align:end; font-weight:700; }}
.rbips .sg {{ position:relative; display:flex; justify-content:space-between; align-items:flex-end; gap:12px; margin-top:16px; color:{_MU}; font-size:.74rem; }}
.rbips .sg b {{ display:block; color:#E9E5F0; font-family:'Brush Script MT','Segoe Script',cursive; font-size:1.3rem; font-weight:400; }}
@media (max-width: 760px) {{ .rbips .grid {{ grid-template-columns:1fr; }} .rbips {{ padding:16px 14px; }} }}

/* ---------- the dashboard ---------- */
.rbauto {{ display:inline-flex; align-items:center; gap:7px; border-radius:999px; padding:4px 11px; font-size:.74rem; font-weight:700;
  color:#C4F1D8; background:rgba(34,197,94,.12); border:1px solid rgba(74,222,128,.38); }}
.rbauto i {{ width:8px; height:8px; border-radius:50%; background:#4ADE80; box-shadow:0 0 0 0 rgba(74,222,128,.7); animation:rbpulse 1.8s infinite; }}
.rbauto.wait {{ color:#FCE3A6; background:rgba(245,185,74,.12); border-color:rgba(245,185,74,.4); }} .rbauto.wait i {{ background:{T.GOLD}; }}
@keyframes rbpulse {{ 70% {{ box-shadow:0 0 0 8px rgba(74,222,128,0); }} 100% {{ box-shadow:0 0 0 0 rgba(74,222,128,0); }} }}
.rbnext {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:0 0 12px; }}
.rbnext > div {{ display:flex; gap:11px; align-items:center; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:12px 14px; }}
.rbnext .i {{ flex:none; width:38px; height:38px; border-radius:12px; display:flex; align-items:center; justify-content:center; background:rgba(45,182,235,.12);
  color:#7DD3FC; box-shadow:inset 0 0 0 1px rgba(45,182,235,.3); }}
.rbnext .i.g {{ background:rgba(74,222,128,.12); color:#86EFAC; box-shadow:inset 0 0 0 1px rgba(74,222,128,.3); }}
.rbnext .i.y {{ background:rgba(245,185,74,.12); color:#FCD34D; box-shadow:inset 0 0 0 1px rgba(245,185,74,.32); }}
.rbnext span {{ display:block; color:{_MU}; font-size:.7rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }}
.rbnext b {{ display:block; color:#fff; font-size:.92rem; margin-top:2px; }}
.rbnext em {{ font-style:normal; color:#B9B3C4; font-size:.74rem; }}
@media (max-width: 760px) {{ .rbnext {{ grid-template-columns:1fr; }} }}
.rbpend {{ display:flex; gap:14px; align-items:center; border-radius:18px; padding:16px 18px; margin:0 0 12px; border:1px solid rgba(245,185,74,.38);
  background:linear-gradient(135deg,rgba(245,185,74,.12),transparent 70%), {T.BOX_BG}; }}
.rbpend .ms {{ font-size:2rem; color:{T.GOLD}; animation:rbfloat 3s ease-in-out infinite; }}
.rbpend b {{ color:#fff; display:block; font-size:1rem; }} .rbpend span {{ color:#CFC8DA; font-size:.84rem; line-height:1.55; }}
.rbdr {{ display:flex; flex-direction:column; gap:12px; }}
.rbdr .r {{ display:grid; grid-template-columns:185px minmax(0,1fr) 92px; gap:12px; align-items:center; }}
.rbdr .f {{ display:flex; align-items:center; gap:8px; min-width:0; }}
.rbdr .f .tk {{ min-width:50px; text-align:center; border-radius:7px; padding:2px 6px; font-size:.72rem; font-weight:800; color:#0E0918; background:var(--c); }}
.rbdr .f span {{ color:#B9B3C4; font-size:.74rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.rbdr .tr {{ position:relative; height:16px; border-radius:8px; background:rgba(157,151,165,.12); direction:ltr; }}
.rbdr .tr .bd {{ position:absolute; top:0; bottom:0; background:rgba(45,182,235,.12); border-left:1px dashed rgba(45,182,235,.45);
  border-right:1px dashed rgba(45,182,235,.45); }}
.rbdr .tr .cu {{ position:absolute; left:0; top:4px; bottom:4px; border-radius:6px; background:var(--c); opacity:.9; animation:rbbar 1s cubic-bezier(.2,.8,.2,1) both; }}
.rbdr .tr .tg {{ position:absolute; top:-3px; bottom:-3px; width:3px; margin-left:-1.5px; border-radius:2px; background:#FCD34D; box-shadow:0 0 6px rgba(252,211,77,.6); }}
.rbdr .v {{ text-align:end; }}
.rbdr .v b {{ color:#fff; font-size:.88rem; }} .rbdr .v em {{ display:block; font-style:normal; font-size:.72rem; font-weight:700; }}
.rbdr .v em.ok {{ color:#86EFAC; }} .rbdr .v em.near {{ color:#FCD34D; }} .rbdr .v em.out {{ color:#F87171; }}
.rbdr .rblg {{ display:flex; gap:14px; flex-wrap:wrap; color:{_MU}; font-size:.72rem; margin-top:2px; }}
.rbdr .rblg i {{ display:inline-block; vertical-align:middle; margin-inline-end:5px; }}
@media (max-width: 640px) {{ .rbdr .r {{ grid-template-columns:minmax(0,1fr) 84px; }} .rbdr .tr {{ grid-column:1 / -1; grid-row:2; }} }}
.rbtbl {{ width:100%; border-collapse:separate; border-spacing:0; font-size:.84rem; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; overflow:hidden; }}
.rbtbl th {{ color:{_MU}; font-size:.7rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; text-align:start; padding:10px 12px;
  border-bottom:1px solid {_BD}; white-space:nowrap; }}
.rbtbl td {{ color:#E9E5F0; padding:10px 12px; border-bottom:1px solid rgba(44,39,56,.7); white-space:nowrap; }}
.rbtbl tr:last-child td {{ border-bottom:0; }}
.rbtbl td.n, .rbtbl th.n {{ text-align:end; }}
.rbtbl .tk {{ display:inline-block; min-width:48px; text-align:center; border-radius:7px; padding:2px 6px; font-size:.72rem; font-weight:800; color:#0E0918;
  background:var(--c); margin-inline-end:8px; }}
.rbtbl .cl {{ color:{_MU}; font-size:.74rem; }}
.rbtbl .up {{ color:{T.POS_FG}; }} .rbtbl .dn {{ color:{T.NEG_FG}; }}
.rbtw {{ overflow-x:auto; margin:0 0 12px; border-radius:16px; }}
.rbtl {{ position:relative; display:flex; flex-direction:column; gap:0; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:18px; padding:8px 14px; }}
.rbtl .e {{ position:relative; display:grid; grid-template-columns:38px minmax(0,1fr) auto; gap:12px; align-items:start; padding:10px 0;
  border-bottom:1px solid rgba(44,39,56,.6); animation:rbup .4s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--i) * 40ms); }}
.rbtl .e:last-child {{ border-bottom:0; }}
.rbtl .ti {{ width:36px; height:36px; border-radius:12px; display:flex; align-items:center; justify-content:center; color:#fff; background:var(--c); }}
.rbtl .ti .ms {{ font-size:1.15rem; color:#fff; }}
.rbtl b {{ color:#F4F1F8; font-size:.88rem; }} .rbtl p {{ margin:2px 0 0; color:#A8A2B3; font-size:.76rem; line-height:1.5; }}
.rbtl .dt {{ color:{_MU}; font-size:.74rem; white-space:nowrap; padding-top:2px; }}
.rbtl .am {{ color:#fff; font-weight:700; direction:ltr; unicode-bidi:isolate; }}
/* ---------- the Opportunity Bot ---------- */
.rbchip.bot {{ color:#FBCFE8; border-color:rgba(236,72,153,.45); background:rgba(236,72,153,.12); }} .rbchip.bot .ms {{ color:#EC4899; }}
.rbbot {{ position:relative; overflow:hidden; isolation:isolate; display:flex; gap:16px; align-items:flex-start; border-radius:20px; padding:18px 20px; margin:2px 0 12px;
  border:1px solid rgba(236,72,153,.38); background:radial-gradient(120% 140% at 100% 0%, rgba(236,72,153,.22), transparent 55%),
  radial-gradient(90% 120% at 0% 100%, rgba(123,69,240,.2), transparent 60%), linear-gradient(135deg,#170E22,#1C1230 60%,#140D20);
  box-shadow:0 18px 40px -22px rgba(236,72,153,.55), {T.GLOW}; animation:rbup .5s cubic-bezier(.2,.8,.2,1) both; }}
.rbbot .sweep {{ position:absolute; z-index:-1; top:-90px; inset-inline-end:-90px; width:260px; height:260px; border-radius:50%; pointer-events:none;
  background:conic-gradient(from 0deg, transparent 0deg, rgba(236,72,153,.32) 50deg, transparent 70deg),
  repeating-radial-gradient(circle, rgba(236,72,153,.16) 0 1px, transparent 1px 34px); animation:rbsweep 4.5s linear infinite; }}
@keyframes rbsweep {{ to {{ transform:rotate(360deg); }} }}
.rbbot .ic {{ flex:none; width:52px; height:52px; border-radius:16px; display:flex; align-items:center; justify-content:center;
  background:linear-gradient(140deg,#EC4899,#7B45F0); box-shadow:0 10px 24px -10px rgba(236,72,153,.8); }}
.rbbot .ic .ms {{ font-size:1.7rem; color:#fff; }}
.rbbot .tx {{ flex:1; min-width:0; }}
.rbbot .eb {{ color:#F9A8D4; font-size:.7rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; }}
.rbbot h3 {{ color:#fff; font-size:1.25rem; font-weight:800; margin:5px 0 6px; padding:0; }}
.rbbot p {{ color:#D9D2E3; font-size:.86rem; line-height:1.6; margin:0 0 10px; }}
.rbbot .sl {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-top:10px; color:#E9E5F0; font-size:.8rem; border-top:1px dashed rgba(236,72,153,.3); padding-top:9px; }}
.rbbot .sl .ms {{ color:#F9A8D4; font-size:1.05rem; }}
.rbsub {{ display:flex; align-items:center; gap:8px; color:#E9E5F0; font-weight:700; font-size:.9rem; margin:4px 0 8px; }}
.rbsub .ms {{ color:#EC4899; }}
.rbsd {{ display:inline-flex; align-items:center; gap:3px; border-radius:999px; padding:2px 8px 2px 6px; font-size:.68rem; font-weight:800; }}
.rbsd .ms {{ font-size:.85rem; }}
.rbsd.long {{ color:#86EFAC; background:rgba(34,197,94,.14); border:1px solid rgba(74,222,128,.4); }}
.rbsd.short {{ color:#FCA5A5; background:rgba(239,68,68,.14); border:1px solid rgba(248,113,113,.4); }}
.rbwc {{ display:inline-block; border-radius:7px; padding:2px 7px; font-size:.68rem; font-weight:600; color:#DCD7E3; background:rgba(157,151,165,.13);
  border:1px solid rgba(157,151,165,.22); margin:0 4px 4px 0; }}
.rbnote2 {{ display:flex; gap:12px; align-items:flex-start; border-radius:16px; padding:12px 15px; margin:0 0 12px;
  border:1px solid rgba(236,72,153,.4); background:linear-gradient(135deg,rgba(236,72,153,.13),transparent 70%), {T.BOX_BG}; }}
.rbnote2 > .ms {{ font-size:1.5rem; color:#F9A8D4; margin-top:2px; }}
.rbnote2 b {{ color:#fff; font-size:.9rem; }} .rbnote2 span {{ color:#B9B3C4; font-size:.76rem; }}
.rbnote2 .tks {{ display:flex; flex-wrap:wrap; gap:6px; margin:7px 0 6px; }}
.rbtk {{ display:inline-flex; align-items:center; gap:3px; border-radius:8px; padding:3px 9px 3px 7px; font-size:.8rem; font-weight:800; }}
.rbtk .ms {{ font-size:.9rem; }}
.rbtk.long {{ color:#86EFAC; background:rgba(34,197,94,.13); border:1px solid rgba(74,222,128,.4); }}
.rbtk.short {{ color:#FCA5A5; background:rgba(239,68,68,.13); border:1px solid rgba(248,113,113,.4); }}
.rbtk.none {{ color:#B9B3C4; font-weight:600; border:1px dashed rgba(157,151,165,.4); }}
.rbplan td {{ vertical-align:middle; }}
.rbplan tr.nx td {{ opacity:.55; }}
.rbplan .cco {{ display:flex; align-items:center; gap:4px; }}
.rbplan .wy {{ white-space:normal; margin-top:5px; max-width:330px; }}
.rbplan-c {{ display:none; }}
@media (max-width: 640px) {{ .rbplan-t {{ display:none; }} .rbplan-c {{ display:flex; flex-direction:column; gap:8px; margin:0 0 10px; }} }}
.rbpq {{ position:relative; overflow:hidden; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:14px; padding:10px 12px;
  animation:rbup .4s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--i) * 40ms); }}
.rbpq::before {{ content:""; position:absolute; inset-inline-start:0; top:0; bottom:0; width:3px; background:#4ADE80; }}
.rbpq.short::before {{ background:#F87171; }}
.rbpq.nx {{ opacity:.6; }}
.rbpq .top {{ display:flex; align-items:center; gap:6px; }}
.rbpq .tk {{ font-weight:800; color:#fff; }}
.rbpq .scr {{ margin-inline-start:auto; width:40px; height:40px; flex:none; }} .rbpq .scr svg {{ width:40px; height:40px; display:block; }}
.rbscr {{ display:inline-block; width:34px; height:34px; vertical-align:middle; }} .rbscr svg {{ width:34px; height:34px; display:block; }}
.rbsck {{ display:flex; align-items:center; gap:10px; color:#B9B3C4; font-size:.74rem; line-height:1.5; margin:0 0 10px; }}
.rbsck svg {{ width:30px; height:30px; flex:none; }} .rbsck b {{ color:#F4F1F8; }}
.rbpq .nm {{ color:{_MU}; font-size:.74rem; margin:1px 0 6px; }}
.rbpq .rr {{ display:flex; justify-content:space-between; gap:8px; color:#B9B3C4; font-size:.76rem; margin:2px 0; }}
.rbpq .rr b {{ color:#F4F1F8; }} .rbpq .rr b.dn {{ color:{T.NEG_FG}; }}
.rbpq .wy {{ margin-top:6px; }}
.rbnx {{ display:inline-block; margin-inline-start:6px; border-radius:6px; padding:1px 6px; font-size:.64rem; font-weight:700; color:#FCD34D;
  border:1px dashed rgba(245,185,74,.5); }}
.rbxh {{ display:inline-block; margin-inline-start:4px; border-radius:6px; padding:0 5px; font-size:.6rem; font-weight:700; white-space:nowrap;
  color:#C4B5FD; background:rgba(139,92,246,.14); border:1px solid rgba(139,92,246,.35); }}
.rbxh.pm {{ color:#7DD3FC; background:rgba(56,189,248,.12); border-color:rgba(56,189,248,.35); }}
.rbds {{ display:inline-block; vertical-align:middle; width:46px; height:6px; border-radius:4px; background:rgba(157,151,165,.16); overflow:hidden; direction:ltr; }}
.rbds i {{ display:block; height:100%; background:#F87171; }} .rbds i.short {{ background:#F97316; }}
.rbrules {{ display:flex; gap:8px; align-items:flex-start; color:#B9B3C4; font-size:.76rem; line-height:1.55; margin:8px 0 12px; }}
.rbrules .ms {{ color:#F9A8D4; font-size:1.05rem; }}
.rbgrp2 {{ display:flex; align-items:center; gap:6px; font-size:.78rem; font-weight:700; margin:2px 0 7px; }}
.rbgrp2 .ms {{ font-size:1rem; }} .rbgrp2.long {{ color:#86EFAC; }} .rbgrp2.short {{ color:#FCA5A5; }}
.rbrad {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(205px,1fr)); gap:10px; margin:0 0 12px; }}
.rbrc {{ position:relative; overflow:hidden; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:12px 13px 11px;
  animation:rbup .45s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--i) * 45ms); transition:transform .2s, border-color .2s; }}
.rbrc:hover {{ transform:translateY(-2px); border-color:rgba(236,72,153,.5); }}
.rbrc::before {{ content:""; position:absolute; inset-inline-start:0; top:0; bottom:0; width:3px; background:#4ADE80; }}
.rbrc.short::before {{ background:#F87171; }}
.rbrc .top {{ display:flex; align-items:center; gap:7px; }}
.rbrc .tk, .rbpc .tk {{ font-weight:800; font-size:.95rem; color:#fff; letter-spacing:.02em; }}
.rbrc .ring {{ margin-inline-start:auto; width:40px; height:40px; }} .rbrc .ring svg {{ width:40px; height:40px; display:block; }}
.rbrc .nm {{ color:#E9E5F0; font-size:.8rem; font-weight:600; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.rbrc .th, .rbpc .th {{ display:flex; align-items:center; gap:4px; color:{_MU}; font-size:.7rem; margin:2px 0 6px; }}
.rbrc .th .ms, .rbpc .th .ms {{ font-size:.85rem; color:#F9A8D4; }}
.rbrc .rpx {{ color:#CFC8DA; font-size:.78rem; margin-bottom:6px; }}
.rbrc .ch, .rbpc .ch {{ min-height:22px; }}
.rbrc .sg {{ display:inline-flex; align-items:center; gap:4px; margin-top:4px; font-size:.7rem; font-weight:700; color:{_MU}; }}
.rbrc .sg .ms {{ font-size:.9rem; }}
.rbrc .sg.on {{ color:#FCD34D; }}
.rbpcs {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:10px; margin:0 0 12px; }}
.rbpc {{ position:relative; overflow:hidden; background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:16px; padding:12px 14px;
  animation:rbup .45s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--i) * 45ms); }}
.rbpc::before {{ content:""; position:absolute; inset-inline-start:0; top:0; bottom:0; width:3px; background:#4ADE80; }}
.rbpc.short::before {{ background:#F87171; }}
.rbpc .top {{ display:flex; align-items:center; gap:7px; }}
.rbpc .ret {{ margin-inline-start:auto; font-size:1.15rem; font-weight:800; }}
.rbpc .ret.up {{ color:{T.POS_FG}; }} .rbpc .ret.dn {{ color:{T.NEG_FG}; }}
.rbpc .pp {{ display:flex; align-items:center; gap:6px; color:#E9E5F0; font-size:.86rem; font-weight:600; }}
.rbpc .pp .ms {{ font-size:1rem; color:{_MU}; }}
.rbpc .meta {{ display:flex; justify-content:space-between; gap:8px; color:{_MU}; font-size:.72rem; margin:6px 0 4px; }}
.rbpc .bar {{ height:5px; border-radius:5px; background:rgba(157,151,165,.16); overflow:hidden; margin-bottom:8px; }}
.rbpc .bar i {{ display:block; height:100%; background:linear-gradient(90deg,#7B45F0,#EC4899); }}
.rblock {{ display:flex; gap:12px; align-items:center; border-radius:16px; padding:13px 16px; margin:2px 0 12px; border:1px dashed rgba(236,72,153,.4);
  background:linear-gradient(135deg,rgba(236,72,153,.08),transparent 70%); }}
.rblock > .ms {{ font-size:1.6rem; color:#F9A8D4; }}
.rblock b {{ display:block; color:#fff; font-size:.92rem; }} .rblock span {{ color:#B9B3C4; font-size:.8rem; line-height:1.55; }}

/* ---------- stress tests, monthly returns ---------- */
.rbscn {{ background:{T.BOX_BG}; border:1px solid {_BD}; border-radius:18px; padding:14px 16px 12px; }}
.rbscn .hd {{ display:flex; align-items:center; gap:8px; color:#fff; font-weight:700; font-size:.95rem; margin-bottom:8px; }}
.rbscn .hd .ms {{ color:{T.GOLD}; }}
.rbscn .r {{ padding:8px 0; border-top:1px solid rgba(44,39,56,.7); animation:rbup .45s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--i) * 70ms); }}
.rbscn .r:first-of-type {{ border-top:0; }}
.rbscn .h {{ display:flex; justify-content:space-between; gap:8px; margin-bottom:5px; }}
.rbscn .h b {{ color:#F4F1F8; font-size:.84rem; }} .rbscn .h span {{ color:{_MU}; font-size:.7rem; }}
.rbscn .b {{ display:grid; grid-template-columns:72px minmax(0,1fr) 46px; gap:8px; align-items:center; margin:3px 0; }}
.rbscn .lb {{ color:#B9B3C4; font-size:.7rem; }}
.rbscn .tr {{ display:block; height:9px; border-radius:6px; background:rgba(157,151,165,.12); overflow:hidden; direction:ltr; }}
.rbscn .tr i {{ display:block; height:100%; border-radius:6px; background:rgba(157,151,165,.55); animation:rbbar 1s cubic-bezier(.2,.8,.2,1) both; }}
.rbscn .tr i.me {{ background:linear-gradient(90deg,#F87171,#F97316); }}
.rbscn em {{ font-style:normal; font-weight:800; font-size:.8rem; text-align:end; }}
.rbscn em.dn {{ color:{T.NEG_FG}; }} .rbscn em.up {{ color:{T.POS_FG}; }}
.rbscn .ft {{ color:{_MU}; font-size:.7rem; margin-top:6px; line-height:1.45; }}
.rbheat {{ width:100%; border-collapse:separate; border-spacing:3px; font-size:.74rem; }}
.rbheat th {{ color:{_MU}; font-weight:700; padding:4px; text-align:center; white-space:nowrap; font-size:.68rem; }}
.rbheat td {{ color:#F4F1F8; text-align:center; padding:7px 4px; border-radius:7px; background:rgba(157,151,165,.06); font-weight:600; white-space:nowrap; }}
.rbheat td.yr {{ background:transparent; font-weight:800; }} .rbheat td.yr.up {{ color:{T.POS_FG}; }} .rbheat td.yr.dn {{ color:{T.NEG_FG}; }}
@media (max-width: 640px) {{ .rbbot {{ flex-direction:column; padding:16px; }} .rbheat {{ font-size:.66rem; }} }}
</style>"""


# =====================================================================
# small pieces
# =====================================================================
def _m(v, dec=0, sign=False):
    return PP._m(v, dec, sign)


def _tk(t):
    """A fund as the robo shows it: its ticker (VTI), or a Tadawul fund by its name (its code is a number)."""
    return T.sym_label(t)


def _sa():
    """The Saudi market's robo (its own account, in riyals, in the funds listed on Tadawul)."""
    return MK.is_sa()


def _cur():
    """($) / (SAR) / (ر.س) for the amount fields."""
    return PP._cur()


def _tp():
    """The money prefix of the charts' axes and tooltips."""
    return "SAR " if _sa() else "$"


def _bench_txt(short=False):
    """The benchmark in words: global stocks (VT) and US bonds (BND) / Saudi stocks (9400) and Saudi sukuk (9403)."""
    if _sa():
        return L("Saudi stocks/sukuk", "أسهم/صكوك سعودية") if short else L("Saudi stocks (YAQEEN fund) and Saudi government sukuk (Albilad fund)",
                                                                            "أسهم سعودية (صندوق يقين) وصكوك حكومية سعودية (صندوق البلاد)")
    return "VT/BND" if short else L("global stocks (VT) and US bonds (BND)", "أسهم عالمية (VT) وسندات أمريكية (BND)")


def _p(v, dec=1, sign=False):
    return PP._p(v, dec, sign)


def _esc(s):
    return T.esc(s)


def _fwd():
    return ":material/arrow_back:" if is_ar() else ":material/arrow_forward:"     # forward points left in Arabic


def _back():
    return ":material/arrow_forward:" if is_ar() else ":material/arrow_back:"


def _ltr(s):
    """A left-to-right run (a number, a ticker with an amount) kept whole inside Arabic text (HTML)."""
    return f'<bdi dir="ltr">{s}</bdi>'


def _i(s):
    """The same for plain text (escaped later): Unicode isolates."""
    return f"\u2066{s}\u2069"


def _date(d):
    d = pd.Timestamp(d)
    return f"{d.day} {MONTHS_AR[d.month - 1]} {d.year}" if is_ar() else d.strftime("%b %-d, %Y")


def _lab(o):
    return o[3] if is_ar() else o[2]


def _sub(o):
    return o[5] if is_ar() else o[4]


def _qtext(q):
    return q["ar"] if is_ar() else q["en"]


def _fund(t):
    f = R.FUNDS.get(t, (t, t, t, "#9D97A5", "stocks"))
    return {"name": f[0], "cls": f[2] if is_ar() else f[1], "c": f[3], "g": f[4]}


def _prof_name(lv):
    en, ar = R.PROFILES[int(lv)]
    return L(en, ar)


def _answer(qid, ans):
    o = R.opt(qid, ans.get(qid))
    return _lab(o) if o else "—"


def _flash():
    msg = ss.pop("rb_flash", None)
    if msg:
        st.toast(msg, icon=":material/task_alt:")


def note():
    return (f'<div class="rbnote">{T.icon("info")}<span>{L("Virtual money on real prices, for learning: not investment advice. Expected returns are long-run estimates, not promises; past results do not repeat.", "فلوس افتراضية على أسعار حقيقية بهدف التعلم، وليست توصية استثمارية. العوائد المتوقعة تقديرات طويلة المدى وليست وعود، والنتائج السابقة ما تتكرر بالضرورة.")}</span></div>')


# =====================================================================
# introduction
# =====================================================================
def _art():
    segs, start = [], 0.0
    for w, c in ((34, "#3B8BEB"), (18, "#2DB6EB"), (10, "#7B45F0"), (22, "#34D399"), (8, "#F97316"), (8, "#F5B94A")):
        segs.append(f'<circle cx="150" cy="150" r="118" fill="none" stroke="{c}" stroke-width="16" pathLength="100" '
                    f'stroke-dasharray="{w - 1.2:.1f} {100 - w + 1.2:.1f}" stroke-dashoffset="{-start:.1f}" stroke-linecap="round"/>')
        start += w
    dots = "".join(f'<circle cx="{150 + 140 * math.cos(a):.1f}" cy="{150 + 140 * math.sin(a):.1f}" r="{r}" fill="{c}"/>'
                   for a, r, c in ((0.3, 4, "#7DD3FC"), (2.2, 3, "#C4B5FD"), (4.1, 5, "#FCD34D")))
    return (f'<div class="rbart"><svg viewBox="0 0 300 300"><circle cx="150" cy="150" r="140" fill="none" stroke="rgba(167,139,250,.18)" stroke-dasharray="2 7"/>'
            f'<g>{dots}<animateTransform attributeName="transform" type="rotate" from="360 150 150" to="0 150 150" dur="18s" repeatCount="indefinite"/></g>'
            f'<g><g transform="rotate(-90 150 150)">{"".join(segs)}</g><animateTransform attributeName="transform" type="rotate" from="0 150 150" '
            f'to="360 150 150" dur="28s" repeatCount="indefinite"/></g>'
            f'<circle cx="150" cy="150" r="96" fill="none" stroke="rgba(45,182,235,.16)" stroke-width="1"/></svg>'
            f'<div class="core">{T.icon("smart_toy")}</div></div>')


def _intro_p():
    if _sa():
        return L("Answer a short questionnaire in the shape of an Investment Policy Statement (IPS). The robo builds a diversified portfolio "
                 "of the funds listed on Tadawul (Saudi stocks, US stocks, Saudi government sukuk, gold), in riyals, then runs it on autopilot.",
                 "جاوب على استبيان قصير مبني على بيان سياسة الاستثمار (IPS). المستشار الآلي يبني لك محفظة متنوعة من الصناديق المتداولة في "
                 "تداول (أسهم سعودية وأسهم أمريكية وصكوك حكومية سعودية وذهب) بالريال، وبعدها يديرها تلقائياً.")
    return L("Answer a short questionnaire in the shape of an Investment Policy Statement (IPS). The robo builds a diversified portfolio of ETFs that fits you, then runs it on autopilot.",
             "جاوب على استبيان قصير مبني على بيان سياسة الاستثمار (IPS). المستشار الآلي يبني لك محفظة متنوعة من صناديق المؤشرات تناسبك، وبعدها يديرها تلقائياً.")


def intro(has_store=True):
    nq = len(R.QIDS)
    steps = [("quiz", L(f"Answer {nq} questions", f"جاوب على {nq} سؤال"),
              L("Your goals, time horizon, and the risk you are able and willing to take: the heart of an IPS.",
                "أهدافك ومدة استثمارك والمخاطرة اللي تقدر عليها وتتقبلها: هذا قلب بيان سياسة الاستثمار.")),
             ("donut_large", L("Get your plan", "استلم خطتك"),
              (L("A risk level from 1 to 10, a mix of the ETFs listed on Tadawul, what to expect, and your IPS to download.",
                 "مستوى مخاطرة من 1 إلى 10، ومزيج من الصناديق المتداولة في تداول، والمتوقع، وبيان السياسة للتحميل.") if _sa() else
               L("A risk level from 1 to 10, a mix of low-cost ETFs, what to expect, and your IPS to download.",
                 "مستوى مخاطرة من 1 إلى 10، ومزيج من صناديق المؤشرات منخفضة التكلفة، والمتوقع، وبيان السياسة للتحميل."))),
             ("autorenew", L("Let it run", "خلها تشتغل"),
              L("Monthly deposits, rebalancing and reinvested dividends, all done for you every day.",
                "إيداعات شهرية وإعادة توازن وإعادة استثمار التوزيعات، كلها تنعمل عنك كل يوم."))]
    steps_html = "".join(f'<div class="rbstep" style="--i:{i}" data-k="{i + 1}"><div class="n">{T.icon(ic)}</div><b>{_esc(t)}</b><span>{_esc(s)}</span></div>'
                         for i, (ic, t, s) in enumerate(steps))
    ui.html(f'<div class="rbhero"><div><div class="eb">{T.icon("smart_toy")}{L("TURA Robo Advisor", "المستشار الآلي من TURA")}</div>'
            f'<h1>{L("Your portfolio, <em>built from your goals</em> and managed for you", "محفظتك <em>مبنية على أهدافك</em> وتُدار عنك")}</h1>'
            f'<p>{_intro_p()}</p>'
            f'<div class="rbchips"><span class="rbchip">{T.icon("timer")}{L("About 2 minutes", "تقريباً دقيقتين")}</span>'
            f'<span class="rbchip">{T.icon("payments")}{L("Virtual money", "فلوس افتراضية")}</span>'
            f'<span class="rbchip">{T.icon("lock")}{L("Yours only, kept in this browser", "خاصة فيك ومحفوظة بمتصفحك")}</span>'
            + ("" if _sa() else f'<span class="rbchip gold">{T.icon("mosque")}{L("Sharia-compliant option", "خيار متوافق مع الشريعة")}</span>')
            + f'<span class="rbchip">{T.icon("description")}{L("Your IPS to download", "بيان السياسة للتحميل")}</span>'
            + ("" if _sa() else f'<span class="rbchip bot">{T.icon("radar")}{L("Opportunity Bot at levels 9–10", "بوت الفرص في المستوى 9–10")}</span>')
            + f'</div></div>{_art()}</div>'
            f'<div class="rbsteps">{steps_html}</div>')
    done = sum(1 for q in R.QIDS if (ss.get("rb_ans") or {}).get(q))
    if done:                                   # a questionnaire left half way: carry on from where it stopped, or start again
        c1, c2, c3, c4 = st.columns([.6, 1.2, 1, .6])
        with c2:
            if st.button(L(f"Continue · {done} of {len(R.QIDS)} answered", f"كمّل · جاوبت {done} من {len(R.QIDS)}"), type="primary",
                         width="stretch", key="rb_resume", icon=_fwd()):
                ss["rb_mode"] = "plan" if done == len(R.QIDS) and (ss.get("rb_ans") or {}).get("amount") else "quiz"
                ss["rb_step"] = min(done, len(R.STEPS) - 1)
                st.rerun()
        with c3:
            if st.button(L("Start again", "ابدأ من جديد"), width="stretch", key="rb_start", icon=":material/restart_alt:"):
                ss["rb_ans"], ss["rb_step"], ss["rb_mode"] = {}, 0, "quiz"
                for k in ("rb_amt", "rb_mon", "rb_lvl", "rb_years", "rb_goal"):
                    ss.pop(k, None)
                st.rerun()
    else:
        c1, c2, c3 = st.columns([1, 1.3, 1])
        with c2:
            if st.button(L("Start the questionnaire", "ابدأ الاستبيان"), type="primary", width="stretch", key="rb_start", icon=_fwd()):
                ss["rb_mode"] = "quiz"
                ss["rb_step"] = 0
                ss.setdefault("rb_ans", {})
                st.rerun()
    feats = [("balance", L("Rebalancing", "إعادة التوازن"), L("Back to target every quarter, and at once when a fund drifts out of its range.",
                                                               "يرجع للنسب المستهدفة كل ربع، وفوراً إذا خرج صندوق عن نطاقه.")),
             ("savings", L("Monthly deposits", "إيداع شهري"), L("Invested on the first trading day of each month, into what is under target first.",
                                                                 "يُستثمر أول يوم تداول من كل شهر، في الأقل من نسبته أولاً.")),
             ("currency_exchange", L("Dividends reinvested", "إعادة استثمار التوزيعات"), L("Every dividend goes back into the portfolio.",
                                                                                         "كل توزيع يرجع يُستثمر في المحفظة.")),
             ("monitoring", L("Clear tracking", "متابعة واضحة"), L("Value against the money invested and a fair benchmark, and everything the robo did.",
                                                                   "القيمة مقابل المبلغ المستثمر ومؤشر مرجعي عادل، وكل اللي سواه المستشار.")),
             ("radar", L("Opportunity Bot", "بوت الفرص"), L("At levels 9 and 10 it hunts emerging companies and explosive moves, long and short.",
                                                            "في المستوى 9 و10 يصطاد الشركات الناشئة والانفجارات السعرية، شراء وبيع على المكشوف.")),
             ("thunderstorm", L("Stress tests", "اختبارات الضغط"), L("How the plan would have held up in 2008, 2020 and 2022.",
                                                                    "كيف بتصمد الخطة في 2008 و2020 و2022.")),
             ("flag", L("Goal odds", "احتمال الهدف"), L("Set a target amount and see the chance of reaching it in time.",
                                                       "حط مبلغ تستهدفه وشوف احتمال توصله في الوقت.")),
             ("mosque", L("Sharia-compliant option", "خيار متوافق مع الشريعة"), L("Islamic funds and sukuk; the bot buys only, from a screened list.",
                                                                                "صناديق إسلامية وصكوك، والبوت يشتري فقط من قائمة مفلترة."))]
    if _sa():                                  # the Saudi robo: no Opportunity Bot, the oil crash among its storms, its funds Islamic
        feats = [f for f in feats if f[0] not in ("radar", "thunderstorm", "mosque")]
        feats.insert(4, ("thunderstorm", L("Stress tests", "اختبارات الضغط"), L("How the plan would have held up in 2008, the 2014–16 oil crash, 2020 and 2022.",
                                                                               "كيف بتصمد الخطة في 2008 وانهيار النفط 2014–2016 و2020 و2022.")))
        feats.append(("account_balance", L("Listed on Tadawul", "متداولة في تداول"), L("Every fund trades on the Saudi exchange, Sunday to Thursday, in riyals.",
                                                                                     "كل الصناديق متداولة في السوق السعودي، من الأحد للخميس، بالريال.")))
    ui.html('<div class="rbfeat">' + "".join(f'<div>{T.icon(ic)}<b>{_esc(t)}</b><span>{_esc(s)}</span></div>' for ic, t, s in feats) + "</div>" + note())


# =====================================================================
# the questionnaire
# =====================================================================
def _sec_of(step):
    sid = R.STEPS[step]
    return "fund" if sid == "fund" else R.Q[sid]["sec"]


def progress_html(step, ans):
    n = len(R.STEPS)
    cur = _sec_of(step)
    order = [s[0] for s in R.SECTIONS]
    ci = order.index(cur)
    secs = "".join(f'<span class="{"done" if i < ci else "cur" if i == ci else ""}">{T.icon("check_circle" if i < ci else ic)}<em>{_esc(L(en, ar))}</em></span>'
                   for i, (k, ic, en, ar) in enumerate(R.SECTIONS))
    lv = R.partial_level(ans)
    segs = "".join(f'<i style="background:{LEVEL_COLORS[i] if lv and i < lv else "rgba(157,151,165,.18)"}"></i>' for i in range(10))
    meter = (f'<span class="rbmeter">{L("Risk level so far", "مستوى المخاطرة حتى الآن")} <b>{lv}</b><span class="segs">{segs}</span></span>' if lv else
             f'<span class="rbmeter">{L("Your risk level builds as you answer", "مستوى المخاطرة يتكوّن مع إجاباتك")}<span class="segs">{segs}</span></span>')
    w = (step + 1) / n * 100
    w0 = step / n * 100
    return (f'<div class="rbprog"><div class="top"><span class="qn">{L("Step", "الخطوة")} {step + 1} <em>{L("of", "من")} {n}</em></span>{meter}</div>'
            f'<div class="bar"><i style="width:{w:.1f}%;--w0:{w0:.1f}%"></i></div><div class="secs">{secs}</div></div>')


def _drop_viz():
    pts = [(0, 30), (40, 26), (80, 31), (120, 22), (160, 25), (200, 18), (240, 40), (280, 52), (320, 70), (360, 64), (400, 82)]
    line = " ".join(f"{x},{y}" for x, y in pts)
    return (f'<svg class="rbdrop" viewBox="0 0 520 96" preserveAspectRatio="xMinYMid meet"><defs><linearGradient id="rbdg" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="#F87171" stop-opacity=".35"/><stop offset="1" stop-color="#F87171" stop-opacity="0"/></linearGradient></defs>'
            f'<line x1="0" y1="18" x2="420" y2="18" stroke="rgba(157,151,165,.35)" stroke-dasharray="3 5"/>'
            f'<polygon points="0,96 {line} 400,96" fill="url(#rbdg)" class="tg"/>'
            f'<polyline class="ln" points="{line}" fill="none" stroke="#F87171" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<g class="tg"><circle cx="400" cy="82" r="5" fill="#F87171" stroke="#fff" stroke-width="2"/>'
            f'<rect x="416" y="62" rx="9" width="78" height="30" fill="rgba(248,113,113,.16)" stroke="#F87171"/>'
            f'<text x="455" y="83" text-anchor="middle" fill="#FCA5A5" font-size="17" font-weight="800">−20%</text>'
            f'<text x="455" y="54" text-anchor="middle" fill="#B9B3C4" font-size="11">{_esc(L("a few months", "خلال كم شهر"))}</text></g></svg>')


def tile_html(q, o, i, on):
    k = "on" if on else ""
    tall = " tall" if any(x[4] for x in q["opts"]) else ""
    ck = f'<span class="ck">{T.icon("check")}</span>'
    x = o[7]
    if q["id"] == "maxloss":
        dep = min(x["loss"], 45) / 45 * 100
        body = f'<span class="big">{_esc(_lab(o))}</span><span class="tx"><span>{_esc(_sub(o))}</span></span><span class="dep"><i style="height:{dep:.0f}%"></i></span>'
    elif q["id"] == "risk":
        stocks = R.stock_share(R.sleeves(x["lv"]))
        body = (f'<span class="ic">{T.icon(o[1])}</span><span class="tx"><b>{_esc(_lab(o))}</b><span>{_esc(_sub(o))}</span>'
                f'<span class="mixw"><span class="mix"><i style="width:{stocks:.0f}%"></i></span>'
                f'<em>{L("stocks", "أسهم")} {_ltr("%.0f%%" % stocks)}</em></span></span>')
    elif q["id"] == "range":
        lo, hi = abs(x["lo"]) / 40 * 50, x["hi"] / 40 * 50
        body = (f'<span class="big">{_esc(_lab(o))}</span><span class="rng"><span class="tr"><i class="lo" style="width:{lo:.1f}%"></i>'
                f'<i class="hi" style="width:{hi:.1f}%"></i></span><span class="lb"><span class="d">{x["lo"]:+d}%</span><span class="u">{x["hi"]:+d}%</span></span></span>')
    else:
        sub = f"<span>{_esc(_sub(o))}</span>" if _sub(o) else ""
        body = f'<span class="ic">{T.icon(o[1])}</span><span class="tx"><b>{_esc(_lab(o))}</b>{sub}</span>'
    return f'<div class="rbo {k}{tall}" style="--i:{i}">{ck}{body}</div>'


def question(q, ans, step):
    sec = next(s for s in R.SECTIONS if s[0] == q["sec"])
    viz = f'<div class="viz">{_drop_viz()}</div>' if q["id"] == "drop" else ""
    if q["id"] == "range":
        viz = f'<div class="viz rbchips"><span class="rbchip">{T.icon("swap_vert")}{L("Each tile: a bad year · a good year", "كل خيار: سنة سيئة · سنة جيدة")}</span></div>'
    ui.html(f'<div class="rbq"><div class="k">{T.icon(sec[1])}{_esc(L(sec[2], sec[3]))}</div><h2>{_esc(_qtext(q))}</h2>'
            f'<div class="why">{T.icon("lightbulb")}<span>{_esc(L(q["why_en"], q["why_ar"]))}</span></div>{viz}</div>')
    opts = q["opts"]
    n = len(opts)
    cols = st.columns(n, gap="small")
    for i, o in enumerate(opts):
        with cols[i], st.container(key=f"rbt_{q['id']}_{i}"):
            ui.html(tile_html(q, o, i, ans.get(q["id"]) == o[0]))
            if st.button(_lab(o), key=f"rbb_{q['id']}_{i}", width="stretch"):
                ans[q["id"]] = o[0]
                ss["rb_ans"] = ans
                ss["rb_step"] = step + 1
                st.rerun()


def funding(ans, step):
    sec = R.SECTIONS[-1]
    ui.html(f'<div class="rbq"><div class="k">{T.icon(sec[1])}{_esc(L(sec[2], sec[3]))}</div>'
            f'<h2>{L("How much will you invest?", "كم بتستثمر؟")}</h2><div class="why">{T.icon("lightbulb")}<span>'
            f'{L("Virtual money: try any amount. Regular monthly deposits are the quiet engine of long-term results.", "فلوس افتراضية فجرّب أي مبلغ. الإيداع الشهري المنتظم هو المحرك الهادي للنتائج على المدى الطويل.")}</span></div></div>')
    ss.setdefault("rb_amt", int(ans.get("amount") or 10000))
    ss.setdefault("rb_mon", int(ans.get("monthly") if ans.get("monthly") is not None else 500))
    has = bool(ss.get("rb_has"))
    c1, c2 = st.columns(2)
    with c1:
        amount = st.number_input(L(f"Starting amount ({_cur()})", f"المبلغ المبدئي ({_cur()})"), min_value=1000, max_value=10_000_000, step=1000, key="rb_amt",
                                 disabled=has, help=L("Already invested: add or withdraw money from Manage on the dashboard.",
                                                      "مستثمر من قبل: تقدر تودع أو تسحب من الإدارة في لوحة المحفظة.") if has else None)
    with c2:
        monthly = st.number_input(L(f"Monthly deposit ({_cur()})", f"الإيداع الشهري ({_cur()})"), min_value=0, max_value=1_000_000, step=50, key="rb_mon")
    prof = R.profile(ans)
    years = prof["years"]
    proj = R.project(prof["mu"], prof["vol"], amount, monthly, years, n=600)
    ui.html(f'<div class="rbfund"><div><div class="l">{T.icon("savings")}{L("You invest", "اللي بتحطه")}</div><div class="v">{_m(proj["invested"].iloc[-1])}</div>'
            f'<div class="s">{L(f"over {years} years", f"خلال {years} سنة")}</div></div>'
            f'<div><div class="l">{T.icon("insights")}{L("A middle outcome", "نتيجة متوسطة")}</div><div class="v">{_m(proj["p50"].iloc[-1])}</div>'
            f'<div class="s">{L("half the paths end above it", "نص الاحتمالات تنتهي فوقها")}</div></div>'
            f'<div><div class="l">{T.icon("shield")}{L("A weak outcome", "نتيجة ضعيفة")}</div><div class="v">{_m(proj["p10"].iloc[-1])}</div>'
            f'<div class="s">{L("9 in 10 paths end above it", "9 من 10 احتمالات تنتهي فوقها")}</div></div></div>')
    b1, b2, b3 = st.columns([1, 1.4, 1])
    with b2:
        if st.button(L("See my plan", "اعرض خطتي"), type="primary", width="stretch", key="rb_build", icon=":material/auto_awesome:"):
            ans["amount"], ans["monthly"] = int(amount), int(monthly)
            ss["rb_ans"] = ans
            ss["rb_mode"] = "plan"
            ss.pop("rb_lvl", None)
            st.rerun()


def quiz():
    ans = ss.setdefault("rb_ans", {})
    step = int(min(max(ss.get("rb_step", 0), 0), len(R.STEPS) - 1))
    ss["rb_step"] = step
    ui.html(progress_html(step, ans))
    sid = R.STEPS[step]
    if sid == "fund":
        funding(ans, step)
    else:
        question(R.Q[sid], ans, step)
    n1, n2, n3 = st.columns([1, 2.2, 1])
    with n1:
        if step > 0 and st.button(L("Back", "رجوع"), key="rb_back", icon=_back(), width="stretch"):
            ss["rb_step"] = step - 1
            st.rerun()
        if step == 0 and st.button(L("Exit", "خروج"), key="rb_exit", icon=":material/close:", width="stretch"):
            ss["rb_mode"] = None
            st.rerun()
    with n3:
        if sid != "fund" and ans.get(sid) is not None and st.button(L("Next", "التالي"), key="rb_next", icon=_fwd(), width="stretch"):
            ss["rb_step"] = step + 1
            st.rerun()


# =====================================================================
# the plan
# =====================================================================
def gauge_svg(level):
    cx, cy, r = 110, 110, 86
    segs = []
    for i in range(10):
        a0 = math.radians(180 + i * 18 + 1.2)
        a1 = math.radians(180 + (i + 1) * 18 - 1.2)
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        on = i < level
        segs.append(f'<path class="seg" style="animation-delay:{i * 60}ms" d="M{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f}" fill="none" '
                    f'stroke="{LEVEL_COLORS[i]}" stroke-opacity="{1 if on else .18}" stroke-width="18"/>')
    ang = -90 + (level - 0.5) * 18
    ticks = "".join(f'<text x="{cx + (r + 22) * math.cos(math.radians(180 + (k - .5) * 18)):.1f}" y="{cy + (r + 22) * math.sin(math.radians(180 + (k - .5) * 18)) + 4:.1f}" '
                    f'text-anchor="middle" font-size="10" fill="#8E889A">{k}</text>' for k in (1, 5, 10))
    col = LEVEL_COLORS[level - 1]
    return (f'<div class="rbg"><svg viewBox="0 0 220 132">{"".join(segs)}{ticks}'
            f'<g transform="rotate({ang:.1f} {cx} {cy})"><line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy - r + 16}" stroke="#fff" stroke-width="4" stroke-linecap="round"/>'
            f'<animateTransform attributeName="transform" type="rotate" from="-90 {cx} {cy}" to="{ang:.1f} {cx} {cy}" dur="1.1s" fill="freeze" '
            f'calcMode="spline" keyTimes="0;1" keySplines=".3 .9 .4 1"/></g>'
            f'<circle cx="{cx}" cy="{cy}" r="11" fill="{col}" stroke="#fff" stroke-width="3"/>'
            f'</svg></div>')


def _why_text(prof):
    ab, wl, raw, rec = prof["ability"], prof["will"], prof["raw"], prof["rec"]
    if prof["governs"] == "ability":
        s = L(f"You are more willing ({wl:.1f}/10) than able ({ab:.1f}/10) to take risk. A sound policy follows the lower of the two, so your ability sets the level.",
              f"رغبتك في المخاطرة ({wl:.1f}/10) أعلى من قدرتك عليها ({ab:.1f}/10). السياسة السليمة تتبع الأقل من الاثنين، فقدرتك هي اللي تحدد المستوى.")
    elif prof["governs"] == "will":
        s = L(f"You are able ({ab:.1f}/10) to take more risk than you are willing to ({wl:.1f}/10). The plan follows your comfort: a portfolio you can stay with beats one you abandon.",
              f"قدرتك على المخاطرة ({ab:.1f}/10) أعلى من رغبتك فيها ({wl:.1f}/10). الخطة تتبع راحتك: المحفظة اللي تقدر تكمل معها أفضل من اللي تتركها في نص الطريق.")
    else:
        s = L("Your ability and your willingness to take risk agree.", "قدرتك ورغبتك في المخاطرة متفقة.")
    reasons = {"horizon": L("your time horizon", "مدة استثمارك"), "goal": L("your goal", "هدفك"),
               "tolerance": L("the risk tolerance you picked", "درجة تحمّل المخاطر اللي اخترتها"),
               "loss": L("the largest loss you accept in a bad year", "أقصى خسارة تتقبلها في سنة سيئة")}
    if prof["binding"]:
        names = L(" and ", " و").join(reasons[k] for k in prof["binding"])
        s += " " + L(f"It is then limited to level {rec} by {names}.", f"وبعدها انحدّ عند المستوى {rec} بسبب {names}.")
    return s


TIER_COLORS = [LEVEL_COLORS[2 * i + 1] for i in range(5)]


def tiers_html(prof, stated=None):
    """The five grades of risk tolerance, conservative to aggressive: the plan's grade lit, the grade the investor picked marked."""
    cur = R.tier(prof["level"])
    pick = next((i for i, t in enumerate(R.TIERS) if t[0] == (stated or prof.get("stated"))), None)
    out = []
    for i, (k, en, ar) in enumerate(R.TIERS):
        cls = ("on " if i == cur else "") + ("you" if i == pick else "")
        mark = f'<em>{L("your pick", "اختيارك")}</em>' if i == pick else ""
        out.append(f'<span class="{cls.strip()}" style="--c:{TIER_COLORS[i]};--i:{i}"><b>{_esc(L(en, ar))}</b>{mark}</span>')
    return f'<div class="rbtier">{"".join(out)}</div>'


def result_html(prof):
    lv = prof["level"]
    col = LEVEL_COLORS[lv - 1]
    bars = ""
    for k, en, ar, v in (("a", "Ability to take risk", "القدرة على المخاطرة", prof["ability"]), ("w", "Willingness", "الرغبة في المخاطرة", prof["will"])):
        c = "linear-gradient(90deg,#2DB6EB,#60A5FA)" if k == "a" else "linear-gradient(90deg,#A78BFA,#7B45F0)"
        bars += f'<div><div class="h"><span>{_esc(L(en, ar))}</span><b>{v:.1f}/10</b></div><div class="t"><i style="width:{v * 10:.0f}%;background:{c}"></i></div></div>'
    chips = []
    if prof["sharia"]:
        chips.append(f'<span class="rbchip gold">{T.icon("mosque")}{L("Sharia-compliant", "متوافقة مع الشريعة")}</span>')
    if prof["income"]:
        chips.append(f'<span class="rbchip">{T.icon("payments")}{L("Income tilt (dividend stocks)", "تركيز على الدخل (أسهم توزيعات)")}</span>')
    if prof["cash"]:
        cash = prof["cash"]
        chips.append(f'<span class="rbchip">{T.icon("account_balance_wallet")}{L(f"{cash}% kept for withdrawals", f"{cash}% محجوزة للسحب")}</span>')
    if lv != prof["rec"]:
        rc = prof["rec"]
        chips.append(f'<span class="rbchip warn">{T.icon("tune")}{L(f"Set by hand (recommended: {rc})", f"معدّل يدوياً (الموصى به: {rc})")}</span>')
    lg = col.lstrip("#")
    glow = f"rgba({int(lg[0:2], 16)},{int(lg[2:4], 16)},{int(lg[4:6], 16)},.24)"
    return (f'<div class="rbres" style="--lg:{glow};--lc:{col}">{gauge_svg(lv)}<div><div class="eb">{L("Your risk profile", "ملفك الاستثماري")}</div>'
            f'<h2>{_esc(_prof_name(lv))}<span class="lv">{L("Level", "المستوى")} {lv}/10</span></h2>{tiers_html(prof)}<p>{_esc(_why_text(prof))}</p>'
            f'<div class="rbsc">{bars}</div><div class="rbchips">{"".join(chips)}</div></div></div>')


def donut_svg(weights, center_big, center_small, inner=None):
    """weights: [(ticker, %)]; inner: [(ticker, %)] drawn as a thinner inner ring (the targets, under the current weights)."""
    def ring(ws, r, sw, cls):
        out, start = [], 0.0
        tot = sum(w for _, w in ws) or 1
        for i, (t, w) in enumerate(ws):
            w = w / tot * 100
            if w <= 0:
                continue
            g = 0.7 if len(ws) > 1 else 0
            out.append(f'<circle class="{cls}" style="animation-delay:{i * 70}ms" cx="120" cy="120" r="{r}" fill="none" stroke="{_fund(t)["c"]}" '
                       f'stroke-width="{sw}" pathLength="100" stroke-dasharray="{max(w - g, 0.2):.2f} {100 - max(w - g, 0.2):.2f}" '
                       f'stroke-dashoffset="{-start:.2f}"><title>{_esc(_tk(t))} {w:.1f}%</title></circle>')
            start += w
        return "".join(out)
    rings = ring(weights, 92, 24, "sg")
    if inner:
        rings += ring(inner, 70, 8, "sg")
    return (f'<div class="rbdon"><svg viewBox="0 0 240 240"><circle cx="120" cy="120" r="92" fill="none" stroke="rgba(157,151,165,.12)" stroke-width="24"/>'
            f'<g transform="rotate(-90 120 120)">{rings}</g>'
            f'<text x="120" y="122" text-anchor="middle" font-size="34" font-weight="800" fill="#FFFFFF">{_esc(center_big)}</text>'
            f'<text x="120" y="{142 if inner else 146}" text-anchor="middle" font-size="{11 if inner else 12.5}" font-weight="600" fill="#9D97A5">{_esc(center_small)}</text></svg></div>')


def groups_html(tg):
    g = {}
    for t, w in tg.items():
        k = _fund(t)["g"]
        g[k] = g.get(k, 0) + w
    order = [k for k in ("stocks", "bot", "bonds", "real", "gold", "cash") if g.get(k)]
    bar = "".join(f'<i style="width:{g[k]:.2f}%;background:{R.GROUPS[k][2]}"></i>' for k in order)
    leg = "".join(f'<span><i style="background:{R.GROUPS[k][2]}"></i>{_esc(L(R.GROUPS[k][0], R.GROUPS[k][1]))} <b>{g[k]:.0f}%</b></span>' for k in order)
    return f'<div class="rbgrp">{bar}</div><div class="rbgl">{leg}</div>'


def allocation_html(prof):
    tg = prof["targets"]
    rows = sorted(tg.items(), key=lambda x: -x[1])
    leg = "".join(f'<div class="r" style="--i:{i};--c:{_fund(t)["c"]}"><span class="tk">{_esc(_tk(t))}</span><span class="nm"><b>{_esc(_fund(t)["cls"])}</b>'
                  f'<span>{_esc(_fund(t)["name"])}</span></span><span class="w">{w:g}%<small>±{R.band(w):g}</small></span></div>'
                  for i, (t, w) in enumerate(rows))
    big = f"{prof['stocks']:.0f}%"
    return (f'<div class="rbal">{donut_svg(rows, big, L("in stocks", "أسهم"))}<div>{groups_html(tg)}'
            f'<div class="rbleg">{leg}</div></div></div>')


def expect_kpis(prof):
    return PP.kpis([
        ("trending_up", L("Expected return", "العائد المتوقع"), _p(prof["mu"], 1, False),
         L("a year · a long-run estimate, not a promise", "سنوياً · تقدير طويل المدى وليس وعد"), None, None),
        ("ssid_chart", L("Volatility", "التذبذب"), _p(prof["vol"], 1, False), L("typical yearly swing", "التأرجح المعتاد بالسنة"), None,
         (prof["vol"] / 18 * 100, LEVEL_COLORS[prof["level"] - 1])),
        ("thunderstorm", L("A bad year", "سنة سيئة"), _p(prof["bad"], 1, True), L("about 1 year in 20", "تقريباً سنة من كل 20"), "neg", None),
        ("crisis_alert", L("A 2008-style crisis", "أزمة مثل 2008"), _p(prof["crisis"], 0, True), L("peak to bottom, rough estimate", "من القمة للقاع، تقدير تقريبي"),
         "neg", None)], "c4")


def projection_fig(proj, years, goal=None):
    x = proj.index / 12
    fig = go.Figure()
    hov = _tp() + "%{y:,.0f}<extra></extra>"
    fig.add_trace(go.Scatter(x=x, y=proj["p90"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x, y=proj["p10"], fill="tonexty", fillcolor=C.rgba(T.CYAN, 0.16), line=dict(width=0),
                             name=L("Likely range", "النطاق المرجح"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x, y=proj["p90"], name=L("Good case", "حالة جيدة"), line=dict(color=C.rgba(T.CYAN, 0.6), width=1.2, dash="dot"),
                             hovertemplate=L("Good: ", "جيدة: ") + hov, showlegend=False))
    fig.add_trace(go.Scatter(x=x, y=proj["p50"], name=L("Middle", "المتوسطة"), line=dict(color=T.CYAN, width=3),
                             hovertemplate=L("Middle: ", "متوسطة: ") + hov))
    fig.add_trace(go.Scatter(x=x, y=proj["p10"], name=L("Weak case", "حالة ضعيفة"), line=dict(color=C.rgba(T.VIOLET, 0.8), width=1.2, dash="dot"),
                             hovertemplate=L("Weak: ", "ضعيفة: ") + hov, showlegend=False))
    fig.add_trace(go.Scatter(x=x, y=proj["invested"], name=L("Invested", "المستثمر"), line=dict(color=T.GOLD, width=1.8, dash="dash"),
                             hovertemplate=L("Invested: ", "المستثمر: ") + hov))
    if goal:
        fig.add_hline(y=goal, line=dict(color=T.GOLD, width=1.4, dash="dot"), annotation_text=L("Goal", "الهدف"),
                      annotation_font=dict(color=T.GOLD, size=11), annotation_position="top left")
    C.style(fig, 380, L(f"Where the plan could be in {years} years", f"وين ممكن توصل الخطة خلال {years} سنة"))
    fig.update_xaxes(title=None, ticksuffix=L("y", " س"), dtick=max(1, round(years / 6)))
    fig.update_yaxes(tickprefix=_tp(), tickformat="~s")
    fig.update_layout(hovermode="x unified")
    return fig


def lines_fig(rep, bm, title, rng="all", height=380):
    cur = rep["curve"].copy()
    if rep.get("live"):
        cur.loc[rep["live"]["d"]] = [rep["live"]["value"], cur["invested"].iloc[-1], 0.0, cur["twr"].iloc[-1]]
    b = bm["curve"]["value"] if bm and not bm.get("pending") else None
    if rng != "all" and len(cur):
        end = cur.index[-1]
        start = {"1m": end - pd.Timedelta(days=31), "3m": end - pd.Timedelta(days=92), "1y": end - pd.Timedelta(days=366),
                 "ytd": pd.Timestamp(end.year, 1, 1)}.get(rng, cur.index[0])
        cur = cur[cur.index >= start]
        b = b[b.index >= start] if b is not None else None
    fig = go.Figure()
    tr = go.Scatter(x=cur.index, y=cur["value"], name=L("Portfolio", "المحفظة"), line=dict(color=T.CYAN, width=2.8), fill="tozeroy",
                    hovertemplate="%{x|%b %d, %Y}: " + _tp() + "%{y:,.0f}<extra></extra>")
    try:
        tr.fillgradient = dict(type="vertical", colorscale=[[0, C.rgba(T.CYAN, 0.0)], [1, C.rgba(T.CYAN, 0.22)]])
    except (ValueError, AttributeError):
        tr.fillcolor = C.rgba(T.CYAN, 0.1)
    fig.add_trace(tr)
    if b is not None and len(b):
        fig.add_trace(go.Scatter(x=b.index, y=b, name=L("Benchmark", "المؤشر المرجعي"), line=dict(color=T.VIOLET, width=1.8, dash="dot"),
                                 hovertemplate="%{x|%b %d, %Y}: " + _tp() + "%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=cur.index, y=cur["invested"], name=L("Invested", "المستثمر"), line=dict(color=T.GOLD, width=1.6, dash="dash", shape="hv"),
                             hovertemplate="%{x|%b %d, %Y}: " + _tp() + "%{y:,.0f}<extra></extra>"))
    ys = [float(v) for v in cur["value"]] + [float(v) for v in cur["invested"]] + ([float(v) for v in b] if b is not None else [])
    lo, hi = (min(ys), max(ys)) if ys else (0, 1)
    pad = max((hi - lo) * 0.12, hi * 0.004, 1)
    C.style(fig, height, title)
    fig.update_yaxes(range=[lo - pad, hi + pad], tickprefix=_tp(), tickformat=",.0f")
    return fig


def _mtab(m, bm):
    def row(lab, a, b, f):
        return f'<tr><td>{_esc(lab)}</td><td class="n">{_ltr(f(a))}</td><td class="n">{_ltr(f(b))}</td></tr>'
    f1 = lambda v: "—" if v is None else _p(v, 1, True)
    f2 = lambda v: "—" if v is None else _p(v, 1, False)
    rows = row(L("Total return (time-weighted)", "العائد الكلي (موزون زمنياً)"), m.get("ret"), bm.get("ret"), f1)
    if m.get("cagr") is not None:
        rows += row(L("A year, on average", "بالمتوسط سنوياً"), m.get("cagr"), bm.get("cagr"), f1)
    rows += row(L("Volatility (a year)", "التذبذب (سنوي)"), m.get("vol"), bm.get("vol"), f2)
    rows += row(L("Largest fall", "أكبر هبوط"), m.get("mdd"), bm.get("mdd"), f1)
    return (f'<table class="rbtbl"><tr><th></th><th class="n">{L("Your plan", "خطتك")}</th><th class="n">{L("Benchmark", "المؤشر المرجعي")}</th></tr>{rows}</table>')


# ---------------------------------------------------------------- the IPS
def ips_parts(prof, ans, amount, monthly, created=None):
    """The IPS as data: [(icon, title, [(label, value)] or a list of lines)] and the allocation rows."""
    years = _answer("horizon", ans)
    lvl = prof["level"]
    word = lambda s: L("high", "عالية") if s >= 7 else L("moderate", "متوسطة") if s >= 4 else L("low", "منخفضة")
    maxloss = _answer("maxloss", ans)
    eq = prof["stocks"]
    if _sa():
        bench = (" ".join([_i("%.0f%%" % eq), L("Saudi stocks", "أسهم سعودية"), "+", _i("%.0f%%" % (100 - eq)),
                           L("Saudi government sukuk", "صكوك حكومية سعودية")]) if eq < 100 else L("100% Saudi stocks", "100% أسهم سعودية"))
    else:
        bench = (" ".join([_i("%.0f%%" % eq), L("global stocks", "أسهم عالمية"), _i("(VT)"), "+", _i("%.0f%%" % (100 - eq)),
                           L("US bonds", "سندات أمريكية"), _i("(BND)")]) if eq < 100 else "100% VT")
    secs = [
        ("flag", L("Objectives", "الأهداف"), [
            (L("Goal", "الهدف"), _answer("goal", ans)),
            (L("Return objective", "العائد المستهدف"), L(f"about {_i(_p(prof['mu']))} a year over the long run", f"تقريباً {_i(_p(prof['mu']))} سنوياً على المدى الطويل")),
            (L("Time horizon", "مدة الاستثمار"), years)]),
        ("shield_person", L("Risk tolerance", "تحمّل المخاطر"), [
            (L("Stated risk tolerance", "تحمّل المخاطر المُعلن"), _answer("risk", ans) + ("" if not is_ar() or not R.opt("risk", ans.get("risk"))
                                                                                     else f' ({R.opt("risk", ans.get("risk"))[2]})')),
            (L("Ability to take risk", "القدرة على المخاطرة"), _i("%.1f/10" % prof["ability"]) + " · " + word(prof["ability"])),
            (L("Willingness", "الرغبة في المخاطرة"), _i("%.1f/10" % prof["will"]) + " · " + word(prof["will"])),
            (L("Risk level", "مستوى المخاطرة"), _i("%d/10" % lvl) + " · " + _prof_name(lvl) + ("" if lvl == prof["rec"] else L(f" (recommended {prof['rec']})", f" (الموصى به {prof['rec']})"))),
            (L("Largest loss accepted in a bad year", "أقصى خسارة مقبولة في سنة سيئة"), maxloss),
            (L("A bad year for this plan (1 in 20)", "سنة سيئة لهالخطة (1 من 20)"), _i(_p(prof["bad"], 1, True))),
            (L("A 2008-style crisis", "أزمة مثل 2008"), L(f"about {_i(_p(prof['crisis'], 0, True))}", f"تقريباً {_i(_p(prof['crisis'], 0, True))}"))]),
        ("lock", L("Constraints", "القيود"), [
            (L("Liquidity", "السيولة"), _answer("withdraw", ans) + (L(f" · {_i(str(prof['cash']) + '%')} kept in cash", f" · {_i(str(prof['cash']) + '%')} محفوظة نقداً") if prof["cash"] else "")),
            (L("Sharia-compliant", "التوافق مع الشريعة"), L("Yes", "نعم") if prof["sharia"] else L("No preference", "ما يفرق")),
            (L("Emergency fund", "مبلغ الطوارئ"), _answer("emergency", ans)),
            (L("Taxes and fees", "الضرائب والرسوم"), L("Not modelled (virtual); fund costs are inside the prices", "غير محتسبة (افتراضية)، وتكاليف الصناديق داخلة في الأسعار"))]),
        ("payments", L("Funding", "التمويل"), [
            (L("Starting amount", "المبلغ المبدئي"), _i(_m(amount))),
            (L("Monthly deposit", "الإيداع الشهري"), _i(_m(monthly)) + L(" on the first trading day", " أول يوم تداول بالشهر")),
            (L("Benchmark", "المؤشر المرجعي"), bench)]),
    ]
    policy = [L("Quarterly review on the first trading day of January, April, July and October: back to target when a fund is more than 1 point away.",
                "مراجعة ربع سنوية أول يوم تداول من يناير وأبريل ويوليو وأكتوبر: يرجع للنسب المستهدفة إذا ابتعد أي صندوق أكثر من نقطة."),
              L("Between reviews: rebalanced at once when a fund leaves its range (target ± band).",
                "بين المراجعات: إعادة توازن فورية إذا خرج أي صندوق عن نطاقه (النسبة ± الهامش)."),
              L("Deposits go to the funds under their target first; withdrawals come from those over it.",
                "الإيداعات تروح للصناديق الأقل من نسبتها أولاً، والسحوبات من الأعلى من نسبتها."),
              L("Dividends are reinvested. The policy is reviewed every year, or after a change in your life (retake the questionnaire).",
                "التوزيعات يُعاد استثمارها. السياسة تُراجع كل سنة أو بعد أي تغيير في حياتك (أعد الاستبيان).")]
    if R.BOT in prof["targets"]:
        n_l, n_s = RB.slots(prof["level"], prof["sharia"])
        policy.append(L(f"Opportunity Bot ({prof['targets'][R.BOT]:g}%): a weekly scan of emerging companies, up to {n_l} long"
                        + (f" and {n_s} short" if n_s else "") + " positions, each with a stop 2.5 ATR away that trails by 3 ATR; one not up 10% after 60 trading days leaves.",
                        f"بوت الفرص ({prof['targets'][R.BOT]:g}%): مسح أسبوعي للشركات الناشئة، لين {n_l} مراكز شراء"
                        + (f" و{n_s} بيع على المكشوف" if n_s else "") + "، لكل مركز وقف على بعد 2.5 ATR يتحرك بـ 3 ATR، واللي ما ربح 10% بعد 60 يوم تداول يطلع."))
        secs[2][2].append((L("Short selling", "البيع على المكشوف"),
                           L("Not used (Sharia)", "غير مستخدم (الشريعة)") if prof["sharia"] else L("Inside the Opportunity Bot only", "داخل بوت الفرص فقط")))
    alloc = [(t, _fund(t)["cls"], w, R.band(w)) for t, w in sorted(prof["targets"].items(), key=lambda x: -x[1])]
    return secs, policy, alloc


def ips_html(prof, ans, amount, monthly, created=None):
    secs, policy, alloc = ips_parts(prof, ans, amount, monthly, created)
    day = _date(pd.Timestamp(PF.parse(created).astimezone(PF._tz()).date()) if created else pd.Timestamp(PF.utcnow().astimezone(PF._tz()).date()))
    blocks = ""
    for i, (ic, title, items) in enumerate(secs):
        its = "".join(f'<div class="it"><span>{_esc(a)}</span><b>{_esc(b)}</b></div>' for a, b in items)
        blocks += f'<div class="sx"><h4>{T.icon(ic)}<i>{i + 1:02d}</i> {_esc(title)}</h4>{its}</div>'
    rows = "".join(f'<tr><td><b>{_esc(_tk(t))}</b></td><td>{_esc(c)}</td><td class="n">{w:g}%</td><td class="n">{max(w - b, 0):g}–{w + b:g}%</td></tr>'
                   for t, c, w, b in alloc)
    blocks += (f'<div class="sx"><h4>{T.icon("donut_large")}<i>05</i> {L("Strategic allocation", "توزيع الأصول الاستراتيجي")}</h4>'
               f'<table><tr><th>{L("Fund", "الصندوق")}</th><th>{L("Asset class", "فئة الأصل")}</th><th class="n">{L("Target", "المستهدف")}</th>'
               f'<th class="n">{L("Range", "النطاق")}</th></tr>{rows}</table></div>')
    blocks += (f'<div class="sx"><h4>{T.icon("balance")}<i>06</i> {L("Rebalancing & review", "إعادة التوازن والمراجعة")}</h4>'
               f'<ul class="pol">{"".join(f"<li>{_esc(p)}</li>" for p in policy)}</ul></div>')
    return (f'<div class="rbips"><div class="hd"><div class="t"><span class="seal">{T.icon("verified")}</span><div><b>{L("Investment Policy Statement", "بيان سياسة الاستثمار")}</b>'
            f'<span>{L("Prepared by TURA Robo Advisor", "أعدّه المستشار الآلي من TURA")} · {day}</span></div></div>'
            f'<span class="rbchip">{T.icon("science")}{L("Virtual · educational", "افتراضي · تعليمي")}</span></div>'
            f'<div class="grid">{blocks}</div><div class="sg"><div><b>TURA Robo</b>{L("Robo advisor", "المستشار الآلي")}</div>'
            f'<div>{L("Not investment advice", "ليست توصية استثمارية")}</div></div></div>')


def ips_file(prof, ans, amount, monthly, created=None):
    """The IPS as a standalone HTML page to download (opens in any browser, prints to PDF)."""
    secs, policy, alloc = ips_parts(prof, ans, amount, monthly, created)
    ar = is_ar()
    day = _date(pd.Timestamp(PF.parse(created).astimezone(PF._tz()).date()) if created else pd.Timestamp(PF.utcnow().astimezone(PF._tz()).date()))
    e = _html.escape
    body = ""
    for i, (ic, title, items) in enumerate(secs):
        body += f"<h2>{i + 1}. {e(title)}</h2><table>" + "".join(f"<tr><th>{e(a)}</th><td>{e(b)}</td></tr>" for a, b in items) + "</table>"
    body += (f"<h2>5. {e(L('Strategic allocation', 'توزيع الأصول الاستراتيجي'))}</h2><table class='al'><tr><th>{e(L('Fund', 'الصندوق'))}</th>"
             f"<th>{e(L('Asset class', 'فئة الأصل'))}</th><th>{e(L('Target', 'المستهدف'))}</th><th>{e(L('Range', 'النطاق'))}</th></tr>"
             + "".join(f"<tr><td><b>{e(_tk(t))}</b> · {e(_fund(t)['name'])}</td><td>{e(c)}</td><td class='n'>{w:g}%</td><td class='n'>{max(w - b, 0):g}–{w + b:g}%</td></tr>"
                       for t, c, w, b in alloc) + "</table>")
    body += f"<h2>6. {e(L('Rebalancing & review', 'إعادة التوازن والمراجعة'))}</h2><ul>" + "".join(f"<li>{e(p)}</li>" for p in policy) + "</ul>"
    disc = L("Virtual portfolio on real prices, for learning. Not investment advice. Expected returns are long-run estimates, not promises.",
             "محفظة افتراضية على أسعار حقيقية بهدف التعلم. ليست توصية استثمارية. العوائد المتوقعة تقديرات طويلة المدى وليست وعود.")
    title = L("Investment Policy Statement", "بيان سياسة الاستثمار")
    return (f"<!doctype html><html lang='{'ar' if ar else 'en'}' dir='{'rtl' if ar else 'ltr'}'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{e(title)} · TURA</title><style>"
            "body{font-family:'DM Sans','Readex Pro',system-ui,sans-serif;max-width:820px;margin:32px auto;padding:0 20px;color:#1E1830;background:#fff;line-height:1.55}"
            "header{border-bottom:3px solid #7B45F0;padding-bottom:12px;margin-bottom:8px}h1{margin:0;font-size:26px}header p{margin:4px 0 0;color:#6B6478}"
            "h2{font-size:16px;color:#5B32C8;margin:22px 0 8px;text-transform:uppercase;letter-spacing:.04em}"
            "table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:7px 8px;border-bottom:1px solid #E7E3EF;text-align:start;vertical-align:top}"
            "table:not(.al) th{width:42%;color:#6B6478;font-weight:600}.al th{background:#F4F1FA}.n{text-align:end;direction:ltr;unicode-bidi:isolate}"
            "ul{padding-inline-start:20px}li{margin:4px 0}footer{margin-top:28px;padding-top:10px;border-top:1px solid #E7E3EF;color:#8A8396;font-size:12px}"
            "@media print{body{margin:0}}</style></head><body>"
            f"<header><h1>{e(title)}</h1><p>TURA Robo Advisor · {e(day)} · {e(L('Risk level', 'مستوى المخاطرة'))} {prof['level']}/10 · {e(_prof_name(prof['level']))}</p></header>"
            f"{body}<footer>{e(disc)}</footer></body></html>")


# =====================================================================
# the Opportunity Bot (levels 9 and 10), storms, frontier, monthly returns
# =====================================================================
BOT_C = "#EC4899"


def load_bot():
    """The bot's hunting list ({ticker: features}); {} when the prices can't be fetched right now."""
    try:
        with st.spinner(L("The bot is scanning emerging companies…", "البوت يمسح الشركات الناشئة…")):
            return RB.load()
    except Exception:
        return {}


def _why_chips(why, cls="rbwc"):
    out = []
    for k, v in why or []:
        en, ar = RB.WHY[k]
        txt = L(en, ar)
        if "{v" in txt:
            txt = txt.replace("×{v:.1f}", _i("×%.1f" % v))
        if "{r" in txt:
            txt = txt.replace("{r:+.0f}%", _i("%+.0f%%" % v))
        out.append(f'<span class="{cls}">{_esc(txt)}</span>')
    return "".join(out)


def _theme(t):
    th = RB.THEMES[RB.UNIVERSE[t][1]] if t in RB.UNIVERSE else ("", "", "category")
    return T.icon(th[2]) + _esc(L(th[0], th[1]))


def _side(side):
    return (f'<span class="rbsd long">{T.icon("north_east")}{L("Long", "شراء")}</span>' if side == "long" else
            f'<span class="rbsd short">{T.icon("south_east")}{L("Short", "مكشوف")}</span>')


def bot_card(prof, n_list=None, stats_line=None):
    lv = prof["level"]
    sat = RB.SAT.get(lv, 0)
    n_l, n_s = RB.slots(lv, prof["sharia"])
    chips = [f'<span class="rbchip">{T.icon("event_repeat")}{L("Scans every week", "يمسح كل أسبوع")}</span>',
             f'<span class="rbchip">{T.icon("north_east")}{L(f"Up to {n_l} long", f"لين {n_l} شراء")}</span>']
    if n_s:
        chips.append(f'<span class="rbchip">{T.icon("south_east")}{L(f"Up to {n_s} short", f"لين {n_s} مكشوف")}</span>')
    chips += [f'<span class="rbchip">{T.icon("shield")}{L("Trailing stops", "وقف متحرك")}</span>',
              f'<span class="rbchip">{T.icon("timer")}{L("A laggard leaves after 60 days", "المتأخر يطلع بعد 60 يوم")}</span>']
    if prof["sharia"]:
        chips.append(f'<span class="rbchip gold">{T.icon("mosque")}{L("Long only, screened list", "شراء فقط وقائمة مفلترة")}</span>')
    n = len(RB.universe(prof["sharia"])) if n_list is None else n_list
    side_txt = (L("buys a breakout as it starts", "يشتري الاختراق وقت بدايته") if prof["sharia"] else
                L("buys a breakout as it starts and sells short a breakdown", "يشتري الاختراق وقت بدايته ويبيع على المكشوف عند الكسر"))
    sl = f'<div class="sl">{stats_line}</div>' if stats_line else ""
    return (f'<div class="rbbot"><span class="sweep"></span><div class="ic">{T.icon("radar")}</div><div class="tx">'
            f'<div class="eb">{L("TURA Opportunity Bot", "بوت الفرص من TURA")} · {_ltr(f"{sat:.0f}%")}</div>'
            f'<h3>{L("Hunting emerging companies and explosive price moves", "يصطاد الشركات الناشئة والانفجارات السعرية")}</h3>'
            f'<p>{L(f"{sat:.0f}% of your portfolio watches {n} young, fast-growing companies (AI, chips, quantum, space, nuclear, fintech and more) and ", f"{sat:.0f}% من محفظتك تراقب {n} شركة ناشئة وسريعة النمو (ذكاء اصطناعي، رقائق، حوسبة كمية، فضاء، طاقة نووية، تقنية مالية وغيرها) و")}'
            f'{side_txt}{L(", with a stop on every position.", "، مع وقف خسارة لكل مركز.")}</p>'
            f'<div class="rbchips">{"".join(chips)}</div>{sl}</div></div>')


def score_ring(score, side):
    """A signal's score (0-100) in a ring that fills with it: green for a buy (long), red for a short."""
    col = "#4ADE80" if side == "long" else "#F87171"
    return (f'<svg viewBox="0 0 40 40" role="img" aria-label="{L("Score", "التقييم")} {score:.0f}/100">'
            f'<circle cx="20" cy="20" r="16" fill="{col}" fill-opacity=".08" stroke="rgba(157,151,165,.18)" stroke-width="4"/>'
            f'<circle cx="20" cy="20" r="16" fill="none" stroke="{col}" stroke-width="4" pathLength="100" '
            f'stroke-dasharray="{max(0, min(100, score)):.0f} 100" transform="rotate(-90 20 20)" stroke-linecap="round"/>'
            f'<text x="20" y="24.5" text-anchor="middle" font-size="12" font-weight="800" fill="#FFFFFF">{score:.0f}</text></svg>')


def score_key():
    """What the number in the ring is, in one line."""
    return (f'<div class="rbsck" data-nogq>{score_ring(RB.THRESHOLD + 15, "long")}<span>'
            + L(f"<b>Score</b> (0–100): how strong the signal is: a breakout above the 55-day high (or a breakdown below the low), "
                f"3-month momentum, volume against its average and the trend. Green ring: buy · red: short · {RB.THRESHOLD} or more is a signal to enter.",
                f"<b>التقييم</b> (من 100): قوة الإشارة: اختراق قمة 55 يوم (أو كسر قاعها) وزخم 3 أشهر والحجم مقارنة بمتوسطه والاتجاه. "
                f"الدائرة الخضراء: شراء · الحمراء: بيع على المكشوف · {RB.THRESHOLD} أو أكثر تعني إشارة دخول.")
            + "</span></div>")


def radar_html(longs, shorts, key=True):
    """key: the line that says what the score is (left out when the trading plan above already has it)."""
    def card(x, i):
        ring = score_ring(x["score"], x["side"])
        st_ = (f'<span class="sg on">{T.icon("bolt")}{L("Signal", "إشارة")}</span>' if x["signal"] else
               f'<span class="sg">{T.icon("visibility")}{L("Watching", "تحت المراقبة")}</span>')
        r63 = x.get("r63")
        mom = "" if r63 is None or r63 != r63 else f' · {L("3m", "3 أشهر")} {_ltr("%+.0f%%" % (r63 * 100))}'
        return (f'<div class="rbrc {x["side"]}" style="--i:{i}"><div class="top"><span class="tk">{x["t"]}</span>{_side(x["side"])}'
                f'<span class="ring">{ring}</span></div><div class="nm">{_esc(x["name"])}</div><div class="th">{_theme(x["t"])}</div>'
                f'<div class="rpx">{_ltr(_m(x["c"], 2))}{mom}</div><div class="ch">{_why_chips(x["why"])}</div>{st_}</div>')
    if not longs and not shorts:
        return PP.empty("radar", L("No candidates right now", "ما فيه مرشحين الحين"), L("The prices of the list aren't available.", "أسعار القائمة مو متاحة."))
    out = score_key() if key else ""
    if longs:
        out += (f'<div class="rbgrp2 long">{T.icon("north_east")}{L("Breakouts: buy candidates", "اختراقات: مرشحة للشراء")}</div>'
                '<div class="rbrad">' + "".join(card(x, i) for i, x in enumerate(longs)) + "</div>")
    if shorts:
        out += (f'<div class="rbgrp2 short">{T.icon("south_east")}{L("Breakdowns: short candidates", "كسور: مرشحة للبيع على المكشوف")}</div>'
                '<div class="rbrad">' + "".join(card(x, i) for i, x in enumerate(shorts)) + "</div>")
    return out


def positions_html(rows):
    if not rows:
        return PP.empty("radar", L("No open positions", "ما فيه مراكز مفتوحة"),
                        L(f"The bot waits for a signal scoring {RB.THRESHOLD} or more at its weekly scan.", f"البوت ينتظر إشارة تقييمها {RB.THRESHOLD} أو أكثر في مسحه الأسبوعي."))
    out = []
    for i, r in enumerate(rows):
        k = "up" if r["ret"] > 0 else "dn" if r["ret"] < 0 else ""
        room = abs(r["px"] - r["stop"]) / r["px"] * 100 if r["px"] else 0
        out.append(f'<div class="rbpc {r["side"]}" style="--i:{i}"><div class="top"><span class="tk">{r["t"]}</span>{_side(r["side"])}'
                   f'<b class="ret {k}">{_ltr("%+.1f%%" % r["ret"])}</b></div><div class="th">{_theme(r["t"])}</div>'
                   f'<div class="pp">{_ltr(_m(r["entry"], 2))} {T.icon("arrow_back" if is_ar() else "arrow_forward")} {_ltr(_m(r["px"], 2))}</div>'
                   f'<div class="meta"><span>{L("Stop", "الوقف")} {_ltr(_m(r["stop"], 2))} · {_ltr("%.0f%%" % room)} {L("away", "بعيد")}</span>'
                   f'<span>{L("Day", "اليوم")} {_ltr("%d/%d" % (r["held"], RB.MAX_DAYS))}</span></div>'
                   f'<div class="bar"><i style="width:{min(100, r["held"] / RB.MAX_DAYS * 100):.0f}%"></i></div>'
                   f'<div class="ch">{_why_chips(r["why"])}</div></div>')
    return '<div class="rbpcs">' + "".join(out) + "</div>"


def plan_html(trades, summ, when=None, first=False):
    """The bot's trading plan: the trades its next scan would open (entry, first stop, size, shares, money at risk)."""
    lab = L("First trades after the close of", "أول صفقاته بعد إغلاق") if first else L("Next scan", "المسح الجاي")
    chips = [f'<span class="rbchip bot">{T.icon("rocket_launch" if first else "event_repeat")}{lab} <b>{_esc(when)}</b></span>' if when else
             f'<span class="rbchip bot">{T.icon("rocket_launch")}{L("If you start now", "لو بدأت الحين")}</span>',
             f'<span class="rbchip">{T.icon("north_east")}{L("Free long slots", "خانات شراء فاضية")} <b>{summ["free_long"]}/{summ["n_long"]}</b></span>']
    if summ["n_short"]:
        chips.append(f'<span class="rbchip">{T.icon("south_east")}{L("Free short slots", "خانات مكشوف فاضية")} <b>{summ["free_short"]}/{summ["n_short"]}</b></span>')
    chips.append(f'<span class="rbchip">{T.icon("payments")}{L("Each position", "كل مركز")} <b>{_ltr(_m(summ["size"]))}</b></span>')
    head = (f'<tr><th>{L("Company", "الشركة")}</th><th>{L("Trade", "الصفقة")}</th><th class="n">{L("Score", "التقييم")}</th>'
            f'<th class="n">{L("Entry ≈", "الدخول ≈")}</th><th class="n">{L("First stop", "الوقف الأول")}</th><th>{L("Distance", "المسافة")}</th>'
            f'<th class="n">{L("Size", "الحجم")}</th><th class="n">{L("Shares", "الأسهم")}</th><th class="n">{L("At risk", "المخاطرة")}</th></tr>')
    body, cards = "", ""
    for i, x in enumerate(trades):
        nxt = f'<span class="rbnx">{L("next in line", "الاحتياط")}</span>' if x["next"] else ""
        bar = min(100, x["dist"] / 25 * 100)
        dist = _ltr(("-" if x["side"] == "long" else "+") + "%.1f%%" % x["dist"])
        ds = f'<span class="rbds"><i class="{x["side"]}" style="width:{bar:.0f}%"></i></span>'
        body += (f'<tr class="{"nx" if x["next"] else ""}"><td><div class="cco"><span class="tk" style="--c:{BOT_C}">{x["t"]}</span>'
                 f'<span class="cl">{_esc(x["name"])}</span>{nxt}</div><div class="wy">{_why_chips(x["why"][:3])}</div></td>'
                 f'<td>{_side(x["side"])}</td><td class="n"><span class="rbscr">{score_ring(x["score"], x["side"])}</span></td><td class="n">{_ltr(_m(x["entry"], 2))}</td>'
                 f'<td class="n">{_ltr(_m(x["stop"], 2))}</td><td>{ds} {dist}</td>'
                 f'<td class="n">{_ltr(_m(x["size"]))}</td><td class="n">{_ltr("%.2f" % x["units"])}</td>'
                 f'<td class="n dn">{_ltr(_m(x["risk"]))} <span class="cl">{_ltr("%.1f%%" % x["risk_pct"])}</span></td></tr>')
        cards += (f'<div class="rbpq {x["side"]}{" nx" if x["next"] else ""}" style="--i:{i}"><div class="top"><span class="tk">{x["t"]}</span>{_side(x["side"])}'
                  f'{nxt}<span class="scr">{score_ring(x["score"], x["side"])}</span></div><div class="nm">{_esc(x["name"])}</div>'
                  f'<div class="rr"><span>{L("Entry ≈", "الدخول ≈")} <b>{_ltr(_m(x["entry"], 2))}</b></span>'
                  f'<span>{L("Stop", "الوقف")} <b>{_ltr(_m(x["stop"], 2))}</b> {dist}</span></div>'
                  f'<div class="rr"><span>{L("Size", "الحجم")} <b>{_ltr(_m(x["size"]))}</b> · {_ltr("%.2f" % x["units"])} {L("sh.", "سهم")}</span>'
                  f'<span>{L("At risk", "المخاطرة")} <b class="dn">{_ltr(_m(x["risk"]))}</b></span></div>'
                  f'<div class="wy">{_why_chips(x["why"][:3])}</div></div>')
    if not trades:
        msg = (L("Every slot is taken: new trades come when a position closes.", "كل الخانات مشغولة: الصفقات الجديدة تجي لما يتسكّر مركز.")
               if summ["free_long"] + summ["free_short"] == 0 else
               L(f"No signal scores {RB.THRESHOLD} or more right now: the free slots wait in cash until one does.",
                 f"ما فيه إشارة تقييمها {RB.THRESHOLD} أو أكثر الحين: الخانات الفاضية تنتظر كنقد لين تطلع وحدة."))
        table = PP.empty("event_busy", L("Nothing to open at the next scan", "ما فيه شي ينفتح في المسح الجاي"), msg)
    else:
        table = f'<div class="rbtw rbplan-t"><table class="rbtbl rbplan">{head}{body}</table></div><div class="rbplan-c">{cards}</div>'
    rules = (f'<div class="rbrules">{T.icon("rule")}<span>{L("Each trade: read on the close of the scan day, bought (or sold short) right after it in the after-hours session · the stop moves with the best close, 3 ATR behind, and is checked at the end of the pre-market and the after-hours session too · a position not up 10% after 60 trading days leaves.", "كل صفقة: تنقرا على إغلاق يوم المسح، وتنشرى (أو تنباع على المكشوف) بعده مباشرة في تداول ما بعد الإغلاق · الوقف يتحرك مع أفضل إغلاق على بعد 3 ATR، ويُفحص كمان مع نهاية ما قبل الافتتاح وما بعد الإغلاق · المركز اللي ما ربح 10% بعد 60 يوم تداول يطلع.")}</span></div>')
    key = score_key() if trades else ""
    return f'<div class="rbchips" style="margin:0 0 8px">{"".join(chips)}</div>{key}{table}{rules}'


XH = {"ah": ("after-hours", "بعد الإغلاق"), "pm": ("pre-market", "قبل الافتتاح")}


def _xh(tag):
    """A small tag for a fill in the pre-market or the after-hours session."""
    return f' <span class="rbxh {tag}">{_esc(L(*XH[tag]))}</span>' if tag in XH else ""


def trades_html(trades, limit=20):
    if not trades:
        return ""
    head = (f'<tr><th>{L("Company", "الشركة")}</th><th>{L("Side", "الاتجاه")}</th><th class="n">{L("In", "الدخول")}</th>'
            f'<th class="n">{L("Out", "الخروج")}</th><th class="n">{L("Days", "الأيام")}</th><th class="n">{L("Result", "النتيجة")}</th><th>{L("Why it left", "سبب الخروج")}</th></tr>')
    body = ""
    for x in sorted(trades, key=lambda x: x["d_out"], reverse=True)[:limit]:
        k = "up" if x["ret"] > 0 else "dn"
        body += (f'<tr><td><span class="tk" style="--c:{BOT_C}">{x["t"]}</span><span class="cl">{_esc(RB.UNIVERSE.get(x["t"], (x["t"],))[0])}</span></td>'
                 f'<td>{L("Long", "شراء") if x["side"] == "long" else L("Short", "مكشوف")}</td>'
                 f'<td class="n">{_ltr(_m(x["px_in"], 2))}<span class="cl"> {_date(x["d_in"])}</span>{_xh(x.get("x_in"))}</td>'
                 f'<td class="n">{_ltr(_m(x["px_out"], 2))}<span class="cl"> {_date(x["d_out"])}</span>{_xh(x.get("x_out"))}</td><td class="n">{x["days"]}</td>'
                 f'<td class="n {k}"><b>{_ltr("%+.1f%%" % x["ret"])}</b></td><td>{_esc(L(*RB.EXIT[x["why"]]))}</td></tr>')
    return f'<div class="rbtw"><table class="rbtbl">{head}{body}</table></div>'


def bot_stats_line(book):
    s = RB.stats(book)
    if not s.get("n"):
        return None
    aw = "—" if s.get("avg_win") is None else "%+.1f%%" % s["avg_win"]
    al = "—" if s.get("avg_loss") is None else "%+.1f%%" % s["avg_loss"]
    return (f'{T.icon("insights")}{L("Its rules over these years:", "قواعده على هالسنوات:")} {_ltr(str(s["n"]))} {L("trades", "صفقة")} · '
            f'{L("won", "ربحت")} {_ltr("%.0f%%" % s["win"])} · {L("average win", "متوسط الربح")} {_ltr(aw)} · {L("average loss", "متوسط الخسارة")} {_ltr(al)} · '
            f'{L("best", "الأفضل")} {_ltr("%s %+.0f%%" % (s["best"]["t"], s["best"]["ret"]))}')


def lock_html(rec):
    return (f'<div class="rblock">{T.icon("lock")}<div><b>{L("Opportunity Bot · levels 9 and 10", "بوت الفرص · المستوى 9 و10")}</b>'
            f'<span>{L("At the two highest risk levels a slice of the portfolio (10% or 20%) hunts emerging companies and explosive price moves, long and short.", "في أعلى مستويين للمخاطرة، جزء من المحفظة (10% أو 20%) يصطاد الشركات الناشئة والانفجارات السعرية، شراء وبيع على المكشوف.")}'
            f'{"" if rec >= 8 else L(" Your answers point to a steadier plan.", " إجاباتك تشير لخطة أهدى.")}</span></div></div>')


def stress_html(prof):
    sl, sh = prof["sleeves"], prof["sharia"]
    stocks = {"sa": 75, "us": 25} if _sa() else {"us": 60, "intl": 28, "em": 12}
    rows = []
    for k, (en, ar, wen, war, _, _) in R.scenarios().items():
        a, b = R.scenario(sl, k, sh), R.scenario(stocks, k, False)
        rows.append((L(en, ar), L(wen, war), a, b))
    top = max([abs(x) for r in rows for x in r[2:]] + [10])
    out = []
    for i, (name, when, a, b) in enumerate(rows):
        out.append(f'<div class="r" style="--i:{i}"><div class="h"><b>{_esc(name)}</b><span>{_esc(when)}</span></div>'
                   f'<div class="b"><span class="lb">{L("Your plan", "خطتك")}</span><span class="tr"><i class="me" style="width:{abs(a) / top * 100:.0f}%"></i></span>'
                   f'<em class="{"dn" if a < 0 else "up"}">{_ltr("%+.0f%%" % a)}</em></div>'
                   f'<div class="b"><span class="lb">{L("All stocks", "أسهم بالكامل")}</span><span class="tr"><i style="width:{abs(b) / top * 100:.0f}%"></i></span>'
                   f'<em class="{"dn" if b < 0 else "up"}">{_ltr("%+.0f%%" % b)}</em></div></div>')
    hd = L("Four real storms", "أربع عواصف حقيقية") if len(rows) == 4 else L("Three real storms", "ثلاث عواصف حقيقية")
    return (f'<div class="rbscn"><div class="hd">{T.icon("thunderstorm")}{hd}</div>{"".join(out)}'
            f'<div class="ft">{L("Peak to bottom, rough estimates from what each kind of asset did then.", "من القمة للقاع، تقديرات تقريبية من أداء كل نوع أصل وقتها.")}</div></div>')


def frontier_fig(prof):
    pts = R.frontier(prof["income"], prof["cash"], prof["sharia"])
    lv, rec = prof["level"], prof["rec"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[p[2] for p in pts], y=[p[1] for p in pts], mode="lines", line=dict(color="rgba(157,151,165,.45)", width=2),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[p[2] for p in pts], y=[p[1] for p in pts], mode="markers+text", text=[str(p[0]) for p in pts],
                             textposition="top center", textfont=dict(size=10, color="#B9B3C4"), showlegend=False,
                             marker=dict(size=[22 if p[0] == lv else 11 for p in pts], color=LEVEL_COLORS,
                                         line=dict(color=["#FFFFFF" if p[0] == lv else "rgba(0,0,0,0)" for p in pts], width=3)),
                             customdata=[[_prof_name(p[0]), p[3]] for p in pts],
                             hovertemplate=L("Level %{text} · %{customdata[0]}<br>Return %{y:.1f}% · swing %{x:.1f}%<br>Stocks %{customdata[1]:.0f}%",
                                             "المستوى %{text} · %{customdata[0]}<br>العائد %{y:.1f}% · التذبذب %{x:.1f}%<br>الأسهم %{customdata[1]:.0f}%")
                             + "<extra></extra>"))
    me = pts[lv - 1]
    fig.add_annotation(x=me[2], y=me[1], text=L("Your plan", "خطتك"), showarrow=True, arrowhead=0, ax=-40, ay=-34,
                       font=dict(color="#FFFFFF", size=12), bgcolor=LEVEL_COLORS[lv - 1], borderpad=4)
    if rec != lv:
        r = pts[rec - 1]
        fig.add_annotation(x=r[2], y=r[1], text=L("Recommended", "الموصى به"), showarrow=True, arrowhead=0, ax=40, ay=30,
                           font=dict(color="#0E0918", size=11), bgcolor="#E9E5F0", borderpad=3)
    C.style(fig, 330, L("Risk and return of the ten levels", "العائد والمخاطرة للمستويات العشرة"), legend=False)
    fig.update_xaxes(title=L("Volatility (a year)", "التذبذب (سنوي)"), ticksuffix="%")
    fig.update_yaxes(title=None, ticksuffix="%")
    fig.update_layout(hovermode="closest")
    return fig


def heat_html(mret):
    if not mret:
        return ""
    years = sorted({y for y, _ in mret}, reverse=True)
    names = MONTHS_AR if is_ar() else ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    head = "<tr><th></th>" + "".join(f"<th>{_esc(n)}</th>" for n in names) + f'<th>{L("Year", "السنة")}</th></tr>'
    body = ""
    for y in years:
        cells, yr = "", 1.0
        for m in range(1, 13):
            v = mret.get((y, m))
            if v is None:
                cells += "<td></td>"
                continue
            yr *= 1 + v / 100
            a = min(abs(v) / 6, 1) * .55 + .08
            col = f"rgba(74,222,128,{a:.2f})" if v >= 0 else f"rgba(248,113,113,{a:.2f})"
            cells += f'<td style="background:{col}">{_ltr("%+.1f" % v)}</td>'
        tot = (yr - 1) * 100
        body += f'<tr><th>{y}</th>{cells}<td class="yr {"up" if tot >= 0 else "dn"}">{_ltr("%+.1f%%" % tot)}</td></tr>'
    return f'<div class="rbtw"><table class="rbheat">{head}{body}</table></div>'


def next_scan(now=None):
    d = R.settled_day(now).date()
    cal = PF._cal()
    nxt = cal.next_trading_day(d)
    while nxt.isocalendar()[1] == d.isocalendar()[1]:
        nxt = cal.next_trading_day(nxt)
    return nxt


def bot_plan(state, rep, feats):
    """(trades, summary, when, first) of the bot's next trades for the dashboard, or None (no bot at this level, no prices).
    Before the first close: the first trades of the money going in; after: the next weekly scan with what is free."""
    plan = state["plans"][-1]
    w = plan["targets"].get(R.BOT, 0)
    if not w or not feats:
        return None
    lv = plan.get("level") if plan.get("level") in RB.SAT else 10
    sh = plan.get("sharia", False)
    book = rep.get("book")
    if rep.get("pending") or book is None:
        tp, summ = RB.trade_plan(feats, float(state["amount"]) * w / 100, lv, sh)
        return tp, summ, _date(rep["start"]), True
    pos = book.positions(rep["vday"])
    n_l = sum(1 for p in pos if p["side"] == "long")
    tp, summ = RB.trade_plan(feats, book.value(rep["vday"]), lv, sh, held=set(book.pos), cool=set(book.cool), n_long_held=n_l,
                             n_short_held=len(pos) - n_l)
    if getattr(book, "wait", None) is not None:           # today's scan: filled in tonight's after-hours session
        return tp, summ, f'{_date(book.wait)} · {L("after the close", "بعد الإغلاق")}', False
    return tp, summ, _date(next_scan()), False


def bot_notice_html(bp):
    """A slim card on the overview: the companies the bot opens next, the full plan in its own tab."""
    tp, summ, when, first = bp
    now = [x for x in tp if not x["next"]]
    lab = L("first trades after the close of", "أول صفقاته بعد إغلاق") if first else L("next scan", "المسح الجاي")
    if now:
        ticks = "".join(f'<span class="rbtk {x["side"]}">{T.icon("north_east" if x["side"] == "long" else "south_east")}{x["t"]}</span>' for x in now)
    else:
        ticks = f'<span class="rbtk none">{L("no new trade", "ما فيه صفقة جديدة")}</span>'
    return (f'<div class="rbnote2">{T.icon("radar")}<div><b>{L("Opportunity Bot", "بوت الفرص")} · {lab} {_esc(when)}</b>'
            f'<div class="tks">{ticks}</div><span>{L("Its full trading plan (entry, stop, size, risk) is in the Opportunity Bot tab.", "خطته الكاملة للتداول (الدخول والوقف والحجم والمخاطرة) في تبويب «بوت الفرص».")}</span></div></div>')


def bot_tab(state, rep, feats, bp=None):
    book = rep.get("book")
    plan = state["plans"][-1]
    on = plan["targets"].get(R.BOT, 0) > 0
    lv = plan.get("level") or 10
    prof = {"level": lv if lv in RB.SAT else 10, "sharia": plan.get("sharia", False)}
    if not on:
        st.info(L("The bot is off at your current risk level (it runs at levels 9 and 10). Its past trades stay below.",
                  "البوت متوقف في مستوى المخاطرة الحالي (يشتغل في المستوى 9 و10). صفقاته السابقة باقية تحت."), icon=":material/power_off:")
    else:
        ui.html(bot_card(prof, stats_line=None))
    if book is None:                           # before the first close: its first trades, its radar
        if bp:
            ui.sec("checklist", "Trading plan: the companies it enters first", "خطة التداول: الشركات اللي بيدخلها أول")
            ui.html(plan_html(*bp))
        if on and feats:
            ui.sec("travel_explore", "On the radar now", "على الرادار الحين")
            lg, sh = RB.radar(feats, prof["sharia"], n_long=10 if prof["sharia"] else 5, n_short=5)
            ui.html(radar_html(lg, sh, key=not (bp and bp[0])))
        elif on:
            st.info(L("The bot's prices aren't available right now. Try again in a minute.", "أسعار البوت مو متاحة الحين. جرّب بعد دقيقة."),
                    icon=":material/cloud_off:")
        return
    d = rep["vday"]
    val, cost = book.value(d), book.cost
    s = RB.stats(book)
    pos = book.positions(d)
    n_l = sum(1 for p in pos if p["side"] == "long")
    gain = val - cost
    ui.html(PP.kpis([
        ("radar", L("Bot slice", "حصة البوت"), _m(val, 2), f'{L("money in it", "المبلغ فيها")} <b>{_m(cost)}</b>', None, None),
        ("show_chart", L("Gain", "الربح"), _m(gain, 2, True), f'<b>{_p(gain / cost * 100 if cost else 0, 1, True)}</b>', PP._k(gain), None),
        ("target", L("Closed trades", "الصفقات المغلقة"), str(s.get("n", 0)),
         f'{L("won", "ربحت")} <b>{_p(s.get("win"), 0) if s.get("n") else "—"}</b>', None, None),
        ("event_repeat", L("Next scan", "المسح الجاي"), _date(next_scan()) if on else "—",
         f'{L("Long", "شراء")} <b>{n_l}</b> · {L("Short", "مكشوف")} <b>{len(pos) - n_l}</b>', None, None)], "c4"))
    if bp:
        ui.sec("checklist", "Trading plan for the next scan", "خطة التداول للمسح الجاي")
        ui.html(plan_html(*bp))
    ui.sec("radar", "Open positions", "المراكز المفتوحة")
    ui.html(positions_html(pos))
    if on and feats:
        ui.sec("travel_explore", "On the radar now", "على الرادار الحين")
        lg, sh = RB.radar(feats, prof["sharia"], n_long=10 if prof["sharia"] else 5, n_short=5)
        ui.html(radar_html(lg, sh, key=not (bp and bp[0])))
        st.caption(L(f"Scores from the latest prices. A signal of {RB.THRESHOLD} or more can be bought or sold short at the next weekly scan, when a slot is free.",
                     f"التقييم من آخر الأسعار. الإشارة {RB.THRESHOLD} أو أكثر ممكن تنشرى أو تنباع على المكشوف في المسح الأسبوعي الجاي إذا فيه خانة فاضية."))
    if book.curve and len(book.curve) > 1:
        cv = pd.DataFrame(book.curve, columns=["d", "value", "cost"]).set_index("d")
        cv = cv[cv["cost"] > 0]
        if len(cv) > 1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=cv.index, y=cv["value"], name=L("Bot slice", "حصة البوت"), line=dict(color=BOT_C, width=2.4), fill="tozeroy",
                                     fillcolor=C.rgba(BOT_C, 0.10), hovertemplate="%{x|%b %d, %Y}: " + _tp() + "%{y:,.0f}<extra></extra>"))
            fig.add_trace(go.Scatter(x=cv.index, y=cv["cost"], name=L("Money in it", "المبلغ فيها"), line=dict(color=T.GOLD, width=1.4, dash="dash", shape="hv"),
                                     hovertemplate="%{x|%b %d, %Y}: " + _tp() + "%{y:,.0f}<extra></extra>"))
            lo, hi = float(min(cv.min())), float(max(cv.max()))
            C.style(fig, 300, L("The bot's slice", "حصة البوت"))
            fig.update_yaxes(range=[lo - (hi - lo) * .1 - 1, hi + (hi - lo) * .1 + 1], tickprefix=_tp(), tickformat=",.0f")
            ui.chart(fig, key="rb_botcv")
    if book.trades:
        ui.sec("receipt_long", "Closed trades", "الصفقات المغلقة")
        ui.html(trades_html(book.trades))


def plan_page(state, row, rkey, err):
    ans = dict(ss.get("rb_ans") or {})
    if not all(ans.get(q) for q in R.QIDS):
        ss["rb_mode"] = "quiz"
        st.rerun()
    amount, monthly = float(ans.get("amount") or 10000), float(ans.get("monthly") or 0)
    if state:                                  # a new plan for an existing robo portfolio: the money already invested stays
        amount = float(state.get("amount") or amount)
    rec = R.profile(ans)
    if not isinstance(ss.get("rb_lvl"), int):
        ss["rb_lvl"] = int(rec["rec"])
    prof = R.profile(ans, level=ss["rb_lvl"])
    ui.html(result_html(prof))
    s1, s2 = st.columns([2.2, 1])
    with s1:
        st.slider(L("Fine-tune the risk level", "عدّل مستوى المخاطرة"), 1, 10, key="rb_lvl",
                  help=L("The plan updates as you move it. Above the recommended level, the swings may be more than your answers support.",
                         "الخطة تتحدث مع التحريك. فوق المستوى الموصى به، ممكن يكون التذبذب أكبر مما تسمح فيه إجاباتك."))
    with s2:
        if prof["level"] > rec["rec"]:
            st.warning(L(f"Above your recommended level ({rec['rec']}): deeper falls than your answers allow.",
                         f"أعلى من مستواك الموصى به ({rec['rec']}): نزول أعمق مما تسمح فيه إجاباتك."), icon=":material/warning:")
        elif prof["level"] < rec["rec"]:
            st.info(L(f"Below your recommended level ({rec['rec']}): steadier, with a lower expected return.",
                      f"أقل من مستواك الموصى به ({rec['rec']}): أهدى، وعائده المتوقع أقل."), icon=":material/info:")
    ui.ai_note("Robo plan", f"risk level {prof['level']}/10 (recommended {prof['rec']}), stocks {prof['stocks']:.0f}%, expected "
               f"{prof['mu']:.1f}% a year, volatility {prof['vol']:.1f}%, a bad year {prof['bad']:.1f}%")
    ui.ai_note("Robo funds", ", ".join(f"{T.sym_label(t, False)} {w:g}%" for t, w in sorted(prof["targets"].items(), key=lambda x: -x[1])))
    ui.sec("donut_large", "Your portfolio", "محفظتك")
    ui.html(allocation_html(prof))
    has_bot = R.BOT in prof["targets"]
    feats = load_bot() if has_bot else {}
    px = R.prices([t for t in prof["targets"] if t != R.BOT] + list(R.bench_funds()), "5y")
    bt, btb = R.backtest(prof, amount, monthly, px, bot=feats if has_bot else None)
    if has_bot:
        ui.sec("radar", "Opportunity Bot", "بوت الفرص")
        line = bot_stats_line(bt.get("book")) if bt is not None and not bt.get("pending") else None
        ui.html(bot_card(prof, stats_line=line))
        if feats:
            tp, summ = RB.trade_plan(feats, amount * RB.SAT.get(prof["level"], 0) / 100, prof["level"], prof["sharia"])
            ui.html(f'<div class="rbsub">{T.icon("checklist")}{L("Its trading plan: the companies it would enter first", "خطته للتداول: الشركات اللي بيدخلها أول")}</div>'
                    + plan_html(tp, summ))
            lg, sh = RB.radar(feats, prof["sharia"], n_long=10 if prof["sharia"] else 5, n_short=5)
            ui.html(f'<div class="rbsub">{T.icon("travel_explore")}{L("On its radar now", "على راداره الحين")}</div>' + radar_html(lg, sh, key=not tp))
        else:
            st.info(L("The bot's prices aren't available right now, so its radar and its past are missing here. Try again in a minute.",
                      "أسعار البوت مو متاحة الحين، فراداره وتاريخه ناقصين هنا. جرّب بعد دقيقة."), icon=":material/cloud_off:")
    elif not _sa():                            # the Saudi robo has no Opportunity Bot
        ui.html(lock_html(rec["rec"]))
    ui.sec("query_stats", "What to expect", "وش تتوقع")
    ui.html(expect_kpis(prof))
    f1, f2 = st.columns([1.25, 1])
    with f1:
        ui.chart(frontier_fig(prof), key="rb_front")
    with f2:
        ui.html(stress_html(prof))
    ui.sec("flag", "Your future", "مستقبلك")
    yrs = [3, 5, 10, 15, 20, 25, 30]
    g1, g2 = st.columns([1.6, 1], vertical_alignment="bottom")
    with g1:
        years = st.segmented_control(L("Years", "السنوات"), yrs, default=min(yrs, key=lambda y: abs(y - prof["years"])), key="rb_years",
                                     format_func=lambda y: L(f"{y} years", f"{y} سنة")) or prof["years"]
    with g2:
        goal = st.number_input(L(f"A goal, if you have one ({_cur()})", f"هدف مالي إذا عندك ({_cur()})"), min_value=0, max_value=100_000_000, step=10_000,
                               key="rb_goal", help=L("The chance the plan gets there in time.", "احتمال إن الخطة توصله في الوقت."))
    proj = R.project(prof["mu"], prof["vol"], amount, monthly, years, goal=goal or None)
    ui.chart(projection_fig(proj, years, goal or None), key="rb_proj")
    beat = proj.attrs["beat"]
    chips = [f'<span class="rbchip">{T.icon("percent")}{L(f"{beat:.0f}% of the paths end above the money invested", f"{beat:.0f}% من الاحتمالات تنتهي فوق المبلغ المستثمر")}</span>',
             f'<span class="rbchip">{T.icon("insights")}{L("A middle outcome", "نتيجة متوسطة")} {_ltr(_m(proj["p50"].iloc[-1]))}</span>']
    if goal:
        gp = proj.attrs.get("goal_p", 0)
        chips.append(f'<span class="rbchip {"gold" if gp >= 50 else "warn"}">{T.icon("flag")}{L("Chance to reach", "احتمال الوصول لـ")} {_ltr(_m(goal))}: '
                     f'<b>{_ltr("%.0f%%" % gp)}</b></span>')
    ui.html(f'<div class="rbchips" style="margin:-4px 0 10px">{"".join(chips)}</div>')
    ui.sec("history", "The last five years", "آخر خمس سنوات")
    if bt is not None and not bt.get("pending"):
        start = bt["curve"].index[0]
        ui.chart(lines_fig(bt, btb, L(f"Your plan since {_date(start)}, with the same deposits", f"خطتك من {_date(start)} بنفس الإيداعات")), key="rb_bt")
        ui.html(f'<div class="rbtw">{_mtab(R.metrics(bt["curve"]), R.metrics(btb["curve"]))}</div>')
        st.caption(L(f"Real daily prices with dividends reinvested, managed by the same rules. The benchmark holds {_bench_txt()} at the same stock share. Past results do not repeat.",
                     f"أسعار يومية حقيقية مع إعادة استثمار التوزيعات، وبنفس قواعد الإدارة. المؤشر المرجعي فيه {_bench_txt()} بنفس نسبة الأسهم. النتائج السابقة ما تتكرر بالضرورة.")
                   + (L(" The Tadawul funds are young (the sukuk, gold and US funds listed in 2022), so the test starts when they all have prices.",
                        " صناديق تداول حديثة (الصكوك والذهب والأسهم الأمريكية أُدرجت في 2022)، فالاختبار يبدأ من أول يوم لها كلها أسعار.") if _sa() else "")
                   + (L(" The bot's list is today's companies, so its past looks better than it really was.",
                        " قائمة البوت هي شركات اليوم، فماضيه يطلع أحسن من الحقيقة.") if has_bot else ""))
    else:
        st.info(L("The price history isn't available right now. Try again in a minute.", "تاريخ الأسعار مو متاح الحين. جرّب بعد دقيقة."), icon=":material/cloud_off:")
    ui.sec("description", "Your Investment Policy Statement", "بيان سياسة الاستثمار")
    ui.html(ips_html(prof, ans, amount, monthly))
    st.download_button(L("Download the IPS", "حمّل بيان السياسة"), ips_file(prof, ans, amount, monthly).encode("utf-8"), file_name="TURA-IPS.html",
                       mime="text/html", icon=":material/download:", key="rb_ips_dl")
    ui.html(note())
    b1, b2, b3 = st.columns([1, 1.6, 1])
    with b1:
        if st.button(L("Edit answers", "عدّل الإجابات"), key="rb_edit", icon=":material/edit:", width="stretch"):
            ss["rb_mode"] = "quiz"
            ss["rb_step"] = 0
            st.rerun()
    with b2:
        label = (L("Apply to my robo portfolio", "طبّق على محفظتي الآلية") if state else
                 L(f"Start investing {_m(amount)}", f"ابدأ الاستثمار بـ {_m(amount)}"))
        if st.button(label, type="primary", key="rb_go", icon=":material/rocket_launch:", width="stretch"):
            activate(state, row, rkey, err, ans, prof, amount, monthly)


def activate(state, row, rkey, err, ans, prof, amount, monthly):
    now = PF.utcnow()
    if state:
        at = PF.iso(now)
        state["answers"] = dict(ans)
        state["plans"].append({"at": at, "level": prof["level"], "rec": prof["rec"], "targets": prof["targets"], "sharia": prof["sharia"],
                               "stocks": prof["stocks"], "why": "retake"})
        cur = state["monthly"][-1]["amount"] if state.get("monthly") else 0
        if float(monthly) != float(cur):
            state["monthly"].append({"at": at, "amount": float(monthly)})
        flash = L("Your new plan is applied at the next close", "خطتك الجديدة تتطبق مع الإغلاق الجاي")
    else:
        state = R.new_robo(ans, prof, amount, monthly, now=now)
        flash = L("Your robo portfolio is on: the first investment goes in at the next close", "محفظتك الآلية اشتغلت: أول استثمار يدخل مع الإغلاق الجاي")
        return commit(state, row, rkey, err, flash, fresh=True)
    commit(state, row, rkey, err, flash)


# ---------------------------------------------------------------- the questionnaire in progress, kept in the browser
# Answers, the step, the plan screen and its settings are written into this browser (a year, with the visitor's portfolio code:
# p_portfolio.keep), so closing the site half way and coming back opens the questionnaire or the plan where it was left.
# Cleared once the plan is invested.
DRAFT = "alt_rb"
_DRAFT_KEYS = {"rb_step": "s", "rb_mode": "m", "rb_lvl": "l", "rb_years": "y", "rb_goal": "g", "rb_amt": "am", "rb_mon": "mo"}


def _draft_cookie(value):
    PP.keep({DRAFT: value or None})


def _draft_value():
    import base64
    import json
    d = {"a": {k: v for k, v in (ss.get("rb_ans") or {}).items() if k in R.Q or k in ("amount", "monthly")}}
    for k, short in _DRAFT_KEYS.items():
        if ss.get(k) is not None:
            d[short] = ss[k]
    raw = json.dumps(d, separators=(",", ":"), sort_keys=True)
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def _draft_keep():
    """Writes the questionnaire in progress into the browser when it changed; removes it once the plan is invested."""
    if ss.pop("rb_draft_kill", False):
        _draft_cookie(None)
        return
    if ss.get("rb_mode") not in ("quiz", "plan") and not (ss.get("rb_ans") or {}):
        return
    v = _draft_value()
    if ss.get("rb_draft_v") != v:
        ss["rb_draft_v"] = v
        _draft_cookie(v)


def _draft_clear():
    """The cookie goes on the next full run of the page (a run cut short by a rerun may never reach the browser)."""
    ss["rb_draft_v"] = None
    ss["rb_draft_kill"] = True


def _draft_restore():
    """Once per visit: the questionnaire this browser left half way (its cookie), back where it was."""
    import base64
    import json
    if ss.get("rb_restored"):
        return
    ss["rb_restored"] = True
    if ss.get("rb_ans"):
        return
    raw = PP.stored(DRAFT)
    if not raw:
        return
    try:
        d = json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode())
    except Exception:
        return
    ans = {k: v for k, v in (d.get("a") or {}).items() if (k in R.Q and R.opt(k, v)) or (k in ("amount", "monthly") and isinstance(v, int))}
    if not ans:
        return
    ss["rb_ans"] = ans
    step = d.get("s")
    ss["rb_step"] = int(step) if isinstance(step, int) and 0 <= step < len(R.STEPS) else min(len(ans), len(R.STEPS) - 1)
    mode = d.get("m")
    ss["rb_mode"] = mode if mode in ("quiz", "plan") else None
    if mode == "plan" and not all(ans.get(q) for q in R.QIDS):
        ss["rb_mode"] = "quiz"
    for k, short in (("rb_lvl", "l"), ("rb_years", "y")):
        v = d.get(short)
        if isinstance(v, int) and 1 <= v <= 40:
            ss[k] = v
    for k, short, lo, hi in (("rb_goal", "g", 0, 100_000_000), ("rb_amt", "am", 1000, 10_000_000), ("rb_mon", "mo", 0, 1_000_000)):
        v = d.get(short)
        if isinstance(v, int) and lo <= v <= hi:
            ss[k] = v
    ss["rb_draft_v"] = raw
    if ss["rb_mode"]:
        ss["rb_flash"] = L("Welcome back: carrying on where you left off", "أهلاً من جديد: كمّلنا من حيث وقفت")


def commit(state, row, rkey, err, flash=None, fresh=False):
    """Keeps a change and reloads the page. fresh: a new robo portfolio (it replaces whatever the row held). If the saved one
    moved on meanwhile (another tab), nothing is overwritten; if the store can't be reached, this visit keeps its own copy."""
    if err is not None:
        ss["rb_practice"] = state
    else:
        try:
            R.save(state, row, expect="any" if fresh or row is None else state.get("rev"), key=rkey)
        except R.Conflict:
            ss["rb_flash"] = L("Your robo portfolio changed a moment ago. Check it and try again.", "محفظتك الآلية تغيرت قبل لحظات. راجعها وجرّب مرة ثانية.")
            st.rerun()
        except PB.StoreError:
            st.error(L("Saving isn't available right now. Try again in a minute.", "الحفظ مو متاح الحين. جرّب بعد دقيقة."), icon=":material/cloud_off:")
            return
    ss["rb_mode"] = None
    if ss.get("rb_ans"):                        # a plan was just invested: nothing is left in progress
        ss["rb_ans"] = {}
        _draft_clear()
    if flash:
        ss["rb_flash"] = flash
    st.rerun()


# =====================================================================
# the dashboard
# =====================================================================
EVENT = {"start": ("rocket_launch", "#7B45F0", "First investment", "أول استثمار"),
         "monthly": ("savings", "#2DB6EB", "Monthly deposit invested", "استثمار الإيداع الشهري"),
         "deposit": ("add_card", "#34D399", "Deposit invested", "استثمار إيداع"),
         "withdraw": ("payments", "#F97316", "Withdrawal", "سحب"),
         "rebalance": ("balance", "#3B8BEB", "Rebalanced", "إعادة توازن"),
         "review": ("fact_check", "#4ADE80", "Quarterly review: on target", "مراجعة ربع سنوية: على النسب"),
         "plan": ("tune", "#F5B94A", "New plan applied", "تطبيق خطة جديدة")}


def _trades_text(tr):
    buys = sorted(((t, v) for t, v in (tr or {}).items() if v > 0), key=lambda x: -x[1])
    sells = sorted(((t, v) for t, v in (tr or {}).items() if v < 0), key=lambda x: x[1])
    parts = []
    if buys:
        parts.append(L("Bought ", "شراء ") + _ltr(", ".join(f"{_tk(t)} {_m(v)}" for t, v in buys[:4])))
    if sells:
        parts.append(L("Sold ", "بيع ") + _ltr(", ".join(f"{_tk(t)} {_m(-v)}" for t, v in sells[:4])))
    return " · ".join(parts)


def timeline_html(events, limit=None):
    evs = list(reversed(events))
    if limit:
        evs = evs[:limit]
    out = []
    for i, e in enumerate(evs):
        ic, col, en, ar = EVENT[e["kind"]]
        title = L(en, ar)
        amt = f' <span class="am">{_m(abs(e["amount"]))}</span>' if e.get("amount") else ""
        if e["kind"] == "rebalance":
            title += " · " + (L("a fund left its range", "صندوق خرج عن نطاقه") if e.get("why") == "drift" else L("quarterly review", "مراجعة ربع سنوية"))
        if e["kind"] == "plan" and e.get("level"):
            title += f' · {L("level", "المستوى")} {e["level"]}'
        det = _trades_text(e.get("trades"))
        if e["kind"] == "review":
            det = L(f"Largest gap {e.get('max', 0):.1f} points: no trade needed", f"أكبر فرق {e.get('max', 0):.1f} نقطة: ما احتاج أي صفقة")
        out.append(f'<div class="e" style="--i:{i}"><span class="ti" style="--c:{col}">{T.icon(ic)}</span><div><b>{_esc(title)}</b>{amt}'
                   f'{f"<p>{det}</p>" if det else ""}</div><span class="dt">{_date(e["d"])}</span></div>')
    return f'<div class="rbtl">{"".join(out)}</div>'


def drift_html(rows):
    top = max([max(r["weight"], r["target"] + r["band"]) for r in rows] + [10])
    sc = lambda v: max(0.0, min(100.0, v / top * 100))
    out = []
    for r in rows:
        f = _fund(r["t"])
        lo, hi = max(r["target"] - r["band"], 0), r["target"] + r["band"]
        a = abs(r["drift"])
        k = "ok" if a <= r["band"] * 0.6 else "near" if a <= r["band"] else "out"
        out.append(f'<div class="r" style="--c:{f["c"]}"><div class="f"><span class="tk">{_esc(_tk(r["t"]))}</span><span>{_esc(f["cls"])}</span></div>'
                   f'<div class="tr"><span class="bd" style="left:{sc(lo):.1f}%;width:{sc(hi) - sc(lo):.1f}%"></span>'
                   f'<span class="cu" style="width:{sc(r["weight"]):.1f}%"></span><span class="tg" style="left:{sc(r["target"]):.1f}%"></span></div>'
                   f'<div class="v"><b>{_ltr("%.1f%%" % r["weight"])}</b><em class="{k}">{_ltr("%+.1f" % r["drift"])} {L("pts", "نقطة")}</em></div></div>')
    leg = (f'<div class="rblg"><span><i style="width:14px;height:8px;border-radius:3px;background:#60A5FA"></i>{L("now", "الحالي")}</span>'
           f'<span><i style="width:3px;height:12px;background:#FCD34D"></i>{L("target", "المستهدف")}</span>'
           f'<span><i style="width:14px;height:10px;background:rgba(45,182,235,.18);border:1px dashed rgba(45,182,235,.6)"></i>{L("range", "النطاق")}</span></div>')
    return f'<div class="rbdr">{"".join(out)}{leg}</div>'


def holdings_html(rows):
    head = (f'<tr><th>{L("Fund", "الصندوق")}</th><th class="n">{L("Units", "الوحدات")}</th><th class="n">{L("Price", "السعر")}</th>'
            f'<th class="n">{L("Value", "القيمة")}</th><th class="n">{L("Weight", "الوزن")}</th><th class="n">{L("Target", "المستهدف")}</th>'
            f'<th class="n">{L("Gain", "الربح")}</th></tr>')
    body = ""
    for r in rows:
        f = _fund(r["t"])
        g = r["gain"]
        gp = g / r["cost"] * 100 if r["cost"] > 0 else 0
        k = "up" if g > 0.005 else "dn" if g < -0.005 else ""
        units = "—" if r["t"] in ("CASH", R.BOT) or r["units"] is None else f'{r["units"]:,.4f}'
        price = "—" if r["t"] in ("CASH", R.BOT) or r["price"] is None else _m(r["price"], 2)
        body += (f'<tr><td><span class="tk" style="--c:{f["c"]}">{_esc(_tk(r["t"]))}</span><span class="cl">{_esc(f["cls"])}</span></td><td class="n">{_ltr(units)}</td>'
                 f'<td class="n">{_ltr(price)}</td><td class="n"><b>{_ltr(_m(r["value"], 2))}</b></td><td class="n">{_ltr("%.1f%%" % r["weight"])}</td>'
                 f'<td class="n">{_ltr("%g%%" % r["target"])}</td><td class="n {k}">{_ltr("%s (%+.1f%%)" % (_m(g, 2, True), gp))}</td></tr>')
    return f'<div class="rbtw"><table class="rbtbl">{head}{body}</table></div>'


def dash_hero(state, rep, err):
    plan = state["plans"][-1]
    lv = plan.get("level") or 5
    cur = rep["curve"]
    if rep["pending"]:
        val, inv = float(state["amount"]), float(state["amount"])
    else:
        val = rep["live"]["value"] if rep.get("live") else float(cur["value"].iloc[-1])
        inv = float(cur["invested"].iloc[-1])
    gain = val - inv
    whole, cents = f"{val:,.2f}".split(".")
    m = R.metrics(cur) if not rep["pending"] else {}
    ret = m.get("ret")
    day = None
    if not rep["pending"]:
        if rep.get("live"):
            day = val - float(cur["value"].iloc[-1])
        elif len(cur) >= 2:
            day = float(cur["value"].iloc[-1]) - float(cur["value"].iloc[-2]) - float(cur["flow"].iloc[-1])
    arrow = lambda x: "▲" if x > 0 else "▼" if x < 0 else "•"
    pls = f'<span class="pl {PP._k(gain)}">{arrow(gain)} {PP._bdi(_m(gain, 2, True))} <em>{L("vs money invested", "مقابل المبلغ المستثمر")}</em></span>'
    if ret is not None:
        pls += f'<span class="pl {PP._k(ret)}">{arrow(ret)} {PP._bdi(_p(ret, 2, True))} <em>{L("time-weighted", "موزون زمنياً")}</em></span>'
    if day is not None:
        pls += f'<span class="pl {PP._k(day)}">{arrow(day)} {PP._bdi(_m(day, 2, True))} <em>{L("Today", "اليوم") if rep.get("live") else L("Last session", "آخر جلسة")}</em></span>'
    mon = state["monthly"][-1]["amount"] if state.get("monthly") else 0
    chips = [f'<span class="chip">{T.icon("savings")}{L("Invested", "المستثمر")} <b>{_m(inv)}</b></span>',
             f'<span class="chip">{T.icon("event_repeat")}{L("Monthly", "شهرياً")} <b>{_m(mon)}</b></span>',
             f'<span class="chip">{T.icon("speed")}{L("Level", "المستوى")} <b>{lv}/10 · {_esc(_prof_name(lv))}</b></span>']
    if plan.get("sharia"):
        chips.append(f'<span class="chip">{T.icon("mosque")}<b>{L("Sharia-compliant", "متوافقة مع الشريعة")}</b></span>')
    if plan["targets"].get(R.BOT):
        chips.append(f'<span class="chip">{T.icon("radar")}{L("Opportunity Bot", "بوت الفرص")} <b>{_ltr("%g%%" % plan["targets"][R.BOT])}</b></span>')
    badge = (f'<span class="rbauto wait"><i></i>{L("Waiting for the first close", "بانتظار أول إغلاق")}</span>' if rep["pending"] else
             f'<span class="rbauto"><i></i>{L("Autopilot on", "الإدارة التلقائية شغالة")}</span>')
    if rep.get("missing"):
        badge = f'<span class="rbauto wait"><i></i>{L("Prices loading", "الأسعار تتحمّل")}</span>'
    if err is not None:
        badge = f'<span class="pfmode prac">{T.icon("science")}{L("This visit only (not saved)", "لهالزيارة فقط (ما ينحفظ)")}</span>'
    spark = PP._spark(cur["value"] if len(cur) else pd.Series([val, val]))
    return (f'<div class="pfhero"><div class="grid"></div><div class="top"><div class="eb">{T.icon("smart_toy")}{L("Robo portfolio", "المحفظة الآلية")}'
            f'</div>{badge}</div><div class="mid"><div><div class="eql">{L("Portfolio value", "قيمة المحفظة")}</div>'
            f'<div class="eq"><span dir="ltr">{"SAR " if _sa() else "$"}{whole}<small>.{cents}</small></span></div><div class="pls">{pls}</div></div>'
            f'<div class="sp">{spark}</div></div><div class="chips">{"".join(chips)}</div></div>')


def next_html(state, rep):
    nd, nq = R.next_dates(start=rep.get("start"))
    mon = state["monthly"][-1]["amount"] if state.get("monthly") else 0
    rows = R.holdings(rep)
    if rows:
        worst = max(rows, key=lambda r: abs(r["drift"]) / r["band"] if r["band"] else 0)
        inside = all(abs(r["drift"]) <= r["band"] for r in rows)
        dr = (f'<b>{L("All funds in range", "كل الصناديق داخل نطاقها") if inside else L("Rebalance due", "يحتاج إعادة توازن")}</b>'
              f'<em>{L("largest gap", "أكبر فرق")} {_ltr(worst["t"])} {_ltr("%+.1f" % worst["drift"])} {L("pts", "نقطة")}</em>')
    else:
        dr = f'<b>—</b><em>{L("after the first close", "بعد أول إغلاق")}</em>'
    dep = (f'<b>{_date(nd)}</b><em>{_m(mon)} {L("to invest", "للاستثمار")}</em>' if mon > 0 else
           f'<b>{L("Off", "متوقف")}</b><em>{L("set one under Manage", "فعّله من الإدارة")}</em>')
    return (f'<div class="rbnext"><div><span class="i">{T.icon("event_repeat")}</span><div><span>{L("Next deposit", "الإيداع الجاي")}</span>{dep}</div></div>'
            f'<div><span class="i y">{T.icon("fact_check")}</span><div><span>{L("Next review", "المراجعة الجاية")}</span><b>{_date(nq)}</b>'
            f'<em>{L("quarterly rebalance check", "فحص إعادة التوازن الربعي")}</em></div></div>'
            f'<div><span class="i g">{T.icon("balance")}</span><div><span>{L("Drift", "الانحراف")}</span>{dr}</div></div></div>')


def manage(state, row, rkey, err):
    ui.sec("settings", "Manage", "الإدارة")
    acts = ["monthly", "flow", "level", "quiz", "close"]
    names = {"monthly": L("Monthly deposit", "الإيداع الشهري"), "flow": L("Add or withdraw", "إيداع أو سحب"), "level": L("Risk level", "مستوى المخاطرة"),
             "quiz": L("Questionnaire", "الاستبيان"), "close": L("Close", "إغلاق")}
    act = st.segmented_control(L("Action", "الإجراء"), acts, default="monthly", key="rb_act", label_visibility="collapsed",
                               format_func=lambda k: names[k]) or "monthly"
    now = PF.iso(PF.utcnow())
    if act == "monthly":
        cur = int(state["monthly"][-1]["amount"]) if state.get("monthly") else 0
        c1, c2 = st.columns([2, 1], vertical_alignment="bottom")
        with c1:
            v = st.number_input(L(f"Monthly deposit ({_cur()})", f"الإيداع الشهري ({_cur()})"), min_value=0, max_value=1_000_000, value=cur, step=50, key="rb_mon_new")
        with c2:
            if st.button(L("Save", "احفظ"), key="rb_mon_save", type="primary", width="stretch", disabled=int(v) == cur):
                state["monthly"].append({"at": now, "amount": float(v)})
                commit(state, row, rkey, err, L("Monthly deposit updated", "تحدّث الإيداع الشهري"))
        st.caption(L("Invested on the first trading day of each month, into the funds under their target first. 0 stops it.",
                     "يُستثمر أول يوم تداول من كل شهر، في الصناديق الأقل من نسبتها أولاً. صفر يوقفه."))
    elif act == "flow":
        c1, c2, c3 = st.columns([1.2, 1.4, 1], vertical_alignment="bottom")
        with c1:
            kind = st.segmented_control(L("Type", "النوع"), ["in", "out"], default="in", key="rb_flow_k",
                                        format_func=lambda k: L("Deposit", "إيداع") if k == "in" else L("Withdraw", "سحب")) or "in"
        with c2:
            amt = st.number_input(L(f"Amount ({_cur()})", f"المبلغ ({_cur()})"), min_value=50, max_value=10_000_000, value=1000, step=50, key="rb_flow_a")
        with c3:
            if st.button(L("Confirm", "تأكيد"), key="rb_flow_go", type="primary", width="stretch"):
                state["flows"].append({"at": now, "amount": float(amt) if kind == "in" else -float(amt)})
                commit(state, row, rkey, err, L("Done: it is carried out at the next close", "تم: يتنفذ مع الإغلاق الجاي"))
        st.caption(L("A deposit buys the funds under their target first; a withdrawal sells those over it first. Carried out at the next close.",
                     "الإيداع يشتري الصناديق الأقل من نسبتها أولاً، والسحب يبيع الأعلى من نسبتها أولاً. يتنفذ مع الإغلاق الجاي."))
    elif act == "level":
        plan = state["plans"][-1]
        ans = state.get("answers") or {}
        rec = R.profile(ans)["rec"] if ans else plan.get("level", 5)
        cur = int(plan.get("level") or rec)
        lv = st.slider(L("Risk level", "مستوى المخاطرة"), 1, 10, value=cur, key="rb_lvl_new")
        prof = R.profile(ans, level=lv)
        ui.html(f'<div class="rbchips" style="margin:2px 0 8px">'
                + "".join(f'<span class="rbchip"><b style="color:{_fund(t)["c"]}">{_esc(_tk(t))}</b> {w:g}%</span>' for t, w in sorted(prof["targets"].items(), key=lambda x: -x[1]))
                + f'<span class="rbchip">{T.icon("trending_up")}{_p(prof["mu"], 1)} · {T.icon("ssid_chart")}{_p(prof["vol"], 1)}</span></div>')
        if lv > rec:
            st.warning(L(f"Above your recommended level ({rec}).", f"أعلى من مستواك الموصى به ({rec})."), icon=":material/warning:")
        if st.button(L("Apply the new level", "طبّق المستوى الجديد"), key="rb_lvl_go", type="primary", disabled=lv == cur):
            state["plans"].append({"at": now, "level": lv, "rec": rec, "targets": prof["targets"], "sharia": prof["sharia"], "stocks": prof["stocks"],
                                   "why": "level"})
            commit(state, row, rkey, err, L("New level applied at the next close", "المستوى الجديد يتطبق مع الإغلاق الجاي"))
    elif act == "quiz":
        st.caption(L("Life changed? Answer again: the new plan replaces the old one at the next close, the money stays invested.",
                     "تغيرت ظروفك؟ جاوب من جديد: الخطة الجديدة تحل محل القديمة مع الإغلاق الجاي، والفلوس تبقى مستثمرة."))
        if st.button(L("Retake the questionnaire", "أعد الاستبيان"), key="rb_retake", icon=":material/restart_alt:"):
            a = dict(state.get("answers") or {})
            a["amount"] = int(state.get("amount") or 10000)
            a["monthly"] = int(state["monthly"][-1]["amount"]) if state.get("monthly") else 0
            ss["rb_ans"] = a
            ss["rb_step"] = 0
            ss["rb_mode"] = "quiz"
            for k in ("rb_amt", "rb_mon", "rb_lvl"):
                ss.pop(k, None)
            st.rerun()
    else:
        st.caption(L("Closing removes the robo portfolio and its history. You can start a new one any time.",
                     "الإغلاق يحذف المحفظة الآلية وسجلها. تقدر تبدأ وحدة جديدة في أي وقت."))
        sure = st.toggle(L("Yes, close my robo portfolio", "نعم، سكّر محفظتي الآلية"), key="rb_close_ok")
        if st.button(L("Close the robo portfolio", "سكّر المحفظة الآلية"), key="rb_close", disabled=not sure, icon=":material/delete:"):
            if err is not None:
                ss.pop("rb_practice", None)
            else:
                try:
                    R.delete(row, rkey)
                except PB.StoreError:
                    st.error(L("Closing isn't available right now. Try again in a minute.", "الإغلاق مو متاح الحين. جرّب بعد دقيقة."),
                             icon=":material/cloud_off:")
                    return
            for k in ("rb_ans", "rb_step", "rb_mode", "rb_close_ok"):
                ss.pop(k, None)
            _draft_clear()
            ss["rb_flash"] = L("Robo portfolio closed", "تسكّرت المحفظة الآلية")
            st.rerun()


def dashboard(state, row, rkey, err):
    tick = sorted({t for p in state["plans"] for t in p["targets"] if t != R.BOT} | set(R.bench_funds()))
    has_bot = any(R.BOT in p["targets"] for p in state["plans"])
    feats = load_bot() if has_bot else {}
    px = R.prices(tick, "5y")
    rep = R.replay(state, px, bot=feats if has_bot else None, ext=RB.load_ext(feats) if has_bot and feats else None)
    bm = R.replay(state, px, bench=True)
    ui.html(dash_hero(state, rep, err))
    if not rep.get("pending") and len(rep["curve"]):
        cv_ = rep["curve"]
        ui.ai_note("Robo portfolio", f"value {cv_['value'].iloc[-1]:,.0f}, invested {cv_['invested'].iloc[-1]:,.0f}, "
                   f"time-weighted return {(cv_['twr'].iloc[-1] / cv_['twr'].iloc[0] - 1) * 100:+.2f}% since {cv_.index[0]:%Y-%m-%d}")
    if err is not None:
        st.warning(L("Saving isn't available right now: this robo portfolio lasts for this visit only.",
                     "الحفظ مو متاح الحين: هالمحفظة الآلية لهالزيارة فقط."), icon=":material/cloud_off:")
    if rep.get("missing"):
        st.info(L("Prices aren't available right now. Try again in a minute.", "الأسعار مو متاحة الحين. جرّب بعد دقيقة."), icon=":material/cloud_off:")
    if has_bot and not feats:
        st.info(L("The Opportunity Bot's prices aren't available right now: its slice shows as cash until they load. Try again in a minute.",
                  "أسعار بوت الفرص مو متاحة الحين: حصته تظهر كنقد لين تتحمّل. جرّب بعد دقيقة."), icon=":material/cloud_off:")
    bp = bot_plan(state, rep, feats) if has_bot else None
    names = [L(":material/space_dashboard: Overview", ":material/space_dashboard: نظرة عامة"),
             L(":material/donut_large: Allocation", ":material/donut_large: التوزيع")]
    if has_bot:
        names.append(L(":material/radar: Opportunity Bot", ":material/radar: بوت الفرص"))
    names += [L(":material/history: Activity", ":material/history: النشاط"), L(":material/tune: Plan & settings", ":material/tune: الخطة والإعدادات")]
    if rep["pending"]:                         # before the first close: the same tabs, with what there is so far
        tabs = st.tabs(names)
        with tabs[0]:
            if not rep.get("missing"):
                first, amt = _date(rep["start"]), _m(state["amount"])
                ui.html(f'<div class="rbpend">{T.icon("hourglass_top")}<div><b>{L("Your first investment is on its way", "أول استثمار في الطريق")}</b>'
                        f'<span>{L(f"{amt} goes in at the close of {first}, spread across your funds by their targets. Then the robo takes it from there.", f"{amt} تدخل مع إغلاق {first}، موزعة على صناديقك حسب نسبها. وبعدها المستشار الآلي يكمل الباقي.")}</span></div></div>')
            ui.html(next_html(state, rep))
            if bp:
                ui.html(bot_notice_html(bp))
        with tabs[1]:
            plan = state["plans"][-1]
            ui.html(allocation_html({"targets": plan["targets"], "stocks": plan.get("stocks", 0)}))
        k = 2
        if has_bot:
            with tabs[k]:
                bot_tab(state, rep, feats, bp)
            k += 1
        with tabs[k]:
            ui.html(PP.empty("history", L("Nothing yet", "ما فيه شي للحين"),
                             L("Everything the robo does shows here from the first close.", "كل اللي يسويه المستشار الآلي يظهر هنا من أول إغلاق.")))
        with tabs[k + 1]:
            plan_tab(state, row, rkey, err)
        return
    tabs = st.tabs(names)
    cur = rep["curve"]
    with tabs[0]:
        ui.html(next_html(state, rep))
        if bp:
            ui.html(bot_notice_html(bp))
        m = R.metrics(cur)
        val = rep["live"]["value"] if rep.get("live") else float(cur["value"].iloc[-1])
        bval = None if bm.get("pending") else (bm["live"]["value"] if bm.get("live") else float(bm["curve"]["value"].iloc[-1]))
        vs = val - bval if bval else None
        ui.html(PP.kpis([
            ("account_balance", L("Value", "القيمة"), _m(val, 2), f'{L("Invested", "المستثمر")} <b>{_m(cur["invested"].iloc[-1])}</b>', None, None),
            ("show_chart", L("Return", "العائد"), _p(m.get("ret"), 2, True), L("time-weighted, since the start", "موزون زمنياً، من البداية"), PP._k(m.get("ret")), None),
            ("compare_arrows", L("vs benchmark", "مقابل المؤشر"), "—" if vs is None else _m(vs, 0, True),
             L(f"same money in {_bench_txt(True)}", f"نفس المبالغ في {_bench_txt(True)}"), PP._k(vs), None),
            ("trending_down", L("Largest fall", "أكبر هبوط"), _p(m.get("mdd"), 1, True), f'{L("Volatility", "التذبذب")} <b>{_p(m.get("vol"), 1)}</b>',
             "neg" if (m.get("mdd") or 0) < 0 else None, None)], "c4"))
        ui.sec("monitoring", "Performance", "الأداء")
        if len(cur) >= 2:
            rng = st.segmented_control(L("Range", "المدة"), ["1m", "3m", "ytd", "1y", "all"], default="all", key="rb_rng", label_visibility="collapsed",
                                       format_func=lambda k: {"1m": L("1M", "شهر"), "3m": L("3M", "3 أشهر"), "ytd": L("YTD", "من بداية السنة"),
                                                              "1y": L("1Y", "سنة"), "all": L("All", "الكل")}[k]) or "all"
            ui.chart(lines_fig(rep, bm, L("Value, money invested and the benchmark", "القيمة والمبلغ المستثمر والمؤشر المرجعي"), rng), key="rb_perf")
            heat = heat_html(R.monthly_returns(cur))
            if heat:
                ui.sec("calendar_month", "Month by month", "شهر بشهر")
                ui.html(heat)
        else:
            ui.html(PP.empty("insights", L("The chart starts after the next close", "الرسم يبدأ بعد الإغلاق الجاي"),
                             L("The value is recorded at every close.", "القيمة تنسجل مع كل إغلاق.")))
    rows = R.holdings(rep)
    with tabs[1]:
        tot = sum(r["weight"] for r in rows if _fund(r["t"])["g"] in ("stocks", "bot"))
        a1, a2 = st.columns([1, 1.6])
        with a1:
            ui.html(donut_svg([(r["t"], r["weight"]) for r in rows], f"{tot:.0f}%", L("stocks now", "أسهم حالياً"),
                              inner=[(r["t"], r["target"]) for r in rows if r["target"] > 0])
                    + f'<div class="rbgl" style="justify-content:center;margin-top:6px"><span>{L("outer: now · inner: target", "الخارجية: الحالي · الداخلية: المستهدف")}</span></div>')
        with a2:
            ui.html(drift_html(rows))
        ui.sec("inventory_2", "Holdings", "المراكز")
        ui.html(holdings_html(rows))
    k = 2
    if has_bot:
        with tabs[k]:
            bot_tab(state, rep, feats, bp)
        k += 1
    with tabs[k]:
        ev = rep["events"]
        ui.html(timeline_html(ev, 12))
        if len(ev) > 12:
            with st.expander(L(f"All {len(ev)} actions", f"كل الإجراءات ({len(ev)})"), icon=":material/list:"):
                ui.html(timeline_html(ev))
    with tabs[k + 1]:
        plan_tab(state, row, rkey, err)


def plan_tab(state, row, rkey, err):
    plan = state["plans"][-1]
    ans = state.get("answers") or {}
    if ans:
        prof = R.profile(ans, level=plan.get("level"))
        prof["targets"] = plan["targets"]
        mon = state["monthly"][-1]["amount"] if state.get("monthly") else 0
        with st.expander(L("Your Investment Policy Statement", "بيان سياسة الاستثمار"), icon=":material/description:"):
            ui.html(ips_html(prof, ans, state["amount"], mon, plan["at"]))
            st.download_button(L("Download the IPS", "حمّل بيان السياسة"), ips_file(prof, ans, state["amount"], mon, plan["at"]).encode("utf-8"),
                               file_name="TURA-IPS.html", mime="text/html", icon=":material/download:", key="rb_ips_dl2")
    manage(state, row, rkey, err)
    from types import SimpleNamespace
    ui.sec("devices", "Yours only, on any device", "خاصة فيك، من أي جهاز")
    PP.code_box(SimpleNamespace(mode="mine", code=ss.get("pf_vid")), flash="rb_flash")
    ui.html(note())



# =====================================================================
# the page
# =====================================================================
def page_robo():
    ui.html(PP.CSS + CSS)
    code, key = PP.ident()
    rkey = R.key_for(PF.market_key(key, MK.current()))        # the Saudi robo: its own row (the US one keeps its key)
    if _sa():
        ui.html(f'<div class="rbnote">{T.icon("flag")}<span>{L("The Saudi market’s robo: its own portfolio in riyals, in the funds listed on Tadawul. Your US robo stays as it is.", "المستشار الآلي للسوق السعودي: محفظة مستقلة بالريال من الصناديق المتداولة في تداول. ومحفظتك الآلية الأمريكية تبقى مثل ما هي.")}</span></div>')
    err, state, row = None, None, None
    try:
        state, row = R.load(rkey)
    except PB.StoreError as e:            # the store can't be reached: this visit's own copy meanwhile (not saved)
        err = e
        state = ss.get("rb_practice")
    _draft_restore()
    _flash()
    ss["rb_has"] = bool(state)
    mode = ss.get("rb_mode")
    if mode == "quiz":
        quiz()
    elif mode == "plan":
        plan_page(state, row, rkey, err)
    elif state:
        dashboard(state, row, rkey, err)
    else:
        intro()
    _draft_keep()
    ui.foot()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "22.5.1"
