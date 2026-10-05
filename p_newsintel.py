"""
p_newsintel.py - Discover → News Intelligence Engine: the news bot's headlines read by newsintel.py (event, sentiment,
materiality, impact, horizon, companies hit directly and indirectly, confidence, price reaction) and set against the price
(a setup score out of 100 with its parts). A live table; a story opens with its AI analysis, the affected stocks, why it
matters, the expected impact, the technical confirmation and a trading scenario.
"""
import json
import time

import pandas as pd
import requests
import streamlit as st

import data
import lightmode as LM
import newsintel as NI
import newsiq
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

IMPACT_LEVELS = [(70, "High", "عالي"), (45, "Medium", "متوسط"), (0, "Low", "منخفض")]
_EV_ABBR = {"macro": "MAC", "market": "MKT", "earnings": "EPS", "guidance": "GUI", "mna": "M&A", "regulation": "REG", "lawsuit": "LAW",
            "management": "CEO", "contract": "WIN", "analyst": "RTG", "offering": "OFF", "payout": "DIV", "restructuring": "CUT",
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


def _sent_txt(lab):
    en, ar, _ = NI.SENT[lab]
    arrow = {"bull": "▲", "bear": "▼", "neutral": "●"}[lab]
    return f"{arrow} {L(en, ar)}"


def _stock_txt(a):
    return ", ".join(a["direct"][:3]) if a["direct"] else L("Market (SPY)", "السوق (SPY)")


def _ny_time(ts):
    try:
        t = pd.Timestamp(ts)
        t = t.tz_localize("UTC") if t.tzinfo is None else t
        return t.tz_convert("America/New_York").strftime("%m/%d %H:%M")
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
    steps = [("rss_feed", ("Sources", "المصادر"), ("35 feeds + Yahoo Finance", "35 مصدر + ياهو فاينانس")),
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


def _fact(label, value):
    return f'<div class="nie-f"><div class="l">{T.esc(label)}</div><div class="v">{value}</div></div>'


def _score_block(a):
    s = a["setup"]
    rows = []
    for k, en, ar, mx in NI.PARTS:
        v = s["parts"][k]
        cls = "p" if v > 0.5 else "n" if v < -0.5 else "z"
        rows.append(f'<div class="r"><span>{T.esc(L(en, ar))} <small style="color:#6F6A78">/{mx}</small></span><b class="{cls}">{v:+.0f}</b></div>')
    col = "#4ADE80" if s["dir"] > 0 and s["total"] >= 40 else "#F87171" if s["dir"] < 0 and s["total"] >= 40 else "#C4B5FD"
    return (f'<div class="nie-score">{"".join(rows)}<div class="r t"><span>{T.esc(L("Total Score", "المجموع"))}</span><b>{s["total"]}/100</b></div>'
            f'<div class="lab" style="color:{col}">{T.esc(L(*s["label"]))} — {s["total"]}/100</div></div>')


def _detail(a, chg, sec_chg, titles_ar):
    n = a["n"]
    ar = is_ar()
    title = (titles_ar.get(n["title"]) if ar and titles_ar else None) or n["title"]
    en_ev, ar_ev, ic, hz = NI.EVENT.get(a["event"], NI.EVENT["other"])
    sen, sar, scol = NI.SENT[a["lab"]]
    who = a["direct"][0] if a["direct"] else "SPY"
    imp_word = {"bull": ("Positive Impact", "أثر إيجابي"), "bear": ("Negative Impact", "أثر سلبي"), "neutral": ("Neutral Impact", "أثر محايد")}[a["lab"]]
    tags = (f'<span class="nie-tag" style="color:{scol};border-color:{scol}55;background:{scol}14">{T.esc(who)} — {T.esc(L(*imp_word))}</span>'
            f'<span class="nie-tag" style="color:#C4B5FD;border-color:#C4B5FD44;background:#7C3AED14">{T.icon(ic)}{T.esc(L(en_ev, ar_ev))}</span>')
    also = T.also_badge(n.get("also"), ar)
    ui.html(f'<div class="nie-card">{T.news_thumb(n, big=True)}<div class="tx"><div class="tt"><a href="{T.esc(n.get("link") or "#")}" '
            f'target="_blank">{T.esc(title)}</a></div><div class="mt">{T.esc(n.get("source") or "")}{also} · '
            f'{T.time_ago(n["time"], ar) if pd.notna(n.get("time")) else ""}</div><div class="hd">{tags}</div></div></div>')
    # the facts, as in a research note
    secs = " / ".join(dict.fromkeys(x for sec, sub in a["sectors"] for x in (L(sec, SECTOR_AR.get(sec, sec)), sub) if x))
    if not secs and a["macro"]:                    # macro news: the sectors it usually helps and hurts most
        eff = a["macro"][3]
        nm = lambda sec: L(sec, SECTOR_AR.get(sec, sec))
        up = [nm(k) for k, e in sorted(eff.items(), key=lambda x: -x[1]) if e >= 1][:3]
        dn = [nm(k) for k, e in sorted(eff.items(), key=lambda x: x[1]) if e <= -1][:2]
        secs = " · ".join(([L("Helped: ", "يستفيد: ") + "، ".join(up) if is_ar() else "Helped: " + ", ".join(up)] if up else [])
                          + ([L("Hurt: ", "يتضرر: ") + "، ".join(dn) if is_ar() else "Hurt: " + ", ".join(dn)] if dn else []))
    secs = secs or L("The whole market", "السوق كله")
    rel = ", ".join(a["indirect"][:5]) or "—"
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
    cells = [_fact(L("Event type", "نوع الخبر"), T.esc(L(en_ev, ar_ev))),
             _fact(L("Expected impact", "التأثير المتوقع"), f'<span style="color:{scol}">{T.esc(L(sen, sar))}</span>'),
             _fact(L("Time horizon", "الأفق الزمني"), T.esc(L(*hzt))),
             _fact(L("Impact severity", "شدة التأثير"), f"{a['severity']}/10 <small style='color:#9D97A5'>({a['impact']:.0f}/100 · {T.esc(impact_level(a['impact']))})</small>"),
             _fact(L("Confidence", "الثقة"), f"{a['confidence']}%"),
             _fact(L("Materiality", "أهمية الخبر للسهم"), f"{a['materiality']:.1f}/10 · " + T.esc(
                 L("material", "مهم فعلاً") if a["materiality"] >= 6 else L("worth watching", "يستحق المتابعة") if a["materiality"] >= 4 else L("mostly noise", "غالباً ضوضاء"))),
             _fact(L("Sectors affected", "القطاعات المتأثرة"), T.esc(secs)),
             _fact(L("Related companies", "شركات مرتبطة"), T.esc(rel)),
             _fact(L("Reason", "السبب"), T.esc(reason)),
             _fact(L("Is the news new?", "هل الخبر جديد؟"), T.esc(new)),
             _fact(L("Did the price move before the news?", "هل تحرك السعر قبل الخبر؟"), T.esc(mb)),
             _fact(L("Market regime", "حالة السوق"), T.esc(L(*NI.REGIME[a["regime"]])))]
    ui.html(f'<div class="nie-grid">{"".join(cells)}</div>')
    ui.html(_score_block(a))
    tabs = st.tabs([L("AI Analysis", "تحليل الذكاء الاصطناعي"), L("Affected Stocks", "الأسهم المتأثرة"), L("Why It Matters", "ليش يهم"),
                    L("Expected Market Impact", "الأثر المتوقع على السوق"), L("Technical Confirmation", "التأكيد الفني"),
                    L("Trading Scenario", "سيناريو التداول")])
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
        _tab_tech(a)
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
        _tile(ic, L("Event", "الحدث"), T.esc(L(en_ev, ar_ev)), T.esc(who)),
        _tile("balance", L("Reading", "القراءة"), f'<span style="color:{scol}">{T.esc(L(sen, sar))}</span> <small>{a["sent"]:+.2f}</small>',
              T.esc(L("from the words and the price", "من الكلمات والسعر"))),
        _tile("bolt", L("Impact", "الأثر"), f"{imp:.0f}<small>/100</small>", T.esc(impact_level(imp)), _bar(imp / 100, _heat(imp / 100))),
        _tile("priority_high", L("Materiality", "الأهمية"), f"{mat:.1f}<small>/10</small>",
              T.esc(L("material", "مهم فعلاً") if mat >= 6 else L("worth watching", "يستحق المتابعة") if mat >= 4 else L("mostly noise", "غالباً ضوضاء")),
              _bar(mat / 10, _heat(mat / 10))),
        _tile("verified", L("Confidence", "الثقة"), f"{conf}<small>%</small>", "", _bar(conf / 100, _heat((conf - 20) / 75))),
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
        ui.html(_note(L("This is the engine’s own reading (rules and numbers). With an AI key (OPENAI_API_KEY in the site’s Secrets) a button here "
                        "asks the AI analyst to explain the story in words.",
                        "هذي قراءة المحرك نفسه (قواعد وأرقام). ولما يكون للموقع مفتاح ذكاء اصطناعي (OPENAI_API_KEY في Secrets) يطلع هنا زر "
                        "يطلب من محلل الذكاء الاصطناعي يشرح الخبر بالكلام."), "auto_awesome"))


def _tab_stocks(a, chg):
    rows = []
    for kind, cls, syms in ((L("Direct", "مباشر"), "dir", a["direct"]), (L("Indirect", "غير مباشر"), "ind", a["indirect"])):
        for sym in syms:
            name, sec, sub = NI.company(sym)
            c = chg.get(sym)
            secn = L(sec, SECTOR_AR.get(sec, sec)) if sec else ""
            rows.append(f'<a class="nx-row" href="stock?symbol={T.esc(sym)}" target="_self">{T.logo_obj(sym, 36)}'
                        f'<div style="min-width:0"><div class="tk">{T.esc(sym)}</div><div class="nm" dir="auto">{T.esc(name)}</div></div>'
                        f'<span class="nx-badge {cls}">{T.esc(kind)}</span>'
                        f'<div class="sc">{T.esc(secn)}<span>{T.esc(sub or "")}</span></div>{T.pill(c[1] if c else None)}</a>')
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
        etf_of = {v: k for k, v in U.SECTOR_ETFS.items()}
        rows = []
        for sec, e in sorted(eff.items(), key=lambda x: -x[1]):
            etf = etf_of.get(sec)
            c = sec_chg.get(etf) if etf else None
            w = abs(e) / 2 * 50
            bar = (f'<i style="left:50%;width:{w:.0f}%;background:linear-gradient(90deg,#22C55E88,#4ADE80)"></i>' if e > 0 else
                   f'<i style="left:{50 - w:.0f}%;width:{w:.0f}%;background:linear-gradient(90deg,#F87171,#EF444488)"></i>' if e < 0 else "")
            if not c or e == 0:
                ok_ = '<span class="nx-ok z">—</span>'
            elif (c[1] > 0) == (e > 0):
                ok_ = f'<span class="nx-ok y">✓ {T.esc(L("as usual", "مثل العادة"))}</span>'
            else:
                ok_ = f'<span class="nx-ok n">✗ {T.esc(L("not today", "مو اليوم"))}</span>'
            rows.append(f'<div class="nx-sec"><span class="n">{T.esc(L(sec, SECTOR_AR.get(sec, sec)))}</span><div class="nx-div">{bar}</div>'
                        f'<span class="e">{T.esc(etf or "")}</span>{T.pill(c[1] if c else None)}{ok_}</div>')
        ui.html(f'<div class="nx-list">{"".join(rows)}</div>')
        ui.html(_note(L("The bar is a rule of thumb of how the sector usually reacts (left hurt, right helped); the change is its sector fund today.",
                        "الشريط قاعدة عامة لتفاعل القطاع عادةً (يسار يتضرر، يمين يستفيد)، والنسبة حركة صندوق القطاع اليوم."), "info"))
    elif a["direct"]:
        ui.html(_note(L("The story's weight on the stock is its impact score; the related companies usually move less, in the same direction.",
                        "وزن الخبر على السهم هو درجة الأثر، والشركات المرتبطة غالباً تتحرك أقل وبنفس الاتجاه."), "info"))


def _tab_tech(a):
    fa = a["facts"]
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
            tiles.append(_tile("trending_up" if above else "trending_down", L(en, ar_), f"{c / v - 1:+.1%}",
                               T.esc(L(f"{sym} {'above' if above else 'below'} it ({v:,.2f})", f"{sym} {'فوقه' if above else 'تحته'} ({v:,.2f})"))
                               + " " + (ok_((above and d > 0) or (not above and d < 0)) if a["dir"] else "")))
    rv = fa.get("rvol")
    if rv:
        tiles.append(_tile("bar_chart", L("Volume", "حجم التداول"), f"{rv:.1f}<small>×</small>",
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
    fmt = lambda x: f"${x:,.2f}"
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
    foot = (f'<div class="ft"><span>{L("With $1,000:", "بـ 1,000 دولار:")} <b class="lo"><bdi dir="ltr">-${lose:,.0f}</bdi></b> {L("at the invalidation", "عند الإلغاء")} · '
            f'<b class="hi"><bdi dir="ltr">+${win:,.0f}</bdi></b> {L("at the target", "عند الهدف")}</span>'
            f'<span>{L("The price now is", "السعر الحين بعيد")} <b class="bl"><bdi dir="ltr">{gap:.1f}%</bdi></b> {L("from the entry", "عن الدخول")}</span></div>')
    return f'<div class="nx-pm{" rtl" if is_ar() else ""}">{head}{caps}{entry}{track}{now}{foot}</div>'


def _tab_plan(a):
    p = NI.plan(a)
    if not p:
        ui.html(_note(L("No trading scenario: the news and the price do not line up enough (the setup is under 40/100).",
                        "ما فيه سيناريو تداول: الخبر والسعر ما يتفقون كفاية (الفرصة أقل من 40/100)."), "block"))
    else:
        up = p["dir"] > 0
        fmt = lambda x: f"${x:,.2f}"
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


def page_news_intel():
    ui.html(CSS)
    ui.header("neurology", "News Intelligence Engine", "محرك ذكاء الأخبار",
              "Every headline read like an analyst would: the kind of event, bullish or bearish, how material it is, its impact from 0 to 100, "
              "how long it may last, the companies it hits directly and indirectly, and whether the price confirms it — then a setup score "
              "out of 100 with its parts.",
              "كل خبر ينقرأ مثل ما يقرأه المحلل: نوع الحدث، صاعد أو هابط، أهميته، أثره من 0 إلى 100، كم يدوم، الشركات اللي يأثر عليها "
              "مباشرة وغير مباشرة، وهل السعر يؤكده، وبعدين درجة الفرصة من 100 مع أجزائها.")
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.6, 1.2, 1.2, 1], vertical_alignment="bottom")
    hrs = c1.segmented_control(L("Time", "الوقت"), [6, 24, 96], default=24, key="nie_hrs",
                               format_func=lambda h: {6: L("6 hours", "6 ساعات"), 24: L("24 hours", "24 ساعة"), 96: L("4 days", "4 أيام")}[h]) or 24
    ev_keys = [k for k, *_ in NI.EVENTS] + ["market", "other"]
    ui.valid_multi("nie_ev", ev_keys)
    pick_ev = c2.multiselect(L("Event type", "نوع الخبر"), ev_keys, key="nie_ev", placeholder=L("All events", "كل الأحداث"),
                             format_func=lambda k: L(*NI.EVENT[k][:2]))
    sent = c3.segmented_control(L("Sentiment", "الاتجاه"), ["all", "bull", "bear"], default="all", key="nie_sent",
                                format_func=lambda k: L("All", "الكل") if k == "all" else L(*NI.SENT[k][:2])) or "all"
    sort = c4.segmented_control(L("Sort by", "الترتيب"), ["impact", "setup", "new"], default="impact", key="nie_sort",
                                format_func=lambda k: {"impact": L("Impact", "الأثر"), "setup": L("Setup", "الفرصة"), "new": L("Latest", "الأحدث")}[k]) or "impact"
    tr = c5.toggle(L("Translate to Arabic", "ترجمة للعربية"), value=is_ar(), key=f"nie_tr_{'ar' if is_ar() else 'en'}")   # one per language: switching to Arabic turns it on
    with st.spinner(L("Reading the news and the prices...", "يقرأ الأخبار والأسعار...")):
        items = data.market_news(96)
        now = pd.Timestamp.now(tz="UTC")
        items = [n for n in items if pd.notna(n.get("time")) and n["time"] >= now - pd.Timedelta(hours=hrs)][:400]
        tick = sorted({t for n in items[:300] for t in (n.get("tickers") or [])[:2] if t})
        chg = data.quick_changes(tick) if tick else {}
        newsiq.enrich(items, chg)
        items = [n for n in items if not any(k[0] == "opinion" for k in n["iq"].get("keywords", []))]      # opinion pieces out
        mains = [((n.get("tickers") or [None])[0]) for n in items]
        syms = ("SPY",) + tuple(sorted({s for s in mains if s and s != "SPY"}))[:79]
        px = data.history_many(syms, "1y") if syms else {}
        res = NI.analyze_all(items, px, chg, px.get("SPY"), now)
    if not res:
        st.info(L("The news bot has no headlines for this time yet; try a longer time or come back in a few minutes.",
                  "بوت الأخبار ما عنده عناوين لهالوقت للحين، جرّب وقت أطول أو ارجع بعد دقائق."), icon=":material/hourglass_empty:")
        return
    ui.html(_pipeline(len(res), sum(1 for a in res if a["direct"]), sum(1 for a in res if a["event"] == "macro"),
                      sum(1 for a in res if a["setup"]["total"] >= 55)))
    shown = [a for a in res if (not pick_ev or a["event"] in pick_ev) and (sent == "all" or a["lab"] == sent)]
    key_of = {"impact": lambda a: -a["impact"], "setup": lambda a: -a["setup"]["total"],
              "new": lambda a: -(a["n"]["time"].timestamp() if pd.notna(a["n"].get("time")) else 0)}
    shown.sort(key=key_of[sort])
    # headline numbers
    bull, bear = sum(1 for a in shown if a["lab"] == "bull"), sum(1 for a in shown if a["lab"] == "bear")
    high = sum(1 for a in shown if a["impact"] >= 70)
    top_ev = pd.Series([a["event"] for a in shown]).value_counts().index[0] if shown else None
    k = st.columns(4)
    k[0].markdown(T.kpi("newspaper", L("Stories analysed", "أخبار تم تحليلها"), f"{len(shown):,}", L("opinion pieces left out", "بدون مقالات الرأي")), unsafe_allow_html=True)
    k[1].markdown(T.kpi("balance", L("Bullish · Bearish", "صاعد · هابط"), f"{bull} · {bear}", L("by the words and the price", "حسب الكلمات والسعر"),
                        "pos" if bull > bear else "neg" if bear > bull else None), unsafe_allow_html=True)
    k[2].markdown(T.kpi("bolt", L("High impact (70+)", "أثر عالي (70+)"), f"{high}", L("worth your attention now", "تستحق انتباهك الحين"), "neg" if high else None),
                  unsafe_allow_html=True)
    k[3].markdown(T.kpi(NI.EVENT[top_ev][2] if top_ev else "category", L("Most common event", "أكثر نوع خبر"),
                        T.esc(L(*NI.EVENT[top_ev][:2])) if top_ev else "—", L("in this window", "في هالفترة")), unsafe_allow_html=True)
    if not shown:
        st.caption(L("No story matches these filters.", "ما فيه خبر يطابق هالفلاتر."))
        return
    ui.sec("monitoring", "Live Market Intelligence", "ذكاء السوق المباشر")
    rows = shown[:120]
    titles_ar = _translate(tuple(a["n"]["title"] for a in rows)) if tr else {}
    df = pd.DataFrame([{"pic": picture(a), "time": _ny_time(a["n"]["time"]), "stock": _stock_txt(a),
                        "news": (titles_ar.get(a["n"]["title"]) if titles_ar else None) or a["n"]["title"],
                        "event": L(*NI.EVENT[a["event"]][:2]), "impact": int(round(a["impact"])),
                        "sent": _sent_txt(a["lab"]), "score": a["setup"]["total"]} for a in rows])
    cfg = {"pic": st.column_config.ImageColumn("", width="small"),
           "time": st.column_config.TextColumn(L("Time (NY)", "الوقت (نيويورك)"), width="small"),
           "stock": st.column_config.TextColumn(L("Stock", "السهم"), width="small"),
           "news": st.column_config.TextColumn(L("News", "الخبر"), width="large"),
           "event": st.column_config.TextColumn(L("Event", "الحدث")),
           "impact": st.column_config.ProgressColumn(L("Impact", "الأثر"), min_value=0, max_value=100, format="%d"),
           "sent": st.column_config.TextColumn(L("Sentiment", "الاتجاه")),
           "score": st.column_config.ProgressColumn(L("Setup", "الفرصة"), min_value=0, max_value=100, format="%d")}
    def _tone(v):                                      # the sentiment in its colour, the stock in bold
        return LM.css("color:#4ADE80;font-weight:700" if str(v).startswith("▲") else "color:#F87171;font-weight:700" if str(v).startswith("▼")
                      else "color:#C4B5FD")
    bold = LM.css("font-weight:800;color:#FFFFFF")
    try:
        view = df.style.map(_tone, subset=["sent"]).map(lambda v: bold, subset=["stock"])
    except Exception:                                  # an older pandas without Styler.map
        view = df
    try:
        ev = st.dataframe(view, hide_index=True, width="stretch", height=min(44 * len(df) + 42, 560), row_height=44, column_config=cfg,
                          on_select="rerun", selection_mode="single-row", key="nie_tbl")
        sel = list(getattr(getattr(ev, "selection", None), "rows", None) or [])
    except TypeError:                                  # an older Streamlit without row selection
        st.dataframe(df, hide_index=True, width="stretch", column_config=cfg)
        sel = []
    st.caption(L("Tick a row to open the story. Impact: how strongly the news can move its stock (0-100). Setup: the news set against "
                 "momentum, volume, trend and the market (0-100).",
                 "علّم على أي سطر عشان يفتح الخبر. الأثر: قوة الخبر في تحريك سهمه (0-100). الفرصة: الخبر مقابل الزخم والحجم والاتجاه "
                 "والسوق (0-100)."))
    i = sel[0] if sel and sel[0] < len(rows) else 0
    a = rows[i]
    ui.sec("article", "Story analysis", "تحليل الخبر")
    peers_ = sorted({s for s in a["direct"] + a["indirect"]})
    chg2 = dict(chg)
    if peers_:
        chg2.update(data.quick_changes(peers_))
    sec_chg = data.quick_changes(list(U.SECTOR_ETFS)) if a["macro"] else {}
    _detail(a, chg2, sec_chg, titles_ar)

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "17.9"
