"""
theme.py - Design system v4 (A.Alturaifi Pro).
Rule used everywhere: positive = light-green box + dark-green text, negative = light-red box + dark-red text.
Fonts: Plus Jakarta Sans (Latin) + Readex Pro (Arabic). Material Symbols icons. No emoji.
"""
import base64
import hashlib
import html
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

import flags
import mcal

# ---------------------------------------------------------------- palette
BG, CARD, CARD2, BORDER = "#0A0E17", "#111723", "#161D2B", "#222B3B"
TEXT, MUTED = "#E9EDF5", "#8A94A7"
UP, DOWN = "#22C55E", "#EF4444"                     # chart strokes on dark surfaces
ACCENT, VIOLET, CYAN, GOLD, ORANGE, PURPLE = "#3D7BFF", "#8B5CF6", "#22D3EE", "#F5B94A", "#F97316", "#A78BFA"
POS_BG, POS_FG, POS_BD = "#D1E7DD", "#0F5132", "#A3CFBB"   # light green box, dark green text
NEG_BG, NEG_FG, NEG_BD = "#F8D7DA", "#842029", "#F1AEB5"   # light red box, dark red text
ACC_BG, ACC_FG = "#DBEAFE", "#1E3A8A"
VIO_BG, VIO_FG = "#EDE9FE", "#4C1D95"
YEL_BG, YEL_FG = "#FEF3C7", "#854D0E"
ORG_BG, ORG_FG = "#FFEDD5", "#9A3412"
NEU_BG, NEU_FG = "#E2E8F0", "#334155"
FONT = "Plus Jakarta Sans, Readex Pro, system-ui, sans-serif"

# ---------------------------------------------------------------- logo
_MARK = """<defs><linearGradient id="bgA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3D7BFF"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient></defs>
<rect x="0" y="0" width="64" height="64" rx="16" fill="url(#bgA)"/>
<path d="M17 48 L29.5 15.5 Q32 11 34.5 15.5 L47 48" fill="none" stroke="#fff" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M22 37 L30 31 L35 34 L48 24" fill="none" stroke="#22D3EE" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M43 23.2 L48.6 23.6 L48.2 29.2" fill="none" stroke="#22D3EE" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>"""

LOGO_ICON = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{_MARK}</svg>'
LOGO_WORDMARK = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 64" width="300" height="64">{_MARK}
<defs><linearGradient id="tx" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5B8CFF"/><stop offset="1" stop-color="#A78BFA"/></linearGradient></defs>
<text x="78" y="43" font-family="Plus Jakarta Sans, Helvetica Neue, Helvetica, Arial, sans-serif" font-size="31" font-weight="800" fill="#FFFFFF" letter-spacing="-0.5">Alturaifi<tspan dx="9" fill="url(#tx)" font-weight="800" letter-spacing="1">PRO</tspan></text>
</svg>"""

FONT_LATIN, FONT_AR = "'Plus Jakarta Sans'", "'Readex Pro'"
FLAG_US, FLAG_SA = flags.US, flags.SA

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Readex+Pro:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..600,0..1,0&display=block');
html, body, .stApp, .stMarkdown, button, input, textarea, select, label, [data-testid="stMetricValue"], [data-baseweb] {{
  font-family: {FONT_LATIN}, {FONT_AR}, system-ui, sans-serif; }}
.stApp {{ background: {BG}; }}
.stApp::before {{ content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
  background: radial-gradient(900px 520px at 8% -12%, rgba(61,123,255,.16), transparent 60%),
              radial-gradient(760px 480px at 96% -6%, rgba(139,92,246,.13), transparent 60%),
              radial-gradient(700px 480px at 50% 112%, rgba(34,211,238,.06), transparent 60%);
  animation: aurora 22s ease-in-out infinite alternate; }}
.stApp::after {{ content:""; position:fixed; inset:0; z-index:0; pointer-events:none; opacity:.3;
  background-image: linear-gradient(rgba(255,255,255,.022) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.022) 1px, transparent 1px);
  background-size: 52px 52px; animation: gridmove 44s linear infinite; }}
@keyframes aurora {{ 0% {{ transform: translate3d(0,0,0) scale(1); }} 100% {{ transform: translate3d(-3%,2%,0) scale(1.08); }} }}
@keyframes gridmove {{ 0% {{ background-position:0 0,0 0; }} 100% {{ background-position:52px 52px,52px 52px; }} }}
[data-testid="stAppViewContainer"] {{ z-index: 1; }}
header[data-testid="stHeader"] {{ background: rgba(9,13,22,.84); backdrop-filter: blur(18px) saturate(150%); -webkit-backdrop-filter: blur(18px) saturate(150%);
  border-bottom: 1px solid rgba(43,53,72,.85); box-shadow: 0 10px 28px rgba(0,0,0,.25); }}
header[data-testid="stHeader"]::after {{ content:""; position:absolute; left:0; right:0; bottom:-1px; height:1px; pointer-events:none;
  background: linear-gradient(90deg, transparent, rgba(61,123,255,.55), rgba(139,92,246,.45), transparent); }}
[data-testid="stToolbarActions"], [data-testid="stAppDeployButton"], [data-testid="stStatusWidget"], [data-testid="stDecoration"] {{ display:none !important; }}
[data-testid="stElementContainer"]:has(.css-anchor), .element-container:has(.css-anchor) {{ display:none !important; }}
.block-container {{ padding-top: 4.4rem; padding-bottom: 3rem; max-width: 1560px; }}
h1 {{ font-size: 1.8rem !important; font-weight: 800 !important; letter-spacing: -.02em; }}
h2, h3 {{ font-weight: 750 !important; letter-spacing: -.01em; }}
.ms {{ font-family:'Material Symbols Rounded'; font-weight:400; font-style:normal; font-size:1.15em; line-height:1; display:inline-block;
  vertical-align:-0.2em; letter-spacing:normal; text-transform:none; white-space:nowrap; font-feature-settings:'liga'; }}
[data-testid="stMetric"] {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:12px 16px; }}
[data-testid="stMetricLabel"] {{ color:{MUTED}; }}
[data-testid="stMetricValue"] {{ font-weight:750; letter-spacing:-.01em; }}
[data-testid="stExpander"] details {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px; }}
[data-testid="stTabs"] button[role="tab"] {{ font-weight:650; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius:16px !important; }}
.stButton > button, .stDownloadButton > button {{ border-radius:10px; font-weight:650; }}
.muted {{ color:{MUTED}; }} .acc {{ color:#7EA6FF; }}
.upt {{ color:{UP}; }} .dnt {{ color:{DOWN}; }}
.num {{ font-variant-numeric: tabular-nums; direction:ltr; display:inline-block; }}
.card {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:16px; padding:16px 18px; margin-bottom:12px; }}
.sec {{ display:flex; align-items:center; gap:8px; font-size:.8rem; letter-spacing:.1em; text-transform:uppercase; color:{MUTED}; margin:26px 0 10px; font-weight:750; }}
.sec .ms {{ color:#fff; background:linear-gradient(135deg,{ACCENT},{VIOLET}); border-radius:8px; padding:4px; font-size:1.05rem; }}
.sec::after {{ content:""; flex:1; height:1px; background:linear-gradient(90deg, {BORDER}, transparent); }}
.page-title {{ display:flex; align-items:center; gap:12px; margin:4px 0 2px; }}
.page-title .ms {{ font-size:1.9rem; color:#fff; background:linear-gradient(135deg,{ACCENT},{VIOLET}); border-radius:12px; padding:7px; }}
.page-title h1 {{ margin:0 !important; padding:0 !important; }}
.page-sub {{ color:{MUTED}; font-size:.92rem; margin:2px 0 12px; }}
/* ---------- the pastel rule ---------- */
.pos {{ background:{POS_BG} !important; color:{POS_FG} !important; }}
.neg {{ background:{NEG_BG} !important; color:{NEG_FG} !important; }}
.pill {{ display:inline-block; min-width:74px; text-align:center; padding:4px 9px; border-radius:8px; font-weight:750; font-size:.82rem;
  font-variant-numeric: tabular-nums; direction:ltr; }}
.pill.pos {{ border:1px solid {POS_BD}; }} .pill.neg {{ border:1px solid {NEG_BD}; }}
.pill.neu {{ background:rgba(138,148,167,.15); color:{MUTED}; }}
.badge {{ display:inline-flex; align-items:center; gap:4px; padding:3px 10px; border-radius:20px; font-size:.76rem; font-weight:700; margin:2px 4px 2px 0; }}
.b-up {{ background:{POS_BG}; color:{POS_FG}; }} .b-down {{ background:{NEG_BG}; color:{NEG_FG}; }}
.b-neu {{ background:rgba(138,148,167,.16); color:#B8C0CE; }} .b-acc {{ background:{ACC_BG}; color:{ACC_FG}; }}
.b-vio {{ background:{VIO_BG}; color:{VIO_FG}; }} .b-gold {{ background:{YEL_BG}; color:{YEL_FG}; }} .b-org {{ background:{ORG_BG}; color:{ORG_FG}; }}
/* tiles */
.tiles {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(196px,1fr)); gap:10px; }}
.tile {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:11px 13px;
  transition: transform .15s, box-shadow .15s; }}
.tile:hover {{ transform: translateY(-2px); box-shadow: 0 10px 24px rgba(0,0,0,.35); }}
.tile.pos {{ background: linear-gradient(180deg, #DDF0E6, {POS_BG}) !important; border-color:{POS_BD}; }}
.tile.neg {{ background: linear-gradient(180deg, #FBE4E6, {NEG_BG}) !important; border-color:{NEG_BD}; }}
.tile.acc {{ background: linear-gradient(180deg, #E8F0FE, {ACC_BG}); border-color:#BFD3FB; color:{ACC_FG}; }}
.t-name {{ color:{MUTED}; font-size:.78rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.tile.pos .t-name {{ color:#3E6F55; }} .tile.neg .t-name {{ color:#8E4A52; }} .tile.acc .t-name {{ color:#4B5E8C; }}
.t-row {{ display:flex; justify-content:space-between; align-items:flex-end; gap:6px; direction:ltr; }}
.t-val {{ font-size:1.18rem; font-weight:800; margin-top:2px; font-variant-numeric: tabular-nums; }}
.t-chg {{ font-size:.8rem; font-weight:700; margin-top:2px; white-space:nowrap; font-variant-numeric: tabular-nums; }}
.t-sub {{ color:{MUTED}; font-size:.7rem; margin-top:3px; }}
.tile.pos .t-sub {{ color:#4F7A63; }} .tile.neg .t-sub {{ color:#98545B; }} .tile.acc .t-sub {{ color:#56689A; }}
/* hero */
.hero {{ position:relative; height:290px; border-radius:20px; overflow:hidden; border:1px solid {BORDER}; margin-bottom:14px;
  background: linear-gradient(120deg, #060c1c, #0c1d3f, #1c1543, #071a33); background-size:300% 300%; animation: sky 20s ease-in-out infinite; }}
@keyframes sky {{ 0% {{ background-position:0% 50%; }} 50% {{ background-position:100% 50%; }} 100% {{ background-position:0% 50%; }} }}
.hero svg.city {{ position:absolute; left:0; right:0; bottom:0; width:100%; height:100%; }}
.hero .content {{ position:absolute; inset:0; padding:30px 34px; display:flex; flex-direction:column;
  background: linear-gradient(90deg, rgba(10,14,23,.88) 0%, rgba(10,14,23,.35) 55%, rgba(10,14,23,0) 100%); }}
.rtl .hero .content {{ background: linear-gradient(270deg, rgba(10,14,23,.88) 0%, rgba(10,14,23,.35) 55%, rgba(10,14,23,0) 100%); }}
.hero .eyebrow {{ color:{CYAN}; font-weight:700; letter-spacing:.2em; font-size:.74rem; text-transform:uppercase; }}
.hero .title {{ font-size:2.45rem; font-weight:800; line-height:1.1; margin:8px 0 6px; color:#fff; letter-spacing:-.02em; }}
.hero .title b {{ background: linear-gradient(90deg,{ACCENT},{VIOLET},{CYAN}); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.hero .tagline {{ color:#C7CFDD; max-width:560px; font-size:.98rem; line-height:1.65; }}
.hero .chips {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:16px; direction:ltr; }}
.rtl .hero .chips {{ justify-content:flex-end; }}
.hero .chip {{ background:rgba(17,23,35,.8); border:1px solid {BORDER}; backdrop-filter: blur(6px); border-radius:10px; padding:6px 10px; font-size:.82rem;
  font-variant-numeric: tabular-nums; display:inline-flex; align-items:center; gap:7px; }}
.hero .chip b {{ color:#fff; }} .hero .chip .pill {{ min-width:0; padding:2px 7px; font-size:.75rem; }}
/* ticker tape */
.tape {{ direction:ltr; overflow:hidden; white-space:nowrap; border:1px solid {BORDER}; border-radius:12px; background:rgba(17,23,35,.85);
  margin-bottom:14px; mask-image: linear-gradient(90deg, transparent, #000 4%, #000 96%, transparent); }}
.tape .track {{ display:inline-flex; gap:26px; padding:8px 0; animation: tape 70s linear infinite; }}
.tape:hover .track {{ animation-play-state: paused; }}
.tape .it {{ font-size:.84rem; font-variant-numeric: tabular-nums; display:inline-flex; align-items:center; gap:7px; }}
.tape .it b {{ color:#fff; }} .tape .it .pill {{ min-width:0; padding:2px 7px; font-size:.74rem; }}
@keyframes tape {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
/* company logo circle + rows */
.lg {{ position:relative; flex:none; display:inline-flex; align-items:center; justify-content:center; border-radius:50%; overflow:hidden;
  color:#fff; font-weight:800; letter-spacing:-.02em; vertical-align:middle; box-shadow: 0 0 0 1px rgba(255,255,255,.08); }}
.lg img {{ width:100%; height:100%; object-fit:contain; background:#fff; padding:12%; box-sizing:border-box; }}
.co {{ display:flex; align-items:center; gap:10px; min-width:0; }}
.co .nm {{ min-width:0; }} .co .tk {{ font-weight:800; color:#fff; }}
.co .sub {{ color:{MUTED}; font-size:.76rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:190px; }}
a.lnk {{ color:inherit !important; text-decoration:none !important; }} a.lnk:hover .tk {{ color:#7EA6FF; text-decoration:underline; }}
.rowlist {{ display:flex; flex-direction:column; }}
.rw {{ display:grid; grid-template-columns: minmax(0,1fr) auto auto; gap:12px; align-items:center; padding:9px 4px; border-bottom:1px solid {BORDER}; direction:ltr; }}
.rw:last-child {{ border-bottom:none; }} .rw:hover {{ background:rgba(61,123,255,.06); border-radius:10px; }}
.px {{ font-variant-numeric: tabular-nums; font-weight:700; text-align:right; }}
.meter {{ height:5px; border-radius:3px; background:{BORDER}; overflow:hidden; margin-top:4px; }}
.meter span {{ display:block; height:100%; background:linear-gradient(90deg,{ACCENT},{VIOLET}); }}
.mcard {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:16px; padding:14px 14px 6px; height:100%; }}
.mcard .hd {{ display:flex; align-items:center; gap:8px; font-weight:750; margin-bottom:6px; }}
.mcard .hd .ms {{ color:#fff; background:linear-gradient(135deg,{ACCENT},{VIOLET}); border-radius:8px; padding:4px; font-size:1.05rem; }}
.mcard .hd .cnt {{ margin-inline-start:auto; color:{MUTED}; font-size:.75rem; font-weight:600; }}
.lead {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:10px; }}
.lc {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:12px; direction:ltr; }}
.lc .top {{ display:flex; justify-content:space-between; align-items:center; gap:8px; }}
.lc .bot {{ display:flex; justify-content:space-between; align-items:flex-end; margin-top:10px; gap:8px; }}
.lc .rank {{ color:{MUTED}; font-size:.75rem; font-weight:700; }}
/* quote */
.q-name {{ color:{MUTED}; font-size:.95rem; }}
.q-price {{ font-size:2.6rem; font-weight:800; line-height:1.15; font-variant-numeric: tabular-nums; direction:ltr; display:inline-block; letter-spacing:-.02em; }}
.q-chg {{ font-size:1rem; font-weight:800; direction:ltr; display:inline-block; padding:4px 10px; border-radius:9px; }}
.q-chg.pos {{ border:1px solid {POS_BD}; }} .q-chg.neg {{ border:1px solid {NEG_BD}; }} .q-chg.neu {{ background:rgba(138,148,167,.15); color:{MUTED}; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(134px,1fr)); gap:8px; margin:8px 0; }}
.stat {{ background:{CARD}; border:1px solid {BORDER}; border-radius:10px; padding:8px 11px; }}
.stat .l {{ color:{MUTED}; font-size:.72rem; }} .stat .v {{ font-weight:700; font-size:.93rem; }}
.range {{ position:relative; height:6px; background:linear-gradient(90deg,{DOWN},{GOLD},{UP}); border-radius:3px; margin:10px 0 4px; opacity:.85; }}
.range .dot {{ position:absolute; top:-5px; width:16px; height:16px; border-radius:50%; background:#fff; border:3px solid {BG}; }}
.plan {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:8px; }}
.plan .p {{ background:{CARD2}; border-radius:12px; padding:10px 13px; border:1px solid {BORDER}; }}
.plan .p .l {{ color:{MUTED}; font-size:.72rem; font-weight:600; }} .plan .p .v {{ font-size:1.05rem; font-weight:800; direction:ltr; display:inline-block; }}
.plan .p.pos, .plan .p.neg, .plan .p.acc {{ border-color:transparent; }}
.plan .p.pos .l {{ color:#3E6F55; }} .plan .p.neg .l {{ color:#8E4A52; }}
.plan .p.acc {{ background:{ACC_BG}; color:{ACC_FG}; }} .plan .p.acc .l {{ color:#4B5E8C; }}
/* profile */
.prof {{ display:grid; grid-template-columns: repeat(auto-fill,minmax(220px,1fr)); gap:10px; }}
.prof .it {{ background:{CARD}; border:1px solid {BORDER}; border-radius:12px; padding:10px 12px; }}
.prof .it .l {{ color:{MUTED}; font-size:.72rem; display:flex; gap:6px; align-items:center; }}
.prof .it .v {{ font-weight:650; margin-top:3px; }}
.desc {{ line-height:1.9; font-size:.97rem; color:#D5DBE6; }}
/* news */
.news {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:14px 16px; margin-bottom:10px; transition:border-color .15s; }}
.news:hover {{ border-color:{ACCENT}; }}
.news a.t {{ color:{TEXT}; text-decoration:none; font-weight:700; font-size:1rem; line-height:1.65; }}
.news a.t:hover {{ color:#7EA6FF; }}
.news .meta {{ color:{MUTED}; font-size:.78rem; margin-top:4px; }}
.news .sum {{ color:{MUTED}; font-size:.88rem; margin-top:6px; line-height:1.75; }}
.news .nh {{ display:flex; gap:14px; align-items:flex-start; }}
.news .nb {{ flex:1; min-width:0; }}
.news.hasiq {{ border-inline-start: 4px solid var(--iqd); }}
.iq {{ flex:none; width:88px; text-align:center; border-radius:12px; padding:7px 6px 6px; background:var(--iqb); color:var(--iqf); border:1px solid var(--iqd); cursor:help; }}
.iq .n {{ font-size:1.35rem; font-weight:800; line-height:1.1; direction:ltr; font-variant-numeric: tabular-nums; }}
.iq .n small {{ font-size:.68rem; font-weight:700; opacity:.7; }}
.iq .l {{ font-size:.64rem; font-weight:800; margin-top:2px; line-height:1.25; }}
.iq .bar {{ height:4px; border-radius:3px; background:rgba(0,0,0,.09); margin-top:5px; overflow:hidden; direction:ltr; }}
.iq .bar i {{ display:block; height:100%; background:var(--iqf); opacity:.55; border-radius:3px; }}
.kw {{ display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }}
.kwc {{ display:inline-flex; align-items:center; gap:5px; padding:3px 10px 3px 8px; border-radius:20px; font-size:.74rem; font-weight:700;
  background:rgba(61,123,255,.1); color:#BFD3FB; border:1px solid rgba(61,123,255,.26); white-space:nowrap; }}
.kwc .ms {{ font-size:.95rem; color:#7EA6FF; }}
.kwc.ent {{ background:rgba(139,92,246,.1); color:#D9CCFC; border-color:rgba(139,92,246,.3); }} .kwc.ent .ms {{ color:#A78BFA; }}
.kwc.op {{ background:rgba(138,148,167,.12); color:#B8C0CE; border-color:rgba(138,148,167,.26); }} .kwc.op .ms {{ color:#8A94A7; }}
.iqleg {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; font-size:.78rem; font-weight:700; }}
.iqleg .sc {{ display:flex; gap:3px; direction:ltr; }}
.iqleg .sc span {{ width:30px; height:24px; border-radius:6px; display:inline-flex; align-items:center; justify-content:center; font-size:.74rem; font-weight:800; }}
.aff {{ margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; align-items:center; }}
.aff .lbl {{ color:{MUTED}; font-size:.74rem; margin-inline-end:4px; }}
.tkc {{ direction:ltr; display:inline-flex; gap:6px; align-items:center; border-radius:20px; padding:3px 10px 3px 3px; font-size:.78rem; font-weight:800;
  border:1px solid {BORDER}; background:{CARD2}; color:{TEXT}; font-variant-numeric: tabular-nums; text-decoration:none !important; }}
.tkc.pos {{ border-color:{POS_BD}; }} .tkc.neg {{ border-color:{NEG_BD}; }}
.story {{ position:relative; background: linear-gradient(135deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:16px; padding:16px 18px; height:100%; }}
.story .rank {{ position:absolute; top:10px; inset-inline-end:14px; font-size:1.9rem; font-weight:800; color:rgba(61,123,255,.25); }}
.story a.t {{ color:#fff; text-decoration:none; font-weight:750; font-size:1.02rem; line-height:1.6; display:block; margin-inline-end:36px; }}
.story a.t:hover {{ color:#7EA6FF; }}
.status {{ display:inline-flex; align-items:center; gap:7px; font-size:.8rem; padding:6px 12px; border-radius:20px; background:{CARD}; border:1px solid {BORDER}; }}
.dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; }}
.dot.live {{ background:{UP}; animation: pulse 1.8s infinite; }} .dot.pre {{ background:{GOLD}; }} .dot.closed {{ background:{DOWN}; }}
@keyframes pulse {{ 0% {{ box-shadow:0 0 0 0 rgba(34,197,94,.6); }} 70% {{ box-shadow:0 0 0 8px rgba(34,197,94,0); }} 100% {{ box-shadow:0 0 0 0 rgba(34,197,94,0); }} }}
.wl {{ font-size:.82rem; text-align:right; padding-top:4px; line-height:1.25; direction:ltr; }}
.check {{ padding:9px 0; border-bottom:1px solid {BORDER}; font-size:.9rem; display:flex; gap:10px; align-items:flex-start; }}
.ico {{ flex:none; width:26px; height:26px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; }}
.ico .ms {{ font-size:1.05rem; vertical-align:0; }}
.summary li {{ margin-bottom:6px; line-height:1.8; }}
.kpi {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:12px 14px; height:100%; }}
.kpi.pos, .kpi.neg {{ border-color:transparent; }}
.kpi .l {{ color:{MUTED}; font-size:.75rem; font-weight:650; display:flex; gap:6px; align-items:center; }}
.kpi.pos .l {{ color:#3E6F55; }} .kpi.neg .l {{ color:#8E4A52; }}
.kpi .v {{ font-size:1.25rem; font-weight:800; margin-top:6px; display:flex; align-items:center; gap:8px; direction:ltr; }}
.kpi .s {{ font-size:.8rem; margin-top:4px; font-weight:650; }}
.kpi:not(.pos):not(.neg):not(.acc) .v {{ color:#fff; }}
.kpi.acc {{ background:linear-gradient(180deg,#E8F0FE,{ACC_BG}); color:{ACC_FG}; border-color:transparent; }} .kpi.acc .l {{ color:#4B5E8C; }}
/* rating meter (technicals) */
.rmeter {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:16px; padding:16px; }}
.rmeter .rt {{ color:{MUTED}; font-size:.78rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }}
.rmeter .rv {{ display:inline-block; margin:8px 0 14px; padding:5px 12px; border-radius:10px; font-weight:800; font-size:1.15rem; }}
.rbar {{ position:relative; display:grid; grid-template-columns:repeat(5,1fr); gap:4px; height:10px; direction:ltr; }}
.rbar span {{ border-radius:6px; }}
.rbar i {{ position:absolute; top:-9px; width:0; height:0; border-left:8px solid transparent; border-right:8px solid transparent; border-top:10px solid #fff;
  filter: drop-shadow(0 2px 3px rgba(0,0,0,.5)); }}
.rlab {{ display:grid; grid-template-columns:repeat(5,1fr); font-size:.66rem; color:{MUTED}; margin-top:6px; text-align:center; direction:ltr; }}
.rcnt {{ display:flex; gap:6px; margin-top:12px; flex-wrap:wrap; }}
/* price ladder */
.ladder {{ display:flex; flex-direction:column; gap:5px; direction:ltr; }}
.lr {{ display:grid; grid-template-columns: 70px 1fr auto; gap:10px; align-items:center; padding:7px 10px; border-radius:10px; background:{CARD};
  border:1px solid {BORDER}; font-variant-numeric: tabular-nums; }}
.lr .ln {{ font-weight:800; font-size:.8rem; }} .lr .lp {{ font-weight:700; }}
.lr.res .ln {{ color:#F87171; }} .lr.sup .ln {{ color:#4ADE80; }} .lr.piv .ln {{ color:#93C5FD; }}
.lr.now {{ background:linear-gradient(90deg, rgba(61,123,255,.3), rgba(139,92,246,.25)); border-color:{ACCENT}; }}
.lr.now .ln, .lr.now .lp {{ color:#fff; }}
/* sector cards / breadth */
.secgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(172px,1fr)); gap:10px; }}
.sc {{ border-radius:14px; padding:11px 12px; border:1px solid transparent; }}
.sc .h {{ display:flex; justify-content:space-between; font-weight:700; font-size:.8rem; }} .sc .v {{ font-size:1.25rem; font-weight:800; margin-top:4px; direction:ltr; }}
.sc .f {{ display:flex; gap:8px; font-size:.7rem; font-weight:700; margin-top:4px; direction:ltr; opacity:.85; }}
.bars .b {{ margin:10px 0; }} .bars .b .t {{ display:flex; justify-content:space-between; font-size:.82rem; font-weight:650; }}
.bars .b .trk {{ height:10px; border-radius:6px; background:{BORDER}; overflow:hidden; margin-top:5px; }}
.bars .b .trk span {{ display:block; height:100%; border-radius:6px; }}
.adbar {{ display:flex; height:14px; border-radius:8px; overflow:hidden; gap:3px; direction:ltr; }}
.adbar span {{ display:block; height:100%; }}
/* options chain */
.chain {{ width:100%; border-collapse:separate; border-spacing:0; font-size:.8rem; direction:ltr; font-variant-numeric: tabular-nums; }}
.chain th {{ position:sticky; top:0; background:{CARD2}; color:{MUTED}; font-weight:650; padding:7px 6px; text-align:right; border-bottom:1px solid {BORDER}; }}
.chain th.side {{ text-align:center; font-size:.84rem; }}
.chain td {{ padding:6px 6px; text-align:right; border-bottom:1px solid rgba(34,43,59,.6); }}
.chain td.k {{ text-align:center; font-weight:800; color:#fff; background:{CARD2}; }}
.chain tr:hover td {{ background:rgba(61,123,255,.08); }}
.chain td.itm-c {{ background:rgba(209,231,221,.10); }} .chain td.itm-p {{ background:rgba(248,215,218,.10); }}
.chain tr.atm td {{ border-top:2px solid {ACCENT}; }}
.chain .cp {{ padding:1px 6px; border-radius:6px; font-weight:700; }}
.chainwrap {{ max-height:560px; overflow:auto; border:1px solid {BORDER}; border-radius:14px; }}
/* academy */
.courses {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(270px,1fr)); gap:14px; }}
.course {{ display:block; text-decoration:none !important; color:{TEXT} !important; background:{CARD}; border:1px solid {BORDER}; border-radius:18px; overflow:hidden;
  transition: transform .18s, border-color .18s, box-shadow .18s; border-top:4px solid var(--lv, {ACCENT}); height:100%; }}
.course:hover {{ transform: translateY(-4px); box-shadow: 0 12px 30px rgba(61,123,255,.18); }}
.course .art {{ height:150px; position:relative; overflow:hidden; }} .course .art svg {{ width:100%; height:100%; display:block; }}
.course .body {{ padding:14px 16px 16px; }}
.course .ttl {{ font-weight:800; font-size:1.05rem; line-height:1.4; }}
.course .tag {{ color:{MUTED}; font-size:.85rem; margin-top:6px; line-height:1.6; }}
.course .meta {{ display:flex; gap:6px; margin-top:10px; flex-wrap:wrap; }}
.course .play {{ position:absolute; inset-inline-end:14px; bottom:12px; width:40px; height:40px; border-radius:50%; background:rgba(255,255,255,.95);
  display:flex; align-items:center; justify-content:center; color:{BG}; }}
.course .prog {{ height:6px; background:{BORDER}; border-radius:3px; overflow:hidden; margin-top:10px; }}
.course .prog span {{ display:block; height:100%; background:var(--lv, {ACCENT}); }}
.b-beg {{ background:{POS_BG}; color:{POS_FG}; }} .b-ess {{ background:{YEL_BG}; color:{YEL_FG}; }}
.b-int {{ background:{ORG_BG}; color:{ORG_FG}; }} .b-adv {{ background:{NEG_BG}; color:{NEG_FG}; }}
[class*="st-key-crs_"], [class*="st-key-nxt_"] {{ position:relative; }}
[class*="st-key-crs_"] [data-testid="stElementContainer"], [class*="st-key-nxt_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-crs_"] .stButton, [class*="st-key-nxt_"] .stButton {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; }}
[class*="st-key-crs_"] .stButton button, [class*="st-key-nxt_"] .stButton button {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
[class*="st-key-crs_"]:hover .course, [class*="st-key-nxt_"]:hover .course {{ transform: translateY(-4px); box-shadow: 0 12px 30px rgba(61,123,255,.18); }}
.dash {{ display:grid; grid-template-columns: 240px 1fr 1fr; gap:14px; }}
.dcard {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:18px; padding:16px 18px; }}
.dcard .dt {{ color:{MUTED}; font-size:.78rem; font-weight:750; letter-spacing:.06em; text-transform:uppercase; margin-bottom:10px; }}
.lvl {{ margin:10px 0; }} .lvl .t {{ display:flex; justify-content:space-between; font-size:.85rem; font-weight:700; }}
.lvl .trk {{ height:10px; border-radius:6px; background:{BORDER}; overflow:hidden; margin-top:6px; }} .lvl .trk span {{ display:block; height:100%; border-radius:6px; }}
.lesson {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:18px; padding:22px 24px; }}
.lesson h3 {{ margin-top:0 !important; }} .lesson p, .lesson li {{ line-height:1.9; font-size:1rem; color:#D5DBE6; }}
.take {{ border-inline-start:3px solid {CYAN}; background:rgba(34,211,238,.07); padding:10px 14px; border-radius:10px; margin-top:12px; }}
.steps {{ display:flex; gap:6px; margin:6px 0 14px; }}
.steps span {{ flex:1; height:6px; border-radius:3px; background:{BORDER}; }} .steps span.on {{ background:linear-gradient(90deg,{ACCENT},{VIOLET}); }}
.gl {{ border-bottom:1px solid {BORDER}; padding:12px 2px; }} .gl b {{ font-size:1rem; }} .gl .d {{ color:#C9D0DC; line-height:1.8; margin-top:4px; }}
.log {{ display:flex; gap:10px; align-items:center; padding:8px 0; border-bottom:1px solid {BORDER}; font-size:.86rem; }}
.foot {{ color:{MUTED}; font-size:.75rem; text-align:center; margin-top:40px; padding-top:14px; border-top:1px solid {BORDER}; }}
/* heatmap (TradingView style) */
.hmwrap {{ background:#0B0F19; border:1px solid {BORDER}; border-radius:16px; padding:8px; overflow:hidden; }}
.hm {{ width:100%; height:auto; display:block; direction:ltr; }}
.hm text {{ font-family:{FONT_LATIN}, {FONT_AR}, sans-serif; pointer-events:none; }}
.hm .tk {{ fill:#fff; font-weight:800; text-anchor:middle; }}
.hm .pc {{ fill:#fff; font-weight:600; text-anchor:middle; opacity:.93; }}
.hm .gh {{ fill:#C9CED8; font-size:12.5px; font-weight:700; }}
.hm .gc {{ font-size:12px; font-weight:800; }}
.hm a:hover .tl {{ stroke:#fff; stroke-width:2; filter:brightness(1.15); }}
.hmlegend {{ display:flex; justify-content:center; gap:3px; margin:8px 0 2px; direction:ltr; flex-wrap:wrap; }}
.hmlegend span {{ min-width:56px; padding:4px 6px; text-align:center; font-size:.74rem; font-weight:800; color:#fff; border-radius:4px; }}
/* trading dashboard (journal style) */
.tdk {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(168px,1fr)); gap:10px; margin-bottom:12px; }}
.tdc {{ background: linear-gradient(180deg,{CARD2},{CARD}); border:1px solid {BORDER}; border-radius:14px; padding:12px 14px; display:flex; flex-direction:column; min-height:172px; }}
.tdc .h {{ color:{MUTED}; font-size:.66rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; }}
.tdc .big {{ font-size:1.45rem; font-weight:800; margin-top:12px; direction:ltr; }}
.tdc svg {{ display:block; margin:6px auto 0; }}
.pbox {{ display:inline-block; padding:3px 10px; border-radius:10px; font-weight:800; direction:ltr; font-variant-numeric:tabular-nums; }}
.pbox.neu {{ background:rgba(138,148,167,.16); color:#C9D0DC; }}
.chip2 {{ display:inline-block; margin-top:8px; padding:2px 9px; border-radius:12px; background:rgba(138,148,167,.16); color:#C9D0DC; font-size:.7rem; font-weight:700; }}
.tdc .foot2 {{ margin-top:auto; padding-top:10px; border-top:1px solid {BORDER}; display:flex; gap:18px; font-size:.66rem; color:{MUTED}; font-weight:800; letter-spacing:.05em; }}
.tdc .foot2 b {{ display:block; font-size:.86rem; letter-spacing:0; margin-top:2px; direction:ltr; }}
.tdc .wl2 {{ display:flex; justify-content:center; gap:8px; font-size:.8rem; font-weight:800; margin-top:2px; direction:ltr; }}
.tdc .goal {{ margin-top:auto; padding-top:8px; }}
.tdc .goal .gt {{ display:flex; justify-content:space-between; font-size:.64rem; color:{MUTED}; font-weight:700; }}
.tdc .goal .gb {{ height:4px; border-radius:3px; background:{BORDER}; margin-top:4px; overflow:hidden; }}
.tdc .goal .gb span {{ display:block; height:100%; background:{CYAN}; border-radius:3px; }}
.tdc .goal.met .gb span {{ background:{UP}; }}
.tdc .split {{ display:flex; height:8px; border-radius:5px; overflow:hidden; gap:3px; margin:12px 0 8px; direction:ltr; }}
.tdc .vals {{ display:flex; justify-content:space-between; gap:6px; font-size:.8rem; font-weight:800; direction:ltr; }}
.tdp {{ background: linear-gradient(180deg,{CARD2},{CARD}); border:1px solid {BORDER}; border-radius:16px; padding:14px 16px; margin-bottom:12px; }}
.tdp .tt {{ font-weight:800; font-size:1rem; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; gap:8px; }}
.tdp .tt .muted {{ font-size:.78rem; font-weight:600; }}
.rtab {{ width:100%; border-collapse:collapse; font-size:.84rem; direction:ltr; }}
.rtab th {{ color:{MUTED}; font-size:.66rem; letter-spacing:.08em; text-transform:uppercase; text-align:left; padding:6px 4px; border-bottom:1px solid {BORDER}; }}
.rtab td {{ padding:7px 4px; border-bottom:1px solid rgba(34,43,59,.6); font-weight:700; }}
.rtab td:last-child, .rtab th:last-child {{ text-align:right; }}
.rtab tr:hover td {{ background:rgba(61,123,255,.06); }}
.rtab a {{ color:#fff !important; text-decoration:none !important; }} .rtab a:hover {{ color:#7EA6FF !important; }}
.cal {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)) 124px; gap:6px; direction:ltr; }}
.cal .dh {{ text-align:center; color:{MUTED}; font-size:.72rem; font-weight:800; padding:4px 0; }}
.cal .d {{ position:relative; min-height:80px; border-radius:10px; padding:18px 6px 6px; text-align:center; background:{CARD}; border:1px solid {BORDER}; }}
.cal .d .n {{ position:absolute; top:5px; right:8px; font-size:.66rem; font-weight:700; opacity:.65; }}
.cal .d .p {{ font-weight:800; font-size:1rem; }}
.cal .d .s {{ font-size:.66rem; font-weight:650; opacity:.85; margin-top:2px; }}
.cal .d.pos {{ border-color:{POS_BD}; }} .cal .d.neg {{ border-color:{NEG_BD}; }}
.cal .d.off {{ opacity:.25; }}
.cal .wk {{ border-radius:10px; padding:8px 10px; background:{CARD2}; border:1px solid {BORDER}; min-height:80px; }}
.cal .wk .l {{ font-size:.62rem; color:{MUTED}; font-weight:800; letter-spacing:.08em; }}
.cal .wk .p {{ margin-top:6px; }} .cal .wk .s {{ margin-top:6px; font-size:.66rem; color:{MUTED}; font-weight:700; }}
.opos {{ display:flex; flex-direction:column; gap:8px; }}
.opos .o {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:8px; align-items:center; padding:8px 10px; border-radius:12px; background:{CARD}; border:1px solid {BORDER}; direction:ltr; }}
.opos .o .m {{ color:{MUTED}; font-size:.72rem; margin-top:2px; }}
/* financial explorer / misc */
.mx {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:8px; margin:6px 0 10px; }}
.mx .m {{ background:{CARD}; border:1px solid {BORDER}; border-radius:12px; padding:9px 11px; }}
.mx .m .l {{ color:{MUTED}; font-size:.72rem; font-weight:650; }} .mx .m .v {{ font-weight:800; margin-top:3px; direction:ltr; }}
.mx .m.pos .l, .mx .m.neg .l {{ opacity:.8; color:inherit; }}
.perfrow {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(96px,1fr)); gap:8px; }}
.perfrow .pc2 {{ border-radius:12px; padding:9px 10px; text-align:center; border:1px solid {BORDER}; background:{CARD}; }}
.perfrow .pc2 .l {{ font-size:.72rem; font-weight:800; opacity:.75; }} .perfrow .pc2 .v {{ font-size:1.05rem; font-weight:800; direction:ltr; margin-top:2px; }}
.perfrow .pc2.pos {{ border-color:{POS_BD}; }} .perfrow .pc2.neg {{ border-color:{NEG_BD}; }}
.sigs {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:8px; }}
.sigs .sg {{ display:flex; justify-content:space-between; align-items:center; gap:8px; padding:8px 10px; border-radius:12px; background:{CARD}; border:1px solid {BORDER}; }}
.sigs .sg .n {{ font-weight:700; font-size:.84rem; }} .sigs .sg .v {{ color:{MUTED}; font-size:.74rem; direction:ltr; }}
/* ---------- insight: daily brief ---------- */
.brief {{ position:relative; border-radius:20px; padding:22px 26px 18px; border:1px solid {BORDER}; overflow:hidden; margin-bottom:12px;
  background: radial-gradient(700px 260px at 0% 0%, rgba(61,123,255,.22), transparent 60%), radial-gradient(600px 240px at 100% 0%, rgba(139,92,246,.18), transparent 60%),
  linear-gradient(180deg, {CARD2}, {CARD}); }}
.brief .eyebrow {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; color:{CYAN}; font-weight:800; letter-spacing:.14em; font-size:.72rem; text-transform:uppercase; }}
.brief .hl {{ font-size:1.75rem; font-weight:800; margin:10px 0 8px; line-height:1.3; color:#fff; letter-spacing:-.01em; }}
.brief ul {{ margin:8px 0 0; padding-inline-start:20px; }} .brief li {{ margin:4px 0; line-height:1.75; color:#D5DBE6; }}
.brief .eyebrow .status {{ text-transform:none; letter-spacing:0; font-size:.74rem; padding:4px 10px; }}
.brief .mood {{ display:inline-flex; align-items:center; gap:6px; padding:4px 11px; border-radius:20px; font-weight:800; font-size:.78rem; letter-spacing:0; text-transform:none; }}
.bstory {{ display:flex; gap:12px; align-items:flex-start; padding:10px 4px; border-bottom:1px solid {BORDER}; }}
.bstory:last-child {{ border-bottom:none; }}
.bstory .sc {{ flex:none; width:46px; height:46px; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center;
  font-weight:800; font-size:1.08rem; line-height:1; border:1px solid; direction:ltr; }}
.bstory .sc small {{ font-size:.55rem; font-weight:700; opacity:.75; margin-top:3px; }}
.bstory .b {{ min-width:0; flex:1; }}
.bstory a {{ color:#E9EDF5 !important; text-decoration:none !important; font-weight:700; line-height:1.55; }} .bstory a:hover {{ color:#7EA6FF !important; }}
.bstory .m {{ color:{MUTED}; font-size:.74rem; margin-top:3px; }}
.bstory .kw {{ margin-top:6px; }} .bstory .kwc {{ font-size:.68rem; padding:2px 8px 2px 6px; }}
.iqs {{ display:inline-block; padding:3px 10px; border-radius:10px; font-size:.74rem; font-weight:800; border:1px solid; }}
.evt {{ display:grid; grid-template-columns: 96px minmax(0,1fr) auto; gap:12px; align-items:center; padding:9px 10px; border-radius:12px; background:{CARD};
  border:1px solid {BORDER}; margin-bottom:6px; }}
.evt .d {{ text-align:center; border-radius:10px; padding:5px 4px; background:rgba(61,123,255,.12); color:#BFD3FB; font-weight:800; font-size:.72rem; line-height:1.4; direction:ltr; }}
.evt .n {{ font-weight:750; }} .evt .x {{ color:{MUTED}; font-size:.74rem; direction:ltr; white-space:nowrap; }}
.evt.key {{ border-color: rgba(245,185,74,.45); }} .evt.key .d {{ background:{YEL_BG}; color:{YEL_FG}; }}
/* ---------- insight: articles ---------- */
.acard {{ background:{CARD}; border:1px solid {BORDER}; border-radius:18px; overflow:hidden; height:100%; transition: transform .18s, box-shadow .18s, border-color .18s; }}
.acard .aart {{ position:relative; height:176px; overflow:hidden; }} .acard .aart svg {{ width:100%; height:100%; display:block; }}
.acard .aicon {{ position:absolute; left:50%; top:46%; transform:translate(-50%,-50%); width:66px; height:66px; border-radius:50%; display:flex; align-items:center;
  justify-content:center; background:rgba(255,255,255,.16); border:1.5px solid rgba(255,255,255,.45); }}
.acard .aicon .ms {{ font-size:2rem; color:#fff; }}
.acard .abody {{ padding:14px 16px 16px; }}
.acat {{ font-size:.66rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; color:#93C5FD; }}
.acard .attl {{ font-weight:800; font-size:1.05rem; line-height:1.45; margin-top:6px; color:#fff; }}
.acard .adek {{ color:{MUTED}; font-size:.84rem; line-height:1.6; margin-top:6px; }}
.acard .ameta {{ display:flex; gap:6px; margin-top:10px; flex-wrap:wrap; }}
.acard.feat {{ display:grid; grid-template-columns: minmax(0,1.05fr) minmax(0,1fr); }}
.acard.feat .aart {{ height:100%; min-height:260px; }} .acard.feat .aicon {{ width:92px; height:92px; }} .acard.feat .aicon .ms {{ font-size:2.8rem; }}
.acard.feat .attl {{ font-size:1.6rem; line-height:1.3; }} .acard.feat .adek {{ font-size:.98rem; }}
.acard.feat .abody {{ padding:26px 28px; display:flex; flex-direction:column; justify-content:center; }}
[class*="st-key-art_"] {{ position:relative; height:100%; }}
[class*="st-key-art_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-art_"] .stButton {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; }}
[class*="st-key-art_"] .stButton button {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
[class*="st-key-art_"]:hover .acard {{ transform: translateY(-4px); box-shadow: 0 14px 32px rgba(61,123,255,.18); border-color: rgba(96,140,255,.5); }}
.article .at {{ font-size:2.15rem; font-weight:800; line-height:1.25; margin:10px 0 8px; color:#fff; letter-spacing:-.015em; }}
.article .dek {{ color:#C7CFDD; font-size:1.1rem; line-height:1.75; }}
.article .ah {{ font-size:1.3rem; font-weight:800; margin:26px 0 6px; color:#fff; }}
.article p, .article li {{ line-height:1.95; color:#D5DBE6; font-size:1.02rem; }}
.article ul {{ padding-inline-start:22px; margin:6px 0; }} .article li {{ margin:5px 0; }}
.acover {{ position:relative; aspect-ratio:16/6; max-height:360px; border-radius:18px; overflow:hidden; margin:6px 0 4px; }} .acover svg {{ width:100%; height:100%; display:block; }}
.tkw {{ background: linear-gradient(135deg, rgba(34,211,238,.1), rgba(61,123,255,.08)); border:1px solid rgba(34,211,238,.28); border-radius:16px; padding:14px 18px; margin:16px 0 8px; }}
.tkw .h {{ font-weight:800; font-size:.78rem; letter-spacing:.1em; text-transform:uppercase; color:{CYAN}; margin-bottom:4px; display:flex; gap:6px; align-items:center; }}
.tkw .t {{ display:flex; gap:10px; align-items:flex-start; margin:6px 0; line-height:1.75; color:#E2E8F0; }} .tkw .t .ms {{ color:#4ADE80; margin-top:4px; }}
.anote {{ border-inline-start:3px solid {ACCENT}; background:rgba(61,123,255,.08); padding:12px 16px; border-radius:12px; margin:16px 0; display:flex; gap:10px; line-height:1.8; }}
.anote .ms {{ color:#7EA6FF; margin-top:3px; }}
.acap {{ color:{MUTED}; font-size:.8rem; margin:2px 0 4px; display:flex; gap:6px; align-items:center; }}
.acap .ms {{ color:{CYAN}; }}
/* ---------- insight: fear & greed ---------- */
.fgcmp {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; margin-top:10px; }}
.fgcmp .c {{ border-radius:12px; padding:9px 8px; text-align:center; border:1px solid transparent; }}
.fgcmp .c .l {{ font-size:.66rem; font-weight:800; opacity:.8; }} .fgcmp .c .v {{ font-size:1.3rem; font-weight:800; margin-top:2px; direction:ltr; }}
.fgcmp .c .s {{ font-size:.64rem; font-weight:800; }}
.fgc {{ background: linear-gradient(180deg,{CARD2},{CARD}); border:1px solid {BORDER}; border-radius:16px; padding:13px 14px; height:100%; }}
.fgc .h {{ display:flex; justify-content:space-between; gap:8px; align-items:flex-start; }}
.fgc .h b {{ font-size:.92rem; }} .fgc .x {{ color:{MUTED}; font-size:.78rem; line-height:1.65; margin-top:8px; }}
.fgc .r {{ font-size:.78rem; margin-top:8px; font-weight:700; color:#C9D0DC; }}
.fgbar {{ position:relative; height:8px; border-radius:5px; margin-top:12px; background: linear-gradient(90deg, #EF4444, #F97316 30%, #94A3B8 50%, #84CC16 70%, #22C55E); direction:ltr; }}
.fgbar i {{ position:absolute; top:-4px; width:16px; height:16px; border-radius:50%; background:#fff; border:3px solid {BG}; transform:translateX(-50%); box-shadow:0 2px 6px rgba(0,0,0,.5); }}
/* ---------- top navigation: lives in the site's top line (Streamlit header row), hover menus ---------- */
.st-key-topnav {{ container-type: inline-size; container-name: topnav; overflow: visible !important; gap: 10px !important; }}
.st-key-topnav, .st-key-topnav div, .st-key-navleft, .st-key-navright {{ overflow: visible !important; }}
/* Streamlit pulls every markdown block up by 1rem (it expects a paragraph margin under it) and every page link by .25rem.
   Inside the bar and its menus that squeezed buttons and made menu items overlap, so both are cancelled here. */
.st-key-topnav [data-testid="stMarkdownContainer"] {{ margin-bottom: 0 !important; }}
.st-key-topnav [data-testid="stElementContainer"]:has(> .stPageLink), .st-key-topnav .stElementContainer:has(> .stPageLink) {{ margin: 0 !important; }}
.st-key-topnav [data-testid="stMarkdownContainer"] p {{ margin: 0 !important; }}
.st-key-navleft {{ flex-wrap: nowrap !important; gap: 2px !important; }}
.st-key-navright {{ flex-wrap: nowrap !important; gap: 8px !important; }}
[data-testid="stLayoutWrapper"]:has(> .st-key-navsearch), .st-key-topnav > .st-key-navsearch {{ flex: 0 1 520px !important; min-width: 180px !important;
  margin-inline-start: auto; }}
[class*="st-key-navsec_"] {{ position: relative; gap: 0 !important; }}
.navbtn {{ display:flex; align-items:center; gap:7px; height:38px; box-sizing:border-box; padding:0 12px; border-radius:11px; font-weight:700; font-size:.9rem;
  line-height:1; color:#C9D2E3; cursor:pointer; white-space:nowrap; border:1px solid transparent; transition: background .18s, color .18s, border-color .18s;
  user-select:none; outline:none; }}
.navbtn .ms {{ font-size:1.14rem; color:#8FA3C8; transition: color .18s; }}
.navbtn .chev {{ font-size:1rem; opacity:.75; transition: transform .22s ease; }}
.navbtn:focus-visible {{ box-shadow: 0 0 0 2px rgba(96,140,255,.7); }}
[class*="st-key-navsec_"]:hover .navbtn {{ color:#fff; background: linear-gradient(135deg, rgba(61,123,255,.24), rgba(139,92,246,.2)); border-color: rgba(96,140,255,.45); }}
[class*="st-key-navsec_"]:hover .navbtn .ms {{ color:#fff; }}
[class*="st-key-navsec_"]:hover .chev {{ transform: rotate(180deg); }}
.navbtn.on {{ color:#fff; background: rgba(61,123,255,.14); border-color: rgba(61,123,255,.34); }}
.navbtn.on .ms {{ color:#7EA6FF; }}
/* menus: open on hover (mouse) or keyboard focus only - a clicked menu never stays open over the next one */
[class*="st-key-navdd_"], .st-key-langdd {{ position:absolute !important; top: calc(100% + 8px); left:0; width: 264px !important; min-width: 264px !important;
  max-width: none !important; z-index: 1000; gap: 2px !important; box-sizing: border-box;
  padding: 10px 8px 8px; background: rgba(17,23,35,.985); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
  border: 1px solid #2B3548; border-radius: 16px; box-shadow: 0 24px 50px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.02) inset;
  opacity: 0; visibility: hidden; transform: translateY(6px); transform-origin: top left; pointer-events: none;
  transition: opacity .1s ease, transform .1s ease, visibility 0s linear .1s; }}
[class*="st-key-navdd_"]::before, .st-key-langdd::before {{ content:""; position:absolute; left:0; right:0; top:-12px; height:12px; }}
[class*="st-key-navsec_"]:hover [class*="st-key-navdd_"], [class*="st-key-navsec_"]:has(:focus-visible) [class*="st-key-navdd_"],
.st-key-langsec:hover .st-key-langdd, .st-key-langsec:has(:focus-visible) .st-key-langdd {{ opacity: 1; visibility: visible; transform: none; pointer-events: auto;
  transition: opacity .16s ease, transform .18s ease, visibility 0s; }}
/* while one menu is hovered, every other menu closes at once (no two menus on top of each other) */
.st-key-topnav:has([class*="st-key-navsec_"]:hover) [class*="st-key-navsec_"]:not(:hover) [class*="st-key-navdd_"],
.st-key-topnav:has([class*="st-key-navsec_"]:hover) .st-key-langdd, .st-key-topnav:has(.st-key-langsec:hover) [class*="st-key-navdd_"] {{
  opacity: 0 !important; visibility: hidden !important; transition: none !important; pointer-events: none !important; }}
[class*="st-key-navsec_"]:hover, .st-key-langsec:hover {{ z-index: 5; }}
@media (hover: none) {{  /* touch screens: a tap opens the menu */
  [class*="st-key-navsec_"]:focus-within [class*="st-key-navdd_"], .st-key-langsec:focus-within .st-key-langdd {{ opacity: 1; visibility: visible; transform: none;
    pointer-events: auto; }} }}
.navhd {{ font-size:.64rem; letter-spacing:.14em; text-transform:uppercase; color:{MUTED}; font-weight:800; padding: 0 10px 7px; line-height:1.2;
  border-bottom: 1px solid {BORDER}; margin-bottom: 4px; }}
[class*="st-key-navdd_"] [data-testid="stPageLink"] a {{ border-radius: 11px; padding: 8px 10px; margin: 0; min-height: 38px; box-sizing: border-box;
  transition: background .14s, transform .14s; }}
[class*="st-key-navdd_"] [data-testid="stPageLink"] a:hover {{ background: rgba(61,123,255,.16); transform: translateX(2px); }}
[class*="st-key-navdd_"] [data-testid="stPageLink"] a span {{ font-weight: 650; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
[class*="st-key-navon_"] [data-testid="stPageLink"] a {{ background: linear-gradient(90deg, rgba(61,123,255,.3), rgba(139,92,246,.16)) !important;
  box-shadow: inset 3px 0 0 {ACCENT}; }}
[class*="st-key-navon_"] {{ gap: 0 !important; }}
.st-key-navright .status {{ display:inline-flex; align-items:center; height:38px; box-sizing:border-box; padding: 0 12px; font-size: .76rem; white-space: nowrap;
  background: rgba(17,23,35,.75); }}
/* search: wide type-ahead box, same height as the buttons */
.st-key-navsearch [data-testid="stSelectbox"], .st-key-navsearch [data-testid="stTextInput"] {{ position: relative; }}
.st-key-navsearch [data-testid="stSelectbox"]::before, .st-key-navsearch [data-testid="stTextInput"]::before {{ content: "search";
  font-family: 'Material Symbols Rounded'; position: absolute; inset-inline-start: 12px; top: 50%; transform: translateY(-50%); z-index: 3;
  font-size: 1.2rem; line-height: 1; color: #8A94A7; pointer-events: none; }}
.st-key-navsearch input {{ padding-inline-start: 38px !important; font-size: .88rem !important; }}
.st-key-navsearch [role="group"], .st-key-navsearch [data-baseweb="select"] > div, .st-key-navsearch [data-baseweb="input"] {{ height: 38px !important;
  min-height: 38px !important; box-sizing: border-box; border-radius: 12px !important; background: rgba(22,29,43,.92) !important; border-color: #2B3548 !important;
  transition: border-color .15s, box-shadow .15s; }}
.st-key-navsearch [role="group"]:hover, .st-key-navsearch [data-baseweb="select"] > div:hover, .st-key-navsearch [data-baseweb="input"]:hover {{ border-color: rgba(96,140,255,.55) !important; }}
.st-key-navsearch [role="group"][data-focus-within], .st-key-navsearch [data-baseweb="select"]:focus-within > div, .st-key-navsearch [data-baseweb="input"]:focus-within {{
  border-color: {ACCENT} !important; box-shadow: 0 0 0 3px rgba(61,123,255,.22); }}
.st-key-navsearch button[aria-label="Open"] {{ display: none !important; }}
.st-key-navsearch input::placeholder {{ color: #8A94A7 !important; }}
/* language menu: flags */
.flag {{ display:inline-block; flex:none; width:24px; height:18px; border-radius:4px; background-size:cover; background-position:center;
  box-shadow: 0 0 0 1px rgba(255,255,255,.22), 0 2px 6px rgba(0,0,0,.35); }}
.flag.us {{ background-image:url("{FLAG_US}"); }}
.flag.sa {{ background-image:url("{FLAG_SA}"); }}
.st-key-langsec {{ position: relative; gap: 0 !important; }}
.langbtn {{ display:flex; align-items:center; gap:7px; height:38px; box-sizing:border-box; padding:0 8px 0 10px; border-radius:11px; border:1px solid #2B3548;
  background: rgba(22,29,43,.9); color:#E9EDF5; cursor:pointer; white-space:nowrap; user-select:none; outline:none; line-height:1;
  transition: border-color .18s, background .18s; }}
.langbtn .flag {{ width:26px; height:19px; }}
.langbtn .chev {{ font-size:1rem; color:{MUTED}; transition: transform .2s ease; }}
.langbtn:focus-visible {{ box-shadow: 0 0 0 2px rgba(96,140,255,.7); }}
.st-key-langsec:hover .langbtn {{ border-color: rgba(96,140,255,.55); background: linear-gradient(135deg, rgba(61,123,255,.22), rgba(139,92,246,.18)); }}
.st-key-langsec:hover .langbtn .chev {{ transform: rotate(180deg); }}
.st-key-langdd {{ left: auto; right: 0; width: 236px !important; min-width: 236px !important; transform-origin: top right; }}
.lopt {{ display:flex; flex-wrap:nowrap; align-items:center; gap:12px; height:46px; box-sizing:border-box; padding:0 12px; border-radius:12px;
  transition: background .14s; white-space:nowrap; }}
.lopt .flag {{ width:30px; height:22px; border-radius:5px; }}
.lopt .nm {{ display:flex; align-items:baseline; gap:8px; min-width:0; line-height:1.2; }}
.lopt .nm b {{ font-size:.95rem; color:#fff; font-weight:800; }}
.lopt .nm small {{ color:{MUTED}; font-size:.74rem; font-weight:600; }}
.lopt .ck {{ margin-inline-start:auto; color:#4ADE80; font-size:1.2rem; }}
.lopt.on {{ background: rgba(61,123,255,.16); box-shadow: inset 0 0 0 1px rgba(61,123,255,.35); }}
[class*="st-key-langopt_"] {{ position:relative; gap:0 !important; }}
[class*="st-key-langopt_"] [data-testid="stElementContainer"] {{ position:static !important; margin:0 !important; }}
[class*="st-key-langopt_"] .stButton {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; }}
[class*="st-key-langopt_"] .stButton button {{ width:100% !important; height:100% !important; min-height:0 !important; opacity:0; cursor:pointer; }}
[class*="st-key-langopt_"]:hover .lopt:not(.on) {{ background: rgba(61,123,255,.1); }}
/* narrower screens: the bar compacts itself step by step instead of wrapping (7 menus + search + status + language) */
@container topnav (max-width: 1760px) {{ .navbtn .chev {{ display:none; }} }}
@container topnav (max-width: 1560px) {{ .st-key-navright .status .muted {{ display:none; }} .navbtn {{ padding:0 10px; gap:6px; }} }}
@container topnav (max-width: 1400px) {{ .navbtn {{ padding:0 8px; gap:5px; font-size:.85rem; }} .navbtn .ms {{ font-size:1.05rem; }}
  .st-key-navright .status b {{ display:none; }} .st-key-navright .status {{ padding: 0 12px; }} }}
@container topnav (max-width: 1030px) {{ .navbtn > span:not(.ms) {{ display:none; }} .navbtn {{ padding:0 10px; }} .navbtn .ms {{ font-size:1.18rem; }} }}
@container topnav (max-width: 760px) {{ .st-key-navright .status {{ display:none; }} .langbtn .chev {{ display:none; }} }}
/* desktop: the bar IS the site's top line. It is anchored to the main area's own box (the same box as Streamlit's header),
   so it spans from the sidebar edge to the menu button, follows the sidebar when it is opened/closed/resized and never scrolls away. */
@media (min-width: 1024px) {{
  [data-testid="stMainBlockContainer"]:has(.st-key-topnav) {{ padding-top: 3.75rem !important; }}
  [data-testid="stLayoutWrapper"]:has(> .st-key-topnav) {{ position: static !important; height: 0; min-height: 0; overflow: visible; }}
  .st-key-topnav {{ position: absolute !important; top: 0; left: 1.25rem; right: 4.25rem; width: auto !important; max-width: none !important;
    height: 3.75rem; min-height: 3.75rem; z-index: 999990; flex-wrap: nowrap !important; align-items: center !important; }}
  .stApp:has([data-testid="stExpandSidebarButton"]) .st-key-topnav {{ left: 6.6rem; }}
}}
@container topnav (min-width: 1900px) {{ [data-testid="stLayoutWrapper"]:has(> .st-key-navsearch), .st-key-topnav > .st-key-navsearch {{ flex-basis: 600px !important; }} }}
/* tablets and phones: a card under the top line, menus open full width */
@media (max-width: 1023.98px) {{
  .st-key-topnav {{ position: relative; z-index: 60; flex-wrap: wrap !important; padding: 6px 8px; margin-bottom: 6px; background: rgba(12,17,28,.86);
    border: 1px solid {BORDER}; border-radius: 16px; }}
  .st-key-navleft {{ flex-wrap: wrap !important; }}
  [data-testid="stLayoutWrapper"]:has(> .st-key-navsearch), .st-key-topnav > .st-key-navsearch {{ flex: 1 1 100% !important; order: 3; margin: 0 !important; }}
  [class*="st-key-navsec_"] {{ position: static; }}
  [class*="st-key-navdd_"] {{ left: 8px !important; right: 8px !important; width: auto !important; min-width: 0 !important; top: calc(100% + 4px); }}
}}
/* ---------- sidebar: market pulse + watchlist ---------- */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: .45rem; }}
.pulse {{ background: linear-gradient(160deg, rgba(61,123,255,.16), rgba(139,92,246,.08) 55%, {CARD}); border:1px solid {BORDER};
  border-radius:14px; padding:10px 12px; margin-bottom:6px; }}
.pulse .ph {{ display:flex; align-items:center; gap:6px; font-size:.7rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase;
  color:#C9D0DC; margin-bottom:4px; }}
.pulse .ph .ms {{ color:#7EA6FF; }}
.pr {{ display:grid; grid-template-columns: minmax(0,1fr) 58px auto; gap:8px; align-items:center; padding:5px 0;
  border-bottom:1px dashed rgba(138,148,167,.16); direction:ltr; }}
.pr:last-child {{ border-bottom:none; }}
.pr .n {{ font-size:.78rem; font-weight:750; color:#fff; }} .pr .v {{ font-size:.7rem; color:{MUTED}; font-variant-numeric: tabular-nums; }}
.pr .pill {{ min-width:0; padding:2px 6px; font-size:.68rem; }}
.wlh {{ display:flex; align-items:center; justify-content:space-between; margin: 8px 0 6px; direction:ltr; }}
.wlh .t {{ font-size:.7rem; font-weight:800; letter-spacing:.1em; color:#B8C0CE; text-transform:uppercase; display:flex; gap:6px; align-items:center; }}
.wlh .t .ms {{ color:#fff; background:linear-gradient(135deg,{ACCENT},{VIOLET}); border-radius:7px; padding:3px; font-size:.95rem; }}
.wlr {{ display:grid; grid-template-columns: minmax(0,1fr) 56px auto; gap:8px; align-items:center; padding:8px 10px; border-radius:12px;
  background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; direction:ltr;
  transition: transform .15s, border-color .15s, box-shadow .15s; }}
.wlr .l {{ display:flex; align-items:center; gap:8px; min-width:0; }}
.wlr .nm {{ min-width:0; }} .wlr .nm b {{ display:block; font-size:.84rem; color:#fff; }}
.wlr .nm span {{ display:block; font-size:.64rem; color:{MUTED}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.wlr .r {{ text-align:right; }} .wlr .r .p {{ font-size:.8rem; font-weight:750; font-variant-numeric: tabular-nums; }}
.wlr .r .pill {{ min-width:0; padding:1px 6px; font-size:.66rem; margin-top:2px; }}
[class*="st-key-wlr_"] {{ position:relative; }}
[class*="st-key-wlr_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-wlr_"] .stButton {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; }}
[class*="st-key-wlr_"] .stButton button {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
[class*="st-key-wlr_"]:hover .wlr {{ border-color: rgba(96,140,255,.6); transform: translateX(3px); box-shadow: 0 8px 18px rgba(0,0,0,.35); }}
@media (max-width: 600px) {{ .iqleg .sc span {{ width:22px; height:22px; font-size:.66rem; }} .iq {{ width:74px; }} }}
@media (max-width: 900px) {{ .acard.feat {{ grid-template-columns: 1fr; }} .fgcmp {{ grid-template-columns: repeat(2,minmax(0,1fr)); }} .dash {{ grid-template-columns: 1fr; }} .cal {{ grid-template-columns:repeat(5,minmax(0,1fr)); }} .cal .wk, .cal .wkh {{ display:none; }} }}
/* ---------- calendar pages ---------- */
.wklbl {{ display:flex; align-items:center; gap:8px; font-size:1rem; color:#fff; flex-wrap:wrap; }}
.wklbl .ms {{ color:#7EA6FF; }}
.wklbl .tag, .ehub .hd .now, .evday .dh .now {{ font-size:.66rem; font-weight:800; padding:3px 9px; border-radius:20px; background:{ACCENT}; color:#fff; letter-spacing:.02em; }}
.lgo {{ position:relative; display:inline-block; flex:none; border-radius:11px; overflow:hidden; background:#fff; box-shadow:0 0 0 1px rgba(255,255,255,.1); }}
.lgo object {{ position:absolute; inset:0; width:100%; height:100%; border:0; pointer-events:none; }}
.lgo .ini {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800; letter-spacing:-.02em; }}
.ehub {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; margin:12px 0 6px; }}
.ehub .day {{ background:linear-gradient(180deg,{CARD2},{CARD}); border:1px solid {BORDER}; border-radius:16px; padding:10px 10px 12px; min-width:0;
  display:flex; flex-direction:column; gap:12px; }}
.ehub .day.today {{ border-color:rgba(61,123,255,.65); box-shadow:0 0 0 1px rgba(61,123,255,.3), 0 14px 32px rgba(61,123,255,.14); }}
.ehub .day.past {{ background:{CARD}; }}
.ehub .hd {{ display:flex; align-items:baseline; gap:6px; padding:2px 4px 9px; border-bottom:1px solid {BORDER}; flex-wrap:wrap; }}
.ehub .hd .dw {{ font-size:.72rem; font-weight:800; letter-spacing:.12em; color:{MUTED}; }}
.ehub .hd .dn {{ font-size:1.55rem; font-weight:800; color:#fff; line-height:1; }}
.ehub .hd .mo {{ font-size:.74rem; color:{MUTED}; font-weight:700; }}
.ehub .hd .cnt {{ margin-inline-start:auto; font-size:.72rem; font-weight:800; color:#BFD3FB; background:rgba(61,123,255,.14); border-radius:10px; padding:2px 8px; }}
.ehub .grp .gh {{ display:flex; align-items:center; gap:6px; font-size:.75rem; font-weight:800; color:#C9D2E3; margin-bottom:8px; }}
.ehub .grp .gh .ms {{ font-size:1.05rem; }}
.ehub .grp.bmo .gh .ms {{ color:{GOLD}; }} .ehub .grp.amc .gh .ms {{ color:{PURPLE}; }} .ehub .grp.tns .gh .ms {{ color:{MUTED}; }} .ehub .grp.ipo .gh .ms {{ color:{CYAN}; }}
.ehub .grp .gh b {{ margin-inline-start:auto; font-size:.7rem; color:{MUTED}; }}
.ehub .tl {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(50px,1fr)); gap:8px 4px; }}
.et {{ position:relative; display:flex; flex-direction:column; align-items:center; gap:5px; text-decoration:none !important; padding:4px 1px; border-radius:10px;
  transition:background .15s, transform .15s; min-width:0; }}
.et:hover {{ background:rgba(61,123,255,.13); transform:translateY(-2px); }}
.et .tk {{ font-size:.66rem; font-weight:800; color:#DDE3EE; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.rs {{ display:inline-block; width:10px; height:10px; border-radius:50%; }} .rs.b {{ background:#22C55E; }} .rs.m {{ background:#EF4444; }}
.et .rs {{ position:absolute; top:0; inset-inline-end:4px; border:2px solid {CARD2}; }}
.ehub details summary {{ cursor:pointer; font-size:.74rem; font-weight:800; color:#7EA6FF; margin-top:8px; list-style:none; }}
.ehub details summary::-webkit-details-marker {{ display:none; }}
.ehub details[open] summary {{ margin-bottom:8px; }}
.ehub .ipr {{ display:flex; align-items:center; gap:6px; font-size:.74rem; padding:5px 7px; border-radius:9px; background:rgba(34,211,238,.08); margin-top:4px; min-width:0; }}
.ehub .ipr .ms {{ color:{CYAN}; font-size:1rem; }} .ehub .ipr b {{ color:#fff; }}
.ehub .ipr span {{ color:{MUTED}; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; min-width:0; flex:1; }}
.ehub .ipr em {{ font-style:normal; color:#BFD3FB; font-weight:700; direction:ltr; white-space:nowrap; }}
.ehub .none {{ color:{MUTED}; font-size:.8rem; text-align:center; padding:18px 4px; }}
.hnote {{ display:inline-flex; align-items:center; gap:6px; font-size:.72rem; font-weight:800; padding:6px 9px; border-radius:10px; }}
.hnote .ms {{ font-size:1rem; }}
.hnote.closed {{ background:{NEG_BG}; color:{NEG_FG}; }} .hnote.early {{ background:{YEL_BG}; color:{YEL_FG}; }}
.elegend {{ display:flex; flex-wrap:wrap; gap:8px 18px; color:{MUTED}; font-size:.76rem; margin:8px 2px 14px; }}
.elegend span {{ display:inline-flex; align-items:center; gap:6px; }}
.elegend .ms {{ font-size:1rem; color:{GOLD}; }} .elegend span:nth-child(2) .ms {{ color:{PURPLE}; }}
.ehit {{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 10px; }}
.ehit .chip {{ display:inline-flex; align-items:center; gap:8px; padding:5px 12px 5px 5px; border-radius:14px; background:{CARD2}; border:1px solid rgba(61,123,255,.45);
  text-decoration:none !important; color:#E9EDF5 !important; font-size:.84rem; }}
.ehit .chip span {{ color:{MUTED}; }}
.etab {{ border:1px solid {BORDER}; border-radius:16px; overflow:hidden; background:{CARD}; margin:6px 0 10px; }}
.erow {{ display:grid; grid-template-columns:minmax(0,2.3fr) 1.35fr .8fr .85fr .75fr .9fr .95fr; gap:10px; align-items:center; padding:8px 14px;
  border-top:1px solid {BORDER}; font-size:.86rem; }}
.erow.eh {{ border-top:none; background:{CARD2}; font-size:.66rem; font-weight:800; letter-spacing:.07em; text-transform:uppercase; color:{MUTED}; padding:8px 14px; }}
.erow .lnk, .drow .lnk, .sprow .lnk {{ display:flex; align-items:center; gap:10px; min-width:0; text-decoration:none !important; }}
.erow .nm, .drow .nm, .sprow .nm, .iprow .nm {{ display:flex; flex-direction:column; min-width:0; line-height:1.3; }}
.erow .nm b, .drow .nm b, .sprow .nm b, .iprow .nm b {{ color:#fff; font-size:.88rem; }}
.erow .nm small, .drow .nm small, .sprow .nm small, .iprow .nm small {{ color:{MUTED}; font-size:.72rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.erow .v, .drow .v, .iprow .v {{ text-align:center; direction:ltr; font-variant-numeric:tabular-nums; }}
.erow .q {{ color:#C9D2E3; font-size:.8rem; }}
.when {{ display:inline-flex; align-items:center; gap:5px; font-size:.78rem; font-weight:700; color:#C9D2E3; white-space:nowrap; }}
.when .ms {{ font-size:1rem; }} .when.bmo .ms {{ color:{GOLD}; }} .when.amc .ms {{ color:{PURPLE}; }} .when.tns .ms, .when.dmh .ms {{ color:{MUTED}; }}
.egrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:14px; margin:12px 0 8px; }}
.ecard {{ background:linear-gradient(180deg,{CARD2},{CARD}); border:1px solid {BORDER}; border-inline-start:4px solid #3A4458; border-radius:18px; padding:14px 16px;
  display:flex; flex-direction:column; gap:12px; min-width:0; }}
.ecard.beat {{ background:linear-gradient(180deg, rgba(34,197,94,.13), {CARD} 72%); border-color:rgba(34,197,94,.38); border-inline-start-color:#22C55E; }}
.ecard.miss {{ background:linear-gradient(180deg, rgba(239,68,68,.13), {CARD} 72%); border-color:rgba(239,68,68,.38); border-inline-start-color:#EF4444; }}
.ecard .top {{ display:flex; gap:12px; align-items:flex-start; }}
.ecard .top .lnk {{ flex:none; }}
.ecard .t {{ min-width:0; flex:1; }}
.ecard .t .nm {{ font-weight:800; color:#fff; font-size:1rem; line-height:1.3; }}
.ecard .t .co {{ color:{MUTED}; font-size:.76rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.ecard .t .d {{ display:flex; align-items:center; gap:5px; font-size:.74rem; color:#C9D2E3; margin-top:5px; }}
.ecard .t .d .ms {{ font-size:1rem; color:{GOLD}; }}
.ecard .px {{ text-align:end; flex:none; }}
.ecard .px .p {{ font-weight:800; font-size:1rem; color:#fff; direction:ltr; }}
.ecard .px .pill {{ margin-top:3px; }}
.ecard .rx {{ font-size:.7rem; color:{MUTED}; margin-top:5px; white-space:nowrap; }}
.ecard .rx .pos {{ color:#4ADE80; font-weight:800; }} .ecard .rx .neg {{ color:#F87171; font-weight:800; }}
.ecard table.res {{ display:table; width:100%; margin:0 !important; border-collapse:separate; border-spacing:0; font-size:.84rem; background:rgba(10,14,23,.5);
  border:1px solid {BORDER}; border-radius:12px; overflow:hidden; }}
.ecard table.res tr {{ border:none; }}
.ecard table.res th {{ font-size:.64rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:{MUTED}; padding:7px 8px; text-align:center; border:none; }}
.ecard table.res td {{ padding:8px; text-align:center; border:none; border-top:1px solid {BORDER}; direction:ltr; font-variant-numeric:tabular-nums; color:#C9D2E3; }}
.ecard table.res td.k {{ text-align:start; font-weight:800; direction:inherit; }}
.ecard table.res td.a {{ color:#fff; font-weight:800; }}
.ecard table.res td.pos {{ color:#4ADE80; font-weight:800; }} .ecard table.res td.neg {{ color:#F87171; font-weight:800; }}
.ecard table.res small {{ color:{MUTED}; font-size:.62rem; font-weight:700; }}
.ecard .vd {{ display:flex; align-items:center; gap:6px; font-size:.78rem; font-weight:800; color:{MUTED}; }}
.ecard .vd .ms {{ font-size:1.05rem; }}
.ecard.beat .vd {{ color:#4ADE80; }} .ecard.miss .vd {{ color:#F87171; }}
.evcal {{ display:flex; flex-direction:column; gap:14px; margin:12px 0 8px; }}
.evday {{ background:{CARD}; border:1px solid {BORDER}; border-radius:16px; overflow:hidden; }}
.evday.today {{ border-color:rgba(61,123,255,.6); }}
.evday .dh {{ display:flex; align-items:center; gap:8px; padding:10px 14px; background:linear-gradient(90deg, rgba(61,123,255,.16), transparent); font-weight:800;
  color:#fff; flex-wrap:wrap; }}
.evday .dh .ms {{ color:#7EA6FF; }}
.evday .dh .c {{ margin-inline-start:auto; font-size:.72rem; color:#BFD3FB; background:rgba(61,123,255,.16); padding:2px 9px; border-radius:10px; }}
.evday .dh .hnote {{ padding:3px 8px; }}
.evr {{ display:grid; grid-template-columns:78px 58px minmax(0,1fr) 92px 92px 92px; gap:10px; align-items:center; padding:8px 14px; border-top:1px solid {BORDER}; font-size:.86rem; }}
.evr.eh {{ font-size:.64rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:{MUTED}; background:{CARD2}; padding:7px 14px; }}
.evr .tm {{ font-weight:800; color:#C9D2E3; direction:ltr; font-variant-numeric:tabular-nums; }}
.evr.eh .tm {{ direction:inherit; }}
.evr .nm {{ color:#E9EDF5; font-weight:650; min-width:0; }}
.evr .nm small {{ color:{MUTED}; font-weight:600; margin-inline-start:4px; }}
.evr .rg {{ font-size:.62rem; font-weight:800; padding:1px 6px; border-radius:6px; background:rgba(138,148,167,.18); color:#C9D2E3; margin-inline-end:6px; }}
.evr .v {{ text-align:center; direction:ltr; font-variant-numeric:tabular-nums; color:#C9D2E3; }}
.evr .v.a {{ font-weight:800; color:#fff; }} .evr .v.a.pos {{ color:#4ADE80; }} .evr .v.a.neg {{ color:#F87171; }}
.evr.s3 {{ background:rgba(239,68,68,.05); }} .evr.s3 .nm {{ font-weight:800; }}
.stars {{ display:inline-flex; gap:3px; }} .stars i {{ width:11px; height:11px; border-radius:3px; background:#2A3142; display:inline-block; }}
.stars.s1 i.on {{ background:#64748B; }} .stars.s2 i.on {{ background:{GOLD}; }} .stars.s3 i.on {{ background:#EF4444; }}
.hlist {{ display:flex; flex-direction:column; gap:8px; margin:10px 0 6px; }}
.hrow {{ display:grid; grid-template-columns:56px minmax(0,1fr) auto 120px; gap:14px; align-items:center; padding:10px 14px; border-radius:14px;
  background:linear-gradient(180deg,{CARD2},{CARD}); border:1px solid {BORDER}; }}
.hrow .dt, .iprow .dt {{ width:52px; height:52px; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center; line-height:1.1;
  background:rgba(239,68,68,.14); color:#FCA5A5; }}
.hrow .dt b, .iprow .dt b {{ font-size:1.25rem; color:#fff; }} .hrow .dt span, .iprow .dt span {{ font-size:.64rem; font-weight:800; text-transform:uppercase; }}
.hrow.early .dt {{ background:rgba(245,185,74,.16); color:{GOLD}; }} .hrow.bonds .dt, .iprow .dt {{ background:rgba(61,123,255,.14); color:#93C5FD; }}
.hrow .nm b {{ display:block; color:#fff; }} .hrow .nm small {{ color:{MUTED}; }}
.hrow .st {{ display:inline-flex; align-items:center; gap:6px; font-size:.76rem; font-weight:800; padding:4px 11px; border-radius:20px; background:{NEG_BG}; color:{NEG_FG};
  white-space:nowrap; }}
.hrow .st .ms {{ font-size:1rem; }}
.hrow.early .st {{ background:{YEL_BG}; color:{YEL_FG}; }} .hrow.bonds .st {{ background:{ACC_BG}; color:{ACC_FG}; }}
.hrow .wh {{ text-align:end; color:{MUTED}; font-size:.8rem; font-weight:700; }}
.hrow.past {{ opacity:.5; }} .hrow.next {{ border-color:rgba(61,123,255,.65); box-shadow:0 10px 26px rgba(61,123,255,.14); }}
.hrow.next .wh {{ color:#BFD3FB; }}
.calnote {{ display:flex; gap:10px; align-items:flex-start; margin:14px 0 6px; line-height:1.85; font-size:.86rem; color:#C9D2E3; }}
.calnote .ms {{ color:#7EA6FF; margin-top:3px; }}
.calempty {{ display:flex; flex-direction:column; align-items:center; gap:8px; padding:36px 18px; margin:12px 0; border:1px dashed #33405A; border-radius:16px;
  color:{MUTED}; text-align:center; line-height:1.7; }}
.calempty .ms {{ font-size:2.2rem; color:#7EA6FF; }}
.drow {{ display:grid; grid-template-columns:minmax(0,2.4fr) 1fr 1fr .9fr 1.1fr; gap:10px; align-items:center; padding:8px 14px; border-top:1px solid {BORDER}; font-size:.86rem; }}
.drow.th {{ font-size:.64rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:{MUTED}; background:{CARD2}; padding:7px 14px; }}
.drow .v.y {{ color:#4ADE80; font-weight:800; }}
.splist {{ display:flex; flex-direction:column; gap:8px; margin:10px 0 6px; }}
.sprow {{ display:grid; grid-template-columns:minmax(0,2fr) 110px 120px minmax(0,1.6fr) 130px; gap:12px; align-items:center; padding:10px 14px; border-radius:14px;
  background:linear-gradient(180deg,{CARD2},{CARD}); border:1px solid {BORDER}; }}
.sprow .ratio {{ font-weight:800; font-size:1.05rem; color:#fff; direction:ltr; text-align:center; }}
.sprow .k {{ display:inline-flex; gap:6px; align-items:center; font-size:.76rem; font-weight:800; padding:4px 11px; border-radius:20px; justify-self:start; }}
.sprow .k .ms {{ font-size:1rem; }}
.sprow.forward .k {{ background:{POS_BG}; color:{POS_FG}; }} .sprow.reverse .k {{ background:{ORG_BG}; color:{ORG_FG}; }}
.sprow .ex {{ color:{MUTED}; font-size:.8rem; }} .sprow .dt {{ text-align:end; font-weight:700; color:#C9D2E3; }}
.iplist {{ border:1px solid {BORDER}; border-radius:16px; overflow:hidden; background:{CARD}; margin:10px 0 6px; }}
.iprow {{ display:grid; grid-template-columns:52px 36px minmax(0,2fr) 90px 110px 90px 100px 74px 128px; gap:10px; align-items:center; padding:9px 14px;
  border-top:1px solid {BORDER}; font-size:.86rem; }}
.iprow.ih {{ border-top:none; background:{CARD2}; font-size:.64rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:{MUTED}; }}
.iprow .ex {{ color:#C9D2E3; font-size:.78rem; font-weight:700; }}
.iprow .badge {{ justify-self:start; }}
@media (max-width: 1100px) {{ .ehub {{ grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); }} }}
@media (max-width: 900px) {{
  .erow {{ grid-template-columns:minmax(0,1.7fr) 1fr .9fr; }} .erow > :nth-child(3), .erow > :nth-child(4), .erow > :nth-child(5), .erow > :nth-child(7) {{ display:none; }}
  .evr {{ grid-template-columns:52px minmax(0,1fr) 70px 70px; }} .evr > :nth-child(2), .evr > :nth-child(6) {{ display:none; }}
  .drow {{ grid-template-columns:minmax(0,1.8fr) 1fr .9fr; }} .drow > :nth-child(3), .drow > :nth-child(5) {{ display:none; }}
  .sprow {{ grid-template-columns:minmax(0,1fr) auto; }} .sprow .ex, .sprow .k {{ display:none; }}
  .iprow {{ grid-template-columns:44px minmax(0,1fr) 90px auto; }} .iprow > :nth-child(2), .iprow > :nth-child(4), .iprow > :nth-child(6), .iprow > :nth-child(7),
  .iprow > :nth-child(8) {{ display:none; }}
  .hrow {{ grid-template-columns:52px minmax(0,1fr); }} .hrow .st, .hrow .wh {{ grid-column:2; justify-self:start; text-align:start; }}
}}
/* ---------- catalyst pro header: name + chips, with room under them for the gauge title ---------- */
.cathead {{ display:flex; flex-direction:column; gap:10px; margin:4px 0 22px; }}
.cathead h3 {{ margin:0 !important; padding:0 !important; line-height:1.3; }}
.cathead .chips {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
.cathead .chips .badge {{ margin:0; }}
/* ---------- news pictures ---------- */
.news .nwrap {{ display:flex; gap:16px; align-items:flex-start; }}
.news .nbody {{ flex:1; min-width:0; }}
.nth {{ position:relative; flex:none; display:flex; align-items:center; justify-content:center; width:176px; height:118px; border-radius:14px; overflow:hidden;
  background:var(--g); box-shadow:0 8px 20px rgba(0,0,0,.35), inset 0 0 0 1px rgba(255,255,255,.08); }}
.nth::before {{ content:""; position:absolute; inset:0; z-index:0; opacity:.5; background:
  radial-gradient(circle at 18% 22%, rgba(255,255,255,.28), transparent 42%),
  repeating-linear-gradient(90deg, rgba(255,255,255,.07) 0 1px, transparent 1px 22px),
  repeating-linear-gradient(0deg, rgba(255,255,255,.05) 0 1px, transparent 1px 22px); }}
.nth img {{ position:relative; z-index:1; display:block; width:100%; height:100%; object-fit:cover; background:#161D2B; }}
.nth img::after {{ content:attr(data-ic); position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
  font-family:'Material Symbols Rounded'; font-size:48px; color:rgba(255,255,255,.95); background:var(--g); }}
.nth.fb .ms {{ position:relative; z-index:1; font-size:50px; color:#fff; text-shadow:0 6px 18px rgba(0,0,0,.3); }}
.nth.fb em {{ position:absolute; z-index:1; inset-inline-start:10px; bottom:8px; font-style:normal; font-size:.64rem; font-weight:800; letter-spacing:.08em;
  text-transform:uppercase; color:rgba(255,255,255,.9); }}
.nth.fb em::after {{ content:attr(data-en); }}
.nth .nlg {{ position:absolute; z-index:2; inset-inline-end:8px; bottom:8px; display:flex; border-radius:11px; box-shadow:0 4px 12px rgba(0,0,0,.45); }}
.nth.big {{ width:100%; height:150px; border-radius:14px; margin-bottom:12px; }}
.story .nth.big {{ margin:-4px 0 12px; }}
@media (max-width: 640px) {{ .news .nwrap {{ flex-direction:column; }} .news .nth {{ width:100%; height:170px; }} }}
.story:has(.nth) .rank {{ top:24px; inset-inline-end:auto; inset-inline-start:28px; z-index:3; font-size:.9rem; color:#fff; background:rgba(10,14,23,.55);
  padding:2px 10px; border-radius:10px; backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px); }}
.story:has(.nth) a.t {{ margin-inline-end:0; }}
/* ---------- news bot ---------- */
.news .meta .also {{ display:inline-block; margin-inline-start:4px; padding:0 6px; border-radius:8px; background:rgba(61,123,255,.18); color:#BFD3FB; font-weight:800;
  font-size:.66rem; cursor:help; }}
.botbar {{ display:flex; align-items:center; gap:10px 16px; flex-wrap:wrap; padding:10px 14px; border-radius:14px; margin:8px 0 10px;
  background:linear-gradient(90deg, rgba(34,197,94,.1), rgba(61,123,255,.08)); border:1px solid rgba(34,197,94,.3); font-size:.84rem; color:#C9D2E3; }}
.botbar .live {{ display:inline-flex; align-items:center; gap:7px; font-weight:800; color:#4ADE80; }}
.botbar .live i {{ width:9px; height:9px; border-radius:50%; background:#22C55E; box-shadow:0 0 0 0 rgba(34,197,94,.6); animation:botpulse 1.8s infinite; }}
@keyframes botpulse {{ 0% {{ box-shadow:0 0 0 0 rgba(34,197,94,.55); }} 70% {{ box-shadow:0 0 0 8px rgba(34,197,94,0); }} 100% {{ box-shadow:0 0 0 0 rgba(34,197,94,0); }} }}
.botbar b {{ color:#fff; }}
.srcgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:8px; }}
.srcc {{ display:flex; align-items:center; gap:8px; padding:8px 10px; border-radius:12px; background:{CARD2}; border:1px solid {BORDER}; font-size:.8rem; min-width:0; }}
.srcc .d {{ width:9px; height:9px; border-radius:50%; flex:none; background:#22C55E; }} .srcc.bad .d {{ background:#EF4444; }} .srcc.wait .d {{ background:#64748B; }}
.srcc b {{ color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.srcc span {{ margin-inline-start:auto; color:{MUTED}; white-space:nowrap; font-size:.72rem; }}
</style>
"""

RTL_CSS = f"""
<style>
.block-container, [data-testid="stMainBlockContainer"], [data-testid="stSidebarContent"] {{ direction: rtl; }}
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"], h1, h2, h3, h4, label, .stMarkdown {{ text-align: right; }}
.stPlotlyChart, .js-plotly-plot, [data-testid="stDataFrame"], .tape, .t-row, [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {{ direction: ltr; }}
.stPlotlyChart *, .js-plotly-plot *, [data-testid="stPlotlyChart"] *, .hm, .hm * {{ direction: ltr !important; }}
[data-testid="stMetricValue"] {{ text-align: right; }}
input, textarea {{ text-align: right; }}
html, body, .stApp, .stMarkdown, button, input, textarea, select, label, [data-baseweb] {{ font-family: {FONT_AR}, {FONT_LATIN}, system-ui, sans-serif; }}
.sec::after {{ background: linear-gradient(270deg, {BORDER}, transparent); }}
[class*="st-key-navdd_"] {{ left:auto; right:0; transform-origin: top right; }}
[class*="st-key-navon_"] [data-testid="stPageLink"] a {{ box-shadow: inset -3px 0 0 {ACCENT}; }}
[class*="st-key-navdd_"] [data-testid="stPageLink"] a:hover {{ transform: translateX(-2px); }}
.st-key-langdd {{ right:auto; left:0; transform-origin: top left; }}
.nth.fb em::after {{ content:attr(data-ar); }} .nth.fb em {{ letter-spacing:0; font-size:.72rem; }}
</style>
"""


# ---------------------------------------------------------------- formatting
def fmt_price(x):
    if x is None or pd.isna(x):
        return "—"
    x = float(x)
    return f"{x:,.2f}" if abs(x) >= 1 else f"{x:.4f}"


def fmt_big(x):
    if x is None or pd.isna(x):
        return "—"
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(x) >= div:
            return f"{x / div:.2f}{unit}"
    return f"{x:,.0f}"


def cls(v, invert=False):
    """'pos' / 'neg' / 'neu' for a signed value (the pastel rule)."""
    try:
        if v is None or pd.isna(v) or v == 0:
            return "neu"
    except (TypeError, ValueError):
        return "neu"
    good = v > 0
    if invert:
        good = not good
    return "pos" if good else "neg"


def txt(v, invert=False):
    """Text color class for signed values shown directly on dark surfaces."""
    c = cls(v, invert)
    return {"pos": "upt", "neg": "dnt"}.get(c, "muted")


def color_style(v):
    """Pandas Styler: light-green cell + dark-green text / light-red cell + dark-red text."""
    try:
        if v > 0:
            return f"background-color: {POS_BG}; color: {POS_FG}; font-weight: 700"
        if v < 0:
            return f"background-color: {NEG_BG}; color: {NEG_FG}; font-weight: 700"
    except TypeError:
        pass
    return ""


def signal_style(v, buy, sell):
    if v == buy:
        return f"background-color: {POS_BG}; color: {POS_FG}; font-weight: 700"
    if v == sell:
        return f"background-color: {NEG_BG}; color: {NEG_FG}; font-weight: 700"
    return ""


def esc(s):
    return html.escape(str(s))


def icon(name, color=None):
    style = f' style="color:{color}"' if color else ""
    return f'<span class="ms"{style}>{name}</span>'


def ico(name, kind="pos"):
    """Icon inside a pastel circle (readable on dark cards)."""
    bg, fg = {"pos": (POS_BG, POS_FG), "neg": (NEG_BG, NEG_FG), "acc": (ACC_BG, ACC_FG), "gold": (YEL_BG, YEL_FG),
              "neu": ("rgba(138,148,167,.2)", "#B8C0CE")}[kind]
    return f'<span class="ico" style="background:{bg};color:{fg}">{icon(name)}</span>'


# ---------------------------------------------------------------- building blocks
def page_title(ic, title, sub=""):
    return f'<div class="page-title">{icon(ic)}<h1>{esc(title)}</h1></div>' + (f'<div class="page-sub">{sub}</div>' if sub else "")


def sec(ic, text):
    return f'<div class="sec">{icon(ic)}<span>{esc(text)}</span></div>'


def stock_href(sym, lang="en"):
    return f"stock?symbol={sym}&lang={lang}"


def logo_circle(sym, uri=None, size=32):
    s = f"width:{size}px;height:{size}px;font-size:{max(9, int(size * 0.36))}px"
    if uri:
        return f'<span class="lg" style="{s}"><img src="{uri}" alt=""/></span>'
    h = int(hashlib.md5(str(sym).encode()).hexdigest()[:6], 16)
    hue = h % 360
    return (f'<span class="lg" style="{s};background:linear-gradient(135deg,hsl({hue},62%,46%),hsl({(hue + 40) % 360},62%,34%))">'
            f'{esc(str(sym).replace("^", "")[:2])}</span>')


def logo_obj(sym, size=40):
    """Company logo loaded by the browser (Parqet, then Financial Modeling Prep); the initials show when neither has it.
    <object> shows its inner content when the image fails, so there is never a broken-image icon."""
    s = str(sym).replace("^", "")
    h = int(hashlib.md5(s.encode()).hexdigest()[:6], 16) % 360
    ini = s[:3] if len(s) <= 3 else s[:2]
    fs = max(9, int(size * (0.3 if len(ini) == 3 else 0.36)))
    return (f'<span class="lgo" style="width:{size}px;height:{size}px">'
            f'<object data="https://assets.parqet.com/logos/symbol/{esc(s)}?format=png&amp;size=100" type="image/png" tabindex="-1" aria-hidden="true">'
            f'<object data="https://financialmodelingprep.com/image-stock/{esc(s)}.png" type="image/png" tabindex="-1" aria-hidden="true">'
            f'<span class="ini" style="font-size:{fs}px;background:linear-gradient(135deg,hsl({h},62%,46%),hsl({(h + 40) % 360},62%,34%))">{esc(ini)}</span>'
            f'</object></object></span>')


def company(sym, name="", uri=None, size=32, sub=None, href=None):
    sub_html = f'<div class="sub">{esc(sub if sub is not None else name)}</div>' if (sub or name) else ""
    inner = f'<div class="co">{logo_circle(sym, uri, size)}<div class="nm"><div class="tk">{esc(sym)}</div>{sub_html}</div></div>'
    return f'<a class="lnk" href="{href}" target="_self">{inner}</a>' if href else inner


def pill(pct, invert=False, suffix="%"):
    if pct is None or pd.isna(pct):
        return '<span class="pill neu">—</span>'
    return f'<span class="pill {cls(pct, invert)}">{pct:+.2f}{suffix}</span>'


def sparkline(values, color, w=84, h=30):
    v = np.asarray([x for x in values if pd.notna(x)], dtype=float) if values is not None else np.array([])
    if len(v) < 2:
        return ""
    lo, hi = v.min(), v.max()
    rng = hi - lo if hi > lo else 1.0
    xs = np.linspace(1, w - 1, len(v))
    ys = h - 2 - (v - lo) / rng * (h - 4)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = f"1,{h} " + pts + f" {w - 1},{h}"
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><polygon fill="{color}" opacity=".14" points="{area}"/>'
            f'<polyline fill="none" stroke="{color}" stroke-width="1.8" points="{pts}"/></svg>')


def tile(name, value, chg=None, pct=None, spark=None, sub="", invert=False, head_html=None, kind=None, chg_text=None):
    """Market tile. Positive -> light-green tile + dark-green text; negative -> light-red + dark-red."""
    c = kind or cls(pct if pct is not None else chg, invert)
    color = {"pos": POS_FG, "neg": NEG_FG, "acc": ACC_FG}.get(c, MUTED)
    if chg_text is not None:
        t = chg_text
    elif pct is not None and chg is not None:
        t = f"{chg:+,.2f} ({pct:+.2f}%)"
    elif pct is not None:
        t = f"{pct:+.2f}%"
    elif chg is not None:
        t = f"{chg:+,.2f}"
    else:
        t = ""
    svg = sparkline(spark, color) if spark is not None else ""
    head = head_html or f'<div class="t-name">{esc(name)}</div>'
    k = f" {c}" if c in ("pos", "neg", "acc") else ""
    return (f'<div class="tile{k}">{head}<div class="t-row"><div><div class="t-val">{value}</div><div class="t-chg">{t}</div></div>{svg}</div>'
            + (f'<div class="t-sub">{esc(sub)}</div>' if sub else "") + "</div>")


def tiles(items):
    return '<div class="tiles">' + "".join(items) + "</div>"


def badge(text, kind="neu", ic=None):
    return f'<span class="badge b-{kind}">{icon(ic) if ic else ""}{esc(text)}</span>'


def ticker_chip(sym, pct, uri=None, href=None):
    c = cls(pct) if pct is not None and not pd.isna(pct) else "neu"
    val = pill(pct) if pct is not None and not pd.isna(pct) else ""
    inner = f'{logo_circle(sym, uri, 20)}{esc(sym)} {val}'
    if href:
        return f'<a class="tkc {c}" href="{href}" target="_self">{inner}</a>'
    return f'<span class="tkc {c}">{inner}</span>'


def kpi(ic, label, value_html, sub="", kind=None):
    k = f" {kind}" if kind in ("pos", "neg", "acc") else ""
    return (f'<div class="kpi{k}"><div class="l">{icon(ic)}{esc(label)}</div><div class="v">{value_html}</div>'
            f'<div class="s">{sub}</div></div>')


def tape(items):
    inner = "".join(f'<span class="it"><b>{esc(n)}</b>{fmt_price(p)} {pill(c)}</span>' for n, p, c in items)
    return f'<div class="tape"><div class="track">{inner}{inner}</div></div>'


def time_ago(ts, ar=False):
    if ts is None or pd.isna(ts):
        return ""
    mins = (pd.Timestamp.now(tz="UTC") - ts).total_seconds() / 60
    if ar:
        if mins < 60:
            return f"قبل {int(max(mins, 1))} دقيقة"
        if mins < 1440:
            return f"قبل {int(mins // 60)} ساعة"
        return f"قبل {int(mins // 1440)} يوم"
    if mins < 60:
        return f"{int(max(mins, 1))}m ago"
    if mins < 1440:
        return f"{int(mins // 60)}h ago"
    return f"{int(mins // 1440)}d ago"


def iq_badge(iq, ar=False):
    """Importance score box: 10 = very important (light red + dark red), 1 = not important (light green + dark green)."""
    import newsiq
    sc = int(iq["score"])
    bg, fg, bd = newsiq.colors(sc)
    en, a = newsiq.level(sc)
    why = " · ".join(f"{r[1] if ar else r[0]} {r[2]:+.1f}" for r in iq.get("reasons", []))
    tip = f"{'الأهمية' if ar else 'Importance'} {sc}/10: {a if ar else en}" + (f" · {why}" if why else "")
    return (f'<div class="iq" style="--iqb:{bg};--iqf:{fg};--iqd:{bd}" title="{esc(tip)}"><div class="n">{sc}<small>/10</small></div>'
            f'<div class="l">{esc(a if ar else en)}</div><div class="bar"><i style="width:{sc * 10}%"></i></div></div>')


def kw_chips(iq, ar=False, limit=6):
    import newsiq
    out = []
    for key, en, a in iq.get("keywords", [])[:limit]:
        k = " op" if key == "opinion" else (" ent" if key == "entity" else "")
        out.append(f'<span class="kwc{k}">{icon(newsiq.TOPIC_ICON.get(key, "label"))}{esc(a if ar else en)}</span>')
    return '<div class="kw">' + "".join(out) + "</div>" if out else ""


def iq_legend(ar=False):
    import newsiq
    cells = "".join(f'<span style="background:{newsiq.COLORS[i][0]};color:{newsiq.COLORS[i][1]}">{i}</span>' for i in range(1, 11))
    lo, hi = ("غير هام", "هام جداً") if ar else ("Not important", "Very important")
    return (f'<div class="iqleg"><span class="muted">{esc(lo)}</span><span class="sc">{cells}</span><span class="muted">{esc(hi)}</span></div>')


# topic -> (gradient, english label, arabic label) for news pictures when the story has no photo
_TG = {"macro": "linear-gradient(135deg,#1D4ED8 0%,#4F46E5 55%,#7C3AED 100%)", "world": "linear-gradient(135deg,#B45309 0%,#EA580C 55%,#DC2626 100%)",
       "company": "linear-gradient(135deg,#047857 0%,#0D9488 55%,#0891B2 100%)", "deal": "linear-gradient(135deg,#7C3AED 0%,#A21CAF 55%,#DB2777 100%)",
       "risk": "linear-gradient(135deg,#991B1B 0%,#BE123C 60%,#E11D48 100%)", "tech": "linear-gradient(135deg,#0369A1 0%,#2563EB 55%,#06B6D4 100%)",
       "crypto": "linear-gradient(135deg,#C2410C 0%,#EA580C 50%,#F59E0B 100%)", "commod": "linear-gradient(135deg,#854D0E 0%,#CA8A04 55%,#EAB308 100%)",
       "market": "linear-gradient(135deg,#1E3A8A 0%,#2563EB 50%,#0EA5E9 100%)"}
_TOPIC_GROUP = {"fed": "macro", "inflation": "macro", "jobs": "macro", "economy": "macro", "bonds": "macro", "trade": "world", "geo": "world",
                "policy": "world", "earnings": "company", "guidance": "company", "analyst": "company", "payout": "company", "mna": "deal", "ipo": "deal",
                "legal": "risk", "distress": "risk", "layoffs": "risk", "health": "tech", "ai": "tech", "product": "tech", "crypto": "crypto",
                "oil": "commod", "metals": "commod", "fx": "commod", "move": "market", "street": "market"}


def _safe_img(url):
    u = str(url or "").strip()
    if not u or not u.startswith(("http://", "https://")) or any(x in u.lower() for x in ("1x1", "pixel", "spacer", "blank.gif")):
        return ""
    return "https://" + u[7:] if u.startswith("http://") else u


def news_thumb(n, big=False):
    """Picture for a story: the outlet's photo when there is one, otherwise a topic picture (never a broken-image icon:
    if the photo cannot load, the topic picture is drawn in its place). The first affected company's logo sits in the corner."""
    import newsiq
    iq = n.get("iq") or {}
    topic = next((t for t in iq.get("topics", []) if t in _TOPIC_GROUP), "street")
    ic = newsiq.TOPIC_ICON.get(topic, "show_chart")
    grad = _TG[_TOPIC_GROUP.get(topic, "market")]
    lab = next(((en, ar) for key, en, ar, *_ in newsiq.TOPICS if key == topic), ("Markets", "الأسواق"))
    tick = [t for t in (n.get("tickers") or []) if t][:1]
    lg = f'<span class="nlg">{logo_obj(tick[0], 34 if big else 30)}</span>' if tick else ""
    url = _safe_img(n.get("img"))
    cls = "nth big" if big else "nth"
    if url:
        return (f'<span class="{cls}" style="--g:{grad}"><img src="{esc(url)}" alt="" loading="lazy" referrerpolicy="no-referrer" '
                f'data-ic="{ic}">{lg}</span>')
    return (f'<span class="{cls} fb" style="--g:{grad}"><span class="ms">{ic}</span>'
            f'<em data-en="{esc(lab[0])}" data-ar="{esc(lab[1])}"></em>{lg}</span>')


def also_badge(also, ar=False):
    """'+3' next to the outlet: the same story was also reported by other outlets (names on hover)."""
    also = [a for a in (also or []) if a]
    if not also:
        return ""
    tip = ("نشرته أيضاً: " + "، ".join(also)) if ar else ("Also reported by: " + ", ".join(also))
    return f' <span class="also" title="{esc(tip)}">+{len(also)}</span>'


def news_card(n, title, summary, chips="", aff_label="", ar=False, tag=None, iq=None, ui_ar=None):
    """News card. iq = newsiq.analyze(...) adds the importance box, a colored edge and keyword chips."""
    import newsiq
    ui_ar = ar if ui_ar is None else ui_ar
    summary = summary or ""
    short = esc(summary[:300]) + ("…" if len(summary) > 300 else "")
    tag_html = f"{badge(tag, 'acc')} " if tag else ""
    aff = f'<div class="aff"><span class="lbl">{esc(aff_label)}</span>{chips}</div>' if chips else ""
    rtl = " rtl" if ar else ""
    head = (f'<div class="nb">{tag_html}<a class="t" href="{esc(n["link"])}" target="_blank">{esc(title)}</a>'
            f'<div class="meta">{icon("schedule")} {esc(n["source"])}{also_badge(n.get("also"), ui_ar)} · {time_ago(n["time"], ar)}</div></div>')
    pic = news_thumb(n)
    if iq:
        edge = newsiq.colors(iq["score"])[2]
        return (f'<div class="news hasiq{rtl}" style="--iqd:{edge}"><div class="nwrap">{pic}<div class="nbody"><div class="nh">{head}{iq_badge(iq, ui_ar)}</div>'
                + (f'<div class="sum">{short}</div>' if short else "") + kw_chips(iq, ui_ar) + aff + "</div></div></div>")
    return (f'<div class="news{rtl}"><div class="nwrap">{pic}<div class="nbody"><div class="nh">{head}</div>'
            + (f'<div class="sum">{short}</div>' if short else "") + aff + "</div></div></div>")


def market_status(ar=False):
    now = datetime.now(ZoneInfo("America/New_York"))
    t = now.hour * 60 + now.minute
    kind, _ = mcal.day_status(now.date())
    close = 780 if kind == "early" else 960          # 1:00 pm on early-close days
    if now.weekday() >= 5:
        state, dot = ("السوق مغلق (عطلة)" if ar else "Closed · Weekend"), "closed"
    elif kind == "closed":
        state, dot = ("السوق مغلق (إجازة رسمية)" if ar else "Closed · Holiday"), "closed"
    elif 570 <= t < close:
        state, dot = ("السوق مفتوح" if ar else "Market Open"), "live"
    elif 240 <= t < 570:
        state, dot = ("ما قبل الافتتاح" if ar else "Pre-Market"), "pre"
    elif close <= t < 1200:
        state, dot = ("ما بعد الإغلاق" if ar else "After-Hours"), "pre"
    else:
        state, dot = ("السوق مغلق" if ar else "Market Closed"), "closed"
    return f'<span class="status" title="{state} · {now:%H:%M} ET"><span class="dot {dot}"></span><b>{state}</b><span class="muted">· {now:%H:%M} ET</span></span>'


# ---------------------------------------------------------------- modern widgets
RATING_COLORS = ["#EF4444", "#F87171", "#64748B", "#4ADE80", "#22C55E"]


def rating_meter(score, label, title, counts=None, labels=("Strong Sell", "Sell", "Neutral", "Buy", "Strong Buy")):
    """Segmented rating bar with a pointer (score in -1..1). counts: [(text, kind), ...]."""
    pos = max(0.0, min(100.0, (score + 1) / 2 * 100))
    kind = "pos" if score > 0.1 else ("neg" if score < -0.1 else "neu")
    bg = {"pos": f"background:{POS_BG};color:{POS_FG}", "neg": f"background:{NEG_BG};color:{NEG_FG}",
          "neu": f"background:{NEU_BG};color:{NEU_FG}"}[kind]
    segs = "".join(f'<span style="background:{c}"></span>' for c in RATING_COLORS)
    cnt = "".join(f'<span class="pill {k}" style="min-width:0">{esc(t)}</span>' for t, k in (counts or []))
    return (f'<div class="rmeter"><div class="rt">{esc(title)}</div><div class="rv" style="{bg}">{esc(label)}</div>'
            f'<div class="rbar">{segs}<i style="left:calc({pos:.1f}% - 8px)"></i></div>'
            f'<div class="rlab">{"".join(f"<span>{esc(x)}</span>" for x in labels)}</div><div class="rcnt">{cnt}</div></div>')


def ladder(levels, price, now_label="Price"):
    """levels: [(name, value, 'res'|'sup'|'piv')] -> vertical price ladder with the current price highlighted."""
    rows = sorted(levels, key=lambda x: -x[1])
    out, placed = [], False
    for name, v, kind in rows:
        if not placed and v < price:
            out.append(f'<div class="lr now"><span class="ln">{esc(now_label)}</span><span class="lp">{fmt_price(price)}</span><span></span></div>')
            placed = True
        d = (v / price - 1) * 100
        out.append(f'<div class="lr {kind}"><span class="ln">{esc(name)}</span><span class="lp">{fmt_price(v)}</span>{pill(d)}</div>')
    if not placed:
        out.append(f'<div class="lr now"><span class="ln">{esc(now_label)}</span><span class="lp">{fmt_price(price)}</span><span></span></div>')
    return '<div class="ladder">' + "".join(out) + "</div>"


def ring(pct, size=150, color=ACCENT, label="", sub="", track=BORDER, stroke=14):
    r = (size - stroke) / 2
    c = 2 * np.pi * r
    off = c * (1 - max(0, min(100, pct)) / 100)
    gid = f"rg{abs(hash((pct, color, size))) % 10**6}"
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="display:block;margin:auto">'
            f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{color}"/>'
            f'<stop offset="1" stop-color="{VIOLET}"/></linearGradient></defs>'
            f'<circle cx="{size / 2}" cy="{size / 2}" r="{r}" stroke="{track}" stroke-width="{stroke}" fill="none"/>'
            f'<circle cx="{size / 2}" cy="{size / 2}" r="{r}" stroke="url(#{gid})" stroke-width="{stroke}" fill="none" stroke-linecap="round" '
            f'stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}" transform="rotate(-90 {size / 2} {size / 2})"/>'
            f'<text x="50%" y="48%" text-anchor="middle" font-size="{size * 0.2:.0f}" font-weight="800" fill="#fff" font-family="{FONT}">{esc(label)}</text>'
            f'<text x="50%" y="64%" text-anchor="middle" font-size="{size * 0.085:.0f}" fill="{MUTED}" font-family="{FONT}">{esc(sub)}</text></svg>')


def pulse_gauge(pct, title, sub=""):
    """Semicircle gauge 0-100 with gradient arc and needle (market breadth)."""
    pct = max(0.0, min(100.0, pct))
    ang = np.pi * (1 - pct / 100)
    cx, cy, r = 150, 150, 110
    nx, ny = cx + (r - 20) * np.cos(ang), cy - (r - 20) * np.sin(ang)
    kind = "pos" if pct > 55 else ("neg" if pct < 45 else "neu")
    col = {"pos": POS_FG, "neg": NEG_FG, "neu": NEU_FG}[kind]
    bgc = {"pos": POS_BG, "neg": NEG_BG, "neu": NEU_BG}[kind]
    return (f'<svg viewBox="0 0 300 236" style="width:100%;max-width:340px;display:block;margin:auto">'
            '<defs><linearGradient id="pg" x1="0" x2="1"><stop offset="0" stop-color="#EF4444"/><stop offset=".5" stop-color="#F5B94A"/>'
            '<stop offset="1" stop-color="#22C55E"/></linearGradient></defs>'
            f'<path d="M40 150 A110 110 0 0 1 260 150" fill="none" stroke="{BORDER}" stroke-width="22" stroke-linecap="round"/>'
            '<path d="M40 150 A110 110 0 0 1 260 150" fill="none" stroke="url(#pg)" stroke-width="22" stroke-linecap="round" opacity=".95"/>'
            f'<line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="#fff" stroke-width="5" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="9" fill="#fff"/>'
            f'<rect x="100" y="166" width="100" height="30" rx="9" fill="{bgc}"/>'
            f'<text x="150" y="187" text-anchor="middle" font-size="18" font-weight="800" fill="{col}" font-family="{FONT}">{pct:.0f}%</text>'
            f'<text x="150" y="214" text-anchor="middle" font-size="12.5" font-weight="700" fill="#C9D0DC" font-family="{FONT}">{esc(title)}</text>'
            f'<text x="150" y="231" text-anchor="middle" font-size="11.5" fill="{MUTED}" font-family="{FONT}">{esc(sub)}</text></svg>')


def progress_bars(items):
    """items: [(label, value_text, pct 0-100, color)]"""
    return '<div class="bars">' + "".join(
        f'<div class="b"><div class="t"><span>{esc(l)}</span><span class="num">{esc(v)}</span></div>'
        f'<div class="trk"><span style="width:{max(0, min(100, p)):.1f}%;background:{c}"></span></div></div>' for l, v, p, c in items) + "</div>"


def ad_bar(adv, dec, unch=0):
    tot = max(adv + dec + unch, 1)
    return (f'<div class="adbar"><span style="width:{adv / tot * 100:.1f}%;background:{UP}"></span>'
            f'<span style="width:{unch / tot * 100:.1f}%;background:#64748B"></span>'
            f'<span style="width:{dec / tot * 100:.1f}%;background:{DOWN}"></span></div>')


def sector_card(name, etf, d1, w1, m1, spark=None, href=None):
    c = cls(d1)
    bg, fg = {"pos": (POS_BG, POS_FG), "neg": (NEG_BG, NEG_FG)}.get(c, (CARD2, TEXT))
    sp = sparkline(spark, fg, 70, 24) if spark is not None else ""
    f = lambda v: f"{v:+.1f}%" if v is not None and pd.notna(v) else "—"
    return (f'<div class="sc" style="background:{bg};color:{fg}"><div class="h"><span>{esc(name)}</span><span style="opacity:.7">{esc(etf)}</span></div>'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-end"><div class="v">{f(d1)}</div>{sp}</div>'
            f'<div class="f"><span>1W {f(w1)}</span><span>1M {f(m1)}</span></div></div>')


# ---------------------------------------------------------------- animated skyline hero
def _windows(x0, y0, w, h, cols, rows, seed):
    rng = np.random.default_rng(seed)
    out = []
    cw, rh = w / cols, h / rows
    for r in range(rows):
        for c in range(cols):
            if rng.random() < 0.55:
                out.append(f'<rect class="win" x="{x0 + c * cw + cw * 0.28:.1f}" y="{y0 + r * rh + rh * 0.3:.1f}" width="{cw * 0.44:.1f}" '
                           f'height="{rh * 0.4:.1f}" style="animation-duration:{rng.uniform(2.5, 9):.1f}s;animation-delay:-{rng.uniform(0, 8):.1f}s"/>')
    return "".join(out)


LINE_PTS = [(0, 210), (90, 200), (160, 215), (240, 180), (320, 190), (400, 150), (470, 165), (560, 120), (640, 140),
            (720, 100), (800, 115), (880, 80), (960, 98), (1040, 60), (1120, 75), (1200, 45), (1300, 58), (1400, 30)]
LINE_PATH = "M" + " L".join(f"{x} {y}" for x, y in LINE_PTS)
HERO_CSS = f"""<style>
.hero .win {{ fill:#9CC3FF; opacity:.7; animation-name: twinkle; animation-iteration-count: infinite; animation-timing-function: ease-in-out; }}
.hero .star {{ fill:#fff; animation: twinkle 4s ease-in-out infinite; }}
@keyframes twinkle {{ 0%,100% {{ opacity:.85; }} 50% {{ opacity:.08; }} }}
.hero .mline {{ stroke-dasharray: 2600; stroke-dashoffset: 2600; animation: draw 9s ease-in-out infinite; }}
@keyframes draw {{ 0% {{ stroke-dashoffset:2600; }} 60%,100% {{ stroke-dashoffset:0; }} }}
.hero .mdot {{ offset-path: path('{LINE_PATH}'); offset-rotate: 0deg; animation: travel 9s ease-in-out infinite; }}
@keyframes travel {{ 0% {{ offset-distance:0%; }} 60%,100% {{ offset-distance:100%; }} }}
.hero .beam {{ animation: beam 7s ease-in-out infinite; transform-origin: 907px 20px; }}
@keyframes beam {{ 0%,100% {{ transform: rotate(-18deg); opacity:.16; }} 50% {{ transform: rotate(18deg); opacity:.3; }} }}
</style>"""


def _skyline():
    back, front = "#0f2247", "#070d1c"
    s = []
    rng = np.random.default_rng(7)
    for _ in range(40):
        s.append(f'<circle class="star" cx="{rng.uniform(0, 1400):.0f}" cy="{rng.uniform(5, 150):.0f}" r="{rng.uniform(0.6, 1.6):.1f}" '
                 f'style="animation-delay:-{rng.uniform(0, 4):.1f}s"/>')
    s.append('<defs><linearGradient id="ln" x1="0" x2="1"><stop offset="0" stop-color="#22D3EE" stop-opacity="0"/>'
             '<stop offset=".35" stop-color="#3D7BFF"/><stop offset="1" stop-color="#A78BFA"/></linearGradient>'
             '<linearGradient id="bm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9CC3FF" stop-opacity=".9"/>'
             '<stop offset="1" stop-color="#9CC3FF" stop-opacity="0"/></linearGradient>'
             '<filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    s.append('<path class="beam" d="M907 20 L760 350 L1054 350 Z" fill="url(#bm)"/>')
    s.append(f'<g fill="{back}"><rect x="640" y="150" width="70" height="200"/><rect x="720" y="120" width="55" height="230"/>'
             '<rect x="1130" y="140" width="80" height="210"/><rect x="1220" y="170" width="60" height="180"/>'
             '<rect x="520" y="175" width="60" height="175"/><rect x="1300" y="130" width="70" height="220"/>'
             '<path d="M1010 350 L1010 95 Q1075 150 1080 350 Z"/><rect x="1004" y="80" width="4" height="20"/>'
             '<path d="M880 350 L880 170 L890 170 L890 120 L898 120 L898 70 L904 70 L904 20 L907 20 L910 70 L916 70 L916 120 L924 120 '
             'L924 170 L934 170 L934 350 Z"/></g>')
    s.append(f'<path class="mline" d="{LINE_PATH}" fill="none" stroke="url(#ln)" stroke-width="2.6" filter="url(#glow)"/>')
    s.append('<circle class="mdot" r="5" fill="#22D3EE" filter="url(#glow)"/>')
    s.append(f'<g fill="{front}"><rect x="150" y="248" width="230" height="102"/><path d="M140 250 L265 205 L390 250 Z"/>'
             '<rect x="140" y="248" width="250" height="8"/><rect x="0" y="210" width="80" height="140"/><rect x="85" y="185" width="55" height="165"/>'
             '<path d="M400 350 L400 170 L412 170 L412 130 L424 130 L424 95 L432 95 L432 55 L436 55 L436 95 L444 95 L444 130 L456 130 L456 170 '
             'L468 170 L468 350 Z"/><rect x="480" y="230" width="75" height="120"/><rect x="590" y="200" width="60" height="150"/>'
             '<rect x="780" y="215" width="80" height="135"/><rect x="950" y="235" width="50" height="115"/>'
             '<rect x="1090" y="225" width="45" height="125"/><rect x="1370" y="205" width="40" height="145"/></g>')
    s.append("".join(f'<rect x="{165 + i * 28}" y="262" width="10" height="84" fill="#10234a"/>' for i in range(8)))
    s.append(_windows(0, 220, 80, 120, 4, 6, 1) + _windows(85, 195, 55, 150, 3, 7, 2) + _windows(400, 180, 68, 165, 3, 9, 3)
             + _windows(480, 240, 75, 105, 4, 5, 4) + _windows(590, 210, 60, 135, 3, 7, 5) + _windows(780, 225, 80, 120, 4, 6, 6)
             + _windows(950, 245, 50, 100, 2, 5, 8) + _windows(1090, 235, 45, 110, 2, 5, 9) + _windows(1370, 215, 40, 130, 2, 6, 10))
    return ('<svg class="city" viewBox="0 0 1400 350" preserveAspectRatio="xMidYMax slice" xmlns="http://www.w3.org/2000/svg">'
            + "".join(s) + "</svg>")


_SKYLINE = None


def hero(eyebrow, title_html, tagline, chips_html, rtl=False):
    global _SKYLINE
    if _SKYLINE is None:
        _SKYLINE = _skyline()
    wrap = ' class="rtl"' if rtl else ""
    return (f'{HERO_CSS}<div{wrap}><div class="hero">{_SKYLINE}<div class="content"><div class="eyebrow">{esc(eyebrow)}</div>'
            f'<div class="title">{title_html}</div><div class="tagline">{esc(tagline)}</div><div class="chips">{chips_html}</div></div></div></div>')




def svg_data_uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


# ---------------------------------------------------------------- trading-dashboard widgets
def money(v, dec=0, short=False):
    """$1,234 / -$1,234 / $1.2K (sign before the dollar)."""
    if v is None or pd.isna(v):
        return "—"
    sign = "-" if v < 0 else ""
    a = abs(float(v))
    if short and a >= 1000:
        for unit, div in (("M", 1e6), ("K", 1e3)):
            if a >= div:
                return f"{sign}${a / div:.1f}{unit}"
    return f"{sign}${a:,.{dec}f}"


def pbox(text, v=None, kind=None):
    """Value inside a pastel box: light green + dark green (positive) / light red + dark red (negative)."""
    k = kind or cls(v)
    return f'<span class="pbox {k}">{text}</span>'


def semi(pct, value_text=None, size=150):
    """Half-circle gauge 0-100 (green arc when >= 50, red below) with a pastel value box."""
    pct = max(0.0, min(100.0, float(pct)))
    kind = "pos" if pct >= 50 else "neg"
    col = UP if kind == "pos" else DOWN
    r, cx, cy = 52, 75, 68
    ang = np.pi * (1 - pct / 100)
    ex, ey = cx + r * np.cos(ang), cy - r * np.sin(ang)
    bg, fg = (POS_BG, POS_FG) if kind == "pos" else (NEG_BG, NEG_FG)
    txt = value_text or f"{pct:.1f}%"
    arc = (f'<path d="M{cx - r} {cy} A{r} {r} 0 0 1 {ex:.1f} {ey:.1f}" fill="none" stroke="{col}" stroke-width="12" stroke-linecap="round"/>'
           if pct > 0.5 else "")
    return (f'<svg width="{size}" height="{size * 0.62:.0f}" viewBox="0 0 150 93">'
            f'<path d="M{cx - r} {cy} A{r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="{BORDER}" stroke-width="12" stroke-linecap="round"/>{arc}'
            f'<rect x="{cx - 36}" y="{cy - 20}" width="72" height="26" rx="8" fill="{bg}"/>'
            f'<text x="{cx}" y="{cy - 2}" text-anchor="middle" font-size="15" font-weight="800" fill="{fg}" font-family="{FONT}">{esc(txt)}</text></svg>')


def goal(pct_of_goal, left, right, met=False):
    w = max(0.0, min(100.0, pct_of_goal))
    return (f'<div class="goal{" met" if met else ""}"><div class="gt"><span>{esc(left)}</span><span>{esc(right)}</span></div>'
            f'<div class="gb"><span style="width:{w:.0f}%"></span></div></div>')


FG_ZONES = [(0, 25, "Extreme fear", "خوف شديد", "neg"), (25, 45, "Fear", "خوف", "neg"), (45, 55, "Neutral", "محايد", "neu"),
            (55, 75, "Greed", "طمع", "pos"), (75, 101, "Extreme greed", "طمع شديد", "pos")]
FG_COLORS = ["#EF4444", "#F97316", "#94A3B8", "#84CC16", "#22C55E"]


def fg_zone(v):
    for lo, hi, en, ar, kind in FG_ZONES:
        if lo <= v < hi:
            return en, ar, kind
    return FG_ZONES[-1][2:]


def fg_gauge(v, ar=False, sub=""):
    """Fear & Greed dial: five colored zones, a needle and the value in a pastel box."""
    v = max(0.0, min(100.0, float(v)))
    cx, cy, r = 160, 158, 118
    def pt(p, rr):
        a = np.pi * (1 - p / 100)
        return cx + rr * np.cos(a), cy - rr * np.sin(a)
    arcs = []
    for (lo, hi, *_), col in zip(FG_ZONES, FG_COLORS):
        x0, y0 = pt(lo + 0.9, r)
        x1, y1 = pt(min(hi, 100) - 0.9, r)
        arcs.append(f'<path d="M{x0:.1f} {y0:.1f} A{r} {r} 0 0 1 {x1:.1f} {y1:.1f}" fill="none" stroke="{col}" stroke-width="24" stroke-linecap="butt" opacity=".92"/>')
    ticks = "".join(f'<text x="{pt(t, r + 26)[0]:.1f}" y="{pt(t, r + 26)[1] + 4:.1f}" text-anchor="middle" font-size="11" fill="{MUTED}" '
                    f'font-family="{FONT}">{t}</text>' for t in (0, 25, 50, 75, 100))
    nx, ny = pt(v, r - 30)
    en, a, kind = fg_zone(v)
    bg, fg = {"pos": (POS_BG, POS_FG), "neg": (NEG_BG, NEG_FG)}.get(kind, (NEU_BG, NEU_FG))
    label = a if ar else en
    return (f'<svg viewBox="0 0 320 250" style="width:100%;max-width:380px;display:block;margin:auto">'
            f'<path d="M{cx - r} {cy} A{r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="{BORDER}" stroke-width="30"/>{"".join(arcs)}{ticks}'
            f'<line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="#fff" stroke-width="5" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="10" fill="#fff"/><circle cx="{cx}" cy="{cy}" r="4" fill="{BG}"/>'
            f'<rect x="{cx - 62}" y="{cy + 20}" width="124" height="42" rx="12" fill="{bg}"/>'
            f'<text x="{cx}" y="{cy + 49}" text-anchor="middle" font-size="26" font-weight="800" fill="{fg}" font-family="{FONT}">{v:.0f}</text>'
            f'<text x="{cx}" y="{cy + 84}" text-anchor="middle" font-size="15" font-weight="800" fill="#fff" font-family="{FONT}">{esc(label)}</text>'
            + (f'<text x="{cx}" y="{cy + 102}" text-anchor="middle" font-size="11" fill="{MUTED}" font-family="{FONT}">{esc(sub)}</text>' if sub else "")
            + "</svg>")

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.8"
