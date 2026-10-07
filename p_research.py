"""
p_research.py - Stock · Screener (Finviz-style) · Scanner · Catalyst Pro
"""
import json
import time
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

import charts
import data
import fairvalue as FV
import engine
import holders as HD
import segments as SG
import sharia
import ta
import taxonomy as X
import theme as T
import ui
import universe as U
from i18n import L, industry_name, is_ar, sector_name, sig, theme_name

ss = st.session_state


def spy_daily():
    return data.history("SPY", "2y")


# =====================================================================
# STOCK
# =====================================================================
TF = {"1D": ("5d", "5m"), "5D": ("5d", "15m"), "1M": ("1mo", "60m"), "3M": 63, "6M": 126, "YTD": "ytd",
      "1Y": 252, "5Y": ("5y", "1wk"), "MAX": ("max", "1mo")}
CHART_TYPES = {"Candles": "شموع", "Heikin Ashi": "هايكن آشي", "OHLC": "أعمدة OHLC", "Line": "خط", "Area": "مساحة"}


def quote_header(sym, daily, inf):
    last, prev = daily["Close"].iloc[-1], daily["Close"].iloc[-2]
    chg, pct = last - prev, (last / prev - 1) * 100
    name = inf.get("longName") or inf.get("shortName") or U.name_of(sym)
    exch = inf.get("fullExchangeName") or inf.get("exchange") or ""
    sec = inf.get("sector") or (U.sector_of(sym) if U.known(sym) else "")
    ind = inf.get("industry") or (U.industry_of(sym) if U.known(sym) else "")
    badges = (T.badge(sector_name(sec), "acc", "category") if sec else "") + (T.badge(industry_name(ind), "vio", "factory") if ind else "")
    for tk, sk in X.themes_of(sym)[:2]:
        badges += T.badge(theme_name(tk, sk), "gold", X.THEMES[tk][2])
    uri = data.logos([sym]).get(sym)
    ui.html(f'<div style="display:flex;gap:14px;align-items:center">{T.logo_circle(sym, uri, 58)}<div>'
            f'<div class="q-name"><b style="color:#fff;font-size:1.15rem">{T.esc(name)}</b> · {sym} · {T.esc(exch)}</div><div>{badges}</div></div></div>'
            f'<div style="margin-top:6px"><span class="q-price">{T.fmt_price(last)}</span> <span class="muted">{inf.get("currency", "USD")}</span></div>'
            f'<div><span class="q-chg {T.cls(chg)}">{chg:+,.2f} ({pct:+.2f}%)</span> '
            f'<span class="muted" style="font-size:.85rem">· {daily.index[-1]:%Y-%m-%d} · </span>{T.market_status(is_ar())}</div>')
    return last


def key_stats(daily, inf):
    last = daily["Close"].iloc[-1]
    yr = daily.tail(252)
    lo52, hi52 = yr["Low"].min(), yr["High"].max()
    div = inf.get("dividendRate")

    def f2(k):
        return f"{inf[k]:.2f}" if isinstance(inf.get(k), (int, float)) else "—"
    stats = [
        (L("Open", "الافتتاح"), T.fmt_price(daily["Open"].iloc[-1])), (L("High", "الأعلى"), T.fmt_price(daily["High"].iloc[-1])),
        (L("Low", "الأدنى"), T.fmt_price(daily["Low"].iloc[-1])), (L("Prev close", "الإغلاق السابق"), T.fmt_price(daily["Close"].iloc[-2])),
        (L("Volume", "الحجم"), T.fmt_big(daily["Volume"].iloc[-1])), (L("Avg vol (3M)", "متوسط الحجم"), T.fmt_big(inf.get("averageVolume"))),
        (L("Market cap", "القيمة السوقية"), T.fmt_big(inf.get("marketCap"))), (L("P/E (TTM)", "مكرر الربحية"), f2("trailingPE")),
        (L("Fwd P/E", "المكرر المستقبلي"), f2("forwardPE")), (L("EPS (TTM)", "ربحية السهم"), f2("trailingEps")),
        (L("Beta", "بيتا"), f2("beta")), (L("Div yield", "عائد التوزيعات"), f"{div / last * 100:.2f}%" if div else "—"),
        (L("Short % float", "البيع على المكشوف"), f"{inf['shortPercentOfFloat'] * 100:.1f}%" if inf.get("shortPercentOfFloat") else "—"),
        (L("Shares out", "الأسهم القائمة"), T.fmt_big(inf.get("sharesOutstanding"))),
    ]
    pos = (last - lo52) / (hi52 - lo52) * 100 if hi52 > lo52 else 50
    ui.html('<div class="stats">' + "".join(f'<div class="stat"><div class="l">{l}</div><div class="v">{v}</div></div>'
                                            for l, v in stats) + "</div>"
            f'<div class="muted" style="font-size:.75rem;display:flex;justify-content:space-between;direction:ltr">'
            f'<span>52W Low {T.fmt_price(lo52)}</span><span>52W High {T.fmt_price(hi52)}</span></div>'
            f'<div class="range" style="direction:ltr"><div class="dot" style="left:calc({pos:.1f}% - 8px)"></div></div>')


def chart_tab(sym, daily):
    c1, c2 = st.columns([3, 1.2])
    tf = c1.segmented_control(L("Range", "المدى"), list(TF), default="1Y", key="st_tf", label_visibility="collapsed") or "1Y"
    ctype = c2.selectbox(L("Chart type", "نوع الرسم"), list(CHART_TYPES), format_func=lambda k: L(k, CHART_TYPES[k]),
                         label_visibility="collapsed")
    c3, c4 = st.columns(2)
    overlays = c3.multiselect(L("Overlays", "إضافات على السعر"), charts.OVERLAYS, default=["SMA 20", "SMA 50", "SMA 200"])
    panels = c4.multiselect(L("Indicator panels", "المؤشرات الفنية"), charts.PANELS, default=["RSI", "MACD"])
    spec = TF[tf]
    intraday = tf in ("1D", "5D", "1M")
    if isinstance(spec, int) or spec == "ytd":
        full = ta.add_all(daily)
        d = full[full.index.year == full.index[-1].year] if spec == "ytd" else full.tail(spec)
    else:
        raw = data.history(sym, *spec)
        if raw.empty:
            st.warning(L("Intraday data isn't available for this symbol. Try 3M or longer.",
                         "البيانات اللحظية غير متاحة لهذا الرمز. جرّب 3 أشهر أو أكثر."))
            return
        d = ta.add_all(raw)
        if tf == "1D":
            d = d[d.index.date == d.index[-1].date()]
    if len(d) < 2:
        st.warning(L("Not enough data for this range.", "لا توجد بيانات كافية لهذا المدى."))
        return
    ui.chart(charts.price_chart(d, ctype, overlays, panels, intraday), key="st_chart")


def _counts(t):
    return [(f'{sig("Sell")} {int((t["Signal"] == "Sell").sum())}', "neg"), (f'{sig("Neutral")} {int((t["Signal"] == "Neutral").sum())}', "neu"),
            (f'{sig("Buy")} {int((t["Signal"] == "Buy").sum())}', "pos")]


def technicals_tab(daily):
    d = ta.add_all(daily)
    table, total, label, parts = ta.technical_summary(d)
    if table.empty:
        st.info(L("Not enough data for technical analysis.", "لا توجد بيانات كافية للتحليل الفني."))
        return
    labels = [sig(x) for x in ("Strong Sell", "Sell", "Neutral", "Buy", "Strong Buy")]
    is_ma = table["Indicator"].str.startswith(("EMA", "SMA"))
    osc, mas = parts.get("Oscillators", 0), parts.get("Moving Averages", 0)
    c1, c2, c3 = st.columns(3)
    c1.markdown(T.rating_meter(osc, sig(ta.label_for(osc)), L("Oscillators", "المذبذبات"), _counts(table[~is_ma]), labels), unsafe_allow_html=True)
    c2.markdown(T.rating_meter(total, sig(label), L("Summary", "الملخص"), _counts(table), labels), unsafe_allow_html=True)
    c3.markdown(T.rating_meter(mas, sig(ta.label_for(mas)), L("Moving averages", "المتوسطات المتحركة"), _counts(table[is_ma]), labels),
                unsafe_allow_html=True)

    # ---- performance strip
    ui.sec("trending_up", "Performance", "الأداء")
    c = daily["Close"]
    cells = []
    for lab, n in (("1D", 1), ("1W", 5), ("1M", 21), ("3M", 63), ("6M", 126), ("YTD", "ytd"), ("1Y", 252)):
        if n == "ytd":
            v = data.ytd_change(c)
        else:
            v = (c.iloc[-1] / c.iloc[-1 - n] - 1) * 100 if len(c) > n else np.nan
        if pd.notna(v):
            cells.append(f'<div class="pc2 {T.cls(v)}"><div class="l">{lab}</div><div class="v">{v:+.2f}%</div></div>')
    ui.html('<div class="perfrow">' + "".join(cells) + "</div>")

    # ---- key readings
    last = d.iloc[-1]
    price = float(last["Close"])

    def m(label_, value, kind="neu"):
        return f'<div class="m {kind}"><div class="l">{label_}</div><div class="v">{value}</div></div>'
    rsi = last.get("RSI", np.nan)
    rsi_kind = "pos" if rsi < 30 else ("neg" if rsi > 70 else "neu")
    rsi_note = L("oversold", "تشبع بيعي") if rsi < 30 else (L("overbought", "تشبع شرائي") if rsi > 70 else L("neutral", "محايد"))
    adx = last.get("ADX", np.nan)
    vol_x = last["Volume"] / last["VolAvg20"] if "VolAvg20" in d and last.get("VolAvg20") else np.nan
    s50, s200 = last.get("SMA50", np.nan), last.get("SMA200", np.nan)
    d50 = (price / s50 - 1) * 100 if pd.notna(s50) else np.nan
    d200 = (price / s200 - 1) * 100 if pd.notna(s200) else np.nan
    cards = [m("RSI (14)", f"{rsi:.1f} · {rsi_note}", rsi_kind),
             m(L("Trend strength (ADX)", "قوة الاتجاه ADX"), f"{adx:.0f} · " + (L("strong", "قوي") if adx > 25 else L("weak", "ضعيف")), "neu") if pd.notna(adx) else "",
             m(L("vs SMA 50", "مقابل متوسط 50"), f"{d50:+.2f}%", T.cls(d50)) if pd.notna(d50) else "",
             m(L("vs SMA 200", "مقابل متوسط 200"), f"{d200:+.2f}%", T.cls(d200)) if pd.notna(d200) else "",
             m("ATR (14)", f"{last['ATR']:.2f} · {last['ATR'] / price * 100:.1f}%") if pd.notna(last.get("ATR", np.nan)) else "",
             m(L("Bollinger width", "عرض بولنجر"), f"{last['BB_width'] * 100:.1f}%") if pd.notna(last.get("BB_width", np.nan)) else "",
             m(L("Volume vs 20-day avg", "الحجم مقابل متوسط 20"), f"{vol_x:.2f}×", "pos" if vol_x > 1.2 else "neu") if pd.notna(vol_x) else "",
             m("MACD", f"{last['MACD']:.2f} / {last['MACD_signal']:.2f}", T.cls(last["MACD"] - last["MACD_signal"])) if pd.notna(last.get("MACD", np.nan)) else ""]
    kl, kr = st.columns([1.35, 1])
    with kl:
        ui.sec("insights", "Key readings", "قراءات أساسية")
        ui.html('<div class="mx">' + "".join(cards) + "</div>")
    with kr:
        ui.sec("stacked_line_chart", "Price ladder: pivots & support / resistance", "سلّم الأسعار: الارتكاز والدعوم والمقاومات")
        piv = ta.pivot_points(daily)
        levels = [(k, v, "res" if k.startswith("R") else ("sup" if k.startswith("S") else "piv")) for k, v in piv.items()]
        sw = ta.swing_levels(daily)
        res_ = sorted([x for x in sw if x > price])[:3]
        sup_ = sorted([x for x in sw if x < price], reverse=True)[:3]
        levels += [(L(f"Res {i + 1}", f"مقاومة {i + 1}"), v, "res") for i, v in enumerate(res_)]
        levels += [(L(f"Sup {i + 1}", f"دعم {i + 1}"), v, "sup") for i, v in enumerate(sup_)]
        ui.html(T.ladder(levels, price, L("Price", "السعر")))
        st.caption(L("R = resistance above the price, S = support below it, P = pivot. Distance is from the current price.",
                     "R = مقاومة فوق السعر، S = دعم تحت السعر، P = نقطة الارتكاز. المسافة محسوبة من السعر الحالي."))

    ui.sec("tune", "Indicator signals", "إشارات المؤشرات")
    groups = [(L("Oscillators", "المذبذبات"), "speed", table[~is_ma]),
              (L("EMA moving averages", "المتوسطات الأُسّية EMA"), "show_chart", table[table["Indicator"].str.startswith("EMA")]),
              (L("SMA moving averages", "المتوسطات البسيطة SMA"), "timeline", table[table["Indicator"].str.startswith("SMA")])]
    cols_html = []
    for name, ic, g in groups:
        if g.empty:
            continue
        nb, ns = int((g["Signal"] == "Buy").sum()), int((g["Signal"] == "Sell").sum())
        rows = "".join(f'<div class="sgr"><span class="n">{T.esc(r["Indicator"])}</span><span class="v">{r["Value"]:,.2f}</span>'
                       f'<span class="pill {({"Buy": "pos", "Sell": "neg"}.get(r["Signal"], "neu"))}">{T.esc(sig(r["Signal"]))}</span></div>'
                       for _, r in g.iterrows())
        cols_html.append(f'<div class="sgcol"><div class="sgh">{T.icon(ic)}<b>{T.esc(name)}</b>'
                         f'<span class="ct"><i class="up">{nb} {T.esc(sig("Buy"))}</i><i class="dn">{ns} {T.esc(sig("Sell"))}</i></span></div>'
                         f'<div class="sgth"><span>{L("Indicator", "المؤشر")}</span><span>{L("Value", "القيمة")}</span><span>{L("Signal", "الإشارة")}</span></div>'
                         f'{rows}</div>')
    ui.html('<div class="sgcols">' + "".join(cols_html) + "</div>")


# ---------------------------------------------------------------- financials
FIN_METRICS = {
    "rev": ("Revenue", "الإيرادات", "money"), "gp": ("Gross profit", "إجمالي الربح", "money"),
    "op": ("Operating income", "الدخل التشغيلي", "money"), "ni": ("Net income", "صافي الدخل", "money"),
    "ebitda": ("EBITDA", "EBITDA", "money"), "eps": ("EPS (diluted)", "ربحية السهم", "eps"),
    "gm": ("Gross margin", "الهامش الإجمالي", "pct"), "om": ("Operating margin", "الهامش التشغيلي", "pct"),
    "nm": ("Net margin", "صافي الهامش", "pct"), "roe": ("Return on equity", "العائد على حقوق الملكية", "pct"),
    "roa": ("Return on assets", "العائد على الأصول", "pct"), "ocf": ("Operating cash flow", "التدفق النقدي التشغيلي", "money"),
    "capex": ("Capital expenditure", "الإنفاق الرأسمالي", "money"), "fcf": ("Free cash flow", "التدفق النقدي الحر", "money"),
    "div": ("Dividends paid", "التوزيعات المدفوعة", "money"), "buyback": ("Share buybacks", "إعادة شراء الأسهم", "money"),
    "cash": ("Cash & equivalents", "النقد وما يعادله", "money"), "debt": ("Total debt", "إجمالي الديون", "money"),
    "equity": ("Shareholders' equity", "حقوق المساهمين", "money"), "de": ("Debt / equity", "الديون / حقوق الملكية", "ratio"),
    "cr": ("Current ratio", "نسبة التداول", "ratio"),
}


def _stmt_row(df, *names):
    if not isinstance(df, pd.DataFrame) or df.empty:
        return None
    for n in names:
        if n in df.index:
            s = df.loc[n]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[0]
            s = pd.to_numeric(s, errors="coerce")
            s.index = pd.to_datetime(s.index, errors="coerce")
            s = s[s.index.notna()].sort_index()
            return s if s.notna().any() else None
    return None


def fin_series(stm, freq="a"):
    inc, bal, cf = stm.get(f"inc_{freq}"), stm.get(f"bal_{freq}"), stm.get(f"cf_{freq}")
    r = lambda df, *n: _stmt_row(df, *n)
    out = {"rev": r(inc, "Total Revenue", "Operating Revenue"), "gp": r(inc, "Gross Profit"),
           "op": r(inc, "Operating Income", "EBIT"), "ni": r(inc, "Net Income", "Net Income Common Stockholders"),
           "ebitda": r(inc, "EBITDA", "Normalized EBITDA"), "eps": r(inc, "Diluted EPS", "Basic EPS"),
           "ocf": r(cf, "Operating Cash Flow", "Cash Flow From Continuing Operating Activities"),
           "capex": r(cf, "Capital Expenditure"), "fcf": r(cf, "Free Cash Flow"),
           "div": r(cf, "Cash Dividends Paid", "Common Stock Dividend Paid"),
           "buyback": r(cf, "Repurchase Of Capital Stock", "Common Stock Payments"),
           "cash": r(bal, "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"),
           "debt": r(bal, "Total Debt"), "equity": r(bal, "Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest")}
    assets = r(bal, "Total Assets")
    ca, cl = r(bal, "Current Assets"), r(bal, "Current Liabilities")
    if out["fcf"] is None and out["ocf"] is not None and out["capex"] is not None:
        out["fcf"] = out["ocf"] + out["capex"]
    ann = 4 if freq == "q" else 1
    rev, ni, eq = out["rev"], out["ni"], out["equity"]
    if rev is not None:
        for k, src in (("gm", "gp"), ("om", "op"), ("nm", "ni")):
            if out[src] is not None:
                out[k] = (out[src] / rev.replace(0, np.nan) * 100).dropna()
    if ni is not None and eq is not None:
        out["roe"] = (ni * ann / eq.replace(0, np.nan) * 100).dropna()
    if ni is not None and assets is not None:
        out["roa"] = (ni * ann / assets.replace(0, np.nan) * 100).dropna()
    if out["debt"] is not None and eq is not None:
        out["de"] = (out["debt"] / eq.replace(0, np.nan)).dropna()
    if ca is not None and cl is not None:
        out["cr"] = (ca / cl.replace(0, np.nan)).dropna()
    return {k: v for k, v in out.items() if v is not None and v.notna().any()}


def _period_labels(idx, freq):
    out = []
    for d in idx:
        lab = (f"FY{d.year}" if freq == "a" else f"Q{(d.month - 1) // 3 + 1} {d.year}") if pd.notna(d) else "—"
        while lab in out:
            lab += "'"
        out.append(lab)
    return out


def _fmt_metric(v, kind):
    if v is None or pd.isna(v):
        return "—"
    if kind == "money":
        return ("-" if v < 0 else "") + "$" + T.fmt_big(abs(v))
    if kind == "pct":
        return f"{v:.1f}%"
    if kind == "eps":
        return f"${v:.2f}"
    return f"{v:.2f}"


def _label_key(label):
    import re
    nums = [int(x) for x in re.findall(r"\d+", str(label))]
    if str(label).startswith("FY") and nums:
        return (nums[0], 0)
    return (nums[1], nums[0]) if len(nums) >= 2 else (nums[0] if nums else 0, 0)


def _peers(sym, n=12):
    """Companies in the same sub-industry (S&P 500) or industry (top 175), biggest first."""
    from sp500 import SP500
    out = []
    if sym in SP500:
        sub, sec_ = SP500[sym][2], SP500[sym][1]
        out = [x for x, v in SP500.items() if v[2] == sub and x != sym]
        if len(out) < 4:
            out += [x for x, v in SP500.items() if v[1] == sec_ and x != sym and x not in out]
    elif U.known(sym):
        ind = U.industry_of(sym)
        out = [x for x, v in U.STOCKS.items() if v[2] == ind and x != sym]
    cap = lambda x: U.STOCKS[x][3] if x in U.STOCKS else 0
    return sorted(out, key=lambda x: -cap(x))[:n]


def financials_tab(sym, inf, price=None):
    def pct(k):
        v = inf.get(k)
        return (f"{v * 100:.2f}%", T.cls(v)) if isinstance(v, (int, float)) else ("—", "neu")

    def num(k, dec=2):
        v = inf.get(k)
        return (f"{v:,.{dec}f}", "neu") if isinstance(v, (int, float)) else ("—", "neu")
    big = lambda k: (T.fmt_big(inf.get(k)), "neu")
    # figures from the financial statements are in the currency the company reports in (TSMC: Taiwan dollars): say which
    fc = str(inf.get("financialCurrency") or "USD")
    cur_ = (lambda v: f' <span class="muted" style="font-size:.7em">{fc}</span>' if fc.upper() != "USD" and isinstance(v, (int, float)) else "")
    bigf = lambda k: (T.fmt_big(inf.get(k)) + cur_(inf.get(k)), "neu")
    saved = inf.get("_saved")
    if saved:                                       # Yahoo refused this server: the copy GitHub saved, moved to today's price
        day = _mdy(saved) if isinstance(saved, str) else ""
        st.caption(L(f"Yahoo Finance isn't answering the site right now: these are the figures saved on {day}, with market cap and "
                     "price ratios moved to today's price.",
                     f"ياهو فاينانس ما يرد على الموقع الحين: هذي الأرقام المحفوظة بتاريخ {day}، والقيمة السوقية ومكررات السعر "
                     "محسوبة على سعر اليوم."))
    ui.safe(FV.section, sym, price or inf.get("currentPrice") or inf.get("regularMarketPrice"), "fv_stock")
    groups = {
        ("Valuation", "التقييم", "price_check"): [
            (L("Market cap", "القيمة السوقية"), big("marketCap")), (L("Enterprise value", "قيمة المنشأة"), big("enterpriseValue")),
            ("P/E (TTM)", num("trailingPE")), (L("Forward P/E", "المكرر المستقبلي"), num("forwardPE")), ("PEG", num("trailingPegRatio")),
            ("P/S", num("priceToSalesTrailing12Months")), ("P/B", num("priceToBook")), ("EV/EBITDA", num("enterpriseToEbitda"))],
        ("Profitability", "الربحية", "savings"): [
            (L("Gross margin", "الهامش الإجمالي"), pct("grossMargins")), (L("Operating margin", "الهامش التشغيلي"), pct("operatingMargins")),
            (L("Profit margin", "صافي الهامش"), pct("profitMargins")), ("ROE", pct("returnOnEquity")), ("ROA", pct("returnOnAssets"))],
        ("Growth", "النمو", "trending_up"): [
            (L("Revenue growth", "نمو الإيرادات"), pct("revenueGrowth")), (L("Earnings growth", "نمو الأرباح"), pct("earningsGrowth")),
            (L("Qtr earnings growth", "نمو الأرباح الفصلي"), pct("earningsQuarterlyGrowth")),
            (L("Revenue (TTM)", "الإيرادات"), bigf("totalRevenue")), ("EBITDA", bigf("ebitda"))],
        ("Balance sheet", "الميزانية", "account_balance_wallet"): [
            (L("Total cash", "النقد"), bigf("totalCash")), (L("Total debt", "الديون"), bigf("totalDebt")),
            (L("Debt/Equity", "الديون/الملكية"), num("debtToEquity", 1)), (L("Current ratio", "نسبة التداول"), num("currentRatio")),
            (L("Free cash flow", "التدفق النقدي الحر"), (T.fmt_big(inf.get("freeCashflow")) + cur_(inf.get("freeCashflow")), T.cls(inf.get("freeCashflow"))))],
    }
    cols = st.columns(4)
    for col, ((gen, gar, ic), items) in zip(cols, groups.items()):
        with col:
            ui.sec(ic, gen, gar)
            ui.html('<div class="mx" style="grid-template-columns:1fr">' + "".join(
                f'<div class="m {k}"><div class="l">{l}</div><div class="v">{v}</div></div>' for l, (v, k) in items) + "</div>")

    with st.spinner(L("Loading financial statements...", "جاري تحميل القوائم المالية...")):
        stm = data.statements(sym)
    if all(v.empty for v in stm.values()):
        st.info(L("Financial statements are not available for this symbol.", "القوائم المالية غير متاحة لهذا الرمز."))
        return

    # ---- interactive explorer: click a metric, see its history
    ui.sec("insights", "Interactive metric explorer", "مستكشف المؤشرات التفاعلي")
    a, b = st.columns([5, 1.2], vertical_alignment="bottom")
    freq = b.segmented_control(L("Period", "الفترة"), ["a", "q"], default="a", key="fin_freq",
                               format_func=lambda k: L("Annual", "سنوي") if k == "a" else L("Quarterly", "ربعي")) or "a"
    series = fin_series(stm, freq)
    avail = [k for k in FIN_METRICS if k in series]
    if not avail:
        st.caption(L("No statement data for this period.", "لا توجد بيانات لهذه الفترة."))
    else:
        if ss.get("fin_metric") not in avail:
            ss["fin_metric"] = "rev" if "rev" in avail else avail[0]
        pick = a.pills(L("Choose a metric", "اختر المؤشر"), avail, key="fin_metric", selection_mode="single",
                       format_func=lambda k: L(FIN_METRICS[k][0], FIN_METRICS[k][1])) or avail[0]
        s_ = series[pick]
        en, ar, kind = FIN_METRICS[pick]
        labels_ = _period_labels(s_.index, freq)
        vals = [float(v) if pd.notna(v) else np.nan for v in s_.values]
        note = L(" (annualized)", " (سنوي)") if pick in ("roe", "roa") and freq == "q" else ""
        peers = _peers(sym)
        cmp = ui.multiselect_free(L("Compare with other companies (up to 4)", "قارن مع شركات أخرى (حتى 4)"), peers, "fin_cmp",
                                  L("Pick peers or type any symbol…", "اختر شركات منافسة أو اكتب أي رمز…"), 4)
        cmp = [c_.strip().upper() for c_ in cmp if c_ and c_.strip().upper() != sym][:4]
        if cmp:
            comp, missing = {sym: s_}, []
            with st.spinner(L("Loading the companies to compare...", "جاري تحميل الشركات للمقارنة...")):
                for c_ in cmp:
                    sc = fin_series(data.statements(c_), freq).get(pick)
                    if sc is not None and sc.notna().any():
                        comp[c_] = sc
                    else:
                        missing.append(c_)
            by = {n_: dict(zip(_period_labels(sr.index, freq), [float(v) if pd.notna(v) else None for v in sr.values])) for n_, sr in comp.items()}
            all_labels = sorted({l_ for m_ in by.values() for l_ in m_}, key=_label_key)[-8:]
            ui.chart(charts.compare_bars(all_labels, {n_: [m_.get(l_) for l_ in all_labels] for n_, m_ in by.items()},
                                         L(en, ar) + note + L(" · comparison", " · مقارنة"), kind), key="fin_cmp_chart")
            lg = data.logos(list(comp))
            cards = []
            for i_, (n_, sr) in enumerate(comp.items()):
                vv = sr.dropna()
                lv = float(vv.iloc[-1]) if len(vv) else np.nan
                pv = float(vv.iloc[-2]) if len(vv) > 1 else np.nan
                ch = None if pd.isna(pv) or pv == 0 else ((lv - pv) if kind in ("pct", "ratio") else (lv / abs(pv) - 1) * 100)
                unit_ = L(" pts", " نقطة") if kind in ("pct", "ratio") else "%"
                col_ = charts.PALETTE[i_ % len(charts.PALETTE)]
                cards.append(f'<div class="m" style="border-top:3px solid {col_}">{T.company(n_, "", lg.get(n_), 24, sub=_period_labels(vv.index[-1:], freq)[0] if len(vv) else "", href=ui.href(n_))}'
                             f'<div class="v" style="margin-top:8px;font-size:1.1rem">{_fmt_metric(lv, kind)}</div>'
                             f'<div style="margin-top:4px">{T.pill(ch, suffix=unit_) if ch is not None else ""}</div></div>')
            ui.html('<div class="mx">' + "".join(cards) + "</div>")
            if missing:
                st.caption(L("No data for: ", "لا توجد بيانات لـ: ") + ", ".join(missing))
        else:
            # same design as the comparison chart (value on every bar, $ axis, company legend), even for one company
            ui.chart(charts.compare_bars(labels_, {sym: vals}, L(en, ar) + note, kind), key="fin_chart")
            last_v = vals[-1]
            prev_v = vals[-2] if len(vals) > 1 else np.nan
            yoy_v = vals[-5] if freq == "q" and len(vals) > 4 else (prev_v if freq == "a" else np.nan)

            def chg(x, y):
                if pd.isna(x) or pd.isna(y) or y == 0:
                    return None
                return (x - y) if kind in ("pct", "ratio") else (x / abs(y) - 1) * 100 if y > 0 else (x - y) / abs(y) * 100
            c_prev, c_yoy = chg(last_v, prev_v), chg(last_v, yoy_v)
            unit = L(" pts", " نقطة") if kind in ("pct", "ratio") else "%"
            k1, k2, k3 = st.columns(3)
            k1.markdown(T.kpi("flag", L("Latest", "الأحدث") + f" · {labels_[-1]}", _fmt_metric(last_v, kind), "", T.cls(last_v) if kind != "ratio" else None),
                        unsafe_allow_html=True)
            k2.markdown(T.kpi("swap_vert", L("vs previous period", "مقابل الفترة السابقة"), f"{c_prev:+.1f}{unit}" if c_prev is not None else "—", "",
                              T.cls(c_prev) if c_prev is not None else None), unsafe_allow_html=True)
            k3.markdown(T.kpi("event_repeat", L("vs a year earlier", "مقابل قبل سنة"), f"{c_yoy:+.1f}{unit}" if c_yoy is not None else "—", "",
                              T.cls(c_yoy) if c_yoy is not None else None), unsafe_allow_html=True)

    # ---- cash flow
    ui.sec("payments", "Cash flow", "التدفقات النقدية")
    ca = fin_series(stm, "a")
    ocf, capex, fcf = ca.get("ocf"), ca.get("capex"), ca.get("fcf")
    if ocf is None and fcf is None:
        st.caption(L("Cash flow statement is not available for this symbol.", "قائمة التدفقات النقدية غير متاحة لهذا الرمز."))
    else:
        base = (fcf if fcf is not None else ocf).dropna()
        idx = base.index
        get = lambda s, d: float(s.get(d, np.nan)) if s is not None else np.nan
        last_d = idx[-1]
        rev = ca.get("rev")
        f_last, o_last = get(fcf, last_d), get(ocf, last_d)
        cap = inf.get("marketCap")
        ni_last = get(ca.get("ni"), last_d)
        k = st.columns(5)
        k[0].markdown(T.kpi("account_balance", L("Operating cash flow", "التدفق التشغيلي"), _fmt_metric(o_last, "money"), f"FY{last_d.year}", T.cls(o_last)),
                      unsafe_allow_html=True)
        k[1].markdown(T.kpi("savings", L("Free cash flow", "التدفق النقدي الحر"), _fmt_metric(f_last, "money"), f"FY{last_d.year}", T.cls(f_last)),
                      unsafe_allow_html=True)
        fm = f_last / get(rev, last_d) * 100 if rev is not None and get(rev, last_d) else np.nan
        k[2].markdown(T.kpi("percent", L("FCF margin", "هامش التدفق الحر"), f"{fm:.1f}%" if pd.notna(fm) else "—", L("of revenue", "من الإيرادات"),
                            T.cls(fm) if pd.notna(fm) else None), unsafe_allow_html=True)
        fy = f_last / cap * 100 if cap and pd.notna(f_last) else np.nan
        k[3].markdown(T.kpi("sell", L("FCF yield", "عائد التدفق الحر"), f"{fy:.2f}%" if pd.notna(fy) else "—", L("FCF / market cap", "التدفق / القيمة السوقية"),
                            T.cls(fy) if pd.notna(fy) else None), unsafe_allow_html=True)
        cc = o_last / ni_last if pd.notna(ni_last) and ni_last > 0 and pd.notna(o_last) else np.nan
        k[4].markdown(T.kpi("sync_alt", L("Cash conversion", "جودة الأرباح النقدية"), f"{cc:.2f}×" if pd.notna(cc) else "—",
                            L("operating cash / net income", "النقد التشغيلي / صافي الدخل"), ("pos" if cc >= 1 else "neg") if pd.notna(cc) else None),
                      unsafe_allow_html=True)
        left, right = st.columns([1.25, 1])
        with left:
            per = _period_labels(idx, "a")
            margin = [get(fcf, d) / get(rev, d) * 100 if rev is not None and get(rev, d) else None for d in idx] if fcf is not None else None
            ui.chart(charts.cash_trend(per, [get(ocf, d) for d in idx], [get(capex, d) for d in idx], [get(fcf, d) for d in idx], margin,
                                       L("Cash flow trend", "اتجاه التدفقات النقدية"),
                                       (L("Operating cash flow", "التدفق التشغيلي"), L("Capital expenditure", "الإنفاق الرأسمالي"),
                                        L("Free cash flow", "التدفق النقدي الحر"), L("FCF margin", "هامش التدفق الحر"))), key="cf_trend")
        with right:
            items = []
            if pd.notna(o_last):
                items.append((L("Operating CF", "التشغيلي"), o_last, "relative"))
            cx = get(capex, last_d)
            if pd.notna(cx):
                items.append((L("CapEx", "الإنفاق الرأسمالي"), cx, "relative"))
            items.append((L("Free CF", "التدفق الحر"), 0, "total"))
            for key_, en_, ar_ in (("div", "Dividends", "التوزيعات"), ("buyback", "Buybacks", "إعادة الشراء")):
                v = get(ca.get(key_), last_d)
                if pd.notna(v) and v != 0:
                    items.append((L(en_, ar_), v, "relative"))
            items.append((L("Left over", "المتبقي"), 0, "total"))
            if len(items) > 2:
                ui.chart(charts.cash_waterfall(items, L(f"Where the cash went · FY{last_d.year}", f"أين ذهب النقد · {last_d.year}")), key="cf_wf")
    with st.expander(L("Full financial statements", "القوائم المالية الكاملة"), icon=":material/table_view:"):
        f2 = st.segmented_control(L("Period ", "الفترة "), ["a", "q"], default="a", key="fin_freq2",
                                  format_func=lambda k: L("Annual", "سنوي") if k == "a" else L("Quarterly", "ربعي")) or "a"
        tabs = st.tabs([L("Income statement", "قائمة الدخل"), L("Balance sheet", "الميزانية العمومية"), L("Cash flow", "التدفقات النقدية")])
        for tab, key_ in zip(tabs, ("inc", "bal", "cf")):
            with tab:
                df = stm.get(f"{key_}_{f2}")
                if not isinstance(df, pd.DataFrame) or df.empty:
                    st.caption("—")
                    continue
                num = df.apply(pd.to_numeric, errors="coerce")
                show = num / 1e9
                raw = [i for i in num.index if any(w in str(i) for w in ("EPS", "Per Share", "Rate"))]
                show.loc[raw] = num.loc[raw]
                show.columns = _period_labels(pd.to_datetime(show.columns, errors="coerce"), f2)
                show.index = [str(i) for i in show.index]
                show.index.name = L("Line item", "البند")
                ui.table(show, index=True, height=520, fmt={c: "{:,.2f}" for c in show.columns})
                st.caption(L("Values in billions of USD (EPS and rates as reported).", "القيم بالمليار دولار (ربحية السهم والنسب كما هي)."))


def _optc():
    """Readable option-table column names in the current language."""
    return {"Type": L("Type", "النوع"), "contractSymbol": L("Contract", "العقد"), "strike": L("Strike", "التنفيذ"), "lastPrice": L("Last", "آخر سعر"),
                "bid": L("Bid", "الطلب"), "ask": L("Ask", "العرض"), "percentChange": L("Change %", "التغير %"), "volume": L("Volume", "الحجم"),
                "openInterest": L("Open int.", "العقود المفتوحة"), "impliedVolatility": L("IV %", "التذبذب الضمني %"), "inTheMoney": L("In the money", "داخل السعر")}


def analysts_tab(sym, inf, price):
    """The same analyst view as the Opportunity Hunter: the rating gauge, the price targets, every rating change of the last
    90 days, then earnings (estimate vs actual, the next date) and the insider transactions."""
    import p_scanner as S
    ui.html(S.CSS + (S.RTL_CSS if is_ar() else ""))
    S.analyst_section(sym, price)
    f = data.fundamentals(sym)
    eh = f["earnings_hist"]
    fig = charts.eps_chart(eh, L("EPS: estimate vs actual", "ربحية السهم: المتوقع مقابل الفعلي")) if isinstance(eh, pd.DataFrame) and not eh.empty else None
    if fig is not None or f["earnings_date"] is not None:
        ui.sec("request_quote", "Earnings", "الأرباح")
        c1, c2 = st.columns([2.2, 1])
        if fig is not None:
            ui.chart(fig, key="an_eps", container=c1)
        if f["earnings_date"] is not None:
            nd = pd.Timestamp(f["earnings_date"])
            days = (nd.normalize() - pd.Timestamp.now().normalize()).days
            c2.markdown(T.kpi("event_upcoming", L("Next earnings", "إعلان الأرباح القادم"), f"{nd:%Y-%m-%d}",
                              L(f"in {days} days", f"بعد {days} يوم") if days >= 0 else L("date not confirmed yet", "الموعد لم يتأكد بعد"), "acc"),
                        unsafe_allow_html=True)
    S.insider_section(sym)


REV_CSS = """<style>
.revsrc { position:relative; overflow:hidden; border-radius:20px; border:1px solid rgba(157,151,165,.28); padding:18px 20px 14px; margin:2px 0 12px;
  background:radial-gradient(120% 140% at 100% 0%, rgba(123,69,240,.22), transparent 60%), linear-gradient(160deg,#1A1534,#15102A 60%,#120D22); }
.revsrc .rvhd { display:flex; align-items:baseline; justify-content:space-between; gap:10px; flex-wrap:wrap; }
.revsrc .rvhd b { color:#fff; font-size:1.25rem; font-weight:800; letter-spacing:-.01em; }
.revsrc .rvhd span { color:#9D97A5; font-size:.8rem; }
.revsrc .rvbd { display:flex; align-items:center; gap:26px; margin-top:12px; flex-wrap:wrap; }
.revsrc .rvdn { position:relative; width:184px; height:184px; flex:none; }
.revsrc .rvdn svg { width:100%; height:100%; transform:rotate(-90deg); overflow:visible; }
.revsrc .rvdn .seg { fill:none; stroke-width:24; transition:stroke-width .2s, opacity .2s; animation:revin 1s cubic-bezier(.2,.8,.2,1) both; }
@keyframes revin { from { opacity:0; } }
.revsrc .rvdn .rvc { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }
.revsrc .rvdn .rvc b { color:#fff; font-size:1.02rem; font-weight:800; direction:ltr; unicode-bidi:isolate; }
.revsrc .rvdn .rvc span { color:#9D97A5; font-size:.7rem; margin-top:2px; }
.revsrc .rvlg { flex:1; min-width:220px; display:flex; flex-direction:column; gap:9px; }
.revsrc .rvrow { display:grid; grid-template-columns:14px minmax(0,1fr) auto; align-items:center; gap:10px; }
.revsrc .rvrow .sw { width:14px; height:14px; display:block; }
.revsrc .rvrow .n { color:#E7E3EB; font-size:.92rem; line-height:1.3; }
.revsrc .rvrow .n small { display:block; color:#9D97A5; font-size:.74rem; }
.revsrc .rvrow .p { color:#fff; font-weight:800; font-size:.98rem; direction:ltr; unicode-bidi:isolate; }
.revsrc .rvrow .br { grid-column:2 / 4; height:4px; border-radius:4px; background:rgba(157,151,165,.14); overflow:hidden; margin-top:-4px; direction:ltr; }
.revsrc .rvrow .br svg { display:block; width:100%; height:100%; }
.revsrc .rvft { margin-top:12px; padding-top:10px; border-top:1px solid rgba(157,151,165,.18); color:#9D97A5; font-size:.74rem; }
.revsrc .rvft a { color:#79B8F4; }
@media (max-width: 640px) { .revsrc .rvbd { justify-content:center; } .revsrc .rvlg { min-width:100%; } }
</style>"""
REV_COLORS = ["#E9E4F5", "#A78BFA", "#2DB6EB", "#F5B94A", "#4ADE80", "#F472B6", "#FB923C", "#79B8F4", "#9D97A5"]
REV_KIND = {"product": ("by product line", "حسب المنتجات"), "segment": ("by business segment", "حسب قطاعات الأعمال"),
            "region": ("by region", "حسب المناطق")}
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_AR_ = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]


def revenue_html(seg):
    """Where the revenue comes from: a donut and its lines (the company's own split, from its latest annual report)."""
    rows = sorted(seg["rows"], key=lambda r: -r[1])
    if len(rows) > 8:                                   # the long tail in one "Other" line
        rows = rows[:7] + [("Other", sum(v for _, v in rows[7:]))]
    tot = sum(v for _, v in rows) or 1.0
    names = [n for n, _ in rows]
    if is_ar():
        names = data.translate(["Others" if n == "Other" else n for n in names], budget=6)
    r, circ = 60, 2 * 3.14159265 * 60
    arcs, legend, off = [], [], 0.0
    cur = seg.get("cur") or "USD"
    money = (lambda v: ("$" if cur == "USD" else "") + T.fmt_big(v) + ("" if cur == "USD" else f" {cur}"))
    for i, ((n, v), name) in enumerate(zip(rows, names)):
        col = REV_COLORS[i % len(REV_COLORS)]
        frac = v / tot
        gap = 1.2 if len(rows) > 1 else 0
        arcs.append(f'<circle class="seg" cx="80" cy="80" r="{r}" stroke="{col}" stroke-dasharray="{max(frac * circ - gap, 0.5):.2f} {circ:.2f}" '
                    f'stroke-dashoffset="{-off:.2f}"><title>{T.esc(name)} {frac * 100:.1f}%</title></circle>')
        off += frac * circ
        # the swatch and the bar are drawn like the ring itself, so the light look turns all three into the same colour
        legend.append(f'<div class="rvrow"><svg class="sw" viewBox="0 0 14 14"><rect width="14" height="14" rx="4" fill="{col}"/></svg>'
                      f'<div class="n">{T.esc(name)}<small><bdi dir="ltr">{money(v)}</bdi></small></div>'
                      f'<div class="p">{frac * 100:.1f}%</div><div class="br"><svg viewBox="0 0 100 4" preserveAspectRatio="none">'
                      f'<rect width="{frac * 100:.2f}" height="4" fill="{col}"/></svg></div></div>')
    end = str(seg.get("end") or "")
    try:
        y, mo, _ = end.split("-")
        when = f"{MONTHS_AR_[int(mo) - 1]} {y}" if is_ar() else f"{MONTHS_EN[int(mo) - 1]} {y}"
        fy = f"FY{y}"
    except ValueError:
        when, fy = end, ""
    kind = L(*REV_KIND.get(seg.get("kind"), REV_KIND["segment"]))
    src = (f'{L("From the annual report", "من التقرير السنوي")} (<bdi dir="ltr">{T.esc(seg.get("form", "10-K"))}</bdi>) '
           f'{L("for the year ending", "للسنة المنتهية في")} {T.esc(when)} · '
           f'<a href="{T.esc(seg.get("url", "https://www.sec.gov"))}" target="_blank">SEC</a>')
    return (f'<div class="revsrc"><div class="rvhd"><b>{L("Revenue sources", "مصادر الإيرادات")}</b><span>{kind}</span></div>'
            f'<div class="rvbd"><div class="rvdn"><svg viewBox="0 0 160 160"><circle cx="80" cy="80" r="{r}" fill="none" stroke="rgba(157,151,165,.12)" '
            f'stroke-width="24"/>{"".join(arcs)}</svg><div class="rvc"><b>{money(seg["total"])}</b><span>{L("revenue", "الإيرادات")} {fy}</span></div></div>'
            f'<div class="rvlg">{"".join(legend)}</div></div><div class="rvft">{src}</div></div>')


REV_SW_CSS = """<style>
[class*="st-key-revsw"] { margin:0 0 -4px; }
[class*="st-key-revsw"] [data-testid="stBaseButton-segmented_control"], [class*="st-key-revsw"] [data-testid="stBaseButton-segmented_controlActive"] {
  min-height:30px !important; padding:2px 14px !important; border-radius:999px !important; }
[class*="st-key-revsw"] [data-testid="stBaseButton-segmented_control"] { background:rgba(26,21,52,.7) !important; border-color:rgba(157,151,165,.28) !important; }
[class*="st-key-revsw"] [data-testid="stBaseButton-segmented_control"] p { color:#CCC7D3 !important; font-size:.82rem !important; }
[class*="st-key-revsw"] [data-testid="stBaseButton-segmented_controlActive"] { background:linear-gradient(95deg,#7B45F0,#2DB6EB) !important; border-color:transparent !important; }
[class*="st-key-revsw"] [data-testid="stBaseButton-segmented_controlActive"] p { color:#fff !important; font-size:.82rem !important; font-weight:700 !important; }
</style>"""


def action_card(icon, title, sub, go, on=False):
    """One of the stock page's action cards (its look is in theme.py, .sax): a gradient icon tile, the title and a line under it,
    and a round button at the end (the arrow, or for the watchlist a plus / a tick that turns into a cross under the pointer)."""
    go_html = (f'<span class="ms a">{go}</span><span class="ms h">close</span>' if on else f'<span class="ms a">{go}</span>')
    return (f'<div class="sax{" on" if on else ""}" data-nogq><span class="sx-ic"><span class="ms">{icon}</span></span>'
            f'<span class="sx-tx"><b>{T.esc(title)}</b><span>{T.esc(sub)}</span></span><span class="sx-go">{go_html}</span></div>')


def revenue_section(sym):
    seg = SG.get(sym)
    if not seg:
        return
    if seg.get("alt"):                                  # a business split and a regional one: the visitor picks
        kinds = {"main": seg.get("kind"), "alt": seg["alt"].get("kind")}
        ui.html(REV_SW_CSS)
        with st.container(key="revsw"):
            view = st.segmented_control(L("Split", "التقسيم"), ["main", "alt"], default="main", key=f"rev_view_{sym}",
                                        label_visibility="collapsed",
                                        format_func=lambda k: L("Regions", "المناطق") if kinds[k] == "region"
                                        else L("Business lines", "خطوط الأعمال"))
        if view == "alt":
            seg = {**seg, **seg["alt"]}
    ui.html(REV_CSS + revenue_html(seg))


SH_CSS = """<style>
.shbox { position:relative; overflow:hidden; border-radius:20px; border:1px solid rgba(157,151,165,.28); padding:18px 20px 16px; margin:2px 0 12px;
  background:radial-gradient(120% 140% at 0% 0%, rgba(45,182,235,.16), transparent 60%), linear-gradient(160deg,#1A1534,#15102A 60%,#120D22); }
.shbox .shhd { display:flex; align-items:baseline; justify-content:space-between; gap:10px; flex-wrap:wrap; }
.shbox .shhd b { color:#fff; font-size:1.25rem; font-weight:800; letter-spacing:-.01em; }
.shbox .shhd span { color:#9D97A5; font-size:.8rem; }
.shbox .shbd { display:flex; align-items:center; gap:26px; margin-top:12px; flex-wrap:wrap; }
.shbox .shdn { position:relative; width:170px; height:170px; flex:none; }
.shbox .shdn svg { width:100%; height:100%; overflow:visible; display:block; background:none !important; border:0 !important; box-shadow:none !important; }
.shbox .shdn .seg { fill:none; stroke-width:17; animation:shin 1s cubic-bezier(.2,.8,.2,1) both; }
@keyframes shin { from { opacity:0; } }      /* a fade: Safari can leave an animated dash pattern at its start */
.shbox .shlg { flex:1; min-width:220px; display:flex; flex-direction:column; gap:4px; }
.shbox .shrow { display:grid; grid-template-columns:12px minmax(0,1fr) auto; align-items:center; gap:10px; padding:9px 12px; border-radius:12px; }
.shbox .shrow.top { background:rgba(255,255,255,.05); box-shadow:inset 0 0 0 1px rgba(255,255,255,.06); }
.shbox .shrow .sw { width:12px; height:12px; display:block; }
.shbox .shrow .n { color:#E7E3EB; font-size:.95rem; }
.shbox .shrow .n small { display:block; color:#9D97A5; font-size:.72rem; }
.shbox .shrow .p { color:#fff; font-weight:800; font-size:1rem; direction:ltr; unicode-bidi:isolate; }
.shbox .shkt { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-top:14px; }
.shbox .shk { border-radius:16px; padding:14px 14px 12px; background:rgba(255,255,255,.045); box-shadow:inset 0 0 0 1px rgba(255,255,255,.06); }
.shbox .shk .l { display:flex; align-items:center; gap:10px; color:#E7E3EB; font-size:.95rem; }
.shbox .shk .l i { width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-style:normal; }
.shbox .shk .l .ms { font-size:1.15rem; }
.shbox .shk .v { color:#fff; font-size:1.45rem; font-weight:800; margin-top:10px; direction:ltr; unicode-bidi:isolate; text-align:start; }
.shbox .shk .c { color:#9D97A5; font-size:.8rem; margin-top:4px; line-height:1.35; }
.shbox .shk .c .up { color:#4ADE80; font-weight:700; } .shbox .shk .c .dn { color:#F87171; font-weight:700; }
.shbox .shft { margin-top:12px; padding-top:10px; border-top:1px solid rgba(157,151,165,.18); color:#9D97A5; font-size:.74rem; }
.shtop { display:flex; flex-direction:column; gap:6px; }
.shtop .r { display:grid; grid-template-columns:22px minmax(0,1fr) auto auto; align-items:center; gap:10px; padding:8px 10px; border-radius:12px;
  background:rgba(255,255,255,.035); }
.shtop .r .k { color:#9D97A5; font-size:.78rem; text-align:center; }
.shtop .r .h { color:#E7E3EB; font-size:.88rem; min-width:0; }
.shtop .r .h .nm { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.shtop .r .h small { display:block; color:#9D97A5; font-size:.72rem; }
.shtop .r .h .bar { height:4px; border-radius:4px; background:rgba(157,151,165,.14); margin-top:5px; overflow:hidden; direction:ltr; }
.shtop .r .h .bar svg { display:block; width:100%; height:100%; }
.shtop .r .p { color:#fff; font-weight:800; font-size:.92rem; direction:ltr; unicode-bidi:isolate; }
.shtop .r .ch { font-size:.74rem; font-weight:700; padding:2px 7px; border-radius:999px; direction:ltr; unicode-bidi:isolate; }
.shtop .r .ch.up { color:#4ADE80; background:rgba(34,197,94,.12); } .shtop .r .ch.dn { color:#F87171; background:rgba(239,68,68,.12); }
.shtop .r .ch.eq { color:#9D97A5; background:rgba(157,151,165,.12); }
@media (max-width: 640px) { .shbox .shbd { justify-content:center; } .shbox .shlg { min-width:100%; } }
</style>"""
SH_COLORS = {"inst": "#E2505E", "ins": "#94AE48", "other": "#5B49D9"}      # Webull's ring: institutions red, insiders olive, others indigo
SH_NAMES = {"inst": ("Institutions", "المؤسسات"), "ins": ("Insiders", "المطّلعون"), "other": ("Others", "أخرى")}
SH_SUBS = {"inst": ("funds, banks, pension plans", "صناديق وبنوك وصناديق تقاعد"), "ins": ("executives, directors, 10% owners", "التنفيذيون وأعضاء المجلس وكبار الملاك"),
           "other": ("individual investors and the rest", "المستثمرون الأفراد والباقي")}


def _mdy(d):
    try:
        return datetime.strptime(str(d)[:10], "%Y-%m-%d").strftime("%m/%d/%Y")
    except ValueError:
        return str(d or "")


def _sh_change(d, key, item):
    """The tile's line under the share: its change over a month, else (insiders) their net buying of 6 months."""
    if d is not None:
        if abs(d) < 0.005:
            return L("No change in 1M", "بدون تغيير خلال شهر")
        cls, arrow = ("up", "▲") if d > 0 else ("dn", "▼")
        return (f'<span class="{cls}"><bdi dir="ltr">{arrow} {abs(d):.2f}%</bdi></span> ' + L("in 1M", "خلال شهر"))
    six = item.get("ins6m") or {}
    if key == "ins" and (six.get("buys") or six.get("sells")):       # until a month of history: their trades of 6 months
        b, s_ = six.get("buys") or 0, six.get("sells") or 0
        return L(f"Insiders in 6M: {b} buys · {s_} sales", f"صفقات المطّلعين خلال 6 أشهر: شراء \u2066{b}\u2069 · بيع \u2066{s_}\u2069")
    return L("The monthly change shows after a month of tracking", "التغيّر الشهري يظهر بعد أول شهر من المتابعة")


def holders_html(item):
    """Who owns the company: a donut of institutions / insiders / others, the two shares with their change, and where it
    comes from."""
    parts, over = HD.split(item)
    r, circ = 62, 2 * 3.14159265 * 62
    arcs, rows, off = [], [], 0.0
    top_key = max(parts, key=lambda kv: kv[1])[0]
    for k, v in parts:
        col = SH_COLORS[k]
        frac = v / 100
        if frac > 0:
            gap = 3.0 if sum(1 for _, x in parts if x > 0) > 1 else 0
            arcs.append(f'<circle class="seg" cx="80" cy="80" r="{r}" stroke="{col}" stroke-dasharray="{max(frac * circ - gap, 0.5):.2f} {circ:.2f}" '
                        f'stroke-dashoffset="{-off:.2f}"><title>{T.esc(L(*SH_NAMES[k]))} {v:.2f}%</title></circle>')
            off += frac * circ
        shown = item.get("inst") if (k == "inst" and over) else v
        rows.append(f'<div class="shrow{" top" if k == top_key else ""}"><svg class="sw" viewBox="0 0 12 12"><circle cx="6" cy="6" r="6" fill="{col}"/></svg>'
                    f'<div class="n">{T.esc(L(*SH_NAMES[k]))}<small>{T.esc(L(*SH_SUBS[k]))}</small></div><div class="p">{shown:.2f}%</div></div>')
    rep = item.get("rep")
    when = (f'{L("Update time", "آخر تحديث")}: <bdi dir="ltr">{_mdy(rep)}</bdi>') if rep else ""
    tiles = []
    for k, ic, bg, fg in (("inst", "apartment", "rgba(59,139,235,.18)", "#3B8BEB"), ("ins", "person", "rgba(245,158,66,.18)", "#F59E42")):
        if item.get(k) is None:
            continue
        tiles.append(f'<div class="shk"><div class="l"><i style="background:{bg};color:{fg}"><span class="ms">{ic}</span></i>{T.esc(L(*SH_NAMES[k]))}</div>'
                     f'<div class="v">{item[k]:.2f}%</div><div class="c">{_sh_change(HD.change(item, k), k, item)}</div></div>')
    n = item.get("n")
    src = L("From Yahoo Finance (institutions' 13F filings and insiders' filings)", "من ياهو فاينانس (إفصاحات المؤسسات 13F وإفصاحات المطّلعين)")
    extra = (f' · {L(f"{n:,} institutions hold it", f"تملكه {n:,} مؤسسة")}' if n else "")
    note = (" · " + L("Yahoo counts institutions above 100% (shares lent out are counted twice)",
                      "ياهو يحسب المؤسسات فوق 100% (الأسهم المُقرضة تنحسب مرتين)")) if over else ""
    return (f'<div class="shbox" data-nogq><div class="shhd"><b>{L("Shareholders", "هيكل المساهمين")}</b><span>{when}</span></div>'
            f'<div class="shbd"><div class="shdn"><svg viewBox="0 0 160 160"><g transform="rotate(-90 80 80)">{"".join(arcs)}</g>'
            f'<text x="80" y="80" text-anchor="middle" dominant-baseline="central" fill="#9D97A5" font-size="13" font-weight="500" '
            f'font-family="inherit">{T.esc(L("Shareholders", "المساهمون"))}</text></svg></div>'
            f'<div class="shlg">{"".join(rows)}</div></div><div class="shkt">{"".join(tiles)}</div>'
            f'<div class="shft">{T.esc(src)}{T.esc(extra)}{T.esc(note)}</div></div>')


def top_holders_html(rows):
    """The largest institutional holders: share of the company, a bar, the change in their shares since their last report."""
    if not rows:
        return ""
    big = max((r[1] or 0) for r in rows) or 1
    out = []
    for i, (name, pct, shares, value, chg, dt) in enumerate(rows, 1):
        if chg is None:
            ch = ""
        elif abs(chg) < 0.005:
            ch = f'<span class="ch eq">{L("no change", "بدون تغيير")}</span>'
        else:
            ch = f'<span class="ch {"up" if chg > 0 else "dn"}">{"▲" if chg > 0 else "▼"} {abs(chg):.2f}%</span>'
        val = f'${T.fmt_big(value)}' if value else ""
        al = ' style="text-align:right"' if is_ar() else ""      # the names are English: written left to right, kept on the right in Arabic
        out.append(f'<div class="r"><div class="k">{i}</div><div class="h"><div class="nm" dir="ltr"{al}>{T.esc(name)}</div><small><bdi dir="ltr">{val}</bdi></small>'
                   f'<div class="bar"><svg viewBox="0 0 100 4" preserveAspectRatio="none"><rect width="{(pct or 0) / big * 100:.1f}" height="4" fill="#A78BFA"/></svg></div></div>'
                   f'<div class="p">{(pct or 0):.2f}%</div>{ch}</div>')
    return f'<div class="shtop" data-nogq>{"".join(out)}</div>'


def holders_section(sym):
    item = HD.get(sym)
    if not item:
        return
    ui.html(SH_CSS + holders_html(item))
    if item.get("top"):
        with st.expander(L("Largest institutional holders", "أكبر المؤسسات المالكة"), icon=":material/account_balance:"):
            ui.html(SH_CSS + top_holders_html(item["top"]))
            st.caption(L("The change is in each holder's shares since its previous quarterly report.",
                         "التغيّر في أسهم كل جهة منذ إفصاحها الربعي السابق."))


def company_tab(sym):
    p = data.profile(sym)
    ui.sec("apartment", "Company description", "نبذة عن الشركة")
    summary = p["summary"]
    if summary:
        if is_ar():
            with st.spinner("جاري ترجمة النبذة..."):
                tr = data.translate_long(summary)
            ui.html(f'<div class="card rtl"><div class="desc">{T.esc(tr)}</div></div>')
            if tr == summary:
                st.caption("خدمة الترجمة مشغولة حالياً؛ نعرض النص الأصلي.")
            with st.expander("النص الأصلي بالإنجليزي"):
                st.write(summary)
        else:
            ui.html(f'<div class="card"><div class="desc">{T.esc(summary)}</div></div>')
    else:
        st.caption(L("No description available for this symbol.", "لا توجد نبذة متاحة لهذا الرمز."))
    ui.safe(revenue_section, sym)

    ui.sec("category", "Classification", "التصنيف")
    th = X.themes_of(sym)
    sub = X.SUBIND.get(sym)
    items = [("category", L("Sector", "القطاع"), sector_name(p["sector"]) if p["sector"] else "—"),
             ("factory", L("Industry", "الصناعة"), industry_name(p["industry"]) if p["industry"] else "—"),
             ("account_tree", L("Sub-industry", "الصناعة الفرعية"), L(sub[0], sub[1]) if sub else "—"),
             ("lightbulb", L("Themes", "الثيمات الاستثمارية"), " · ".join(dict.fromkeys(theme_name(t) for t, _ in th)) or "—"),
             ("label", L("Sub-themes", "الثيمات الفرعية"), " · ".join(theme_name(t, s_) for t, s_ in th) or "—"),
             ("location_city", L("Headquarters", "المقر الرئيسي"), p["hq"] or "—"),
             ("groups", L("Employees", "الموظفون"), f"{p['employees']:,}" if p["employees"] else "—"),
             ("person", L("CEO", "الرئيس التنفيذي"), p["ceo"] or "—"),
             ("storefront", L("Exchange", "السوق"), p["exchange"] or "—")]
    web = f'<a href="{T.esc(p["website"])}" target="_blank" style="color:#79B8F4">{T.esc(p["website"])}</a>' if p["website"] else "—"
    ui.html('<div class="prof">' + "".join(f'<div class="it"><div class="l">{T.icon(ic)}{T.esc(l)}</div><div class="v">{T.esc(v)}</div></div>'
                                           for ic, l, v in items)
            + f'<div class="it"><div class="l">{T.icon("language")}{L("Website", "الموقع الإلكتروني")}</div><div class="v">{web}</div></div></div>')
    ui.safe(sharia.section, sym, p.get("industry"))
    if p["officers"]:
        ui.sec("badge", "Key executives", "كبار التنفيذيين")
        off = pd.DataFrame([{L("Name", "الاسم"): o.get("name"), L("Title", "المنصب"): o.get("title"),
                             L("Age", "العمر"): o.get("age")} for o in p["officers"]])
        ui.table(off, fmt={L("Age", "العمر"): "{:,.0f}"}, wrap={L("Title", "المنصب")})
    if p["industry"]:
        peers = [s for s, v in U.STOCKS.items() if v[2] == p["industry"] and s != sym][:8]
        if peers:
            ui.sec("hub", "Peers in the same industry", "شركات منافسة في نفس الصناعة")
            ch = data.changes(peers)
            df = pd.DataFrame([{"Symbol": s, "Name": U.name_of(s), "Price": ch.get(s, (np.nan, np.nan))[0], "Chg %": ch.get(s, (np.nan, np.nan))[1]} for s in peers])
            ui.html(f'<div class="card">{ui.row_list(df, data.logos(peers))}</div>')
    ui.safe(holders_section, sym)                   # who owns it: the last section of the tab


def _max_pain(calls, puts):
    strikes = sorted(set(calls.get("strike", pd.Series(dtype=float))) | set(puts.get("strike", pd.Series(dtype=float))))
    if not strikes:
        return None
    num = lambda df, c: pd.to_numeric(df[c], errors="coerce").fillna(0).to_numpy() if c in df else np.zeros(len(df))
    ck, coi, pk, poi = num(calls, "strike"), num(calls, "openInterest"), num(puts, "strike"), num(puts, "openInterest")
    pain = [(float((coi * np.maximum(k - ck, 0)).sum() + (poi * np.maximum(pk - k, 0)).sum()), k) for k in strikes]
    return min(pain)[1]


def _chain_html(calls, puts, price, n):
    c = calls.set_index("strike") if not calls.empty else pd.DataFrame()
    p = puts.set_index("strike") if not puts.empty else pd.DataFrame()
    strikes = sorted(set(c.index) | set(p.index))
    if not strikes:
        return ""
    atm = min(range(len(strikes)), key=lambda i: abs(strikes[i] - price))
    if n:
        strikes = strikes[max(0, atm - n): atm + n + 1]
    cols = ["bid", "ask", "lastPrice", "percentChange", "volume", "openInterest", "impliedVolatility"]
    hdr = [L("Bid", "العرض"), L("Ask", "الطلب"), L("Last", "آخر"), L("Chg%", "التغير%"), L("Vol", "الحجم"), L("OI", "العقود المفتوحة"), "IV"]

    def cell(df, k, col, side):
        if df.empty or k not in df.index:
            return "<td>—</td>"
        v = df.loc[k, col]
        if isinstance(v, pd.Series):
            v = v.iloc[0]
        itm = (side == "c" and k < price) or (side == "p" and k > price)
        klass = f' class="itm-{side}"' if itm else ""
        if pd.isna(v):
            txt = "—"
        elif col == "impliedVolatility":
            txt = f"{v * 100:.1f}%"
        elif col == "percentChange":
            txt = f'<span class="{T.cls(v)}">{v:+.1f}%</span>'
        elif col in ("volume", "openInterest"):
            txt = f"{int(v):,}"
        else:
            txt = f"{v:,.2f}"
        return f"<td{klass}>{txt}</td>"
    rows = []
    above = False
    for k in strikes:
        atm_cls = ""
        if not above and k >= price:
            atm_cls, above = ' class="atm"', True
        rows.append(f"<tr{atm_cls}>" + "".join(cell(c, k, col, "c") for col in reversed(cols)) + f'<td class="k">{k:,.2f}</td>'
                    + "".join(cell(p, k, col, "p") for col in cols) + "</tr>")
    head = (f'<tr><th class="side" colspan="7" style="color:{T.UP}">{L("CALLS", "عقود الشراء CALL")}</th><th class="side">{L("Strike", "سعر التنفيذ")}</th>'
            f'<th class="side" colspan="7" style="color:{T.DOWN}">{L("PUTS", "عقود البيع PUT")}</th></tr><tr>'
            + "".join(f"<th>{h}</th>" for h in reversed(hdr)) + f'<th style="text-align:center">$</th>' + "".join(f"<th>{h}</th>" for h in hdr) + "</tr>")
    return f'<div class="chainwrap"><table class="chain"><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'


def options_tab(sym, price):
    ui.safe(_options_tab, sym, price)


def _options_tab(sym, price):
    exps = data.expirations(sym)
    if not exps:
        st.info(L("No listed options for this symbol.", "لا توجد عقود خيارات مدرجة لهذا الرمز."), icon=":material/info:")
        return
    today = pd.Timestamp.now().normalize()

    def lab(e):
        d = (pd.Timestamp(e) - today).days
        return f"{pd.Timestamp(e):%b %d, %Y} · {d}{L('d', ' يوم')}"
    c1, c2, c3 = st.columns([1.4, 1, 1])
    exp = c1.selectbox(L("Expiration", "تاريخ الانتهاء"), exps[:24], format_func=lab)
    rng = c2.segmented_control(L("Strikes", "أسعار التنفيذ"), [8, 15, 30, 0], default=15, key="op_rng",
                               format_func=lambda n: L("All", "الكل") if n == 0 else f"±{n}") or 15
    view = c3.segmented_control(L("View", "العرض"), ["chain", "calls", "puts"], default="chain", key="op_view",
                                format_func=lambda v: {"chain": L("T-Chain", "الجدول الكامل"), "calls": "Calls", "puts": "Puts"}[v]) or "chain"
    with st.spinner(L("Loading option chain...", "جاري تحميل سلسلة الخيارات...")):
        calls, puts = data.option_chain(sym, exp)
    if calls.empty and puts.empty:
        st.warning(L("Option chain unavailable right now.", "سلسلة الخيارات غير متاحة حالياً."))
        return
    dte = max((pd.Timestamp(exp) - today).days, 0)
    atm_k = min(set(calls["strike"]) | set(puts["strike"]), key=lambda k: abs(k - price))

    def mid(df, k):
        r = df[df["strike"] == k]
        if r.empty:
            return np.nan
        r = r.iloc[0]
        return (r["bid"] + r["ask"]) / 2 if r["bid"] > 0 and r["ask"] > 0 else r["lastPrice"]
    straddle = np.nansum([mid(calls, atm_k), mid(puts, atm_k)])
    atm_iv = np.nanmean([calls.loc[calls["strike"] == atm_k, "impliedVolatility"].mean(), puts.loc[puts["strike"] == atm_k, "impliedVolatility"].mean()])
    pc_vol = puts["volume"].fillna(0).sum() / max(calls["volume"].fillna(0).sum(), 1)
    pc_oi = puts["openInterest"].fillna(0).sum() / max(calls["openInterest"].fillna(0).sum(), 1)
    mp = _max_pain(calls, puts)
    m = st.columns(6)
    m[0].metric(L("Underlying", "سعر السهم"), f"${price:,.2f}", L(f"{dte} days to expiry", f"{dte} يوم للانتهاء"), delta_color="off")
    m[1].metric(L("ATM implied vol.", "التذبذب الضمني"), f"{atm_iv * 100:.1f}%" if pd.notna(atm_iv) else "—")
    m[2].metric(L("Expected move", "الحركة المتوقعة"), f"±${straddle:,.2f}", f"±{straddle / price * 100:.1f}%", delta_color="off")
    m[3].metric(L("Put/Call volume", "نسبة PUT/CALL حجم"), f"{pc_vol:.2f}")
    m[4].metric(L("Put/Call open int.", "نسبة PUT/CALL عقود"), f"{pc_oi:.2f}")
    m[5].metric(L("Max pain", "نقطة الألم القصوى"), f"${mp:,.2f}" if mp else "—")
    st.caption(L("Expected move = at-the-money straddle price. Max pain = strike where option holders lose the most at expiration. "
                 "Shaded cells are in the money.",
                 "الحركة المتوقعة = سعر الستراديل عند سعر السوق. نقطة الألم القصوى = السعر الذي يخسر عنده حاملو العقود أكثر شيء عند الانتهاء. "
                 "الخانات المظللة داخل السعر (In the money)."))
    if view == "chain":
        ui.html(_chain_html(calls, puts, price, rng))
    else:
        df = calls if view == "calls" else puts
        cols = ["contractSymbol", "strike", "lastPrice", "bid", "ask", "percentChange", "volume", "openInterest", "impliedVolatility", "inTheMoney"]
        df = df[[c for c in cols if c in df]].reset_index(drop=True)
        if rng:
            i = (df["strike"] - price).abs().idxmin()
            pos = df.index.get_loc(i)
            df = df.iloc[max(0, pos - rng): pos + rng + 1]
        df["impliedVolatility"] = df["impliedVolatility"] * 100
        OPT_COLS = _optc()
        ui.table(df.rename(columns=OPT_COLS), pills={OPT_COLS["percentChange"]}, height=560,
                 fmt={OPT_COLS[k]: v for k, v in {"strike": "{:,.2f}", "lastPrice": "{:,.2f}", "bid": "{:,.2f}", "ask": "{:,.2f}", "percentChange": "{:+.1f}%",
                                                   "impliedVolatility": "{:.1f}%", "volume": "{:,.0f}", "openInterest": "{:,.0f}"}.items()})
    a, b = st.columns(2)
    win = lambda d: d[(d["strike"] > price * 0.7) & (d["strike"] < price * 1.3)]
    ui.chart(charts.oi_by_strike(win(calls), win(puts), price, L("Open interest by strike", "العقود المفتوحة حسب سعر التنفيذ"),
                                 (L("Calls", "شراء"), L("Puts", "بيع"))), key=f"oi_{sym}", container=a)
    ui.chart(charts.iv_smile(win(calls), win(puts), price, L("Implied volatility smile", "منحنى التذبذب الضمني"),
                             (L("Calls IV", "تذبذب الشراء"), L("Puts IV", "تذبذب البيع"))), key=f"iv_{sym}", container=b)
    ui.sec("local_fire_department", "Most active contracts", "العقود الأكثر تداولاً")
    act = pd.concat([calls.assign(Type="CALL"), puts.assign(Type="PUT")], ignore_index=True)
    act = act.sort_values("volume", ascending=False).head(10)[["Type", "contractSymbol", "strike", "lastPrice", "percentChange", "volume", "openInterest", "impliedVolatility"]]
    act["impliedVolatility"] = act["impliedVolatility"] * 100
    OPT_COLS = _optc()
    ui.table(act.rename(columns=OPT_COLS), pills={OPT_COLS["percentChange"]}, words={OPT_COLS["Type"]: ("CALL", "PUT")},
             fmt={OPT_COLS[k]: v for k, v in {"strike": "{:,.2f}", "lastPrice": "{:,.2f}", "percentChange": "{:+.1f}%", "impliedVolatility": "{:.1f}%",
                                               "volume": "{:,.0f}", "openInterest": "{:,.0f}"}.items()})


def page_stock():
    sym = ss.symbol
    with st.spinner(L(f"Loading {sym}...", f"جاري تحميل {sym}...")):
        daily = data.history(sym, "2y")
    if daily.empty or len(daily) < 3:
        st.error(L(f"No data found for {sym}. Use the search box at the top.", f"لا توجد بيانات للرمز {sym}. استخدم البحث في الأعلى."))
        return
    inf = data.info(sym)
    h1, h2 = st.columns([3, 1.2])                  # room for the action cards' titles on one line
    with h1:
        price = quote_header(sym, daily, inf)
    with h2, st.container(key="stkact"):
        # three action cards, each in its own colour: the watchlist star (a toggle), the hunter's analysis, the paper ticket.
        # The card is HTML; an invisible button over it takes the tap (its label still names it for screen readers)
        inwl = sym in ss.watchlist
        with st.container(key="stkact_wl_on" if inwl else "stkact_wl"):
            ui.html(action_card("star", L("In watchlist", "في المتابعة") if inwl else L("Add to watchlist", "أضف للمتابعة"),
                                L("Tap to remove it", "اضغط لإزالته") if inwl else L("Follow it in the sidebar", "تابعه من القائمة الجانبية"),
                                "check" if inwl else "add", on=inwl))
            if st.button(L("In watchlist", "في المتابعة") if inwl else L("Add to watchlist", "أضف للمتابعة"), width="stretch",
                         key="stk_wl", help=L("Tap to remove it from the watchlist", "اضغط لإزالته من المتابعة") if inwl else
                         L("Follow it in the sidebar watchlist", "تابعه في قائمة المتابعة الجانبية")):
                if inwl:
                    ss.watchlist.remove(sym)
                else:
                    ss.watchlist.append(sym)
                st.rerun()
        arrow = "arrow_back" if is_ar() else "arrow_forward"
        with st.container(key="stkact_hn"):
            ui.html(action_card("radar", L("Opportunity Hunter", "صائد الفرص"),
                                L("Score, entry, stop and target", "التقييم والدخول والوقف والهدف"), arrow))
            if st.button(L("Opportunity Hunter", "صائد الفرص"), width="stretch", key="stk_hn",
                         help=L("Its full setup analysis: score, entry, stop and target", "تحليل الفرصة الكامل: التقييم والدخول والوقف والهدف")):
                ss["hn_look"] = ss["hn_look_in"] = sym      # the Scanner opens this stock's full analysis
                ui.goto("scanner")
        with st.container(key="stkact_pf"):
            ui.html(action_card("account_balance_wallet", L("Paper trade", "تداول افتراضي"),
                                L("Buy or short it with virtual money", "اشترِه أو بعه على المكشوف بفلوس افتراضية"), arrow))
            if st.button(L("Paper trade", "تداول افتراضي"), width="stretch", key="stk_pf",
                         help=L("Buy or sell it short with virtual money", "اشترِه أو بعه على المكشوف بفلوس افتراضية")):
                ss["pf_sym"] = sym                          # the paper portfolio's ticket opens on this stock
                ui.goto("pf_trade")
    key_stats(daily, inf)
    tabs = st.tabs([L(":material/candlestick_chart: Chart", ":material/candlestick_chart: الرسم البياني"),
                    L(":material/apartment: Company", ":material/apartment: عن الشركة"),
                    L(":material/speed: Technicals", ":material/speed: التحليل الفني"),
                    L(":material/request_quote: Financials", ":material/request_quote: المالية"),
                    L(":material/groups: Analysts", ":material/groups: المحللون"),
                    L(":material/tune: Options", ":material/tune: الخيارات"),
                    L(":material/newspaper: News", ":material/newspaper: الأخبار")])
    with tabs[0]:
        ui.safe(chart_tab, sym, daily)
    with tabs[1]:
        ui.safe(company_tab, sym)
    with tabs[2]:
        ui.safe(technicals_tab, daily)
    with tabs[3]:
        ui.safe(financials_tab, sym, inf, float(price))
    with tabs[4]:
        ui.safe(analysts_tab, sym, inf, price)
    with tabs[5]:
        options_tab(sym, float(price))
    with tabs[6]:
        ui.safe(ui.news_list, data.symbol_news(sym, 20), 20)
    ui.foot()


# =====================================================================
# SCREENER (Finviz-style)
# =====================================================================
def _o(en, ar, *filters):
    return (en, ar, list(filters))


F = {  # key -> (en, ar, group, [options]); groups: desc / fund / tech = Yahoo's live screener, l* = computed here after the screen
    # ---------------- descriptive
    "mcap": ("Market cap", "القيمة السوقية", "desc", [_o("Any", "الكل"), _o("Mega (>200B)", "عملاقة (>200 مليار)", ("gt", "intradaymarketcap", 2e11)),
             _o("Large (10–200B)", "كبيرة (10–200 مليار)", ("btwn", "intradaymarketcap", 1e10, 2e11)),
             _o("Mid (2–10B)", "متوسطة (2–10 مليار)", ("btwn", "intradaymarketcap", 2e9, 1e10)),
             _o("Small (0.3–2B)", "صغيرة (0.3–2 مليار)", ("btwn", "intradaymarketcap", 3e8, 2e9)),
             _o("Micro (<300M)", "متناهية الصغر (<300 مليون)", ("lt", "intradaymarketcap", 3e8)),
             _o("+Large (over 10B)", "+كبيرة (أكثر من 10 مليار)", ("gt", "intradaymarketcap", 1e10)),
             _o("+Mid (over 2B)", "+متوسطة (أكثر من 2 مليار)", ("gt", "intradaymarketcap", 2e9)),
             _o("+Small (over 300M)", "+صغيرة (أكثر من 300 مليون)", ("gt", "intradaymarketcap", 3e8)),
             _o("-Small (under 2B)", "-صغيرة (أقل من 2 مليار)", ("lt", "intradaymarketcap", 2e9))]),
    "exch": ("Exchange", "البورصة", "desc", [_o("Any", "الكل"), _o("NASDAQ", "ناسداك", ("eq", "exchange", "NMS")), _o("NYSE", "بورصة نيويورك", ("eq", "exchange", "NYQ")),
             _o("NYSE American", "نيويورك أمريكان", ("eq", "exchange", "ASE"))]),
    "index": ("Index", "المؤشر", "ldesc", [_o("Any", "الكل"), _o("S&P 500", "إس آند بي 500"), _o("Dow Jones 30", "داو جونز 30"), _o("Not in S&P 500", "خارج إس آند بي 500")]),
    "price": ("Price", "السعر", "desc", [_o("Any", "الكل"), _o("Under $5", "أقل من 5$", ("lt", "intradayprice", 5)),
              _o("$5–20", "5–20$", ("btwn", "intradayprice", 5, 20)), _o("$20–50", "20–50$", ("btwn", "intradayprice", 20, 50)),
              _o("$50–100", "50–100$", ("btwn", "intradayprice", 50, 100)), _o("Over $100", "أكثر من 100$", ("gt", "intradayprice", 100)),
              _o("Under $1", "أقل من 1$", ("lt", "intradayprice", 1)), _o("Under $10", "أقل من 10$", ("lt", "intradayprice", 10)),
              _o("Over $10", "أكثر من 10$", ("gt", "intradayprice", 10)), _o("Over $20", "أكثر من 20$", ("gt", "intradayprice", 20)),
              _o("Over $50", "أكثر من 50$", ("gt", "intradayprice", 50)), _o("Over $500", "أكثر من 500$", ("gt", "intradayprice", 500))]),
    "avgvol": ("Avg volume", "متوسط الحجم", "desc", [_o("Any", "الكل"), _o("Over 100K", "أكثر من 100 ألف", ("gt", "avgdailyvol3m", 1e5)),
               _o("Over 500K", "أكثر من 500 ألف", ("gt", "avgdailyvol3m", 5e5)), _o("Over 1M", "أكثر من مليون", ("gt", "avgdailyvol3m", 1e6)),
               _o("Over 5M", "أكثر من 5 ملايين", ("gt", "avgdailyvol3m", 5e6)), _o("Under 100K", "أقل من 100 ألف", ("lt", "avgdailyvol3m", 1e5)),
               _o("Over 2M", "أكثر من 2 مليون", ("gt", "avgdailyvol3m", 2e6)), _o("Over 10M", "أكثر من 10 ملايين", ("gt", "avgdailyvol3m", 1e7))]),
    "curvol": ("Current volume", "حجم اليوم", "desc", [_o("Any", "الكل"), _o("Over 100K", "أكثر من 100 ألف", ("gt", "dayvolume", 1e5)),
               _o("Over 500K", "أكثر من 500 ألف", ("gt", "dayvolume", 5e5)), _o("Over 1M", "أكثر من مليون", ("gt", "dayvolume", 1e6)),
               _o("Over 5M", "أكثر من 5 ملايين", ("gt", "dayvolume", 5e6)), _o("Over 10M", "أكثر من 10 ملايين", ("gt", "dayvolume", 1e7))]),
    "relvol": ("Relative volume", "الحجم النسبي", "ldesc", [_o("Any", "الكل"), _o("Over 1.5", "أكثر من 1.5"), _o("Over 2", "أكثر من 2"), _o("Over 3", "أكثر من 3"),
               _o("Under 0.5", "أقل من 0.5")]),
    "div": ("Dividend yield", "عائد التوزيعات", "desc", [_o("Any", "الكل"), _o("None (0%)", "بدون توزيعات", ("lt", "forward_dividend_yield", 0.01)),
            _o("Positive (>0%)", "يوزع (>0%)", ("gt", "forward_dividend_yield", 0)), _o("Over 2%", "أكثر من 2%", ("gt", "forward_dividend_yield", 2)),
            _o("Over 4%", "أكثر من 4%", ("gt", "forward_dividend_yield", 4)), _o("Over 1%", "أكثر من 1%", ("gt", "forward_dividend_yield", 1)),
            _o("Over 3%", "أكثر من 3%", ("gt", "forward_dividend_yield", 3)), _o("Over 5%", "أكثر من 5%", ("gt", "forward_dividend_yield", 5)),
            _o("Over 8%", "أكثر من 8%", ("gt", "forward_dividend_yield", 8))]),
    "divgrow": ("Dividend growth (years)", "سنوات نمو التوزيعات", "desc", [_o("Any", "الكل"),
                _o("5+ years", "5 سنوات أو أكثر", ("gt", "consecutive_years_of_dividend_growth_count", 4)),
                _o("10+ years", "10 سنوات أو أكثر", ("gt", "consecutive_years_of_dividend_growth_count", 9)),
                _o("25+ years (aristocrats)", "25 سنة أو أكثر (الأرستقراطيون)", ("gt", "consecutive_years_of_dividend_growth_count", 24))]),
    "beta": ("Beta", "بيتا", "desc", [_o("Any", "الكل"), _o("Under 0.5", "أقل من 0.5", ("lt", "beta", 0.5)),
             _o("0.5–1", "0.5–1", ("btwn", "beta", 0.5, 1)), _o("1–1.5", "1–1.5", ("btwn", "beta", 1, 1.5)), _o("Over 1.5", "أكثر من 1.5", ("gt", "beta", 1.5)),
             _o("Over 2", "أكثر من 2", ("gt", "beta", 2))]),
    "short": ("Short float", "البيع على المكشوف", "desc", [_o("Any", "الكل"), _o("Over 5%", "أكثر من 5%", ("gt", "short_percentage_of_float.value", 5)),
              _o("Over 10%", "أكثر من 10%", ("gt", "short_percentage_of_float.value", 10)),
              _o("Over 20%", "أكثر من 20%", ("gt", "short_percentage_of_float.value", 20)),
              _o("Low (<5%)", "منخفض (<5%)", ("lt", "short_percentage_of_float.value", 5)),
              _o("Over 15%", "أكثر من 15%", ("gt", "short_percentage_of_float.value", 15)),
              _o("Over 30%", "أكثر من 30%", ("gt", "short_percentage_of_float.value", 30))]),
    "dtc": ("Days to cover", "أيام التغطية", "desc", [_o("Any", "الكل"), _o("Over 3", "أكثر من 3", ("gt", "days_to_cover_short.value", 3)),
            _o("Over 5", "أكثر من 5", ("gt", "days_to_cover_short.value", 5)), _o("Over 10", "أكثر من 10", ("gt", "days_to_cover_short.value", 10))]),
    "insider": ("Insider ownership", "ملكية المطلعين", "desc", [_o("Any", "الكل"), _o("Over 10%", "أكثر من 10%", ("gt", "pctheldinsider", 10)),
                _o("Over 30%", "أكثر من 30%", ("gt", "pctheldinsider", 30)), _o("Over 50%", "أكثر من 50%", ("gt", "pctheldinsider", 50)),
                _o("Under 1%", "أقل من 1%", ("lt", "pctheldinsider", 1))]),
    "inst": ("Institutional ownership", "ملكية المؤسسات", "desc", [_o("Any", "الكل"), _o("Over 50%", "أكثر من 50%", ("gt", "pctheldinst", 50)),
             _o("Over 70%", "أكثر من 70%", ("gt", "pctheldinst", 70)), _o("Over 90%", "أكثر من 90%", ("gt", "pctheldinst", 90)),
             _o("Under 10%", "أقل من 10%", ("lt", "pctheldinst", 10))]),
    "recom": ("Analyst recom.", "توصية المحللين", "ldesc", [_o("Any", "الكل"), _o("Strong Buy (≤1.5)", "شراء قوي (≤1.5)"), _o("Buy or better (≤2)", "شراء أو أفضل (≤2)"),
              _o("Hold or better (≤3)", "احتفاظ أو أفضل (≤3)"), _o("Sell or worse (>3.5)", "بيع أو أسوأ (>3.5)")]),
    # ---------------- fundamental
    "pe": ("P/E", "مكرر الربحية", "fund", [_o("Any", "الكل"), _o("Low (0–15)", "منخفض (0–15)", ("btwn", "peratio.lasttwelvemonths", 0, 15)),
           _o("15–25", "15–25", ("btwn", "peratio.lasttwelvemonths", 15, 25)), _o("25–50", "25–50", ("btwn", "peratio.lasttwelvemonths", 25, 50)),
           _o("High (>50)", "مرتفع (>50)", ("gt", "peratio.lasttwelvemonths", 50)), _o("Profitable (>0)", "رابح (>0)", ("gt", "peratio.lasttwelvemonths", 0)),
           _o("Under 10", "أقل من 10", ("btwn", "peratio.lasttwelvemonths", 0, 10)), _o("Under 20", "أقل من 20", ("btwn", "peratio.lasttwelvemonths", 0, 20)),
           _o("Under 30", "أقل من 30", ("btwn", "peratio.lasttwelvemonths", 0, 30)), _o("Over 30", "أكثر من 30", ("gt", "peratio.lasttwelvemonths", 30))]),
    "fpe": ("Forward P/E", "المكرر المستقبلي", "lfund", [_o("Any", "الكل"), _o("Profitable (>0)", "رابح (>0)"), _o("Under 10", "أقل من 10"), _o("Under 15", "أقل من 15"),
            _o("Under 20", "أقل من 20"), _o("Under 30", "أقل من 30"), _o("Over 30", "أكثر من 30"), _o("Over 50", "أكثر من 50")]),
    "peg": ("PEG", "PEG", "fund", [_o("Any", "الكل"), _o("Under 1", "أقل من 1", ("btwn", "pegratio_5y", 0, 1)),
            _o("1–2", "1–2", ("btwn", "pegratio_5y", 1, 2)), _o("Over 2", "أكثر من 2", ("gt", "pegratio_5y", 2)), _o("Under 2", "أقل من 2", ("btwn", "pegratio_5y", 0, 2))]),
    "ps": ("P/S", "السعر/المبيعات", "fund", [_o("Any", "الكل"), _o("Under 1", "أقل من 1", ("btwn", "lastclosemarketcaptotalrevenue.lasttwelvemonths", 0, 1)),
           _o("Under 2", "أقل من 2", ("btwn", "lastclosemarketcaptotalrevenue.lasttwelvemonths", 0, 2)),
           _o("Under 5", "أقل من 5", ("btwn", "lastclosemarketcaptotalrevenue.lasttwelvemonths", 0, 5)),
           _o("Under 10", "أقل من 10", ("btwn", "lastclosemarketcaptotalrevenue.lasttwelvemonths", 0, 10)),
           _o("Over 10", "أكثر من 10", ("gt", "lastclosemarketcaptotalrevenue.lasttwelvemonths", 10))]),
    "pb": ("P/B", "السعر/القيمة الدفترية", "fund", [_o("Any", "الكل"), _o("Under 1", "أقل من 1", ("btwn", "pricebookratio.quarterly", 0, 1)),
           _o("1–3", "1–3", ("btwn", "pricebookratio.quarterly", 1, 3)), _o("Over 3", "أكثر من 3", ("gt", "pricebookratio.quarterly", 3)),
           _o("Under 2", "أقل من 2", ("btwn", "pricebookratio.quarterly", 0, 2)), _o("Over 5", "أكثر من 5", ("gt", "pricebookratio.quarterly", 5))]),
    "evebitda": ("EV/EBITDA", "قيمة المنشأة/EBITDA", "fund", [_o("Any", "الكل"), _o("Under 5", "أقل من 5", ("btwn", "lastclosetevebitda.lasttwelvemonths", 0, 5)),
                 _o("Under 10", "أقل من 10", ("btwn", "lastclosetevebitda.lasttwelvemonths", 0, 10)),
                 _o("Under 15", "أقل من 15", ("btwn", "lastclosetevebitda.lasttwelvemonths", 0, 15)),
                 _o("Over 20", "أكثر من 20", ("gt", "lastclosetevebitda.lasttwelvemonths", 20))]),
    "roe": ("ROE", "العائد على الملكية", "fund", [_o("Any", "الكل"), _o("Over 10%", "أكثر من 10%", ("gt", "returnonequity.lasttwelvemonths", 10)),
            _o("Over 20%", "أكثر من 20%", ("gt", "returnonequity.lasttwelvemonths", 20)), _o("Negative", "سالب", ("lt", "returnonequity.lasttwelvemonths", 0)),
            _o("Positive", "إيجابي", ("gt", "returnonequity.lasttwelvemonths", 0)), _o("Over 30%", "أكثر من 30%", ("gt", "returnonequity.lasttwelvemonths", 30))]),
    "roa": ("ROA", "العائد على الأصول", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "returnonassets.lasttwelvemonths", 0)),
            _o("Over 5%", "أكثر من 5%", ("gt", "returnonassets.lasttwelvemonths", 5)), _o("Over 10%", "أكثر من 10%", ("gt", "returnonassets.lasttwelvemonths", 10)),
            _o("Over 15%", "أكثر من 15%", ("gt", "returnonassets.lasttwelvemonths", 15)), _o("Negative", "سالب", ("lt", "returnonassets.lasttwelvemonths", 0))]),
    "roi": ("ROIC", "العائد على رأس المال", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "returnontotalcapital.lasttwelvemonths", 0)),
            _o("Over 10%", "أكثر من 10%", ("gt", "returnontotalcapital.lasttwelvemonths", 10)),
            _o("Over 15%", "أكثر من 15%", ("gt", "returnontotalcapital.lasttwelvemonths", 15)),
            _o("Over 20%", "أكثر من 20%", ("gt", "returnontotalcapital.lasttwelvemonths", 20))]),
    "epsg": ("EPS growth (TTM)", "نمو ربحية السهم", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "epsgrowth.lasttwelvemonths", 0)),
             _o("Over 10%", "أكثر من 10%", ("gt", "epsgrowth.lasttwelvemonths", 10)), _o("Over 25%", "أكثر من 25%", ("gt", "epsgrowth.lasttwelvemonths", 25)),
             _o("Negative", "سالب", ("lt", "epsgrowth.lasttwelvemonths", 0)), _o("Over 50%", "أكثر من 50%", ("gt", "epsgrowth.lasttwelvemonths", 50))]),
    "sales1y": ("Sales growth (1Y)", "نمو المبيعات (سنة)", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "totalrevenues1yrgrowth.lasttwelvemonths", 0)),
                _o("Over 5%", "أكثر من 5%", ("gt", "totalrevenues1yrgrowth.lasttwelvemonths", 5)),
                _o("Over 10%", "أكثر من 10%", ("gt", "totalrevenues1yrgrowth.lasttwelvemonths", 10)),
                _o("Over 20%", "أكثر من 20%", ("gt", "totalrevenues1yrgrowth.lasttwelvemonths", 20)),
                _o("Over 30%", "أكثر من 30%", ("gt", "totalrevenues1yrgrowth.lasttwelvemonths", 30)),
                _o("Negative", "سالب", ("lt", "totalrevenues1yrgrowth.lasttwelvemonths", 0))]),
    "revg": ("Revenue growth (Q)", "نمو الإيرادات الفصلي", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "quarterlyrevenuegrowth.quarterly", 0)),
             _o("Over 10%", "أكثر من 10%", ("gt", "quarterlyrevenuegrowth.quarterly", 10)), _o("Over 25%", "أكثر من 25%", ("gt", "quarterlyrevenuegrowth.quarterly", 25)),
             _o("Negative", "سالب", ("lt", "quarterlyrevenuegrowth.quarterly", 0))]),
    "nig": ("Net income growth (1Y)", "نمو صافي الربح (سنة)", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "netincome1yrgrowth.lasttwelvemonths", 0)),
            _o("Over 10%", "أكثر من 10%", ("gt", "netincome1yrgrowth.lasttwelvemonths", 10)),
            _o("Over 25%", "أكثر من 25%", ("gt", "netincome1yrgrowth.lasttwelvemonths", 25)),
            _o("Negative", "سالب", ("lt", "netincome1yrgrowth.lasttwelvemonths", 0))]),
    "fcfg": ("FCF growth (1Y)", "نمو التدفق النقدي الحر", "fund", [_o("Any", "الكل"),
             _o("Positive", "إيجابي", ("gt", "leveredfreecashflow1yrgrowth.lasttwelvemonths", 0)),
             _o("Over 20%", "أكثر من 20%", ("gt", "leveredfreecashflow1yrgrowth.lasttwelvemonths", 20))]),
    "gm": ("Gross margin", "الهامش الإجمالي", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "grossprofitmargin.lasttwelvemonths", 0)),
           _o("Over 20%", "أكثر من 20%", ("gt", "grossprofitmargin.lasttwelvemonths", 20)), _o("Over 40%", "أكثر من 40%", ("gt", "grossprofitmargin.lasttwelvemonths", 40)),
           _o("Over 60%", "أكثر من 60%", ("gt", "grossprofitmargin.lasttwelvemonths", 60)), _o("Over 80%", "أكثر من 80%", ("gt", "grossprofitmargin.lasttwelvemonths", 80))]),
    "ebitdam": ("EBITDA margin", "هامش EBITDA", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "ebitdamargin.lasttwelvemonths", 0)),
                _o("Over 10%", "أكثر من 10%", ("gt", "ebitdamargin.lasttwelvemonths", 10)), _o("Over 20%", "أكثر من 20%", ("gt", "ebitdamargin.lasttwelvemonths", 20)),
                _o("Over 30%", "أكثر من 30%", ("gt", "ebitdamargin.lasttwelvemonths", 30)), _o("Negative", "سالب", ("lt", "ebitdamargin.lasttwelvemonths", 0))]),
    "margin": ("Net margin", "صافي الهامش", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "netincomemargin.lasttwelvemonths", 0)),
               _o("Over 10%", "أكثر من 10%", ("gt", "netincomemargin.lasttwelvemonths", 10)), _o("Over 20%", "أكثر من 20%", ("gt", "netincomemargin.lasttwelvemonths", 20)),
               _o("Negative", "سالب", ("lt", "netincomemargin.lasttwelvemonths", 0)), _o("Over 30%", "أكثر من 30%", ("gt", "netincomemargin.lasttwelvemonths", 30))]),
    "de": ("Debt/Equity", "الديون/الملكية", "fund", [_o("Any", "الكل"), _o("Under 50%", "أقل من 50%", ("lt", "totaldebtequity.lasttwelvemonths", 50)),
           _o("Under 100%", "أقل من 100%", ("lt", "totaldebtequity.lasttwelvemonths", 100)), _o("Over 100%", "أكثر من 100%", ("gt", "totaldebtequity.lasttwelvemonths", 100)),
           _o("Under 10%", "أقل من 10%", ("lt", "totaldebtequity.lasttwelvemonths", 10)), _o("Over 200%", "أكثر من 200%", ("gt", "totaldebtequity.lasttwelvemonths", 200))]),
    "ltde": ("LT Debt/Equity", "الديون طويلة الأجل/الملكية", "fund", [_o("Any", "الكل"), _o("Under 10%", "أقل من 10%", ("lt", "ltdebtequity.lasttwelvemonths", 10)),
             _o("Under 50%", "أقل من 50%", ("lt", "ltdebtequity.lasttwelvemonths", 50)), _o("Under 100%", "أقل من 100%", ("lt", "ltdebtequity.lasttwelvemonths", 100)),
             _o("Over 100%", "أكثر من 100%", ("gt", "ltdebtequity.lasttwelvemonths", 100))]),
    "cr": ("Current ratio", "نسبة التداول", "fund", [_o("Any", "الكل"), _o("Under 1", "أقل من 1", ("lt", "currentratio.lasttwelvemonths", 1)),
           _o("Over 1", "أكثر من 1", ("gt", "currentratio.lasttwelvemonths", 1)), _o("Over 1.5", "أكثر من 1.5", ("gt", "currentratio.lasttwelvemonths", 1.5)),
           _o("Over 2", "أكثر من 2", ("gt", "currentratio.lasttwelvemonths", 2)), _o("Over 3", "أكثر من 3", ("gt", "currentratio.lasttwelvemonths", 3))]),
    "qr": ("Quick ratio", "النسبة السريعة", "fund", [_o("Any", "الكل"), _o("Under 0.5", "أقل من 0.5", ("lt", "quickratio.lasttwelvemonths", 0.5)),
           _o("Over 1", "أكثر من 1", ("gt", "quickratio.lasttwelvemonths", 1)), _o("Over 1.5", "أكثر من 1.5", ("gt", "quickratio.lasttwelvemonths", 1.5)),
           _o("Over 2", "أكثر من 2", ("gt", "quickratio.lasttwelvemonths", 2))]),
    "ndebt": ("Net debt/EBITDA", "صافي الدين/EBITDA", "fund", [_o("Any", "الكل"), _o("Net cash (<0)", "نقد صافٍ (<0)", ("lt", "netdebtebitda.lasttwelvemonths", 0)),
              _o("Under 1", "أقل من 1", ("lt", "netdebtebitda.lasttwelvemonths", 1)), _o("Under 2", "أقل من 2", ("lt", "netdebtebitda.lasttwelvemonths", 2)),
              _o("Under 3", "أقل من 3", ("lt", "netdebtebitda.lasttwelvemonths", 3)), _o("Over 3", "أكثر من 3", ("gt", "netdebtebitda.lasttwelvemonths", 3))]),
    "icov": ("Interest coverage", "تغطية الفوائد", "fund", [_o("Any", "الكل"), _o("Over 3×", "أكثر من 3 مرات", ("gt", "ebitinterestexpense.lasttwelvemonths", 3)),
             _o("Over 5×", "أكثر من 5 مرات", ("gt", "ebitinterestexpense.lasttwelvemonths", 5)),
             _o("Over 10×", "أكثر من 10 مرات", ("gt", "ebitinterestexpense.lasttwelvemonths", 10)),
             _o("Under 1.5× (weak)", "أقل من 1.5 مرة (ضعيف)", ("lt", "ebitinterestexpense.lasttwelvemonths", 1.5))]),
    "altman": ("Altman Z-score", "مؤشر ألتمان Z", "fund", [_o("Any", "الكل"),
               _o("Safe (>3)", "آمن (>3)", ("gt", "altmanzscoreusingtheaveragestockinformationforaperiod.lasttwelvemonths", 3)),
               _o("Grey zone (1.8–3)", "منطقة رمادية (1.8–3)", ("btwn", "altmanzscoreusingtheaveragestockinformationforaperiod.lasttwelvemonths", 1.8, 3)),
               _o("Distress (<1.8)", "خطر (<1.8)", ("lt", "altmanzscoreusingtheaveragestockinformationforaperiod.lasttwelvemonths", 1.8))]),
    "fcf": ("Free cash flow", "التدفق النقدي الحر", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "leveredfreecashflow.lasttwelvemonths", 0)),
            _o("Negative", "سالب", ("lt", "leveredfreecashflow.lasttwelvemonths", 0)), _o("Over $1B", "أكثر من مليار$", ("gt", "leveredfreecashflow.lasttwelvemonths", 1e9))]),
    # ---------------- technical
    "chg": ("Change today", "التغير اليوم", "tech", [_o("Any", "الكل"), _o("Up", "صاعد", ("gt", "percentchange", 0)), _o("Up > 3%", "صاعد > 3%", ("gt", "percentchange", 3)),
            _o("Up > 5%", "صاعد > 5%", ("gt", "percentchange", 5)), _o("Down", "نازل", ("lt", "percentchange", 0)),
            _o("Down > 3%", "نازل > 3%", ("lt", "percentchange", -3)), _o("Down > 5%", "نازل > 5%", ("lt", "percentchange", -5)),
            _o("Up > 10%", "صاعد > 10%", ("gt", "percentchange", 10)), _o("Down > 10%", "نازل > 10%", ("lt", "percentchange", -10))]),
    "perf52": ("52W performance", "أداء 52 أسبوع", "tech", [_o("Any", "الكل"), _o("Up", "صاعد", ("gt", "fiftytwowkpercentchange", 0)),
               _o("Over +20%", "أكثر من +20%", ("gt", "fiftytwowkpercentchange", 20)), _o("Over +50%", "أكثر من +50%", ("gt", "fiftytwowkpercentchange", 50)),
               _o("Down", "نازل", ("lt", "fiftytwowkpercentchange", 0)), _o("Over +100%", "أكثر من +100%", ("gt", "fiftytwowkpercentchange", 100)),
               _o("Down > 20%", "نازل > 20%", ("lt", "fiftytwowkpercentchange", -20)), _o("Down > 50%", "نازل > 50%", ("lt", "fiftytwowkpercentchange", -50))]),
    "perfw": ("Performance (week)", "الأداء (أسبوع)", "local", [_o("Any", "الكل"), _o("Up", "صاعد"), _o("Up > 5%", "صاعد > 5%"), _o("Up > 10%", "صاعد > 10%"),
              _o("Down", "نازل"), _o("Down > 5%", "نازل > 5%"), _o("Down > 10%", "نازل > 10%")]),
    "perfm": ("Performance (month)", "الأداء (شهر)", "local", [_o("Any", "الكل"), _o("Up", "صاعد"), _o("Up > 10%", "صاعد > 10%"), _o("Up > 20%", "صاعد > 20%"),
              _o("Down", "نازل"), _o("Down > 10%", "نازل > 10%"), _o("Down > 20%", "نازل > 20%")]),
    "perfq": ("Performance (quarter)", "الأداء (ربع سنة)", "local", [_o("Any", "الكل"), _o("Up", "صاعد"), _o("Up > 20%", "صاعد > 20%"), _o("Up > 50%", "صاعد > 50%"),
              _o("Down", "نازل"), _o("Down > 20%", "نازل > 20%")]),
    "perfytd": ("Performance (YTD)", "الأداء منذ بداية العام", "local", [_o("Any", "الكل"), _o("Up", "صاعد"), _o("Up > 20%", "صاعد > 20%"), _o("Up > 50%", "صاعد > 50%"),
                _o("Down", "نازل"), _o("Down > 20%", "نازل > 20%")]),
    "volat": ("Volatility (annual)", "التذبذب (سنوي)", "local", [_o("Any", "الكل"), _o("Under 20%", "أقل من 20%"), _o("20–40%", "20–40%"), _o("Over 40%", "أكثر من 40%"),
              _o("Over 60%", "أكثر من 60%")]),
    "atr": ("ATR (% of price)", "متوسط المدى الحقيقي (% من السعر)", "local", [_o("Any", "الكل"), _o("Under 2%", "أقل من 2%"), _o("Over 2%", "أكثر من 2%"),
            _o("Over 4%", "أكثر من 4%"), _o("Over 6%", "أكثر من 6%")]),
    "gap": ("Gap today", "فجوة اليوم", "local", [_o("Any", "الكل"), _o("Gap up", "فجوة صاعدة"), _o("Gap up > 3%", "فجوة صاعدة > 3%"), _o("Gap down", "فجوة هابطة"),
            _o("Gap down > 3%", "فجوة هابطة > 3%")]),
    "sma20": ("SMA 20", "متوسط 20", "local", [_o("Any", "الكل"), _o("Price above", "السعر فوقه"), _o("Price below", "السعر تحته")]),
    "sma50": ("SMA 50", "متوسط 50", "local", [_o("Any", "الكل"), _o("Price above", "السعر فوقه"), _o("Price below", "السعر تحته")]),
    "sma200": ("SMA 200", "متوسط 200", "local", [_o("Any", "الكل"), _o("Price above", "السعر فوقه"), _o("Price below", "السعر تحته")]),
    "cross": ("SMA 50 vs SMA 200", "متوسط 50 مقابل 200", "local", [_o("Any", "الكل"), _o("50 above 200 (uptrend)", "50 فوق 200 (اتجاه صاعد)"),
              _o("50 below 200 (downtrend)", "50 تحت 200 (اتجاه هابط)")]),
    "high52": ("52W high", "القمة السنوية", "local", [_o("Any", "الكل"), _o("Within 5%", "ضمن 5%"), _o("Within 10%", "ضمن 10%"), _o("More than 30% below", "أقل منها بأكثر من 30%"),
               _o("New high (within 1%)", "قمة جديدة (ضمن 1%)")]),
    "low52": ("52W low", "القاع السنوي", "local", [_o("Any", "الكل"), _o("Within 5%", "ضمن 5%"), _o("Within 10%", "ضمن 10%"), _o("More than 50% above", "أعلى منه بأكثر من 50%")]),
    "rsi": ("RSI (14)", "RSI (14)", "local", [_o("Any", "الكل"), _o("Oversold (<30)", "تشبع بيعي (<30)"), _o("Overbought (>70)", "تشبع شرائي (>70)"),
            _o("Neutral (40–60)", "محايد (40–60)"), _o("Under 40", "أقل من 40"), _o("Over 60", "أكثر من 60")]),
}
LOCAL_GROUPS = ("local", "ldesc", "lfund")          # filters computed here (not by Yahoo's screener)
SORTS = {"intradaymarketcap": ("Market cap", "القيمة السوقية", False), "percentchange": ("Change %", "التغير %", False),
         "dayvolume": ("Volume", "الحجم", False), "peratio.lasttwelvemonths": ("P/E (low first)", "مكرر الربحية (الأقل)", True),
         "forward_dividend_yield": ("Dividend yield", "عائد التوزيعات", False),
         "short_percentage_of_float.value": ("Short float", "البيع على المكشوف", False),
         "fiftytwowkpercentchange": ("52W performance", "أداء 52 أسبوع", False)}
PRESETS = {
    "custom": ("Custom", "مخصص", {}),
    "gainers": ("Top gainers (large caps)", "الأكثر ارتفاعاً (شركات كبيرة)", {"mcap": 2, "chg": 1}),
    "highs": ("Near 52-week high", "قرب القمة السنوية", {"mcap": 2, "high52": 1, "sma50": 1}),
    "oversold": ("Oversold large caps", "شركات كبيرة في تشبع بيعي", {"mcap": 2, "rsi": 1}),
    "dividend": ("Dividend payers > 4%", "توزيعات أكثر من 4%", {"div": 4, "mcap": 2}),
    "shorts": ("High short interest", "بيع على المكشوف مرتفع", {"short": 2, "avgvol": 3}),
    "value": ("Undervalued growth", "نمو بتقييم منخفض", {"pe": 1, "epsg": 2, "revg": 1}),
    "ai": ("AI leaders", "قادة الذكاء الاصطناعي", {"theme": "ai"}),
    "nuclear": ("Clean energy & nuclear", "الطاقة النظيفة والنووية", {"theme": "power"}),
}


# backup screener: when Yahoo's live screener refuses the server (e.g. HTTP 401), filter our own universe with live batch quotes
LOCAL_FIELDS = {"intradaymarketcap": "Mkt Cap", "intradayprice": "Price", "avgdailyvol3m": "Avg Vol", "peratio.lasttwelvemonths": "P/E",
                "pricebookratio.quarterly": "P/B", "forward_dividend_yield": "Div %", "percentchange": "Chg %",
                "fiftytwowkpercentchange": "52W %"}
LOCAL_SORT = {"intradaymarketcap": "Mkt Cap", "percentchange": "Chg %", "dayvolume": "Volume", "peratio.lasttwelvemonths": "P/E",
              "forward_dividend_yield": "Div %", "fiftytwowkpercentchange": "52W %"}
_LIVE_DOWN = {"until": 0.0, "err": ""}


def _field_label(field):
    for en, ar, _, opts in F.values():
        if any(f[1] == field for o in opts for f in o[2]):
            return L(en, ar)
    return field


def _local_screen(filters, sort, asc, size):
    """(DataFrame, skipped filter fields) from the S&P 500 + top 175 with live quotes; (None, []) if quotes are unavailable."""
    from sp500 import SP500
    syms = list(dict.fromkeys(list(U.US_UNIVERSE) + list(SP500)))
    try:
        raw = data._quotes(tuple(syms))
    except Exception:
        return None, []
    df = _fix52(data._quotes_df(raw))
    if df.empty:
        return None, []
    keep, skipped = _eval_local(df, filters)
    return _sort_local(df[keep], sort, asc).head(size).reset_index(drop=True), skipped


def _fix52(df):
    """Some versions of Yahoo's quote send the 52-week change as a fraction: as a percent like the rest."""
    if not df.empty and "52W %" in df and df["52W %"].notna().sum() > 5 and pd.to_numeric(df["52W %"], errors="coerce").abs().median() < 1.5:
        df["52W %"] = pd.to_numeric(df["52W %"], errors="coerce") * 100
    return df


def _sort_local(df, sort, asc):
    sc = LOCAL_SORT.get(sort, "Mkt Cap")
    return df.sort_values(sc, ascending=asc, na_position="last") if sc in df else df


def _eval_local(df, filters):
    """(rows that pass, filter fields that can't be checked here) for screener filters checked on live quotes."""
    meta = data.classify(df["Symbol"].tolist(), limit=0)
    sec_ = df["Symbol"].map(lambda x: meta.get(x, (None, None))[0] or U.sector_of(x))
    ind_ = df["Symbol"].map(lambda x: meta.get(x, (None, None))[1] or U.industry_of(x))
    keep = pd.Series(True, index=df.index)
    skipped = []
    for f in filters:
        op, field, *vals = f
        if field in ("region", "exchange"):
            continue
        if op == "or_eq":
            keep &= (sec_ if field == "sector" else ind_).isin(list(vals[0]))
            continue
        if op == "eq" and field in ("sector", "industry"):
            keep &= (sec_ if field == "sector" else ind_) == vals[0]
            continue
        col = LOCAL_FIELDS.get(field)
        if col is None or col not in df:
            skipped.append(field)
            continue
        v = pd.to_numeric(df[col], errors="coerce")
        m = v > vals[0] if op == "gt" else (v < vals[0] if op == "lt" else ((v >= vals[0]) & (v <= vals[1]) if op == "btwn" else None))
        if m is not None:
            keep &= m.fillna(False)
    return keep, list(dict.fromkeys(skipped))


def _theme_passing(qdf, filters):
    """(symbols of the theme that pass every Yahoo filter, error, symbols that couldn't be checked).
    One screen over the theme's sectors, between its smallest and largest company; when Yahoo's 250-row window comes back
    full, each company still outside it is asked about on its own (its sector, a narrow band around its market cap), so a
    company is kept only when Yahoo's screener says it passes."""
    caps = pd.to_numeric(qdf["Mkt Cap"], errors="coerce") if "Mkt Cap" in qdf else pd.Series(np.nan, index=qdf.index)
    cap_of = dict(zip(qdf["Symbol"], caps))
    secs = {t: U.sector_of(t) for t in qdf["Symbol"]}
    known = sorted(set(secs.values()) - {"Other"})
    q = list(filters)
    if known and all(v != "Other" for v in secs.values()):
        q.append(["or_eq", "sector", known])
    if caps.notna().any():
        q.append(["btwn", "intradaymarketcap", float(caps.min()) * 0.9, float(caps.max()) * 1.1])
    first, err = data.screen_custom(q, "intradaymarketcap", False, 250)
    if err:
        return set(), err, []
    passed = set(first["Symbol"]) if not first.empty else set()
    unsure = []
    if len(first) >= 250:
        for t in qdf["Symbol"]:
            if t in passed:
                continue
            c = cap_of.get(t)
            if c is None or not np.isfinite(c) or c <= 0:
                unsure.append(t)
                continue
            qq = list(filters) + ([["eq", "sector", secs[t]]] if secs[t] != "Other" else []) + [["btwn", "intradaymarketcap", c * 0.97, c * 1.03]]
            d2, e2 = data.screen_custom(qq, "intradaymarketcap", False, 250)
            if e2:
                unsure.append(t)
            elif not d2.empty and t in set(d2["Symbol"]):
                passed.add(t)
    return passed, None, unsure


def _theme_screen(theme_syms, filters, sort, asc):
    """(DataFrame, error, source, skipped filters, unchecked symbols) for an investment theme: exactly its own companies,
    with live quotes, each one kept only if it passes every chosen filter."""
    try:
        raw = data._quotes(tuple(theme_syms))
    except Exception:
        raw = []
    df = _fix52(data._quotes_df(raw))
    source = "live"
    if df.empty:                                         # quotes unavailable: the last daily prices
        ch = data.changes(tuple(theme_syms))
        df = pd.DataFrame([{"Symbol": t, "Name": U.name_of(t), "Price": ch[t][0], "Chg %": ch[t][1]} for t in theme_syms if t in ch])
        source = "history"
        if df.empty:
            return df, None, source, [], []
    df = df[df["Symbol"].isin(theme_syms)].drop_duplicates("Symbol")
    df["Name"] = [n if isinstance(n, str) and n and n != t else U.name_of(t) for t, n in zip(df["Symbol"], df.get("Name", df["Symbol"]))]
    err, skipped, unsure = None, [], []
    if filters:
        passed, err, unsure = _theme_passing(df, filters) if source == "live" else (set(), "quotes", [])
        if err:                                          # Yahoo's screener refused: check what the quotes can, list the rest
            keep, skipped = _eval_local(df, filters)
            df = df[keep]
        else:
            df = df[df["Symbol"].isin(passed)]
    return _sort_local(df, sort, asc).reset_index(drop=True), err, source, skipped, unsure


def _reset_filters():
    """Every filter back to 'Any' and a fresh screen."""
    for k in F:
        ss[f"sf_{k}"] = 0
    ss["sf_sector"], ss["sf_industry"], ss["sf_theme"], ss["sf_subtheme"] = "Any", "Any", "Any", "Any"
    ss["sc_preset"] = "custom"
    ss["sc_q"] = ""
    ss.pop("screen", None)


def _apply_preset():
    p = PRESETS[ss.sc_preset][2]
    for k in F:
        ss[f"sf_{k}"] = p.get(k, 0)
    ss["sf_theme"] = p.get("theme", "Any")
    ss["sf_subtheme"] = "Any"


def _num(df, col):
    return pd.to_numeric(df[col], errors="coerce") if col in df else pd.Series(np.nan, index=df.index)


def _rating_value(v):
    """'1.9 - Buy' -> 1.9"""
    try:
        return float(str(v).split("-")[0].strip())
    except (TypeError, ValueError):
        return np.nan


def _pre_filters(df):
    """Filters answered from the screen's own columns (index membership, relative volume, analyst rating, forward P/E,
    moving averages and 52-week range) - they work on every row."""
    from sp500 import DOW30, SP500
    g = lambda k: ss.get(f"sf_{k}", 0)
    px = _num(df, "Price")
    keep = pd.Series(True, index=df.index)
    if g("index"):
        member = df["Symbol"].isin(set(SP500)) if g("index") in (1, 3) else df["Symbol"].isin(set(DOW30))
        keep &= ~member if g("index") == 3 else member
    if g("relvol"):
        rv = _num(df, "Volume") / _num(df, "Avg Vol")
        keep &= {1: rv > 1.5, 2: rv > 2, 3: rv > 3, 4: rv < 0.5}[g("relvol")].fillna(False)
    if g("recom"):
        r = df["Rating"].map(_rating_value) if "Rating" in df else pd.Series(np.nan, index=df.index)
        keep &= {1: r <= 1.5, 2: r <= 2, 3: r <= 3, 4: r > 3.5}[g("recom")].fillna(False)
    if g("fpe"):
        f = _num(df, "Fwd P/E")
        keep &= {1: f > 0, 2: f.between(0, 10), 3: f.between(0, 15), 4: f.between(0, 20), 5: f.between(0, 30), 6: f > 30, 7: f > 50}[g("fpe")].fillna(False)
    for k, col in (("sma50", "SMA50"), ("sma200", "SMA200")):
        if g(k) and col in df:
            m = _num(df, col)
            keep &= ((px > m) if g(k) == 1 else (px < m)).fillna(False)
    if g("cross") and "SMA50" in df and "SMA200" in df:
        keep &= ((_num(df, "SMA50") > _num(df, "SMA200")) if g("cross") == 1 else (_num(df, "SMA50") < _num(df, "SMA200"))).fillna(False)
    if g("high52") and "52W High" in df:
        dist = px / _num(df, "52W High") - 1
        keep &= {1: dist >= -0.05, 2: dist >= -0.10, 3: dist < -0.30, 4: dist >= -0.01}[g("high52")].fillna(False)
    if g("low52") and "52W Low" in df:
        up = px / _num(df, "52W Low") - 1
        keep &= {1: up <= 0.05, 2: up <= 0.10, 3: up > 0.50}[g("low52")].fillna(False)
    return df[keep]


def _local_filters(df):   # kept for compatibility with older saved state
    return _pre_filters(df)


TECH_KEYS = ("perfw", "perfm", "perfq", "perfytd", "volat", "atr", "gap", "sma20", "rsi")


def _post_filters(df):
    """Filters that need price history (performance, volatility, ATR, gap, SMA 20, RSI)."""
    g = lambda k: ss.get(f"sf_{k}", 0)
    keep = pd.Series(True, index=df.index)
    perf = {"perfw": ("Perf W", {1: (0, None), 2: (5, None), 3: (10, None), 4: (None, 0), 5: (None, -5), 6: (None, -10)}),
            "perfm": ("Perf M", {1: (0, None), 2: (10, None), 3: (20, None), 4: (None, 0), 5: (None, -10), 6: (None, -20)}),
            "perfq": ("Perf 3M", {1: (0, None), 2: (20, None), 3: (50, None), 4: (None, 0), 5: (None, -20)}),
            "perfytd": ("Perf YTD", {1: (0, None), 2: (20, None), 3: (50, None), 4: (None, 0), 5: (None, -20)})}
    for k, (col, rules) in perf.items():
        if g(k) and col in df:
            lo, hi = rules[g(k)]
            v = _num(df, col)
            keep &= ((v > lo) if lo is not None else (v < hi)).fillna(False)
    if g("volat") and "Volatility" in df:
        v = _num(df, "Volatility")
        keep &= {1: v < 20, 2: v.between(20, 40), 3: v > 40, 4: v > 60}[g("volat")].fillna(False)
    if g("atr") and "ATR %" in df:
        v = _num(df, "ATR %")
        keep &= {1: v < 2, 2: v > 2, 3: v > 4, 4: v > 6}[g("atr")].fillna(False)
    if g("gap") and "Gap %" in df:
        v = _num(df, "Gap %")
        keep &= {1: v > 0, 2: v > 3, 3: v < 0, 4: v < -3}[g("gap")].fillna(False)
    if g("sma20") and "SMA20" in df:
        keep &= ((_num(df, "Last") > _num(df, "SMA20")) if g("sma20") == 1 else (_num(df, "Last") < _num(df, "SMA20"))).fillna(False)
    if g("rsi") and "RSI" in df:
        v = _num(df, "RSI")
        keep &= {1: v < 30, 2: v > 70, 3: v.between(40, 60), 4: v < 40, 5: v > 60}[g("rsi")].fillna(False)
    return df[keep]


def _technicals(symbols):
    hist = data.history_many(tuple(symbols), "1y")
    rows = []
    for s, df in hist.items():
        if len(df) < 30:
            continue
        c = df["Close"]
        perf = lambda n: (c.iloc[-1] / c.iloc[-n - 1] - 1) * 100 if len(c) > n else np.nan
        vol = c.pct_change().tail(21).std() * np.sqrt(252) * 100
        atr, gap = np.nan, np.nan
        if {"High", "Low"} <= set(df.columns):
            tr = pd.concat([df["High"] - df["Low"], (df["High"] - c.shift()).abs(), (df["Low"] - c.shift()).abs()], axis=1).max(axis=1)
            atr = float(tr.tail(14).mean() / c.iloc[-1] * 100)
        if "Open" in df.columns and len(c) > 1:
            gap = float((df["Open"].iloc[-1] / c.iloc[-2] - 1) * 100)
        rows.append({"Symbol": s, "Perf W": perf(5), "Perf M": perf(21), "Perf 3M": perf(63),
                     "Perf YTD": data.ytd_change(c),
                     "RSI": float(ta.rsi(c).iloc[-1]), "Volatility": vol, "ATR %": atr, "Gap %": gap,
                     "SMA20": float(c.tail(20).mean()), "Last": float(c.iloc[-1]), "_spark": c.tail(60).values})
    return pd.DataFrame(rows)


def _theme_opts():
    return ["Any"] + list(X.THEMES)


def _share_view(df, total, group_name):
    """Revenue market share inside the chosen group: donut + ranked cards."""
    d = df.dropna(subset=["Revenue"]).sort_values("Revenue", ascending=False)
    top = d.head(8)
    labels = list(top["Symbol"])
    values = list(top["Revenue"])
    rest = d["Revenue"].iloc[8:].sum()
    if rest > 0:
        labels.append(L("Others", "أخرى"))
        values.append(rest)
    hover = ["$" + T.fmt_big(v) for v in values]
    left, right = st.columns([1.1, 1])
    with left:
        ui.chart(charts.share_donut(labels, values, L(f"Revenue market share · {group_name}", f"الحصة السوقية من الإيرادات · {group_name}"),
                                    f"<b>${T.fmt_big(total)}</b><br><span style='font-size:11px'>{L('total revenue', 'مجموع الإيرادات')}</span>", hover),
                 key="sc_share")
    with right:
        lg = data.logos(d["Symbol"].head(12).tolist())
        rows = []
        for i, (_, r) in enumerate(d.head(12).iterrows(), 1):
            w = r["Rev share"] if pd.notna(r["Rev share"]) else 0
            rows.append(f'<div class="b"><div class="t"><span style="display:flex;align-items:center;gap:8px">'
                        f'<span class="muted" style="width:18px">{i}</span>{T.company(r["Symbol"], str(r.get("Name") or "")[:24], lg.get(r["Symbol"]), 26, href=ui.href(r["Symbol"]))}</span>'
                        f'<span class="num">${T.fmt_big(r["Revenue"])} · <b>{w:.1f}%</b></span></div>'
                        f'<div class="trk"><span style="width:{min(100, w / max(d["Rev share"].max(), 1e-9) * 100):.1f}%;'
                        f'background:linear-gradient(90deg,{T.ACCENT},{T.VIOLET})"></span></div></div>')
        ui.html(f'<div class="card"><div class="muted" style="font-size:.75rem;font-weight:600;letter-spacing:.08em">'
                f'{L("LEADERS BY REVENUE", "الأكبر حسب الإيرادات")}</div><div class="bars">{"".join(rows)}</div></div>')
    st.caption(L("Market share = company revenue (last 12 months) ÷ total revenue of the companies in this list.",
                 "الحصة السوقية = إيرادات الشركة (آخر 12 شهر) ÷ مجموع إيرادات الشركات في هذه القائمة."))


def page_screener():
    ui.header("filter_alt", "Stock Screener", "فلتر الأسهم",
              "Filter the entire US market by sector, industry, investment theme, valuation, growth, dividends, short interest and technicals.",
              "فلترة السوق الأمريكي كامل حسب القطاع والصناعة والثيم الاستثماري والتقييم والنمو والتوزيعات والبيع على المكشوف والتحليل الفني.")
    # one row: preset · order · results · [Screen] [Reset] - the buttons sit on the same line as the boxes
    top = st.columns([1.35, 1.0, 0.7, 1.25, 0.72, 0.78], vertical_alignment="bottom")
    top[0].selectbox(L("Preset", "قالب جاهز"), list(PRESETS), key="sc_preset", on_change=_apply_preset,
                     format_func=lambda k: L(PRESETS[k][0], PRESETS[k][1]))
    sort = top[1].selectbox(L("Order by", "ترتيب حسب"), list(SORTS), key="sc_sort", format_func=lambda k: L(SORTS[k][0], SORTS[k][1]))
    size = top[2].selectbox(L("Results", "عدد النتائج"), [50, 100, 250], index=1, key="sc_size")
    find = top[3].text_input(L("Find in results", "ابحث في النتائج"), key="sc_q", placeholder=L("Symbol or company…", "رمز أو اسم شركة…")).strip()
    run = top[4].button(L("Screen", "ابحث"), type="primary", icon=":material/search:", width="stretch", key="sc_run")
    top[5].button(L("Reset", "إعادة ضبط"), icon=":material/restart_alt:", width="stretch", key="sc_reset", on_click=_reset_filters)

    # ---- classification row (always visible): sector · industry · theme · sub-theme
    c = st.columns(4)
    c[0].selectbox(L("Sector", "القطاع"), ["Any"] + U.SECTORS, key="sf_sector",
                   format_func=lambda s_: L("Any", "الكل") if s_ == "Any" else sector_name(s_))
    sec = ss.get("sf_sector", "Any")
    iopts = ["Any"] + (U.INDUSTRIES.get(sec, []) if sec != "Any" else [])
    if ss.get("sf_industry") not in iopts:
        ss["sf_industry"] = "Any"
    c[1].selectbox(L("Industry", "الصناعة"), iopts, key="sf_industry", disabled=sec == "Any",
                   format_func=lambda s_: L("Any", "الكل") if s_ == "Any" else industry_name(s_))
    c[2].selectbox(L("Theme", "الثيم الاستثماري"), _theme_opts(), key="sf_theme",
                   format_func=lambda t: L("Any", "الكل") if t == "Any" else theme_name(t))
    th = ss.get("sf_theme", "Any")
    sopts = ["Any"] + (list(X.THEMES[th][3]) if th != "Any" else [])
    if ss.get("sf_subtheme") not in sopts:
        ss["sf_subtheme"] = "Any"
    c[3].selectbox(L("Sub-theme", "الثيم الفرعي"), sopts, key="sf_subtheme", disabled=th == "Any",
                   format_func=lambda k: L("Any", "الكل") if k == "Any" else theme_name(th, k))

    groups = {"desc": L("Descriptive", "وصفية"), "fund": L("Fundamental", "أساسية"), "tech": L("Technical", "فنية")}
    alias = {"tech": "local", "desc": "ldesc", "fund": "lfund"}
    keys_of = {g: [k for k, v in F.items() if v[2] in (g, alias[g])] for g in groups}
    for k in F:
        ss.setdefault(f"sf_{k}", 0)
        if not isinstance(ss.get(f"sf_{k}"), int) or not 0 <= ss[f"sf_{k}"] < len(F[k][3]):
            ss[f"sf_{k}"] = 0
    n_on = {g: sum(1 for k in keys_of[g] if ss.get(f"sf_{k}", 0)) for g in groups}
    tabs = st.tabs([f"{name} · {n_on[g]}" if n_on[g] else name for g, name in groups.items()])
    for tab, g in zip(tabs, groups):
        with tab:
            cols = st.columns(5)
            for i, k in enumerate(keys_of[g]):
                en, ar, _, opts = F[k]
                cols[i % 5].selectbox(L(en, ar), list(range(len(opts))), key=f"sf_{k}", format_func=lambda i_, o=opts: L(o[i_][0], o[i_][1]))

    active = [(k, ss.get(f"sf_{k}", 0)) for k in F if ss.get(f"sf_{k}", 0)]
    chips = [T.badge(f"{L(F[k][0], F[k][1])}: {L(F[k][3][v][0], F[k][3][v][1])}", "acc", "filter_alt") for k, v in active]
    if sec != "Any":
        chips.append(T.badge(sector_name(sec), "acc", "category"))
    if ss.get("sf_industry", "Any") != "Any":
        chips.append(T.badge(industry_name(ss.sf_industry), "vio", "factory"))
    if th != "Any":
        chips.append(T.badge(theme_name(th) + ("" if ss.get("sf_subtheme", "Any") == "Any" else f" › {theme_name(th, ss.sf_subtheme)}"), "gold", X.THEMES[th][2]))
    if chips:
        ui.html(" ".join(chips))

    theme_syms = X.theme_tickers(th, None if ss.get("sf_subtheme", "Any") == "Any" else ss.sf_subtheme) if th != "Any" else None
    filters = []
    for k in F:
        v = ss.get(f"sf_{k}", 0)
        if v and F[k][2] not in LOCAL_GROUPS:
            filters += [list(f) for f in F[k][3][v][2]]
    if sec != "Any":
        filters.append(["eq", "sector", sec])
    if ss.get("sf_industry", "Any") != "Any":
        filters.append(["eq", "industry", ss.sf_industry])
    # the results always answer the filters on screen: any change of a filter, the theme, the order or the count screens again
    # (before, a theme picked without pressing Screen kept the old list - the top 100 of the whole market - under the theme's name)
    sig_ = json.dumps([filters, th, ss.get("sf_subtheme", "Any"), sort, size], default=str)
    if run or ss.get("screen", {}).get("sig") != sig_:
        with st.spinner(L("Screening the US market...", "جاري فلترة السوق الأمريكي...")):
            skipped, unsure = [], []
            if theme_syms is not None:                     # a theme: exactly its companies, each checked against the filters
                df, err, source, skipped, unsure = _theme_screen(theme_syms, filters, sort, SORTS[sort][2])
                source = "live" if not err else "theme_local"
            elif time.time() < _LIVE_DOWN["until"]:        # Yahoo refused a moment ago: don't hammer it, use the backup directly
                df, err, source = pd.DataFrame(), _LIVE_DOWN["err"], "live"
            else:
                df, err = data.screen_custom(filters, sort, SORTS[sort][2], size)
                source = "live"
                if err:
                    _LIVE_DOWN.update(until=time.time() + 600, err=err)
            if err and theme_syms is None:
                ldf, skipped = _local_screen(filters, sort, SORTS[sort][2], size)
                if ldf is not None:
                    df, source = ldf, "local"
            if df.empty and theme_syms is None and err and source == "live":     # both the live and the backup screener are down
                source = "fallback"
                fb = data.changes(tuple(U.US_UNIVERSE))
                df = pd.DataFrame([{"Symbol": s_, "Name": U.name_of(s_), "Price": p_, "Chg %": c_, "Mkt Cap": U.STOCKS[s_][3] * 1e9}
                                   for s_, (p_, c_) in fb.items()])
                if sec != "Any" and not df.empty:
                    df = df[df["Symbol"].map(U.sector_of) == sec]
        ss.screen = {"df": df, "err": err, "source": source, "skipped": skipped, "unsure": unsure, "sig": sig_}

    res = ss.screen
    df = _pre_filters(res["df"].copy()) if not res["df"].empty else res["df"]
    if find and not df.empty:
        f_ = find.upper()
        df = df[df["Symbol"].astype(str).str.upper().str.contains(f_, regex=False, na=False)
                | df["Name"].fillna("").astype(str).str.upper().str.contains(f_, regex=False) if "Name" in df else
                df["Symbol"].astype(str).str.upper().str.contains(f_, regex=False, na=False)]
    if res["source"] == "local":
        st.info(L("Yahoo's live screener isn't answering our server right now, so these results are filtered from our own data "
                  "(S&P 500 + top 175 US stocks, live prices). Everything else on the page works normally.",
                  "فلتر ياهو المباشر لا يستجيب لخادم الموقع حالياً، لذلك النتائج مفلترة من بياناتنا "
                  "(أسهم إس آند بي 500 + أكبر 175 سهم أمريكي بأسعار مباشرة). وباقي الصفحة يعمل بشكل طبيعي."), icon=":material/cloud_sync:")
    if res["source"] == "theme_local":
        st.info(L("Yahoo's live screener isn't answering our server right now, so the theme's companies are checked against the "
                  "filters with their live quotes.",
                  "فلتر ياهو المباشر لا يستجيب لخادم الموقع حالياً، لذلك نتحقق من شركات الثيم مقابل الفلاتر بأسعارها المباشرة."),
                icon=":material/cloud_sync:")
    if res["source"] in ("local", "theme_local") and res.get("skipped"):
        st.caption(L("Filters that need the live screener and were skipped: ", "فلاتر تحتاج الفلتر المباشر وتم تجاهلها: ")
                   + " · ".join(_field_label(f_) for f_ in res["skipped"]))
    if res.get("unsure"):
        st.caption(L("Couldn't check these against the filters right now, so they're left out: ",
                     "تعذّر التحقق من هذه الأسهم مقابل الفلاتر الآن، فتم استبعادها: ") + " · ".join(res["unsure"]))
    if res["source"] == "fallback":
        st.warning(L("Live screener unavailable right now; showing the top 175 US stocks with price filters only.",
                     "الفلتر المباشر غير متاح حالياً؛ نعرض أكبر 175 سهم أمريكي مع فلاتر السعر فقط."), icon=":material/cloud_off:")
    if df.empty:
        st.info(L("No stocks match these filters.", "لا توجد أسهم تطابق هذه الفلاتر."))
        return
    tech = _technicals(df["Symbol"].head(200).tolist())
    if not tech.empty:
        df = df.merge(tech, on="Symbol", how="left")
        if any(ss.get(f"sf_{k}", 0) for k in TECH_KEYS):
            n_before = len(df)
            df = _post_filters(df)
            if n_before > 200:
                st.caption(L("Price-history filters (performance, RSI, volatility, ATR, gap, SMA 20) are checked on the first 200 results.",
                             "فلاتر التاريخ السعري (الأداء وRSI والتذبذب وATR والفجوة ومتوسط 20) تُطبق على أول 200 نتيجة."))
    if df.empty:
        st.info(L("No stocks match these filters.", "لا توجد أسهم تطابق هذه الفلاتر."))
        return
    # ---- classification columns
    with st.spinner(L("Classifying companies...", "جاري تصنيف الشركات...")):
        cls_map = data.classify(df["Symbol"].tolist(), limit=40)
    df["_sector"] = df["Symbol"].map(lambda s_: sec if sec != "Any" else (cls_map.get(s_, (None, None))[0]))
    df["_industry"] = df["Symbol"].map(lambda s_: ss.sf_industry if ss.get("sf_industry", "Any") != "Any" else (cls_map.get(s_, (None, None))[1]))
    df["Sector"] = df["_sector"].map(lambda v: sector_name(v) if v else "—")
    df["Industry"] = df["_industry"].map(lambda v: industry_name(v) if v else "—")
    df["Theme"] = df["Symbol"].map(lambda s_: " · ".join(dict.fromkeys(theme_name(t) for t, _ in X.themes_of(s_))) or "—")
    df["Sub-theme"] = df["Symbol"].map(lambda s_: " · ".join(theme_name(t, k) for t, k in X.themes_of(s_)) or "—")
    df.insert(0, "Logo", df["Symbol"].map(data.logo_url))

    # ---- revenue market share when a sector / industry / theme / sub-theme is chosen
    group = sec != "Any" or ss.get("sf_industry", "Any") != "Any" or th != "Any"
    tot_rev, covered = np.nan, 0
    if group:
        order = df.sort_values("Mkt Cap", ascending=False)["Symbol"].tolist() if "Mkt Cap" in df else df["Symbol"].tolist()
        with st.spinner(L("Loading company revenues...", "جاري تحميل إيرادات الشركات...")):
            rv = data.revenues(order, limit=60)
        df["Revenue (company)"] = pd.to_numeric(df["Symbol"].map(rv), errors="coerce")
        # a company with several businesses only counts the business that belongs to this group (e.g. AWS for Amazon in Cloud)
        sub_, ind_ = ss.get("sf_subtheme", "Any"), ss.get("sf_industry", "Any")
        segs = {s_: X.segment_of(s_, th, sub_, ind_) for s_ in df["Symbol"]}
        df["Revenue"] = df["Revenue (company)"] * df["Symbol"].map(lambda s_: segs[s_][0] if segs.get(s_) else 1.0)
        df["Segment"] = df["Symbol"].map(lambda s_: f"{L(segs[s_][1], segs[s_][2])} · {segs[s_][0] * 100:.0f}%" if segs.get(s_)
                                         else L("Whole company", "الشركة كاملة"))
        n_seg = int(sum(1 for s_, v in segs.items() if v and pd.notna(df.loc[df["Symbol"] == s_, "Revenue (company)"]).any()))
        covered = int(df["Revenue"].notna().sum())
        tot_rev = float(df["Revenue"].sum()) if covered else np.nan
        df["Rev share"] = df["Revenue"] / tot_rev * 100 if covered else np.nan
    group_name = " › ".join(x for x in (
        sector_name(sec) if sec != "Any" else "", industry_name(ss.sf_industry) if ss.get("sf_industry", "Any") != "Any" else "",
        theme_name(th) if th != "Any" else "", theme_name(th, ss.sf_subtheme) if th != "Any" and ss.get("sf_subtheme", "Any") != "Any" else "") if x)

    adv = int((df["Chg %"] > 0).sum()) if "Chg %" in df else 0
    kp = [T.kpi("filter_alt", L("Matches", "النتائج"), f"{len(df)}", group_name or L("whole market", "السوق كامل")),
          T.kpi("trending_up", L("Advancing", "صاعدة"), f"{adv}/{len(df)}", L("up today", "مرتفعة اليوم"), "pos" if adv >= len(df) / 2 else "neg"),
          T.kpi("price_check", L("Median P/E", "وسيط مكرر الربحية"), f"{df['P/E'].median():.1f}" if "P/E" in df and df["P/E"].notna().any() else "—"),
          T.kpi("account_balance", L("Total market cap", "إجمالي القيمة السوقية"), T.fmt_big(df["Mkt Cap"].sum()) if "Mkt Cap" in df else "—")]
    if group:
        sub_txt = L(f"{covered} of {len(df)} companies", f"{covered} من {len(df)} شركة")
        if covered and n_seg:
            sub_txt += L(f" · {n_seg} by business segment", f" · {n_seg} حسب النشاط")
        kp.append(T.kpi("payments", L("Revenue in this group (TTM)", "إيرادات هذه المجموعة (آخر 12 شهر)"), ("$" + T.fmt_big(tot_rev)) if covered else "—",
                        sub_txt, "acc"))
    for col, k in zip(st.columns(len(kp)), kp):
        col.markdown(k, unsafe_allow_html=True)
    if group and covered and n_seg:
        st.caption(L(f"For {n_seg} companies with several businesses, only the business that belongs to this group is counted "
                     "(e.g. AWS for Amazon in Cloud, Data Center for Nvidia in AI chips). Their shares come from the latest annual reports "
                     "and are rounded; see the “Counted business” column.",
                     f"لـ {n_seg} شركات لديها أكثر من نشاط، نحتسب فقط إيرادات النشاط الذي ينتمي لهذه المجموعة "
                     "(مثل AWS لأمازون في الحوسبة السحابية، ومراكز البيانات لإنفيديا في رقائق الذكاء الاصطناعي). النسب من آخر تقارير سنوية "
                     "ومقرّبة، وتجدها في عمود «النشاط المحتسب»."))
    if group and not covered:
        st.caption(L("Revenue data isn't available from the data source right now.", "بيانات الإيرادات غير متاحة من المصدر حالياً."))
    elif group and len(df) > 60:
        st.caption(L("Revenue and market share are calculated for the 60 largest companies in this list.",
                     "الإيرادات والحصص السوقية محسوبة لأكبر 60 شركة في هذه القائمة."))

    N = {"Symbol": L("Ticker", "الرمز"), "Name": L("Company", "الشركة"), "Sector": L("Sector", "القطاع"), "Industry": L("Industry", "الصناعة"),
         "Theme": L("Theme", "الثيم"), "Sub-theme": L("Sub-theme", "الثيم الفرعي"), "Mkt Cap": L("Market cap", "القيمة السوقية"),
         "Price": L("Price", "السعر"), "Chg %": L("Change", "التغير"), "Volume": L("Volume", "الحجم"), "P/E": "P/E", "Fwd P/E": "Fwd P/E",
         "P/B": "P/B", "EPS": "EPS", "Div %": L("Dividend", "التوزيعات"), "52W %": L("52W perf", "أداء سنوي"), "Rating": L("Analyst rating", "تقييم المحللين"),
         "Perf W": L("Perf week", "أسبوع"), "Perf M": L("Perf month", "شهر"), "Perf 3M": L("Perf quarter", "3 أشهر"), "Perf YTD": L("Perf YTD", "منذ بداية العام"),
         "RSI": "RSI", "Volatility": L("Volatility", "التذبذب"), "Logo": "Logo", "Revenue": L("Revenue (TTM)", "الإيرادات"),
         "Rev share": L("Market share (revenue)", "الحصة السوقية (إيرادات)"), "Segment": L("Counted business", "النشاط المحتسب")}
    rev_cols = ["Revenue", "Segment", "Rev share"] if group else []
    views = {L("Overview", "نظرة عامة"): ["Logo", "Symbol", "Name", "Sector", "Industry"] + rev_cols + ["Mkt Cap", "P/E", "Price", "Chg %", "Volume"],
             L("Classification", "التصنيف"): ["Logo", "Symbol", "Name", "Sector", "Industry", "Theme", "Sub-theme"] + rev_cols,
             L("Valuation", "التقييم"): ["Logo", "Symbol", "Mkt Cap", "P/E", "Fwd P/E", "P/B", "EPS", "Div %", "Rating"],
             L("Performance", "الأداء"): ["Logo", "Symbol", "Price", "Chg %", "Perf W", "Perf M", "Perf 3M", "Perf YTD", "52W %", "RSI", "Volatility"]}
    if group and covered:
        share_tab = L("Market share", "الحصص السوقية")
    else:
        share_tab = None
    vt = st.tabs(list(views) + ([share_tab] if share_tab else []) + [L("Charts", "الرسوم")])
    max_share = float(df["Rev share"].max()) if "Rev share" in df and df["Rev share"].notna().any() else 100.0
    for tab, (vname, cols) in zip(vt, views.items()):
        with tab:
            cols = [c_ for c_ in cols if c_ in df.columns]
            show = df[cols].copy()
            if "Revenue" in show:
                show = show.sort_values("Revenue", ascending=False, na_position="last")
                show["Revenue"] = show["Revenue"].map(lambda v: "$" + T.fmt_big(v) if pd.notna(v) else "—")
            for c_ in ("Mkt Cap", "Volume"):
                if c_ in show:
                    show[c_] = show[c_].map(T.fmt_big)
            pct_cols = [c_ for c_ in ("Chg %", "Perf W", "Perf M", "Perf 3M", "Perf YTD", "52W %") if c_ in show]
            show = show.rename(columns=N)
            fmt = {**{N[c_]: "{:+.2f}%" for c_ in pct_cols}, **{N[c_]: "{:,.2f}" for c_ in ("Price", "P/E", "Fwd P/E", "P/B", "EPS") if c_ in cols}}
            if "Div %" in cols:
                fmt[N["Div %"]] = "{:.2f}%"
            if "RSI" in cols:
                fmt["RSI"] = "{:.0f}"
            if "Volatility" in cols:
                fmt[N["Volatility"]] = "{:.1f}%"
            if "Rev share" in cols:
                fmt[N["Rev share"]] = "{:.1f}%"
            cell = {}
            if "Rev share" in cols:
                top_ = max(max_share, 1.0)
                cell[N["Rev share"]] = lambda v, r, top_=top_: (ui.score_bar(v, top_).replace(f"<b>{float(v):.0f}</b>", f"<b>{float(v):.1f}%</b>")
                                                               if pd.notna(v) else '<span class="m">—</span>')
            ui.table(show, sym=N["Symbol"] if N.get("Symbol") in show else None, pills={N[c_] for c_ in pct_cols[:1]},
                     signed={N[c_] for c_ in pct_cols[1:]}, fmt=fmt, cell=cell, height=600, wrap={N[c_] for c_ in ("Name",) if c_ in cols})
    if share_tab:
        with vt[len(views)]:
            ui.safe(_share_view, df, tot_rev, group_name)
    with vt[-1]:
        if "_spark" in df:
            lg = data.logos(df["Symbol"].head(36).tolist())
            items = []
            for _, r in df.head(36).iterrows():
                sp = r["_spark"] if isinstance(r["_spark"], np.ndarray) else None
                head = f'<div style="margin-bottom:4px">{T.company(r["Symbol"], str(r["Name"])[:22], lg.get(r["Symbol"]), 26, href=ui.href(r["Symbol"]))}</div>'
                items.append(T.tile("", T.fmt_price(r["Price"]), None, r["Chg %"], sp, head_html=head))
            ui.html(T.tiles(items))
    a, c_ = st.columns([3, 1], vertical_alignment="bottom")
    with a:
        ui.open_picker(df["Symbol"].tolist(), "sc", "Selected stock", "السهم المختار")
    c_.download_button(L("Export CSV", "تصدير CSV"), df.drop(columns=["_spark", "Logo", "_sector", "_industry"], errors="ignore").to_csv(index=False).encode(),
                       "screener.csv", "text/csv", icon=":material/download:", width="stretch")
    if res.get("err") and res["source"] != "live":
        with st.expander(L("Technical details (Yahoo)", "تفاصيل فنية (ياهو)")):
            st.code(res["err"])
    ui.foot()


# =====================================================================
# SCANNER
# =====================================================================
# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "20.2"
