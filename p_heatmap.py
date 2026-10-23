"""
p_heatmap.py - TURA Pro · Market Heatmap (v2)

Modern, high-contrast treemap:  Market → Sector → Industry → Company.
- Industries are drawn as clearly-labelled tiles (name + % change) at the top level.
- Clicking a sector / industry on the map drills down AND opens, under the map, the list of all
  companies in that sector/industry with a side-by-side comparison of their financial metrics
  (valuation, profitability, growth, balance sheet, analysts) plus a composite score and rank.
- Works with the mouse click on the map (Streamlit chart selections) and with the drop-downs
  under the map as a fallback.

On the home page (the US market) as section(): the map with its controls, the drill-down and the comparison, without the
page's header; the frame of the day is kept ready in the background (warm.py) so the map draws at once.
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

import data
import theme as T
import ui
import universe as U
from i18n import L, is_ar, sector_name

ss = st.session_state

# ---------------------------------------------------------------- settings
PERIODS = {"1D": 1, "1W": 5, "1M": 21, "3M": 63, "YTD": "ytd"}
COLOR_RANGE = {"1D": 3, "1W": 6, "1M": 10, "3M": 20, "YTD": 40}      # ± % that saturates the colour
COLORSCALE = [[0, "#F23645"], [0.3, "#9B2530"], [0.5, "#2A2E39"], [0.7, "#0E7A52"], [1, "#089981"]]
FONT = T.FONT

INDUSTRY_AR = {
    "Semiconductors": "أشباه الموصلات", "Semiconductor Equipment & Materials": "معدات أشباه الموصلات",
    "Software - Infrastructure": "برمجيات - بنية تحتية", "Software - Application": "برمجيات - تطبيقات",
    "Consumer Electronics": "إلكترونيات استهلاكية", "Communication Equipment": "معدات اتصالات",
    "Information Technology Services": "خدمات تقنية المعلومات", "Computer Hardware": "عتاد الحاسب",
    "Internet Content & Information": "محتوى ومعلومات الإنترنت", "Entertainment": "الترفيه",
    "Telecom Services": "خدمات الاتصالات", "Electronic Gaming & Multimedia": "الألعاب الإلكترونية",
    "Internet Retail": "تجزئة إلكترونية", "Auto Manufacturers": "صناعة السيارات", "Home Improvement Retail": "تجزئة تحسين المنازل",
    "Restaurants": "المطاعم", "Travel Services": "خدمات السفر", "Apparel Retail": "تجزئة الملابس",
    "Footwear & Accessories": "الأحذية والإكسسوارات", "Auto Parts": "قطع غيار السيارات", "Lodging": "الفنادق",
    "Discount Stores": "متاجر التخفيضات", "Household & Personal Products": "منتجات منزلية وشخصية",
    "Beverages - Non-Alcoholic": "المشروبات", "Tobacco": "التبغ", "Confectioners": "الحلويات",
    "Insurance - Diversified": "تأمين متنوع", "Banks - Diversified": "بنوك كبرى", "Credit Services": "خدمات ائتمانية",
    "Capital Markets": "أسواق المال", "Asset Management": "إدارة الأصول",
    "Financial Data & Stock Exchanges": "بيانات مالية وبورصات", "Insurance - Property & Casualty": "تأمين ممتلكات وحوادث",
    "Drug Manufacturers - General": "شركات الأدوية الكبرى", "Healthcare Plans": "التأمين الصحي",
    "Medical Devices": "الأجهزة الطبية", "Diagnostics & Research": "التشخيص والأبحاث",
    "Medical Instruments & Supplies": "أدوات ومستلزمات طبية", "Biotechnology": "التقنية الحيوية",
    "Medical Care Facilities": "المستشفيات والرعاية", "Aerospace & Defense": "الطيران والدفاع",
    "Farm & Heavy Construction Machinery": "المعدات الثقيلة والزراعية", "Specialty Industrial Machinery": "الآلات الصناعية",
    "Conglomerates": "تكتلات صناعية", "Railroads": "السكك الحديدية", "Staffing & Employment Services": "خدمات التوظيف",
    "Waste Management": "إدارة النفايات", "Integrated Freight & Logistics": "الشحن واللوجستيات",
    "Oil & Gas Integrated": "نفط وغاز متكامل", "Oil & Gas E&P": "استكشاف وإنتاج النفط", "Oil & Gas Midstream": "نقل وتخزين النفط",
    "Oil & Gas Refining & Marketing": "تكرير وتسويق النفط", "Oil & Gas Equipment & Services": "معدات وخدمات نفطية",
    "Specialty Chemicals": "كيماويات متخصصة", "Gold": "الذهب", "Copper": "النحاس", "Steel": "الصلب",
    "REIT - Industrial": "صناديق عقارية صناعية", "REIT - Healthcare Facilities": "صناديق عقارية صحية",
    "REIT - Specialty": "صناديق عقارية متخصصة", "REIT - Retail": "صناديق عقارية تجارية",
    "Utilities - Regulated Electric": "كهرباء منظمة", "Utilities - Renewable": "طاقة متجددة",
    "Utilities - Independent Power Producers": "منتجو طاقة مستقلون",
}


def industry_name(i):
    return L(i, INDUSTRY_AR.get(i, i))


# ---------------------------------------------------------------- price frame
@st.cache_data(ttl=300, show_spinner=False)
def heatmap_frame(period="1D", sizing="cap"):
    """Symbol, Name, Sector, Industry, Chg %, Price, Cap, Volume."""
    hist = data.history_many(tuple(U.US_UNIVERSE), "1y")
    caps, _ = data.market_caps()
    n = PERIODS[period]
    rows = []
    for s, df in hist.items():
        if s not in U.STOCKS:
            continue
        c = df["Close"]
        if n == "ytd":
            ytd = c[c.index.year == c.index[-1].year]
            if len(ytd) < 2:
                continue
            chg = (c.iloc[-1] / ytd.iloc[0] - 1) * 100
        elif len(c) > n:
            chg = (c.iloc[-1] / c.iloc[-1 - n] - 1) * 100
        else:
            continue
        name, sec, ind, _ = U.STOCKS[s]
        rows.append({"Symbol": s, "Name": name, "Sector": sec, "Industry": ind, "Chg %": float(chg),
                     "Price": float(c.iloc[-1]), "Cap": float(caps.get(s, 1e9)),
                     "Size": float(caps.get(s, 1e9)) if sizing == "cap" else 1.0,
                     "Volume": float(df["Volume"].iloc[-1]) if "Volume" in df else np.nan})
    return pd.DataFrame(rows)


def _wavg(g):
    w = g["Cap"].sum()
    return float(np.average(g["Chg %"], weights=g["Cap"])) if w > 0 else float(g["Chg %"].mean())


# ---------------------------------------------------------------- treemap figure
def treemap_figure(df, period="1D", level="", detail="industries", height=720, root_label="US Market"):
    """Returns (figure, ids). Node ids:  root | s:<Sector> | i:<Sector>|<Industry> | t:<Symbol>"""
    ids, labels, parents, values, colors, text, custom = [], [], [], [], [], [], []

    def add(i, lab, par, val, col, txt, cd):
        ids.append(i); labels.append(lab); parents.append(par); values.append(float(val))
        colors.append(float(col)); text.append(txt); custom.append(cd)

    tot = _wavg(df)
    add("root", root_label, "", df["Size"].sum(), tot, f"{root_label}  {tot:+.2f}%",
        ["root", root_label, "", T.fmt_big(df["Cap"].sum()), f"{tot:+.2f}%", len(df)])
    for sec, g in df.groupby("Sector"):
        sid = f"s:{sec}"
        v = _wavg(g)
        add(sid, sector_name(sec), "root", g["Size"].sum(), v, f"<b>{sector_name(sec)}</b>  {v:+.2f}%",
            [sid, sector_name(sec), L("Sector", "قطاع"), T.fmt_big(g["Cap"].sum()), f"{v:+.2f}%", len(g)])
        for ind, h in g.groupby("Industry"):
            iid = f"i:{sec}|{ind}"
            v = _wavg(h)
            add(iid, industry_name(ind), sid, h["Size"].sum(), v, f"<b>{industry_name(ind)}</b><br>{v:+.2f}%",
                [iid, industry_name(ind), L("Industry", "صناعة"), T.fmt_big(h["Cap"].sum()), f"{v:+.2f}%", len(h)])
            for _, r in h.sort_values("Size", ascending=False).iterrows():
                add(f"t:{r['Symbol']}", r["Symbol"], iid, r["Size"], r["Chg %"], f"<b>{r['Symbol']}</b><br>{r['Chg %']:+.2f}%",
                    [f"t:{r['Symbol']}", r["Name"], industry_name(r["Industry"]), T.fmt_big(r["Cap"]), f"{r['Chg %']:+.2f}%",
                     f"${r['Price']:,.2f}"])

    rng = COLOR_RANGE.get(period, 3)
    marker = dict(colors=colors, colorscale=COLORSCALE, cmid=0, cmin=-rng, cmax=rng,
                  line=dict(width=2, color=T.BG), pad=dict(t=30, l=4, r=4, b=4), showscale=False)
    tr = go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, branchvalues="total", text=text, customdata=custom,
        texttemplate="%{text}", textposition="middle center", textfont=dict(family=FONT, size=15, color="#FFFFFF"),
        hovertemplate=("<b>%{customdata[1]}</b> · %{customdata[2]}<br>"
                       + L("Market cap", "القيمة السوقية") + ": %{customdata[3]}<br>"
                       + L("Change", "التغير") + ": <b>%{customdata[4]}</b><br>"
                       + L("Companies / Price", "الشركات / السعر") + ": %{customdata[5]}<extra></extra>"),
        hoverlabel=dict(bgcolor=T.CARD2, bordercolor=T.BORDER, font=dict(family=FONT, size=13, color=T.TEXT)),
        marker=marker, level=level or "", maxdepth=3 if detail == "industries" else 4,
        pathbar=dict(visible=True, thickness=34, side="top", textfont=dict(family=FONT, size=14, color=T.TEXT),
                     edgeshape=">"),
        tiling=dict(pad=3, packing="squarify"), root=dict(color=T.BG))
    fig = go.Figure(tr)
    try:                               # rounded tiles (plotly >= 5.14)
        fig.update_traces(marker_cornerradius=6)
    except Exception:
        pass
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT, color=T.TEXT),
                      uniformtext=dict(minsize=9, mode="hide"), showlegend=False)
    return fig, ids


def _clicked_id(event, ids):
    """Node id from a Streamlit chart-selection event (several Streamlit versions supported)."""
    try:
        pts = event.selection.points
    except Exception:
        try:
            pts = event["selection"]["points"]
        except Exception:
            return None
    if not pts:
        return None
    p = pts[-1]
    cd = p.get("customdata")
    if isinstance(cd, (list, tuple)) and cd and str(cd[0]) in set(ids):
        return str(cd[0])
    for k in ("id",):
        if p.get(k) in ids:
            return p[k]
    idx = p.get("point_index", p.get("point_number"))
    if isinstance(idx, int) and 0 <= idx < len(ids):
        return ids[idx]
    return None


# ---------------------------------------------------------------- fundamentals (company comparison)
_INFO, _LOCK, _TTL = {}, threading.Lock(), 6 * 3600


def _fetch(sym):
    try:
        i = dict(yf.Ticker(sym).info or {})
        return sym, i if len(i) > 3 else {}
    except Exception:
        return sym, {}


def infos(symbols):
    """symbol -> yfinance info dict. Fetched in parallel, cached in memory for 6h."""
    now = time.time()
    need = [s for s in symbols if s not in _INFO or now - _INFO[s][1] > _TTL]
    if need:
        with ThreadPoolExecutor(max_workers=8) as ex:
            res = list(ex.map(_fetch, need))
        with _LOCK:
            for s, i in res:
                if i:
                    _INFO[s] = (i, now)
    return {s: _INFO[s][0] for s in symbols if s in _INFO}


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not (isinstance(v, float) and np.isnan(v)) else np.nan


def _pct(v):
    v = _num(v)
    return v * 100 if pd.notna(v) else np.nan


# column -> (english, arabic, higher_is_better or None)
METRICS = {
    "Price": ("Price", "السعر", None), "Chg %": ("Change", "التغير", True), "Cap": ("Market cap", "القيمة السوقية", None),
    "P/E": ("P/E", "مكرر الربحية", False), "Fwd P/E": ("Fwd P/E", "المكرر المستقبلي", False), "PEG": ("PEG", "PEG", False),
    "P/S": ("P/S", "السعر/المبيعات", False), "P/B": ("P/B", "السعر/الدفترية", False), "EV/EBITDA": ("EV/EBITDA", "EV/EBITDA", False),
    "Gross %": ("Gross margin", "الهامش الإجمالي", True), "Op %": ("Op. margin", "الهامش التشغيلي", True),
    "Net %": ("Net margin", "صافي الهامش", True), "ROE %": ("ROE", "العائد على الملكية", True),
    "Rev g %": ("Revenue growth", "نمو الإيرادات", True), "EPS g %": ("EPS growth", "نمو الأرباح", True),
    "D/E": ("Debt/Equity", "الديون/الملكية", False), "Div %": ("Div. yield", "عائد التوزيعات", True),
    "Beta": ("Beta", "بيتا", None), "52W %": ("52W perf", "أداء 52 أسبوع", True),
    "Upside %": ("Analyst upside", "مساحة الصعود", True), "Rating": ("Analyst rating", "تقييم المحللين", False),
    "Short %": ("Short float", "البيع على المكشوف", False), "Score": ("TURA score", "تقييم TURA", True),
}
PCT_COLS = ["Chg %", "Gross %", "Op %", "Net %", "ROE %", "Rev g %", "EPS g %", "Div %", "52W %", "Upside %", "Short %"]
SCORE_PARTS = {"P/E": False, "PEG": False, "P/B": False, "Rev g %": True, "EPS g %": True, "Net %": True, "ROE %": True,
               "D/E": False, "Upside %": True, "Chg %": True}
VIEWS = {
    ("Overview", "نظرة عامة"): ["Symbol", "Name", "Industry", "Price", "Chg %", "Cap", "P/E", "Div %", "52W %", "Score"],
    ("Valuation", "التقييم"): ["Symbol", "Cap", "P/E", "Fwd P/E", "PEG", "P/S", "P/B", "EV/EBITDA", "Upside %", "Rating", "Score"],
    ("Profitability & growth", "الربحية والنمو"): ["Symbol", "Gross %", "Op %", "Net %", "ROE %", "Rev g %", "EPS g %", "Score"],
    ("Risk & health", "المخاطر والميزانية"): ["Symbol", "D/E", "Beta", "Short %", "Div %", "52W %", "Chg %", "Score"],
}


def comparison_frame(view, ind_label=None):
    """view: rows of heatmap_frame for one sector/industry. Adds fundamentals, composite score and rank."""
    ind_label = ind_label or industry_name
    inf = infos(view["Symbol"].tolist())
    rows = []
    for _, r in view.iterrows():
        i = inf.get(r["Symbol"], {})
        g = i.get
        price = _num(g("currentPrice")) if pd.notna(_num(g("currentPrice"))) else r["Price"]
        div = _num(g("trailingAnnualDividendRate")) if pd.notna(_num(g("trailingAnnualDividendRate"))) else _num(g("dividendRate"))
        tgt = _num(g("targetMeanPrice"))
        rows.append({
            "Symbol": r["Symbol"], "Name": r["Name"], "Industry": ind_label(r["Industry"]), "Price": price,
            "Chg %": r["Chg %"], "Cap": _num(g("marketCap")) if pd.notna(_num(g("marketCap"))) else r["Cap"],
            "P/E": _num(g("trailingPE")), "Fwd P/E": _num(g("forwardPE")), "PEG": _num(g("trailingPegRatio")),
            "P/S": _num(g("priceToSalesTrailing12Months")), "P/B": _num(g("priceToBook")), "EV/EBITDA": _num(g("enterpriseToEbitda")),
            "Gross %": _pct(g("grossMargins")), "Op %": _pct(g("operatingMargins")), "Net %": _pct(g("profitMargins")),
            "ROE %": _pct(g("returnOnEquity")), "Rev g %": _pct(g("revenueGrowth")), "EPS g %": _pct(g("earningsGrowth")),
            "D/E": _num(g("debtToEquity")), "Div %": div / price * 100 if pd.notna(div) and price else np.nan,
            "Beta": _num(g("beta")), "52W %": _pct(g("52WeekChange")),
            "Upside %": (tgt / price - 1) * 100 if pd.notna(tgt) and price else np.nan,
            "Rating": _num(g("recommendationMean")), "Short %": _pct(g("shortPercentOfFloat")),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    for c in METRICS:                                   # numbers as floats (a missing one is NaN, shown as a dash)
        if c in df and c != "Score":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # sanity clips (negative P/E = loss-making: treated as missing for valuation ranking)
    for c in ("P/E", "Fwd P/E", "PEG", "P/B", "P/S", "EV/EBITDA"):
        df.loc[df[c] <= 0, c] = np.nan
    parts = []
    for col, hib in SCORE_PARTS.items():
        pr = df[col].rank(pct=True)
        parts.append(pr if hib else 1 - pr + 1 / len(df))
    sc = pd.concat(parts, axis=1)
    cnt = sc.notna().sum(axis=1)
    df["Score"] = (sc.mean(axis=1) * 100).where(cnt >= 3).round(0)
    df["Rank"] = df["Score"].rank(ascending=False, method="min")
    return df.sort_values("Cap", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------- small UI pieces
def _layout(fig, height):
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=40, b=8), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT, color=T.TEXT, size=12),
                      xaxis=dict(gridcolor=T.BORDER, zerolinecolor=T.MUTED), yaxis=dict(gridcolor=T.BORDER, zerolinecolor=T.MUTED),
                      hoverlabel=dict(bgcolor=T.CARD2, bordercolor=T.BORDER, font=dict(family=FONT)), showlegend=False)
    return fig


def metric_bars(df, col, title, height=None):
    d = df[["Symbol", col]].dropna().sort_values(col)
    if d.empty:
        return None
    med = float(d[col].median())
    hib = METRICS[col][2]
    good = (d[col] >= med) if hib in (True, None) else (d[col] <= med)
    colors = [T.UP if ok else T.DOWN for ok in good] if hib is not None else [T.ACCENT] * len(d)
    suffix = "%" if col in PCT_COLS else ""
    fig = go.Figure(go.Bar(x=d[col], y=d["Symbol"].map(T.sym_label), orientation="h", marker=dict(color=colors, line=dict(width=0)),
                           text=[f"{v:,.1f}{suffix}" for v in d[col]], textposition="outside",
                           textfont=dict(color=T.TEXT, size=11), hovertemplate="<b>%{y}</b>: %{x:,.2f}" + suffix + "<extra></extra>"))
    fig.add_vline(x=med, line=dict(color=T.GOLD, width=1.5, dash="dot"),
                  annotation_text=L(f"median {med:,.1f}{suffix}", f"الوسيط {med:,.1f}{suffix}"),
                  annotation_font=dict(color=T.GOLD, size=11), annotation_position="top")
    fig.update_layout(title=dict(text=title, font=dict(size=14), x=0, xanchor="left"), bargap=0.3,
                      xaxis=dict(ticksuffix=suffix, showgrid=True), yaxis=dict(tickfont=dict(size=12)))
    return _layout(fig, height or max(260, 30 * len(d) + 90))


def valuation_scatter(df):
    d = df.dropna(subset=["Fwd P/E", "Rev g %"])
    if len(d) < 3:
        d = df.dropna(subset=["P/E", "Rev g %"])
        xcol = "P/E"
    else:
        xcol = "Fwd P/E"
    if len(d) < 3:
        return None
    size = np.sqrt(d["Cap"].fillna(1e9)) / np.sqrt(d["Cap"].max()) * 42 + 10
    fig = go.Figure(go.Scatter(
        x=d[xcol], y=d["Rev g %"], mode="markers+text", text=d["Symbol"].map(T.sym_label), textposition="top center",
        textfont=dict(size=11, color=T.TEXT),
        marker=dict(size=size, color=d["Chg %"], colorscale=COLORSCALE, cmid=0, cmin=-5, cmax=5,
                    line=dict(width=1, color=T.BG), opacity=0.9),
        customdata=np.stack([d["Name"], d["Cap"].map(T.fmt_big), d["Score"].fillna(0)], axis=1),
        hovertemplate=("<b>%{text}</b> %{customdata[0]}<br>" + xcol + ": %{x:.1f}<br>"
                       + L("Revenue growth", "نمو الإيرادات") + ": %{y:+.1f}%<br>"
                       + L("Market cap", "القيمة السوقية") + ": %{customdata[1]}<br>"
                       + L("TURA score", "تقييم TURA") + ": %{customdata[2]:.0f}<extra></extra>")))
    fig.add_hline(y=float(d["Rev g %"].median()), line=dict(color=T.MUTED, width=1, dash="dot"))
    fig.add_vline(x=float(d[xcol].median()), line=dict(color=T.MUTED, width=1, dash="dot"))
    fig.add_annotation(x=0.02, y=0.98, xref="paper", yref="paper", showarrow=False, font=dict(color=T.UP, size=11),
                       text=L("cheap & growing", "رخيص وينمو"), xanchor="left")
    fig.add_annotation(x=0.98, y=0.02, xref="paper", yref="paper", showarrow=False, font=dict(color=T.DOWN, size=11),
                       text=L("expensive & slow", "غالي وبطيء"), xanchor="right")
    fig.update_layout(title=dict(text=L(f"Valuation vs growth<br><span style='font-size:11px;color:{T.MUTED}'>{xcol} × revenue growth · bubble = market cap · colour = change</span>",
                                        f"التقييم مقابل النمو<br><span style='font-size:11px;color:{T.MUTED}'>{xcol} × نمو الإيرادات · الحجم = القيمة السوقية · اللون = التغير</span>"),
                                 font=dict(size=14), x=0, xanchor="left"),
                      xaxis=dict(title=xcol), yaxis=dict(title=L("Revenue growth %", "نمو الإيرادات %"), ticksuffix="%"))
    return _layout(fig, 440)


def _style_table(show, cols, raw):
    """Colour cells green/red versus the group median (direction-aware) and format numbers."""
    N = {c: L(*METRICS[c][:2]) if c in METRICS else L(c, {"Symbol": "الرمز", "Name": "الشركة", "Industry": "الصناعة", "Rank": "الترتيب"}.get(c, c))
         for c in cols}
    disp = show[cols].rename(columns=N)
    fmt = {}
    for c in cols:
        if c == "Cap":
            disp[N[c]] = disp[N[c]].map(T.fmt_big)
        elif c in PCT_COLS:
            fmt[N[c]] = "{:+.1f}%" if c in ("Chg %", "52W %", "Upside %", "Rev g %", "EPS g %") else "{:.1f}%"
        elif c == "Price":
            fmt[N[c]] = "{:,.2f}"
        elif c in ("Score", "Rank"):
            fmt[N[c]] = "{:.0f}"
        elif c in METRICS:
            fmt[N[c]] = "{:,.2f}" if c in ("Beta", "Rating", "PEG") else "{:,.1f}"
    sty = disp.style.format(fmt, na_rep="—")
    meds = {c: raw[c].median() for c in cols if c in METRICS and METRICS[c][2] is not None and c in raw}

    def vs_median(s, c):
        hib = METRICS[c][2]
        m = meds[c]
        out = []
        for v in raw[c].values:
            if pd.isna(v) or pd.isna(m):
                out.append("")
            elif (v >= m) == bool(hib):
                out.append(f"color:{T.UP};font-weight:600")
            else:
                out.append(f"color:{T.DOWN}")
        return pd.Series(out, index=s.index)
    for c in meds:
        sty = sty.apply(lambda s, c=c: vs_median(s, c), subset=[N[c]])
    if "Score" in cols:
        def score_bg(s):
            return pd.Series([f"background:rgba(212,175,55,{min(0.45, v / 220):.2f});font-weight:700" if pd.notna(v) else ""
                              for v in raw["Score"].values], index=s.index)
        sty = sty.apply(score_bg, subset=[N["Score"]])
    return sty


def company_table(df, with_industry, key="hm2"):
    """Comparison tabs for the companies of a sector / industry."""
    best = df.dropna(subset=["Score"]).sort_values("Score", ascending=False)
    k = st.columns(5)
    k[0].markdown(T.kpi("apartment", L("Companies", "الشركات"), f"{len(df)}", T.fmt_big(df["Cap"].sum()) + " " + L("total cap", "إجمالي القيمة")),
                  unsafe_allow_html=True)
    wa = float(np.average(df["Chg %"], weights=df["Cap"].fillna(1))) if len(df) else 0.0
    k[1].markdown(T.kpi("percent", L("Cap-weighted change", "التغير المرجّح"), f"{wa:+.2f}%",
                        f"{int((df['Chg %'] > 0).sum())} ▲ · {int((df['Chg %'] < 0).sum())} ▼", T.cls(wa)), unsafe_allow_html=True)
    k[2].markdown(T.kpi("price_check", L("Median P/E", "وسيط مكرر الربحية"),
                        f"{df['P/E'].median():.1f}" if df["P/E"].notna().any() else "—",
                        L(f"Fwd {df['Fwd P/E'].median():.1f}", f"مستقبلي {df['Fwd P/E'].median():.1f}") if df["Fwd P/E"].notna().any() else ""),
                  unsafe_allow_html=True)
    k[3].markdown(T.kpi("trending_up", L("Median growth / margin", "وسيط النمو / الهامش"),
                        f"{df['Rev g %'].median():+.1f}%" if df["Rev g %"].notna().any() else "—",
                        L(f"net margin {df['Net %'].median():.1f}%", f"صافي الهامش {df['Net %'].median():.1f}%") if df["Net %"].notna().any() else ""),
                  unsafe_allow_html=True)
    if not best.empty:
        b = best.iloc[0]
        k[4].markdown(T.kpi("workspace_premium", L("Best TURA score", "أعلى تقييم TURA"), f"{b['Symbol']}",
                            f"{b['Score']:.0f}/100 · {b['Name'][:18]}", "gold"), unsafe_allow_html=True)
    tabs = st.tabs([L(en, ar) for en, ar in VIEWS])
    for ti, (tab, (_, cols)) in enumerate(zip(tabs, VIEWS.items())):
        with tab:
            cols = [c for c in cols if with_industry or c != "Industry"]
            st.dataframe(_style_table(df, cols, df), hide_index=True, height=min(620, 40 + 36 * len(df)), key=f"{key}_tab_{ti}")
    st.caption(L("Green = better than the group median for that metric, red = worse. TURA score = average percentile across valuation, "
                 "growth, profitability, leverage, analyst upside and performance (100 = best in group).",
                 "الأخضر = أفضل من وسيط المجموعة في هذا المؤشر، والأحمر = أسوأ. تقييم TURA = متوسط الترتيب المئوي عبر التقييم والنمو "
                 "والربحية والديون وهدف المحللين والأداء (100 = الأفضل في المجموعة)."))


# ---------------------------------------------------------------- page
ALL = "__all__"


def _sector_changed():
    s = ss.get("hm2_sec_dd", ALL)
    ss.hm2_level = "root" if s == ALL else f"s:{s}"
    ss.hm2_last_sel = None


def _industry_changed():
    s, i = ss.get("hm2_sec_dd", ALL), ss.get("hm2_ind_dd", ALL)
    if s != ALL:
        ss.hm2_level = f"s:{s}" if i == ALL else f"i:{s}|{i}"
    ss.hm2_last_sel = None


def _crumbs(level):
    if not level or level == "root":
        return [("root", L("US Market", "السوق الأمريكي"))]
    out = [("root", L("US Market", "السوق الأمريكي"))]
    if level.startswith("s:"):
        out.append((level, sector_name(level[2:])))
    elif level.startswith("i:"):
        sec, ind = level[2:].split("|", 1)
        out += [(f"s:{sec}", sector_name(sec)), (level, industry_name(ind))]
    return out


def page_heatmap():
    ui.header("grid_view", "Market Heatmap", "الخريطة الحرارية",
              "Sectors and industries at a glance. Click a sector or an industry to zoom in and compare all of its companies.",
              "القطاعات والصناعات بنظرة واحدة. اضغط على قطاع أو صناعة للتكبير ومقارنة كل شركاتها.")
    _body()
    ui.foot()


def section(pre=None):
    """The map as a part of the home page: the title line, then the map and all that is under it. pre: the frame of the day
    made in the background ({(period, sizing): frame}), used when the visitor's choice matches."""
    ui.sec("grid_view", "Market heatmap", "الخريطة الحرارية")
    st.caption(L("Sectors and industries at a glance. Click a sector or an industry to zoom in and compare all of its companies.",
                 "القطاعات والصناعات بنظرة واحدة. اضغط على قطاع أو صناعة للتكبير ومقارنة كل شركاتها."))
    _body(pre)


def _body(pre=None):
    ss.setdefault("hm2_level", "root")
    ss.setdefault("hm2_last_sel", None)

    c1, c2, c3 = st.columns([1.5, 1, 1.2])
    period = c1.segmented_control(L("Performance", "الأداء"), list(PERIODS), default="1D", key="hm2_per") or "1D"
    size_opts = [L("Market cap", "القيمة السوقية"), L("Equal", "متساوٍ")]
    sizing = c2.segmented_control(L("Size by", "الحجم حسب"), size_opts, default=size_opts[0], key="hm2_size") or size_opts[0]
    det_opts = [L("Industries", "الصناعات"), L("Companies", "الشركات")]
    detail = c3.segmented_control(L("Detail", "التفصيل"), det_opts, default=det_opts[0], key="hm2_detail") or det_opts[0]

    with st.spinner(L("Building heatmap...", "جاري بناء الخريطة...")):
        sz = "equal" if sizing == size_opts[1] else "cap"
        df = (pre or {}).get((period, sz))
        if df is None:
            df = heatmap_frame(period, sz)
    if df.empty:
        st.warning(L("Market data is temporarily unavailable.", "بيانات السوق غير متاحة مؤقتاً."))
        return

    # ---- KPI strip
    tot = _wavg(df)
    w = df.assign(_w=df["Chg %"] * df["Cap"]).groupby("Sector")[["_w", "Cap"]].sum()
    by_sec = w["_w"] / w["Cap"]
    best, worst = by_sec.idxmax(), by_sec.idxmin()
    adv, dec = int((df["Chg %"] > 0).sum()), int((df["Chg %"] < 0).sum())
    k = st.columns(4)
    k[0].markdown(T.kpi("public", L(f"US market · {period}", f"السوق الأمريكي · {period}"), f"{tot:+.2f}%",
                        L("cap-weighted, top 175 stocks", "مرجّح بالقيمة السوقية، أكبر 175 سهم"), T.cls(tot)), unsafe_allow_html=True)
    k[1].markdown(T.kpi("balance", L("Breadth", "اتساع السوق"), f"{adv} ▲ · {dec} ▼",
                        L(f"{adv / len(df) * 100:.0f}% advancing", f"{adv / len(df) * 100:.0f}% صاعدة"), "up" if adv > dec else "down"),
                  unsafe_allow_html=True)
    k[2].markdown(T.kpi("trending_up", L("Leading sector", "القطاع الأقوى"), sector_name(best), f"{by_sec[best]:+.2f}%", "up"),
                  unsafe_allow_html=True)
    k[3].markdown(T.kpi("trending_down", L("Lagging sector", "القطاع الأضعف"), sector_name(worst), f"{by_sec[worst]:+.2f}%", "down"),
                  unsafe_allow_html=True)

    # ---- breadcrumb + legend
    level = ss.hm2_level if ss.hm2_level in {"root"} | {f"s:{s}" for s in df["Sector"].unique()} \
        | {f"i:{r.Sector}|{r.Industry}" for r in df[["Sector", "Industry"]].drop_duplicates().itertuples()} else "root"
    ss.hm2_level = level
    crumbs = _crumbs(level)
    rng = COLOR_RANGE.get(period, 3)
    bc = st.columns([3, 2])
    with bc[0]:
        cols = st.columns(len(crumbs) + 1)
        for i, (cid, name) in enumerate(crumbs):
            if cols[i].button(name, key=f"hm2_bc_{i}", type="secondary" if i < len(crumbs) - 1 else "primary",
                              disabled=(i == len(crumbs) - 1), icon=":material/chevron_right:" if i else ":material/home:"):
                ss.hm2_level, ss.hm2_last_sel = cid, None
                st.rerun()
    with bc[1]:
        ui.html(f'<div style="display:flex;align-items:center;gap:10px;font-size:.78rem;color:{T.MUTED};direction:ltr;padding-top:10px">'
                f'<span>-{rng}%</span><div style="flex:1;height:10px;border-radius:6px;'
                f'background:linear-gradient(90deg,#F23645,#9B2530,#2A2E39,#0E7A52,#089981)"></div><span>+{rng}%</span>'
                f'<span class="muted">· {L("size = market cap", "الحجم = القيمة السوقية")}</span></div>')

    # ---- treemap with click drill-down
    fig, ids = treemap_figure(df, period, "" if level == "root" else level, "industries" if detail == det_opts[0] else "companies",
                              720, L("US Market", "السوق الأمريكي"))
    try:
        ev = st.plotly_chart(fig, key="hm2_map", on_select="rerun", selection_mode="points", config={"displayModeBar": False})
    except TypeError:                                   # older Streamlit: no chart selections
        st.plotly_chart(fig, config={"displayModeBar": False})
        ev = None
    clicked = _clicked_id(ev, ids) if ev is not None else None
    if clicked is None:
        ss.hm2_last_sel = None
    elif clicked != ss.hm2_last_sel:
        ss.hm2_last_sel = clicked
        if clicked.startswith("t:"):
            sym = clicked[2:]
            sec, ind = U.sector_of(sym), U.industry_of(sym)
            ss.hm2_level, ss.hm2_pick = f"i:{sec}|{ind}", sym
        else:
            ss.hm2_level = clicked
        st.rerun()

    # ---- drop-down navigation (fallback / mobile). Widgets are synced FROM the level; their
    #      on_change callbacks write back TO the level, so the two never fight each other.
    sectors = sorted(df["Sector"].unique())
    cur_sec = level[2:] if level.startswith("s:") else (level[2:].split("|")[0] if level.startswith("i:") else None)
    cur_ind = level[2:].split("|")[1] if level.startswith("i:") else None
    ss.hm2_sec_dd, ss.hm2_ind_dd = cur_sec or ALL, cur_ind or ALL
    inds = sorted(df[df["Sector"] == cur_sec]["Industry"].unique()) if cur_sec else []
    a, b = st.columns(2)
    a.selectbox(L("Sector", "القطاع"), [ALL] + sectors, key="hm2_sec_dd", on_change=_sector_changed,
                format_func=lambda s: L("All sectors", "كل القطاعات") if s == ALL else sector_name(s))
    b.selectbox(L("Industry", "الصناعة"), [ALL] + inds, key="hm2_ind_dd", on_change=_industry_changed, disabled=not cur_sec,
                format_func=lambda i: L("All industries", "كل الصناعات") if i == ALL else industry_name(i))

    # ---- company comparison for the selected sector / industry
    if level == "root":
        st.info(L("Click any sector or industry on the map (or pick one above) to see all of its companies with a full "
                  "financial comparison.", "اضغط على أي قطاع أو صناعة في الخريطة (أو اخترها من القوائم) لعرض كل شركاتها مع مقارنة مالية كاملة."),
                icon=":material/touch_app:")
        return
    view = df[df["Sector"] == cur_sec] if cur_ind is None else df[(df["Sector"] == cur_sec) & (df["Industry"] == cur_ind)]
    title = f"{sector_name(cur_sec)}" + (f" › {industry_name(cur_ind)}" if cur_ind else "")
    compare_section(view, title, period, sub_label=industry_name if cur_ind is None else None,
                    file_name=(cur_ind or cur_sec).replace(" ", "_"))


def compare_section(view, title, period, sub_label=None, ind_label=None, file_name="group", key="hm2", on_close=None):
    """The companies of one group (a sector, an industry, a theme) compared side by side: the industries' leaderboard inside a
    sector (sub_label: the industry's display name, None when the group is one industry), the KPI strip and the tables, a metric
    across the group, valuation against growth, and a way to open a company. view: Symbol, Name, Industry, Chg %, Price, Cap."""
    ind_label = ind_label or industry_name
    head = st.columns([6, 1]) if on_close else [st.container()]
    with head[0]:
        ui.sec("compare_arrows", f"{title}: companies & financial comparison", f"{title}: الشركات والمقارنة المالية")
    if on_close:
        head[1].button(L("Close", "إغلاق"), key=f"{key}_close", icon=":material/close:", on_click=on_close, width="stretch")
    with st.spinner(L(f"Loading financials for {len(view)} companies...", f"جاري تحميل البيانات المالية لـ {len(view)} شركة...")):
        comp = comparison_frame(view, ind_label)
    if comp.empty:
        st.warning(L("No companies found.", "لا توجد شركات."))
        return
    if sub_label is not None and view["Industry"].nunique() > 1:
        # industry leaderboard inside the sector
        w = view.assign(_w=view["Chg %"] * view["Cap"].fillna(0)).groupby("Industry")[["_w", "Cap"]].sum()
        ind_perf = (w["_w"] / w["Cap"].replace(0, np.nan)).dropna().sort_values()
        if len(ind_perf) > 1:
            fig = go.Figure(go.Bar(x=ind_perf.values, y=[sub_label(i) for i in ind_perf.index], orientation="h",
                                   marker=dict(color=[T.UP if v >= 0 else T.DOWN for v in ind_perf.values]),
                                   text=[f"{v:+.2f}%" for v in ind_perf.values], textposition="outside", textfont=dict(size=11),
                                   hovertemplate="<b>%{y}</b>: %{x:+.2f}%<extra></extra>"))
            fig.update_layout(title=dict(text=L(f"Industries in {title} · {period}", f"صناعات {title} · {period}"),
                                         font=dict(size=14), x=0, xanchor="left"), xaxis=dict(ticksuffix="%"), bargap=0.3)
            st.plotly_chart(_layout(fig, max(260, 30 * len(ind_perf) + 90)), config={"displayModeBar": False}, key=f"{key}_inds")
    company_table(comp, with_industry=sub_label is not None, key=key)

    # ---- open a company
    x, y = st.columns([2.5, 1])
    syms = comp["Symbol"].tolist()
    pick = ss.get("hm2_pick") if ss.get("hm2_pick") in syms else syms[0]
    names = comp.set_index("Symbol")["Name"]
    s = x.selectbox(L("Open company", "افتح شركة"), syms, index=syms.index(pick),
                    format_func=lambda t: f"{T.sym_label(t)} · {names.loc[t]}", key=f"{key}_open_sel")
    if y.button(L("Open stock page", "افتح صفحة السهم"), icon=":material/open_in_new:", key=f"{key}_open", type="primary"):
        ui.open_stock(s)
    st.download_button(L("Export comparison (CSV)", "تصدير المقارنة (CSV)"), comp.to_csv(index=False).encode("utf-8-sig"),
                       f"tura_{file_name}.csv", "text/csv", icon=":material/download:", key=f"{key}_csv")

BUILD = "23.4.67"
