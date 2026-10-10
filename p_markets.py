"""
p_markets.py - Overview (TradingView-style heatmap, sector rotation, market breadth) · Futures · Options market ·
Economy · What's Trending · News
"""
import re
import time

import numpy as np
import pandas as pd
import streamlit as st

import charts
import data
import heatmap as HM
import home
import markets as MK
import newsbot
import newsiq
import ta
import tasi
import taxonomy as X
import theme as T
import ui
import universe as U
from i18n import L, industry_name, is_ar, lang, sector_name, theme_name
from sp500 import DOW30, SP500, gics_name

ss = st.session_state


# the Saudi market's overview: its index, the biggest companies, oil, gold and the dollar (the riyal is pegged to the dollar at
# 3.75, and Yahoo's daily USD/SAR candles jump around it: not shown)
SA_TILES = {("Saudi market", "السوق السعودي"): {"^TASI.SR": ("TASI", "تاسي"), "^NOMUC.SR": ("Nomu (parallel market)", "نمو (السوق الموازية)")},
            ("Heavyweights", "الشركات القيادية"): {s: None for s in ("2222.SR", "1120.SR", "1211.SR", "1180.SR", "7010.SR", "2010.SR")},
            ("Commodities", "السلع"): {"BZ=F": ("Brent crude", "خام برنت"), "CL=F": ("WTI crude", "خام غرب تكساس"), "GC=F": ("Gold", "الذهب"),
                                       "NG=F": ("Natural gas", "الغاز الطبيعي")},
            ("Currencies", "العملات"): {"DX-Y.NYB": ("US dollar index", "مؤشر الدولار"), "EURUSD=X": ("EUR / USD", "يورو / دولار"),
                                        "GBPUSD=X": ("GBP / USD", "استرليني / دولار"), "BTC-USD": ("Bitcoin", "بيتكوين")}}
SA_TAPE = ["^TASI.SR", "2222.SR", "1120.SR", "1180.SR", "1211.SR", "7010.SR", "2010.SR", "2082.SR", "1150.SR", "1010.SR", "4013.SR",
           "BZ=F", "GC=F"]


def _sa_name(sym):
    """A tile / tape name in the visitor's language."""
    for g in SA_TILES.values():
        if g.get(sym):
            return L(*g[sym])
    if tasi.known(sym):
        return tasi.name_of(sym, is_ar())
    return {"BZ=F": L("Brent", "برنت"), "GC=F": L("Gold", "الذهب"), "SAR=X": L("USD/SAR", "دولار/ريال")}.get(sym, sym)


# currencies pegged to the dollar: a close far from the peg is a bad print in Yahoo's data (a USD/SAR "+3.2%" day), not a move
PEGS = {"SAR=X": 3.75, "AED=X": 3.6725, "QAR=X": 3.64, "BHD=X": 0.376, "OMR=X": 0.3845}


def _clean_pegs(px):
    out = dict(px)
    for sym, peg in PEGS.items():
        df = out.get(sym)
        if df is not None and len(df) and "Close" in df:
            out[sym] = df[(pd.to_numeric(df["Close"], errors="coerce") / peg - 1).abs() < 0.01]
    return out


def _tile_prices():
    return _clean_pegs(_tile_prices_raw())


def _tile_prices_raw():
    if MK.is_sa():
        syms = [s for g in SA_TILES.values() for s in g]
        px = data.history_many(tuple(syms + SA_TAPE), "1mo")
        return data.with_quotes(px, ["^TASI.SR", "^NOMUC.SR"])      # the indices: Yahoo keeps only their live quote
    syms = [s for g in U.MARKET_TILES.values() for s in g]
    return data.history_many(tuple(syms + list(U.TAPE)), "1mo")


def _last(px, sym):
    df = px.get(sym)
    if df is None or len(df) < 2:
        return None, None, None
    last, prev = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
    pct = (last / prev - 1) * 100
    if str(sym).endswith("=X") and abs(pct) > 4:     # a currency moving 4% in a day is almost always a bad print: no change shown
        return last, None, None
    return last, last - prev, pct


def _chg(df, n):
    """% change over n bars ('ytd' = since the last close of the previous year)."""
    if df is None or df.empty:
        return np.nan
    c = df["Close"].dropna()
    if n == "ytd":
        return data.ytd_change(c)
    return (c.iloc[-1] / c.iloc[-1 - n] - 1) * 100 if len(c) > n else np.nan


def ticker_tape(px):
    if MK.is_sa():
        items = [(_sa_name(s), *_last(px, s)[::2]) for s in SA_TAPE if _last(px, s)[0] is not None]
        if items:
            ui.html(T.tape(items))
        return
    items = [(U.TAPE_NAMES.get(s, s), *_last(px, s)[::2]) for s in U.TAPE if _last(px, s)[0] is not None]
    if items:
        ui.html(T.tape(items))


def _universe_moves(period="5d"):
    uni = data.history_many(tuple(U.US_UNIVERSE), period)
    rows = []
    for s, df in uni.items():
        if len(df) >= 2:
            rows.append({"Symbol": s, "Name": U.name_of(s), "Chg %": float((df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100),
                         "Price": float(df["Close"].iloc[-1]), "Volume": float(df["Volume"].iloc[-1]), "Avg Vol": float(df["Volume"].mean()),
                         "Mkt Cap": U.STOCKS[s][3] * 1e9})
    return pd.DataFrame(rows)


# =====================================================================
# HEATMAP (TradingView style, inside Overview)
# =====================================================================
HM_PERIODS = {"1D": ("Change 1D, %", "التغير يوم، %"), "1W": ("Change 1W, %", "التغير أسبوع، %"), "1M": ("Change 1M, %", "التغير شهر، %"),
              "3M": ("Change 3M, %", "التغير 3 أشهر، %"), "YTD": ("Change YTD, %", "منذ بداية العام، %"), "1Y": ("Change 1Y, %", "التغير سنة، %"),
              "PRE": ("Pre-market, %", "ما قبل الافتتاح، %"), "POST": ("After-hours, %", "ما بعد الإغلاق، %")}
HM_SIZES = {"cap": ("Market cap", "القيمة السوقية"), "dvol": ("Dollar volume", "قيمة التداول"), "equal": ("Equal size", "حجم متساوٍ")}


def hm_universes():
    if MK.is_sa():
        return {"sa_all": (L("All Saudi companies (main market)", "كل الشركات السعودية (السوق الرئيسية)"), list(tasi.SYMBOLS)),
                "sa_top": (L("The 50 biggest companies", "أكبر 50 شركة"), tasi.top(50)),
                "sa_noreit": (L("Without the REITs", "بدون الصناديق العقارية"), [s for s in tasi.SYMBOLS if tasi.group_of(s) != "reits"])}
    u = {"sp500": (L("S&P 500 Index", "مؤشر إس آند بي 500"), list(SP500)),
         "dow": (L("Dow Jones 30", "داو جونز 30"), DOW30),
         "top": (L("Top 175 US stocks", "أكبر 175 سهم أمريكي"), list(U.US_UNIVERSE))}
    for tk, (en, ar, _, _) in X.THEMES.items():
        u[f"t:{tk}"] = (L(f"Theme · {en}", f"ثيم · {ar}"), X.theme_tickers(tk))
    return u


def _meta(sym):
    """(name, sector, industry, industry naming) from the static lists."""
    if tasi.known(sym):
        return tasi.name_of(sym, is_ar()), tasi.sector_of(sym), tasi.industry_of(sym), "tadawul"
    if sym in SP500:
        n, sec, sub = SP500[sym]
        return n, sec, sub, "gics"
    if U.known(sym):
        return U.name_of(sym), U.sector_of(sym), U.industry_of(sym), "yahoo"
    return sym, "Other", "Other", "yahoo"


def heatmap_frame(ukey, period, sizing):
    syms = hm_universes()[ukey][1]
    q, source = data.market_quotes(syms)
    if q.empty:
        return pd.DataFrame(), source
    q = q.drop_duplicates("Symbol").set_index("Symbol")
    rows = []
    for s in syms:
        if s not in q.index:
            continue
        r = q.loc[s]
        name, sec, ind, kind = _meta(s)
        rows.append({"Symbol": s, "Name": name if kind == "tadawul" else r.get("Name") if isinstance(r.get("Name"), str) and r.get("Name") != s else name,
                     "Sector": sec, "Industry": ind, "Kind": kind, "Price": r.get("Price"), "1D": r.get("Chg %"),
                     "1Y": r.get("52W %"), "PRE": r.get("PRE"), "POST": r.get("POST"), "Cap": r.get("Mkt Cap"),
                     "Volume": r.get("Volume")})
    df = pd.DataFrame(rows)
    if df.empty:
        return df, source
    if period in ("1W", "1M", "3M", "YTD") or (period == "1Y" and df["1Y"].isna().all()):
        perf = data.perf_table(df["Symbol"].tolist())
        if not perf.empty:
            df = df.drop(columns=[c for c in ("1W", "1M", "3M", "YTD") if c in df]).merge(
                perf[["Symbol", "1W", "1M", "3M", "YTD"] + (["1Y"] if period == "1Y" else [])].rename(columns={"1Y": "1Y_h"}), on="Symbol", how="left")
            if "1Y_h" in df:
                df["1Y"] = df["1Y"].fillna(df["1Y_h"])
    df["Val"] = pd.to_numeric(df.get(period), errors="coerce") if period in df else np.nan
    live = pd.to_numeric(df["Cap"], errors="coerce")
    if source != "live":                               # the fallback quotes carry the site's own list figures, not live caps
        live = pd.Series(np.nan, index=df.index)
    static = df["Symbol"].map(lambda s: U.STOCKS[s][3] * 1e9 if s in U.STOCKS else tasi.cap_b(s) * 1e9 if tasi.known(s) else np.nan)
    cap = live.fillna(static)
    # where the market cap comes from: live (the quote), approx (the site's list, an older figure), none (unknown: the tile
    # only gets a placeholder size and stays out of the weighted change)
    df["CapSrc"] = np.where(live.notna(), "live", np.where(static.notna(), "approx", "none"))
    if sizing == "cap":
        df["Size"] = cap.fillna(cap.median() if cap.notna().any() else 2e10).fillna(2e10)
    elif sizing == "dvol":
        dv = pd.to_numeric(df["Volume"], errors="coerce") * pd.to_numeric(df["Price"], errors="coerce")
        df["Size"] = dv.fillna(dv.median() if dv.notna().any() else 1.0).clip(lower=1.0)
    else:
        df["Size"] = 1.0
    df["Cap"] = cap                                    # NaN when unknown (never a stand-in figure)
    return df, source


def _sa_sector(s_):
    return tasi.sector_ar(s_) if is_ar() else s_


# short names for the points of the sector rotation chart
SA_SEC_SHORT = {"Energy": ("Energy", "الطاقة"), "Materials": ("Materials", "المواد"), "Industrials": ("Industrials", "الصناعات"),
                "Consumer Discretionary": ("Discretionary", "الكمالية"), "Consumer Staples": ("Staples", "الأساسية"),
                "Health Care": ("Health", "الصحة"), "Financials": ("Financials", "المالي"), "Information Technology": ("Tech", "التقنية"),
                "Communication Services": ("Telecom", "الاتصالات"), "Utilities": ("Utilities", "المرافق"), "Real Estate": ("Real estate", "العقار")}


def _sa_industry(g):
    return tasi.industry_ar(g) if is_ar() else g


def heatmap_section():
    sa = MK.is_sa()
    ui.sec("grid_view", "Stock heatmap", "خريطة الأسهم الحرارية")
    unis = hm_universes()
    c = st.columns([1.35, 1, 1.05, 1.25])
    sfx = "_sa" if sa else ""                              # the Saudi market keeps its own choices
    ukey = c[0].selectbox(L("Index", "المؤشر"), list(unis), key="hm_uni" + sfx, format_func=lambda k: unis[k][0])
    sizes = {k: v for k, v in HM_SIZES.items()} if not sa else {"cap": HM_SIZES["cap"], "dvol": ("Traded value", "قيمة التداول"), "equal": HM_SIZES["equal"]}
    sizing = c[1].selectbox(L("Size", "الحجم"), list(sizes), key="hm_size" + sfx, format_func=lambda k: L(*sizes[k]))
    pers = [k for k in HM_PERIODS if not (sa and k in ("PRE", "POST"))]       # Tadawul has no pre-market / after-hours trading
    period = c[2].selectbox(L("Color", "اللون"), pers, key="hm_per" + sfx, format_func=lambda k: L(*HM_PERIODS[k]))
    theme_uni = ukey.startswith("t:")
    with st.spinner(L("Building the heatmap...", "جاري بناء الخريطة...")):
        df, source = heatmap_frame(ukey, period, sizing)
    if df.empty:
        c[3].selectbox(L("Sector", "القطاع"), ["all"], key="hm_sec_empty", format_func=lambda s: L("All sectors", "كل القطاعات"))
        st.warning(L("Market data is temporarily unavailable.", "بيانات السوق غير متاحة مؤقتاً."))
        return None
    sectors = ["all"] + sorted(df["Sector"].unique(), key=lambda s: -df.loc[df["Sector"] == s, "Cap"].sum())
    if ss.get("hm_sec" + sfx) not in sectors:
        ss["hm_sec" + sfx] = "all"
    sec_label = _sa_sector if sa else sector_name
    sec = c[3].selectbox(L("Sector", "القطاع"), sectors, key="hm_sec" + sfx,
                         format_func=lambda s: L("All sectors", "كل القطاعات") if s == "all" else sec_label(s))
    view = df if sec == "all" else df[df["Sector"] == sec]
    if theme_uni and sec == "all":                         # themes are grouped by sub-theme
        tk = ukey[2:]
        first = {}
        for sk, (_, _, tickers) in X.THEMES[tk][3].items():
            for t_ in tickers:
                first.setdefault(t_, sk)
        view = view.assign(Group=view["Symbol"].map(first))
        label = lambda g: theme_name(tk, g)
    elif sec == "all":
        view = view.assign(Group=view["Sector"])
        label = sec_label
    else:
        view = view.assign(Group=view["Industry"])
        kind_of = view.groupby("Industry")["Kind"].first().to_dict()
        label = (lambda g: _sa_industry(g)) if sa else (lambda g: gics_name(g) if kind_of.get(g) == "gics" else industry_name(g))
    if view["Val"].isna().all():
        st.info(L("This measure isn't available right now (for example pre-market data outside trading hours). Showing today's change.",
                  "هذا المقياس غير متاح حالياً (مثل بيانات ما قبل الافتتاح خارج أوقات التداول). نعرض تغير اليوم."), icon=":material/info:")
        view = view.assign(Val=view["1D"])
        period = "1D"
    rng = HM.RANGE.get(period, 3)
    tiles, groups = HM.layout(view, "Group", "Size")
    big = HM.big_symbols(tiles, 38)
    lg = {s: u for s, u in data.logos(big[:140]).items() if u}
    lg.update(data.known_logos(HM.big_symbols(tiles, 20)))

    def tip(t):
        v = t.get("Val")
        chg = f"{v:+.2f}%" if v is not None and np.isfinite(v) else "—"
        c_, src_ = t.get("Cap"), t.get("CapSrc")
        if c_ is None or not np.isfinite(c_) or src_ == "none":
            capt = L("unknown", "غير متاحة")
        elif src_ == "approx":                             # the site's own list: an older, approximate figure
            capt = "≈" + T.fmt_big(c_) + L(" (approx.)", " (تقديرية)")
        else:
            capt = T.fmt_big(c_)
        return f'{T.sym_label(t["Symbol"])} · {T.name_line(t["Symbol"], t.get("Name", ""))}\n{T.fmt_price(t.get("Price"))} · {chg} · {L("Mkt cap", "القيمة")} {capt}'
    if sa:                                                 # Saudi tiles show the company's name (the code is a number)
        tiles = [dict(t, Label=tasi.name_of(t["Symbol"], is_ar()) or t["Symbol"]) for t in tiles]
    ui.html(HM.render(tiles, groups, lg, rng, lang(), label, tip, rtl=is_ar()))
    ui.html(HM.legend(rng))
    up, dn = int((view["Val"] > 0).sum()), int((view["Val"] < 0).sum())
    # the weighted change: only companies whose weight is known (a placeholder size never weighs on it)
    known = view["Val"].notna() & ((view["CapSrc"] != "none") if sizing == "cap" else True)
    wv = view[known]
    w = np.average(wv["Val"], weights=wv["Size"]) if len(wv) and wv["Size"].sum() > 0 else 0
    n_est = int((view["CapSrc"] != "live").sum()) if sizing == "cap" else 0
    est_en = (f" · {n_est} sizes estimated (no live market cap)" if n_est else "")
    est_ar = (f" · حجم {n_est} شركة تقديري (ما فيه قيمة سوقية مباشرة)" if n_est else "")
    st.caption(L(f"{len(view)} companies · {up} up · {dn} down · weighted change {w:+.2f}% · size = {L(*HM_SIZES[sizing])}{est_en} · "
                 "click any company to open its page" + ("" if source == "live" else " · delayed data"),
                 f"{len(view)} شركة · {up} صاعدة · {dn} نازلة · التغير المرجّح {w:+.2f}% · الحجم = {L(*HM_SIZES[sizing])}{est_ar} · "
                 "اضغط على أي شركة لفتح صفحتها" + ("" if source == "live" else " · بيانات متأخرة")))
    ui.open_picker(view.sort_values("Size", ascending=False)["Symbol"].tolist(), "hm", "Open a company from the map", "افتح شركة من الخريطة")
    return df if ukey in ("sp500", "sa_all") else None


# =====================================================================
# SECTOR PERFORMANCE (cards + rotation graph) · MARKET BREADTH
# =====================================================================
SEC_PERIODS = {"1D": 1, "1W": 5, "1M": 21, "3M": 63, "YTD": "ytd"}


def _rrg(hist, window=12, tail=5, bench="SPY", keys=None, week="W-FRI"):
    """JdK-style Relative Rotation Graph points (weekly, smoothed): RS-Ratio (trend of relative strength) and RS-Momentum."""
    spy = hist.get(bench)
    if spy is None or len(spy) < 120:
        return {}
    sw = spy["Close"].resample(week).last()
    out = {}
    for etf in (keys if keys is not None else U.SECTOR_ETFS):
        df = hist.get(etf)
        if df is None or len(df) < 120:
            continue
        rs = ((df["Close"].resample(week).last() / sw).dropna() * 100).ewm(span=4).mean()
        ratio = 100 + (rs - rs.rolling(window).mean()) / rs.rolling(window).std()
        ratio = ratio.ewm(span=3).mean()
        roc = ratio.diff()
        mom = (100 + (roc - roc.rolling(window).mean()) / roc.rolling(window).std()).ewm(span=3).mean()
        t = pd.DataFrame({"ratio": ratio, "mom": mom}).replace([np.inf, -np.inf], np.nan).dropna().tail(tail)
        if len(t) >= 2:
            out[etf] = t
    return out


def sector_section():
    ui.sec("donut_small", "Sector performance", "أداء القطاعات")
    per = st.segmented_control(L("Period", "الفترة"), list(SEC_PERIODS), default="1D", key="ov_per", label_visibility="collapsed") or "1D"
    hist = data.history_many(tuple(list(U.SECTOR_ETFS) + ["SPY"]), "2y")
    if not hist:
        st.info(L("Sector data unavailable right now.", "بيانات القطاعات غير متاحة حالياً."))
        return
    rows = []
    for etf, name in U.SECTOR_ETFS.items():
        df = hist.get(etf)
        if df is None or len(df) < 25:
            continue
        rows.append((name, etf, _chg(df, SEC_PERIODS[per]), _chg(df, 5), _chg(df, 21), df["Close"].tail(22).values))
    if not rows:
        st.info(L("Sector data unavailable right now.", "بيانات القطاعات غير متاحة حالياً."))
        return
    rows.sort(key=lambda r: -(r[2] if pd.notna(r[2]) else -1e9))
    left, right = st.columns([1, 1.15])
    with left:
        spy = _chg(hist.get("SPY"), SEC_PERIODS[per])
        best, worst = rows[0], rows[-1]
        ui.html(f'<div class="card" style="padding:12px 14px"><div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">'
                f'{T.badge(L("Leader", "الأقوى") + ": " + sector_name(best[0]), "up", "north_east")}'
                f'{T.badge(L("Laggard", "الأضعف") + ": " + sector_name(worst[0]), "down", "south_east")}'
                f'<span class="muted" style="font-size:.8rem">S&amp;P 500 {per}</span>{T.pill(spy)}</div></div>')
        ui.html('<div class="secgrid">' + "".join(T.sector_card(sector_name(n), e, v, w, m, sp) for n, e, v, w, m, sp in rows) + "</div>")
    with right:
        tails = _rrg(hist)
        if tails:
            ui.chart(charts.sector_rrg(tails, {e: sector_name(n) for e, n in U.SECTOR_ETFS.items()},
                                       L("Sector rotation vs S&P 500 (weekly, last 5 weeks)", "دوران القطاعات مقابل إس آند بي 500 (أسبوعي، آخر 5 أسابيع)"),
                                       (L("Leading", "قيادي"), L("Weakening", "يضعف"), L("Lagging", "متأخر"), L("Improving", "يتحسن"))))
            st.caption(L("Right = stronger than the market, top = gaining momentum. Sectors usually rotate clockwise: Improving → Leading → Weakening → Lagging.",
                         "اليمين = أقوى من السوق، والأعلى = زخم متزايد. القطاعات تدور عادة مع عقارب الساعة: يتحسن ← قيادي ← يضعف ← متأخر."))


@st.cache_data(ttl=1800, show_spinner=False)
def _sa_sector_frames(ar):
    """{sector: DataFrame(Close)} equal-weighted indices of the Saudi sectors (2 years), plus "MKT": the whole market the same way
    (the TASI index itself when Yahoo has its history)."""
    hist = data.history_many(tuple(tasi.SYMBOLS) + ("^TASI.SR",), "2y")
    closes = pd.DataFrame({s_: df["Close"] for s_, df in hist.items() if tasi.known(s_) and len(df) > 60}).sort_index()
    if closes.empty:
        return {}
    rets = closes.pct_change(fill_method=None).clip(-0.4, 0.4)

    def ix(cols):
        r = rets[cols].mean(axis=1, skipna=True).fillna(0.0)
        return pd.DataFrame({"Close": (1 + r).cumprod() * 100})
    out = {sec: ix([c for c in closes if tasi.sector_of(c) == sec]) for sec in tasi.SECTORS if any(tasi.sector_of(c) == sec for c in closes)}
    tx = hist.get("^TASI.SR")
    out["MKT"] = tx[["Close"]] if tx is not None and len(tx) >= 200 else ix(list(closes))
    out["_tasi"] = tx is not None and len(tx) >= 200
    return out


def sector_section_sa():
    ui.sec("donut_small", "Sector performance", "أداء القطاعات")
    per = st.segmented_control(L("Period", "الفترة"), list(SEC_PERIODS), default="1D", key="ov_per_sa", label_visibility="collapsed") or "1D"
    fr = _sa_sector_frames(is_ar())
    rows = [(sec, "", _chg(df, SEC_PERIODS[per]), _chg(df, 5), _chg(df, 21), df["Close"].tail(22).values)
            for sec, df in fr.items() if sec not in ("MKT", "_tasi")]
    if not rows:
        st.info(L("Sector data unavailable right now.", "بيانات القطاعات غير متاحة حالياً."))
        return
    rows.sort(key=lambda r: -(r[2] if pd.notna(r[2]) else -1e9))
    left, right = st.columns([1, 1.15])
    mkt_name = L("TASI", "تاسي") if fr.get("_tasi") else L("Market", "السوق")
    with left:
        mk = _chg(fr["MKT"], SEC_PERIODS[per])
        best, worst = rows[0], rows[-1]
        ui.html(f'<div class="card" style="padding:12px 14px"><div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">'
                f'{T.badge(L("Leader", "الأقوى") + ": " + _sa_sector(best[0]), "up", "north_east")}'
                f'{T.badge(L("Laggard", "الأضعف") + ": " + _sa_sector(worst[0]), "down", "south_east")}'
                f'<span class="muted" style="font-size:.8rem">{T.esc(mkt_name)} {per}</span>{T.pill(mk)}</div></div>')
        ui.html('<div class="secgrid">' + "".join(T.sector_card(_sa_sector(n), "", v, w, m, sp) for n, e, v, w, m, sp in rows) + "</div>")
        st.caption(L("Each sector is the average move of its companies (equal weights).", "كل قطاع = متوسط حركة شركاته (بأوزان متساوية)."))
    with right:
        keys = [r[0] for r in rows]
        tails = _rrg(fr, bench="MKT", keys=keys, week="W-THU")
        if tails:
            ui.chart(charts.sector_rrg(tails, {k: _sa_sector(k) for k in keys},
                                       L(f"Sector rotation vs {mkt_name} (weekly, last 5 weeks)", f"دوران القطاعات مقابل {mkt_name} (أسبوعي، آخر 5 أسابيع)"),
                                       (L("Leading", "قيادي"), L("Weakening", "يضعف"), L("Lagging", "متأخر"), L("Improving", "يتحسن")),
                                       tags={k: L(*SA_SEC_SHORT.get(k, (k, _sa_sector(k)))) for k in keys}))
            st.caption(L("Right = stronger than the market, top = gaining momentum. Sectors usually rotate clockwise: Improving → Leading → Weakening → Lagging.",
                         "اليمين = أقوى من السوق، والأعلى = زخم متزايد. القطاعات تدور عادة مع عقارب الساعة: يتحسن ← قيادي ← يضعف ← متأخر."))


def breadth_section(sp=None):
    sa = MK.is_sa()
    uni = list(tasi.SYMBOLS) if sa else list(SP500)
    if sa:
        ui.sec("monitor_heart", "Market breadth · Saudi main market", "اتساع السوق · السوق السعودية الرئيسية")
    else:
        ui.sec("monitor_heart", "Market breadth · S&P 500", "اتساع السوق · إس آند بي 500")
    if sp is None:
        q, _ = data.market_quotes(uni)
        sp = q.rename(columns={"Chg %": "1D"}) if not q.empty else q
        if not sp.empty:
            sp["Sector"] = sp["Symbol"].map(tasi.sector_of if sa else (lambda s: SP500.get(s, ("", "Other", ""))[1]))
    if sp is None or sp.empty:
        st.info(L("Breadth data unavailable right now.", "بيانات اتساع السوق غير متاحة حالياً."))
        return
    q = data.quotes_df(uni) if "vs50 %" not in sp else sp
    chg = pd.to_numeric(sp["1D"], errors="coerce").dropna()
    adv, dec = int((chg > 0).sum()), int((chg < 0).sum())
    unch = len(chg) - adv - dec
    pct = adv / max(len(chg), 1) * 100
    a, b, c = st.columns([1, 1.1, 1.2])
    with a:
        mood = L("Bullish breadth", "اتساع إيجابي") if pct > 55 else (L("Bearish breadth", "اتساع سلبي") if pct < 45 else L("Mixed", "متوازن"))
        ui.html(f'<div class="card">{T.pulse_gauge(pct, L("advancing", "صاعدة"), mood)}'
                f'<div style="margin-top:8px">{T.ad_bar(adv, dec, unch)}</div>'
                f'<div style="display:flex;justify-content:space-between;margin-top:8px;font-size:.8rem;font-weight:600;direction:ltr">'
                f'<span class="pill pos" style="min-width:0">▲ {adv}</span><span class="pill neu" style="min-width:0">= {unch}</span>'
                f'<span class="pill neg" style="min-width:0">▼ {dec}</span></div></div>')
    with b:
        items = []
        if not q.empty and "vs50 %" in q:
            v50, v200 = pd.to_numeric(q["vs50 %"], errors="coerce").dropna(), pd.to_numeric(q["vs200 %"], errors="coerce").dropna()
            hi, lo = pd.to_numeric(q["Hi52 %"], errors="coerce").dropna(), pd.to_numeric(q["Lo52 %"], errors="coerce").dropna()
            for lab, s_, col in ((L("Above 50-day average", "فوق متوسط 50 يوم"), v50 > 0, T.ACCENT),
                                 (L("Above 200-day average", "فوق متوسط 200 يوم"), v200 > 0, T.VIOLET)):
                if len(s_):
                    p_ = s_.mean() * 100
                    items.append((lab, f"{p_:.0f}%", p_, T.UP if p_ >= 50 else T.DOWN))
            if len(hi):
                nh, nl = int((hi >= -2).sum()), int((lo <= 2).sum())
                items.append((L("Near 52-week high", "قرب القمة السنوية"), str(nh), nh / len(hi) * 100 * 4, T.UP))
                items.append((L("Near 52-week low", "قرب القاع السنوي"), str(nl), nl / len(lo) * 100 * 4, T.DOWN))
        ui.html(f'<div class="card"><div class="muted" style="font-size:.75rem;font-weight:600;letter-spacing:.08em">'
                f'{L("PARTICIPATION", "المشاركة")}</div>{T.progress_bars(items) if items else ""}</div>')
    with c:
        if "Sector" in sp:
            g = sp.assign(up=pd.to_numeric(sp["1D"], errors="coerce") > 0).groupby("Sector")["up"].mean().sort_values(ascending=False) * 100
            ui.html(f'<div class="card"><div class="muted" style="font-size:.75rem;font-weight:600;letter-spacing:.08em">'
                    f'{L("ADVANCING BY SECTOR", "الصاعدة حسب القطاع")}</div>' +
                    T.progress_bars([((_sa_sector if sa else sector_name)(s_), f"{v:.0f}%", v, T.UP if v >= 50 else T.DOWN) for s_, v in g.items()]) + "</div>")
    ui.chart(charts.change_distribution(chg, L("Distribution of today's moves (Saudi main market)", "توزيع حركة الأسهم اليوم (السوق السعودية)") if sa else
                                        L("Distribution of today's moves (S&P 500)", "توزيع حركة الأسهم اليوم (إس آند بي 500)"),
                                        L("Change %", "التغير %"), L("Stocks", "عدد الأسهم")))


# =====================================================================
# OVERVIEW
# =====================================================================
def page_overview_sa():
    """The Saudi market's overview: TASI, the biggest companies, oil, gold and the riyal; the heat map, the sectors and breadth
    of the main market."""
    px = _tile_prices()
    ticker_tape(px)
    chips = ""
    for s_ in ("^TASI.SR", "2222.SR", "1120.SR", "BZ=F", "GC=F", "DX-Y.NYB"):
        p, _, c = _last(px, s_)
        if p is not None:
            chips += f'<span class="chip"><b>{T.esc(_sa_name(s_))}</b>{T.fmt_price(p)} {T.pill(c)}</span>'
    home.hero(chips)
    ui.header("monitoring", "Saudi Market Overview", "نظرة عامة على السوق السعودي",
              "Live snapshot of the Saudi Exchange (Tadawul): TASI, the biggest companies, sectors, oil, gold and the dollar. Prices in SAR.",
              "لمحة مباشرة عن السوق السعودية (تداول): مؤشر تاسي، وأكبر الشركات، والقطاعات، والنفط، والذهب، والدولار. الأسعار بالريال.")
    icons = {"Saudi market": "show_chart", "Heavyweights": "domain", "Commodities": "oil_barrel", "Currencies": "currency_exchange"}
    for (gen, gar), syms in SA_TILES.items():
        ui.sec(icons.get(gen, "insights"), gen, gar)
        items = []
        for sym in syms:
            p, chg, pct = _last(px, sym)
            name = _sa_name(sym)
            if p is None:
                items.append(T.tile(name, "—"))
                continue
            items.append(T.tile(name, T.fmt_price(p), chg, pct, px[sym]["Close"].tail(22).values))
        ui.html(T.tiles(items))
    sp = ui.safe(heatmap_section)
    ui.safe(sector_section_sa)
    ui.safe(breadth_section, sp)
    st.caption(L("Prices from Yahoo Finance (may be delayed). The Saudi market trades Sunday to Thursday, 10 am to 3 pm Riyadh time.",
                 "الأسعار من Yahoo Finance (قد تكون متأخرة). السوق السعودي يتداول من الأحد للخميس، من 10 الصبح لين 3 العصر بتوقيت الرياض."))
    ui.foot()


def page_overview():
    if home.intro():                 # the interactive landing comes first (once per visit), then the home page
        return
    if MK.is_sa():
        page_overview_sa()
        return
    px = _tile_prices()
    ticker_tape(px)
    chips = ""
    for s, name in (("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ"), ("^DJI", "DOW"), ("^TNX", "US10Y"), ("GC=F", "GOLD"), ("BTC-USD", "BTC")):
        p, _, c = _last(px, s)
        if p is not None:
            chips += f'<span class="chip"><b>{name}</b>{f"{p:.2f}%" if s == "^TNX" else T.fmt_price(p)} {T.pill(c)}</span>'
    home.hero(chips)
    ui.header("monitoring", "Market Overview", "نظرة عامة على السوق",
              "Live snapshot of US stocks, futures, rates, commodities, currencies and crypto.",
              "لمحة مباشرة عن الأسهم والعقود والسندات والسلع والعملات والعملات الرقمية.")
    icons = {"Indices": "show_chart", "Futures": "update", "Treasury Yields": "account_balance", "Commodities": "oil_barrel",
             "Currencies": "currency_exchange", "Crypto": "currency_bitcoin"}
    for (gen, gar), syms in U.MARKET_TILES.items():
        ui.sec(icons.get(gen, "insights"), gen, gar)
        items = []
        for sym, (nen, nar) in syms.items():
            p, chg, pct = _last(px, sym)
            if p is None:
                items.append(T.tile(L(nen, nar), "—"))
                continue
            val = f"{p:.3f}%" if gen == "Treasury Yields" else T.fmt_price(p)
            items.append(T.tile(L(nen, nar), val, chg, pct, px[sym]["Close"].tail(22).values, invert=(sym == "^VIX")))
        ui.html(T.tiles(items))
    # key economic indicators sit right after crypto; the slot is filled last, so the heatmap and charts below never wait for economic data
    econ_slot = st.container()
    sp = ui.safe(heatmap_section)
    ui.safe(sector_section)
    ui.safe(breadth_section, sp)
    a, b, c = st.columns(3)
    if a.button(L("Futures market", "سوق العقود الآجلة"), icon=":material/update:", width="stretch"):
        ui.goto("futures")
    if b.button(L("Options market", "سوق الخيارات"), icon=":material/tune:", width="stretch"):
        ui.goto("options")
    if c.button(L("Economy dashboard", "لوحة الاقتصاد"), icon=":material/account_balance:", width="stretch"):
        ui.goto("economy")
    with econ_slot:
        ui.safe(indicators_section, True)
    ui.foot()


# =====================================================================
# FUTURES
# =====================================================================
FU_PERIODS = {"1D": 1, "1W": 5, "1M": 21, "3M": 63, "YTD": "ytd", "1Y": 251}


def _perf_matrix(rows, hdr):
    head = "".join(f"<th>{h}</th>" for h in hdr)
    body = []
    for name, sym, price, vals in rows:
        cells = "".join(f'<td><span class="cp {T.cls(v)}">{v:+.2f}%</span></td>' if pd.notna(v) else "<td>—</td>" for v in vals)
        body.append(f'<tr><td style="text-align:left"><b>{T.esc(name)}</b> <span class="muted">{T.esc(sym)}</span></td>'
                    f'<td>{T.fmt_price(price)}</td>{cells}</tr>')
    return (f'<div class="chainwrap" style="max-height:none"><table class="chain"><thead><tr><th style="text-align:left">{L("Contract", "العقد")}</th>'
            f'<th>{L("Last", "آخر سعر")}</th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')


def page_futures():
    ui.header("update", "Futures", "العقود الآجلة",
              "US futures on stock indices, energy, metals, agriculture, interest rates, currencies and crypto.",
              "العقود الآجلة الأمريكية على مؤشرات الأسهم والطاقة والمعادن والزراعة والفائدة والعملات والعملات الرقمية.")
    syms = list(U.FUTURES_NAMES)
    with st.spinner(L("Loading futures...", "جاري تحميل العقود...")):
        hist = data.history_many(tuple(syms), "1y")
    if not hist:
        st.warning(L("Futures data is temporarily unavailable.", "بيانات العقود غير متاحة مؤقتاً."))
        return
    groups = {g[0]: g for g in U.FUTURES}
    pick = st.segmented_control(L("Market", "السوق"), ["all"] + list(groups), default="all", key="fu_grp",
                                format_func=lambda k: L("All markets", "كل الأسواق") if k == "all" else L(groups[k][0], groups[k][1])) or "all"
    for (gen, gar, ic), items in U.FUTURES.items():
        if pick not in ("all", gen):
            continue
        ui.sec(ic, gen, gar)
        tl = []
        for sym, (en, ar) in items.items():
            df = hist.get(sym)
            if df is None or len(df) < 2:
                tl.append(T.tile(L(en, ar), "—", sub=sym))
                continue
            p, pr = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
            tl.append(T.tile(L(en, ar), T.fmt_price(p), p - pr, (p / pr - 1) * 100, df["Close"].tail(22).values, sub=sym))
        ui.html(T.tiles(tl))

    ui.sec("table_chart", "Performance matrix", "مصفوفة الأداء")
    rows = []
    for (gen, gar, ic), items in U.FUTURES.items():
        if pick not in ("all", gen):
            continue
        for sym, (en, ar) in items.items():
            df = hist.get(sym)
            if df is not None and len(df) > 1:
                rows.append((L(en, ar), sym, float(df["Close"].iloc[-1]), [_chg(df, n) for n in FU_PERIODS.values()]))
    ui.html(_perf_matrix(rows, list(FU_PERIODS)))

    ui.sec("candlestick_chart", "Contract chart", "رسم العقد")
    avail = [s for s in syms if s in hist and (pick == "all" or s in U.FUTURES[groups[pick]])]
    if not avail:
        ui.foot()
        return
    ui.valid("fu_sym", avail)
    c1, c2 = st.columns([2, 1])
    sym = c1.selectbox(L("Contract", "العقد"), avail, key="fu_sym", format_func=lambda s: f"{L(*U.FUTURES_NAMES[s])} · {s}")
    rng = c2.segmented_control(L("Range", "المدى"), ["3M", "6M", "1Y"], default="6M", key="fu_rng") or "6M"
    d = ta.add_all(hist[sym]).tail({"3M": 63, "6M": 126, "1Y": 252}[rng])
    if len(d) > 2:
        ui.chart(charts.price_chart(d, "Candles", ["SMA 20", "SMA 50"], ["RSI"], height=560))
    grp = next((g for g in U.FUTURES if sym in U.FUTURES[g]), None)
    if grp:
        ui.chart(charts.norm_lines({L(*U.FUTURES_NAMES[s]): hist[s]["Close"].tail(63) for s in U.FUTURES[grp] if s in hist},
                                   L(f"{grp[0]}: relative performance (3 months)", f"{grp[1]}: الأداء النسبي (3 أشهر)")))
    st.caption(L("Continuous front-month contracts. Futures trade almost 24 hours on weekdays; prices may be delayed.",
                 "عقود الشهر الأقرب المستمرة. العقود الآجلة تتداول تقريباً 24 ساعة في أيام الأسبوع، والأسعار قد تكون متأخرة."))
    ui.foot()


# =====================================================================
# OPTIONS MARKET
# =====================================================================
def page_options():
    ui.header("tune", "Options Market", "سوق الخيارات",
              "Volatility, put/call sentiment, expected moves and unusual activity across the most traded US options.",
              "التذبذب ومعنويات PUT/CALL والحركة المتوقعة والنشاط غير المعتاد في أكثر عقود الخيارات تداولاً.")
    vix = data.history_many(tuple(U.VIX_CURVE), "1mo")
    pts = [(L(*U.VIX_CURVE[s]), float(vix[s]["Close"].iloc[-1])) for s in U.VIX_CURVE if s in vix and len(vix[s])]
    c1, c2 = st.columns([1.4, 1])
    with c1:
        if len(pts) >= 2:
            ui.chart(charts.term_structure([p[0] for p in pts], [p[1] for p in pts], L("VIX term structure", "منحنى مؤشر الخوف VIX")))
        else:
            st.caption(L("VIX curve unavailable right now.", "منحنى VIX غير متاح حالياً."))
    with c2:
        v = vix.get("^VIX")
        if v is not None and len(v) > 1:
            lv, pv = float(v["Close"].iloc[-1]), float(v["Close"].iloc[-2])
            calm = lv < 20
            contango = len(pts) >= 2 and pts[-1][1] > pts[0][1]
            k = st.columns(2)
            k[0].markdown(T.kpi("speed", L("VIX (fear index)", "مؤشر الخوف VIX"), f"{lv:.2f}", f"{(lv / pv - 1) * 100:+.2f}%",
                                "pos" if calm else "neg"), unsafe_allow_html=True)
            k[1].markdown(T.kpi("stacked_line_chart", L("Curve", "شكل المنحنى"),
                                L("Contango", "كونتانغو") if contango else L("Backwardation", "باكورديشن"),
                                L("calm market", "سوق هادئ") if contango else L("stress / hedging", "توتر وتحوّط"),
                                "pos" if contango else "neg"), unsafe_allow_html=True)
            ui.html(f'<div class="card" style="margin-top:10px;font-size:.86rem;line-height:1.8">{L("VIX below 20 usually means a calm market; above 30 means fear. When short-term VIX is above long-term (backwardation), traders are paying up for protection now.", "مؤشر VIX تحت 20 يعني غالباً سوق هادئ، وفوق 30 يعني خوف. إذا كان VIX القصير أعلى من الطويل (باكورديشن) فالمتداولون يدفعون أكثر للحماية الآن.")}</div>')

    with st.spinner(L("Loading option chains...", "جاري تحميل سلاسل الخيارات...")):
        snaps = data.options_snapshot(U.OPTION_UNDERLYINGS)
    if not snaps:
        st.warning(L("Options data is temporarily unavailable.", "بيانات الخيارات غير متاحة مؤقتاً."))
    else:
        ui.sec("insights", "Most traded underlyings · nearest expiry", "الأصول الأكثر تداولاً · أقرب انتهاء")
        lg = data.logos([s["symbol"] for s in snaps])
        cards = []
        for s in snaps:
            pc = s["pc_vol"]
            kind = "pos" if pc < 0.7 else ("neg" if pc > 1 else "neu")
            senti = L("bullish", "إيجابي") if kind == "pos" else (L("bearish", "سلبي") if kind == "neg" else L("neutral", "محايد"))
            cards.append(f'<div class="lc"><div class="top">{T.company(s["symbol"], s["expiry"], lg.get(s["symbol"]), 34, href=ui.href(s["symbol"]))}'
                         f'<span class="pill {kind}" style="min-width:0">P/C {pc:.2f}</span></div>'
                         f'<div class="bot"><div><div class="muted" style="font-size:.7rem">{L("Price", "السعر")}</div><b>{T.fmt_price(s["price"])}</b></div>'
                         f'<div><div class="muted" style="font-size:.7rem">{L("ATM IV", "التذبذب")}</div><b>{s["iv"]:.1f}%</b></div>'
                         f'<div><div class="muted" style="font-size:.7rem">{L("Exp. move", "الحركة المتوقعة")}</div><b>±{s["move_pct"]:.1f}%</b></div></div>'
                         f'<div class="muted" style="font-size:.72rem;margin-top:8px">{L("Sentiment", "المعنويات")}: {senti} · '
                         f'{T.fmt_big(s["call_vol"] + s["put_vol"])} {L("contracts", "عقد")} · {s["dte"]}{L("d", " يوم")}</div></div>')
        ui.html('<div class="lead">' + "".join(cards) + "</div>")
        a, b = st.columns(2)
        with a:
            ui.chart(charts.pc_bars([s["symbol"] for s in snaps], [s["pc_vol"] for s in snaps],
                                    L("Put/Call volume ratio (green < 0.7 bullish, red > 1 bearish)", "نسبة PUT/CALL (أخضر < 0.7 إيجابي، أحمر > 1 سلبي)")))
        with b:
            ui.chart(charts.metric_bars([s["symbol"] for s in snaps], [s["iv"] for s in snaps],
                                        L("At-the-money implied volatility", "التذبذب الضمني عند سعر السوق"), "pct", 300))
        ui.sec("local_fire_department", "Unusual options activity", "نشاط الخيارات غير المعتاد")
        un = pd.DataFrame([u for s in snaps for u in s["unusual"]])
        if un.empty:
            st.caption(L("No unusual activity (volume above open interest) right now.", "لا يوجد نشاط غير معتاد حالياً (حجم أعلى من العقود المفتوحة)."))
        else:
            un["Vol/OI"] = un["Volume"] / un["OI"].replace(0, np.nan)
            un = un.sort_values(["Vol/OI", "Volume"], ascending=False).head(25)
            un.insert(0, "Logo", un["Symbol"].map(data.logo_url))
            N = {"Symbol": L("Symbol", "الرمز"), "Type": L("Type", "النوع"), "Strike": L("Strike", "التنفيذ"), "Expiry": L("Expiry", "الانتهاء"),
                 "Volume": L("Volume", "الحجم"), "OI": L("Open int.", "العقود المفتوحة"), "Last": L("Last", "آخر سعر"), "IV %": "IV %", "Vol/OI": "Vol/OI"}
            show = un.rename(columns=N)
            ui.table(show, sym=N["Symbol"], words={N["Type"]: ("CALL", "PUT")}, height=460,
                     fmt={N["Strike"]: "{:,.2f}", N["Volume"]: "{:,.0f}", N["OI"]: "{:,.0f}", N["Last"]: "{:,.2f}", "IV %": "{:.1f}%", "Vol/OI": "{:.1f}×"})
            st.caption(L("Unusual = contracts trading more today than their total open interest (at least 500 contracts): often new positions.",
                         "غير معتاد = عقود تداولها اليوم أكبر من إجمالي العقود المفتوحة (500 عقد على الأقل): غالباً مراكز جديدة."))
    ui.sec("table_rows", "Option chain explorer", "مستعرض سلسلة الخيارات")
    import p_research
    sym = st.selectbox(L("Underlying", "الأصل"), U.OPTION_UNDERLYINGS + ["Other"], key="om_sym",
                       format_func=lambda s: L("Other symbol...", "رمز آخر...") if s == "Other" else s)
    if sym == "Other":
        sym = st.text_input(L("Symbol", "الرمز"), "SMCI", key="om_other").strip().upper() or "SPY"
    d = data.history(sym, "1mo")
    if d.empty:
        st.warning(L("No data for this symbol.", "لا توجد بيانات لهذا الرمز."))
    else:
        p_research.options_tab(sym, float(d["Close"].iloc[-1]))
    ui.foot()


# =====================================================================
# ECONOMY
# =====================================================================
RATE_NAMES = {0.25: ("3-month T-bill", "أذونات 3 أشهر"), 2.0: ("2-year Treasury", "سندات سنتين"), 5.0: ("5-year Treasury", "سندات 5 سنوات"),
              10.0: ("10-year Treasury", "سندات 10 سنوات"), 30.0: ("30-year Treasury", "سندات 30 سنة")}


def indicators_section(compact=False):
    if compact:
        ui.sec("query_stats", "Key economic indicators", "أهم المؤشرات الاقتصادية")
    else:
        ui.sec("query_stats", "Key indicators", "أهم المؤشرات")
    with st.spinner(L("Loading economic data...", "جاري تحميل البيانات الاقتصادية...")):
        mac, errors, status = data.macro()
    if mac:
        items = []
        for sid, m in mac.items():
            chg = m["value"] - m["prev"]
            unit = m["unit"]
            val = f"{m['value']:,.2f}{unit}" if unit == "%" else f"{m['value']:,.1f}{unit}"
            sub = L(f"{m['date']:%b %Y} · prior {m['prev']:,.2f} · {m['source']}", f"{m['date']:%Y-%m} · السابق {m['prev']:,.2f} · {m['source']}")
            neutral = m["higher_is_bad"] is None
            items.append(T.tile(L(m["en"], m["ar"]), val, chg, None, m["hist"].values, sub, invert=bool(m["higher_is_bad"]),
                                kind="acc" if neutral else None))
        ui.html(T.tiles(items))
        st.caption(L("Green = better than the previous reading, red = worse (for inflation and unemployment, a rise counts as worse).",
                     "الأخضر = أفضل من القراءة السابقة، والأحمر = أسوأ (للتضخم والبطالة: الارتفاع يعتبر أسوأ)."))
        names = {L(m["en"], m["ar"]): sid for sid, m in mac.items()}
        if compact:
            ui.valid("ov_ind_pick", list(names))
        pick = st.selectbox(L("Explore an indicator", "استعرض مؤشراً"), list(names), key="ov_ind_pick" if compact else None)
        ui.chart(charts.line(mac[names[pick]]["hist"], pick, height=320, fill=True), key="ov_ind" if compact else "ec_ind")
        if compact:
            st.page_link(ui.PAGES["economy"], label=L("Open the economy page: interest rates, the yield curve and the calendar",
                                                      "افتح صفحة الاقتصاد: أسعار الفائدة ومنحنى العائد والتقويم"), icon=":material/arrow_forward:")
    else:
        st.warning(L("Indicator sources (FRED and BLS) could not be reached from the server right now. "
                     "For a permanent fix add a free FRED API key in Streamlit secrets as FRED_API_KEY.",
                     "تعذر الوصول لمصادر المؤشرات (FRED وBLS) من الخادم حالياً. "
                     "للحل الدائم أضف مفتاح FRED المجاني في إعدادات Streamlit باسم FRED_API_KEY."), icon=":material/cloud_off:")
    return errors, status


def rates_section():
    ui.sec("percent", "Interest rates", "أسعار الفائدة")
    with st.spinner(L("Loading interest rates...", "جاري تحميل أسعار الفائدة...")):
        fed, fsrc = data.fed_funds()
        curve, csrc = data.yield_curve()
    items = []
    if not fed.empty:
        last = fed.iloc[-1]
        lo, hi = last.get("targetRateFrom", np.nan), last.get("targetRateTo", np.nan)
        eff = fed["percentRate"].dropna()
        if pd.notna(lo) and pd.notna(hi):
            items.append(T.tile(L("Fed funds target range", "النطاق المستهدف لفائدة الفيدرالي"), f"{lo:.2f}–{hi:.2f}%", kind="acc",
                                chg_text=L("Federal Reserve policy rate", "سعر الفائدة الرسمي للفيدرالي"), sub=f"{fed.index[-1]:%Y-%m-%d}"))
        if len(eff):
            ago = eff[eff.index <= eff.index[-1] - pd.Timedelta(days=90)]
            d = (eff.iloc[-1] - ago.iloc[-1]) * 100 if len(ago) else None
            items.append(T.tile(L("Effective fed funds (EFFR)", "الفائدة الفعلية (EFFR)"), f"{eff.iloc[-1]:.2f}%", d, None, eff.tail(250).values,
                                L("vs 3 months ago", "مقارنة بقبل 3 أشهر"), chg_text=f"{d:+.0f} bps" if d is not None else ""))
    sp, lab = None, ""
    if not curve.empty:
        last_row = curve.iloc[-1]
        prev_row = curve.iloc[-2] if len(curve) > 1 else last_row
        for m, (en, ar) in RATE_NAMES.items():
            if m not in curve.columns or pd.isna(last_row[m]):
                continue
            v, pv = float(last_row[m]), prev_row[m]
            bps = (v - pv) * 100 if pd.notna(pv) else None
            items.append(T.tile(L(en, ar), f"{v:.2f}%", bps, None, curve[m].dropna().tail(66).values, L("change today", "تغير اليوم"),
                                chg_text=f"{bps:+.0f} bps" if bps is not None else ""))
        short = 2.0 if 2.0 in curve.columns else (0.25 if 0.25 in curve.columns else None)
        if 10.0 in curve.columns and short is not None:
            sp = (curve[10.0] - curve[short]).dropna()
            lab = f"10Y − {data.maturity_label(short)}"
            if len(sp):
                v = float(sp.iloc[-1]) * 100
                items.append(T.tile(L(f"Yield spread {lab}", f"فرق العائد {lab}"), f"{v:+.0f} bps", v, None, sp.tail(250).values,
                                    L("normal curve", "منحنى طبيعي") if v >= 0 else L("inverted curve: a classic recession warning", "منحنى مقلوب: إشارة ركود تقليدية"),
                                    chg_text=L("positive = normal", "موجب = طبيعي") if v >= 0 else L("negative = inverted", "سالب = مقلوب")))
    if not items:
        st.warning(L("Interest-rate sources are not reachable from the server right now.", "مصادر أسعار الفائدة غير متاحة من الخادم حالياً."),
                   icon=":material/cloud_off:")
        return
    ui.html(T.tiles(items))
    if not curve.empty:
        c1, c2 = st.columns(2)
        labels = lambda r: [data.maturity_label(m) for m in r.index]

        def near(days):
            sub = curve[curve.index <= curve.index[-1] - pd.Timedelta(days=days)]
            return sub.iloc[-1].dropna() if len(sub) else None
        today = curve.iloc[-1].dropna()
        curves = [(L("Today", "اليوم") + f" · {curve.index[-1]:%b %d}", labels(today), today.values, T.CYAN, "solid")]
        for days, (en, ar), col, dash in ((30, ("1 month ago", "قبل شهر"), T.VIOLET, "dot"), (365, ("1 year ago", "قبل سنة"), T.GOLD, "dash")):
            r = near(days)
            if r is not None and len(r):
                curves.append((L(en, ar), labels(r), r.values, col, dash))
        with c1:
            ui.chart(charts.yield_curves(curves, L("Treasury yield curve", "منحنى عائد السندات الأمريكية")), key="ec_curve")
        with c2:
            if sp is not None and len(sp):
                ui.chart(charts.spread_area(sp, L(f"Yield spread {lab} (below zero = inverted)", f"فرق العائد {lab} (تحت الصفر = مقلوب)"), lab), key="ec_spread")
    if not fed.empty and len(fed) > 5:
        ui.chart(charts.fed_path(fed, L("Federal Reserve: target range and effective rate", "الفيدرالي: النطاق المستهدف والفائدة الفعلية"),
                                 (L("Fed target range", "النطاق المستهدف"), L("Effective fed funds rate", "الفائدة الفعلية"))), key="ec_fed")
    src = " · ".join(x for x in (fsrc, csrc) if x)
    st.caption(L(f"Sources: {src}. 1 bps = 0.01%. When short-term rates are above long-term rates (inverted curve), markets expect slower growth.",
                 f"المصادر: {src}. نقطة الأساس = 0.01%. إذا صار العائد القصير أعلى من الطويل (منحنى مقلوب) فالسوق يتوقع تباطؤ النمو."))


def calendar_section():
    cal = data.econ_calendar(7, 7)
    if cal.empty:
        st.caption(L("Economic calendar is not available right now.", "التقويم الاقتصادي غير متاح حالياً."))
        return
    cal = cal.copy()
    tcol = next((c for c in cal.columns if "Time" in c or "Date" in c), None)
    if tcol:
        cal[tcol] = pd.to_datetime(cal[tcol], errors="coerce", utc=True)
        now = pd.Timestamp.now(tz="UTC")
        past, upcoming = cal[cal[tcol] < now].sort_values(tcol, ascending=False), cal[cal[tcol] >= now].sort_values(tcol)
        for fr in (past, upcoming):
            fr[tcol] = fr[tcol].dt.tz_convert("America/New_York").dt.strftime("%a %b %d · %H:%M ET")
    else:
        past, upcoming = cal, cal.iloc[0:0]
    ar_cols = {"Event": "الحدث", "Region": "المنطقة", "Event Time": "الوقت", "For": "الفترة", "Actual": "الفعلي",
               "Expected": "المتوقع", "Last": "السابق", "Revised": "المعدّل"}
    t1, t2 = st.tabs([L("Upcoming", "القادمة"), L("Recent releases", "صدرت مؤخراً")])
    for tab, df in ((t1, upcoming), (t2, past)):
        with tab:
            if df.empty:
                st.caption("—")
            else:
                ui.table(df.rename(columns=ar_cols) if is_ar() else df, height=480, wrap={L("Event", "الحدث")})


def page_economy():
    ui.header("account_balance", "US Economy", "الاقتصاد الأمريكي",
              "Key economic indicators and interest rates: the Fed, Treasury yields and the yield curve.",
              "أهم المؤشرات الاقتصادية وأسعار الفائدة: الفيدرالي وعوائد السندات ومنحنى العائد.")
    res = ui.safe(indicators_section)
    ui.safe(rates_section)
    with st.expander(L("Economic calendar (US)", "التقويم الاقتصادي (أمريكا)"), icon=":material/event:"):
        ui.safe(calendar_section)
    if res:
        errors, status = res
        with st.expander(L("Data source status", "حالة مصادر البيانات"), icon=":material/lan:"):
            st.write(status)
            if errors:
                st.code("\n".join(errors[:8]))
    ui.foot()


# =====================================================================
# WHAT'S TRENDING
# =====================================================================
LISTS = {"day_gainers": ("Top Gainers", "الأكثر ارتفاعاً", "trending_up"), "day_losers": ("Top Losers", "الأكثر انخفاضاً", "trending_down"),
         "most_actives": ("Most Active", "الأكثر تداولاً", "bolt"), "most_shorted_stocks": ("Most Shorted", "الأكثر بيعاً على المكشوف", "south_east"),
         "small_cap_gainers": ("Small-Cap Gainers", "شركات صغيرة صاعدة", "rocket_launch"),
         "aggressive_small_caps": ("Aggressive Small Caps", "شركات صغيرة سريعة النمو", "speed")}


def _list(kind, moves):
    df = data.screen(kind, 25)
    if not df.empty:
        df = df.copy()
    elif moves.empty:
        return pd.DataFrame(), True
    else:
        t = moves.copy()
        if kind == "day_losers":
            t = t.sort_values("Chg %")
        elif kind in ("most_actives", "most_shorted_stocks"):
            t = t.sort_values("Volume", ascending=False)
        else:
            t = t.sort_values("Chg %", ascending=False)
        df = t.head(25).copy()
        df["_fallback"] = True
    df["Rel Vol"] = df["Volume"] / df["Avg Vol"]
    return df, "_fallback" in df


def summary_points(px, moves, lists):
    pts = []
    sp, nq = _last(px, "^GSPC")[2], _last(px, "^IXIC")[2]
    if sp is not None:
        mood = ("higher", "على ارتفاع") if sp > 0 else ("lower", "على انخفاض")
        pts.append((f"S&P 500 is trading {mood[0]} ({sp:+.2f}%), Nasdaq {nq:+.2f}%.", f"مؤشر إس آند بي 500 يتداول {mood[1]} ({sp:+.2f}%) وناسداك ({nq:+.2f}%)."))
    if not moves.empty:
        adv = (moves["Chg %"] > 0).mean() * 100
        pts.append((f"Breadth: {adv:.0f}% of the top 175 US stocks are up today.", f"اتساع السوق: {adv:.0f}% من أكبر 175 سهم أمريكي صاعدة اليوم."))
    sec = data.history_many(tuple(U.SECTOR_ETFS), "5d")
    perf = {U.SECTOR_ETFS[e]: (df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100 for e, df in sec.items() if len(df) > 1}
    if perf:
        best, worst = max(perf, key=perf.get), min(perf, key=perf.get)
        pts.append((f"Leading sector: {best} ({perf[best]:+.2f}%). Lagging: {worst} ({perf[worst]:+.2f}%).",
                    f"القطاع الأقوى: {sector_name(best)} ({perf[best]:+.2f}%)، والأضعف: {sector_name(worst)} ({perf[worst]:+.2f}%)."))
    v = _last(px, "^VIX")
    if v[0] is not None:
        fear = ("rising fear", "ارتفاع القلق") if v[2] > 0 else ("easing fear", "تراجع القلق")
        pts.append((f"VIX at {v[0]:.2f} ({v[2]:+.2f}%): {fear[0]}.", f"مؤشر الخوف VIX عند {v[0]:.2f} ({v[2]:+.2f}%): {fear[1]}."))
    y = _last(px, "^TNX")
    if y[0] is not None:
        pts.append((f"10-year Treasury yield {y[0]:.2f}% ({y[1] * 100:+.0f} bps).", f"عائد السندات لأجل 10 سنوات {y[0]:.2f}% ({y[1] * 100:+.0f} نقطة أساس)."))
    oil, gold, btc = _last(px, "CL=F"), _last(px, "GC=F"), _last(px, "BTC-USD")
    if oil[0] is not None and gold[0] is not None:
        b = btc[2] if btc[2] is not None else 0
        pts.append((f"Oil {oil[2]:+.2f}% · Gold {gold[2]:+.2f}% · Bitcoin {b:+.2f}%.", f"النفط {oil[2]:+.2f}% · الذهب {gold[2]:+.2f}% · بيتكوين {b:+.2f}%."))
    g, lo, sh = lists["day_gainers"][0], lists["day_losers"][0], lists["most_shorted_stocks"][0]
    if not g.empty and not lo.empty:
        pts.append((f"Biggest gainer: {g.iloc[0]['Symbol']} ({g.iloc[0]['Chg %']:+.1f}%). Biggest loser: {lo.iloc[0]['Symbol']} ({lo.iloc[0]['Chg %']:+.1f}%).",
                    f"الأكثر ارتفاعاً: {g.iloc[0]['Symbol']} ({g.iloc[0]['Chg %']:+.1f}%)، والأكثر انخفاضاً: {lo.iloc[0]['Symbol']} ({lo.iloc[0]['Chg %']:+.1f}%)."))
    if not sh.empty:
        names = ", ".join(sh["Symbol"].head(3))
        pts.append((f"Heavily shorted names in focus: {names}.", f"أسهم عليها بيع على المكشوف مرتفع: {names}."))
    return pts


def summary_data(px, moves, lists):
    """Everything the market summary shows, as numbers (None when a feed is missing)."""
    d = {}
    for k, sym in (("sp", "^GSPC"), ("nq", "^IXIC"), ("dj", "^DJI"), ("vix", "^VIX"), ("tnx", "^TNX"), ("oil", "CL=F"), ("gold", "GC=F"),
                   ("btc", "BTC-USD"), ("eth", "ETH-USD"), ("usd", "DX-Y.NYB")):
        d[k] = _last(px, sym)
    d["up"] = d["down"] = d["n"] = 0
    if not moves.empty:
        ch = moves["Chg %"]
        d["up"], d["down"], d["n"] = int((ch > 0).sum()), int((ch < 0).sum()), int(len(ch))
    sec = data.history_many(tuple(U.SECTOR_ETFS), "5d")
    d["sectors"] = sorted(((U.SECTOR_ETFS[e], (df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100) for e, df in sec.items() if len(df) > 1),
                          key=lambda x: -x[1])
    g, lo, sh = lists["day_gainers"][0], lists["day_losers"][0], lists["most_shorted_stocks"][0]
    d["gainer"] = (g.iloc[0]["Symbol"], str(g.iloc[0].get("Name") or ""), float(g.iloc[0]["Chg %"])) if not g.empty else None
    d["loser"] = (lo.iloc[0]["Symbol"], str(lo.iloc[0].get("Name") or ""), float(lo.iloc[0]["Chg %"])) if not lo.empty else None
    d["shorted"] = [(r["Symbol"], float(r["Chg %"])) for _, r in sh.head(5).iterrows()] if not sh.empty else []
    return d


def _sgn(v, digits=2, suffix="%"):
    return f'<b class="{T.txt(v)}" dir="ltr">{v:+.{digits}f}{suffix}</b>' if v is not None else '<b class="muted">—</b>'


def _ud(v):
    return "u" if v > 0 else "d" if v < 0 else "z"


def _mst(icon, title, body, why, link=None, cls=""):
    """One tile of the market summary: a link to the page with the details when there is one; why = what the number means."""
    head = (f'<div class="mh">{T.icon(icon)}<span>{title}</span>'
            + ('<span class="ms go">arrow_outward</span>' if link else "") + "</div>")
    inner = f'{head}<div class="mb">{body}</div><div class="why">{why}</div>'
    tip = T.esc(re.sub("<[^>]+>", "", why))
    if link:
        return f'<a class="mst{cls}" href="{link}" target="_self" title="{tip}">{inner}</a>'
    return f'<div class="mst{cls}" title="{tip}">{inner}</div>'


def summary_html(d, lg):
    """The market summary: the day's tone and breadth on top, then a tile for each part of the market. Every tile opens the
    page with the details; hover a tile or a sector for what the number means."""
    lg_ = lang()
    page = lambda path: f"{path}?lang={lg_}"
    sp, nq, dj = d["sp"][2], d["nq"][2], d["dj"][2]
    # the tone of the day, from the S&P 500
    if sp is None:
        tone, tic, tcls = L("Waiting for prices", "بانتظار الأسعار"), "hourglass_empty", "t-z"
    elif sp >= 1:
        tone, tic, tcls = L("Stocks are rallying", "الأسهم في صعود قوي"), "rocket_launch", "t-u"
    elif sp >= .25:
        tone, tic, tcls = L("Stocks are higher", "الأسهم على ارتفاع"), "trending_up", "t-u"
    elif sp > -.25:
        tone, tic, tcls = L("Stocks are little changed", "الأسهم شبه مستقرة"), "trending_flat", "t-z"
    elif sp > -1:
        tone, tic, tcls = L("Stocks are lower", "الأسهم على انخفاض"), "trending_down", "t-d"
    else:
        tone, tic, tcls = L("Stocks are selling off", "الأسهم تحت ضغط بيع"), "south", "t-d"
    idx = " · ".join(f'<span>{n} {_sgn(v)}</span>' for n, v in (("S&P 500", sp), ("Nasdaq", nq), ("Dow", dj)) if v is not None)
    n, up, dn = d["n"], d["up"], d["down"]
    pu = up / n * 100 if n else 0
    breadth = (f'<div class="brd" title="{T.esc(L("How many of the 175 biggest US stocks are up today.", "كم سهم من أكبر 175 سهم أمريكي صاعد اليوم."))}">'
               f'<div class="bl"><span>{L("Breadth", "اتساع السوق")}</span><b dir="ltr">{pu:.0f}% {L("up", "صاعدة")}</b></div>'
               f'<div class="bar"><i class="u" style="width:{pu:.1f}%"></i><i class="d" style="width:{(dn / n * 100 if n else 0):.1f}%"></i></div>'
               f'<div class="bc"><span class="upt" dir="ltr">▲ {up}</span><span class="muted">{L(f"of {n} stocks", f"من {n} سهم")}</span>'
               f'<span class="dnt" dir="ltr">▼ {dn}</span></div></div>') if n else ""
    top = (f'<div class="msh {tcls}"><div class="tone"><span class="ti">{T.icon(tic)}</span><div><div class="tt">{tone}</div>'
           f'<div class="ix">{idx}</div></div></div>{breadth}</div>')
    tiles = []
    # sectors: every sector as a bar, best first
    if d["sectors"]:
        mx = max(.5, max(abs(p) for _, p in d["sectors"]))
        rows = "".join(f'<div class="sr" title="{T.esc(sector_name(nm))}: {p:+.2f}%"><span class="n">{T.esc(sector_name(nm))}</span>'
                       f'<span class="b"><i class="{_ud(p)}" style="width:{abs(p) / mx * 50:.1f}%"></i></span>{_sgn(p)}</div>'
                       for nm, p in d["sectors"])
        best, worst = d["sectors"][0], d["sectors"][-1]
        why = L(f"Leading: {best[0]} ({best[1]:+.2f}%). Lagging: {worst[0]} ({worst[1]:+.2f}%).",
                f"الأقوى: {sector_name(best[0])} ({best[1]:+.2f}%)، والأضعف: {sector_name(worst[0])} ({worst[1]:+.2f}%).")
        tiles.append(_mst("donut_small", L("Sectors today", "القطاعات اليوم"), f'<div class="secs">{rows}</div>', why, page("overview"), " wide"))
    # fear gauge
    v = d["vix"]
    if v[0] is not None:
        lvl = v[0]
        word = (L("calm", "هدوء") if lvl < 15 else L("normal", "طبيعي") if lvl < 20 else L("nervous", "توتر") if lvl < 30 else L("fearful", "خوف"))
        trend = L("rising fear", "القلق يرتفع") if (v[2] or 0) > 0 else L("easing fear", "القلق يتراجع")
        pos = min(100, max(0, (lvl - 10) / 30 * 100))
        body = (f'<div class="big" dir="ltr">{lvl:.2f} {_sgn(v[2])}</div><div class="sub">{word} · {trend}</div>'
                f'<div class="gauge" dir="ltr"><i style="left:{pos:.1f}%"></i><span style="left:33.3%"></span>'
                f'<span style="left:66.6%"></span></div><div class="gl" dir="ltr"><span>10</span><span>20</span><span>30</span><span>40</span></div>')
        tiles.append(_mst("speed", L("Fear gauge · VIX", "مؤشر الخوف · VIX"), body,
                          L("The S&P 500 swings traders expect over the next 30 days: above 20 is nervous, above 30 fearful.",
                            "التذبذب اللي يتوقعه المتداولون لمؤشر إس آند بي 500 خلال 30 يوم: فوق 20 توتر، وفوق 30 خوف."), page("sentiment")))
    # 10-year yield
    y = d["tnx"]
    if y[0] is not None:
        bps = y[1] * 100
        body = (f'<div class="big" dir="ltr">{y[0]:.2f}% <b class="{T.txt(-bps)}">{bps:+.0f} {L("bps", "نقطة")}</b></div>'
                f'<div class="sub">{L("10-year Treasury yield", "عائد سندات الخزانة لأجل 10 سنوات")}</div>')
        tiles.append(_mst("account_balance", L("Bond yields", "عوائد السندات"), body,
                          L("Higher yields make borrowing dearer and usually weigh on growth stocks.",
                            "ارتفاع العوائد يرفع كلفة الاقتراض وغالباً يضغط على أسهم النمو."), page("economy")))
    # oil, gold, bitcoin
    rows = [(L("Oil", "النفط"), d["oil"][2]), (L("Gold", "الذهب"), d["gold"][2]), (L("US dollar", "الدولار"), d["usd"][2]),
            (L("Bitcoin", "بيتكوين"), d["btc"][2]), (L("Ethereum", "إيثريوم"), d["eth"][2])]
    rows = [(nm, p) for nm, p in rows if p is not None]
    if rows:
        mx = max(1.0, max(abs(p) for _, p in rows))
        body = '<div class="rows">' + "".join(
            f'<div class="r"><span class="n">{nm}</span><span class="b"><i class="{_ud(p)}" style="width:{abs(p) / mx * 100:.0f}%"></i></span>{_sgn(p)}</div>'
            for nm, p in rows) + "</div>"
        tiles.append(_mst("oil_barrel", L("Commodities, dollar & crypto", "السلع والدولار والعملات الرقمية"), body,
                          L("Since yesterday's close. The dollar is its index against six major currencies.",
                            "منذ إغلاق أمس. الدولار هنا مؤشره مقابل ست عملات رئيسية."), page("futures")))
    # biggest movers
    mv = []
    for key, lab in (("gainer", L("Biggest gainer", "الأكثر ارتفاعاً")), ("loser", L("Biggest loser", "الأكثر انخفاضاً"))):
        m = d[key]
        if m:
            mv.append(f'<a class="mvr" href="{ui.href(m[0])}" target="_self">{T.logo_circle(m[0], lg.get(m[0]), 34)}'
                      f'<span class="nm"><small>{lab}</small><b>{T.esc(m[0])}</b><em>{T.esc(m[1][:24])}</em></span>{T.pill(m[2])}</a>')
    if d["shorted"]:                       # the heavily shorted names, under the movers
        chips = "".join(f'<a class="mchip" href="{ui.href(s_)}" target="_self">{T.esc(s_)} {_sgn(p, 1)}</a>' for s_, p in d["shorted"][:5])
        mv.append(f'<div class="shl">{L("Heavily shorted", "بيع على المكشوف مرتفع")}</div><div class="chips">{chips}</div>')
    if mv:
        tiles.append(_mst("swap_vert", L("Biggest movers", "الأكثر حركة"), "".join(mv),
                          L("The day's top gainer and loser, and the names many traders bet against (their moves can be sharp).",
                            "أكثر سهم ارتفع وأكثر سهم نزل اليوم، والأسهم اللي متداولين كثير يراهنون على نزولها (حركتها ممكن تكون حادة).")))
    return f'<div class="msum{" rtl" if is_ar() else ""}">{top}<div class="msg">{"".join(tiles)}</div></div>'


def _leaderboard(df, lg, n=12):
    cards = []
    for i, (_, r) in enumerate(df.head(n).iterrows(), 1):
        rv = r.get("Rel Vol")
        meter = ""
        if pd.notna(rv):
            meter = (f'<div class="muted" style="font-size:.7rem;margin-top:6px">{L("Rel. volume", "الحجم النسبي")} {rv:.1f}×</div>'
                     f'<div class="meter"><span style="width:{min(100, rv / 5 * 100):.0f}%"></span></div>')
        cap = T.fmt_big(r.get("Mkt Cap"))
        cards.append(f'<div class="lc"><div class="top">{T.company(r["Symbol"], str(r.get("Name") or "")[:26], lg.get(r["Symbol"]), 36, href=ui.href(r["Symbol"]))}'
                     f'<span class="rank">#{i}</span></div><div class="bot"><div><div class="px" style="font-size:1.15rem;text-align:left">'
                     f'{T.fmt_price(r["Price"])}</div><div class="muted" style="font-size:.72rem">{L("Mkt cap", "القيمة")} {cap}</div></div>'
                     f'{T.pill(r["Chg %"])}</div>{meter}</div>')
    return '<div class="lead">' + "".join(cards) + "</div>"


# ---------------------------------------------------------------- the Saudi market's trending page
SA_LISTS = {"gainers": ("Top Gainers", "الأكثر ارتفاعاً", "trending_up"), "losers": ("Top Losers", "الأكثر انخفاضاً", "trending_down"),
            "value": ("Most Traded (value)", "الأعلى قيمة تداول", "payments"), "volume": ("Unusual Volume", "حجم تداول غير عادي", "bolt"),
            "highs": ("Near a 52-week High", "قرب القمة السنوية", "north_east"), "lows": ("Near a 52-week Low", "قرب القاع السنوي", "south_east")}
SA_LIQUID = 2e6                    # SAR traded today: below it a move says little (a few trades)


def sa_lists(mv):
    """{kind: DataFrame} the Saudi movers (SA_LISTS) from data.sa_moves()."""
    if mv is None or mv.empty:
        return {k: pd.DataFrame() for k in SA_LISTS}
    mv = mv.copy()
    if is_ar():
        mv["Name"] = mv["NameAr"]
    liq = mv[mv["Value"].fillna(0) >= SA_LIQUID]
    out = {"gainers": liq.sort_values("Chg %", ascending=False), "losers": liq.sort_values("Chg %"),
           "value": mv.sort_values("Value", ascending=False),
           "volume": liq[liq["Rel Vol"].notna()].sort_values("Rel Vol", ascending=False),
           "highs": mv[mv["Hi52 %"] >= -3].sort_values("Hi52 %", ascending=False),
           "lows": mv[mv["Lo52 %"] <= 4].sort_values("Lo52 %")}
    return {k: v.head(25).reset_index(drop=True) for k, v in out.items()}


def summary_html_sa(px, mv, lists, lg):
    """The Saudi market's summary: the day's tone from TASI and the breadth of the main market on top, then the sectors, oil, gold
    and the dollar, and the biggest movers."""
    tx = _last(px, "^TASI.SR")[2]
    if tx is None:
        tone, tic, tcls = L("Waiting for prices", "بانتظار الأسعار"), "hourglass_empty", "t-z"
    elif tx >= 1:
        tone, tic, tcls = L("Saudi stocks are rallying", "الأسهم السعودية في صعود قوي"), "rocket_launch", "t-u"
    elif tx >= .25:
        tone, tic, tcls = L("Saudi stocks are higher", "الأسهم السعودية على ارتفاع"), "trending_up", "t-u"
    elif tx > -.25:
        tone, tic, tcls = L("Saudi stocks are little changed", "الأسهم السعودية شبه مستقرة"), "trending_flat", "t-z"
    elif tx > -1:
        tone, tic, tcls = L("Saudi stocks are lower", "الأسهم السعودية على انخفاض"), "trending_down", "t-d"
    else:
        tone, tic, tcls = L("Saudi stocks are selling off", "الأسهم السعودية تحت ضغط بيع"), "south", "t-d"
    nm_ = _last(px, "^NOMUC.SR")[2]
    idx = " · ".join(f'<span>{n} {_sgn(v)}</span>' for n, v in ((L("TASI", "تاسي"), tx), (L("Nomu", "نمو"), nm_)) if v is not None)
    n = len(mv) if mv is not None else 0
    up = int((mv["Chg %"] > 0).sum()) if n else 0
    dn = int((mv["Chg %"] < 0).sum()) if n else 0
    pu = up / n * 100 if n else 0
    breadth = (f'<div class="brd" title="{T.esc(L("How many of the main market companies are up today.", "كم شركة من السوق الرئيسية صاعدة اليوم."))}">'
               f'<div class="bl"><span>{L("Breadth", "اتساع السوق")}</span><b dir="ltr">{pu:.0f}% {L("up", "صاعدة")}</b></div>'
               f'<div class="bar"><i class="u" style="width:{pu:.1f}%"></i><i class="d" style="width:{(dn / n * 100 if n else 0):.1f}%"></i></div>'
               f'<div class="bc"><span class="upt" dir="ltr">▲ {up}</span><span class="muted">{L(f"of {n} companies", f"من {n} شركة")}</span>'
               f'<span class="dnt" dir="ltr">▼ {dn}</span></div></div>') if n else ""
    top = (f'<div class="msh {tcls}"><div class="tone"><span class="ti">{T.icon(tic)}</span><div><div class="tt">{tone}</div>'
           f'<div class="ix">{idx}</div></div></div>{breadth}</div>')
    tiles = []
    if n:
        sec = mv.groupby("Sector")["Chg %"].mean().dropna().sort_values(ascending=False)
        sec = [(k, float(v)) for k, v in sec.items() if k]
        if sec:
            mx = max(.5, max(abs(p) for _, p in sec))
            rows = "".join(f'<div class="sr" title="{T.esc(_sa_sector(nm))}: {p:+.2f}%"><span class="n">{T.esc(_sa_sector(nm))}</span>'
                           f'<span class="b"><i class="{_ud(p)}" style="width:{abs(p) / mx * 50:.1f}%"></i></span>{_sgn(p)}</div>' for nm, p in sec)
            best, worst = sec[0], sec[-1]
            why = L(f"Each sector is the average move of its companies today. Leading: {best[0]} ({best[1]:+.2f}%). Lagging: {worst[0]} ({worst[1]:+.2f}%).",
                    f"كل قطاع = متوسط حركة شركاته اليوم. الأقوى: {_sa_sector(best[0])} ({best[1]:+.2f}%)، والأضعف: {_sa_sector(worst[0])} ({worst[1]:+.2f}%).")
            tiles.append(_mst("donut_small", L("Sectors today", "القطاعات اليوم"), f'<div class="secs">{rows}</div>', why,
                              f"?lang={lang()}&m=sa", " wide"))
    rows = [(L("Brent crude", "خام برنت"), _last(px, "BZ=F")[2]), (L("WTI crude", "خام غرب تكساس"), _last(px, "CL=F")[2]),
            (L("Gold", "الذهب"), _last(px, "GC=F")[2]), (L("US dollar", "الدولار"), _last(px, "DX-Y.NYB")[2]),
            (L("Bitcoin", "بيتكوين"), _last(px, "BTC-USD")[2])]
    rows = [(nm, p) for nm, p in rows if p is not None]
    if rows:
        mx = max(1.0, max(abs(p) for _, p in rows))
        body = '<div class="rows">' + "".join(
            f'<div class="r"><span class="n">{nm}</span><span class="b"><i class="{_ud(p)}" style="width:{abs(p) / mx * 100:.0f}%"></i></span>{_sgn(p)}</div>'
            for nm, p in rows) + "</div>"
        tiles.append(_mst("oil_barrel", L("Oil, gold & the dollar", "النفط والذهب والدولار"), body,
                          L("Since yesterday's close. Oil matters most for the Saudi market: energy and petrochemicals are a large part of it, "
                            "and the riyal is pegged to the dollar.",
                            "منذ إغلاق أمس. النفط الأهم للسوق السعودي: الطاقة والبتروكيماويات جزء كبير منه، والريال مربوط بالدولار.")))
    mvs = []
    for key, lab in (("gainers", L("Biggest gainer", "الأكثر ارتفاعاً")), ("losers", L("Biggest loser", "الأكثر انخفاضاً"))):
        d = lists.get(key)
        if d is not None and not d.empty:
            r = d.iloc[0]
            mvs.append(f'<a class="mvr" href="{ui.href(r["Symbol"])}" target="_self">{T.logo_circle(r["Symbol"], lg.get(r["Symbol"]), 34)}'
                       f'<span class="nm"><small>{lab}</small><b dir="auto">{T.esc(T.sym_label(r["Symbol"]))}</b><em>{T.esc(T.sym_sub(r["Symbol"]))}</em></span>{T.pill(r["Chg %"])}</a>')
    d = lists.get("value")
    if d is not None and not d.empty:
        chips = "".join(f'<a class="mchip" href="{ui.href(s_)}" target="_self"><bdi>{T.esc(T.sym_label(s_))}</bdi> {_sgn(p, 1)}</a>'
                        for s_, p in zip(d["Symbol"].head(5), d["Chg %"].head(5)))
        mvs.append(f'<div class="shl">{L("Most traded today", "الأعلى قيمة تداول اليوم")}</div><div class="chips">{chips}</div>')
    if mvs:
        tiles.append(_mst("swap_vert", L("Biggest movers", "الأكثر حركة"), "".join(mvs),
                          L(f"Among the companies that traded more than SAR {SA_LIQUID / 1e6:.0f} million today, and the most traded by value.",
                            f"بين الشركات اللي تداولت بأكثر من {SA_LIQUID / 1e6:.0f} مليون ريال اليوم، والأعلى قيمة تداول.")))
    return f'<div class="msum{" rtl" if is_ar() else ""}">{top}<div class="msg">{"".join(tiles)}</div></div>'


def page_trending_sa():
    ui.header("local_fire_department", "What's Trending · Saudi Market", "الأكثر رواجاً · السوق السعودي",
              "Today's most important Saudi stories, the biggest movers of the main market, the most traded and the unusual volumes, and a "
              "plain-language summary.",
              "أهم أخبار السوق السعودي اليوم، والأسهم الأكثر حركة في السوق الرئيسية، والأعلى تداولاً والأحجام غير العادية، وملخص بلغة بسيطة.")
    px = _tile_prices()
    mv = data.sa_moves()
    lists = sa_lists(mv)
    all_syms = [s_ for df in lists.values() if not df.empty for s_ in df["Symbol"].head(12)]
    ui.sec("newspaper", "Top 3 trending stories", "أهم 3 أخبار رائجة")
    stories = ui.safe(top_stories, 3) or []
    tick = sorted({s_ for n in stories for s_ in n["tickers"]})
    lg = data.logos(list(dict.fromkeys(all_syms + tick)))
    if stories:
        titles = [n["title"] for n in stories]
        if is_ar():
            titles = data.translate(titles)
        chg = data.quick_changes(tick) if tick else {}
        cards = []
        for i, (n, t) in enumerate(zip(stories, titles)):
            ch = ui.chips(n["tickers"], chg, lg) or f'<span class="muted">{L("Broad market", "السوق بشكل عام")}</span>'
            iq = n.get("iq")
            score = ""
            if iq:
                bg, fg, bd = newsiq.colors(iq["score"])
                score = f'<span class="iqs" style="background:{bg};color:{fg};border-color:{bd}">{iq["score"]}/10 · {T.esc(L(*newsiq.level(iq["score"])))}</span>'
            cards.append(f'<div class="story r{i + 1}{" rtl" if is_ar() else ""}">{T.news_thumb(n, big=True)}<div class="rank">0{i + 1}</div>'
                         f'<a class="t nogq" href="{T.esc(n["link"])}" target="_blank">{T.esc(t)}</a>'
                         f'<div class="muted" style="font-size:.78rem;margin-top:6px">{T.esc(n["source"])} · {T.time_ago(n["time"], is_ar())}</div>'
                         f'<div style="margin-top:8px">{score}</div>' + (T.kw_chips(iq, is_ar(), 3) if iq else "") +
                         f'<div class="aff"><span class="lbl" style="width:100%">{L("Affected companies", "الشركات المتأثرة")}</span>{ch}</div>'
                         + T.coverage(n, is_ar()) + '</div>')
        ui.html(f'<div class="stories n{len(cards)}">' + "".join(cards) + "</div>")
    else:
        st.caption(L("No trending stories right now.", "لا توجد أخبار رائجة حالياً."))
    _talked_section()
    ui.sec("summarize", "Market summary", "ملخص السوق")
    ui.html(summary_html_sa(px, mv, lists, lg))
    if mv.empty:
        st.info(L("Saudi quotes are unavailable right now. Try again in a minute.", "أسعار السوق السعودي غير متاحة حالياً. حاول بعد دقيقة."))
        ui.foot()
        return
    ui.sec("leaderboard", "Movers at a glance", "الأسهم الأكثر حركة")
    keys = list(SA_LISTS)
    for i, row in enumerate((keys[:3], keys[3:])):
        with st.container(key=f"mvrow_{i}"):
            cols = st.columns(3)
        for col, kind in zip(cols, row):
            df = lists[kind]
            en, ar, ic = SA_LISTS[kind]
            body = ui.row_list(df.head(6), lg, show_vol=kind == "volume") if not df.empty else f'<div class="muted">{L("No data", "لا بيانات")}</div>'
            col.markdown(f'<div class="mcard"><div class="hd">{T.icon(ic)}<span>{T.esc(L(en, ar))}</span></div>{body}</div>', unsafe_allow_html=True)
    ui.sec("table_rows", "Full lists", "القوائم الكاملة")
    tabs = st.tabs([f":material/{v[2]}: {L(v[0], v[1])}" for v in SA_LISTS.values()])
    for tab, kind in zip(tabs, SA_LISTS):
        with tab:
            df = lists[kind]
            if df.empty:
                st.info(L("No company fits this list today.", "ما فيه شركة تنطبق عليها هالقائمة اليوم."))
                continue
            ui.html(_leaderboard(df, lg))
            ui.chart(charts.movers_bubble(df.assign(Label=df["Symbol"].map(lambda s_: T.sym_label(s_)[:12])),
                                          L("Change vs relative volume (bubble = market cap)", "التغير مقابل الحجم النسبي (حجم الفقاعة = القيمة السوقية)"),
                                          L("Relative volume (×)", "الحجم النسبي (×)"), L("Change %", "التغير %")), key=f"bub_sa_{kind}")
            show = df[["Symbol", "Name", "Price", "Chg %", "Value", "Rel Vol", "Mkt Cap"]].copy()
            show.insert(0, "Logo", show["Symbol"].map(data.logo_url))
            show["Value"] = show["Value"].map(T.fmt_big)
            show["Mkt Cap"] = show["Mkt Cap"].map(T.fmt_big)
            N = {"Symbol": L("Symbol", "الرمز"), "Name": L("Company", "الشركة"), "Price": L("Price (SAR)", "السعر (ر.س)"), "Chg %": L("Change %", "التغير %"),
                 "Value": L("Traded value (SAR)", "قيمة التداول (ر.س)"), "Rel Vol": L("Rel. volume", "الحجم النسبي"),
                 "Mkt Cap": L("Market cap (SAR)", "القيمة السوقية (ر.س)")}
            show = show.rename(columns=N)
            ui.table(show, sym=N["Symbol"], pills={N["Chg %"]}, height=480,
                     fmt={N["Price"]: "{:,.2f}", N["Chg %"]: "{:+.2f}%", N["Rel Vol"]: "{:.1f}×"})
            ui.open_picker(df["Symbol"].tolist(), f"tr_sa_{kind}", "Open a company", "افتح شركة")
    st.caption(L(f"From Yahoo Finance quotes of the {len(mv)} main-market companies (may be delayed). Gainers, losers and unusual volume count only "
                 f"companies that traded more than SAR {SA_LIQUID / 1e6:.0f} million today.",
                 f"من أسعار ياهو فاينانس لـ {len(mv)} شركة في السوق الرئيسية (قد تكون متأخرة). الأكثر ارتفاعاً وانخفاضاً والحجم غير العادي تحسب بس "
                 f"الشركات اللي تداولت بأكثر من {SA_LIQUID / 1e6:.0f} مليون ريال اليوم."))
    ui.foot()


def page_trending():
    if MK.is_sa():
        return page_trending_sa()
    ui.header("local_fire_department", "What's Trending", "الأكثر رواجاً",
              "Today's most important stories, the biggest movers, short interest and a plain-language market summary.",
              "أهم أخبار اليوم، الأسهم الأكثر حركة، البيع على المكشوف، وملخص السوق بلغة بسيطة.")
    px = _tile_prices()
    moves = _universe_moves()
    lists = {k: _list(k, moves) for k in LISTS}
    all_syms = [s for df, _ in lists.values() if not df.empty for s in df["Symbol"].head(12)]

    ui.sec("newspaper", "Top 3 trending stories", "أهم 3 أخبار رائجة")
    stories = top_stories(3)
    tick = sorted({s_ for n in stories for s_ in n["tickers"]})
    lg = data.logos(list(dict.fromkeys(all_syms + tick)))
    if stories:
        titles = [n["title"] for n in stories]
        if is_ar():
            titles = data.translate(titles)
        chg = data.changes(tick) if tick else {}
        cards = []
        for i, (n, t) in enumerate(zip(stories, titles)):
            ch = ui.chips(n["tickers"], chg, lg) or f'<span class="muted">{L("Broad market", "السوق بشكل عام")}</span>'
            iq = n.get("iq")
            score = ""
            if iq:
                bg, fg, bd = newsiq.colors(iq["score"])
                lv = newsiq.level(iq["score"])
                score = (f'<span class="iqs" style="background:{bg};color:{fg};border-color:{bd}">{iq["score"]}/10 · {T.esc(L(*lv))}</span>')
            cards.append(f'<div class="story r{i + 1}{" rtl" if is_ar() else ""}">{T.news_thumb(n, big=True)}<div class="rank">0{i + 1}</div>'
                         f'<a class="t nogq" href="{T.esc(n["link"])}" target="_blank">{T.esc(t)}</a>'
                         f'<div class="muted" style="font-size:.78rem;margin-top:6px">{T.esc(n["source"])} · {T.time_ago(n["time"], is_ar())}</div>'
                         f'<div style="margin-top:8px">{score}</div>' + (T.kw_chips(iq, is_ar(), 3) if iq else "") +
                         f'<div class="aff"><span class="lbl" style="width:100%">{L("Affected companies", "الشركات المتأثرة")}</span>{ch}</div>'
                         + T.coverage(n, is_ar()) + '</div>')
        # ranked by size: the first story is the biggest card, the second a step smaller, the third smaller again
        ui.html(f'<div class="stories n{len(cards)}">' + "".join(cards) + "</div>")
    else:
        st.caption(L("No trending stories right now.", "لا توجد أخبار رائجة حالياً."))
    _talked_section()

    ui.sec("summarize", "Market summary", "ملخص السوق")
    ui.html(summary_html(summary_data(px, moves, lists), lg))

    ui.sec("leaderboard", "Movers at a glance", "الأسهم الأكثر حركة")
    keys = list(LISTS)
    for i, row in enumerate((keys[:3], keys[3:])):
        with st.container(key=f"mvrow_{i}"):
            cols = st.columns(3)
        for col, kind in zip(cols, row):
            df, _ = lists[kind]
            en, ar, ic = LISTS[kind]
            body = ui.row_list(df.head(6), lg) if not df.empty else f'<div class="muted">{L("No data", "لا بيانات")}</div>'
            col.markdown(f'<div class="mcard"><div class="hd">{T.icon(ic)}<span>{T.esc(L(en, ar))}</span></div>{body}</div>', unsafe_allow_html=True)

    ui.sec("table_rows", "Full lists", "القوائم الكاملة")
    tabs = st.tabs([f":material/{v[2]}: {L(v[0], v[1])}" for v in LISTS.values()])
    for tab, kind in zip(tabs, LISTS):
        with tab:
            df, fallback = lists[kind]
            if df.empty:
                st.info(L("Data unavailable right now.", "البيانات غير متاحة حالياً."))
                continue
            ui.html(_leaderboard(df, lg))
            ui.chart(charts.movers_bubble(df, L("Change vs relative volume (bubble = market cap)", "التغير مقابل الحجم النسبي (حجم الفقاعة = القيمة السوقية)"),
                                          L("Relative volume (×)", "الحجم النسبي (×)"), L("Change %", "التغير %")), key=f"bub_{kind}")
            show = df[["Symbol", "Name", "Price", "Chg %", "Volume", "Rel Vol", "Mkt Cap"]].copy()
            show.insert(0, "Logo", show["Symbol"].map(data.logo_url))
            show["Volume"] = show["Volume"].map(T.fmt_big)
            show["Mkt Cap"] = show["Mkt Cap"].map(T.fmt_big)
            N = {"Symbol": L("Symbol", "الرمز"), "Name": L("Company", "الشركة"), "Price": L("Price", "السعر"), "Chg %": L("Change %", "التغير %"),
                 "Volume": L("Volume", "الحجم"), "Rel Vol": L("Rel. volume", "الحجم النسبي"), "Mkt Cap": L("Market cap", "القيمة السوقية")}
            show = show.rename(columns=N)
            ui.table(show, sym=N["Symbol"], pills={N["Chg %"]}, height=480,
                     fmt={N["Price"]: "{:,.2f}", N["Chg %"]: "{:+.2f}%", N["Rel Vol"]: "{:.1f}×"})
            if fallback:
                st.caption(L("Computed from the top 175 US stocks (screener source unavailable).", "محسوبة من أكبر 175 سهم أمريكي (مصدر القوائم غير متاح حالياً)."))
            ui.open_picker(df["Symbol"].tolist(), f"tr_{kind}", "Open a stock", "افتح سهماً")
    ui.foot()


# =====================================================================
# NEWS
# =====================================================================
def talked_about(k=8):
    """The companies the news talks about most in the last 24 hours: each story counts once per outlet that told it (the same
    event from five outlets weighs five), and only the companies a story is about (its first two)."""
    from collections import Counter
    items = newsbot.cluster(data.market_news(24)[:800])
    cnt, stories = Counter(), Counter()
    for n in items:
        w = 1 + len(n.get("also") or [])
        for t in (n.get("tickers") or [])[:2]:
            if t and "^" not in t and "=" not in t:
                cnt[t] += w
                stories[t] += 1
    return [(t, c, stories[t]) for t, c in cnt.most_common(k)]


def talked_html(rows, chg, lg):
    """Cards of the most talked-about companies: logo, name, how many stories and outlets, today's move; a click opens the company."""
    if not rows:
        return ""
    top = max(c for _, c, _ in rows) or 1
    cards = []
    for i, (t, c, k) in enumerate(rows):
        pct = (chg.get(t) or (None, None))[1]
        mv = T.pill(pct) if pct is not None and pd.notna(pct) else '<span class="muted">—</span>'
        what = L(f"{k} {'story' if k == 1 else 'stories'}", f"{k} {'خبر' if k == 1 else 'أخبار'}")
        if c > k:
            what += L(f" · {c} reports", f" · {c} تقارير")
        cards.append(f'<a class="tkt" href="{T.esc(ui.href(t))}" target="_self"><span class="rk">{i + 1}</span>'
                     f'<span class="lg">{T.logo_obj(t, 34)}</span><b class="nm" dir="auto">{T.esc(T.sym_label(t))}</b>'
                     f'<span class="mv">{mv}</span><small class="sub">{T.esc(what)}</small>'
                     f'<i class="bar" style="width:{c / top * 100:.0f}%"></i></a>')
    return '<div class="tktg">' + "".join(cards) + "</div>"


def _talked_section():
    rows = ui.safe(talked_about, 8) or []
    if not rows:
        return
    ui.sec("forum", "Most talked-about companies", "أكثر الشركات حضوراً في الأخبار")
    syms = [t for t, _, _ in rows]
    chg = data.quick_changes(syms) if syms else {}
    ui.html(talked_html(rows, chg, {}))
    st.caption(L("Counted from the last 24 hours of news: a story told by several outlets counts once for each of them.",
                 "محسوبة من أخبار آخر 24 ساعة: الخبر اللي نشرته عدة مصادر ينحسب مرة لكل مصدر."))


def top_stories(k=3):
    """The most important recent stories that name at least one company (importance score, then freshness)."""
    items = [n for n in data.market_news(24)[:400]]
    fresh = [n for n in items if pd.notna(n.get("time")) and n["time"] >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=14)] or items[:60]
    fresh = newsbot.cluster(fresh)              # three different events, each with its full coverage (not one event three times)
    tick = sorted({s_ for n in fresh for s_ in n.get("tickers", [])})
    newsiq.enrich(fresh, data.quick_changes(tick) if tick else {})
    ranked = newsiq.rank([n for n in fresh if n.get("tickers")]) or newsiq.rank(fresh)
    return ranked[:k]


def _ago(ts):
    if not ts:
        return "—"
    m = max(0, (time.time() - ts) / 60)
    return L(f"{int(m)} min ago", f"قبل {int(m)} دقيقة") if m < 60 else L(f"{int(m // 60)} h ago", f"قبل {int(m // 60)} ساعة")


def _news_bot(wait=False):
    """The news bot of the page's market (the Saudi market has its own)."""
    return newsbot.sa_bot(wait=wait) if MK.is_sa() else newsbot.bot(wait=wait)


def _refresh_bot():
    try:
        _news_bot().collect(force=True)
    except Exception:
        pass


def bot_panel(items_24h):
    """Live strip: how many headlines the bot has, from how many outlets, when it last updated; plus the status of every source."""
    try:
        b = _news_bot()
        health, updated = b.health(), b.updated
    except Exception:
        health, updated = [], None
    live = sum(1 for h in health if h["ok"])
    outlets = len({n.get("source") for n in items_24h})
    c1, c2 = st.columns([5, 1], vertical_alignment="center")
    c1.markdown(f'<div class="botbar"><span class="live"><i></i>{L("News bot · live", "بوت الأخبار · مباشر")}</span>'
                f'<span><b>{len(items_24h):,}</b> {L("headlines in the last 24 hours", "خبراً خلال آخر 24 ساعة")}</span>'
                f'<span><b>{outlets}</b> {L("outlets", "مصدراً")}</span>'
                f'<span>{L("sources working", "مصادر تعمل")}: <b>{live}/{len(health) or len(newsbot.SA_OUTLETS if MK.is_sa() else newsbot.OUTLETS)}</b></span>'
                f'<span>{L("updated", "آخر تحديث")} {_ago(updated)} · {L("every 3 minutes", "كل 3 دقائق")}</span></div>', unsafe_allow_html=True)
    c2.button(L("Refresh", "تحديث"), icon=":material/refresh:", key="nw_refresh", on_click=_refresh_bot, width="stretch")
    if health:
        with st.expander(L(f"News sources ({live} working now)", f"مصادر الأخبار ({live} تعمل الآن)"), icon=":material/rss_feed:"):
            cards = []
            for h in health:
                cls = "" if h["ok"] else ("wait" if not h["err"] else "bad")
                right = (f'{h["items"]} · {h["ms"] / 1000:.1f}s' if h["ok"] and h["ms"] is not None else
                         (T.esc(h["err"]) if h["err"] else L("waiting", "بالانتظار")))
                cards.append(f'<div class="srcc {cls}"><i class="d"></i><b>{T.esc(h["outlet"])}</b><span>{right}</span></div>')
            st.markdown('<div class="srcgrid">' + "".join(cards) + "</div>", unsafe_allow_html=True)
            st.caption(L("The bot reads every source every 3 minutes and merges the same story told by several outlets (+N next to the source). "
                         "A source in red is blocked or down right now and is retried automatically.",
                         "البوت يقرأ كل المصادر كل 3 دقائق ويدمج الخبر نفسه إذا نشرته عدة مصادر (+N بجانب المصدر). "
                         "المصدر الأحمر محجوب أو متوقف حالياً وتتم إعادة المحاولة تلقائياً."))


def page_news():
    sa = MK.is_sa()
    if sa:
        ui.header("newspaper", "Saudi Market News", "أخبار السوق السعودي",
                  "Live headlines on Saudi stocks collected by the news bot from Argaam, Al Eqtisadiah, Maaal, Asharq Bloomberg, CNBC Arabia, "
                  "Reuters, Arab News and more, in Arabic and English, with the companies each story names.",
                  "أخبار مباشرة عن الأسهم السعودية يجمعها بوت الأخبار من أرقام والاقتصادية ومال والشرق بلومبرغ وCNBC عربية ورويترز وعرب نيوز وغيرها، "
                  "بالعربي والإنجليزي، مع الشركات اللي يذكرها كل خبر.")
    else:
        ui.header("newspaper", "Market News", "أخبار السوق",
                  "Live headlines collected by the news bot from Reuters, Bloomberg, WSJ, FT, CNBC, Benzinga and 20+ other sources, with keywords, "
                  "an importance score from 1 to 10 and the companies affected by each story.",
                  "أخبار مباشرة يجمعها بوت الأخبار من رويترز وبلومبرغ ووول ستريت جورنال وفايننشال تايمز وCNBC وبنزينغا وأكثر من 20 مصدراً آخر، "
                  "مع الكلمات المفتاحية ودرجة أهمية من 1 إلى 10 والشركات المتأثرة بكل خبر.")
    # the bot's live strip first, then every filter in one panel: what to read (company, time, kind, outlets) and how to list it
    with st.spinner(L("The news bot is collecting headlines from 35 feeds (only the first time)...",
                      "بوت الأخبار يجمع العناوين من 35 مصدراً (أول مرة فقط)...")):
        everything = data.market_news(96)
    now = pd.Timestamp.now(tz="UTC")
    bot_panel([n for n in everything if pd.notna(n.get("time")) and n["time"] >= now - pd.Timedelta(hours=24)])
    with st.container(key="nwfilt"):
        c1, c2, c3, c4 = st.columns([1.7, 1.25, 1.35, 0.75], vertical_alignment="bottom")
        if sa:
            sym = ui.sa_company(L("Company", "الشركة"), "nw_sym_sa2", container=c1, none_label=L("All the market", "السوق كله")) or ""
        else:
            sym = c1.text_input(L("Company", "الشركة"), "", key="nw_sym",
                                placeholder=L("Symbol, e.g. NVDA · empty = all the market", "رمز السهم مثل NVDA · فاضي = السوق كله")).strip().upper()
        sort = c2.segmented_control(L("Order", "الترتيب"), ["imp", "new"], default="new" if sa else "imp", key="nw_sort_sa" if sa else "nw_sort",
                                    format_func=lambda k: L("Important", "الأهم") if k == "imp" else L("Latest", "الأحدث")) or "imp"
        lvl = c3.segmented_control(L("Importance", "الأهمية"), [1, 5, 7, 9], default=1, key="nw_min",
                                   format_func=lambda v: L("All", "الكل") if v == 1 else f"{v}+") or 1
        count = c4.selectbox(L("Stories", "عدد الأخبار"), [10, 20, 30, 50, 100], index=1, key="nw_count")
        items = data.symbol_news(sym) if sym else everything
        pick_c, pick_s, hrs = [], [], 96
        if not sym:
            d1, d2, d3, d4 = st.columns([1.35, 2.2, 1.45, 0.75], vertical_alignment="bottom")
            hrs = d1.segmented_control(L("Time", "الوقت"), [1, 6, 24, 96], default=24, key="nw_hrs",
                                       format_func=lambda h: {1: L("1h", "ساعة"), 6: L("6h", "6 ساعات"), 24: L("24h", "24 ساعة"),
                                                              96: L("4 days", "4 أيام")}[h]) or 24
            cats = [c for c in newsbot.CATS if any(n.get("cat") == c for n in items)]
            if isinstance(ss.get("nw_cat"), list):
                ss["nw_cat"] = [c for c in ss["nw_cat"] if c in cats]
            pick_c = d2.pills(L("Category", "التصنيف"), cats, selection_mode="multi", key="nw_cat",
                              format_func=lambda c: L(newsbot.CATS[c][0], newsbot.CATS[c][1])) or []
            outs = sorted({n.get("source") for n in items if n.get("source")}, key=lambda o: (newsbot.RANK.get(o, 99), o))
            ui.valid_multi("nw_src", outs)
            pick_s = d3.multiselect(L("Sources", "المصادر"), outs, key="nw_src", placeholder=L("All sources", "كل المصادر"))
            translate = d4.toggle(L("Arabic", "ترجمة"), value=is_ar(), key="nw_tr", help=L("Translate the headlines to Arabic", "ترجم العناوين للعربي"))
        else:
            translate = c4.toggle(L("Arabic", "ترجمة"), value=is_ar(), key="nw_tr", help=L("Translate the headlines to Arabic", "ترجم العناوين للعربي"))
    items = [n for n in items if pd.notna(n.get("time")) and n["time"] >= now - pd.Timedelta(hours=hrs)] if not sym else items
    # the same event told by several outlets becomes one story with its full coverage (newsbot.cluster)
    items = newsbot.cluster(items[:1500])
    if pick_c:
        items = [n for n in items if n.get("cat") in pick_c]
    if pick_s:
        items = [n for n in items if n.get("source") in pick_s or any(a in pick_s for a in n.get("also") or [])]
    items = items[:1200]
    recent = items[:250]
    tick = sorted({s_ for n in recent for s_ in n.get("tickers", [])})
    chg = data.quick_changes(tick) if tick else {}
    newsiq.enrich(items, chg)
    if items:
        scores = [n["iq"]["score"] for n in items]
        vi, im = sum(1 for x in scores if x >= 9), sum(1 for x in scores if 7 <= x < 9)
        avg = sum(scores) / len(scores)
        k = st.columns(4)
        grouped = sum(1 for n in items if n.get("more"))
        k[0].markdown(T.kpi("newspaper", L("Stories analysed", "أخبار تم تحليلها"), f"{len(items):,}",
                            L(f"{grouped} told by several outlets, grouped", f"{grouped} منها نشرتها عدة مصادر وتم تجميعها") if grouped else
                            L("keywords and score for each one", "كلمات مفتاحية ودرجة لكل خبر")), unsafe_allow_html=True)
        k[1].markdown(T.kpi("priority_high", L("Very important (9–10)", "هام جداً (9–10)"), f"{vi}",
                            L("red = worth your attention now", "الأحمر = يستحق انتباهك الآن"), "neg" if vi else None), unsafe_allow_html=True)
        k[2].markdown(T.kpi("label_important", L("Important (7–8)", "هام (7–8)"), f"{im}", L("market-moving stories", "أخبار مؤثرة في السوق")),
                      unsafe_allow_html=True)
        lv = newsiq.level(round(avg))
        k[3].markdown(T.kpi("speed", L("Average importance", "متوسط الأهمية"), f"{avg:.1f}/10", T.esc(L(*lv)),
                            "neg" if avg >= 7 else ("pos" if avg < 4 else None)), unsafe_allow_html=True)
        top = newsiq.top_keywords(items, 14)
        if top:
            opts = [kw[1] for kw, _ in top]
            cnt = {kw[1]: c for kw, c in top}
            ar_of = {kw[1]: kw[2] for kw, _ in top}
            if isinstance(ss.get("nw_kw"), list):
                ss["nw_kw"] = [v for v in ss["nw_kw"] if v in opts]
            pick = st.pills(L("Top keywords (click to filter)", "أبرز الكلمات المفتاحية (اضغط للفلترة)"), opts, selection_mode="multi", key="nw_kw",
                            format_func=lambda en: f"{ar_of.get(en, en) if is_ar() else en} · {cnt.get(en, 0)}") or []
            if pick:
                items = [n for n in items if any(kw[1] in pick for kw in n["iq"]["keywords"])]
        ui.html(f'<div class="card" style="padding:10px 14px;display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">'
                f'<b style="font-size:.85rem">{L("Importance score", "درجة الأهمية")}</b>{T.iq_legend(is_ar())}'
                f'<span class="muted" style="font-size:.74rem">{L("Hover a score to see why it was given.", "مرّر الماوس على الدرجة لتعرف سببها.")}</span></div>')
    items = [n for n in items if n["iq"]["score"] >= lvl]
    if sort == "imp":
        items = newsiq.rank(items)
    if not items:
        st.info(L("No headlines match these filters right now. Choose a longer time, a lower importance or more sources.",
                  "لا توجد أخبار تطابق هذه الفلاتر حالياً. اختر وقتاً أطول أو أهمية أقل أو مصادر أكثر."), icon=":material/filter_alt_off:")
        ui.foot()
        return
    ui.news_list(items, count, translate=translate, analyze=True)
    ui.foot()

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "22.4.2"
