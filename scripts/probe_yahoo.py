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
