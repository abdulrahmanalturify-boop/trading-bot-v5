"""
caldata.py - Data for the Calendar pages: earnings dates and results, IPOs, stock splits, dividends and economic events.
Source: Yahoo Finance calendars (yfinance.Calendars). Dividends: Nasdaq's calendar, or (if Nasdaq is unreachable)
the announced ex-dividend dates of ~110 well-known dividend payers from Yahoo.
As everywhere on the site, a failure is never cached: the page shows what it has and retries later.
"""
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

import data
import mcal

ET = mcal.ET
EARN_COLS = ["Symbol", "Company", "Cap", "Date", "When", "Hour", "Quarter", "Est", "EPS", "Surprise"]


def week_of(d):
    """Monday of the week that contains d (Saturday/Sunday -> the coming week)."""
    if d.weekday() >= 5:
        d += timedelta(days=7 - d.weekday())
    return d - timedelta(days=d.weekday())


def _col(df, *names):
    low = {str(c).lower().strip(): c for c in df.columns}
    for n in names:
        if n in low:
            return low[n]
    return None


def _calendars(start, end):
    if not hasattr(yf, "Calendars"):
        raise data.Empty("this yfinance version has no calendars")
    return yf.Calendars(start=start, end=end)


def _pages(fetch, pages):
    frames = []
    for i in range(pages):
        df = fetch(limit=100, offset=i * 100, force=True)
        if df is None or df.empty:
            break
        frames.append(df.reset_index())
        if len(df) < 100:
            break
    if not frames:
        raise data.Empty("calendar")
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------- earnings
@st.cache_data(ttl=1800, show_spinner=False)
def _earnings(start, end, min_cap, pages):
    cal = _calendars(start, end)
    return _pages(lambda **k: cal.get_earnings_calendar(market_cap=min_cap or None, filter_most_active=False, start=start, end=end, **k), pages)


def _et(series):
    t = pd.to_datetime(series, errors="coerce", utc=True)
    return t.dt.tz_convert(ET)


def _norm_earnings(raw):
    df = raw
    sym, comp, cap = _col(df, "symbol", "ticker"), _col(df, "company", "company name", "companyshortname"), _col(df, "marketcap", "market cap (intraday)", "intradaymarketcap")
    when_c, dt_c = _col(df, "timing", "startdatetimetype", "earnings call time"), _col(df, "event start date", "startdatetime", "earnings date")
    ev, est, act, sur = (_col(df, "event name", "eventname"), _col(df, "eps estimate", "epsestimate"), _col(df, "reported eps", "epsactual"),
                         _col(df, "surprise(%)", "surprise (%)", "epssurprisepct"))
    if sym is None or dt_c is None:
        return pd.DataFrame(columns=EARN_COLS)
    t = _et(df[dt_c])
    num = lambda c: pd.to_numeric(df[c], errors="coerce") if c else pd.Series(np.nan, index=df.index)
    out = pd.DataFrame({"Symbol": df[sym].astype(str).str.upper().str.strip(), "Company": df[comp].astype(str) if comp else "",
                        "Cap": num(cap), "Date": t.dt.date, "Hour": t.dt.hour + t.dt.minute / 60,
                        "Quarter": df[ev].astype(str).str.extract(r"(Q[1-4]\s*\d{4})", expand=False).str.replace(r"\s+", " ", regex=True) if ev else None,
                        "Est": num(est), "EPS": num(act), "Surprise": num(sur)})
    timing = df[when_c].astype(str).str.upper().str.strip() if when_c else pd.Series("", index=df.index)
    by_hour = np.where(out["Hour"] < 9.5, "bmo", np.where(out["Hour"] >= 16, "amc", "dmh"))
    has_time = (out["Hour"].fillna(0) > 0) & ~timing.isin(["TNS", ""])
    out["When"] = np.select([timing.eq("BMO"), timing.eq("AMC"), has_time], ["bmo", "amc", by_hour], default="tns")
    # a missing surprise can be computed from estimate and actual
    miss = out["Surprise"].isna() & out["EPS"].notna() & out["Est"].notna() & (out["Est"].abs() > 0)
    out.loc[miss, "Surprise"] = (out.loc[miss, "EPS"] - out.loc[miss, "Est"]) / out.loc[miss, "Est"].abs() * 100
    out = out[out["Symbol"].str.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", na=False) & out["Date"].notna()]
    out["_rep"] = out["EPS"].notna()
    out = out.sort_values(["_rep", "Cap"], ascending=False).drop_duplicates(["Symbol", "Date"]).drop(columns="_rep")
    return out[EARN_COLS].sort_values("Cap", ascending=False, na_position="last").reset_index(drop=True)


def earnings(start, end, min_cap=0, pages=8):
    """Companies reporting between two dates (inclusive, US Eastern dates). Biggest companies first."""
    q_end = (end + timedelta(days=1)).isoformat()
    try:
        df = _norm_earnings(_earnings(start.isoformat(), q_end, int(min_cap or 0), pages))
    except Exception:
        return pd.DataFrame(columns=EARN_COLS)
    return df[(df["Date"] >= start) & (df["Date"] <= end)].reset_index(drop=True)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _revenue(sym):
    """Latest reported quarter: revenue, the same quarter a year earlier, and the quarter's end date."""
    q = yf.Ticker(sym).quarterly_income_stmt
    if q is None or q.empty:
        raise data.Empty(sym)
    row = next((r for r in ("Total Revenue", "Operating Revenue", "TotalRevenue") if r in q.index), None)
    if row is None:
        raise data.Empty(sym)
    s = pd.to_numeric(q.loc[row], errors="coerce").dropna().sort_index(ascending=False)
    if s.empty:
        raise data.Empty(sym)
    end = pd.Timestamp(s.index[0])
    yago = s[(s.index <= end - pd.Timedelta(days=330)) & (s.index >= end - pd.Timedelta(days=400))]
    return {"rev": float(s.iloc[0]), "rev_ya": float(yago.iloc[0]) if len(yago) else None, "q_end": end.date()}


@st.cache_data(ttl=3 * 3600, show_spinner=False)
def _rev_estimate(sym):
    """Analysts' revenue estimate for the quarter being reported next (Yahoo '0q')."""
    e = yf.Ticker(sym).revenue_estimate
    if e is None or e.empty or "avg" not in e.columns:
        raise data.Empty(sym)
    idx = next((i for i in e.index if str(i).lower() in ("0q", "currentquarter")), e.index[0])
    v = pd.to_numeric(e.loc[idx, "avg"], errors="coerce")
    if pd.isna(v):
        raise data.Empty(sym)
    return {"est": float(v), "ya": float(pd.to_numeric(e.loc[idx].get("yearAgoRevenue"), errors="coerce"))
            if "yearAgoRevenue" in e.columns else None}


def revenue_many(symbols, reported=None):
    """symbol -> {"rev", "rev_ya", "q_end", "est"}. reported: symbol -> report date (the revenue must belong to that report)."""
    out = {}

    def one(s):
        r = {}
        try:
            r.update(_revenue(s))
        except Exception:
            pass
        if reported is None or s not in (reported or {}) or reported[s] >= mcal.today_et():
            try:
                r["est"] = _rev_estimate(s)["est"]
            except Exception:
                pass
        return s, r
    syms = list(dict.fromkeys(symbols))
    if not syms:
        return out
    with ThreadPoolExecutor(max_workers=10) as ex:
        for s, r in ex.map(one, syms):
            if reported and s in reported and r.get("q_end"):
                # statement not updated yet: its latest quarter ended long before this report
                if (reported[s] - r["q_end"]).days > 120:
                    r = {k: v for k, v in r.items() if k == "est"}
            out[s] = r
    return out


def reactions(rows):
    """Price move caused by each report: the report-day move (before open / during the day) or the next day's (after close).
    rows: DataFrame with Symbol, Date, When. -> symbol -> % move"""
    if rows.empty:
        return {}
    hist = data.history_many(tuple(rows["Symbol"].unique()), "3mo")
    out = {}
    for _, r in rows.iterrows():
        df = hist.get(r["Symbol"])
        if df is None or len(df) < 3:
            continue
        c = df["Close"].dropna()
        days = pd.Index([pd.Timestamp(x).date() for x in c.index])
        d = r["Date"] if r["When"] in ("bmo", "dmh", "tns") else mcal.next_trading_day(r["Date"])
        if d not in days:
            continue
        i = days.get_loc(d)
        if isinstance(i, int) and i > 0:
            out[r["Symbol"]] = float((c.iloc[i] / c.iloc[i - 1] - 1) * 100)
    return out


# ---------------------------------------------------------------- IPOs
@st.cache_data(ttl=3600, show_spinner=False)
def _ipos(start, end):
    cal = _calendars(start, end)
    return _pages(lambda **k: cal.get_ipo_info_calendar(start=start, end=end, **k), 5)


def ipos(start, end):
    """-> Symbol, Company, Exchange, Date, Filed, Low, High, Price, Shares, Status (expected/priced/filed/withdrawn/...), Size"""
    try:
        df = _ipos(start.isoformat(), (end + timedelta(days=1)).isoformat())
    except Exception:
        return pd.DataFrame()
    sym = _col(df, "symbol", "ticker")
    if sym is None:
        return pd.DataFrame()
    num = lambda *n: pd.to_numeric(df[_col(df, *n)], errors="coerce") if _col(df, *n) else pd.Series(np.nan, index=df.index)
    dcol = _col(df, "date", "startdatetime")
    out = pd.DataFrame({"Symbol": df[sym].astype(str).str.upper(), "Company": df[_col(df, "company", "company name")].astype(str) if _col(df, "company", "company name") else "",
                        "Exchange": df[_col(df, "exchange", "exchange short name")].astype(str) if _col(df, "exchange", "exchange short name") else "",
                        "Date": _et(df[dcol]).dt.date if dcol else None,
                        "Filed": _et(df[_col(df, "filing date", "filingdate")]).dt.date if _col(df, "filing date", "filingdate") else None,
                        "Low": num("price from", "pricefrom"), "High": num("price to", "priceto"), "Price": num("price", "offerprice"),
                        "Shares": num("shares"), "Status": df[_col(df, "deal type", "dealtype")].astype(str).str.lower().str.strip()
                        if _col(df, "deal type", "dealtype") else ""})
    for c in ("Company", "Exchange", "Status"):
        out[c] = out[c].replace({"nan": "", "None": "", "NaN": ""}) if c in out else ""
    mid = out["Price"].fillna((out["Low"] + out["High"]) / 2).fillna(out["High"]).fillna(out["Low"])
    out["Size"] = mid * out["Shares"]
    out = out[out["Date"].notna()].drop_duplicates(["Symbol", "Date"])
    return out[(out["Date"] >= start) & (out["Date"] <= end)].sort_values("Date").reset_index(drop=True)


# ---------------------------------------------------------------- stock splits
@st.cache_data(ttl=3600, show_spinner=False)
def _splits(start, end):
    cal = _calendars(start, end)
    return _pages(lambda **k: cal.get_splits_calendar(start=start, end=end, **k), 4)


def splits(start, end):
    """-> Symbol, Company, Date, Old, New, Ratio ("10-for-1"), Kind ("forward" / "reverse"), Optionable"""
    try:
        df = _splits(start.isoformat(), (end + timedelta(days=1)).isoformat())
    except Exception:
        return pd.DataFrame()
    sym, dcol = _col(df, "symbol", "ticker"), _col(df, "payable on", "startdatetime", "date")
    if sym is None or dcol is None:
        return pd.DataFrame()
    old = pd.to_numeric(df[_col(df, "old share worth", "old_share_worth")], errors="coerce") if _col(df, "old share worth", "old_share_worth") else np.nan
    new = pd.to_numeric(df[_col(df, "share worth", "share_worth")], errors="coerce") if _col(df, "share worth", "share_worth") else np.nan
    oc = _col(df, "optionable", "optionable?")
    out = pd.DataFrame({"Symbol": df[sym].astype(str).str.upper(), "Company": df[_col(df, "company", "company name")].astype(str)
                        if _col(df, "company", "company name") else "", "Date": _et(df[dcol]).dt.date, "Old": old, "New": new,
                        "Optionable": df[oc].astype(str) if oc else ""})
    out = out[out["Date"].notna() & out["Old"].notna() & out["New"].notna() & (out["Old"] > 0) & (out["New"] > 0)]
    fmt = lambda v: f"{v:g}"
    out["Ratio"] = [f"{fmt(n)}-for-{fmt(o)}" for o, n in zip(out["Old"], out["New"])]
    out["Kind"] = np.where(out["New"] > out["Old"], "forward", "reverse")
    out = out.drop_duplicates(["Symbol", "Date"])
    return out[(out["Date"] >= start) & (out["Date"] <= end)].sort_values("Date").reset_index(drop=True)


# ---------------------------------------------------------------- economic events
# Yahoo's calendar uses Reuters-style short names ("Build Permits R Chg MM*", "Initial Jobless Clm", "U Mich Sentiment Final",
# "Core PCE Price Index MM", "ISM N-Mfg PMI", "Non-Farm Payrolls"), so the patterns cover both the short and the long forms.
HIGH = re.compile(r"(\bcpi\b|consumer price|\bpce\b|non-?farm|payrolls|unemployment rate|fomc|fed(?:eral)? funds|fed interest rate|"
                  r"interest rate decision|rate decision|\bgdp\b|retail sales|\bism\b.*(?:manuf|mfg|services|pmi)|\bppi\b|producer price)", re.I)
MEDIUM = re.compile(r"(jobless|initial claims|continuing claims|durable goods|\bu\.? ?mich|michigan|consumer confidence|conf(?:erence)? board|"
                    r"housing starts|build(?:ing)? permits|new home sales|existing home|pending home|industrial production|ind(?:ustrial)? prod|"
                    r"capacity util|mfg output|manufacturing output|\badp\b|jolts|job openings|trade balance|goods trade|intl trade|international trade|"
                    r"personal income|consumption|personal spending|phil(?:ly|adelphia)? fed|empire state|ny fed manufacturing|chicago pmi|\bpmi\b|"
                    r"factory orders|business inventories|retail inventories|wholesale inv|import prices|export prices|productivity|labor costs|"
                    r"employment cost|\beci\b|corporate profits|current account|construction spending|beige book|powell|fed chair|fomc minutes|"
                    r"average earnings|avg earnings|avg hourly|core capex|nondef|case.?shiller|house price|fhfa|federal budget|treasury budget|"
                    r"crude oil inventories|\beia\b|consumer credit|gdpnow)", re.I)
LOWER_IS_BETTER = re.compile(r"(unemployment|jobless|claims|\bclm\b|inventor|invt|deficit)", re.I)


def importance(name):
    n = str(name or "")
    return 3 if HIGH.search(n) else 2 if MEDIUM.search(n) else 1


def econ(start, end, region="US"):
    """-> Event, Time (ET), Date, Period, Actual, Expected, Last, Revised, Region, Stars (1-3)"""
    try:
        df = data._econ_calendar(start.isoformat(), (end + timedelta(days=1)).isoformat()).copy()
    except Exception:
        return pd.DataFrame()
    ev = _col(df, "event", "econ release", "econ_release")
    tc = _col(df, "event time", "startdatetime", "date")
    if ev is None or tc is None:
        return pd.DataFrame()
    num = lambda *n: pd.to_numeric(df[_col(df, *n)], errors="coerce") if _col(df, *n) else pd.Series(np.nan, index=df.index)
    reg = _col(df, "region", "country", "country code", "country_code")
    t = _et(df[tc])
    out = pd.DataFrame({"Event": df[ev].astype(str), "Time": t, "Date": t.dt.date, "Period": df[_col(df, "for", "period")].astype(str)
                        if _col(df, "for", "period") else "", "Actual": num("actual", "after_release_actual"),
                        "Expected": num("expected", "market expectation", "consensus_estimate"), "Last": num("last", "prior to this", "prior_release_actual"),
                        "Revised": num("revised", "revised from", "originally_reported_actual"),
                        "Region": df[reg].astype(str).str.upper() if reg else "US"})
    if region == "US":
        out = out[out["Region"].isin(["US", "USA", "UNITED STATES"])]
    out["Stars"] = out["Event"].map(importance)
    out = out[out["Date"].notna()].drop_duplicates(["Event", "Time", "Region"])
    return out[(out["Date"] >= start) & (out["Date"] <= end)].sort_values("Time").reset_index(drop=True)


# ---------------------------------------------------------------- dividends
NASDAQ_HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
              "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9", "Origin": "https://www.nasdaq.com",
              "Referer": "https://www.nasdaq.com/"}
DIV_NAMES = ("AAPL MSFT NVDA AVGO JPM V MA WMT COST HD PG JNJ ABBV MRK PFE LLY KO PEP PM MO MDLZ CL KMB GIS HSY KHC SJM MCD SBUX YUM "
             "XOM CVX COP EOG PSX MPC VLO OXY DVN KMI WMB OKE BAC WFC C GS MS BLK SCHW USB PNC TFC AXP COF MET PRU AFL ALL TRV CB "
             "UNH CVS CI ELV ABT MDT AMGN GILD BMY TXN QCOM CSCO IBM ORCL INTC ADI AVGO ACN HPQ DELL "
             "CAT DE HON GE MMM LMT RTX GD NOC UNP CSX NSC UPS FDX EMR ITW ETN PH "
             "DUK SO NEE D AEP EXC XEL WEC ED PEG SRE PCG "
             "O SPG PLD AMT CCI PSA EQIX DLR VICI WELL "
             "T VZ CMCSA TGT LOW NKE F GM DOW LYB NUE ADM SYY CLX KR TSN BBY GPC LEG").split()


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _nasdaq_div_day(day):
    r = requests.get("https://api.nasdaq.com/api/calendar/dividends", params={"date": day}, headers=NASDAQ_HDR, timeout=8)
    if getattr(r, "status_code", 0) != 200:
        raise data.Empty(f"nasdaq {getattr(r, 'status_code', '?')}")
    js = r.json() or {}
    d = js.get("data")
    if d is None:
        raise data.Empty("nasdaq: no data")
    return ((d.get("calendar") or {}).get("rows")) or []


def _date(v):
    if v is None or v == "" or v == "N/A":
        return None
    try:
        if isinstance(v, (int, float, np.integer, np.floating)) and not pd.isna(v):
            return pd.Timestamp(int(v), unit="s", tz="UTC").tz_convert(ET).date()
        t = pd.to_datetime(str(v), errors="coerce")
        return None if pd.isna(t) else t.date()
    except Exception:
        return None


def _money(v):
    try:
        return float(str(v).replace("$", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return np.nan


def _nasdaq_dividends(start, end):
    rows, d = [], start
    while d <= end:
        if d.weekday() < 5:
            for r in _nasdaq_div_day(d.isoformat()):     # raises when Nasdaq is unreachable -> Yahoo fallback
                rows.append({"Symbol": str(r.get("symbol") or "").upper().strip(), "Company": r.get("companyName") or "",
                             "ExDate": _date(r.get("dividend_Ex_Date")) or d, "PayDate": _date(r.get("payment_Date")),
                             "RecordDate": _date(r.get("record_Date")), "Amount": _money(r.get("dividend_Rate")),
                             "Annual": _money(r.get("indicated_Annual_Dividend")), "Announced": _date(r.get("announcement_Date"))})
        d += timedelta(days=1)
    return pd.DataFrame(rows)


def _yahoo_dividends(start, end):
    def one(s):
        try:
            i = data.info(s) or {}
        except Exception:
            return None
        ex = _date(i.get("exDividendDate"))
        if not ex or not (start <= ex <= end):
            return None
        price = i.get("currentPrice") or i.get("regularMarketPrice") or i.get("previousClose")
        rate = i.get("dividendRate") or i.get("trailingAnnualDividendRate")
        last = i.get("lastDividendValue")
        amount = last if last else (rate / 4 if rate else np.nan)
        return {"Symbol": s, "Company": i.get("shortName") or i.get("longName") or s, "ExDate": ex, "PayDate": _date(i.get("dividendDate")),
                "RecordDate": None, "Amount": amount, "Annual": rate or np.nan, "Announced": None, "Price": price}
    with ThreadPoolExecutor(max_workers=12) as ex:
        rows = [r for r in ex.map(one, list(dict.fromkeys(DIV_NAMES))) if r]
    return pd.DataFrame(rows)


def dividends(start, end):
    """(DataFrame, source) - upcoming and recent ex-dividend dates. Columns: Symbol, Company, ExDate, PayDate, RecordDate,
    Amount (per share), Annual, Announced, Price"""
    try:
        df, src = _nasdaq_dividends(start, end), "Nasdaq"
    except Exception:
        df, src = pd.DataFrame(), ""
    if df.empty:
        try:
            df, src = _yahoo_dividends(start, end), "Yahoo Finance"
        except Exception:
            df = pd.DataFrame()
    if df.empty:
        return df, src
    df = df[df["Symbol"].str.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", na=False)]
    if "Price" not in df.columns:
        df["Price"] = np.nan
    return df.drop_duplicates(["Symbol", "ExDate"]).sort_values(["ExDate", "Symbol"]).reset_index(drop=True), src

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.3"
