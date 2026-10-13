"""
p_xbots.py - The X Bots page of the current market: its five bots that read X (Twitter) and trade what they read on paper
(xbots.py). The US market and the Saudi market each have their own five, and the page shows the market the visitor is in.

The page only shows what the bots stored on their last run (scripts/xbots_run.py, every hour of their market's day): it never
reads X itself, so opening it costs nothing.
"""
import hashlib
import math

import pandas as pd
import streamlit as st

import charts
import data
import markets as MK
import theme as T
import ui
import xbots as XB
from i18n import L, is_ar

ss = st.session_state
COST = 0.005                        # what X charges for one post read (pay per use), in dollars

CSS = """<style>
.xbhero { display:flex; flex-wrap:wrap; gap:12px 22px; align-items:center; justify-content:space-between; padding:14px 18px; border-radius:18px;
  background:linear-gradient(135deg, rgba(59,139,235,.14), rgba(123,69,240,.12) 60%, rgba(26,22,36,.9)); border:1px solid rgba(167,139,250,.28); }
.xbhero .st { display:flex; align-items:center; gap:10px; font-weight:700; color:#fff; }
.xbhero .st i { width:10px; height:10px; border-radius:50%; background:#F5B94A; box-shadow:0 0 0 4px rgba(245,185,74,.18); }
.xbhero .st.on i { background:#34D27A; box-shadow:0 0 0 4px rgba(52,210,122,.18); animation:xbpulse 1.8s ease-in-out infinite; }
.xbhero .st.err i { background:#F26B6B; box-shadow:0 0 0 4px rgba(242,107,107,.18); }
.xbhero .st small { display:block; font-weight:500; color:#B9B3C4; font-size:.76rem; margin-top:2px; }
@keyframes xbpulse { 50% { box-shadow:0 0 0 8px rgba(52,210,122,0); } }
.xbhero .facts { display:flex; flex-wrap:wrap; gap:8px 22px; align-items:center; color:#B9B3C4; font-size:.8rem; }
.xbhero .facts b { color:#fff; font-variant-numeric:tabular-nums; }
.xbhero .facts .f { display:flex; align-items:center; gap:8px; }
.xbhero .facts .f span { display:flex; flex-direction:column; line-height:1.25; }
.xbhero .facts svg { flex:none; }
.xbhero .mk { display:inline-flex; align-items:center; gap:6px; padding:3px 10px; border-radius:99px; background:rgba(255,255,255,.07); color:#E7E3EB; font-size:.76rem; }
.xbhero .mk i { width:7px; height:7px; border-radius:50%; background:#8F899B; }
.xbhero .mk.live i { background:#34D27A; } .xbhero .mk.pre i { background:#F5B94A; }
.xbg { display:grid; grid-template-columns:repeat(5, minmax(0,1fr)); gap:12px; margin:8px 0 2px; }
@media (max-width: 1250px) { .xbg { grid-template-columns:repeat(3, minmax(0,1fr)); } }
@media (max-width: 760px) { .xbg { grid-template-columns:1fr; } }
.xbc { position:relative; display:flex; flex-direction:column; gap:9px; padding:14px 14px 12px; border-radius:18px; overflow:hidden; min-width:0;
  background:linear-gradient(160deg, rgba(36,28,58,.95), rgba(20,16,32,.95)); border:1px solid rgba(157,151,165,.22);
  transition:transform .18s ease, border-color .18s ease, box-shadow .18s ease; }
.xbc:hover { transform:translateY(-3px); border-color:rgba(167,139,250,.5); box-shadow:0 18px 36px -22px rgba(123,69,240,.8); }
.xbc.sel { border-color:var(--xc); box-shadow:0 0 0 1px var(--xc), 0 18px 40px -22px var(--xc); }
.xbc::before { content:""; position:absolute; inset:0 0 auto 0; height:3px; background:linear-gradient(90deg, var(--xc), transparent 140%); }
.xbc .rk { display:inline-block; padding:0 6px; border-radius:99px; font-size:.66rem; font-weight:800; color:#B9B3C4; background:rgba(255,255,255,.08); letter-spacing:.03em; margin-inline-end:4px; }
.xbc .rk.top { color:#1A1624; background:#F5B94A; }
.xbc .hd { display:flex; align-items:center; gap:10px; }
.xbc .ic { flex:none; width:38px; height:38px; border-radius:12px; display:grid; place-items:center; color:#fff;
  background:linear-gradient(140deg, var(--xc), rgba(255,255,255,.12)); box-shadow:0 10px 22px -12px var(--xc); }
.xbc .ic .ms { font-size:1.3rem; }
.xbc .nm { min-width:0; } .xbc .nm b { display:block; color:#fff; font-size:.92rem; line-height:1.25; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.xbc .nm small { display:flex; align-items:center; gap:4px; color:#8F899B; font-size:.72rem; white-space:nowrap; }
.xbc .beat { color:#B9B3C4; font-size:.77rem; line-height:1.5; min-height:3.1em; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
.xbc .eq { display:flex; align-items:flex-end; justify-content:space-between; gap:8px; }
.xbc .eq .v { display:flex; flex-direction:row; align-items:center; flex-wrap:wrap; gap:3px 8px; color:#fff; font-weight:800; font-size:1rem; font-variant-numeric:tabular-nums; line-height:1.1; min-width:0; }
.xbc .eq .v small { flex-basis:100%; color:#8F899B; font-weight:500; font-size:.7rem; }
.xbc .eq .v .n { white-space:nowrap; } .xbc .eq .v .n em { font-style:normal; font-weight:600; font-size:.72rem; color:#B9B3C4; margin-inline-end:3px; }
.xbc .eq .v .pill, .xbc .eq .v [class*="pill"] { font-size:.72rem; }
.xbc .sp { margin-top:-4px; } .xbc .sp svg { width:100%; height:30px; display:block; }
.xbc .gg { display:flex; align-items:center; gap:10px; }
.xbc .gg svg { flex:none; }
.xbc .gg .t { display:flex; flex-direction:column; line-height:1.2; font-size:.72rem; color:#8F899B; }
.xbc .gg .t b { font-size:.95rem; font-variant-numeric:tabular-nums; }
.xbc .slots { display:flex; align-items:center; gap:5px; font-size:.72rem; color:#8F899B; }
.xbc .slots i { width:9px; height:9px; border-radius:3px; background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.14); }
.xbc .slots i.on { background:var(--xc); border-color:transparent; }
.xbc .slots span { margin-inline-start:4px; }
.xbc .stt { font-size:.72rem; color:#8F899B; display:flex; align-items:center; gap:6px; padding-top:8px; border-top:1px solid rgba(255,255,255,.07); }
.xbc .stt i { width:7px; height:7px; border-radius:50%; background:#F5B94A; flex:none; }
.xbc .stt.on i { background:#34D27A; } .xbc .stt.err i { background:#F26B6B; }
.xbd { display:flex; align-items:center; gap:14px; flex-wrap:wrap; padding:14px 16px; border-radius:18px; margin:6px 0 10px;
  background:linear-gradient(120deg, color-mix(in srgb, var(--xc) 16%, transparent), rgba(26,22,36,.6) 70%); border:1px solid color-mix(in srgb, var(--xc) 40%, transparent); }
.xbd .ic { flex:none; width:46px; height:46px; border-radius:14px; display:grid; place-items:center; color:#fff; background:linear-gradient(140deg, var(--xc), rgba(255,255,255,.12)); }
.xbd .ic .ms { font-size:1.55rem; }
.xbd .tx { flex:1 1 320px; min-width:0; }
.xbd .tx b { display:block; color:#fff; font-size:1.1rem; }
.xbd .tx p { margin:3px 0 8px; color:#B9B3C4; font-size:.84rem; line-height:1.55; }
.xbd .chips { display:flex; flex-wrap:wrap; gap:6px; }
.xbd .chips span { display:inline-flex; align-items:center; gap:5px; padding:4px 10px; border-radius:99px; font-size:.74rem; color:#E7E3EB;
  background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.1); font-variant-numeric:tabular-nums; }
.xbd .chips span .ms { font-size:.95rem; color:var(--xc); }
.xbempty { display:flex; align-items:center; gap:12px; padding:16px; border-radius:14px; border:1px dashed rgba(157,151,165,.3); color:#B9B3C4; font-size:.86rem;
  background:rgba(255,255,255,.02); min-height:88px; }
.xbempty .ms { color:#8F899B; font-size:1.4rem; }
.xpost { display:flex; flex-direction:column; gap:6px; padding:12px 14px; border-radius:14px; background:rgba(255,255,255,.03);
  border:1px solid rgba(157,151,165,.16); margin-bottom:8px; border-inline-start:3px solid rgba(157,151,165,.3); }
.xpost.bull { border-inline-start-color:#4ADE80; } .xpost.bear { border-inline-start-color:#F87171; }
.xpost .who { display:flex; align-items:center; gap:8px; font-size:.8rem; color:#8F899B; flex-wrap:wrap; }
.xpost .who b { color:#fff; } .xpost .who .vf { color:#79B8F4; font-size:.95rem; }
.xpost .tx { color:#E7E3EB; font-size:.9rem; line-height:1.6; white-space:pre-wrap; overflow-wrap:anywhere; }
.xpost .ft { display:flex; align-items:center; gap:8px; flex-wrap:wrap; font-size:.76rem; color:#8F899B; }
.xpost .tag { padding:2px 9px; border-radius:99px; font-weight:700; font-size:.72rem; border:1px solid currentColor; font-variant-numeric:tabular-nums; }
.xpost .tag.bull { color:#4ADE80; background:rgba(74,222,128,.08); } .xpost .tag.bear { color:#F87171; background:rgba(248,113,113,.08); }
.xpost .tag.neutral { color:#C4B5FD; background:rgba(167,139,250,.08); }
.xpost .ev { padding:2px 8px; border-radius:99px; background:rgba(255,255,255,.06); font-size:.7rem; }
.xpost a.go { margin-inline-start:auto; color:#79B8F4 !important; text-decoration:none !important; font-weight:600; }
.xrules { padding:14px 16px; border-radius:14px; border:1px dashed rgba(167,139,250,.35); background:rgba(123,69,240,.06); color:#D8D3E2;
  font-size:.88rem; line-height:1.75; }
.xrules b { color:#fff; }
/* the bot picker in the site's tab look: a frosted track, the chosen bot a lit blue-violet pill, the others light up under the pointer */
[class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] { display:flex; flex-wrap:wrap; gap:6px; padding:6px; border-radius:16px; width:fit-content; max-width:100%;
  background:linear-gradient(180deg, rgba(30,24,46,.80), rgba(16,12,28,.80)); border:1px solid rgba(157,151,165,.20);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.05), 0 10px 26px -16px rgba(0,0,0,.8); backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px); }
[class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] button { height:44px; padding:0 18px; border-radius:12px !important; border:none !important; background:transparent;
  color:#C2BCCD; font-weight:600; font-size:.98rem; box-shadow:none; transition:color .2s, background-color .2s, transform .2s, box-shadow .2s; }
[class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] button:active { transform:scale(.97); }
[class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] button p { color:inherit; font-size:inherit; font-weight:inherit; margin:0; }
[class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] button [data-testid="stIconMaterial"], [class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] button [role="img"]
  { color:#79B8F4; font-size:1.15em; margin-inline-end:3px; transition:transform .25s cubic-bezier(.3,1.6,.5,1), color .2s; }
[class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] button:hover { color:#fff; background-color:rgba(255,255,255,.06); }
[class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] button:hover [data-testid="stIconMaterial"] { transform:translateY(-1px) scale(1.12); }
[class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] button[kind="segmented_controlActive"], [class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] button[aria-checked="true"]
  { color:#fff; font-weight:700; background:linear-gradient(135deg, #3B8BEB, #7B45F0); box-shadow:0 8px 20px -8px rgba(91,124,242,.8), inset 0 1px 0 rgba(255,255,255,.25); }
[class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] button[kind="segmented_controlActive"] [data-testid="stIconMaterial"],
[class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] button[aria-checked="true"] [data-testid="stIconMaterial"] { color:#fff; }
[class*="st-key-xb_pick_"] [data-testid="stButtonGroup"] button:focus-visible { box-shadow:0 0 0 2px rgba(121,184,244,.75); }
.xvd { display:inline-flex; align-items:center; gap:6px; padding:3px 10px; border-radius:99px; font-size:.74rem; font-weight:700; white-space:nowrap;
  border:1px solid currentColor; }
.xvd i { width:7px; height:7px; border-radius:50%; background:currentColor; }
.xvd.truthful { color:#4ADE80; background:rgba(74,222,128,.08); } .xvd.noise { color:#B9B3C4; background:rgba(185,179,196,.06); }
.xvd.reversed { color:#F5B94A; background:rgba(245,185,74,.08); } .xvd.collecting { color:#79B8F4; background:rgba(121,184,244,.08); }
.xlog { display:inline-flex; align-items:center; gap:7px; padding:4px 11px; border-radius:99px; font-size:.74rem; color:#D8D3E2;
  background:rgba(52,210,122,.08); border:1px solid rgba(52,210,122,.35); }
.xlog i { width:8px; height:8px; border-radius:50%; background:#34D27A; box-shadow:0 0 0 3px rgba(52,210,122,.18); }
.xlog.off { background:rgba(255,255,255,.04); border-color:rgba(157,151,165,.3); } .xlog.off i { background:#8F899B; box-shadow:none; }
.xverd { display:flex; align-items:center; gap:14px; flex-wrap:wrap; padding:14px 16px; border-radius:16px; margin:4px 0 12px;
  border:1px solid rgba(157,151,165,.22); background:rgba(255,255,255,.03); }
.xverd.truthful { border-color:rgba(74,222,128,.45); background:linear-gradient(120deg, rgba(74,222,128,.10), transparent 70%); }
.xverd.reversed { border-color:rgba(245,185,74,.45); background:linear-gradient(120deg, rgba(245,185,74,.10), transparent 70%); }
.xverd.collecting { border-color:rgba(121,184,244,.4); background:linear-gradient(120deg, rgba(121,184,244,.09), transparent 70%); }
.xverd .q { flex:1 1 300px; min-width:0; color:#B9B3C4; font-size:.86rem; line-height:1.6; }
.xverd .q b { display:block; color:#fff; font-size:1.02rem; margin-bottom:2px; }
.xverd .bar { width:160px; height:8px; border-radius:99px; background:rgba(255,255,255,.08); overflow:hidden; }
.xverd .bar i { display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,#3B8BEB,#7B45F0); }
.xwait { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:10px; margin-top:8px; }
@media (max-width: 760px) { .xwait { grid-template-columns:1fr; } }
.xwait div { padding:12px 14px; border-radius:14px; background:rgba(255,255,255,.03); border:1px solid rgba(157,151,165,.16); font-size:.82rem; color:#B9B3C4; line-height:1.55; }
.xwait div b { display:flex; align-items:center; gap:6px; color:#fff; margin-bottom:4px; }
.xwait div b .ms { color:#A78BFA; }
</style>"""

EV_WORDS = {"earnings": ("Earnings", "أرباح"), "mna": ("Deal", "صفقة"), "guidance": ("Guidance", "توقعات"), "analyst": ("Rating", "تصنيف"),
            "regulation": ("Regulator", "جهة تنظيمية"), "contract": ("Contract", "عقد"), "product": ("Product", "منتج"), "payout": ("Dividend", "توزيعات"),
            "management": ("Management", "إدارة")}


@st.cache_data(ttl=120, show_spinner=False)
def _load():
    return XB.load_all()


# ---------------------------------------------------------------- small pieces
def _when(iso):
    t = pd.Timestamp(iso) if iso else None
    if t is None or pd.isna(t):
        return "—"
    t = t.tz_localize("UTC") if t.tzinfo is None else t
    return T.time_ago(t, is_ar())


def _mood_word(m):
    if m is None:
        return L("No posts yet", "ما فيه تغريدات للحين"), "#8F899B"
    if m >= 25:
        return L("Bullish", "صاعد"), "#4ADE80"
    if m >= 8:
        return L("Leaning bullish", "يميل للصعود"), "#86EFAC"
    if m <= -25:
        return L("Bearish", "هابط"), "#F87171"
    if m <= -8:
        return L("Leaning bearish", "يميل للهبوط"), "#FCA5A5"
    return L("Mixed", "متوازن"), "#C4B5FD"


def _status(state):
    """(css class, words) of a bot's state."""
    s = (state or {}).get("status")
    if s == "ok":
        return "on", L(f"Read X {_when(state.get('read_at'))}", f"قرأ X {_when(state.get('read_at'))}")
    if s == "resting":
        return "on", L("Resting until its market's next day", "يرتاح لين يوم السوق الجاي")
    if s == "cap":
        return "", L("Today's reading ceiling reached", "وصل سقف القراءة لليوم")
    if s == "error":
        return "err", L("X did not answer on the last try", "X ما رد في آخر محاولة")
    return "", L("Waiting for the X connection", "ينتظر ربط X")


def _fol(n):
    """A follower count the way X shows it: 950, 12K, 250K, 1.2M."""
    n = int(n or 0)
    for d, u in ((1e6, "M"), (1e3, "K")):
        if n >= d:
            v = n / d
            return f"{v:.1f}".rstrip("0").rstrip(".") + u if v < 10 else f"{v:,.0f}{u}"
    return f"{n:,}"


def _spark(curve, color, w=110, h=34):
    """The account's curve as a small line (flat and faint before its first trading day)."""
    ys = [float(c["eq"]) for c in (curve or []) if c.get("eq") is not None][-60:]
    if len(ys) < 2:
        return (f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true"><line x1="2" y1="{h / 2:.0f}" x2="{w - 2}" y2="{h / 2:.0f}" vector-effect="non-scaling-stroke" '
                f'stroke="rgba(255,255,255,.18)" stroke-width="2" stroke-dasharray="3 4" stroke-linecap="round"/></svg>')
    lo, hi = min(ys), max(ys)
    if hi - lo < max(1.0, abs(hi) * 1e-5):                  # no move yet: a level line across the middle
        pts = [(2 + i * (w - 4) / (len(ys) - 1), h / 2) for i in range(len(ys))]
    else:
        pts = [(2 + i * (w - 4) / (len(ys) - 1), 3 + (h - 6) * (1 - (y - lo) / (hi - lo))) for i, y in enumerate(ys)]
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    gid = "g" + hashlib.md5((color + d).encode()).hexdigest()[:10]
    return (f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="{gid}" x1="0" x2="0" y1="0" y2="1">'
            f'<stop offset="0" stop-color="{color}" stop-opacity=".35"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
            f'<polygon points="{pts[0][0]:.1f},{h} {d} {pts[-1][0]:.1f},{h}" fill="url(#{gid})"/>'
            f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg>')


def _gauge(m, color, size=58):
    """A half dial of the mood: -100 (left) .. +100 (right)."""
    r = size / 2 - 5
    cx, cy = size / 2, size / 2 + 2
    length = math.pi * r
    pos = 0.5 if m is None else (max(-100.0, min(100.0, m)) + 100) / 200
    ang = math.pi * (1 - pos)
    nx, ny = cx + (r - 1) * math.cos(ang), cy - (r - 1) * math.sin(ang)
    return (f'<svg width="{size}" height="{size / 2 + 8:.0f}" viewBox="0 0 {size} {size / 2 + 8:.0f}" aria-hidden="true">'
            f'<path d="M{cx - r},{cy} A{r},{r} 0 0 1 {cx + r},{cy}" fill="none" stroke="rgba(255,255,255,.09)" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="M{cx - r},{cy} A{r},{r} 0 0 1 {cx + r},{cy}" fill="none" stroke="{color}" stroke-width="6" stroke-linecap="round" '
            f'stroke-dasharray="{length * pos:.1f} {length:.1f}" opacity="{0.35 if m is None else 1}"/>'
            f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="3.2" fill="#fff" stroke="{color}" stroke-width="2"/></svg>')


def _ring(frac, size=34, color="#A78BFA"):
    r = size / 2 - 4
    c = 2 * math.pi * r
    frac = max(0.0, min(1.0, frac))
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" aria-hidden="true" style="transform:rotate(-90deg)">'
            f'<circle cx="{size / 2}" cy="{size / 2}" r="{r}" fill="none" stroke="rgba(255,255,255,.1)" stroke-width="4"/>'
            f'<circle cx="{size / 2}" cy="{size / 2}" r="{r}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" '
            f'stroke-dasharray="{c * frac:.1f} {c:.1f}"/></svg>')


def _last(led):
    """(value, % return) of an account at its last run's prices (the last point of its curve); before any run, its cash."""
    curve = led.get("curve") or []
    eq = float(curve[-1]["eq"]) if curve and curve[-1].get("eq") is not None else XB.equity(led, {s: p["px"] for s, p in led["pos"].items()})
    return eq, (eq / led["start"] - 1) * 100


def _cur(bot):
    return "SAR " if bot["market"] == MK.SA else "$"


def _chips(bot):
    """The bot's numbers as chips: what it holds or its size, slots, stop, target and time."""
    out = []
    if bot["style"] == "pulse":
        out.append(("inventory_2", L("Holds", "يمسك") + " " + " · ".join(T.sym_label(s) for s in bot["trade"])))
    else:
        out.append(("pie_chart", L(f"{bot['size'] * 100:.0f}% per position", f"{bot['size'] * 100:.0f}% لكل مركز")))
        out.append(("grid_view", L(f"up to {bot['slots']}", f"لين {bot['slots']}") + " " + L("positions", "مراكز")))
    if bot["stop"]:
        out.append(("block", L("Stop", "وقف") + f" −{bot['stop']:g}%"))
    if bot["target"]:
        out.append(("flag", L("Target", "هدف") + f" +{bot['target']:g}%"))
    if bot["days"]:
        out.append(("schedule", L(f"{bot['days']} days at most", f"{bot['days']} أيام بالكثير")))
    else:
        out.append(("schedule", L("No time limit", "بدون حد زمني")))
    out.append(("payments", L("0.1% fee each way", "رسوم 0.1% كل اتجاه")))
    return "".join(f"<span>{T.icon(ic)}{T.esc(tx)}</span>" for ic, tx in out)


# ---------------------------------------------------------------- the cards
def _card(bot, state, rank, sel):
    read = (state or {}).get("read") or {}
    led = (state or {}).get("ledger") or XB.new_ledger(bot["market"])
    m = read.get("mood6") if read.get("mood6") is not None else read.get("mood24")
    word, col = _mood_word(m)
    st_ = XB.stats(led, {s: p["px"] for s, p in led["pos"].items()})
    st_["equity"], st_["ret"] = _last(led)
    cls, words = _status(state)
    slots = "".join(f'<i class="{"on" if i < st_["open"] else ""}"></i>' for i in range(bot["slots"]))
    rk = (f'<span class="rk {"top" if rank == 1 else ""}" title="{T.esc(L("Rank by return", "الترتيب حسب العائد"))}">#{rank}</span>' if rank else "")
    return (f'<div class="xbc {"sel" if sel else ""}" style="--xc:{bot["color"]}">'
            f'<div class="hd"><span class="ic">{T.icon(bot["icon"])}</span><span class="nm"><b>{T.esc(L(*bot["name"]))}</b>'
            f'<small>{rk}{T.esc(L("Paper account", "حساب وهمي"))}</small></span></div>'
            f'<div class="beat">{T.esc(L(*bot["beat"]))}</div>'
            f'<div class="eq"><span class="v"><small>{T.esc(L("Account", "الحساب"))}</small><span class="n"><em>{_cur(bot).strip()}</em>{st_["equity"]:,.0f}</span>{T.pill(st_["ret"])}</span></div>'
            f'<div class="sp">{_spark(led.get("curve"), bot["color"])}</div>'
            f'<div class="gg">{_gauge(m, col)}<span class="t"><span>{T.esc(L("Mood · 6 h", "المزاج · 6 ساعات"))}</span>'
            f'<b style="color:{col}">{"—" if m is None else f"{m:+.0f}"}</b><span>{T.esc(word)}</span></span></div>'
            f'<div class="slots">{slots}<span>{st_["open"]} / {bot["slots"]} {T.esc(L("positions", "مراكز"))}</span></div>'
            f'<div class="stt {cls}"><i></i>{T.esc(words)}</div></div>')


def _post(p):
    lab = p.get("lab") or "neutral"
    words = {"bull": L("Bullish", "صاعد"), "bear": L("Bearish", "هابط"), "neutral": L("Neutral", "محايد")}[lab]
    tick = "".join(f'<span class="mchip">{T.esc(T.sym_label(t))}</span>' for t in (p.get("tickers") or []))
    ev = EV_WORDS.get(p.get("event"))
    evh = f'<span class="ev">{T.esc(L(*ev))}</span>' if ev else ""
    link = f"https://x.com/{p.get('user') or 'i'}/status/{p.get('id')}"
    return (f'<div class="xpost {lab}"><div class="who"><b dir="auto">{T.esc(p.get("name") or p.get("user") or "")}</b>'
            f'<bdi>@{T.esc(p.get("user") or "")}</bdi><span>· {T.esc(_when(p.get("t")))}</span>'
            f'<span>· {_fol(p.get("followers"))} {T.esc(L("followers", "متابع"))}</span></div>'
            f'<div class="tx" dir="auto">{T.esc(p.get("text") or "")}</div>'
            f'<div class="ft"><span class="tag {lab}">{T.esc(words)} {p.get("s", 0):+.2f}</span>{evh}{tick}'
            f'<span>♥ {int(p.get("likes") or 0):,} · ↻ {int(p.get("reposts") or 0):,}</span>'
            f'<a class="go" href="{T.esc(link)}" target="_blank" rel="noopener">{T.esc(L("Open on X", "افتح في X"))} ↗</a></div></div>')


AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
VERDICT = {"truthful": ("Truthful signals", "إشاراته صادقة"), "noise": ("Noise", "ضوضاء"),
           "reversed": ("Reversed: the price goes the other way", "عكسية: السعر يمشي عكس كلامه"),
           "collecting": ("Collecting data", "يجمع البيانات")}


def _verdict(score):
    v = (score or {}).get("verdict") or "collecting"
    words = L(*VERDICT[v])
    if v == "collecting":
        words += f" · {int((score or {}).get('n') or 0)}/{XB.MIN_OBS}"
    return f'<span class="xvd {v}"><i></i>{T.esc(words)}</span>'


def _log_mark(state):
    """The mark that the bot's log is being kept: since when, how many hours and trading days."""
    lm = (state or {}).get("log_meta")
    if not lm or not lm.get("since"):
        return (f'<span class="xlog off"><i></i>{T.esc(L("Its log starts with its first run", "سجله يبدأ مع أول تشغيل"))}</span>')
    t_ = pd.Timestamp(lm["since"])
    t_ = (t_.tz_localize("UTC") if t_.tzinfo is None else t_).tz_convert(MK.tz((state or {}).get("market")))
    since = f"{t_.day} {AR_MONTHS[t_.month - 1]}" if is_ar() else t_.strftime("%d %b")
    days = int(lm.get("days") or 0)
    words = L(f"Log kept since {since} · {days} trading days", f"السجل محفوظ منذ {since} · {days} يوم تداول")
    return f'<span class="xlog"><i></i>{T.esc(words)}</span>'


def _csvs(bot, log, led):
    """The bot's log as three files to keep: its daily signals with the moves that followed, its hourly mood, its trades."""
    ar = is_ar()
    sig = pd.DataFrame([{L("Day", "اليوم"): x["d"], L("Time (UTC)", "الوقت (UTC)"): x["t"][11:16], L("Company", "الشركة"): T.sym_label(x["sym"], ar),
                         L("Symbol", "الرمز"): x["sym"], L("Tone", "النبرة"): x["s"], L("Posts (24 h)", "تغريدات (24 ساعة)"): x["n"],
                         L("Price then", "السعر وقتها"): x["px"], L("Next day %", "اليوم التالي %"): x.get("r1"),
                         L("After 3 days %", "بعد 3 أيام %"): x.get("r3")} for x in log.get("sig") or []])
    hrs = pd.DataFrame([{L("Time (UTC)", "الوقت (UTC)"): h["t"][:16].replace("T", " "), L("Mood (6 h)", "المزاج (6 ساعات)"): h.get("m"),
                         L("Posts (6 h)", "تغريدات (6 ساعات)"): h.get("n"), L("Price", "السعر"): h.get("px")} for h in log.get("hourly") or []])
    trd = pd.DataFrame([{L("Time (UTC)", "الوقت (UTC)"): t["t"][:16].replace("T", " "), L("Company", "الشركة"): T.sym_label(t["sym"], ar),
                         L("Symbol", "الرمز"): t["sym"], L("Side", "الجهة"): L("Buy", "شراء") if t["side"] == "buy" else L("Sell", "بيع"),
                         L("Shares", "الأسهم"): t.get("qty"), L("Price", "السعر"): t.get("px"), L("Result %", "النتيجة %"): t.get("pnl"),
                         L("Why", "السبب"): L(*XB.WHY.get(t.get("why"), ("", "")))} for t in led.get("trades") or []])
    return [(d.to_csv(index=False).encode("utf-8-sig"), f"xbot_{bot['id']}_{n}.csv", lab, ic) for d, n, lab, ic in (
        (sig, "signals", L("Signals and what followed", "الإشارات وش صار بعدها"), ":material/insights:"),
        (hrs, "hourly_mood", L("Mood hour by hour", "المزاج ساعة بساعة"), ":material/schedule:"),
        (trd, "trades", L("Trades", "الصفقات"), ":material/receipt_long:"))]


@st.cache_data(ttl=120, show_spinner=False)
def _load_log(bot_id):
    return XB.load_log(bot_id)


def _pct(v, dec=2):
    return "—" if v is None else f"{v:+.{dec}f}%"


def _score_view(bot, state):
    """Does the mood come before the price, is the bot's reading truthful or noise, and how its account does: the verdict, its
    numbers, the next day's move after bearish / neutral / bullish readings, the account's metrics, and its log to download."""
    sc = state.get("score") or XB.scorecard(bot, [])
    pf = state.get("perf") or XB.perf(state["ledger"], state.get("reads"))
    v = sc.get("verdict") or "collecting"
    mood_bot = bot["style"] == "pulse"
    what = (L("the market's mood", "مزاج السوق") if mood_bot else L("its tone about a company", "نبرته عن الشركة"))
    if v == "collecting":
        msg = L(f"It needs {XB.MIN_OBS} bullish or bearish readings with a known next day before it can be judged; it has {sc.get('n', 0)}. "
                "Each trading day adds one reading per company it talks about (one a day for a market-mood bot).",
                f"يحتاج {XB.MIN_OBS} قراءة صاعدة أو هابطة عرفنا وش صار بعدها في اليوم التالي عشان ينحكم عليه، وعنده {sc.get('n', 0)}. "
                "كل يوم تداول يضيف قراءة لكل شركة يتكلم عنها (ولبوت مزاج السوق قراءة وحدة باليوم).")
        bar = f'<span class="bar"><i style="width:{min(100, sc.get("n", 0) / XB.MIN_OBS * 100):.0f}%"></i></span>'
    else:
        msg = {"truthful": L(f"When {what} was bullish the price rose the next day {sc['hit']:.0f}% of the time (counting bearish calls the other way): "
                             "its reading came before the price.",
                             f"لما كانت {what} صاعدة ارتفع السعر في اليوم التالي {sc['hit']:.0f}% من المرات (والهابطة بالعكس): قراءته تسبق السعر."),
               "noise": L(f"Its calls were right {sc['hit']:.0f}% of the time, about a coin toss: what it reads on X does not tell where the price goes.",
                          f"إشاراته صحّت {sc['hit']:.0f}% من المرات، قريب من رمي العملة: اللي يقرأه في X ما يدل وين يروح السعر."),
               "reversed": L(f"Its calls were right only {sc['hit']:.0f}% of the time: the price tends to go against what X says on its beat.",
                             f"إشاراته صحّت {sc['hit']:.0f}% بس: السعر يميل يمشي عكس كلام X في مجاله.")}[v]
        bar = ""
    ui.html(f'<div class="xverd {v}">{_verdict(sc)}<span class="q"><b>{T.esc(L("Does the mood come before the price?", "هل المزاج يسبق السعر؟"))}</b>'
            f'{T.esc(msg)}</span>{bar}</div>')
    k = st.columns(4)
    k[0].markdown(T.kpi("ads_click", L("Direction right", "دقة الاتجاه"), "—" if sc.get("hit") is None else f"{sc['hit']:.0f}%",
                        L("bullish then up, bearish then down", "صاعد ثم ارتفاع، هابط ثم نزول")), unsafe_allow_html=True)
    k[1].markdown(T.kpi("compare_arrows", L("Edge (next day)", "الفرق (اليوم التالي)"), _pct(sc.get("edge")),
                        L("after bullish minus after bearish", "بعد الصاعدة ناقص بعد الهابطة"),
                        "pos" if (sc.get("edge") or 0) > 0 else "neg" if (sc.get("edge") or 0) < 0 else None), unsafe_allow_html=True)
    k[2].markdown(T.kpi("scatter_plot", L("Correlation", "الارتباط"), "—" if sc.get("ic") is None else f"{sc['ic']:+.2f}",
                        L("tone vs next day's move (−1..+1)", "النبرة مقابل حركة اليوم التالي (−1..+1)")), unsafe_allow_html=True)
    k[3].markdown(T.kpi("dataset", L("Readings judged", "قراءات محسوبة"), f"{sc.get('n', 0)}",
                        L(f"{sc.get('obs', 0)} with a known next day", f"{sc.get('obs', 0)} عرفنا يومها التالي")), unsafe_allow_html=True)
    bk = sc.get("buckets") or {}
    if any((bk.get(x) or [None, 0])[1] for x in ("bear", "neutral", "bull")):
        ui.chart(charts.signal_bars([L("After bearish", "بعد الهابطة"), L("After neutral", "بعد المحايدة"), L("After bullish", "بعد الصاعدة")],
                                    [(bk.get(x) or [None])[0] for x in ("bear", "neutral", "bull")],
                                    [(bk.get(x) or [None, 0])[1] for x in ("bear", "neutral", "bull")],
                                    L("The next day's average move after its readings", "متوسط حركة السعر في اليوم التالي بعد قراءاته"), 300,
                                    (L("readings", "قراءة"), "%")), key=f"xb_sig_{bot['id']}")
    else:
        _empty("insights", "The chart of what followed its readings appears after its first trading days.",
               "رسم وش صار بعد قراءاته يطلع بعد أول أيام تداول.")
    ui.sec("monitoring", "The account's metrics", "مؤشرات الحساب")
    bn = L("the S&P 500", "S&P 500") if bot["market"] == MK.US else L("TASI", "تاسي")
    k = st.columns(4)
    k[0].markdown(T.kpi("balance", L(f"Against {bn}", f"مقابل {bn}"), _pct(pf.get("vs")),
                        L(f"{bn}: {_pct(pf.get('bench'))} over the same days", f"{bn}: {_pct(pf.get('bench'))} بنفس الأيام"),
                        "pos" if (pf.get("vs") or 0) > 0 else "neg" if (pf.get("vs") or 0) < 0 else None), unsafe_allow_html=True)
    k[1].markdown(T.kpi("trending_down", L("Deepest fall", "أقصى تراجع"), _pct(pf.get("mdd")),
                        L("from the account's high", "من أعلى قيمة للحساب")), unsafe_allow_html=True)
    pf_txt = "—" if pf.get("pf") is None else f"{pf['pf']:.2f}"
    if pf.get("pf") is None and pf.get("wins"):
        pf_txt = L("no loss yet", "بدون خسارة")
    k[2].markdown(T.kpi("scale", L("Profit factor", "معامل الربح"), pf_txt,
                        L(f"avg win {_pct(pf.get('avg_win'))} · loss {_pct(pf.get('avg_loss'))}",
                          f"متوسط الربح {_pct(pf.get('avg_win'))} · الخسارة {_pct(pf.get('avg_loss'))}")), unsafe_allow_html=True)
    hold = "—" if pf.get("hold") is None else L(f"{pf['hold']:.1f} days", f"{pf['hold']:.1f} يوم")
    k[3].markdown(T.kpi("payments", L("Reading cost", "تكلفة القراءة"), f"${pf.get('cost', 0):,.2f}",
                        L(f"avg trade held {hold}", f"متوسط مدة الصفقة {hold}")), unsafe_allow_html=True)
    st.caption(L(f"How it is judged: every trading day its last reading of each company it talks about (of the market, for a market-mood bot) and the "
                 f"price at that moment are kept, then set against the next day's close. Truthful: right 55% of the time or more with a positive "
                 f"edge, over {XB.MIN_OBS} readings at least. Profit factor: the gains of the winning trades over the losses of the losing ones (above 1 = it makes money).",
                 f"طريقة الحكم: كل يوم تداول تنحفظ آخر قراءة للبوت عن كل شركة يتكلم عنها (وعن السوق لبوت المزاج) والسعر وقتها، وتنقارن بإغلاق "
                 f"اليوم اللي بعده. صادقة: تصيب 55% أو أكثر مع فرق موجب، على {XB.MIN_OBS} قراءة على الأقل. معامل الربح: أرباح الصفقات الرابحة على "
                 f"خسائر الخاسرة (فوق 1 يعني يكسب)."))
    ui.sec("save", "Save the bot's log", "حفظ سجل البوت")
    ui.html(_log_mark(state))
    log = _load_log(bot["id"])
    files = _csvs(bot, log, state["ledger"])
    c = st.columns(3)
    for col, (blob, name, lab, ic) in zip(c, files):
        col.download_button(lab, blob, file_name=name, mime="text/csv", icon=ic, key=f"xb_dl_{bot['id']}_{name}", use_container_width=True)
    st.caption(L("The log is kept by itself every hour (its signals for 120 days, its hourly mood for 45 days); each file opens in Excel.",
                 "السجل ينحفظ لحاله كل ساعة (الإشارات 120 يوم، والمزاج بالساعة 45 يوم)، وكل ملف ينفتح في Excel."))


def _empty(ic, en, ar):
    ui.html(f'<div class="xbempty">{T.icon(ic)}<span>{T.esc(L(en, ar))}</span></div>')


# ---------------------------------------------------------------- one bot in full
def _bot_view(bot, state):
    state = state or XB.new_bot_state(bot)
    read = state.get("read") or XB.reading([])
    led = state["ledger"]
    held = list(led["pos"])
    talked = read.get("talked") or []
    syms = list(dict.fromkeys(held + [d["sym"] for d in talked[:15]]))
    chg = data.quick_changes(syms) if syms else {}
    now_px = {s: (chg.get(s) or (None, None))[0] or led["pos"].get(s, {}).get("px") for s in syms}
    stt = XB.stats(led, {s: v for s, v in now_px.items() if v})
    cur = _cur(bot)
    ui.html(f'<div class="xbd" style="--xc:{bot["color"]}"><span class="ic">{T.icon(bot["icon"])}</span>'
            f'<span class="tx"><b>{T.esc(L(*bot["name"]))}</b><p>{T.esc(L(*bot["beat"]))}</p>{_log_mark(state)}</span><span class="chips">{_chips(bot)}</span></div>')
    k = st.columns(4)
    k[0].markdown(T.kpi("account_balance_wallet", L("Account value", "قيمة الحساب"), f"{cur}{stt['equity']:,.0f}",
                        L(f"started with {cur}{led['start']:,.0f}", f"بدأ بـ {cur}{led['start']:,.0f}")), unsafe_allow_html=True)
    k[1].markdown(T.kpi("trending_up", L("Return", "العائد"), T.pill(stt["ret"]),
                        L(f"since {_when(led.get('since'))}" if led.get("since") else "no trade yet",
                          f"من {_when(led.get('since'))}" if led.get("since") else "ما تداول للحين"),
                        "pos" if stt["ret"] > 0 else "neg" if stt["ret"] < 0 else None), unsafe_allow_html=True)
    wr = "—" if stt["win_rate"] is None else f"{stt['win_rate']:.0f}%"
    avg = "" if stt["avg"] is None else L(f" · avg {stt['avg']:+.1f}%", f" · المتوسط {stt['avg']:+.1f}%")
    k[2].markdown(T.kpi("rule", L("Closed trades", "صفقات مقفلة"), f"{stt['closed']}", L(f"won {wr}", f"الرابحة {wr}") + T.esc(avg)), unsafe_allow_html=True)
    word, col = _mood_word(read.get("mood6"))
    m6 = read.get("mood6")
    k[3].markdown(T.kpi("forum", L("Mood · 6 h", "المزاج · 6 ساعات"), f'<span style="color:{col}">{"—" if m6 is None else f"{m6:+.0f}"}</span>',
                        T.esc(word) + L(f" · {read.get('n24', 0):,} posts in 24 h", f" · {read.get('n24', 0):,} تغريدة في 24 ساعة")), unsafe_allow_html=True)
    a, b = st.columns(2)
    hours = read.get("hours") or []
    with a:
        if any(h.get("n") for h in hours):
            ui.chart(charts.mood_bars([h["t"] for h in hours], [h["mood"] for h in hours],
                                      L("Mood hour by hour · 48 h", "المزاج ساعة بساعة · 48 ساعة"), 300,
                                      (L("Mood", "المزاج"), L("Posts", "تغريدات"))), key=f"xb_mood_{bot['id']}")
        else:
            _empty("bar_chart", "The mood chart appears after the first reads.", "رسم المزاج يطلع بعد أول قراءة.")
    with b:
        curve = led.get("curve") or []
        if len(curve) >= 2:
            s_ = pd.Series([c["eq"] for c in curve], index=pd.to_datetime([c["d"] for c in curve]))
            ui.chart(charts.equity_trades(s_, led.get("trades") or [], L("Paper account · buys and sells", "الحساب الوهمي · الشراء والبيع"), 300,
                                          bot["color"], cur), key=f"xb_eq_{bot['id']}")
        else:
            _empty("show_chart", "The account's curve starts with its first trading day.", "منحنى الحساب يبدأ من أول يوم تداول.")
    t1, t2, t4, t3 = st.tabs([f":material/forum: {L('The reading', 'القراءة')}", f":material/work: {L('The account', 'الحساب')}",
                              f":material/verified: {L('Is it truthful?', 'هل هو صادق؟')}", f":material/gavel: {L('The rules', 'القواعد')}"])
    with t4:
        _score_view(bot, state)
    with t1:
        ui.sec("trending_up", "What X talks about", "وش يتكلم عنه X")
        if talked:
            rows = [{"Symbol": d["sym"], L("Posts · 24 h", "تغريدات · 24 ساعة"): d["n24"], L("Last 6 h", "آخر 6 ساعات"): d["n6"],
                     L("Authors", "كتّاب"): d.get("authors", 0), L("Pace", "الوتيرة"): d["spike"], L("Tone", "النبرة"): d["s"],
                     L("Today %", "اليوم %"): (chg.get(d["sym"]) or (None, None))[1]} for d in talked[:12]]
            ui.table(pd.DataFrame(rows), sym="Symbol", pills={L("Today %", "اليوم %")}, signed={L("Tone", "النبرة")},
                     fmt={L("Pace", "الوتيرة"): "{:.1f}×", L("Tone", "النبرة"): "{:+.2f}", L("Today %", "اليوم %"): "{:+.2f}%"})
            st.caption(L("Pace: the last 6 hours against the bot's 3-day average for that company (2× = twice the usual talk).",
                         "الوتيرة: آخر 6 ساعات مقابل معدل 3 أيام لنفس الشركة (2× يعني ضعف الكلام المعتاد)."))
        else:
            _empty("search_off", "No company in its posts yet.", "ما فيه شركات في تغريداته للحين.")
        ui.sec("chat", "Its strongest posts · 24 h", "أقوى تغريداته · 24 ساعة")
        top = read.get("top") or []
        if top:
            counts = {k: sum(1 for p in top if (p.get("lab") or "neutral") == k) for k in ("bull", "bear", "neutral")}
            names = {"all": L(f"All · {len(top)}", f"الكل · {len(top)}"), "bull": L(f"Bullish · {counts['bull']}", f"صاعد · {counts['bull']}"),
                     "bear": L(f"Bearish · {counts['bear']}", f"هابط · {counts['bear']}"), "neutral": L(f"Neutral · {counts['neutral']}", f"محايد · {counts['neutral']}")}
            pick = st.pills(L("Tone", "النبرة"), list(names), default="all", key=f"xb_tone_{bot['id']}", format_func=names.get,
                            label_visibility="collapsed") or "all"
            shown = [p for p in top if pick == "all" or (p.get("lab") or "neutral") == pick][:10]
            ui.html("".join(_post(p) for p in shown) if shown else "")
            if not shown:
                _empty("chat_bubble", "No post in this tone in the last 24 hours.", "ما فيه تغريدة بهالنبرة في آخر 24 ساعة.")
        else:
            _empty("chat_bubble", "No posts read yet.", "ما قرأ تغريدات للحين.")
    with t2:
        ui.sec("work", "Open positions", "المراكز المفتوحة")
        if led["pos"]:
            rows = []
            for s, p in led["pos"].items():
                px = now_px.get(s) or p["px"]
                rows.append({"Symbol": s, L("Shares", "الأسهم"): p["qty"], L("Entry", "الدخول"): p["px"], L("Now", "الآن"): px,
                             L("Value", "القيمة"): p["qty"] * px, L("Return %", "العائد %"): (px / p["px"] - 1) * 100,
                             L("Since", "منذ"): _when(p.get("t")), L("Why", "السبب"): L(*XB.WHY.get(p.get("why"), ("", "")))})
            ui.table(pd.DataFrame(rows), sym="Symbol", pills={L("Return %", "العائد %")}, wrap={L("Why", "السبب")},
                     fmt={L("Entry", "الدخول"): "{:,.2f}", L("Now", "الآن"): "{:,.2f}", L("Value", "القيمة"): "{:,.0f}", L("Return %", "العائد %"): "{:+.2f}%"})
            st.caption(L(f"Cash: {cur}{led['cash']:,.0f}", f"الكاش: {cur}{led['cash']:,.0f}"))
        else:
            _empty("hourglass_empty", "No open position: the bot waits for its signal.", "ما فيه مراكز: البوت ينتظر إشارته.")
        ui.sec("receipt_long", "Latest trades", "آخر الصفقات")
        if led["trades"]:
            rows = []
            for t in reversed(led["trades"][-20:]):
                rows.append({L("When", "متى"): _when(t["t"]), "Symbol": t["sym"],
                             L("Side", "الجهة"): L("Buy", "شراء") if t["side"] == "buy" else L("Sell", "بيع"), L("Shares", "الأسهم"): t.get("qty"),
                             L("Price", "السعر"): t["px"], L("Result %", "النتيجة %"): t.get("pnl"),
                             L("Why", "السبب"): L(*XB.WHY.get(t.get("why"), ("", "")))})
            ui.table(pd.DataFrame(rows), sym="Symbol", pills={L("Result %", "النتيجة %")}, wrap={L("Why", "السبب")},
                     words={L("Side", "الجهة"): (L("Buy", "شراء"), L("Sell", "بيع"))},
                     fmt={L("Price", "السعر"): "{:,.2f}", L("Result %", "النتيجة %"): lambda v: "—" if v is None or pd.isna(v) else f"{v:+.2f}%"})
        else:
            _empty("receipt_long", "No trade yet.", "ما فيه صفقات للحين.")
    with t3:
        ui.html(f'<div class="xrules"><b>{T.esc(L("Its rules", "قواعده"))}:</b> {T.esc(L(*bot["rules"]))}<br>'
                f'<b>{T.esc(L("Always", "دائماً"))}:</b> {T.esc(L("long only, no leverage, trades at the latest price while its market is open, never buys back a company it sold the same day.", "شراء فقط بدون رافعة، يتداول بآخر سعر والسوق مفتوح، وما يرجع يشتري شركة باعها بنفس اليوم."))}</div>')
        st.caption(L("What it searches on X (the search X runs every hour):", "وش يبحث عنه في X (البحث اللي يشغله X كل ساعة):"))
        st.code(bot["query"], language=None)
        st.caption(L(f"Read {int(state.get('reads') or 0):,} posts in all · keeps the last {XB.KEEP_HOURS // 24} days of posts.",
                     f"قرأ {int(state.get('reads') or 0):,} تغريدة بالمجمل · يحتفظ بتغريدات آخر {XB.KEEP_HOURS // 24} أيام."))


# ---------------------------------------------------------------- the page
def _hero(cur, bots, states, meta):
    ar = is_ar()
    mine = {b["id"]: states.get(b["id"]) for b in bots}
    read_at = max((s.get("read_at") or "" for s in mine.values() if s), default="")
    errs = [s for s in mine.values() if s and s.get("status") == "error"]
    reads, cap = int(meta.get("reads") or 0), XB.daily_reads()
    mk_txt, mk_cls, mk_time = MK.status(cur, ar)
    mname = L("Saudi market", "السوق السعودي") if cur == MK.SA else L("US market", "السوق الأمريكي")
    mk = f'<span class="mk {mk_cls}"><i></i>{T.esc(mname)} · {T.esc(mk_txt)} · {T.esc(mk_time)}</span>'
    if read_at:
        cls, head = ("err", L("X did not answer on the last try", "X ما رد في آخر محاولة")) if errs and len(errs) == len([s for s in mine.values() if s]) else \
                    ("on", L("Reading X every hour of the market's day", "تقرأ X كل ساعة من يوم السوق"))
        sub = L(f"Last read {_when(read_at)} · the five bots of this market", f"آخر قراءة {_when(read_at)} · بوتات هالسوق الخمسة")
        facts = (f'<span class="f">{_ring(reads / cap)}<span><b>{reads:,} / {cap:,}</b>{T.esc(L("posts read today (all ten bots)", "تغريدة مقروءة اليوم (البوتات العشرة)"))}</span></span>'
                 f'<span class="f"><span><b>${reads * COST:,.2f}</b>{T.esc(L("reading cost today", "تكلفة القراءة اليوم"))}</span></span>{mk}')
    else:
        stat = {(s or {}).get("status") for s in mine.values()} | {(s or {}).get("error") for s in mine.values()}
        if "auth" in stat:
            cls, head = "err", L("X refused the key", "X رفض المفتاح")
            sub = L("The X key in the site's secrets is wrong or was replaced: it needs the current Bearer Token.",
                    "مفتاح X في أسرار الموقع غلط أو تغيّر: يحتاج الـ Bearer Token الحالي.")
        elif "credits" in stat:
            cls, head = "err", L("No credit left on X", "خلص الرصيد في X")
            sub = L("The bots read again once the X developer account has credit.", "البوتات ترجع تقرأ أول ما ينشحن رصيد حساب مطوري X.")
        elif stat & {"resting", "cap", "error"}:
            cls, head = "on", L("Connected to X: the first read is in the market's next hour", "متصلة بـ X: أول قراءة في أول ساعة من يوم السوق الجاي")
            sub = L("The bots read every hour of the market's day (from an hour before the open to an hour after the close).",
                    "البوتات تقرأ كل ساعة من يوم السوق (من ساعة قبل الافتتاح لين ساعة بعد الإغلاق).")
        else:
            cls, head = "", L("Ready: waiting for the X connection", "جاهزة: تنتظر ربط X")
            sub = L("Nothing is read or traded until the site is connected to X.", "ما تقرأ ولا تتداول شي لين يتربط الموقع بـ X.")
        facts = mk
    ui.html(f'<div class="xbhero"><div class="st {cls}"><i></i><span>{T.esc(head)}<small>{T.esc(sub)}</small></span></div><div class="facts">{facts}</div></div>')
    if not read_at and cls == "":
        ui.html('<div class="xwait">'
                f'<div><b>{T.icon("key")}{T.esc(L("1 · The key", "1 · المفتاح"))}</b>{T.esc(L("The site owner adds the X API key to the secrets of the site; the key is never shown here.", "صاحب الموقع يضيف مفتاح X API في أسرار الموقع، والمفتاح ما يظهر هنا أبداً."))}</div>'
                f'<div><b>{T.icon("schedule")}{T.esc(L("2 · Every hour", "2 · كل ساعة"))}</b>{T.esc(L("From then on each bot reads the new posts of its beat every hour of the day of its market, within a daily ceiling.", "بعدها كل بوت يقرأ تغريدات مجاله الجديدة كل ساعة من يوم سوقه، ضمن سقف يومي."))}</div>'
                f'<div><b>{T.icon("candlestick_chart")}{T.esc(L("3 · On paper", "3 · وهمياً"))}</b>{T.esc(L("It turns what it reads into a mood and signals, and trades a paper account by its written rules.", "يحوّل اللي يقرأه لمزاج وإشارات، ويتداول حساب وهمي حسب قواعده المكتوبة."))}</div></div>')


def _compare(bots, states):
    """Which bot's signals are truthful and which are noise: the five side by side."""
    ui.sec("verified", "Which bot is truthful, which is noise?", "أي بوت إشاراته صادقة وأي واحد ضوضاء؟")
    rows = []
    for b in bots:
        stt = states.get(b["id"]) or {}
        sc = stt.get("score") or XB.scorecard(b, [])
        pf = stt.get("perf") or XB.perf(stt.get("ledger") or XB.new_ledger(b["market"]), stt.get("reads"))
        rows.append({L("Bot", "البوت"): L(*b["name"]), L("Verdict", "الحكم"): sc.get("verdict") or "collecting",
                     L("Direction right", "دقة الاتجاه"): sc.get("hit"), L("Edge", "الفرق"): sc.get("edge"), L("Readings", "قراءات"): sc.get("n", 0),
                     L("Return %", "العائد %"): pf.get("ret"), L("Vs market", "مقابل السوق"): pf.get("vs"), L("Deepest fall", "أقصى تراجع"): pf.get("mdd"),
                     L("Cost", "التكلفة"): pf.get("cost", 0.0), "_score": sc})
    df = pd.DataFrame(rows)
    vcol = L("Verdict", "الحكم")
    ui.table(df.drop(columns=["_score"]), pills={L("Return %", "العائد %"), L("Vs market", "مقابل السوق")}, signed={L("Edge", "الفرق")},
             cell={vcol: lambda v, r: _verdict({"verdict": v, "n": r[L("Readings", "قراءات")]})},
             fmt={L("Direction right", "دقة الاتجاه"): lambda v: "—" if v is None or pd.isna(v) else f"{v:.0f}%",
                  L("Edge", "الفرق"): lambda v: _pct(None if v is None or pd.isna(v) else v),
                  L("Return %", "العائد %"): "{:+.2f}%", L("Vs market", "مقابل السوق"): lambda v: _pct(None if v is None or pd.isna(v) else v),
                  L("Deepest fall", "أقصى تراجع"): "{:+.2f}%", L("Cost", "التكلفة"): "${:,.2f}"})
    st.caption(L("Truthful: its bullish readings were followed by rises and its bearish ones by falls (55% of the time or more, over "
                 f"{XB.MIN_OBS} readings at least). Noise: about a coin toss. Reversed: the price tends to go the other way. Each bot is judged "
                 "on its own log; open its tab \"Is it truthful?\" for the detail.",
                 f"صادقة: قراءاته الصاعدة تبعها ارتفاع والهابطة نزول (55% من المرات أو أكثر، على {XB.MIN_OBS} قراءة على الأقل). ضوضاء: قريب من "
                 "رمي العملة. عكسية: السعر يميل يمشي بالعكس. كل بوت ينحكم على سجله، وتفاصيله في تبويب \"هل هو صادق؟\"."))


def page_xbots():
    ui.html(CSS)
    cur = MK.current()
    sa = cur == MK.SA
    ui.header("alternate_email", "X Bots · Saudi market" if sa else "X Bots · US market", "بوتات X · السوق السعودي" if sa else "بوتات X · السوق الأمريكي",
              ("Five bots that read X (Twitter) about the Saudi market every hour of its day: TASI's mood, the companies on everyone's lips, "
               "the technical crowd, the market's news wire and the talk about oil. Each turns what it reads into signals and trades them on paper.")
              if sa else
              ("Five bots that read X (Twitter) about the US market every hour of its day: the mood, the stocks suddenly talked about, the "
               "market pros, breaking news and the crowd's fear about the mega-caps. Each turns what it reads into signals and trades them on paper."),
              ("خمس بوتات تقرأ X (تويتر) عن السوق السعودي كل ساعة من يومه: مزاج تاسي، والشركات اللي على كل لسان، وأهل التحليل الفني، "
               "وأخبار السوق، والكلام عن النفط. كل بوت يحوّل اللي يقرأه لإشارات ويتداولها وهمياً.")
              if sa else
              ("خمس بوتات تقرأ X (تويتر) عن السوق الأمريكي كل ساعة من يومه: المزاج، والأسهم اللي فجأة صار عنها كلام، والمحللين، والعاجل، "
               "وخوف الناس من الشركات العملاقة. كل بوت يحوّل اللي يقرأه لإشارات ويتداولها وهمياً."))
    try:
        states, meta = _load()
    except Exception:
        states, meta = {}, {}
    bots = XB.bots_of(cur)
    _hero(cur, bots, states, meta)

    rets = {b["id"]: _last((states.get(b["id"]) or {}).get("ledger") or XB.new_ledger(cur))[1] for b in bots}
    # a rank only once the accounts differ (before the first trade they are all level: no "#1")
    rank = ({b["id"]: i + 1 for i, b in enumerate(sorted(bots, key=lambda b: -rets[b["id"]]))}
            if max(rets.values()) - min(rets.values()) > 0.005 else {b["id"]: 0 for b in bots})
    key = f"xb_pick_{cur}"
    ids = {b["id"] for b in bots}
    # the chosen bot: the picker's value, or (when its chosen entry is pressed again and cleared) the last one chosen
    if ss.get(key) in ids:
        ss[key + "_last"] = ss[key]
    pick = ss.get(key) if ss.get(key) in ids else ss.get(key + "_last") if ss.get(key + "_last") in ids else bots[0]["id"]
    ui.html('<div class="xbg">' + "".join(_card(b, states.get(b["id"]), rank[b["id"]], b["id"] == pick) for b in bots) + "</div>")
    # the race of the five accounts (once at least one has two days)
    race = {}
    for b in bots:
        curve = (states.get(b["id"]) or {}).get("ledger", {}).get("curve") or []
        if len(curve) >= 2:
            s_ = pd.Series([c["eq"] for c in curve], index=pd.to_datetime([c["d"] for c in curve]))
            race[b["id"]] = (s_ / XB.START_CASH - 1) * 100
    if race:
        ui.chart(charts.equity_race(race, L("The five accounts since their start", "الحسابات الخمسة من بدايتها"), 300,
                                    colors={b["id"]: b["color"] for b in bots}, names={b["id"]: L(*b["name"]) for b in bots}), key=f"xb_race_{cur}")
    _compare(bots, states)
    names = {b["id"]: f":material/{b['icon']}: {L(*b['name'])}" for b in bots}
    chosen = st.segmented_control(L("Bot", "البوت"), list(names), default=pick, key=key, format_func=names.get, label_visibility="collapsed")
    bot = XB.BY_ID.get(chosen if chosen in ids else pick, bots[0])
    ui.safe(_bot_view, bot, states.get(bot["id"]))
    st.caption(L("The posts are shown as written on X, with a link to each. The bots' trades are on paper at the latest prices (long only, "
                 "a 0.1% fee each way): an experiment in reading the crowd, not advice.",
                 "التغريدات معروضة مثل ما انكتبت في X مع رابط كل وحدة. صفقات البوتات وهمية بآخر الأسعار (شراء فقط، رسوم 0.1% كل اتجاه): "
                 "تجربة لقراءة كلام الناس، مو توصية."))
    ui.foot()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "23.3.13"
