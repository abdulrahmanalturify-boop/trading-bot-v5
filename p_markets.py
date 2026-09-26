"""
p_markets.py - Overview (TradingView-style heatmap, sector rotation, market breadth) · Futures · Options market ·
Economy · What's Trending · News
"""
import time

import numpy as np
import pandas as pd
import streamlit as st

import charts
import data
import heatmap as HM
import newsbot
import newsiq
import ta
import taxonomy as X
import theme as T
import ui
import universe as U
from i18n import L, industry_name, is_ar, lang, sector_name, theme_name
from sp500 import DOW30, SP500, gics_name

ss = st.session_state


def _tile_prices():
    syms = [s for g in U.MARKET_TILES.values() for s in g]
    return data.history_many(tuple(syms + list(U.TAPE)), "1mo")


def _last(px, sym):
    df = px.get(sym)
    if df is None or len(df) < 2:
        return None, None, None
    last, prev = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
    return last, last - prev, (last / prev - 1) * 100


def _chg(df, n):
    """% change over n bars ('ytd' = since the first close of the year)."""
    if df is None or df.empty:
        return np.nan
    c = df["Close"].dropna()
    if n == "ytd":
        y = c[c.index.year == c.index[-1].year]
        return (c.iloc[-1] / y.iloc[0] - 1) * 100 if len(y) > 1 else np.nan
    return (c.iloc[-1] / c.iloc[-1 - n] - 1) * 100 if len(c) > n else np.nan


def ticker_tape(px):
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
    u = {"sp500": (L("S&P 500 Index", "مؤشر إس آند بي 500"), list(SP500)),
         "dow": (L("Dow Jones 30", "داو جونز 30"), DOW30),
         "top": (L("Top 175 US stocks", "أكبر 175 سهم أمريكي"), list(U.US_UNIVERSE))}
    for tk, (en, ar, _, _) in X.THEMES.items():
        u[f"t:{tk}"] = (L(f"Theme · {en}", f"ثيم · {ar}"), X.theme_tickers(tk))
    return u


def _meta(sym):
    """(name, sector, industry, industry naming) from the static lists."""
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
        rows.append({"Symbol": s, "Name": r.get("Name") if isinstance(r.get("Name"), str) and r.get("Name") != s else name,
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
    cap = pd.to_numeric(df["Cap"], errors="coerce")
    static = df["Symbol"].map(lambda s: U.STOCKS[s][3] * 1e9 if s in U.STOCKS else np.nan)
    cap = cap.fillna(static).fillna(cap.median() if cap.notna().any() else 2e10).fillna(2e10)
    if sizing == "cap":
        df["Size"] = cap
    elif sizing == "dvol":
        dv = pd.to_numeric(df["Volume"], errors="coerce") * pd.to_numeric(df["Price"], errors="coerce")
        df["Size"] = dv.fillna(dv.median() if dv.notna().any() else 1.0).clip(lower=1.0)
    else:
        df["Size"] = 1.0
    df["Cap"] = cap
    return df, source


def heatmap_section():
    ui.sec("grid_view", "Stock heatmap", "خريطة الأسهم الحرارية")
    unis = hm_universes()
    c = st.columns([1.35, 1, 1.05, 1.25])
    ukey = c[0].selectbox(L("Index", "المؤشر"), list(unis), key="hm_uni", format_func=lambda k: unis[k][0])
    sizing = c[1].selectbox(L("Size", "الحجم"), list(HM_SIZES), key="hm_size", format_func=lambda k: L(*HM_SIZES[k]))
    period = c[2].selectbox(L("Color", "اللون"), list(HM_PERIODS), key="hm_per", format_func=lambda k: L(*HM_PERIODS[k]))
    theme_uni = ukey.startswith("t:")
    with st.spinner(L("Building the heatmap...", "جاري بناء الخريطة...")):
        df, source = heatmap_frame(ukey, period, sizing)
    if df.empty:
        c[3].selectbox(L("Sector", "القطاع"), ["all"], key="hm_sec_empty", format_func=lambda s: L("All sectors", "كل القطاعات"))
        st.warning(L("Market data is temporarily unavailable.", "بيانات السوق غير متاحة مؤقتاً."))
        return None
    sectors = ["all"] + sorted(df["Sector"].unique(), key=lambda s: -df.loc[df["Sector"] == s, "Cap"].sum())
    if ss.get("hm_sec") not in sectors:
        ss["hm_sec"] = "all"
    sec = c[3].selectbox(L("Sector", "القطاع"), sectors, key="hm_sec",
                         format_func=lambda s: L("All sectors", "كل القطاعات") if s == "all" else sector_name(s))
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
        label = sector_name
    else:
        view = view.assign(Group=view["Industry"])
        kind_of = view.groupby("Industry")["Kind"].first().to_dict()
        label = lambda g: gics_name(g) if kind_of.get(g) == "gics" else industry_name(g)
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
        return f'{t["Symbol"]} · {t.get("Name", "")}\n{T.fmt_price(t.get("Price"))} · {chg} · {L("Mkt cap", "القيمة")} {T.fmt_big(t.get("Cap"))}'
    ui.html(HM.render(tiles, groups, lg, rng, lang(), label, tip, rtl=is_ar()))
    ui.html(HM.legend(rng))
    up, dn = int((view["Val"] > 0).sum()), int((view["Val"] < 0).sum())
    w = np.average(view["Val"].fillna(0), weights=view["Size"]) if view["Size"].sum() > 0 else 0
    st.caption(L(f"{len(view)} companies · {up} up · {dn} down · weighted change {w:+.2f}% · size = {L(*HM_SIZES[sizing])} · "
                 "click any company to open its page" + ("" if source == "live" else " · delayed data"),
                 f"{len(view)} شركة · {up} صاعدة · {dn} نازلة · التغير المرجّح {w:+.2f}% · الحجم = {L(*HM_SIZES[sizing])} · "
                 "اضغط على أي شركة لفتح صفحتها" + ("" if source == "live" else " · بيانات متأخرة")))
    ui.open_picker(view.sort_values("Size", ascending=False)["Symbol"].tolist(), "hm", "Open a company from the map", "افتح شركة من الخريطة")
    return df if ukey == "sp500" else None


# =====================================================================
# SECTOR PERFORMANCE (cards + rotation graph) · MARKET BREADTH
# =====================================================================
SEC_PERIODS = {"1D": 1, "1W": 5, "1M": 21, "3M": 63, "YTD": "ytd"}


def _rrg(hist, window=12, tail=5):
    """JdK-style Relative Rotation Graph points (weekly, smoothed): RS-Ratio (trend of relative strength) and RS-Momentum."""
    spy = hist.get("SPY")
    if spy is None or len(spy) < 120:
        return {}
    sw = spy["Close"].resample("W-FRI").last()
    out = {}
    for etf in U.SECTOR_ETFS:
        df = hist.get(etf)
        if df is None or len(df) < 120:
            continue
        rs = ((df["Close"].resample("W-FRI").last() / sw).dropna() * 100).ewm(span=4).mean()
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


def breadth_section(sp=None):
    ui.sec("monitor_heart", "Market breadth · S&P 500", "اتساع السوق · إس آند بي 500")
    if sp is None:
        q, _ = data.market_quotes(list(SP500))
        sp = q.rename(columns={"Chg %": "1D"}) if not q.empty else q
        if not sp.empty:
            sp["Sector"] = sp["Symbol"].map(lambda s: SP500.get(s, ("", "Other", ""))[1])
    if sp is None or sp.empty:
        st.info(L("Breadth data unavailable right now.", "بيانات اتساع السوق غير متاحة حالياً."))
        return
    q = data.quotes_df(list(SP500)) if "vs50 %" not in sp else sp
    chg = pd.to_numeric(sp["1D"], errors="coerce").dropna()
    adv, dec = int((chg > 0).sum()), int((chg < 0).sum())
    unch = len(chg) - adv - dec
    pct = adv / max(len(chg), 1) * 100
    a, b, c = st.columns([1, 1.1, 1.2])
    with a:
        mood = L("Bullish breadth", "اتساع إيجابي") if pct > 55 else (L("Bearish breadth", "اتساع سلبي") if pct < 45 else L("Mixed", "متوازن"))
        ui.html(f'<div class="card">{T.pulse_gauge(pct, L("advancing", "صاعدة"), mood)}'
                f'<div style="margin-top:8px">{T.ad_bar(adv, dec, unch)}</div>'
                f'<div style="display:flex;justify-content:space-between;margin-top:8px;font-size:.8rem;font-weight:700;direction:ltr">'
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
        ui.html(f'<div class="card"><div class="muted" style="font-size:.75rem;font-weight:800;letter-spacing:.08em">'
                f'{L("PARTICIPATION", "المشاركة")}</div>{T.progress_bars(items) if items else ""}</div>')
    with c:
        if "Sector" in sp:
            g = sp.assign(up=pd.to_numeric(sp["1D"], errors="coerce") > 0).groupby("Sector")["up"].mean().sort_values(ascending=False) * 100
            ui.html(f'<div class="card"><div class="muted" style="font-size:.75rem;font-weight:800;letter-spacing:.08em">'
                    f'{L("ADVANCING BY SECTOR", "الصاعدة حسب القطاع")}</div>' +
                    T.progress_bars([(sector_name(s_), f"{v:.0f}%", v, T.UP if v >= 50 else T.DOWN) for s_, v in g.items()]) + "</div>")
    ui.chart(charts.change_distribution(chg, L("Distribution of today's moves (S&P 500)", "توزيع حركة الأسهم اليوم (إس آند بي 500)"),
                                        L("Change %", "التغير %"), L("Stocks", "عدد الأسهم")))


# =====================================================================
# OVERVIEW
# =====================================================================
def page_overview():
    px = _tile_prices()
    ticker_tape(px)
    chips = ""
    for s, name in (("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ"), ("^DJI", "DOW"), ("^TNX", "US10Y"), ("GC=F", "GOLD"), ("BTC-USD", "BTC")):
        p, _, c = _last(px, s)
        if p is not None:
            chips += f'<span class="chip"><b>{name}</b>{f"{p:.2f}%" if s == "^TNX" else T.fmt_price(p)} {T.pill(c)}</span>'
    ui.html(T.hero("A.Alturaifi Pro", L("Invest with <b>clarity</b>", "استثمر <b>بوضوح</b>"),
                   L("US market intelligence in one place: live markets, research, screeners, an academy and an automated trading lab.",
                     "كل ما تحتاجه عن السوق الأمريكي في مكان واحد: أسواق مباشرة، أبحاث، فلاتر، أكاديمية، ومختبر تداول آلي."), chips, rtl=is_ar()))
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
            st.dataframe(show.style.map(lambda v: T.signal_style(v, "CALL", "PUT"), subset=[N["Type"]]).format(
                {N["Strike"]: "{:,.2f}", N["Volume"]: "{:,.0f}", N["OI"]: "{:,.0f}", N["Last"]: "{:,.2f}", "IV %": "{:.1f}%", "Vol/OI": "{:.1f}×"}, na_rep="—"),
                hide_index=True, height=420, column_config={"Logo": st.column_config.ImageColumn(" ", width="small")})
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
                st.dataframe(df.rename(columns=ar_cols) if is_ar() else df, hide_index=True, height=min(460, 38 + 35 * len(df)))


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


def page_trending():
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
        cols = st.columns(len(stories))
        for i, (col, n, t) in enumerate(zip(cols, stories, titles)):
            ch = ui.chips(n["tickers"], chg, lg) or f'<span class="muted">{L("Broad market", "السوق بشكل عام")}</span>'
            iq = n.get("iq")
            score = ""
            if iq:
                bg, fg, bd = newsiq.colors(iq["score"])
                lv = newsiq.level(iq["score"])
                score = (f'<span class="iqs" style="background:{bg};color:{fg};border-color:{bd}">{iq["score"]}/10 · {T.esc(L(*lv))}</span>')
            col.markdown(f'<div class="story{" rtl" if is_ar() else ""}">{T.news_thumb(n, big=True)}<div class="rank">0{i + 1}</div>'
                         f'<a class="t" href="{T.esc(n["link"])}" target="_blank">{T.esc(t)}</a>'
                         f'<div class="muted" style="font-size:.78rem;margin-top:6px">{T.esc(n["source"])} · {T.time_ago(n["time"], is_ar())}</div>'
                         f'<div style="margin-top:8px">{score}</div>' + (T.kw_chips(iq, is_ar(), 3) if iq else "") +
                         f'<div class="aff"><span class="lbl" style="width:100%">{L("Affected companies", "الشركات المتأثرة")}</span>{ch}</div></div>',
                         unsafe_allow_html=True)
    else:
        st.caption(L("No trending stories right now.", "لا توجد أخبار رائجة حالياً."))

    ui.sec("summarize", "Market summary", "ملخص السوق")
    ui.html(f'<div class="card{" rtl" if is_ar() else ""}"><ul class="summary">' +
            "".join(f"<li>{T.esc(L(e, a))}</li>" for e, a in summary_points(px, moves, lists)) + "</ul></div>")

    ui.sec("leaderboard", "Movers at a glance", "الأسهم الأكثر حركة")
    keys = list(LISTS)
    for row in (keys[:3], keys[3:]):
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
            st.dataframe(show.style.map(T.color_style, subset=[N["Chg %"]]).format({N["Price"]: "{:,.2f}", N["Chg %"]: "{:+.2f}%", N["Rel Vol"]: "{:.1f}×"}, na_rep="—"),
                         hide_index=True, height=420, column_config={"Logo": st.column_config.ImageColumn(" ", width="small")})
            if fallback:
                st.caption(L("Computed from the top 175 US stocks (screener source unavailable).", "محسوبة من أكبر 175 سهم أمريكي (مصدر القوائم غير متاح حالياً)."))
            ui.open_picker(df["Symbol"].tolist(), f"tr_{kind}", "Open a stock", "افتح سهماً")
    ui.foot()


# =====================================================================
# NEWS
# =====================================================================
def top_stories(k=3):
    """The most important recent stories that name at least one company (importance score, then freshness)."""
    items = [n for n in data.market_news(24)[:400]]
    fresh = [n for n in items if pd.notna(n.get("time")) and n["time"] >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=14)] or items[:60]
    tick = sorted({s_ for n in fresh for s_ in n.get("tickers", [])})
    newsiq.enrich(fresh, data.quick_changes(tick) if tick else {})
    ranked = newsiq.rank([n for n in fresh if n.get("tickers")]) or newsiq.rank(fresh)
    return ranked[:k]


def _ago(ts):
    if not ts:
        return "—"
    m = max(0, (time.time() - ts) / 60)
    return L(f"{int(m)} min ago", f"قبل {int(m)} دقيقة") if m < 60 else L(f"{int(m // 60)} h ago", f"قبل {int(m // 60)} ساعة")


def _refresh_bot():
    try:
        newsbot.bot(wait=False).collect(force=True)
    except Exception:
        pass


def bot_panel(items_24h):
    """Live strip: how many headlines the bot has, from how many outlets, when it last updated; plus the status of every source."""
    try:
        b = newsbot.bot(wait=False)
        health, updated = b.health(), b.updated
    except Exception:
        health, updated = [], None
    live = sum(1 for h in health if h["ok"])
    outlets = len({n.get("source") for n in items_24h})
    c1, c2 = st.columns([5, 1], vertical_alignment="center")
    c1.markdown(f'<div class="botbar"><span class="live"><i></i>{L("News bot · live", "بوت الأخبار · مباشر")}</span>'
                f'<span><b>{len(items_24h):,}</b> {L("headlines in the last 24 hours", "خبراً خلال آخر 24 ساعة")}</span>'
                f'<span><b>{outlets}</b> {L("outlets", "مصدراً")}</span>'
                f'<span>{L("sources working", "مصادر تعمل")}: <b>{live}/{len(health) or len(newsbot.OUTLETS)}</b></span>'
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
    ui.header("newspaper", "Market News", "أخبار السوق",
              "Live headlines collected by the news bot from Reuters, Bloomberg, WSJ, FT, CNBC, Benzinga and 20+ other sources, with keywords, "
              "an importance score from 1 to 10 and the companies affected by each story.",
              "أخبار مباشرة يجمعها بوت الأخبار من رويترز وبلومبرغ ووول ستريت جورنال وفايننشال تايمز وCNBC وبنزينغا وأكثر من 20 مصدراً آخر، "
              "مع الكلمات المفتاحية ودرجة أهمية من 1 إلى 10 والشركات المتأثرة بكل خبر.")
    c1, c2, c3, c4, c5 = st.columns([1.5, 1.25, 1.45, 0.7, 0.9], vertical_alignment="bottom")
    sym = c1.text_input(L("Symbol (leave empty for market news)", "رمز سهم (اتركه فارغاً لأخبار السوق)"), "").strip().upper()
    sort = c2.segmented_control(L("Sort by", "الترتيب"), ["imp", "new"], default="imp", key="nw_sort",
                                format_func=lambda k: L("Most important", "الأهم أولاً") if k == "imp" else L("Latest", "الأحدث")) or "imp"
    lvl = c3.segmented_control(L("Importance", "الأهمية"), [1, 5, 7, 9], default=1, key="nw_min",
                               format_func=lambda v: L("All", "الكل") if v == 1 else f"{v}+") or 1
    count = c4.selectbox(L("Headlines", "عدد الأخبار"), [10, 20, 30, 50, 100], index=1)
    translate = c5.toggle(L("Translate to Arabic", "ترجمة للعربية"), value=is_ar())
    with st.spinner(L("The news bot is collecting headlines from 35 feeds (only the first time)...",
                      "بوت الأخبار يجمع العناوين من 35 مصدراً (أول مرة فقط)...")):
        items = data.symbol_news(sym) if sym else data.market_news(96)
    if not sym:
        now = pd.Timestamp.now(tz="UTC")
        day = [n for n in items if pd.notna(n.get("time")) and n["time"] >= now - pd.Timedelta(hours=24)]
        bot_panel(day)
        d1, d2, d3 = st.columns([1.1, 2.3, 1.6], vertical_alignment="bottom")
        hrs = d1.segmented_control(L("Time", "الوقت"), [1, 6, 24, 96], default=24, key="nw_hrs",
                                   format_func=lambda h: {1: L("1 hour", "ساعة"), 6: L("6 hours", "6 ساعات"), 24: L("24 hours", "24 ساعة"),
                                                          96: L("4 days", "4 أيام")}[h]) or 24
        cats = [c for c in newsbot.CATS if any(n.get("cat") == c for n in items)]
        if isinstance(ss.get("nw_cat"), list):
            ss["nw_cat"] = [c for c in ss["nw_cat"] if c in cats]
        pick_c = d2.pills(L("Category", "التصنيف"), cats, selection_mode="multi", key="nw_cat",
                          format_func=lambda c: L(newsbot.CATS[c][0], newsbot.CATS[c][1])) or []
        outs = sorted({n.get("source") for n in items if n.get("source")}, key=lambda o: (newsbot.RANK.get(o, 99), o))
        ui.valid_multi("nw_src", outs)
        pick_s = d3.multiselect(L("Sources", "المصادر"), outs, key="nw_src", placeholder=L("All sources", "كل المصادر"))
        items = [n for n in items if pd.notna(n.get("time")) and n["time"] >= now - pd.Timedelta(hours=hrs)]
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
        k[0].markdown(T.kpi("newspaper", L("Headlines analysed", "أخبار تم تحليلها"), f"{len(items):,}",
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
    ui.news_list(items, count, translate=translate)
    ui.foot()

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.5"
