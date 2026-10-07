"""
fairvalue.py - The fair value of a company: what its business is worth per share, estimated three ways and blended.

  1. Discounted cash flow (DCF): the free cash flow of the last years grows for 5 years at the expected rate (analysts' 5-year
     estimate when Yahoo has it), slows down to the long-run rate over the next 5, and everything after year 10 is a terminal
     value; all of it is discounted at the cost of equity (10-year Treasury yield + beta x 4.5% market premium), then the net
     cash is added. Banks and insurers have no meaningful free cash flow: they get the justified price-to-book instead
     (book value x (ROE - g) / (cost of equity - g)).
  2. Earnings at the company's usual multiple: next year's EPS x the median P/E the stock traded at in its last fiscal years.
  3. Graham's growth formula: EPS x (8.5 + 2 x growth) x 4.4 / corporate bond yield (Benjamin Graham's intrinsic value).
Weights 40 / 35 / 25 % (a method without the data it needs is left out and the others share its weight). A bear and a bull
case (discount rate +/- 1 point, growth x 0.6 / x 1.3, multiple -/+ 15%) give the range. The analysts' mean target is shown
next to it for comparison, not blended in. An estimate from public data, not a price prediction.
"""
import math

import numpy as np
import pandas as pd
import streamlit as st

import data
import theme as T
import ui
from i18n import L, is_ar

ERP = 0.045                 # equity risk premium
LRI, PDI = "\u2066", "\u2069"   # keep "$168.00" in one piece inside Arabic text
W_DCF, W_PE, W_GR = 0.40, 0.35, 0.25
FINANCIAL = ("Financial Services",)


def _f(x):
    try:
        x = float(x)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def _clip(x, lo, hi):
    return max(lo, min(hi, x))


# ---------------------------------------------------------------- inputs
@st.cache_data(ttl=43200, show_spinner=False)
def _growth_est(sym):
    """Analysts' growth estimates from Yahoo: {'+5y': 0.12, '+1y': 0.09} (fractions)."""
    import yfinance as yf
    out = {}
    t = yf.Ticker(sym)
    try:
        ge = t.growth_estimates
        if isinstance(ge, pd.DataFrame) and not ge.empty:
            col = next((c for c in ge.columns if "stock" in str(c).lower()), ge.columns[0])
            for k in ("+5y", "+1y", "0y"):
                if k in ge.index:
                    v = _f(ge.loc[k, col])
                    if v is not None:
                        out[k] = v
    except Exception:
        pass
    if "+1y" not in out:
        try:
            ee = t.earnings_estimate
            if isinstance(ee, pd.DataFrame) and "+1y" in ee.index and "growth" in ee.columns:
                v = _f(ee.loc["+1y", "growth"])
                if v is not None:
                    out["+1y"] = v
        except Exception:
            pass
    return out


def growth_est(sym):
    try:
        return _growth_est(sym)
    except Exception:
        return {}


def risk_free():
    """The 10-year Treasury yield (a fraction); 4.25% when it can't be read."""
    try:
        d = data.history("^TNX", "1mo")
        v = float(d["Close"].dropna().iloc[-1])
        v = v / 10 if v > 20 else v
        return _clip(v / 100, 0.01, 0.10)
    except Exception:
        return 0.0425


def _row(df, *names):
    if not isinstance(df, pd.DataFrame) or df.empty:
        return None
    for n in names:
        if n in df.index:
            s = pd.to_numeric(df.loc[n], errors="coerce")
            s = s[s.notna()]
            if len(s):
                return s.sort_index(ascending=False)
    return None


# ---------------------------------------------------------------- the model
def dcf(fcf0, g1, r, gt, years=10, stage1=5):
    """[(year, growth, fcf, present value)], terminal value, its present value, enterprise value."""
    rows, f = [], fcf0
    for t in range(1, years + 1):
        g = g1 if t <= stage1 else g1 + (gt - g1) * (t - stage1) / (years - stage1)
        f *= 1 + g
        rows.append((t, g, f, f / (1 + r) ** t))
    tv = f * (1 + gt) / (r - gt)
    pv_tv = tv / (1 + r) ** years
    return rows, tv, pv_tv, sum(x[3] for x in rows) + pv_tv


def _growth(info, stm, ge):
    """(5-year growth, where it comes from)."""
    if ge.get("+5y") is not None:
        return ge["+5y"], "analysts_5y"
    if ge.get("+1y") is not None:
        return ge["+1y"], "analysts_1y"
    te, fe = _f(info.get("trailingEps")), _f(info.get("forwardEps"))
    if te and fe and te > 0 and fe > 0:
        return fe / te - 1, "eps"
    rev = _row(stm.get("inc_a"), "Total Revenue", "Operating Revenue")
    if rev is not None and len(rev) >= 3 and rev.iloc[-1] > 0 and rev.iloc[0] > 0:
        n = min(len(rev) - 1, 3)
        return (rev.iloc[0] / rev.iloc[n]) ** (1 / n) - 1, "revenue"
    g = _f(info.get("revenueGrowth")) or _f(info.get("earningsGrowth"))
    return (g, "revenue") if g is not None else (0.05, "default")


def _fcf_base(info, stm):
    """Free cash flow to start from: the average of the last twelve months and the last two fiscal years (when positive)."""
    ttm = _f(info.get("freeCashflow"))
    ann = _row(stm.get("cf_a"), "Free Cash Flow")
    vals = ([ttm] if ttm else []) + ([float(x) for x in ann.iloc[:2]] if ann is not None else [])
    if not vals:
        return None, []
    pos = [v for v in vals if v > 0]
    if (ttm is not None and ttm <= 0) or len(pos) < max(1, len(vals) - 1):
        return None, vals                    # losing cash, or too unsteady to project
    return float(np.mean(pos)), vals


def _pe_hist(stm, hist):
    """Median P/E at the last fiscal year ends (price on the report date's eve / diluted EPS)."""
    eps = _row(stm.get("inc_a"), "Diluted EPS", "Basic EPS")
    if eps is None or hist is None or hist.empty:
        return None, []
    close = hist["Close"].copy()
    idx = pd.to_datetime(close.index)
    close.index = idx.tz_localize(None) if getattr(idx, "tz", None) is not None else idx
    pes = []
    for d, e in eps.items():
        if e <= 0:
            continue
        p = close[close.index <= pd.Timestamp(d)]
        if len(p):
            pes.append(float(p.iloc[-1]) / float(e))
    if len(pes) < 2:
        return None, pes
    return _clip(float(np.median(pes)), 6.0, 45.0), pes


def compute(sym, info, stm, ge, rf, hist, price):
    """Everything the card shows; {'ok': False, 'why': ...} when there's no honest fair value to give."""
    qt = str(info.get("quoteType") or "EQUITY").upper()
    if qt != "EQUITY":
        return {"ok": False, "why": "not_equity"}
    shares = _f(info.get("sharesOutstanding")) or _f(info.get("impliedSharesOutstanding"))
    if not shares and _f(info.get("marketCap")) and price:
        shares = _f(info.get("marketCap")) / price
    if not shares or not price:
        return {"ok": False, "why": "no_data"}
    fin = info.get("sector") in FINANCIAL
    beta = _clip(_f(info.get("beta")) or 1.0, 0.6, 2.0)
    ke = _clip(rf + beta * ERP, 0.07, 0.14)
    g_raw, g_src = _growth(info, stm, ge)
    g = _clip(g_raw, -0.05, 0.25)
    gt = _clip(min(0.025, rf - 0.005), 0.01, 0.03)
    cash, debt = _f(info.get("totalCash")) or 0.0, _f(info.get("totalDebt")) or 0.0
    eps_f = _f(info.get("forwardEps"))
    eps_t = _f(info.get("trailingEps"))
    eps = eps_f if eps_f and eps_f > 0 else eps_t if eps_t and eps_t > 0 else None
    bvps, roe = _f(info.get("bookValue")), _f(info.get("returnOnEquity"))
    fcf0, fcf_vals = (None, []) if fin else _fcf_base(info, stm)
    pe_med, pes = _pe_hist(stm, hist)
    bond = rf + 0.01                         # a high-grade corporate bond yield

    def values(r, gg, mult):
        out = {}
        if fcf0:
            rows, tv, pv_tv, ev = dcf(fcf0, gg, r, gt)
            out["dcf"] = (ev + cash - debt) / shares
        if fin and bvps and bvps > 0 and roe and roe > 0:
            gs = min(gg, 0.04)
            out["pb"] = bvps * (_clip(roe, 0.0, 0.30) - gs) / (r - gs) if r > gs else None
        if eps and pe_med:
            out["pe"] = eps * pe_med * mult
        if eps:
            out["graham"] = eps * (8.5 + 2 * _clip(gg * 100, 0, 20)) * 4.4 / (bond * 100)
        return {k: v for k, v in out.items() if v is not None and v > 0}

    def blend(vals):
        w = {"dcf": W_DCF, "pb": W_DCF, "pe": W_PE, "graham": W_GR}
        tot = sum(w[k] for k in vals)
        return sum(w[k] * v for k, v in vals.items()) / tot if tot else None

    base = values(ke, g, 1.0)
    if not base:
        return {"ok": False, "why": "no_profit", "target": _f(info.get("targetMeanPrice"))}
    fv = blend(base)
    bear = blend(values(ke + 0.01, g * 0.6 if g > 0 else g - 0.02, 0.85) or base)
    bull = blend(values(max(ke - 0.01, gt + 0.02), min(g * 1.3, 0.30) if g > 0 else g + 0.02, 1.15) or base)
    up = (fv / price - 1) * 100
    vs = sorted(base.values())
    spread = vs[-1] / vs[0] if vs[0] > 0 else 9
    conf = ("high" if len(base) >= 3 and spread <= 1.6 and g_src.startswith("analysts") else
            "medium" if len(base) >= 2 and spread <= 2.5 else "low")
    det = None
    if fcf0:
        rows, tv, pv_tv, ev = dcf(fcf0, g, ke, gt)
        det = {"rows": rows, "tv": tv, "pv_tv": pv_tv, "ev": ev, "equity": ev + cash - debt}
    total_w = sum({"dcf": W_DCF, "pb": W_DCF, "pe": W_PE, "graham": W_GR}[k] for k in base)
    return {"ok": True, "sym": sym, "price": price, "fv": fv, "bear": min(bear, bull), "bull": max(bear, bull), "up": up,
            "methods": base, "weights": {k: {"dcf": W_DCF, "pb": W_DCF, "pe": W_PE, "graham": W_GR}[k] / total_w for k in base},
            "conf": conf, "fin": fin, "beta": beta, "ke": ke, "rf": rf, "g": g, "g_src": g_src, "gt": gt, "fcf0": fcf0, "fcf_vals": fcf_vals,
            "cash": cash, "debt": debt, "shares": shares, "eps": eps, "eps_kind": "fwd" if eps == eps_f else "ttm", "pe_med": pe_med,
            "pes": pes, "bvps": bvps, "roe": roe, "bond": bond, "target": _f(info.get("targetMeanPrice")),
            "n_an": int(_f(info.get("numberOfAnalystOpinions")) or 0), "dcf": det}


@st.cache_data(ttl=21600, show_spinner=False)
def _model(sym):
    """The fair value itself (from the financials, which change once a quarter); today's price is applied by value()."""
    info = data.info(sym) or {}
    price = _f(info.get("currentPrice")) or _f(info.get("regularMarketPrice")) or _f(info.get("previousClose"))
    r = compute(sym, info, data.statements(sym), growth_est(sym), risk_free(), data.history(sym, "5y"), price)
    if not r.get("ok") and r.get("why") == "no_data":
        raise ValueError("no data")          # not kept: asked again on the next view
    return r


def value(sym, price=None):
    try:
        r = dict(_model(sym))
    except Exception:
        return {"ok": False, "why": "error"}
    if r.get("ok") and price:
        r["price"] = float(price)
        r["up"] = (r["fv"] / r["price"] - 1) * 100
    return r


# ---------------------------------------------------------------- the card
VERDICT = [(20, "Undervalued", "أقل من قيمته العادلة", "uv"), (5, "Slightly undervalued", "أقل من قيمته بقليل", "suv"),
           (-5, "Near its fair value", "قريب من قيمته العادلة", "fair"), (-20, "Slightly overvalued", "أعلى من قيمته بقليل", "sov"),
           (-1e9, "Overvalued", "أعلى من قيمته العادلة", "ov")]
METHOD = {"dcf": ("Discounted cash flow", "التدفقات النقدية المخصومة", "waterfall_chart"),
          "pb": ("Justified price-to-book", "مضاعف القيمة الدفترية المبرر", "account_balance"),
          "pe": ("Earnings × its usual P/E", "الأرباح × مكررها المعتاد", "query_stats"),
          "graham": ("Graham's growth formula", "معادلة غراهام للنمو", "school")}
GSRC = {"analysts_5y": ("analysts, 5 years", "المحللون، 5 سنوات"), "analysts_1y": ("analysts, next year", "المحللون، السنة الجاية"),
        "eps": ("next year's EPS", "ربحية السنة الجاية"), "revenue": ("revenue trend", "اتجاه الإيرادات"), "default": ("default", "افتراضي")}
CSS = f"""<style>
.fvc {{ container-type:inline-size; position:relative; overflow:hidden; border-radius:20px; border:1px solid {T.BORDER}; padding:18px 20px 16px; margin:8px 0 12px;
  background:radial-gradient(120% 120% at 100% 0%, rgba(123,69,240,.20), transparent 55%), radial-gradient(80% 120% at 0% 100%, rgba(45,182,235,.10), transparent 60%),
  linear-gradient(180deg,{T.CARD2},{T.CARD}); box-shadow:0 14px 34px rgba(0,0,0,.22), {T.GLOW}; }}
.fvc::before {{ content:""; position:absolute; left:0; right:0; top:0; height:3px; background:var(--fvline); opacity:.95; }}
.fvc .hd {{ display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; }}
.fvc .hd .t {{ display:flex; align-items:center; gap:8px; color:#fff; font-weight:700; font-size:1.12rem; }} .fvc .hd .t .ms {{ color:{T.CYAN}; }}
.fvc .hd .t small {{ color:{T.MUTED}; font-weight:500; font-size:.76rem; }}
.fvv {{ display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:5px 12px; font-weight:700; font-size:.82rem; border:1px solid; }}
.fvv.uv, .fvv.suv {{ color:{T.POS_FG}; background:{T.POS_BG}; border-color:{T.POS_BD}; }} .fvv.fair {{ color:#FCD34D; background:{T.YEL_BG}; border-color:rgba(245,185,74,.45); }}
.fvv.sov, .fvv.ov {{ color:{T.NEG_FG}; background:{T.NEG_BG}; border-color:{T.NEG_BD}; }}
.fvc .top {{ display:grid; grid-template-columns:minmax(0,1.1fr) minmax(0,1.6fr); gap:14px; align-items:stretch; margin-top:14px; }}
@container (max-width: 820px) {{ .fvc .top {{ grid-template-columns:1fr; }} }}
.fvc .big {{ border-radius:16px; padding:14px 16px; background:rgba(14,9,24,.45); border:1px solid rgba(123,69,240,.35); }}
.fvc .big .l {{ color:{T.MUTED}; font-size:.7rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; }}
.fvc .big .v {{ font-size:2.5rem; font-weight:800; line-height:1.05; margin:4px 0 6px; }}
.fvc .big .v span {{ display:inline-block; direction:ltr; unicode-bidi:isolate; background:linear-gradient(95deg,#fff 10%,#C4B5FD 55%,{T.CYAN});
  -webkit-background-clip:text; background-clip:text; color:transparent; }}
.fvc .big .r {{ color:#CFC8DA; font-size:.8rem; }} .fvc .big .r bdi {{ direction:ltr; unicode-bidi:isolate; color:#fff; font-weight:600; }}
.fvc .cells {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }}
.fvc .cell {{ border-radius:14px; padding:12px 14px; background:rgba(14,9,24,.35); border:1px solid rgba(44,39,56,.9); }}
.fvc .cell .l {{ color:{T.MUTED}; font-size:.68rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }}
.fvc .cell .v {{ color:#fff; font-size:1.35rem; font-weight:700; margin-top:5px; }} .fvc .cell .v span {{ display:inline-block; direction:ltr; unicode-bidi:isolate; }}
.fvc .cell .s {{ color:{T.MUTED}; font-size:.72rem; margin-top:3px; }}
.fvc .cell.up .v {{ color:{T.POS_FG}; }} .fvc .cell.dn .v {{ color:{T.NEG_FG}; }}
.fvc .dots {{ display:inline-flex; gap:4px; margin-inline-start:6px; vertical-align:middle; }}
.fvc .dots i {{ width:8px; height:8px; border-radius:50%; background:rgba(157,151,165,.3); }} .fvc .dots i.on {{ background:{T.CYAN}; box-shadow:0 0 8px rgba(45,182,235,.6); }}
.fvc .band {{ margin:14px 0 4px; }} .fvc .band svg {{ width:100%; height:auto; display:block; overflow:visible; }}
.fvc .band.narrow {{ display:none; }}
@container (max-width: 560px) {{ .fvc .band.wide {{ display:none; }} .fvc .band.narrow {{ display:block; }} .fvc .cells {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .fvc .cells .cell:last-child {{ grid-column:1 / -1; }}
  .fvc .big .v {{ font-size:2.1rem; }} }}
@media (max-width: 640px) {{ .fvc {{ padding:16px 14px 14px; }} }}
.fvc .ms3 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:10px; margin-top:10px; }}
.fvm {{ position:relative; border-radius:14px; padding:12px 14px; background:{T.BOX_BG}; border:1px solid {T.BORDER}; transition:transform .18s, border-color .18s; }}
.fvm:hover {{ transform:translateY(-2px); border-color:rgba(121,184,244,.45); }}
.fvm.ref {{ border-style:dashed; background:rgba(26,22,36,.55); }}
.fvm .h {{ display:flex; align-items:center; gap:7px; color:#DCD7E3; font-weight:600; font-size:.84rem; }} .fvm .h .ms {{ color:{T.CYAN}; font-size:1.05rem; }}
.fvm .h .w {{ margin-inline-start:auto; color:{T.MUTED}; font-size:.72rem; font-weight:600; }}
.fvm .v {{ display:flex; align-items:baseline; gap:8px; margin-top:6px; }} .fvm .v b {{ color:#fff; font-size:1.25rem; direction:ltr; unicode-bidi:isolate; }}
.fvm .v em {{ font-style:normal; font-size:.76rem; font-weight:700; border-radius:7px; padding:1px 6px; direction:ltr; unicode-bidi:isolate; }}
.fvm .v em.up {{ color:{T.POS_FG}; background:{T.POS_BG}; }} .fvm .v em.dn {{ color:{T.NEG_FG}; background:{T.NEG_BG}; }}
.fvm .bar {{ position:relative; height:6px; border-radius:6px; background:rgba(157,151,165,.16); margin:9px 0 7px; direction:ltr; }}
.fvm .bar i {{ position:absolute; top:0; bottom:0; border-radius:6px; }} .fvm .bar b {{ position:absolute; top:-3px; width:2px; height:12px; background:#fff; border-radius:2px; }}
.fvm .d {{ color:{T.MUTED}; font-size:.74rem; line-height:1.45; }} .fvm .d bdi {{ direction:ltr; unicode-bidi:isolate; color:#CFC8DA; }}
.fvc .as {{ display:flex; flex-wrap:wrap; gap:7px; margin-top:12px; }}
.fvc .as span {{ background:rgba(26,22,36,.8); border:1px solid {T.BORDER}; border-radius:9px; padding:5px 9px; font-size:.75rem; color:#CCC7D3;
  display:inline-flex; align-items:center; gap:6px; }}
.fvc .as span b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }} .fvc .as .ms {{ color:{T.CYAN}; font-size:.95rem; }}
.fvc .nt {{ color:{T.MUTED}; font-size:.72rem; margin-top:10px; line-height:1.5; }}
.fvempty {{ border:1px dashed rgba(157,151,165,.35); border-radius:16px; padding:16px 18px; color:#BCB6C7; font-size:.86rem; background:rgba(26,22,36,.45); margin:8px 0 10px; }}
.fvempty b {{ color:#fff; }}
</style>"""


def _m(v, dec=2):
    return "—" if v is None else f"${v:,.{dec}f}"


def _big(v):
    if v is None:
        return "—"
    return ("-" if v < 0 else "") + "$" + T.fmt_big(abs(v))


def verdict(up):
    for lim, en, ar, k in VERDICT:
        if up >= lim:
            return L(en, ar), k
    return L(*VERDICT[-1][1:3]), VERDICT[-1][3]


def band_svg(r, W=760, narrow=False):
    """The valuation band: undervalued (green, under 80% of fair value), about right, overvalued (red, over 120%); the fair value,
    the bear-to-bull range and today's price on it. narrow: the phone version (its own proportions, the two labels on two rows)."""
    fv, p, bear, bull = r["fv"], r["price"], r["bear"], r["bull"]
    lo = min(bear, p, fv * 0.7) * 0.92
    hi = max(bull, p, fv * 1.3) * 1.06
    fs = 1.0 if not narrow else 1.08
    pad, y = 14, (58 if not narrow else 72)
    H = y + 70
    x = lambda v: pad + (v - lo) / (hi - lo) * (W - 2 * pad)
    z1, z2 = x(fv * 0.8), x(fv * 1.2)
    f = T.FONT
    parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="direction:ltr">',
             f'<defs><linearGradient id="fvg{W}" x1="0" x2="1"><stop offset="0" stop-color="#16A34A"/><stop offset="1" stop-color="#22C55E"/></linearGradient>'
             f'<linearGradient id="fvr{W}" x1="0" x2="1"><stop offset="0" stop-color="#EF4444"/><stop offset="1" stop-color="#B91C1C"/></linearGradient>'
             f'<filter id="fvgl{W}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/>'
             '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
             f'<rect x="{pad}" y="{y - 9}" width="{max(z1 - pad, 0):.1f}" height="18" rx="9" fill="url(#fvg{W})" opacity=".85"/>',
             f'<rect x="{z1:.1f}" y="{y - 9}" width="{max(z2 - z1, 0):.1f}" height="18" fill="#E8A93B" opacity=".55"/>',
             f'<rect x="{z2:.1f}" y="{y - 9}" width="{max(W - pad - z2, 0):.1f}" height="18" rx="9" fill="url(#fvr{W})" opacity=".85"/>',
             f'<rect x="{x(bear):.1f}" y="{y - 14}" width="{max(x(bull) - x(bear), 2):.1f}" height="28" rx="8" fill="none" stroke="#C4B5FD" '
             f'stroke-width="1.6" stroke-dasharray="4 3"/>']

    def anchor(xx):
        return "start" if xx < W * 0.16 else "end" if xx > W * 0.84 else "middle"
    # under the bar: what each zone means, then the bear and bull cases (two rows, so nothing sits on the markers)
    for xx, en, ar, col in (((pad + z1) / 2, "Undervalued", "أقل من قيمته", "#4ADE80"), ((z1 + z2) / 2, "About right", "قريب من العادل", "#F5B94A"),
                            ((z2 + W - pad) / 2, "Overvalued", "أعلى من قيمته", "#F87171")):
        parts.append(f'<text x="{xx:.1f}" y="{y + 31}" text-anchor="middle" font-size="{11 * fs:.1f}" font-weight="700" fill="{col}" '
                     f'font-family="{f}">{T.esc(L(en, ar))}</text>')
    for v, en, ar in ((bear, "Bear", "متشائم"), (bull, "Bull", "متفائل")):
        parts.append(f'<line x1="{x(v):.1f}" y1="{y + 14}" x2="{x(v):.1f}" y2="{y + 40}" stroke="#C4B5FD" stroke-opacity=".5" stroke-dasharray="2 2"/>'
                     f'<text x="{x(v):.1f}" y="{y + 54}" text-anchor="{anchor(x(v))}" font-size="{11 * fs:.1f}" fill="#A09AAB" font-family="{f}">{T.esc(L(en, ar))} '
                     f'{LRI}${v:,.0f}{PDI}</text>')
    xf, xp = x(fv), x(p)
    parts.append(f'<path d="M{xf:.1f} {y - 13} L{xf + 9:.1f} {y} L{xf:.1f} {y + 13} L{xf - 9:.1f} {y} Z" fill="#fff" stroke="#7B45F0" stroke-width="2.5" '
                 f'filter="url(#fvgl{W})"/>')
    if narrow:                                         # two rows: the price on top, the fair value under it
        a_f, a_p, y_f, y_p = anchor(xf), anchor(xp), y - 22, y - 44
    else:
        near = abs(xf - xp) < 150
        a_f = ("end" if xf < xp else "start") if near else anchor(xf)
        a_p = ("start" if xf < xp else "end") if near else anchor(xp)
        y_f, y_p = y - 22, y - 30
    parts.append(f'<text x="{xf:.1f}" y="{y_f}" text-anchor="{a_f}" font-size="{12.5 * fs:.1f}" font-weight="800" fill="#C4B5FD" font-family="{f}">'
                 f'{T.esc(L("Fair value", "القيمة العادلة"))} {LRI}${fv:,.2f}{PDI}</text>')
    parts.append(f'<line x1="{xp:.1f}" y1="{y - 16 if not narrow else y_p + 6}" x2="{xp:.1f}" y2="{y + 16}" stroke="#fff" stroke-width="3" stroke-linecap="round"/>'
                 f'<circle cx="{xp:.1f}" cy="{y - 20 if not narrow else y_p + 6}" r="5" fill="#fff"/>'
                 f'<text x="{xp:.1f}" y="{y_p}" text-anchor="{a_p}" font-size="{12.5 * fs:.1f}" font-weight="800" fill="#fff" font-family="{f}">'
                 f'{T.esc(L("Price", "السعر"))} {LRI}${p:,.2f}{PDI}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _method_card(key, v, w, r, ref=False):
    p = r["price"]
    en, ar, ic = METHOD.get(key, ("Analysts' target", "هدف المحللين", "flag"))
    d = (v / p - 1) * 100
    lo, hi = min(v, p) * 0.8, max(v, p) * 1.15
    pos = lambda z: (z - lo) / (hi - lo) * 100
    col = "linear-gradient(90deg,#16A34A,#4ADE80)" if v >= p else "linear-gradient(90deg,#F87171,#DC2626)"
    a, b = sorted((pos(p), pos(v)))
    if key == "dcf":
        desc = L(f"Free cash flow <bdi>{_big(r['fcf0'])}</bdi> grows <bdi>{r['g'] * 100:.1f}%</bdi> a year for 5 years, slows to "
                 f"<bdi>{r['gt'] * 100:.1f}%</bdi>, discounted at <bdi>{r['ke'] * 100:.1f}%</bdi>, plus net cash.",
                 f"التدفق النقدي الحر <bdi>{_big(r['fcf0'])}</bdi> ينمو <bdi>{r['g'] * 100:.1f}%</bdi> سنوياً 5 سنوات، ثم يتباطأ إلى "
                 f"<bdi>{r['gt'] * 100:.1f}%</bdi>، مخصوم بـ <bdi>{r['ke'] * 100:.1f}%</bdi>، مع صافي الكاش.")
    elif key == "pb":
        desc = L(f"Book value <bdi>{_m(r['bvps'])}</bdi> a share × (ROE <bdi>{(r['roe'] or 0) * 100:.1f}%</bdi> − growth) ÷ (<bdi>{r['ke'] * 100:.1f}%</bdi> − growth).",
                 f"القيمة الدفترية <bdi>{_m(r['bvps'])}</bdi> للسهم × (العائد على الملكية <bdi>{(r['roe'] or 0) * 100:.1f}%</bdi> − النمو) ÷ (<bdi>{r['ke'] * 100:.1f}%</bdi> − النمو).")
    elif key == "pe":
        k = L("next year's", "السنة الجاية") if r["eps_kind"] == "fwd" else L("last year's", "آخر سنة")
        desc = L(f"{k} EPS <bdi>{_m(r['eps'])}</bdi> × the median P/E <bdi>{r['pe_med']:.1f}</bdi> of its last fiscal years.",
                 f"ربحية السهم ({k}) <bdi>{_m(r['eps'])}</bdi> × متوسط مكرر الربحية <bdi>{r['pe_med']:.1f}</bdi> في آخر سنواته المالية.")
    elif key == "graham":
        desc = L(f"EPS <bdi>{_m(r['eps'])}</bdi> × (8.5 + 2 × growth <bdi>{_clip(r['g'] * 100, 0, 20):.1f}</bdi>) × 4.4 ÷ bond yield <bdi>{r['bond'] * 100:.2f}%</bdi>.",
                 f"ربحية السهم <bdi>{_m(r['eps'])}</bdi> × (8.5 + 2 × النمو <bdi>{_clip(r['g'] * 100, 0, 20):.1f}</bdi>) × 4.4 ÷ عائد السندات <bdi>{r['bond'] * 100:.2f}%</bdi>.")
    else:
        n = r.get("n_an") or 0
        desc = (L(f"The mean 12-month target of {n} analysts. Shown to compare, not blended in.",
                  f"متوسط السعر المستهدف لـ {n} محلل خلال 12 شهر. للمقارنة فقط وما يدخل في الحساب.") if n else
                L("The analysts' mean 12-month target. Shown to compare, not blended in.",
                  "متوسط السعر المستهدف للمحللين خلال 12 شهر. للمقارنة فقط وما يدخل في الحساب."))
    wt = L("for comparison", "للمقارنة") if ref else L(f"weight {w * 100:.0f}%", f"الوزن {w * 100:.0f}%")
    return (f'<div class="fvm{" ref" if ref else ""}"><div class="h">{T.icon(ic)}<span>{T.esc(L(en, ar))}</span><span class="w">{wt}</span></div>'
            f'<div class="v"><b>{_m(v)}</b><em class="{"up" if d >= 0 else "dn"}">{d:+.1f}%</em></div>'
            f'<div class="bar"><i style="left:{a:.1f}%;width:{max(b - a, 1.5):.1f}%;background:{col}"></i><b style="left:{pos(p):.1f}%"></b></div>'
            f'<div class="d">{desc}</div></div>')


def card_html(r):
    lab, k = verdict(r["up"])
    line = {"uv": "linear-gradient(90deg,#16A34A,#4ADE80)", "suv": "linear-gradient(90deg,#16A34A,#4ADE80)", "fair": "linear-gradient(90deg,#D97706,#F5B94A)",
            "sov": "linear-gradient(90deg,#DC2626,#F87171)", "ov": "linear-gradient(90deg,#DC2626,#F87171)"}[k]
    up = r["up"]
    n_on = {"high": 3, "medium": 2, "low": 1}[r["conf"]]
    dots = '<span class="dots">' + "".join(f'<i class="{"on" if i < n_on else ""}"></i>' for i in range(3)) + "</span>"
    conf = {"high": L("High", "عالية"), "medium": L("Medium", "متوسطة"), "low": L("Low", "منخفضة")}[r["conf"]]
    conf_s = {"high": L("the methods agree", "الطرق متقاربة"), "medium": L("the methods differ a bit", "الطرق مختلفة شوي"),
              "low": L("few data, read with care", "بيانات قليلة، اقرأها بحذر")}[r["conf"]]
    cells = (f'<div class="cell"><div class="l">{L("Price now", "السعر الحالي")}</div><div class="v"><span>{_m(r["price"])}</span></div></div>'
             f'<div class="cell {"up" if up >= 0 else "dn"}"><div class="l">{L("To fair value", "إلى القيمة العادلة")}</div><div class="v"><span>{up:+.1f}%</span></div>'
             f'<div class="s">{L("upside" if up >= 0 else "downside", "صعود" if up >= 0 else "نزول")}</div></div>'
             f'<div class="cell"><div class="l">{L("Confidence", "الثقة")}</div><div class="v">{conf}{dots}</div><div class="s">{conf_s}</div></div>')
    methods = "".join(_method_card(m, v, r["weights"][m], r) for m, v in r["methods"].items())
    if r.get("target"):
        methods += _method_card("target", r["target"], 0, r, ref=True)
    net = r["cash"] - r["debt"]
    chips = [("percent", L("Discount rate", "معدل الخصم"), f"{r['ke'] * 100:.1f}%"),
             ("trending_up", L("Growth", "النمو") + f" ({L(*GSRC[r['g_src']])})", f"{r['g'] * 100:.1f}%"),
             ("all_inclusive", L("Long-run growth", "النمو طويل المدى"), f"{r['gt'] * 100:.1f}%"),
             ("account_balance", L("10Y Treasury", "عائد 10 سنوات"), f"{r['rf'] * 100:.2f}%"),
             ("hub", L("Beta", "بيتا"), f"{r['beta']:.2f}")]
    if "dcf" in r["methods"]:                           # banks' cash and debt are their business, not part of the value
        chips.append(("savings", L("Net cash" if net >= 0 else "Net debt", "صافي الكاش" if net >= 0 else "صافي الدين"), _big(abs(net))))
    chips_h = "".join(f'<span>{T.icon(ic)}{T.esc(lab_)} <b>{v}</b></span>' for ic, lab_, v in chips)
    return (f'<div class="fvc" style="--fvline:{line}"><div class="hd"><div class="t">{T.icon("balance")}{L("Fair value", "القيمة العادلة")}'
            f'<small>· {L("what the business is worth per share", "قيمة الشركة الحقيقية للسهم")}</small></div><span class="fvv {k}">{T.esc(lab)}</span></div>'
            f'<div class="top"><div class="big"><div class="l">{L("Fair value per share", "القيمة العادلة للسهم")}</div>'
            f'<div class="v"><span>{_m(r["fv"])}</span></div><div class="r">{L("Range", "المدى")} <bdi>{_m(r["bear"])}</bdi> – <bdi>{_m(r["bull"])}</bdi> '
            f'{L("(bear to bull case)", "(من المتشائم للمتفائل)")}</div></div><div class="cells">{cells}</div></div>'
            f'<div class="band wide">{band_svg(r)}</div><div class="band narrow">{band_svg(r, 400, True)}</div>'
            f'<div class="ms3">{methods}</div><div class="as">{chips_h}</div>'
            f'<div class="nt">{L("An estimate from public data (Yahoo Finance), not a price prediction: small changes in growth or the discount rate move it a lot.", "تقدير من بيانات عامة (ياهو فاينانس) وليس توقعاً للسعر: أي تغيير بسيط في النمو أو معدل الخصم يحركه كثير.")}</div></div>')


def section(sym, price=None, key="fv"):
    """The fair value block of one company (the scanner's fundamental analysis and the stock page's financials)."""
    ui.html(CSS)
    r = value(sym, price)
    if not r.get("ok"):
        why = r.get("why")
        msg = {"not_equity": L("A fair value is computed for company shares, not for funds, indices or crypto.",
                               "القيمة العادلة تنحسب لأسهم الشركات، مو للصناديق والمؤشرات والعملات الرقمية."),
               "no_profit": L("<b>No fair value yet:</b> the company doesn't make steady profits or free cash flow, so a value from them would mislead. "
                              "The analysts' targets are a better guide for now.",
                              "<b>ما فيه قيمة عادلة للحين:</b> الشركة ما تحقق أرباح أو تدفق نقدي حر ثابت، فأي قيمة منها بتكون مضللة. أهداف المحللين أفضل مرجع حالياً.")}.get(
            why, L("Yahoo Finance sent no financial data for this company right now; the fair value is tried again on the next view.",
                   "ياهو فاينانس ما أرسل البيانات المالية لهالشركة الحين، والقيمة العادلة تنحسب من جديد مع الفتح القادم."))
        ui.html(f'<div class="fvempty">{T.icon("balance")} {msg}</div>')
        return r
    ui.html(card_html(r))
    with st.expander(L("How this fair value is worked out", "كيف انحسبت القيمة العادلة"), icon=":material/calculate:"):
        ui.html(f'<div style="font-size:.86rem;line-height:1.7;color:#CFC8DA">{explain(r)}</div>')
        if r.get("dcf"):
            d = r["dcf"]
            rows = [{L("Year", "السنة"): t, L("Growth", "النمو"): g * 100, L("Free cash flow", "التدفق النقدي الحر"): T.fmt_big(f),
                     L("Worth today", "قيمته اليوم"): T.fmt_big(pv)} for t, g, f, pv in d["rows"]]
            ui.table(pd.DataFrame(rows), fmt={L("Growth", "النمو"): "{:+.1f}%"}, title=L("Ten years of cash flow", "عشر سنوات من التدفقات النقدية"),
                     icon="waterfall_chart")
            ui.html(f'<div class="fvc" style="--fvline:linear-gradient(90deg,{T.ACCENT},{T.VIOLET});padding:12px 16px"><div class="as" style="margin-top:0">'
                    f'<span>{L("Ten years, today", "العشر سنوات بقيمة اليوم")} <b>{T.fmt_big(d["ev"] - d["pv_tv"])}</b></span>'
                    f'<span>{L("After year 10, today", "ما بعد السنة 10 بقيمة اليوم")} <b>{T.fmt_big(d["pv_tv"])}</b></span>'
                    f'<span>{L("+ cash − debt", "+ الكاش − الدين")} <b>{T.fmt_big(r["cash"] - r["debt"])}</b></span>'
                    f'<span>{L("÷ shares", "÷ عدد الأسهم")} <b>{T.fmt_big(r["shares"])}</b></span>'
                    f'<span>{L("= per share", "= للسهم")} <b>{_m(d["equity"] / r["shares"])}</b></span></div></div>')
    return r


def explain(r):
    parts = [L("The fair value blends three ways of valuing the company, each one a classic of fundamental analysis:",
               "القيمة العادلة تجمع ثلاث طرق لتقييم الشركة، كل وحدة منها من أساسيات التحليل الأساسي:")]
    if "dcf" in r["methods"]:
        parts.append(L("<b>Discounted cash flow</b>: a company is worth the cash it will make in the future, in today's money. Its free cash flow "
                       f"(the average of the last year and the two before, <bdi>{_big(r['fcf0'])}</bdi>) grows <bdi>{r['g'] * 100:.1f}%</bdi> a year for five years, "
                       f"then slows to <bdi>{r['gt'] * 100:.1f}%</bdi>; every year is brought back to today at <bdi>{r['ke'] * 100:.1f}%</bdi> (the 10-year Treasury "
                       f"<bdi>{r['rf'] * 100:.2f}%</bdi> + beta <bdi>{r['beta']:.2f}</bdi> × 4.5% for the risk of stocks).",
                       "<b>التدفقات النقدية المخصومة</b>: الشركة تسوى الكاش اللي بتحققه بالمستقبل، بقيمة اليوم. التدفق النقدي الحر "
                       f"(متوسط آخر سنة والسنتين قبلها، <bdi>{_big(r['fcf0'])}</bdi>) ينمو <bdi>{r['g'] * 100:.1f}%</bdi> سنوياً خمس سنوات، "
                       f"ثم يتباطأ إلى <bdi>{r['gt'] * 100:.1f}%</bdi>، وكل سنة ترجع لقيمة اليوم بمعدل <bdi>{r['ke'] * 100:.1f}%</bdi> (عائد سندات 10 سنوات "
                       f"<bdi>{r['rf'] * 100:.2f}%</bdi> + بيتا <bdi>{r['beta']:.2f}</bdi> × 4.5% مقابل مخاطرة الأسهم)."))
    if "pb" in r["methods"]:
        parts.append(L("<b>Justified price-to-book</b> (banks and insurers, whose cash flows don't mean the same): the book value is worth more than "
                       "its face value when the company earns more on it than investors ask for.",
                       "<b>مضاعف القيمة الدفترية المبرر</b> (للبنوك والتأمين لأن تدفقاتها النقدية ما تعني نفس الشي): القيمة الدفترية تسوى أكثر من رقمها "
                       "إذا الشركة تربح عليها أكثر من العائد اللي يطلبه المستثمرين."))
    if "pe" in r["methods"]:
        pes = ", ".join(f"{x:.1f}" for x in r["pes"][:4])
        parts.append(L(f"<b>Earnings at its usual multiple</b>: the P/E the stock traded at in its last fiscal years (<bdi>{pes}</bdi>, median <bdi>{r['pe_med']:.1f}</bdi>) "
                       "applied to its earnings per share.",
                       f"<b>الأرباح × مكررها المعتاد</b>: مكرر الربحية اللي تداول عليه السهم في آخر سنواته المالية (<bdi>{pes}</bdi>، الوسيط <bdi>{r['pe_med']:.1f}</bdi>) "
                       "مضروب في ربحية السهم."))
    if "graham" in r["methods"]:
        parts.append(L("<b>Graham's formula</b>: Benjamin Graham's intrinsic value, a no-growth company is worth 8.5× its earnings, plus two times its "
                       "growth rate, adjusted for today's bond yields.",
                       "<b>معادلة غراهام</b>: القيمة الجوهرية عند بنجامين غراهام، الشركة بدون نمو تسوى 8.5 ضعف أرباحها، ويُضاف ضعفين نسبة نموها، "
                       "مع تعديلها حسب عوائد السندات الحالية."))
    parts.append(L("The bear and bull cases move the discount rate one point and the growth by −40% / +30%. Weights: 40% cash flows (or book value), "
                   "35% usual multiple, 25% Graham.",
                   "الحالة المتشائمة والمتفائلة تحرك معدل الخصم نقطة والنمو −40% / +30%. الأوزان: 40% التدفقات (أو القيمة الدفترية)، "
                   "35% المكرر المعتاد، 25% غراهام."))
    return "<br><br>".join(parts)


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "20.5"
