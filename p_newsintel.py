"""
p_newsintel.py - Discover → News Intelligence Engine: the news bot's headlines read by newsintel.py (event, sentiment,
materiality, impact, horizon, companies hit directly and indirectly, confidence, price reaction) and set against the price
(a setup score out of 100 with its parts). A command centre (the mood of the news on a dial, the window's numbers, the mood
through the window), a breaking strip, the companies in the news (each filters the page), the flow of the news as bubbles,
the sectors' mood, then a feed of cards (or a table). A story opens in a window: its four numbers in rings, the facts, the
setup score's parts, then its AI analysis, the affected stocks, why it matters, the expected impact, the technical
confirmation (with the price around the story) and a trading scenario.
"""
import json
import time

import pandas as pd
import requests
import streamlit as st

import data
import lightmode as LM
import markets as MK
import newsbot
import newsintel as NI
import newsiq
import tasi
import theme as T
import ui
import universe as U
from i18n import SECTOR_AR, L, is_ar

ss = st.session_state

CSS = """<style>
.nie-pipe { display:flex; flex-wrap:wrap; align-items:stretch; gap:6px; margin:4px 0 14px; }
.nie-pipe .st { flex:1 1 120px; min-width:110px; background:linear-gradient(180deg, rgba(40,28,70,.72), rgba(24,17,40,.78));
  border:1px solid rgba(157,151,165,.22); border-radius:12px; padding:9px 11px; }
.nie-pipe .st .ms { color:#A78BFA; font-size:1.1rem; }
.nie-pipe .st b { display:block; color:#fff; font-size:.8rem; margin-top:3px; }
.nie-pipe .st span.s { display:block; color:#9D97A5; font-size:.7rem; margin-top:2px; line-height:1.35; }
.nie-pipe .ar { align-self:center; color:#6D5BA8; font-size:1rem; }
.nie-lv { display:flex; flex-wrap:wrap; gap:8px; margin:0 0 16px; }
.nie-lv span { display:inline-flex; align-items:center; gap:6px; font-size:.74rem; font-weight:600; color:#DCD6F7; padding:4px 11px;
  border-radius:999px; border:1px solid rgba(167,139,250,.35); background:rgba(124,58,237,.12); }
.nie-lv span b { color:#A78BFA; }
.nie-card { display:flex; gap:14px; align-items:flex-start; background:linear-gradient(180deg, rgba(34,24,58,.86), rgba(20,14,34,.9));
  border:1px solid rgba(157,151,165,.25); border-radius:16px; padding:14px; margin:6px 0 12px; }
.nie-card .nth.big { flex:none; width:170px; height:112px; }
.nie-card .tx { min-width:0; flex:1; }
.nie-card .tt { font-size:1.08rem; font-weight:700; color:#fff; line-height:1.4; }
.nie-card .tt a { color:#fff; text-decoration:none; } .nie-card .tt a:hover { text-decoration:underline; }
.nie-card .mt { color:#9D97A5; font-size:.76rem; margin-top:4px; }
.nie-card .hd { display:flex; flex-wrap:wrap; gap:6px; margin-top:9px; }
.nie-tag { display:inline-flex; align-items:center; gap:5px; font-size:.78rem; font-weight:700; padding:4px 10px; border-radius:9px;
  border:1px solid; }
.nie-grid { display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:8px; margin:4px 0 12px; }
.nie-f { background:rgba(24,18,38,.82); border:1px solid rgba(157,151,165,.18); border-radius:12px; padding:9px 12px; }
.nie-f .l { color:#9D97A5; font-size:.68rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; }
.nie-f .v { color:#fff; font-size:.9rem; font-weight:600; margin-top:3px; line-height:1.4; }
.nie-score { background:rgba(12,9,20,.88); border:1px solid rgba(157,151,165,.22); border-radius:14px; padding:12px 16px; margin:4px 0 12px;
  font-family:'Roboto Mono', ui-monospace, monospace; direction:ltr; }
.nie-score .r { display:grid; grid-template-columns: 1fr auto; gap:12px; font-size:.86rem; color:#DDD8E6; padding:3px 0; }
.nie-score .r b.p { color:#4ADE80; } .nie-score .r b.n { color:#F87171; } .nie-score .r b.z { color:#9D97A5; }
.nie-score .t { border-top:1px dashed rgba(157,151,165,.35); margin-top:6px; padding-top:7px; font-weight:700; color:#fff; }
.nie-score .lab { margin-top:9px; font-family:'DM Sans','Readex Pro',sans-serif; font-size:1rem; font-weight:800; }
.nie-note { color:#9D97A5; font-size:.76rem; line-height:1.55; margin-top:8px; }
.nie-li { margin:0; padding-inline-start:18px; color:#DDD8E6; font-size:.88rem; line-height:1.7; }
@media (max-width: 700px) { .nie-card { flex-direction:column; } .nie-card .nth.big { width:100%; height:150px; }
  .nie-grid { grid-template-columns: minmax(0, 1fr); } }
/* ---------- the tabs: tiles, bars, chips, rows, a trade plan ---------- */
.nx-tiles { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:10px; margin:6px 0 12px; }
.nx-tile { position:relative; background:linear-gradient(180deg, rgba(36,26,60,.88), rgba(20,14,34,.92)); border:1px solid rgba(157,151,165,.2);
  border-radius:14px; padding:12px 14px; min-width:0; }
.nx-tile .l { display:flex; align-items:center; gap:6px; color:#A59FB0; font-size:.68rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase; }
.nx-tile .l .ms { font-size:1rem; color:#A78BFA; }
.nx-tile .v { color:#fff; font-size:1.25rem; font-weight:800; margin-top:6px; line-height:1.2; font-variant-numeric:tabular-nums; }
.nx-tile .v small { font-size:.75rem; color:#9D97A5; font-weight:600; }
.nx-tile .s { color:#9D97A5; font-size:.74rem; margin-top:4px; line-height:1.4; }
.nx-bar { height:6px; border-radius:6px; background:rgba(157,151,165,.18); margin-top:9px; overflow:hidden; }
.nx-bar i { display:block; height:100%; border-radius:6px; }
.nx-chips { display:flex; flex-wrap:wrap; gap:6px; margin:4px 0 10px; }
.nx-chip { display:inline-flex; align-items:center; gap:5px; padding:4px 11px; border-radius:999px; font-size:.78rem; font-weight:700; border:1px solid; }
.nx-chip.up { color:#4ADE80; border-color:rgba(74,222,128,.35); background:rgba(74,222,128,.08); }
.nx-chip.dn { color:#F87171; border-color:rgba(248,113,113,.35); background:rgba(248,113,113,.08); }
.nx-chip.nu { color:#C4B5FD; border-color:rgba(196,181,253,.35); background:rgba(124,58,237,.1); }
.nx-h { color:#DCD6F7; font-size:.8rem; font-weight:700; margin:12px 0 6px; display:flex; align-items:center; gap:6px; }
.nx-h .ms { color:#A78BFA; font-size:1rem; }
.nx-note { display:flex; gap:8px; align-items:flex-start; color:#9D97A5; font-size:.76rem; line-height:1.55; margin-top:10px; padding:9px 12px;
  border-radius:12px; background:rgba(124,58,237,.07); border:1px dashed rgba(167,139,250,.28); }
.nx-note .ms { color:#A78BFA; font-size:1rem; flex:none; }
.nx-list { display:flex; flex-direction:column; gap:8px; margin:6px 0; }
.nx-row { display:grid; grid-template-columns: auto minmax(0, 1.4fr) auto minmax(0, 1.2fr) auto; align-items:center; gap:12px;
  background:linear-gradient(180deg, rgba(34,24,56,.86), rgba(20,14,34,.9)); border:1px solid rgba(157,151,165,.18); border-radius:14px;
  padding:10px 14px; text-decoration:none !important; transition:border-color .15s, transform .15s; }
a.nx-row:hover { border-color:rgba(167,139,250,.5); transform:translateY(-1px); }
.nx-row .tk { color:#fff; font-weight:800; font-size:.92rem; }
.nx-row .nm { color:#9D97A5; font-size:.74rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.nx-row .sc { color:#CFC9DA; font-size:.78rem; line-height:1.35; min-width:0; }
.nx-row .sc span { display:block; color:#8F899B; font-size:.7rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.nx-badge { display:inline-flex; align-items:center; gap:4px; font-size:.68rem; font-weight:800; letter-spacing:.04em; padding:3px 9px;
  border-radius:999px; white-space:nowrap; }
.nx-badge.dir { color:#FDE68A; background:rgba(251,191,36,.12); border:1px solid rgba(251,191,36,.35); }
.nx-badge.ind { color:#C4B5FD; background:rgba(124,58,237,.12); border:1px solid rgba(167,139,250,.35); }
.nx-callout { display:flex; gap:14px; align-items:flex-start; padding:16px 18px; border-radius:16px; margin:6px 0;
  background:linear-gradient(135deg, rgba(124,58,237,.16), rgba(20,14,34,.9) 60%); border:1px solid rgba(167,139,250,.28);
  border-inline-start:4px solid #8B5CF6; }
.nx-callout .ms { font-size:1.6rem; color:#C4B5FD; flex:none; }
.nx-callout p { margin:0; color:#EDE9F5; font-size:.95rem; line-height:1.75; }
.nx-sec { display:grid; grid-template-columns: minmax(110px, 1.2fr) minmax(0, 1.8fr) 48px 92px 122px; align-items:center; gap:12px;
  padding:9px 14px; border-radius:12px; background:rgba(22,16,36,.86); border:1px solid rgba(157,151,165,.16); }
.nx-sec .n { color:#fff; font-weight:700; font-size:.84rem; }
.nx-sec > .pill, .nx-sec > .nx-ok { justify-self:stretch; text-align:center; }
.nx-row .tk, .nx-row .nm, .nx-row .sc span, .nx-sec .e { unicode-bidi:plaintext; }
.nx-sec .e { color:#8F899B; font-size:.72rem; font-weight:700; }
.nx-div { position:relative; height:8px; border-radius:8px; background:rgba(157,151,165,.16); direction:ltr; }
.nx-div::before { content:""; position:absolute; left:50%; top:-3px; bottom:-3px; width:1px; background:rgba(220,214,247,.45); }
.nx-div i { position:absolute; top:0; bottom:0; border-radius:8px; }
.nx-ok { font-size:.72rem; font-weight:800; padding:3px 9px; border-radius:999px; white-space:nowrap; }
.nx-ok.y { color:#4ADE80; background:rgba(74,222,128,.1); } .nx-ok.n { color:#F87171; background:rgba(248,113,113,.1); }
.nx-ok.z { color:#9D97A5; background:rgba(157,151,165,.1); }
.nx-plan { display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:10px; margin:6px 0 12px; }
.nx-lv { border-radius:14px; padding:12px 14px; border:1px solid; }
.nx-lv .l { font-size:.68rem; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }
.nx-lv .v { font-size:1.35rem; font-weight:800; margin-top:5px; font-variant-numeric:tabular-nums; direction:ltr; unicode-bidi:isolate; }
.nx-lv .s { font-size:.74rem; color:#B7B1C2; margin-top:4px; line-height:1.45; }
.nx-lv.go { border-color:rgba(96,165,250,.4); background:rgba(59,130,246,.09); } .nx-lv.go .l, .nx-lv.go .v { color:#93C5FD; }
.nx-lv.st { border-color:rgba(248,113,113,.4); background:rgba(239,68,68,.08); } .nx-lv.st .l, .nx-lv.st .v { color:#FCA5A5; }
.nx-lv.tg { border-color:rgba(74,222,128,.4); background:rgba(34,197,94,.08); } .nx-lv.tg .l, .nx-lv.tg .v { color:#86EFAC; }
/* ---- the trade map: stop and target at the two ends; the bar from the stop to the entry is the risk (red), from the entry to the
   target the reward (green); the entry is marked above the bar and the price now below it, so the two never sit on each other.
   Every part explains itself when the pointer is on it or when it is tapped. */
.nx-pm { position:relative; margin:4px 0 12px; padding:14px 16px 12px; border-radius:16px; border:1px solid rgba(196,181,253,.18);
  background:linear-gradient(180deg, rgba(34,24,58,.72), rgba(20,14,34,.82)); }
.nx-pm .hd { display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom:12px; }
.nx-pm .hd .t { display:flex; align-items:center; gap:8px; font-weight:800; font-size:.92rem; color:#fff; }
.nx-pm .hd .t .ms { font-size:19px; color:#C4B5FD; }
.nx-pm .rr { font-size:.74rem; font-weight:800; color:#C4B5FD; background:rgba(123,69,240,.16); border:1px solid rgba(167,139,250,.35);
  border-radius:999px; padding:4px 10px; white-space:nowrap; }
.nx-pm .rr b { color:#fff; direction:ltr; unicode-bidi:isolate; }
.nx-pm .ends { display:flex; justify-content:space-between; gap:12px; margin-bottom:6px; }
.nx-pm .cap { display:flex; flex-direction:column; gap:1px; padding:6px 10px; border-radius:11px; outline:none; cursor:help; position:relative;
  transition: background .15s, box-shadow .15s; }
.nx-pm .cap.st { align-items:flex-start; background:rgba(239,68,68,.09); }
.nx-pm .cap.tg { align-items:flex-end; background:rgba(34,197,94,.09); text-align:end; }
.nx-pm .cap small { font-size:.66rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; display:flex; align-items:center; gap:6px; }
.nx-pm .cap small i { width:9px; height:9px; border-radius:50%; display:inline-block; }
.nx-pm .cap.st small { color:#FCA5A5; } .nx-pm .cap.st small i { background:#F87171; box-shadow:0 0 0 3px rgba(248,113,113,.2); }
.nx-pm .cap.tg small { color:#86EFAC; } .nx-pm .cap.tg small i { background:#4ADE80; box-shadow:0 0 0 3px rgba(74,222,128,.2); }
.nx-pm .cap b { font-size:1.02rem; font-weight:800; color:#fff; direction:ltr; unicode-bidi:isolate; font-variant-numeric:tabular-nums; }
.nx-pm .band { position:relative; height:40px; }
.nx-pm .pin { position:absolute; inset-inline-start:var(--x); transform:translateX(-50%); display:flex; flex-direction:column; align-items:center;
  white-space:nowrap; outline:none; cursor:help; z-index:2; }
.nx-pm.rtl .pin { transform:translateX(50%); }
.nx-pm .pin .lb { font-size:.7rem; font-weight:800; padding:3px 9px; border-radius:999px; display:flex; gap:6px; align-items:center;
  transition: transform .15s, box-shadow .15s; }
.nx-pm .pin .lb b { direction:ltr; unicode-bidi:isolate; font-variant-numeric:tabular-nums; }
.nx-pm .pin.go .lb { color:#BFDBFE; background:rgba(59,130,246,.22); border:1px solid rgba(96,165,250,.5); }
.nx-pm .pin.now .lb { color:#fff; background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.3); }
.nx-pm .band.top .pin { bottom:0; } .nx-pm .band.bot .pin { top:0; }
.nx-pm .pin .cn { display:block; width:2px; height:9px; border-radius:2px; }
.nx-pm .pin.go .cn { background:#60A5FA; } .nx-pm .pin.now .cn { background:rgba(255,255,255,.7); }
.nx-pm .track { position:relative; height:28px; border-radius:10px; background:rgba(157,151,165,.12); direction:inherit; }
.nx-pm .seg { position:absolute; top:0; bottom:0; display:flex; align-items:center; justify-content:center; outline:none; cursor:help;
  font-size:.74rem; font-weight:800; white-space:nowrap; animation: nxgrow .8s cubic-bezier(.2,.8,.2,1) both; transition: filter .15s, box-shadow .15s; }
.nx-pm .seg.r { inset-inline-start:0; width:var(--w); color:#FFE4E6; border-start-start-radius:10px; border-end-start-radius:10px;
  background:linear-gradient(90deg, rgba(220,38,38,.85), rgba(248,113,113,.55)); transform-origin:right; }
.nx-pm .seg.g { inset-inline-end:0; width:var(--w); color:#DCFCE7; border-start-end-radius:10px; border-end-end-radius:10px;
  background:linear-gradient(90deg, rgba(74,222,128,.5), rgba(22,163,74,.9)); transform-origin:left; }
.nx-pm.rtl .seg.r { background:linear-gradient(270deg, rgba(220,38,38,.85), rgba(248,113,113,.55)); transform-origin:left; }
.nx-pm.rtl .seg.g { background:linear-gradient(270deg, rgba(74,222,128,.5), rgba(22,163,74,.9)); transform-origin:right; }
@keyframes nxgrow { from { transform:scaleX(0); opacity:.3; } to { transform:none; opacity:1; } }
.nx-pm .tick { position:absolute; top:-5px; bottom:-5px; width:3px; margin-inline-start:-1.5px; inset-inline-start:var(--x); border-radius:3px; z-index:2;
  pointer-events:none; }
.nx-pm .tick.go { background:#60A5FA; box-shadow:0 0 0 2px rgba(14,9,24,.9), 0 0 12px rgba(96,165,250,.8); }
.nx-pm .dot { position:absolute; top:50%; inset-inline-start:var(--x); width:14px; height:14px; margin-top:-7px; margin-inline-start:-7px; border-radius:50%;
  background:#fff; box-shadow:0 0 0 3px rgba(14,9,24,.9); z-index:3; pointer-events:none; }
.nx-pm .dot::after { content:""; position:absolute; inset:-3px; border-radius:50%; border:2px solid rgba(255,255,255,.7); animation: nxping 1.8s ease-out infinite; }
@keyframes nxping { from { transform:scale(.6); opacity:1; } to { transform:scale(2.2); opacity:0; } }
.nx-pm .ft { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
.nx-pm .ft span { font-size:.76rem; color:#CFCAD6; background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.08); border-radius:10px;
  padding:6px 10px; line-height:1.5; }
.nx-pm .ft b { direction:ltr; unicode-bidi:isolate; font-variant-numeric:tabular-nums; }
.nx-pm .ft .lo { color:#FCA5A5; } .nx-pm .ft .hi { color:#86EFAC; } .nx-pm .ft .bl { color:#93C5FD; }
/* the explanation of each part: on the pointer, or tapped (focus) on a phone */
.nx-pm [data-tip]::before { content:attr(data-tip); position:absolute; bottom:calc(100% + 8px); left:50%; width:max-content; max-width:240px;
  transform:translate(-50%, 4px); padding:8px 11px; border-radius:11px; background:#0E0918; border:1px solid rgba(167,139,250,.4); color:#E7E3EB;
  font-size:.74rem; font-weight:600; line-height:1.5; letter-spacing:0; text-transform:none; white-space:normal; text-align:center;
  box-shadow:0 12px 30px rgba(0,0,0,.5); opacity:0; pointer-events:none; transition: opacity .15s, transform .15s; z-index:20; }
.nx-pm .cap.st[data-tip]::before { left:auto; inset-inline-start:0; transform:translateY(4px); }
.nx-pm .cap.tg[data-tip]::before { left:auto; inset-inline-end:0; transform:translateY(4px); }
/* a pin's note leans away from the nearer edge: at the start it opens toward the end, at the end toward the start */
.nx-pm .pin[data-tip]::before { transform:translate(calc(-1 * var(--x)), 4px); }
.nx-pm.rtl .pin[data-tip]::before { transform:translate(calc(var(--x) - 100%), 4px); }
.nx-pm [data-tip]:is(:hover, :focus, :focus-within)::before { opacity:1; transform:translate(-50%, 0); }
.nx-pm .cap[data-tip]:is(:hover, :focus, :focus-within)::before { transform:none; }
.nx-pm .pin[data-tip]:is(:hover, :focus)::before { transform:translate(calc(-1 * var(--x)), 0); }
.nx-pm.rtl .pin[data-tip]:is(:hover, :focus)::before { transform:translate(calc(var(--x) - 100%), 0); }
.nx-pm .band.bot .pin[data-tip]::before { bottom:auto; top:calc(100% + 8px); }
.nx-pm .seg:is(:hover, :focus) { z-index:5; box-shadow: inset 0 0 0 2px rgba(255,255,255,.55), 0 0 18px rgba(255,255,255,.12); }
.nx-pm .pin:is(:hover, :focus), .nx-pm .cap:is(:hover, :focus) { z-index:6; }
/* the red part's note opens from its own edge, the green part's from its own: they never leave the box */
.nx-pm .seg.r[data-tip]::before { left:auto; inset-inline-start:0; transform:translateY(4px); }
.nx-pm .seg.g[data-tip]::before { left:auto; inset-inline-end:0; transform:translateY(4px); }
.nx-pm .seg[data-tip]:is(:hover, :focus)::before { transform:none; }
.nx-pm .pin:is(:hover, :focus) .lb { transform:translateY(-2px); box-shadow:0 6px 16px rgba(0,0,0,.4); }
.nx-pm .cap:is(:hover, :focus) { box-shadow: inset 0 0 0 1px rgba(255,255,255,.2); }
.nx-pm:has(.seg.r:is(:hover, :focus)) .cap.st, .nx-pm:has(.cap.st:is(:hover, :focus)) .seg.r { box-shadow: inset 0 0 0 2px rgba(248,113,113,.7); }
.nx-pm:has(.seg.g:is(:hover, :focus)) .cap.tg, .nx-pm:has(.cap.tg:is(:hover, :focus)) .seg.g { box-shadow: inset 0 0 0 2px rgba(74,222,128,.7); }
@media (prefers-reduced-motion: reduce) { .nx-pm .seg, .nx-pm .dot::after { animation:none; } }
@media (max-width: 700px) {
  .nx-row { grid-template-columns: auto minmax(0, 1fr) auto; } .nx-row .sc, .nx-row .nx-badge { display:none; }
  .nx-sec { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 86px; } .nx-sec .e, .nx-sec .nx-ok { display:none; }
  .nx-plan { grid-template-columns: minmax(0, 1fr); }
  .nx-tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); gap:8px; } .nx-tile { padding:10px 11px; } .nx-tile .v { font-size:1.05rem; } }
</style>"""

CSS2 = """<style>
.nx-relc { display:flex; flex-wrap:wrap; gap:6px; margin-top:2px; }
.nx-relc .tkc { font-size:.78rem; transition:transform .18s, box-shadow .18s; }
.nx-relc .tkc:hover { transform:translateY(-2px); box-shadow:0 8px 18px -10px rgba(121,184,244,.7); }
/* ---------- the command centre: the mood of the news, its numbers, its mood hour by hour ---------- */
.nie-hero { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.45fr) minmax(0,1.05fr); gap:12px; margin:2px 0 12px; }
.nie-hc { position:relative; overflow:hidden; border-radius:18px; padding:14px 16px 15px; border:1px solid rgba(157,151,165,.2); min-width:0;
  background:linear-gradient(160deg, rgba(42,29,74,.86), rgba(18,13,32,.93)); box-shadow:inset 0 1px 0 rgba(255,255,255,.05);
  animation:nieup .5s cubic-bezier(.2,.8,.2,1) both; }
.nie-hc:nth-child(2) { animation-delay:.06s; } .nie-hc:nth-child(3) { animation-delay:.12s; }
@keyframes nieup { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }
.nie-hc .h { display:flex; align-items:center; gap:7px; color:#A59FB0; font-size:.68rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
.nie-hc .h .ms { color:#A78BFA; font-size:1rem; }
.nie-hc .h .nie-live { margin-inline-start:auto; }
.nie-gauge { text-align:center; margin-top:6px; }
.nie-gauge svg { width:100%; max-width:240px; height:auto; display:block; margin:0 auto; }
.nie-gauge .ends { display:flex; justify-content:space-between; max-width:240px; margin:-4px auto 0; direction:ltr; font-size:.66rem; font-weight:800;
  letter-spacing:.05em; text-transform:uppercase; }
.nie-gauge .ends .b { color:#FCA5A5; } .nie-gauge .ends .u { color:#86EFAC; }
.nie-gauge .mv { font-size:1.7rem; font-weight:800; color:#fff; line-height:1; margin-top:4px; font-variant-numeric:tabular-nums; }
.nie-gauge .mv bdi { direction:ltr; }
.nie-gauge .ml { font-size:.9rem; font-weight:800; margin-top:5px; }
.nie-gauge .mb { color:#9D97A5; font-size:.72rem; margin-top:3px; line-height:1.45; }
.nie-mix { display:flex; height:8px; border-radius:8px; overflow:hidden; margin:12px 0 6px; background:rgba(157,151,165,.16); }
.nie-mix i { display:block; height:100%; }
.nie-mixl { display:flex; justify-content:space-between; gap:6px; font-size:.72rem; color:#B9B3C4; } .nie-mixl b { color:#fff; }
.nie-hc { display:flex; flex-direction:column; }
.nie-stats { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); grid-auto-rows:1fr; gap:8px; margin-top:10px; flex:1; }
.nie-st { border-radius:13px; padding:10px 12px; background:rgba(255,255,255,.035); border:1px solid rgba(157,151,165,.14); min-width:0; }
.nie-st .l { display:flex; align-items:center; gap:5px; color:#A59FB0; font-size:.66rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; }
.nie-st .l .ms { font-size:.95rem; color:#A78BFA; }
.nie-st .v { color:#fff; font-size:1.3rem; font-weight:800; margin-top:4px; line-height:1.15; font-variant-numeric:tabular-nums;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.nie-st .v.sm { font-size:1rem; }
.nie-st .s { color:#9D97A5; font-size:.7rem; margin-top:2px; }
.nie-st.hot { border-color:rgba(248,113,113,.3); background:rgba(239,68,68,.07); } .nie-st.hot .v { color:#FCA5A5; }
.nie-st.go { border-color:rgba(74,222,128,.28); background:rgba(34,197,94,.06); } .nie-st.go .v { color:#86EFAC; }
.nie-tl { display:flex; align-items:stretch; gap:3px; height:84px; min-height:84px; flex:1; margin:14px 0 5px; position:relative; direction:ltr; }
.nie-tl::before { content:""; position:absolute; left:0; right:0; top:50%; border-top:1px dashed rgba(157,151,165,.35); }
.nie-tl span { flex:1; position:relative; }
.nie-tl span i { position:absolute; left:16%; right:16%; border-radius:99px; animation:niebar .7s cubic-bezier(.2,.8,.2,1) both; transition:filter .2s, transform .2s; }
.nie-tl span:hover i { filter:brightness(1.25); }
.nie-tl span i.u { bottom:calc(50% + 1px); background:linear-gradient(0deg, rgba(74,222,128,.35), #4ADE80); transform-origin:bottom; box-shadow:0 0 10px -2px rgba(74,222,128,.55); }
.nie-tl span i.d { top:calc(50% + 1px); background:linear-gradient(180deg, rgba(248,113,113,.35), #F87171); transform-origin:top; box-shadow:0 0 10px -2px rgba(248,113,113,.55); }
.nie-tl span.e i { top:calc(50% - 1px); height:2px; background:rgba(157,151,165,.35); }
@keyframes niebar { from { transform:scaleY(0); } to { transform:none; } }
.nie-tll { display:flex; justify-content:space-between; color:#8F899B; font-size:.66rem; direction:ltr; }
.nie-live { display:inline-flex; align-items:center; gap:6px; font-size:.66rem; font-weight:800; color:#86EFAC; letter-spacing:.08em; }
.nie-live i { width:8px; height:8px; border-radius:50%; background:#4ADE80; animation:niepulse 1.8s infinite; }
@keyframes niepulse { 0% { box-shadow:0 0 0 0 rgba(74,222,128,.55); } 70% { box-shadow:0 0 0 9px rgba(74,222,128,0); } 100% { box-shadow:0 0 0 0 rgba(74,222,128,0); } }
.nie-upd { color:#9D97A5; font-size:.72rem; margin-top:8px; line-height:1.5; }
/* ---------- breaking: the stories that matter most, running across ---------- */
.nie-brk { position:relative; display:flex; align-items:center; overflow:hidden; border-radius:14px; border:1px solid rgba(248,113,113,.28);
  background:linear-gradient(90deg, rgba(239,68,68,.14), rgba(20,14,34,.92) 26%); margin:0 0 14px; min-height:42px; }
.nie-brk .lb { flex:none; display:inline-flex; align-items:center; gap:6px; align-self:stretch; padding:0 14px; font-weight:800; font-size:.7rem;
  letter-spacing:.1em; text-transform:uppercase; color:#FECACA; background:linear-gradient(90deg, rgba(220,38,38,.55), rgba(220,38,38,.15)); }
.nie-brk .lb .ms { font-size:1rem; animation:nieblink 1.6s ease-in-out infinite; }
@keyframes nieblink { 50% { opacity:.35; } }
.nie-brk .vw { flex:1; overflow:hidden; -webkit-mask-image:linear-gradient(90deg, transparent, #000 3%, #000 97%, transparent);
  mask-image:linear-gradient(90deg, transparent, #000 3%, #000 97%, transparent); direction:ltr; }
.nie-brk .tr { display:inline-flex; gap:34px; white-space:nowrap; padding:10px 0; animation:niemq 60s linear infinite; will-change:transform; }
.nie-brk:hover .tr { animation-play-state:paused; }
@keyframes niemq { from { transform:translateX(0); } to { transform:translateX(-50%); } }
.nie-brk .it { display:inline-flex; gap:8px; align-items:center; font-size:.82rem; color:#E9E5F0; }
.nie-brk .it b { font-weight:800; color:#fff; }
.nie-brk .it .ar { font-weight:900; } .nie-brk .it.bull .ar { color:#4ADE80; } .nie-brk .it.bear .ar { color:#F87171; } .nie-brk .it.neutral .ar { color:#C4B5FD; }
.nie-brk .it small { color:#8F899B; font-size:.72rem; }
.nie-brk .it .im { font-size:.66rem; font-weight:800; color:#FCA5A5; border:1px solid rgba(248,113,113,.4); border-radius:6px; padding:1px 5px; }
@media (prefers-reduced-motion: reduce) { .nie-brk .tr { animation:none; } }
/* ---------- the tickers in the news (each one filters the page) ---------- */
[class*="st-key-nie_tk_"], [class*="st-key-nie_c_"] { position:relative; gap:0 !important; }
[class*="st-key-nie_tk_"] [data-testid="stElementContainer"], [class*="st-key-nie_c_"] [data-testid="stElementContainer"] { position:static !important; margin:0 !important; }
[class*="st-key-nie_tk_"] .stButton, [class*="st-key-nie_c_"] .stButton { position:absolute !important; inset:0; z-index:4; margin:0 !important; }
[class*="st-key-nie_tk_"] .stButton > div, [class*="st-key-nie_tk_"] [data-testid="stTooltipHoverTarget"],
[class*="st-key-nie_c_"] .stButton > div, [class*="st-key-nie_c_"] [data-testid="stTooltipHoverTarget"] { width:100% !important; height:100% !important; }
[class*="st-key-nie_tk_"] .stButton button, [class*="st-key-nie_c_"] .stButton button { width:100% !important; height:100% !important; min-height:0 !important;
  padding:0 !important; opacity:0; cursor:pointer; border-radius:16px !important; }
.nie-tkc { display:flex; flex-direction:column; gap:6px; padding:11px 12px; border-radius:16px; border:1px solid rgba(157,151,165,.2); min-width:0;
  background:linear-gradient(160deg, rgba(38,27,64,.86), rgba(19,14,32,.92)); transition:transform .2s, border-color .2s, box-shadow .2s; }
[class*="st-key-nie_tk_"]:hover .nie-tkc { transform:translateY(-2px); border-color:rgba(167,139,250,.55); box-shadow:0 14px 28px -18px rgba(123,69,240,.8); }
.nie-tkc.on { border-color:#A78BFA; box-shadow:0 0 0 1px #A78BFA, 0 14px 28px -18px rgba(123,69,240,.9); background:linear-gradient(160deg, rgba(91,52,170,.5), rgba(24,17,40,.92)); }
.nie-tkc .t { display:flex; align-items:center; gap:8px; min-width:0; }
.nie-tkc .t b { color:#fff; font-weight:800; font-size:.92rem; }
.nie-tkc .t .ok { margin-inline-start:auto; color:#C4B5FD; } .nie-tkc .t .ok .ms { font-size:1.05rem; }
.nie-tkc .n { align-items:center; } .nie-tkc .n .pill { font-size:.72rem; padding:2px 7px; }
.nie-tkc .n { color:#A59FB0; font-size:.72rem; display:flex; justify-content:space-between; gap:6px; } .nie-tkc .n > span:first-child { white-space:nowrap; }
.nie-tkc .sb { position:relative; height:5px; border-radius:5px; background:rgba(157,151,165,.18); direction:ltr; }
.nie-tkc .sb::before { content:""; position:absolute; left:50%; top:-2px; bottom:-2px; width:1px; background:rgba(220,214,247,.45); }
.nie-tkc .sb i { position:absolute; top:0; bottom:0; border-radius:5px; }
.st-key-nie_tks [data-testid="stHorizontalBlock"] { gap:10px; }
@media (max-width: 640px) {
  .st-key-nie_tks [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; overflow-x:auto; padding-bottom:4px; scrollbar-width:none; }
  .st-key-nie_tks [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex:0 0 164px !important; min-width:164px !important; width:164px !important; } }
.nie-flt { display:inline-flex; align-items:center; gap:8px; font-size:.8rem; color:#E9E5F0; padding:5px 12px; border-radius:999px;
  border:1px solid rgba(167,139,250,.45); background:rgba(124,58,237,.16); }
.nie-flt .ms { color:#C4B5FD; font-size:1rem; }
/* ---------- the sectors in the news ---------- */
.nie-sp { display:flex; flex-direction:column; gap:7px; padding:12px 14px; border-radius:16px; border:1px solid rgba(157,151,165,.18);
  background:linear-gradient(180deg, rgba(34,24,56,.82), rgba(20,14,34,.9)); }
.nie-sp .r { display:grid; grid-template-columns:minmax(0,1.3fr) 30px minmax(0,1.5fr) 42px; align-items:center; gap:9px; font-size:.8rem; }
.nie-sp .r .nm { color:#E9E5F0; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.nie-sp .r .c { color:#A59FB0; font-size:.7rem; font-weight:800; text-align:center; background:rgba(157,151,165,.12); border-radius:7px; padding:1px 0; }
.nie-sp .r .v { font-weight:800; font-size:.76rem; text-align:end; direction:ltr; }
.nie-sp .r .v.u { color:#4ADE80; } .nie-sp .r .v.d { color:#F87171; } .nie-sp .r .v.z { color:#A59FB0; }
.nie-sp .bar { position:relative; height:8px; border-radius:8px; background:rgba(157,151,165,.14); direction:ltr; }
.nie-sp .bar::before { content:""; position:absolute; left:50%; top:-3px; bottom:-3px; width:1px; background:rgba(220,214,247,.45); }
.nie-sp .bar i { position:absolute; top:0; bottom:0; border-radius:8px; animation:niegrow .8s cubic-bezier(.2,.8,.2,1) both; }
@keyframes niegrow { from { clip-path:inset(0 50% 0 50%); } to { clip-path:inset(0 0 0 0); } }
.nie-sp .lg2 { display:flex; justify-content:space-between; color:#8F899B; font-size:.66rem; direction:ltr; margin-top:2px; }
/* ---------- the feed: the top story large, then a card for every story ---------- */
.nie-cd { position:relative; display:flex; gap:13px; padding:12px; border-radius:18px; min-width:0; height:100%; box-sizing:border-box;
  border:1px solid rgba(157,151,165,.2); background:linear-gradient(165deg, rgba(36,26,60,.88), rgba(18,13,31,.94));
  transition:transform .22s cubic-bezier(.2,.8,.2,1), border-color .22s, box-shadow .22s; animation:nieup .45s cubic-bezier(.2,.8,.2,1) both; }
[class*="st-key-nie_c_"]:hover .nie-cd { transform:translateY(-3px); border-color:rgba(167,139,250,.55); box-shadow:0 18px 34px -20px rgba(123,69,240,.85); }
.nie-cd::before { content:""; position:absolute; inset-inline-start:0; top:14px; bottom:14px; width:3px; border-radius:3px; background:#8B5CF6; }
.nie-cd.bull::before { background:#4ADE80; } .nie-cd.bear::before { background:#F87171; }
.nie-cd.hi { border-color:transparent; background:linear-gradient(165deg, rgba(36,26,60,.94), rgba(18,13,31,.96)) padding-box,
  linear-gradient(135deg, rgba(248,113,113,.75), rgba(167,139,250,.35) 45%, rgba(45,182,235,.55)) border-box; }
.nie-cd .pic { flex:none; width:118px; }
@media (min-width: 641px) { .nie-cd:not(.big) { min-height:170px; } }
.nie-cd .pic .nth { width:118px !important; height:84px !important; }
.nie-cd:not(.big) .pic .nth.fb .ms { font-size:34px; } .nie-cd:not(.big) .pic .nth.fb em { display:none; }
.nie-cd .bd { min-width:0; flex:1; display:flex; flex-direction:column; gap:6px; }
.nie-cd .top { display:flex; flex-wrap:wrap; align-items:center; gap:5px; }
.nie-cd .ev { display:inline-flex; align-items:center; gap:4px; font-size:.68rem; font-weight:800; color:#C4B5FD; padding:2px 8px; border-radius:7px;
  background:rgba(124,58,237,.14); border:1px solid rgba(167,139,250,.3); }
.nie-cd .ev .ms { font-size:.9rem; }
.nie-cd .tkr { display:inline-flex; align-items:center; gap:4px; font-size:.68rem; font-weight:800; color:#fff; padding:2px 7px; border-radius:7px;
  background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.1); }
.nie-cd .tkr .u { color:#4ADE80; } .nie-cd .tkr .d { color:#F87171; }
.nie-cd .nw { font-size:.62rem; font-weight:900; letter-spacing:.08em; color:#0E0918; background:#FCD34D; border-radius:6px; padding:2px 6px; }
.nie-cd .tt { color:#fff; font-weight:700; font-size:.94rem; line-height:1.42; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
.nie-cd .mt { color:#8F899B; font-size:.72rem; }
.nie-cd .ft { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-top:auto; padding-top:4px; }
.nie-cd .se { display:inline-flex; align-items:center; gap:4px; font-size:.74rem; font-weight:800; padding:3px 9px; border-radius:999px; }
.nie-cd .se.bull { color:#4ADE80; background:rgba(74,222,128,.1); } .nie-cd .se.bear { color:#F87171; background:rgba(248,113,113,.1); }
.nie-cd .se.neutral { color:#C4B5FD; background:rgba(124,58,237,.12); }
.nie-cd .im { display:inline-flex; align-items:center; gap:6px; font-size:.7rem; color:#A59FB0; }
.nie-cd .im .bar { width:64px; height:6px; border-radius:6px; background:rgba(157,151,165,.18); overflow:hidden; direction:ltr; }
.nie-cd .im .bar i { display:block; height:100%; border-radius:6px; }
.nie-cd .im b { color:#fff; font-size:.8rem; font-variant-numeric:tabular-nums; }
.nie-cd .su { display:inline-flex; align-items:center; gap:5px; font-size:.7rem; color:#A59FB0; margin-inline-start:auto; }
.nie-cd .su svg { width:30px; height:30px; display:block; }
.nie-cd .go { display:inline-flex; align-items:center; gap:3px; font-size:.72rem; font-weight:800; color:#C4B5FD; }
.nie-cd .go .ms { font-size:1rem; transition:transform .2s; }
[class*="st-key-nie_c_"]:hover .nie-cd .go .ms { transform:translateX(3px); }
.nie-cd.big { padding:16px; gap:18px; }
.nie-cd.big .pic { width:min(40%, 330px); }
.nie-cd.big .pic .nth { width:100% !important; height:100% !important; min-height:190px; }
.nie-cd.big .tt { font-size:1.22rem; -webkit-line-clamp:4; }
.nie-cd.big .sm { color:#B9B3C4; font-size:.84rem; line-height:1.6; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
.nie-cd.big .why { display:flex; gap:8px; align-items:flex-start; color:#DCD6F7; font-size:.8rem; line-height:1.55; padding:8px 11px; border-radius:12px;
  background:rgba(124,58,237,.1); border:1px solid rgba(167,139,250,.25); }
.nie-cd.big .why .ms { color:#C4B5FD; font-size:1.05rem; }
.nie-spot { display:inline-flex; align-items:center; gap:5px; font-size:.66rem; font-weight:900; letter-spacing:.1em; text-transform:uppercase;
  color:#FDE68A; }
.nie-spot .ms { font-size:.95rem; }
.nie-rings { display:flex; gap:12px; flex-wrap:wrap; }
.nie-rg { display:flex; align-items:center; gap:7px; }
.nie-rg svg { width:46px; height:46px; display:block; flex:none; }
.nie-rg span { display:flex; flex-direction:column; font-size:.66rem; font-weight:800; letter-spacing:.05em; text-transform:uppercase; color:#A59FB0; }
.nie-rg span b { color:#fff; font-size:.82rem; letter-spacing:0; text-transform:none; }
.nie-more { color:#9D97A5; font-size:.76rem; text-align:center; margin:4px 0 0; }
@media (max-width: 900px) { .nie-hero { grid-template-columns:minmax(0,1fr) minmax(0,1fr); } .nie-hero .nie-hc:nth-child(3) { grid-column:1 / -1; } }
@media (max-width: 640px) {
  .nie-hero { grid-template-columns:minmax(0,1fr); } .nie-hero .nie-hc:nth-child(3) { grid-column:auto; }
  .nie-cd { gap:10px; padding:11px; } .nie-cd:not(.big) .pic, .nie-cd:not(.big) .pic .nth { width:92px !important; } .nie-cd:not(.big) .pic .nth { height:72px !important; }
  .nie-cd .tt { font-size:.88rem; }
  .nie-cd.big { flex-direction:column; } .nie-cd.big .pic { width:100%; } .nie-cd.big .pic .nth { width:100% !important; height:170px !important; min-height:0; }
  .nie-cd.big .tt { font-size:1.06rem; } .nie-sp .r { grid-template-columns:minmax(0,1.2fr) 28px minmax(0,1.2fr) 40px; } }
/* ---------- the story's window ---------- */
.nie-vd { display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:8px; margin:4px 0 12px; }
.nie-vd .c { display:flex; flex-direction:column; align-items:center; gap:4px; padding:12px 8px 10px; border-radius:14px; text-align:center;
  background:rgba(24,18,38,.85); border:1px solid rgba(157,151,165,.18); }
.nie-vd .c svg { width:66px; height:66px; display:block; }
.nie-vd .c .l { color:#A59FB0; font-size:.66rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; }
.nie-vd .c .s { color:#DCD6F7; font-size:.72rem; }
.nie-sb { background:rgba(12,9,20,.6); border:1px solid rgba(157,151,165,.2); border-radius:14px; padding:12px 14px; margin:4px 0 12px; }
.nie-sb .r { display:grid; grid-template-columns:minmax(0,1.3fr) minmax(0,2fr) 44px; align-items:center; gap:12px; padding:4px 0; font-size:.82rem; color:#DDD8E6; }
.nie-sb .r small { color:#6F6A78; }
.nie-sb .bar { position:relative; height:9px; border-radius:9px; background:rgba(157,151,165,.14); direction:ltr; }
.nie-sb .bar::before { content:""; position:absolute; left:50%; top:-3px; bottom:-3px; width:1px; background:rgba(220,214,247,.45); }
.nie-sb .bar i { position:absolute; top:0; bottom:0; border-radius:9px; animation:niegrow .8s cubic-bezier(.2,.8,.2,1) both; }
.nie-sb .r b { text-align:end; direction:ltr; font-variant-numeric:tabular-nums; } .nie-sb .r b.p { color:#4ADE80; } .nie-sb .r b.n { color:#F87171; } .nie-sb .r b.z { color:#9D97A5; }
.nie-sb .t { display:flex; align-items:center; gap:12px; border-top:1px dashed rgba(157,151,165,.35); margin-top:8px; padding-top:10px; }
.nie-sb .t svg { width:54px; height:54px; flex:none; }
.nie-sb .t .x { display:flex; flex-direction:column; gap:2px; } .nie-sb .t .x small { color:#A59FB0; font-size:.68rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; }
.nie-sb .t .x b { font-size:.95rem; font-weight:800; }
@media (max-width: 640px) { .nie-vd { grid-template-columns:repeat(2, minmax(0,1fr)); } .nie-sb .r { grid-template-columns:minmax(0,1.2fr) minmax(0,1.3fr) 40px; } }
</style>"""

IMPACT_LEVELS = [(70, "High", "عالي"), (45, "Medium", "متوسط"), (0, "Low", "منخفض")]
_EV_ABBR = {"macro": "MAC", "market": "MKT", "earnings": "EPS", "guidance": "GUI", "mna": "M&A", "regulation": "REG", "lawsuit": "LAW",
            "management": "CEO", "contract": "WIN", "analyst": "RTG", "offering": "OFF", "payout": "DIV", "restructuring": "CUT", "competition": "VS",
            "product": "NEW", "distress": "RSK", "other": "CO"}


def impact_level(x):
    for lo, en, ar in IMPACT_LEVELS:
        if x >= lo:
            return L(en, ar)
    return L("Low", "منخفض")


def _ev_pic(ev):
    """A small picture for a story with no photo and no company: the kind of event on the site's colours (a data URL)."""
    col = {"macro": ("#3B82F6", "#7C3AED"), "market": ("#0EA5E9", "#6366F1")}.get(ev, ("#7C3AED", "#DB2777"))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="64"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
           f'<stop offset="0" stop-color="{col[0]}"/><stop offset="1" stop-color="{col[1]}"/></linearGradient></defs>'
           f'<rect width="96" height="64" rx="12" fill="url(#g)"/><text x="48" y="40" font-family="Arial" font-size="20" font-weight="700" '
           f'fill="#fff" text-anchor="middle">{_EV_ABBR.get(ev, "NEWS").replace("&", "&amp;")}</text></svg>')
    import base64
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def picture(a):
    """Every story has a picture: the outlet's photo, else a free photo of its topic (newspics), else the company's logo,
    else the kind of event."""
    img = str(a["n"].get("img") or "")
    if img.startswith("http"):
        return img
    try:
        import newspics
        tp = newspics.topic_photo(newspics.topic_of(a["n"]), a["n"].get("link") or a["n"].get("title"))
        if tp:
            return tp["u"]
    except Exception:
        pass
    if a["direct"]:
        return data.logo_url(a["direct"][0])
    return _ev_pic(a["event"])


def _ev_name(a, en, ar):
    """The kind of event, marked when it was read in the summary only (less certain)."""
    return L(en, ar) + (L(" · uncertain", " · غير مؤكد") if a.get("ev_unsure") else "")


def _sent_txt(lab):
    en, ar, _ = NI.SENT[lab]
    arrow = {"bull": "▲", "bear": "▼", "neutral": "●"}[lab]
    return f"{arrow} {L(en, ar)}"


# ---------------------------------------------------------------- the page's market (the Saudi market reads its own news on KSA)
def _bench():
    return "KSA" if MK.is_sa() else "SPY"


def _tk(sym):
    """How a company shows in a chip: its ticker (a Saudi company: its short name, as Saudi readers know it)."""
    if str(sym).endswith(".SR"):
        nm = tasi.name_of(sym, is_ar()) or sym
        return nm if len(nm) <= 22 else nm[:21] + "…"
    return sym


def _secn(sec):
    return L(sec, SECTOR_AR.get(sec) or tasi.sector_ar(sec))


def _subn(sym, sub):
    """A company's industry in the page's language (the Saudi industry groups have Arabic names)."""
    return tasi.industry_ar(sub) if sub and is_ar() and str(sym).endswith(".SR") else (sub or "")


def _money(x):
    return MK.money(x, dec=2)


def _stock_txt(a):
    if a["direct"]:
        return ", ".join(_tk(s_) for s_ in a["direct"][:3])
    return L("Saudi market (KSA)", "السوق السعودي (KSA)") if a.get("sa") else L("Market (SPY)", "السوق (SPY)")


def _ny_time(ts):
    """The time in the page's market (New York, or Riyadh on the Saudi page)."""
    try:
        t = pd.Timestamp(ts)
        t = t.tz_localize("UTC") if t.tzinfo is None else t
        return t.tz_convert(MK.tz()).strftime("%m/%d %H:%M")
    except Exception:
        return ""


def _translate(titles):
    """{english headline: arabic} (data.translate keeps every answer for all visitors; a headline it could not translate keeps
    its english and is tried again on the next view)."""
    try:
        out = data.translate(list(titles), "ar")
    except Exception:
        return {}
    return {a: b for a, b in zip(titles, out or []) if b}


# ---------------------------------------------------------------- the optional AI analysis (only when the site has a key)
def _ai_key():
    try:
        import ai_assistant as AI
        return AI.settings()
    except Exception:
        return "", ""


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _ai_analysis(payload, lang):
    """A language model explains one story from the engine's numbers (it never decides a trade). '' when it cannot."""
    key, model = _ai_key()
    if not key:
        return ""
    try:
        import ai_assistant as AI
        ins = ("You are the News Analyst of a market-research website. Explain in 5 short bullet points what this news means for the "
               "companies named, why, how long the effect may last and what would confirm or cancel it, using ONLY the facts given. "
               "No buy/sell instructions; it is education. Answer in " + ("Arabic (clear Gulf-friendly Arabic)." if lang == "ar" else "English."))
        r = requests.post(AI.API_URL, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                          json={"model": model, "instructions": ins, "input": payload, "max_output_tokens": 500, "store": False}, timeout=35)
        if r.status_code < 400:
            return AI.extract(r.json())
    except Exception:
        pass
    return ""


def _engine_summary(a):
    """The engine's own reading in a few lines (shown when there is no AI key, and as the base of the AI's input)."""
    n, ev = a["n"], a["event"]
    en_ev, ar_ev = NI.EVENT.get(ev, NI.EVENT["other"])[:2]
    sen, sar, _ = NI.SENT[a["lab"]]
    hz = NI.HORIZON[a["horizon"]]
    who = _stock_txt(a)
    fa = a["facts"] or {}
    lines = [(f"Event: {en_ev} · {who}", f"الحدث: {ar_ev} · {who}"),
             (f"Reading: {sen} ({a['sent']:+.2f}), impact {a['impact']:.0f}/100, materiality {a['materiality']:.1f}/10, confidence {a['confidence']}%",
              f"القراءة: {sar} ({a['sent']:+.2f})، الأثر {a['impact']:.0f}/100، الأهمية {a['materiality']:.1f}/10، الثقة {a['confidence']}%"),
             (f"Horizon: {hz[0]}", f"الأفق الزمني: {hz[1]}")]
    if fa.get("chg") is not None:
        rv = f", volume {fa['rvol']:.1f}× its average" if fa.get("rvol") else ""
        rvar = f"، والحجم {fa['rvol']:.1f}× متوسطه" if fa.get("rvol") else ""
        lines.append((f"Price today: {fa['chg']:+.2f}%{rv}", f"السعر اليوم: {fa['chg']:+.2f}%{rvar}"))
    if a["words"]:
        w = ", ".join(dict.fromkeys(x.lower() for x in a["words"][:6]))
        lines.append((f"Words that decided the sentiment: {w}", f"الكلمات اللي حددت الاتجاه: {w}"))
    return lines


# ---------------------------------------------------------------- page
def _pipeline(n_items, n_co, n_macro, n_setups):
    src = (("Saudi feeds, Arabic and English", "مصادر سعودية بالعربي والإنجليزي") if MK.is_sa() else ("35 feeds + Yahoo Finance", "35 مصدر + ياهو فاينانس"))
    steps = [("rss_feed", ("Sources", "المصادر"), src),
             ("filter_alt", ("Filter", "الفلترة"), ("duplicates merged, opinion pieces marked", "دمج المكرر وتمييز مقالات الرأي")),
             ("psychology", ("Understand", "الفهم"), (f"{n_items} stories: event, sentiment, materiality", f"{n_items} خبر: الحدث والاتجاه والأهمية")),
             ("hub", ("Link companies", "ربط الشركات"), (f"{n_co} with companies, direct and indirect", f"{n_co} مع شركات، مباشرة وغير مباشرة")),
             ("speed", ("Impact", "تقييم الأثر"), (f"impact 0-100, {n_macro} macro stories by sector", f"أثر 0-100، و{n_macro} خبر اقتصادي حسب القطاع")),
             ("insights", ("Setup", "الفرصة"), (f"{n_setups} setups: news + momentum + volume + trend + market",
                                                  f"{n_setups} فرصة: الخبر + الزخم + الحجم + الاتجاه + السوق"))]
    out = []
    for i, (ic, (en, ar), (sen, sar)) in enumerate(steps):
        if i:
            out.append(f'<span class="ar">{"←" if is_ar() else "→"}</span>')
        out.append(f'<div class="st">{T.icon(ic)}<b>{T.esc(L(en, ar))}</b><span class="s">{T.esc(L(sen, sar))}</span></div>')
    lv = [("Level 1", "المستوى 1", "News Scanner", "ماسح الأخبار"), ("Level 2", "المستوى 2", "News Analyst", "محلل الأخبار"),
          ("Level 3", "المستوى 3", "Trading Setup", "محرك الفرص")]
    lvh = "".join(f'<span><b>{T.esc(L(a, b))}</b>{T.esc(L(c, d))} ✓</span>' for a, b, c, d in lv)
    return f'<div class="nie-pipe">{"".join(out)}</div><div class="nie-lv">{lvh}</div>'


def _bar(frac, color):
    return f'<div class="nx-bar"><i style="width:{max(0, min(1, frac)) * 100:.0f}%;background:{color}"></i></div>'


def _tile(ic, label, value, sub="", bar=None):
    return (f'<div class="nx-tile"><div class="l">{T.icon(ic)}{T.esc(label)}</div><div class="v">{value}</div>'
            + (f'<div class="s">{sub}</div>' if sub else "") + (bar or "") + "</div>")


def _note(text, ic="info"):
    return f'<div class="nx-note">{T.icon(ic)}<span>{T.esc(text)}</span></div>'


def _heat(x):
    """A colour from red (0) through amber to green (1)."""
    return "#F87171" if x < .34 else "#FBBF24" if x < .67 else "#4ADE80"


def _imp_col(v):
    """An impact's colour: how hot the story is (violet, amber, rose), never its direction."""
    return "#FB7185" if v >= 70 else "#FBBF24" if v >= 45 else "#A78BFA"


def _fact(label, value):
    return f'<div class="nie-f"><div class="l">{T.esc(label)}</div><div class="v">{value}</div></div>'


def _ring(v, mx, col, size=40, sw=5, text=None):
    """A value in a ring that fills with it (v out of mx)."""
    r = size / 2 - sw / 2 - 1
    f = max(0.0, min(1.0, (v or 0) / mx)) if mx else 0
    t = text if text is not None else f"{v:.0f}"
    return (f'<svg viewBox="0 0 {size} {size}" role="img" aria-label="{t}"><circle cx="{size / 2}" cy="{size / 2}" r="{r:.1f}" fill="{col}" fill-opacity=".07" '
            f'stroke="rgba(157,151,165,.2)" stroke-width="{sw}"/><circle cx="{size / 2}" cy="{size / 2}" r="{r:.1f}" fill="none" stroke="{col}" '
            f'stroke-width="{sw}" pathLength="100" stroke-dasharray="0 100" stroke-linecap="round" transform="rotate(-90 {size / 2} {size / 2})">'
            f'<animate attributeName="stroke-dasharray" from="0 100" to="{f * 100:.1f} 100" dur=".9s" fill="freeze" calcMode="spline" '
            f'keyTimes="0;1" keySplines=".2 .8 .2 1"/></circle><text x="{size / 2}" y="{size / 2 + size * .11:.1f}" text-anchor="middle" '
            f'font-size="{size * (.3 if len(str(t)) <= 2 else .26 if len(str(t)) == 3 else .22):.1f}" font-weight="800" fill="#FFFFFF">{t}</text></svg>')


def _setup_col(s):
    return "#4ADE80" if s["dir"] > 0 and s["total"] >= 40 else "#F87171" if s["dir"] < 0 and s["total"] >= 40 else "#C4B5FD"


def _score_block(a):
    """The setup score: each part as a bar from the middle (helps right, hurts left), then the total in a ring."""
    s = a["setup"]
    rows = []
    for k, en, ar, mx in NI.PARTS:
        v = s["parts"][k]
        cls = "p" if v > 0.5 else "n" if v < -0.5 else "z"
        w = min(abs(v) / mx, 1) * 50 if mx else 0
        bar = (f'<i style="left:50%;width:{w:.1f}%;background:linear-gradient(90deg,#22C55E88,#4ADE80)"></i>' if v > 0.5 else
               f'<i style="left:{50 - w:.1f}%;width:{w:.1f}%;background:linear-gradient(90deg,#F87171,#EF444488)"></i>' if v < -0.5 else "")
        rows.append(f'<div class="r"><span>{T.esc(L(en, ar))} <small>/{mx}</small></span><div class="bar">{bar}</div><b class="{cls}">{v:+.0f}</b></div>')
    col = _setup_col(s)
    return (f'<div class="nie-sb">{"".join(rows)}<div class="t">{_ring(s["total"], 100, col, 54, 6)}<div class="x">'
            f'<small>{T.esc(L("Total Score", "المجموع"))} · {s["total"]}/100</small><b style="color:{col}">{T.esc(L(*s["label"]))}</b></div></div></div>')


def _setup_short(s):
    """The setup in two or three words."""
    if not s["dir"]:
        return L("no direction", "بلا اتجاه")
    side = L("bullish", "صاعدة") if s["dir"] > 0 else L("bearish", "هابطة")
    t = s["total"]
    if t >= 75:
        return L(f"strong {side}", f"{side} قوية")
    if t >= 55:
        return L(f"moderate {side}", f"{side} متوسطة")
    if t >= 40:
        return L(f"weak {side}", f"{side} ضعيفة")
    return L("price doesn't confirm", "السعر ما يؤكد")


def _mat_word(m):
    return L("material", "مهم فعلاً") if m >= 6 else L("worth watching", "يستحق المتابعة") if m >= 4 else L("mostly noise", "غالباً ضوضاء")


def _verdict(a):
    """The four numbers of a story, each in a ring."""
    s = a["setup"]
    imp, conf, mat = a["impact"], a["confidence"], a["materiality"]
    cells = [(_ring(imp, 100, _imp_col(imp), 66, 7), L("Impact", "الأثر"), impact_level(imp)),
             (_ring(s["total"], 100, _setup_col(s), 66, 7), L("Setup", "الفرصة"), _setup_short(s)),
             (_ring(conf, 100, _heat((conf - 20) / 75), 66, 7, f"{conf}%"), L("Confidence", "الثقة"),
              L("source, coverage, price", "المصدر والتغطية والسعر")),
             (_ring(mat, 10, _heat(mat / 10), 66, 7, f"{mat:.1f}"), L("Materiality", "الأهمية"), _mat_word(mat))]
    return '<div class="nie-vd" data-nogq>' + "".join(
        f'<div class="c">{r}<span class="l">{T.esc(l_)}</span><span class="s">{T.esc(s_)}</span></div>' for r, l_, s_ in cells) + "</div>"


def _detail(a, chg, sec_chg, titles_ar, dfm=None):
    n = a["n"]
    ar = is_ar()
    title = (titles_ar.get(n["title"]) if ar and titles_ar else None) or n["title"]
    en_ev, ar_ev, ic, hz = NI.EVENT.get(a["event"], NI.EVENT["other"])
    sen, sar, scol = NI.SENT[a["lab"]]
    who = _tk(a["direct"][0]) if a["direct"] else _bench()
    imp_word = {"bull": ("Positive Impact", "أثر إيجابي"), "bear": ("Negative Impact", "أثر سلبي"), "neutral": ("Neutral Impact", "أثر محايد")}[a["lab"]]
    tags = (f'<span class="nie-tag" style="color:{scol};border-color:{scol}55;background:{scol}14">{T.esc(who)} — {T.esc(L(*imp_word))}</span>'
            f'<span class="nie-tag" style="color:#C4B5FD;border-color:#C4B5FD44;background:#7C3AED14">{T.icon(ic)}{T.esc(_ev_name(a, en_ev, ar_ev))}</span>')
    also = T.also_badge(n.get("also"), ar)
    ui.html(f'<div class="nie-card">{T.news_thumb(n, big=True)}<div class="tx"><div class="tt"><a href="{T.esc(n.get("link") or "#")}" '
            f'target="_blank">{T.esc(title)}</a></div><div class="mt"><bdi>{T.esc(n.get("source") or "")}</bdi>{also} · '
            f'{T.time_ago(n["time"], ar) if pd.notna(n.get("time")) else ""}</div><div class="hd">{tags}</div></div></div>')
    if n.get("more"):                                    # the same event told by other outlets
        ui.html(T.coverage(n, ar))
    ui.html(_verdict(a))
    ui.ai_note("Story", n.get("title") or "")
    ui.ai_note("Engine reading", f"{NI.EVENT.get(a['event'], NI.EVENT['other'])[0]}{' (uncertain)' if a.get('ev_unsure') else ''}, "
               f"{NI.SENT[a['lab']][0]}, impact {a['impact']:.0f}/100, setup {a['setup']['total']}/100, confidence {a['confidence']}%")
    # the facts, as in a research note
    main_ = a["direct"][0] if a["direct"] else ""
    secs = " / ".join(dict.fromkeys(x for sec, sub in a["sectors"] for x in (_secn(sec), _subn(main_, sub)) if x))
    if not secs and a["macro"]:                    # macro news: the sectors it usually helps and hurts most
        eff = a["macro"][3]
        nm = _secn
        up = [nm(k) for k, e in sorted(eff.items(), key=lambda x: -x[1]) if e >= 1][:3]
        dn = [nm(k) for k, e in sorted(eff.items(), key=lambda x: x[1]) if e <= -1][:2]
        secs = " · ".join(([L("Helped: ", "يستفيد: ") + "، ".join(up) if is_ar() else "Helped: " + ", ".join(up)] if up else [])
                          + ([L("Hurt: ", "يتضرر: ") + "، ".join(dn) if is_ar() else "Hurt: " + ", ".join(dn)] if dn else []))
    secs = secs or L("The whole market", "السوق كله")
    if a["indirect"]:                              # related companies: each a chip (logo, today's move) that opens its page
        rel = '<div class="nx-relc">' + "".join(T.ticker_chip(s_, (chg.get(s_) or (None, None))[1], None, ui.href(s_)) for s_ in a["indirect"][:6]) + "</div>"
    else:
        rel = T.esc(L("None found for this company", "ما لقينا شركات مرتبطة"))
    fa = a["facts"] or {}
    if a["moved_before"] is None:
        mb = L("Not known (no prices before it)", "غير معروف (ما فيه أسعار قبله)")
    elif a["moved_before"]:
        mb = L(f"Yes: {fa['pre']:+.1f}% in the 3 sessions before (more than 1.5× a normal move)",
               f"نعم: {fa['pre']:+.1f}% في الـ 3 جلسات قبله (أكثر من 1.5 ضعف الحركة العادية)")
    else:
        mb = L(f"No: {fa['pre']:+.1f}% in the 3 sessions before", f"لا: {fa['pre']:+.1f}% في الـ 3 جلسات قبله")
    age = a["age_h"]
    if age is None:
        new = "—"
    elif a["new"]:
        new = L(f"Yes, first seen {age * 60:.0f} min ago" if age < 1 else f"Yes, first seen {age:.1f} h ago",
                f"نعم، أول ظهور قبل {age * 60:.0f} دقيقة" if age < 1 else f"نعم، أول ظهور قبل {age:.1f} ساعة")
    else:
        new = L(f"No, reported {age:.0f} h ago" if age < 48 else f"No, reported {age / 24:.0f} days ago",
                f"لا، نُشر قبل {age:.0f} ساعة" if age < 48 else f"لا، نُشر قبل {age / 24:.0f} يوم")
    why_en, why_ar = NI.why(a)
    reason = L(why_en, why_ar).split(". ")[1] if ". " in L(why_en, why_ar) else L(why_en, why_ar)
    hzt = NI.HORIZON[hz]
    cells = [_fact(L("Event type", "نوع الخبر"), T.esc(_ev_name(a, en_ev, ar_ev))),
             _fact(L("Expected impact", "التأثير المتوقع"), f'<span style="color:{scol}">{T.esc(L(sen, sar))}</span>'),
             _fact(L("Time horizon", "الأفق الزمني"), T.esc(L(*hzt))),
             _fact(L("Sectors affected", "القطاعات المتأثرة"), T.esc(secs)),
             _fact(L("Related companies", "شركات مرتبطة"), rel),
             _fact(L("Reason", "السبب"), T.esc(reason)),
             _fact(L("Is the news new?", "هل الخبر جديد؟"), T.esc(new)),
             _fact(L("Did the price move before the news?", "هل تحرك السعر قبل الخبر؟"), T.esc(mb)),
             _fact(L("Market regime", "حالة السوق"), T.esc(L(*NI.REGIME[a["regime"]])))]
    ui.html(f'<div class="nie-grid">{"".join(cells)}</div>')
    ui.html(_score_block(a))
    tabs = st.tabs([L(":material/auto_awesome: AI analysis", ":material/auto_awesome: التحليل الذكي"),
                    L(":material/hub: Stocks", ":material/hub: الأسهم المتأثرة"), L(":material/lightbulb: Why it matters", ":material/lightbulb: ليش يهم"),
                    L(":material/public: Market impact", ":material/public: الأثر على السوق"),
                    L(":material/candlestick_chart: Technical", ":material/candlestick_chart: التأكيد الفني"),
                    L(":material/route: Scenario", ":material/route: سيناريو التداول")])
    with tabs[0]:
        _tab_ai(a, n, ar)
    with tabs[1]:
        _tab_stocks(a, chg)
    with tabs[2]:
        ui.html(f'<div class="nx-callout">{T.icon("lightbulb")}<p>{T.esc(L(why_en, why_ar))}</p></div>')
        if a["words"]:
            ui.html(f'<div class="nx-h">{T.icon("key")}{T.esc(L("What in the headline decided it", "وش في العنوان حدد الاتجاه"))}</div>' + _word_chips(a))
    with tabs[3]:
        _tab_impact(a, sec_chg)
    with tabs[4]:
        _tab_tech(a, dfm)
    with tabs[5]:
        _tab_plan(a)


def _word_chips(a):
    return '<div class="nx-chips">' + "".join(
        f'<span class="nx-chip {"up" if NI.word_sign(w) > 0 else "dn"}">{"▲" if NI.word_sign(w) > 0 else "▼"} {T.esc(w.lower())}</span>'
        for w in dict.fromkeys(a["words"][:8])) + "</div>"


def _tab_ai(a, n, ar):
    lines = _engine_summary(a)
    key, _m = _ai_key()
    if key:
        payload = json.dumps({"headline": n["title"], "summary": (n.get("summary") or "")[:600], "source": n.get("source"),
                              "engine": [ln[0] for ln in lines], "companies_direct": a["direct"], "companies_indirect": a["indirect"],
                              "setup": {"score": a["setup"]["total"], "label": a["setup"]["label"][0], "parts": a["setup"]["parts"]}})
        k_ = "nie_ai_" + str(abs(hash(n.get("link") or n["title"])))
        if st.button(L("Analyse this story with AI", "حلّل هالخبر بالذكاء الاصطناعي"), icon=":material/auto_awesome:", key=k_):
            ss[k_ + "_on"] = True
        if ss.get(k_ + "_on"):
            with st.spinner(L("The AI analyst is reading the story...", "محلل الذكاء الاصطناعي يقرأ الخبر...")):
                txt = _ai_analysis(payload, "ar" if ar else "en")
            if txt:
                ui.html(f'<div class="nx-callout">{T.icon("auto_awesome")}<p>{T.esc(txt).replace(chr(10), "<br>")}</p></div>')
            else:
                st.caption(L("The AI could not answer this time; the engine's reading is below.", "الذكاء الاصطناعي ما رد هالمرة، وقراءة المحرك تحت."))
    en_ev, ar_ev, ic, hz = NI.EVENT.get(a["event"], NI.EVENT["other"])
    sen, sar, scol = NI.SENT[a["lab"]]
    fa = a["facts"] or {}
    who = _stock_txt(a)
    imp, mat, conf = a["impact"], a["materiality"], a["confidence"]
    tiles = [
        _tile(ic, L("Event", "الحدث"), T.esc(_ev_name(a, en_ev, ar_ev)), T.esc(who)),
        _tile("balance", L("Reading", "القراءة"), f'<span style="color:{scol}">{T.esc(L(sen, sar))}</span> <small>{a["sent"]:+.2f}</small>',
              T.esc(L("from the words and the price", "من الكلمات والسعر"))),
        _tile("schedule", L("Horizon", "الأفق"), T.esc(L(*NI.HORIZON[hz])), T.esc(L("how long it may last", "كم ممكن يدوم"))),
    ]
    if fa.get("chg") is not None:
        rv = fa.get("rvol")
        tiles.append(_tile("show_chart", L("Price today", "السعر اليوم"), T.pill(fa["chg"]),
                           T.esc(L(f"volume {rv:.1f}× its average", f"الحجم {rv:.1f}× متوسطه")) if rv else "",
                           _bar(min(rv / 3, 1), "#60A5FA") if rv else None))
    ui.html(f'<div class="nx-tiles">{"".join(tiles)}</div>')
    if a["words"]:
        ui.html(f'<div class="nx-h">{T.icon("key")}{T.esc(L("Words that decided the sentiment", "الكلمات اللي حددت الاتجاه"))}</div>' + _word_chips(a))
    if not key:
        ui.html(_note(L("This is the engine’s own reading: the kind of event, the words and today’s price, scored by fixed rules.",
                        "هذي قراءة المحرك نفسه: نوع الحدث والكلمات وسعر اليوم، بقواعد ثابتة."), "auto_awesome"))


def _tab_stocks(a, chg):
    rows = []
    for kind, cls, syms in ((L("Direct", "مباشر"), "dir", a["direct"]), (L("Indirect", "غير مباشر"), "ind", a["indirect"])):
        for sym in syms:
            name, sec, sub = NI.company(sym, is_ar())
            if name == sym and not str(sym).endswith(".SR"):      # a company outside the site's lists: its saved summary
                inf_ = data.saved_info(sym) or {}
                name, sec, sub = inf_.get("shortName") or inf_.get("longName") or sym, sec or inf_.get("sector") or "", sub or inf_.get("industry") or ""
            c = chg.get(sym)
            secn = _secn(sec) if sec else ""
            rows.append(f'<a class="nx-row" href="stock?symbol={T.esc(sym)}" target="_self">{T.logo_obj(sym, 36)}'
                        f'<div style="min-width:0"><div class="tk" dir="auto">{T.esc(T.sym_label(sym))}</div><div class="nm" dir="auto">{T.esc(T.name_line(sym, name))}</div></div>'
                        f'<span class="nx-badge {cls}">{T.esc(kind)}</span>'
                        f'<div class="sc">{T.esc(secn)}<span>{T.esc(_subn(sym, sub))}</span></div>{T.pill(c[1] if c else None)}</a>')
    if rows:
        ui.html(f'<div class="nx-list">{"".join(rows)}</div>')
        ui.html(_note(L("Direct: named in the story. Indirect: suppliers, customers and closest rivals the site knows, then the largest "
                        "companies of the same industry. Open one for its full research page.",
                        "مباشر: مذكور في الخبر. غير مباشر: الموردين والعملاء وأقرب المنافسين اللي يعرفهم الموقع، وبعدهم أكبر شركات نفس "
                        "الصناعة. اضغط على أي سهم عشان تفتح صفحة أبحاثه."), "hub"))
    else:
        ui.html(_note(L("No single company: this story moves the market as a whole (see the expected impact by sector).",
                        "ما فيه شركة محددة: هالخبر يحرك السوق كله (شف الأثر المتوقع حسب القطاع)."), "public"))


def _tab_impact(a, sec_chg):
    sen, sar, scol = NI.SENT[a["lab"]]
    hz = NI.HORIZON[a["horizon"]]
    cls = {"bull": "up", "bear": "dn", "neutral": "nu"}[a["lab"]]
    ui.html('<div class="nx-chips">'
            f'<span class="nx-chip {cls}">{T.esc(L(sen, sar))}</span>'
            f'<span class="nx-chip nu">{T.icon("schedule")}{T.esc(L(*hz))}</span>'
            f'<span class="nx-chip nu">{T.esc(L("Severity", "الشدة"))} {a["severity"]}/10</span>'
            f'<span class="nx-chip nu">{T.esc(L("Confidence", "الثقة"))} {a["confidence"]}%</span></div>')
    if a["macro"]:
        key_, en_m, ar_m, eff = a["macro"]
        ui.html(f'<div class="nx-h">{T.icon("public")}{T.esc(L(f"{en_m}: how each sector usually takes it, and how it moved today", f"{ar_m}: كيف يتأثر كل قطاع عادةً، وكيف تحرك اليوم"))}</div>')
        etf_of = {} if a.get("sa") else {v: k for k, v in U.SECTOR_ETFS.items()}
        rows = []
        for sec, e in sorted(eff.items(), key=lambda x: -x[1]):
            etf = etf_of.get(sec)
            c = sec_chg.get(sec) if a.get("sa") else sec_chg.get(etf) if etf else None
            w = abs(e) / 2 * 50
            bar = (f'<i style="left:50%;width:{w:.0f}%;background:linear-gradient(90deg,#22C55E88,#4ADE80)"></i>' if e > 0 else
                   f'<i style="left:{50 - w:.0f}%;width:{w:.0f}%;background:linear-gradient(90deg,#F87171,#EF444488)"></i>' if e < 0 else "")
            if not c or e == 0:
                ok_ = '<span class="nx-ok z">—</span>'
            elif (c[1] > 0) == (e > 0):
                ok_ = f'<span class="nx-ok y">✓ {T.esc(L("as usual", "مثل العادة"))}</span>'
            else:
                ok_ = f'<span class="nx-ok n">✗ {T.esc(L("not today", "مو اليوم"))}</span>'
            rows.append(f'<div class="nx-sec"><span class="n">{T.esc(_secn(sec))}</span><div class="nx-div">{bar}</div>'
                        f'<span class="e">{T.esc(etf or "")}</span>{T.pill(c[1] if c else None)}{ok_}</div>')
        ui.html(f'<div class="nx-list">{"".join(rows)}</div>')
        if a.get("sa"):
            ui.html(_note(L("The bar is a rule of thumb of how the Saudi sector usually reacts (left hurt, right helped); the change is the "
                            "average move of its companies today.",
                            "الشريط قاعدة عامة لتفاعل القطاع السعودي عادةً (يسار يتضرر، يمين يستفيد)، والنسبة متوسط حركة شركاته اليوم."), "info"))
        else:
            ui.html(_note(L("The bar is a rule of thumb of how the sector usually reacts (left hurt, right helped); the change is its sector fund today.",
                            "الشريط قاعدة عامة لتفاعل القطاع عادةً (يسار يتضرر، يمين يستفيد)، والنسبة حركة صندوق القطاع اليوم."), "info"))
    elif a["direct"]:
        ui.html(_note(L("The story's weight on the stock is its impact score; the related companies usually move less, in the same direction.",
                        "وزن الخبر على السهم هو درجة الأثر، والشركات المرتبطة غالباً تتحرك أقل وبنفس الاتجاه."), "info"))


def _price_fig(df, when, sym, d):
    """The last four months of the stock with the day of the story marked: did the price react?"""
    import plotly.graph_objects as go
    c = df["Close"].dropna().iloc[-85:]
    if len(c) < 5:
        return None
    try:
        t = pd.Timestamp(when)
        t = (t.tz_localize("UTC") if t.tzinfo is None else t).tz_convert(MK.tz()).tz_localize(None).normalize()
    except Exception:
        t = c.index[-1]
    idx = c.index.tz_localize(None) if getattr(c.index, "tz", None) is not None else c.index
    pos = min(int(idx.searchsorted(t)), len(c) - 1)
    col = "#4ADE80" if d > 0 else "#F87171" if d < 0 else "#A78BFA"
    fill = "rgba(74,222,128,.10)" if d > 0 else "rgba(248,113,113,.10)" if d < 0 else "rgba(167,139,250,.10)"
    cur = "" if str(sym).endswith(".SR") else "$"            # a Saudi price is in riyals (the axis says nothing, the page does)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=idx, y=c.values, mode="lines", line=dict(color=col, width=2.2), fill="tozeroy", fillcolor=fill,
                             hovertemplate="%{x|%b %d}<br>" + cur + "%{y:,.2f}<extra></extra>", name=sym))
    fig.add_trace(go.Scatter(x=[idx[pos]], y=[c.values[pos]], mode="markers", marker=dict(size=12, color="#FFFFFF", line=dict(color=col, width=3)),
                             hovertemplate=L("The news", "الخبر") + "<br>%{x|%b %d}: " + cur + "%{y:,.2f}<extra></extra>", showlegend=False))
    fig.add_vline(x=idx[pos], line=dict(color="rgba(253,230,138,.7)", width=1.5, dash="dot"))
    fig.add_annotation(x=idx[pos], y=1, yref="paper", text=L("the news", "الخبر"), showarrow=False, yanchor="bottom",
                       font=dict(color="#FDE68A", size=11), bgcolor="rgba(14,9,24,.7)")
    lo, hi = float(c.min()), float(c.max())
    pad = (hi - lo) * .08 or hi * .02
    fig.update_layout(height=230, margin=dict(l=8, r=8, t=26, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      showlegend=False, hovermode="x unified", font=dict(color="#CFC8DA", size=11),
                      xaxis=dict(showgrid=False, tickformat="%b %d", color="#8F899B"),
                      yaxis=dict(range=[lo - pad, hi + pad], gridcolor="rgba(157,151,165,.12)", tickprefix=cur, color="#8F899B", side="right"))
    return fig


def _tab_tech(a, dfm=None):
    fa = a["facts"]
    if dfm is not None and len(dfm) > 5 and "Close" in dfm:
        fig = _price_fig(dfm, a["n"].get("time"), a["main"], a["dir"])
        if fig is not None:
            main = a["main"]
            mn = _tk(main)
            ui.html(f'<div class="nx-h">{T.icon("show_chart")}{T.esc(L(f"{mn}: the price around the story", f"{mn}: السعر حول الخبر"))}</div>')
            ui.chart(fig, key="nie_px_" + _sid(a))
    if not fa:
        ui.html(_note(L("No prices for this stock right now.", "ما فيه أسعار لهالسهم الحين."), "hourglass_empty"))
        return
    sym, d, c = a["main"], a["dir"] or 1, fa.get("close")
    ok_ = lambda good: (f'<span class="nx-ok y">✓ {T.esc(L("confirms", "يؤكد"))}</span>' if good else
                        f'<span class="nx-ok n">✗ {T.esc(L("against", "يعاكس"))}</span>')
    tiles = []
    for k, en, ar_ in (("sma20", "20-day average", "متوسط 20 يوم"), ("sma50", "50-day average", "متوسط 50 يوم"), ("sma200", "200-day average", "متوسط 200 يوم")):
        v = fa.get(k)
        if v and c:
            above = c > v
            tiles.append(_tile("trending_up" if above else "trending_down", L(en, ar_), f'<bdi dir="ltr">{c / v - 1:+.1%}</bdi>',
                               T.esc(L(f"{_tk(sym)} {'above' if above else 'below'} it ({v:,.2f})", f"{_tk(sym)} {'فوقه' if above else 'تحته'} ({v:,.2f})"))
                               + " " + (ok_((above and d > 0) or (not above and d < 0)) if a["dir"] else "")))
    rv = fa.get("rvol")
    if rv:
        tiles.append(_tile("bar_chart", L("Volume", "حجم التداول"), f'<bdi dir="ltr">{rv:.1f}<small>×</small></bdi>',
                           T.esc(L("of its 20-day average", "من متوسط 20 يوم")), _bar(min(rv / 3, 1), "#60A5FA")))
    if a["move"] is not None and fa.get("chg") is not None:
        mv = abs(a["move"])
        tiles.append(_tile("bolt", L("Today's move", "حركة اليوم"), T.pill(fa["chg"]),
                           T.esc(L(f"{mv:.1f}× a normal day (ATR {fa['atr_pct']:.1f}%)", f"{mv:.1f} ضعف اليوم العادي (ATR {fa['atr_pct']:.1f}%)"))
                           if fa.get("atr_pct") else "", _bar(min(mv / 3, 1), "#A78BFA")))
    if fa.get("ret21") is not None:
        tiles.append(_tile("calendar_month", L("Last month", "آخر شهر"), T.pill(fa["ret21"]),
                           ok_((fa["ret21"] > 0) == (d > 0)) if a["dir"] else ""))
    ui.html(f'<div class="nx-tiles">{"".join(tiles)}</div>')


def _price_map(p):
    """The trade map: the stop at the start, the target at the end; risk in red up to the entry, reward in green after it; the entry
    above the bar and the price now below it (they are often a few cents apart); each part explains itself on hover or tap."""
    up = p["dir"] > 0
    span = p["target"] - p["stop"]
    pos = lambda x: max(2.0, min(98.0, (x - p["stop"]) / span * 100)) if span else 50.0
    fmt = _money
    iso = lambda x: f"\u2066{x}\u2069"                     # a number in a note keeps its sign on the right side in Arabic
    stop_, tgt_, trg_, now_ = fmt(p["stop"]), fmt(p["target"]), fmt(p["trigger"]), fmt(p["price"])
    s_, t_, g_ = iso(stop_), iso(tgt_), iso(trg_)
    xe, xn = pos(p["trigger"]), pos(p["price"])
    risk, reward = p["risk_pct"], p["reward_pct"]          # from the price now, as on the three cards above
    rr = reward / risk if risk else 0
    gap = abs(p["trigger"] - p["price"]) / p["price"] * 100
    lose, win = 1000 * risk / 100, 1000 * reward / 100
    side_en, side_ar = ("above", "فوق") if up else ("below", "تحت")
    rk, rw, gp = iso(f"-{risk:.1f}%"), iso(f"+{reward:.1f}%"), iso(f"{gap:.1f}%")
    t_stop = L(f"The idea is wrong if the price reaches {s_}: get out, about {rk} from the price now.",
               f"الفكرة تسقط إذا وصل السعر {s_}: اطلع، تقريباً {rk} من السعر الحين.")
    t_tgt = L(f"The first target, twice the risk: {t_}, about {rw} from the price now.",
              f"أول هدف، ضعف المخاطرة: {t_}، تقريباً {rw} من السعر الحين.")
    t_go = L(f"The trade starts only on a close {side_en} {g_} with volume above its average.",
             f"الصفقة تبدأ بس إذا أغلق السعر {side_ar} {g_} بحجم فوق متوسطه.")
    t_r = L(f"Risk: down to the invalidation, {rk}.", f"المخاطرة: لين الإلغاء، {rk}.")
    t_g = L(f"Reward: up to the target, {rw}.", f"العائد: لين الهدف، {rw}.")
    t_now = L(f"The last price, {gp} from the entry.", f"آخر سعر، بعيد عن الدخول {gp}.")
    e = T.esc
    caps = (f'<div class="ends"><div class="cap st" tabindex="0" data-tip="{e(t_stop)}"><small><i></i>{L("Invalidation", "الإلغاء")}</small>'
            f'<b>{stop_}</b></div><div class="cap tg" tabindex="0" data-tip="{e(t_tgt)}"><small>{L("Target", "الهدف")}<i></i></small>'
            f'<b>{tgt_}</b></div></div>')
    entry = (f'<div class="band top"><div class="pin go" style="--x:{xe:.1f}%" tabindex="0" data-tip="{e(t_go)}">'
             f'<span class="lb">{L("Entry", "الدخول")} <b>{trg_}</b></span><i class="cn"></i></div></div>')
    track = (f'<div class="track"><div class="seg r" style="--w:{xe:.1f}%" tabindex="0" data-tip="{e(t_r)}"><bdi dir="ltr">-{risk:.1f}%</bdi></div>'
             f'<div class="seg g" style="--w:{100 - xe:.1f}%" tabindex="0" data-tip="{e(t_g)}"><bdi dir="ltr">+{reward:.1f}%</bdi></div>'
             f'<i class="tick go" style="--x:{xe:.1f}%"></i><i class="dot" style="--x:{xn:.1f}%"></i></div>')
    now = (f'<div class="band bot"><div class="pin now" style="--x:{xn:.1f}%" tabindex="0" data-tip="{e(t_now)}">'
           f'<i class="cn"></i><span class="lb">{L("Now", "الحين")} <b>{now_}</b></span></div></div>')
    head = (f'<div class="hd"><div class="t">{T.icon("route")}{L("Trade map", "خريطة الصفقة")}</div>'
            f'<span class="rr">{L("Reward : risk", "العائد : المخاطرة")} <b><bdi dir="ltr">{rr:.1f} : 1</bdi></b></span></div>')
    sa_ = MK.is_sa()
    with_ = L("With SAR 1,000:", "بـ 1,000 ريال:") if sa_ else L("With $1,000:", "بـ 1,000 دولار:")
    lo_ = f"-{lose:,.0f}" if sa_ else f"-${lose:,.0f}"
    hi_ = f"+{win:,.0f}" if sa_ else f"+${win:,.0f}"
    foot = (f'<div class="ft"><span>{with_} <b class="lo"><bdi dir="ltr">{lo_}</bdi></b> {L("at the invalidation", "عند الإلغاء")} · '
            f'<b class="hi"><bdi dir="ltr">{hi_}</bdi></b> {L("at the target", "عند الهدف")}</span>'
            f'<span>{L("The price now is", "السعر الحين بعيد")} <b class="bl"><bdi dir="ltr">{gap:.1f}%</bdi></b> {L("from the entry", "عن الدخول")}</span></div>')
    return f'<div class="nx-pm{" rtl" if is_ar() else ""}">{head}{caps}{entry}{track}{now}{foot}</div>'


def _tab_plan(a):
    p = NI.plan(a)
    if p and a.get("sa") and p["dir"] < 0:          # the Saudi market has no short selling for individuals: a bearish story is a reason to stay out
        ui.html(_note(L("A bearish setup, but the Saudi market has no short selling for individual investors: for a holder it is a reason to "
                        f"reduce or protect the position (the idea is wrong above {_money(p['stop'])}); for others, a reason to wait.",
                        "فرصة هابطة، لكن السوق السعودي ما فيه بيع على المكشوف للأفراد: لمن يملك السهم سبب لتخفيف المركز أو حمايته "
                        f"(الفكرة تسقط فوق {_money(p['stop'])})، ولغيره سبب للانتظار."), "block"))
        p = None
        ui.html(_note(L("Education, not a recommendation.", "للتعليم، مو توصية."), "school"))
        return
    if not p:
        ui.html(_note(L("No trading scenario: the news and the price do not line up enough (the setup is under 40/100).",
                        "ما فيه سيناريو تداول: الخبر والسعر ما يتفقون كفاية (الفرصة أقل من 40/100)."), "block"))
    else:
        up = p["dir"] > 0
        fmt = _money
        cards = [("go", L("Trigger", "إشارة الدخول"), fmt(p["trigger"]),
                  L("a close above today's high, with volume above its average" if up else "a close below today's low, with volume above its average",
                    "إغلاق فوق أعلى سعر اليوم بحجم فوق متوسطه" if up else "إغلاق تحت أدنى سعر اليوم بحجم فوق متوسطه")),
                 ("st", L("Invalidation", "إلغاء الفكرة"), fmt(p["stop"]),
                  L(f"today's {'low' if up else 'high'} or 1.5 ATR away · risk {p['risk_pct']:.1f}%",
                    f"{'أدنى' if up else 'أعلى'} سعر اليوم أو 1.5 ATR · المخاطرة {p['risk_pct']:.1f}%")),
                 ("tg", L("First target", "أول هدف"), fmt(p["target"]),
                  L(f"2× the risk · {p['reward_pct']:+.1f}%" if up else f"2× the risk · -{p['reward_pct']:.1f}%",
                    f"ضعف المخاطرة · {p['reward_pct']:+.1f}%" if up else f"ضعف المخاطرة · -{p['reward_pct']:.1f}%"))]
        ui.html('<div class="nx-plan">' + "".join(f'<div class="nx-lv {c}"><div class="l">{T.esc(t)}</div><div class="v">{v}</div>'
                                                   f'<div class="s">{T.esc(s_)}</div></div>' for c, t, v, s_ in cards) + "</div>")
        ui.html(_price_map(p))
    ui.html(_note(L("Education, not a recommendation. The rules above decide the setup; a language model only explains a story and never trades.",
                    "للتعليم، مو توصية. القواعد فوق هي اللي تحدد الفرصة، والذكاء الاصطناعي يشرح الخبر بس وما يتداول أبداً."), "school"))


# ---------------------------------------------------------------- the page's parts (21.5)
def _sid(a):
    """A story's id (for its card's button and its window)."""
    import hashlib
    return hashlib.md5(str(a["n"].get("link") or a["n"].get("title") or "").encode()).hexdigest()[:10]


def _mood(rows):
    """The mood of the news: the stories' sentiment weighted by their impact, from -100 (all bearish) to +100 (all bullish)."""
    w = sum(a["impact"] for a in rows)
    return 100 * sum(a["sent"] * a["impact"] for a in rows) / w if w else 0.0


def _mood_word(m):
    if m >= 25:
        return L("Bullish", "صاعد"), "#4ADE80"
    if m >= 8:
        return L("Leaning bullish", "يميل للصعود"), "#86EFAC"
    if m > -8:
        return L("Mixed", "متذبذب"), "#C4B5FD"
    if m > -25:
        return L("Leaning bearish", "يميل للهبوط"), "#FCA5A5"
    return L("Bearish", "هابط"), "#F87171"


def _gauge_svg(m):
    """A half dial from bearish (left, red) through mixed to bullish (right, green); the needle swings to m."""
    ang = max(-100.0, min(100.0, m)) * 0.9
    ticks = "".join(f'<line x1="100" y1="13" x2="100" y2="{21 if k % 2 else 25}" stroke="rgba(231,227,235,.45)" stroke-width="1.5" '
                    f'transform="rotate({k * 22.5 - 90:.1f} 100 100)"/>' for k in range(9))
    return ('<svg viewBox="0 0 200 112" aria-hidden="true"><defs><linearGradient id="niegd" x1="0" y1="0" x2="1" y2="0">'
            '<stop offset="0" stop-color="#EF4444"/><stop offset=".5" stop-color="#8B5CF6"/><stop offset="1" stop-color="#22C55E"/></linearGradient>'
            '<filter id="niegl" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="4"/></filter></defs>'
            '<path d="M22 100 A78 78 0 0 1 178 100" fill="none" stroke="rgba(157,151,165,.16)" stroke-width="18" stroke-linecap="round"/>'
            '<path d="M22 100 A78 78 0 0 1 178 100" fill="none" stroke="url(#niegd)" stroke-width="11" stroke-linecap="round" opacity=".35" filter="url(#niegl)"/>'
            '<path d="M22 100 A78 78 0 0 1 178 100" fill="none" stroke="url(#niegd)" stroke-width="9" stroke-linecap="round"/>' + ticks +
            f'<g><animateTransform attributeName="transform" type="rotate" from="0 100 100" to="{ang:.1f} 100 100" dur="1.1s" fill="freeze" '
            'calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"/>'
            '<path d="M100 32 L104.5 100 L95.5 100 Z" fill="#FFFFFF"/></g>'
            '<circle cx="100" cy="100" r="9" fill="#FFFFFF"/><circle cx="100" cy="100" r="4" fill="#1B1728"/></svg>')


def _mood_bars(rows, hrs, now, nb=12):
    """The mood in equal slices of the time window, oldest first (None: no story in that slice)."""
    span = hrs * 3600 / nb
    num, den = [0.0] * nb, [0.0] * nb
    for a in rows:
        t = a["n"].get("time")
        if t is None or pd.isna(t):
            continue
        k = int((now - t).total_seconds() // span)
        if 0 <= k < nb:
            i = nb - 1 - k
            num[i] += a["sent"] * a["impact"]
            den[i] += a["impact"]
    return [100 * x / y if y else None for x, y in zip(num, den)]


def _hero(res, hrs, now, n_src):
    """The command centre: the mood dial, the numbers of the window, the mood through the window."""
    m = _mood(res)
    word, col = _mood_word(m)
    bull = sum(1 for a in res if a["lab"] == "bull")
    bear = sum(1 for a in res if a["lab"] == "bear")
    neu = len(res) - bull - bear
    tot = max(len(res), 1)
    high = sum(1 for a in res if a["impact"] >= 70)
    setups = sum(1 for a in res if a["setup"]["total"] >= 55)
    top_ev = pd.Series([a["event"] for a in res]).value_counts().index[0] if res else None
    win = {6: L("6 hours", "6 ساعات"), 24: L("24 hours", "24 ساعة"), 96: L("4 days", "4 أيام")}.get(hrs, f"{hrs}h")
    mv = f"{m:+.0f}"
    dial = (f'<div class="nie-hc" data-nogq><div class="h">{T.icon("speed")}{T.esc(L("News mood", "مزاج الأخبار"))}</div>'
            f'<div class="nie-gauge">{_gauge_svg(m)}<div class="ends"><span class="b">{T.esc(L("Bearish", "هابط"))}</span>'
            f'<span class="u">{T.esc(L("Bullish", "صاعد"))}</span></div><div class="mv"><bdi>{mv}</bdi></div>'
            f'<div class="ml" style="color:{col}">{T.esc(word)}</div>'
            f'<div class="mb">{T.esc(L(f"the last {win}, each story weighted by its impact", f"آخر {win}، وكل خبر بوزن أثره"))}</div></div>'
            f'<div class="nie-mix"><i style="width:{bull / tot * 100:.1f}%;background:#4ADE80"></i><i style="width:{neu / tot * 100:.1f}%;background:#8B5CF6"></i>'
            f'<i style="width:{bear / tot * 100:.1f}%;background:#F87171"></i></div>'
            f'<div class="nie-mixl"><span>▲ <b>{bull}</b> {T.esc(L("bullish", "صاعد"))}</span><span>● <b>{neu}</b> {T.esc(L("neutral", "محايد"))}</span>'
            f'<span>▼ <b>{bear}</b> {T.esc(L("bearish", "هابط"))}</span></div></div>')
    ev_name = T.esc(L(*NI.EVENT[top_ev][:2])) if top_ev else "—"
    ev_ic = NI.EVENT[top_ev][2] if top_ev else "category"
    stats = [("newspaper", L("Stories read", "أخبار مقروءة"), f"{len(res):,}", L(f"from {n_src} sources", f"من {n_src} مصدر"), ""),
             ("bolt", L("High impact", "أثر عالي"), f"{high}", L("70 or more out of 100", "70 أو أكثر من 100"), " hot" if high else ""),
             ("insights", L("Setups", "فرص"), f"{setups}", L("news and price agree (55+)", "الخبر والسعر متفقين (55+)"), " go" if setups else ""),
             (ev_ic, L("Most common", "الأكثر"), ev_name, L("kind of event", "نوع الحدث"), "")]
    st_html = "".join(f'<div class="nie-st{c}"><div class="l">{T.icon(ic)}{T.esc(l_)}</div><div class="v{" sm" if i == 3 else ""}">{v}</div>'
                      f'<div class="s">{T.esc(s_)}</div></div>' for i, (ic, l_, v, s_, c) in enumerate(stats))
    nums = (f'<div class="nie-hc"><div class="h">{T.icon("monitoring")}{T.esc(L("This window", "هالفترة"))}</div>'
            f'<div class="nie-stats">{st_html}</div></div>')
    bars = []
    vals = _mood_bars(res, hrs, now)
    top = max([abs(v) for v in vals if v is not None] + [1.0])        # the strongest hour fills its half: the shape is readable
    step = hrs / max(len(vals), 1)
    for k, v in enumerate(vals):
        ago = round((len(vals) - 1 - k) * step, 1)
        when = L(f"{ago:g}h ago" if ago else "latest", f"قبل {ago:g} ساعة" if ago else "الأحدث")
        if v is None or abs(v) < 1:
            bars.append(f'<span class="e" title="{T.esc(when)} · {T.esc(L("calm", "هادئ"))}"><i></i></span>')
        else:
            h = max(8.0, abs(v) / top * 47)
            bars.append(f'<span title="{T.esc(when)} · {v:+.0f}"><i class="{"u" if v > 0 else "d"}" style="height:{h:.0f}%"></i></span>')
    upd = _ny_time(now)
    tz_en, tz_ar = MK.get()["tz_label"]
    flow = (f'<div class="nie-hc" data-nogq><div class="h">{T.icon("timeline")}{T.esc(L("Mood through time", "المزاج مع الوقت"))}'
            f'<span class="nie-live"><i></i>{T.esc(L("LIVE", "مباشر"))}</span></div>'
            f'<div class="nie-tl">{"".join(bars)}</div><div class="nie-tll"><span>-{hrs}h</span><span>{T.esc(L("now", "الحين"))}</span></div>'
            f'<div class="nie-upd">{T.esc(L(f"Updated {upd} {tz_en} time. Green above the line: bullish news led that hour; red below: bearish.", f"آخر تحديث {upd} بتوقيت {tz_ar}. الأخضر فوق الخط: الأخبار الصاعدة غلبت بهالوقت، والأحمر تحته: الهابطة."))}</div></div>')
    return f'<div class="nie-hero">{dial}{nums}{flow}</div>'


def _breaking(res, titles_ar):
    """The stories with the most impact, running across the page (hover to stop)."""
    top = sorted(res, key=lambda a: -a["impact"])
    hot = [a for a in top if a["impact"] >= 65][:10]
    if len(hot) < 3:
        hot = top[:6]
    if not hot:
        return ""
    ar = is_ar()
    items = []
    for a in hot:
        n = a["n"]
        title = (titles_ar.get(n["title"]) if ar and titles_ar else None) or n["title"]
        who = _tk(a["direct"][0]) if a["direct"] else L(*NI.EVENT[a["event"]][:2])
        arrow = {"bull": "▲", "bear": "▼", "neutral": "●"}[a["lab"]]
        items.append(f'<span class="it {a["lab"]}"><span class="ar">{arrow}</span><b>{T.esc(who)}</b><span dir="auto">{T.esc(title)}</span>'
                     f'<span class="im">{a["impact"]:.0f}</span><small>{T.time_ago(n["time"], ar) if pd.notna(n.get("time")) else ""}</small></span>')
    inner = "".join(items)
    dur = max(30, 9 * len(items))
    return (f'<div class="nie-brk" data-nogq><span class="lb">{T.icon("campaign")}{T.esc(L("Breaking", "عاجل"))}</span>'
            f'<div class="vw"><div class="tr" style="animation-duration:{dur}s">{inner}{inner}</div></div></div>')


def _flow_fig(rows, titles_ar):
    """Every story as a bubble: when (across), its impact (up), bullish green / bearish red / neutral violet, the bigger the
    better its setup. A click opens the story."""
    import html as _h
    import textwrap
    import plotly.graph_objects as go
    ar = is_ar()
    fig = go.Figure()
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(248,113,113,.07)", line_width=0)
    fig.add_hline(y=70, line=dict(color="rgba(248,113,113,.45)", width=1, dash="dot"))
    fig.add_annotation(x=0, xref="paper", y=99, text=L("High impact", "أثر عالي"), showarrow=False, xanchor="left", yanchor="top",
                       font=dict(color="#FCA5A5", size=11))
    for lab, col in (("neutral", "#A78BFA"), ("bear", "#F87171"), ("bull", "#4ADE80")):
        pts = [a for a in rows if a["lab"] == lab and pd.notna(a["n"].get("time"))]
        if not pts:
            continue
        xs = [pd.Timestamp(a["n"]["time"]).tz_convert(MK.tz()).tz_localize(None) for a in pts]
        tips = []
        for a in pts:
            t = (titles_ar.get(a["n"]["title"]) if ar and titles_ar else None) or a["n"]["title"]
            who = ", ".join(_tk(s_) for s_ in a["direct"][:3]) or L("Market", "السوق")
            tips.append("<b>" + _h.escape(who) + "</b> · " + _h.escape(L(*NI.EVENT[a["event"]][:2])) + "<br>"
                        + "<br>".join(_h.escape(x) for x in textwrap.wrap(t, 58)[:3])
                        + "<br>" + L("Impact", "الأثر") + f" <b>{a['impact']:.0f}</b> · " + L("Setup", "الفرصة") + f" <b>{a['setup']['total']}</b>")
        fig.add_trace(go.Scatter(
            x=xs, y=[a["impact"] for a in pts], mode="markers", name=L(*NI.SENT[lab][:2]), customdata=[_sid(a) for a in pts],
            text=tips, hovertemplate="%{text}<extra></extra>",
            marker=dict(size=[9 + a["setup"]["total"] / 100 * 20 for a in pts], color=col, opacity=.82,
                        line=dict(color="rgba(255,255,255,.55)", width=1))))
    fig.update_layout(height=320, margin=dict(l=8, r=8, t=34, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#CFC8DA", size=11), dragmode=False, clickmode="event+select",
                      hoverlabel=dict(bgcolor="#1B1728", bordercolor="rgba(167,139,250,.5)", font=dict(color="#F4F1F8", size=12), align="left"),
                      legend=dict(orientation="h", x=1, xanchor="right", y=1.02, yanchor="bottom", font=dict(size=11)),
                      xaxis=dict(showgrid=False, color="#8F899B", tickformat="%H:%M<br>%b %d", fixedrange=True, zeroline=False),
                      yaxis=dict(range=[0, 104], gridcolor="rgba(157,151,165,.12)", color="#8F899B", zeroline=False, fixedrange=True,
                                 title=dict(text=L("Impact", "الأثر"), font=dict(size=11))))
    return fig


def _sectors(res):
    """The sectors in the news: how many stories, and their mood (impact weighted)."""
    agg = {}
    for a in res:
        names = {sec for sec, _ in a["sectors"]}
        if not names and a["event"] in ("macro", "market"):
            names = {"__market"}
        for sec in names:
            d = agg.setdefault(sec, [0, 0.0, 0.0])
            d[0] += 1
            d[1] += a["sent"] * a["impact"]
            d[2] += a["impact"]
    top = sorted(agg.items(), key=lambda x: (-x[1][0], -x[1][2]))[:8]
    if not top:
        return ""
    rows = []
    for i, (sec, (n, num, den)) in enumerate(top):
        net = 100 * num / den if den else 0
        name = L("Whole market", "السوق كله") if sec == "__market" else _secn(sec)
        w = min(abs(net), 100) / 100 * 50
        bar = (f'<i style="left:50%;width:{w:.1f}%;background:linear-gradient(90deg,#22C55E88,#4ADE80);animation-delay:{i * 60}ms"></i>' if net >= 1 else
               f'<i style="left:{50 - w:.1f}%;width:{w:.1f}%;background:linear-gradient(90deg,#F87171,#EF444488);animation-delay:{i * 60}ms"></i>' if net <= -1 else "")
        cls = "u" if net >= 1 else "d" if net <= -1 else "z"
        rows.append(f'<div class="r"><span class="nm">{T.esc(name)}</span><span class="c">{n}</span><div class="bar">{bar}</div>'
                    f'<span class="v {cls}">{net:+.0f}</span></div>')
    return (f'<div class="nie-sp" data-nogq>{"".join(rows)}<div class="lg2"><span>◀ {T.esc(L("bearish", "هابط"))}</span>'
            f'<span>{T.esc(L("bullish", "صاعد"))} ▶</span></div></div>')


def _tickers(res, chg, k=6):
    """The companies in the most stories: (symbol, stories, mood, change today)."""
    agg = {}
    for a in res:
        for sym in a["direct"][:2]:
            d = agg.setdefault(sym, [0, 0.0, 0.0])
            d[0] += 1
            d[1] += a["sent"] * a["impact"]
            d[2] += a["impact"]
    top = sorted(agg.items(), key=lambda x: (-x[1][0], -x[1][2]))[:k]
    return [(sym, n, 100 * num / den if den else 0.0, (chg.get(sym) or (None, None))[1]) for sym, (n, num, den) in top]


def _tk_card(sym, n, net, c, on):
    w = min(abs(net), 100) / 100 * 50
    bar = (f'<i style="left:50%;width:{w:.1f}%;background:#4ADE80"></i>' if net >= 1 else
           f'<i style="left:{50 - w:.1f}%;width:{w:.1f}%;background:#F87171"></i>' if net <= -1 else "")
    stories = L(f"{n} stories" if n != 1 else "1 story", f"{n} خبر" if n != 1 else "خبر واحد")
    chk = f'<span class="ok">{T.icon("filter_alt")}</span>' if on else ""
    return (f'<div class="nie-tkc{" on" if on else ""}" data-nogq><div class="t">{T.logo_obj(sym, 28)}<b dir="auto">{T.esc(_tk(sym))}</b>{chk}</div>'
            f'<div class="n"><span>{T.esc(stories)}</span>{T.pill(c)}</div><div class="sb">{bar}</div></div>')


def _pick_ticker(sym):
    ss["nie_tkf"] = None if ss.get("nie_tkf") == sym else sym
    ss["nie_n"] = 12


def _open(sid):
    ss["nie_open"] = sid


def _clear_filters():
    ss["nie_tkf"] = None
    ss["nie_q"] = ""
    ss["nie_n"] = 12


def _card_html(a, title, chg, big=False):
    """One story as a card: its picture, the kind of event and the companies with today's move, the headline, the outlet and the
    time, then its reading (sentiment, impact, setup)."""
    n = a["n"]
    ar = is_ar()
    en_ev, ar_ev, ic, _hz = NI.EVENT.get(a["event"], NI.EVENT["other"])
    sen, sar, _c = NI.SENT[a["lab"]]
    arrow = {"bull": "▲", "bear": "▼", "neutral": "●"}[a["lab"]]
    tks = []
    for sym in a["direct"][:3]:
        cc = (chg.get(sym) or (None, None))[1]
        mv = "" if cc is None or pd.isna(cc) else f' <span class="{"u" if cc >= 0 else "d"}"><bdi dir="ltr">{cc:+.1f}%</bdi></span>'
        tks.append(f'<span class="tkr" dir="auto">{T.esc(_tk(sym))}{mv}</span>')
    new = f'<span class="nw">{T.esc(L("NEW", "جديد"))}</span>' if a["new"] else ""
    when = T.time_ago(n["time"], ar) if pd.notna(n.get("time")) else ""
    imp = a["impact"]
    st_ = a["setup"]
    meta = f'<bdi>{T.esc(n.get("source") or "")}</bdi>{T.also_badge(n.get("also"), ar)} · {when}'
    foot = (f'<div class="ft"><span class="se {a["lab"]}">{arrow} {T.esc(L(sen, sar))}</span>'
            f'<span class="im">{T.esc(L("Impact", "الأثر"))} <span class="bar"><i style="width:{imp:.0f}%;background:{_imp_col(imp)}"></i></span><b>{imp:.0f}</b></span>'
            f'<span class="su">{T.esc(L("Setup", "الفرصة"))} {_ring(st_["total"], 100, _setup_col(st_), 30, 4)}</span></div>')
    cls = f'nie-cd {a["lab"]}{" hi" if imp >= 70 else ""}{" big" if big else ""}'
    if big:
        why_en, why_ar = NI.why(a)
        summ = str(n.get("summary") or "").strip()
        sm = f'<div class="sm" dir="auto">{T.esc(summ[:320])}</div>' if summ and not ar else ""
        return (f'<div class="{cls}" data-nogq><div class="pic">{T.news_thumb(n, big=True)}</div><div class="bd">'
                f'<span class="nie-spot">{T.icon("local_fire_department")}{T.esc(L("Top story right now", "أهم خبر الحين"))}</span>'
                f'<div class="top"><span class="ev">{T.icon(ic)}{T.esc(_ev_name(a, en_ev, ar_ev))}</span>{"".join(tks)}{new}</div>'
                f'<div class="tt" dir="auto">{T.esc(title)}</div><div class="mt">{meta}</div>{sm}'
                f'<div class="why">{T.icon("lightbulb")}<span>{T.esc(L(why_en, why_ar))}</span></div>{foot}'
                f'<span class="go">{T.esc(L("Open the full analysis", "افتح التحليل الكامل"))} {T.icon("arrow_back" if ar else "arrow_forward")}</span></div></div>')
    return (f'<div class="{cls}" data-nogq><div class="pic">{T.news_thumb(n)}</div><div class="bd">'
            f'<div class="top"><span class="ev">{T.icon(ic)}{T.esc(_ev_name(a, en_ev, ar_ev))}</span>{"".join(tks)}{new}</div>'
            f'<div class="tt" dir="auto">{T.esc(title)}</div><div class="mt">{meta}</div>{foot}</div></div>')


def _card(a, title, chg, big=False):
    with st.container(key="nie_c_" + _sid(a)):
        ui.html(_card_html(a, title, chg, big))
        st.button(L("Open", "افتح"), key="nie_cb_" + _sid(a), on_click=_open, args=(_sid(a),), width="stretch")


def _table(rows, titles_ar):
    """The same stories as a table (a row opens the story)."""
    df = pd.DataFrame([{"pic": picture(a), "time": _ny_time(a["n"]["time"]), "stock": _stock_txt(a),
                        "news": (titles_ar.get(a["n"]["title"]) if titles_ar else None) or a["n"]["title"],
                        "event": L(*NI.EVENT[a["event"]][:2]), "impact": int(round(a["impact"])),
                        "sent": _sent_txt(a["lab"]), "score": a["setup"]["total"]} for a in rows])
    cfg = {"pic": st.column_config.ImageColumn("", width="small"),
           "time": st.column_config.TextColumn(L(f"Time ({MK.get()['tz_label'][0]})", f"الوقت ({MK.get()['tz_label'][1]})"), width="small"),
           "stock": st.column_config.TextColumn(L("Stock", "السهم"), width="small"),
           "news": st.column_config.TextColumn(L("News", "الخبر"), width="large"),
           "event": st.column_config.TextColumn(L("Event", "الحدث")),
           "impact": st.column_config.ProgressColumn(L("Impact", "الأثر"), min_value=0, max_value=100, format="%d"),
           "sent": st.column_config.TextColumn(L("Sentiment", "الاتجاه")),
           "score": st.column_config.ProgressColumn(L("Setup", "الفرصة"), min_value=0, max_value=100, format="%d")}

    def _tone(v):
        return LM.css("color:#4ADE80;font-weight:700" if str(v).startswith("▲") else "color:#F87171;font-weight:700" if str(v).startswith("▼")
                      else "color:#C4B5FD")
    bold = LM.css("font-weight:800;color:#FFFFFF")
    try:
        view = df.style.map(_tone, subset=["sent"]).map(lambda v: bold, subset=["stock"])
    except Exception:
        view = df
    try:
        ev = st.dataframe(view, hide_index=True, width="stretch", height=min(44 * len(df) + 42, 620), row_height=44, column_config=cfg,
                          on_select="rerun", selection_mode="single-row", key="nie_tbl")
        sel = list(getattr(getattr(ev, "selection", None), "rows", None) or [])
    except TypeError:
        st.dataframe(df, hide_index=True, width="stretch", column_config=cfg)
        sel = []
    st.caption(L("Tick a row to open the story. Impact: how strongly the news can move its stock (0-100). Setup: the news set against "
                 "momentum, volume, trend and the market (0-100).",
                 "علّم على أي سطر عشان يفتح الخبر. الأثر: قوة الخبر في تحريك سهمه (0-100). الفرصة: الخبر مقابل الزخم والحجم والاتجاه "
                 "والسوق (0-100)."))
    sig = sel[0] if sel and sel[0] < len(rows) else None
    if sig is not None and ss.get("nie_tbl_last") != _sid(rows[sig]):
        ss["nie_tbl_last"] = _sid(rows[sig])
        return _sid(rows[sig])
    if sig is None:
        ss["nie_tbl_last"] = None
    return None


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _more_peers(sym, exclude=()):
    """Related companies for a stock the site's own lists don't cover: the biggest of its industry (from the summaries the
    site keeps), then the ones investors follow with it on Yahoo. -> (peers, sector, industry)"""
    peers_, info_ = data.industry_peers(sym, 6)
    out = [s for s in peers_ if s not in exclude]
    if len(out) < 5:
        sa = str(sym).upper().endswith(".SR")      # the same market as the story's company
        out += [s for s in data.similar(sym, 8) if s not in exclude and s not in out and "^" not in s and "=" not in s
                and str(s).upper().endswith(".SR") == sa]
    return out[:5], info_.get("sector") or "", info_.get("industry") or ""


def _enrich(a):
    """A story about a company the engine knows little about (no peers, no sector): its related companies and sector are
    looked up when the story is opened."""
    if not a["direct"] or (a["indirect"] and a["sectors"]):
        return a
    try:
        more, sec, ind = _more_peers(a["main"], tuple(a["direct"]))
    except Exception:
        return a
    a = dict(a)
    if not a["indirect"] and more:
        a["indirect"] = more
    if not a["sectors"] and (sec or ind):
        a["sectors"] = [(sec, ind)]
    return a


def _quick_window(a, chg):
    """A story opened from the News page: its reading in four rings, then its AI analysis, the stocks it hits and why it matters."""
    n = a["n"]
    ar = is_ar()
    title = n["title"]
    if ar:
        title = (_translate((n["title"],)) or {}).get(n["title"]) or title
    en_ev, ar_ev, ic, _hz = NI.EVENT.get(a["event"], NI.EVENT["other"])
    sen, sar, scol = NI.SENT[a["lab"]]
    tags = (f'<span class="nie-tag" style="color:{scol};border-color:{scol}55;background:{scol}14">{T.esc(L(sen, sar))}</span>'
            f'<span class="nie-tag" style="color:#C4B5FD;border-color:#C4B5FD44;background:#7C3AED14">{T.icon(ic)}{T.esc(_ev_name(a, en_ev, ar_ev))}</span>')
    ui.html(f'<div class="nie-card">{T.news_thumb(n, big=True)}<div class="tx"><div class="tt"><a href="{T.esc(n.get("link") or "#")}" '
            f'target="_blank" dir="auto">{T.esc(title)}</a></div><div class="mt"><bdi>{T.esc(n.get("source") or "")}</bdi> · '
            f'{T.time_ago(n["time"], ar) if pd.notna(n.get("time")) else ""}</div><div class="hd">{tags}</div></div></div>')
    if n.get("more"):                                    # the same event told by other outlets
        ui.html(T.coverage(n, ar))
    ui.html(_verdict(a))
    why_en, why_ar = NI.why(a)
    tabs = st.tabs([L(":material/auto_awesome: AI analysis", ":material/auto_awesome: التحليل الذكي"),
                    L(":material/hub: Stocks", ":material/hub: الأسهم المتأثرة"), L(":material/lightbulb: Why it matters", ":material/lightbulb: ليش يهم")])
    with tabs[0]:
        _tab_ai(a, n, ar)
    with tabs[1]:
        _tab_stocks(a, chg)
    with tabs[2]:
        ui.html(f'<div class="nx-callout">{T.icon("lightbulb")}<p>{T.esc(L(why_en, why_ar))}</p></div>')
        if a["words"]:
            ui.html(f'<div class="nx-h">{T.icon("key")}{T.esc(L("What in the headline decided it", "وش في العنوان حدد الاتجاه"))}</div>' + _word_chips(a))
    st.page_link(ui.PAGES["newsintel"], label=L("The full analysis in the News Intelligence Engine", "التحليل الكامل في محرك ذكاء الأخبار"),
                 icon=":material/neurology:")


def story_quick(n):
    """Opens one story of the News page in its analysis window (the engine reads it on the spot)."""
    ui.html(CSS + CSS2)
    bench = _bench()
    tick = [t for t in (n.get("tickers") or []) if t and t not in NI.BENCHES][:4]
    px = data.history_many((bench,) + tuple(tick[:1]), "1y") or {}
    chg = data.quick_changes(tick) if tick else {}
    if "iq" not in n:
        newsiq.enrich([n], chg)
    rg = NI.regime(px.get(bench)) if px.get(bench) is not None else "mixed"
    a = _enrich(NI.analyze(n, px, chg, rg, None, bench))
    more = [s_ for s_ in a["direct"] + a["indirect"] if s_ not in chg]
    if more:
        try:
            chg = dict(chg, **data.quick_changes(more))
        except Exception:
            pass
    st.dialog(L("Story analysis", "تحليل الخبر"), width="large")(_quick_window)(a, chg)


def _story_window(a, chg, sec_chg, titles_ar, dfm):
    _detail(a, chg, sec_chg, titles_ar, dfm)


def _show_story(a, chg, px, titles_ar):
    a = _enrich(a)
    peers_ = sorted({s_ for s_ in a["direct"] + a["indirect"]})
    chg2 = dict(chg)
    if peers_:
        try:
            chg2.update(data.quick_changes(peers_))
        except Exception:
            pass
    try:
        if a["macro"] and a.get("sa"):            # the Saudi sectors: the average move of their companies today
            mv = data.sa_moves()
            sec_chg = {k: (None, float(v)) for k, v in mv.groupby("Sector")["Chg %"].mean().dropna().items()} if not mv.empty else {}
        else:
            sec_chg = data.quick_changes(list(U.SECTOR_ETFS)) if a["macro"] else {}
    except Exception:
        sec_chg = {}
    st.dialog(L("Story analysis", "تحليل الخبر"), width="large")(_story_window)(a, chg2, sec_chg, titles_ar, px.get(a["main"]))


def page_news_intel():
    ui.html(CSS + CSS2)
    sa = MK.is_sa()
    bench = _bench()
    if sa:
        ui.header("neurology", "News Intelligence Engine · Saudi Market", "محرك ذكاء الأخبار · السوق السعودي",
                  "Every Saudi headline (Arabic and English) read like an analyst would: the kind of event, bullish or bearish, how material it "
                  "is, its impact from 0 to 100, the companies it hits directly and through their industry, and whether the price confirms "
                  "it — then a setup score out of 100 with its parts.",
                  "كل خبر عن السوق السعودي (عربي وإنجليزي) ينقرأ مثل ما يقرأه المحلل: نوع الحدث، صاعد أو هابط، أهميته، أثره من 0 إلى 100، "
                  "الشركات اللي يأثر عليها مباشرة وعن طريق قطاعها، وهل السعر يؤكده، وبعدين درجة الفرصة من 100 مع أجزائها.")
    else:
        ui.header("neurology", "News Intelligence Engine", "محرك ذكاء الأخبار",
                  "Every headline read like an analyst would: the kind of event, bullish or bearish, how material it is, its impact from 0 to 100, "
                  "how long it may last, the companies it hits directly and indirectly, and whether the price confirms it — then a setup score "
                  "out of 100 with its parts.",
                  "كل خبر ينقرأ مثل ما يقرأه المحلل: نوع الحدث، صاعد أو هابط، أهميته، أثره من 0 إلى 100، كم يدوم، الشركات اللي يأثر عليها "
                  "مباشرة وغير مباشرة، وهل السعر يؤكده، وبعدين درجة الفرصة من 100 مع أجزائها.")
    hrs = ss.get("nie_hrs") or 24
    with st.spinner(L("Reading the news and the prices...", "يقرأ الأخبار والأسعار...")):
        items = data.market_news(96)
        now = pd.Timestamp.now(tz="UTC")
        items = [n for n in items if pd.notna(n.get("time")) and n["time"] >= now - pd.Timedelta(hours=hrs)][:600]
        items = newsbot.cluster(items)[:400]            # one card per event, with every outlet that told it
        tick = sorted({t for n in items[:300] for t in (n.get("tickers") or [])[:2] if t})
        chg = data.quick_changes(tick) if tick else {}
        newsiq.enrich(items, chg)
        items = [n for n in items if not any(k[0] == "opinion" for k in n["iq"].get("keywords", []))]      # opinion pieces out
        mains = [((n.get("tickers") or [None])[0]) for n in items]
        syms = (bench,) + tuple(sorted({s_ for s_ in mains if s_ and s_ != bench}))[:79]
        px = data.history_many(syms, "1y") if syms else {}
        res = NI.analyze_all(items, px, chg, px.get(bench), now, bench)
    seen = set()                                        # one card per story (a story's id is its link): never two widgets with one key
    res = [a for a in res if not (_sid(a) in seen or seen.add(_sid(a)))]
    tr = ss.get(f"nie_tr_{'ar' if is_ar() else 'en'}", is_ar())
    n_src = len({n.get("source") for n in items if n.get("source")})
    if res:
        top_hot = sorted(res, key=lambda a: -a["impact"])[:10]
        titles_ar = _translate(tuple(dict.fromkeys(a["n"]["title"] for a in (top_hot + res[:120])))) if tr else {}
        ui.html(_hero(res, hrs, now, n_src))
        ui.html(_breaking(res, titles_ar))
    else:
        titles_ar = {}
    # ---- the filters
    # the filters on three rows, so no choice is cut on a narrower screen (or in Arabic, whose labels are longer)
    c1, c2 = st.columns([1.7, 1.3], vertical_alignment="bottom")
    q = c1.text_input(L("Search", "بحث"), key="nie_q", placeholder=L("A word, a company or a ticker…", "كلمة أو شركة أو رمز…"))
    c2.segmented_control(L("Time", "الوقت"), [6, 24, 96], default=24, key="nie_hrs",
                         format_func=lambda h: {6: L("6 hours", "6 ساعات"), 24: L("24 hours", "24 ساعة"), 96: L("4 days", "4 أيام")}[h])
    c3, c4, e2 = st.columns([1.2, 1.4, 1.1], vertical_alignment="bottom")
    sent = c3.segmented_control(L("Sentiment", "الاتجاه"), ["all", "bull", "bear"], default="all", key="nie_sent",
                                format_func=lambda k: L("All", "الكل") if k == "all" else L(*NI.SENT[k][:2])) or "all"
    sort = c4.segmented_control(L("Sort by", "الترتيب"), ["impact", "setup", "new"], default="impact", key="nie_sort",
                                format_func=lambda k: {"impact": L("Impact", "الأثر"), "setup": L("Setup", "الفرصة"), "new": L("Latest", "الأحدث")}[k]) or "impact"
    e1, e3 = st.columns([3, 1.2], vertical_alignment="bottom")
    ev_keys = [k for k, *_ in NI.EVENTS] + ["market", "other"]
    ui.valid_multi("nie_ev", ev_keys)
    pick_ev = e1.multiselect(L("Event type", "نوع الخبر"), ev_keys, key="nie_ev", placeholder=L("All events", "كل الأحداث"),
                             format_func=lambda k: L(*NI.EVENT[k][:2]))
    view = e2.segmented_control(L("View", "العرض"), ["cards", "table"], default="cards", key="nie_view",
                                format_func=lambda k: L("Cards", "بطاقات") if k == "cards" else L("Table", "جدول")) or "cards"
    e3.toggle(L("Translate to Arabic", "ترجمة للعربية"), value=is_ar(), key=f"nie_tr_{'ar' if is_ar() else 'en'}")   # one per language
    if not res:
        st.info(L("The news bot has no headlines for this time yet; try a longer time or come back in a few minutes.",
                  "بوت الأخبار ما عنده عناوين لهالوقت للحين، جرّب وقت أطول أو ارجع بعد دقائق."), icon=":material/hourglass_empty:")
        return
    # ---- the companies in the news (each one filters the page)
    tks = _tickers(res, chg)
    tkf = ss.get("nie_tkf")
    if tkf and tkf not in {t for t, *_ in tks} and not any(tkf in a["direct"] for a in res):
        tkf = ss["nie_tkf"] = None
    if tks:
        ui.sec("trending_up", "In the news now", "في الأخبار الحين")
        with st.container(key="nie_tks"):
            cols = st.columns(len(tks))
            for col, (sym, n, net, c) in zip(cols, tks):
                with col:
                    with st.container(key="nie_tk_" + sym):
                        ui.html(_tk_card(sym, n, net, c, tkf == sym))
                        st.button(sym, key="nie_tb_" + sym, on_click=_pick_ticker, args=(sym,), width="stretch")
    # ---- what the filters keep
    qn = str(q or "").strip().lower()

    def keep(a):
        if pick_ev and a["event"] not in pick_ev:
            return False
        if sent != "all" and a["lab"] != sent:
            return False
        if tkf and tkf not in a["direct"]:
            return False
        if qn:
            hay = " ".join([a["n"]["title"], titles_ar.get(a["n"]["title"], ""), " ".join(a["direct"]), str(a["n"].get("source") or "")]
                           + [NI.company(t_)[0] for t_ in a["direct"][:2]]).lower()
            return qn in hay
        return True
    shown = [a for a in res if keep(a)]
    key_of = {"impact": lambda a: -a["impact"], "setup": lambda a: -a["setup"]["total"],
              "new": lambda a: -(a["n"]["time"].timestamp() if pd.notna(a["n"].get("time")) else 0)}
    shown.sort(key=key_of[sort])
    opened = ss.pop("nie_open", None)
    # ---- the flow of the news and the sectors
    left, right = st.columns([1.75, 1], gap="medium")
    with left:
        ui.sec("bubble_chart", "News flow", "تدفق الأخبار")
        if shown:
            try:
                ev = st.plotly_chart(LM.figure(_flow_fig(shown[:150], titles_ar)), theme=None, key="nie_flow", config=ui.CHART_CONFIG,
                                     on_select="rerun", selection_mode=("points",))
                pts = list(getattr(getattr(ev, "selection", None), "points", None) or []) if ev is not None else []
            except TypeError:
                ui.chart(_flow_fig(shown[:150], titles_ar), key="nie_flow")
                pts = []
            sid = None
            if pts:
                cd = pts[0].get("customdata") if isinstance(pts[0], dict) else None
                sid = cd[0] if isinstance(cd, (list, tuple)) and cd else cd if isinstance(cd, str) else None
            if sid and ss.get("nie_flow_last") != sid:
                opened = sid
            ss["nie_flow_last"] = sid
            st.caption(L("Every bubble is a story: higher means more impact, bigger means a better setup. Click one to open it.",
                         "كل فقاعة خبر: كل ما ارتفعت زاد أثره، وكل ما كبرت كانت فرصته أقوى. اضغط على أي وحدة عشان تفتحها."))
    with right:
        ui.sec("donut_small", "Sectors in the news", "القطاعات في الأخبار")
        ui.html(_sectors(res) or _note(L("No sector stands out yet.", "ما فيه قطاع بارز للحين.")))
    # ---- the feed
    ui.sec("dynamic_feed", "Live feed", "الأخبار أول بأول")
    if tkf or qn:
        f1, f2 = st.columns([4, 1], vertical_alignment="center")
        lab = []
        if tkf:
            lab.append(L(f"Company: {tkf}", f"الشركة: {tkf}"))
        if qn:
            lab.append(L(f"Search: {q}", f"بحث: {q}"))
        f1.markdown(f'<span class="nie-flt">{T.icon("filter_alt")}{T.esc(" · ".join(lab))} · <b>{len(shown)}</b></span>', unsafe_allow_html=True)
        f2.button(L("Clear", "مسح"), key="nie_clear", icon=":material/close:", width="stretch", on_click=_clear_filters)
    if not shown:
        st.caption(L("No story matches these filters.", "ما فيه خبر يطابق هالفلاتر."))
    elif view == "table":
        hit = _table(shown[:120], titles_ar)
        opened = hit or opened
    else:
        title_of = lambda a: (titles_ar.get(a["n"]["title"]) if titles_ar else None) or a["n"]["title"]
        _card(shown[0], title_of(shown[0]), chg, big=True)
        rest = shown[1:]
        n_show = int(ss.get("nie_n") or 12)
        page = rest[:n_show]
        for i in range(0, len(page), 2):
            cols = st.columns(2)
            for col, a in zip(cols, page[i:i + 2]):
                with col:
                    _card(a, title_of(a), chg)
        if len(rest) > n_show:
            m1, m2, m3 = st.columns([1, 1.2, 1])
            if m2.button(L(f"Show more · {len(rest) - n_show} left", f"اعرض أكثر · باقي {len(rest) - n_show}"), key="nie_more",
                         icon=":material/expand_more:", width="stretch"):
                ss["nie_n"] = n_show + 12
                st.rerun()
        st.markdown(f'<div class="nie-more">{T.esc(L("Click any story for its full analysis.", "اضغط على أي خبر عشان تشوف تحليله الكامل."))}</div>',
                    unsafe_allow_html=True)
    # ---- how the engine works
    with st.expander(L("How the engine reads the news", "كيف يقرأ المحرك الأخبار"), icon=":material/neurology:"):
        ui.html(_pipeline(len(res), sum(1 for a in res if a["direct"]), sum(1 for a in res if a["event"] == "macro"),
                          sum(1 for a in res if a["setup"]["total"] >= 55)))
    # ---- a story opened: its full analysis in a window
    if opened:
        a = next((x for x in res if _sid(x) == opened), None)
        if a is not None:
            _show_story(a, chg, px, titles_ar)

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "22.4.2"
