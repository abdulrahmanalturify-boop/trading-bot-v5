"""
scripts/saudi_probe2.py - What Yahoo Finance has for the Saudi market's calendars, funds and long history, read on a GitHub
server (run by .github/workflows/saudiprobe.yml): the earnings calendar for region "sa", the economic events by region, per
company calendars / earnings dates / dividends / splits, the ex-dividend dates of every main-market company, the Saudi ETFs
and their history, the IPO and splits calendars, and how far back the prices go. Writes research/results/saudi_probe2.txt
and saudi_probe2.json.
"""
import json
import os
import sys
import time
import traceback
import warnings
from datetime import date, timedelta

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "research", "results")
os.makedirs(OUT, exist_ok=True)

import pandas as pd       # noqa: E402
import yfinance as yf     # noqa: E402

import tasi               # noqa: E402

LINES, J = [], {}


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def t(name, fn):
    t0 = time.time()
    try:
        v = fn()
        log(f"ok    | {name} | {time.time() - t0:.1f}s | {str(v)[:1500]}")
        return v
    except Exception as e:
        log(f"ERROR | {name} | {time.time() - t0:.1f}s | {type(e).__name__}: {str(e)[:500]}")
        return None


def main():
    try:
        _main()
    except Exception:
        log("CRASH", traceback.format_exc())
    open(os.path.join(OUT, "saudi_probe2.txt"), "w", encoding="utf-8").write("\n".join(LINES) + "\n")
    json.dump(J, open(os.path.join(OUT, "saudi_probe2.json"), "w", encoding="utf-8"), ensure_ascii=False, default=str)
    return 0


def _main():
    log("yfinance", yf.__version__)
    today = date.today()
    s0, s1 = (today - timedelta(days=45)).isoformat(), (today + timedelta(days=60)).isoformat()
    try:
        from yfinance.calendars import CalendarQuery
    except Exception:
        log("no CalendarQuery:", traceback.format_exc()[-400:])
        CalendarQuery = None
    cal = t("Calendars()", lambda: yf.Calendars(start=s0, end=s1))

    def earn(region):
        q = CalendarQuery("and", [CalendarQuery("eq", ["region", region]),
                                  CalendarQuery("or", [CalendarQuery("eq", ["eventtype", "EAD"]), CalendarQuery("eq", ["eventtype", "ERA"])]),
                                  CalendarQuery("gte", ["startdatetime", s0]), CalendarQuery("lte", ["startdatetime", s1])])
        frames = []
        for off in range(0, 500, 100):
            df = cal._get_data("sp_earnings", q, limit=100, offset=off, force=True)
            if df is None or df.empty:
                break
            frames.append(df.reset_index())
            if len(df) < 100:
                break
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    df = t("earnings calendar region sa", lambda: earn("sa"))
    if df is not None and len(df):
        log("columns", list(df.columns))
        log(df.head(30).to_string()[:4000])
        J["earnings_sa"] = json.loads(df.head(300).to_json(orient="records", date_format="iso"))

    def econ():
        frames = []
        for off in range(0, 1500, 100):
            d = cal.get_economic_events_calendar(start=s0, end=s1, limit=100, offset=off, force=True)
            if d is None or d.empty:
                break
            frames.append(d.reset_index())
            if len(d) < 100:
                break
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    ev = t("economic events (all regions)", econ)
    if ev is not None and len(ev):
        log("econ columns", list(ev.columns))
        reg = [c for c in ev.columns if c.lower() in ("region", "country", "country_code")]
        if reg:
            vc = ev[reg[0]].astype(str).str.upper().value_counts()
            log("econ regions", vc.head(60).to_dict())
            sa = ev[ev[reg[0]].astype(str).str.upper().isin(["SA", "SAU", "SAUDI ARABIA"])]
            log("econ SA rows", len(sa))
            log(sa.head(40).to_string()[:4000])
            J["econ_sa"] = json.loads(sa.to_json(orient="records", date_format="iso"))

    for name, fn in (("ipo calendar", lambda: cal.get_ipo_info_calendar(start=s0, end=s1, limit=100, force=True)),
                     ("splits calendar", lambda: cal.get_splits_calendar(start=s0, end=s1, limit=100, force=True))):
        d = t(name, fn)
        if d is not None and len(d):
            d = d.reset_index()
            txt = d.astype(str).apply(" ".join, axis=1)
            hit = d[txt.str.contains(r"\.SR|SAU|Saudi|Tadawul", case=False, regex=True)]
            log(f"{name}: {len(d)} rows, Saudi rows {len(hit)}")
            log(hit.head(20).to_string()[:2000])

    for sym in ("2222.SR", "1120.SR", "2010.SR", "7010.SR", "1180.SR", "4013.SR"):
        tk = yf.Ticker(sym)
        t(f"{sym} calendar", lambda: tk.calendar)
        t(f"{sym} earnings_dates", lambda: (lambda d: None if d is None else d.head(8).to_string())(tk.get_earnings_dates(limit=8)))
        t(f"{sym} dividends", lambda: (lambda d: (len(d), d.tail(6).to_dict()))(tk.dividends))
        t(f"{sym} splits", lambda: (lambda d: (len(d), d.tail(4).to_dict()))(tk.splits))
        t(f"{sym} info dividend keys", lambda: {k: (tk.info or {}).get(k) for k in ("exDividendDate", "dividendDate", "dividendRate", "dividendYield",
                                                                                 "lastDividendValue", "lastDividendDate", "earningsTimestamp",
                                                                                 "earningsTimestampStart", "earningsTimestampEnd", "currency")})
        time.sleep(0.5)

    # every main-market company: ex-dividend and earnings dates from the quote summary
    rows = []
    for n, sym in enumerate(tasi.SYMBOLS):
        inf = {}
        for attempt in range(2):
            try:
                inf = yf.Ticker(sym).info or {}
                break
            except Exception:
                time.sleep(3)
        rows.append({"sym": sym, **{k: inf.get(k) for k in ("exDividendDate", "dividendDate", "dividendRate", "lastDividendValue",
                                                               "lastDividendDate", "earningsTimestamp", "earningsTimestampStart",
                                                               "earningsTimestampEnd", "isEarningsDateEstimate", "marketCap")}})
        if n % 40 == 0:
            log("info sweep", n, sym, rows[-1])
        time.sleep(0.25)
    sw = pd.DataFrame(rows)
    for c in ("exDividendDate", "dividendDate", "lastDividendDate", "earningsTimestamp", "earningsTimestampStart", "earningsTimestampEnd"):
        if c in sw:
            d = pd.to_datetime(sw[c], unit="s", errors="coerce")
            log(f"sweep {c}: {int(d.notna().sum())} set, in [-45d, +60d]: "
                f"{int(((d >= pd.Timestamp(s0)) & (d <= pd.Timestamp(s1))).sum())}, range {d.min()} .. {d.max()}")
    J["sweep"] = json.loads(sw.to_json(orient="records"))

    # Saudi ETFs
    try:
        from yfinance import ETFQuery
        r = t("ETF screen region sa", lambda: yf.screen(ETFQuery("eq", ["region", "sa"]), size=100))
        qs = (r or {}).get("quotes") or []
        J["etfs"] = [{k: q.get(k) for k in ("symbol", "shortName", "longName", "regularMarketPrice", "averageDailyVolume3Month", "netAssets")} for q in qs]
        log("ETFs", len(qs), J["etfs"][:40])
    except Exception:
        log(traceback.format_exc()[:800])
    cands = sorted({q["symbol"] for q in J.get("etfs", [])} | {f"{c}.SR" for c in range(9400, 9431)})
    hist = {}
    for s in cands:
        def h(s=s):
            d = yf.Ticker(s).history(period="max")
            return (len(d), str(d.index[0].date()) if len(d) else None, str(d.index[-1].date()) if len(d) else None,
                    float(d["Close"].iloc[-1]) if len(d) else None, float(d["Volume"].tail(60).mean()) if len(d) else None)
        hist[s] = t(f"history max {s}", h)
        time.sleep(0.3)
    J["etf_hist"] = hist
    for s in cands[:40]:
        t(f"name {s}", lambda s=s: {k: (yf.Ticker(s).info or {}).get(k) for k in ("shortName", "longName", "quoteType", "category", "fundFamily")})

    # long history: the index, the funds that follow the market, the biggest companies
    for s in ["^TASI.SR", "^TASI", "TASI.SR", "^TASISR", "KSA", "FLSA", "^NOMUC.SR"] + tasi.top(25):
        t(f"history max {s}", lambda s=s: (lambda d: (len(d), str(d.index[0].date()) if len(d) else None))(yf.Ticker(s).history(period="max")))



if __name__ == "__main__":
    sys.exit(main())
