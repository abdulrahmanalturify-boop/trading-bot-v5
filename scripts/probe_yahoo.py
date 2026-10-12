"""Which Yahoo Finance calls answer right now (run by .github/workflows/probe.yml): the company summary (info), the light
quote (fast_info), statements, holders, price history. Prints one line per call."""
import time
import traceback

import yfinance as yf

print("yfinance", yf.__version__)
for sym in ("META", "NKE", "AAPL"):
    t = yf.Ticker(sym)
    for name, fn in (("info", lambda: len(t.info or {})),
                     ("info keys", lambda: sorted(k for k in (t.info or {}) if k in ("marketCap", "trailingPE", "forwardPE", "profitMargins", "longBusinessSummary")) ),
                     ("fast_info", lambda: {k: getattr(t.fast_info, k, None) for k in ("market_cap", "shares", "last_price", "three_month_average_volume")}),
                     ("income_stmt", lambda: getattr(t.quarterly_income_stmt, "shape", None)),
                     ("major_holders", lambda: getattr(t.major_holders, "shape", None)),
                     ("history", lambda: len(t.history(period="5d")))):
        t0 = time.time()
        try:
            out = fn()
            print(f"{sym} {name}: ok {time.time() - t0:.1f}s -> {str(out)[:200]}")
        except Exception as e:
            print(f"{sym} {name}: FAIL {time.time() - t0:.1f}s -> {type(e).__name__}: {str(e)[:200]}")
    time.sleep(1)

# the Saudi indices (TASI, Nomu): the batch quote, the chart API, history, the light quote
print("--- Saudi indices")
import requests
from yfinance.data import YfData
for name, fn in (
        ("v7 quote", lambda: [(q.get("symbol"), q.get("regularMarketPrice"), q.get("regularMarketChangePercent"), q.get("regularMarketTime"))
                              for q in ((YfData().get_raw_json("https://query1.finance.yahoo.com/v7/finance/quote?",
                                                              params={"symbols": "^TASI.SR,^NOMUC.SR,2222.SR", "formatted": "false"}) or {})
                                        .get("quoteResponse") or {}).get("result") or []]),
        ("download 1mo", lambda: {s: len(yf.download(s, period="1mo", progress=False, auto_adjust=False)) for s in ("^TASI.SR", "^NOMUC.SR", "2222.SR")}),
        ("history 1mo", lambda: {s: len(yf.Ticker(s).history(period="1mo")) for s in ("^TASI.SR", "^NOMUC.SR")}),
        ("history 5d 1h", lambda: {s: len(yf.Ticker(s).history(period="5d", interval="1h")) for s in ("^TASI.SR", "^NOMUC.SR")}),
        ("fast_info", lambda: {s: (getattr(yf.Ticker(s).fast_info, "last_price", None), getattr(yf.Ticker(s).fast_info, "previous_close", None))
                               for s in ("^TASI.SR", "^NOMUC.SR")}),
        ("chart v8", lambda: [(s, (lambda js: (js["chart"]["result"][0]["meta"].get("regularMarketPrice"),
                                               js["chart"]["result"][0]["meta"].get("chartPreviousClose"),
                                               len((js["chart"]["result"][0].get("timestamp") or []))))(
                                   YfData().get_raw_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}", params={"range": "1mo", "interval": "1d"})))
                              for s in ("^TASI.SR", "^NOMUC.SR")]),
        ("tasi alt symbols", lambda: {s: len(yf.Ticker(s).history(period="1mo")) for s in ("^TASI", "TASI.SR", "^TASI.SR")})):
    t0 = time.time()
    try:
        print(f"{name}: ok {time.time() - t0:.1f}s -> {str(fn())[:400]}")
    except Exception as e:
        print(f"{name}: FAIL {time.time() - t0:.1f}s -> {type(e).__name__}: {str(e)[:300]}")
