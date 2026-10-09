"""
scripts/saudi_list.py - The Saudi market's company list for the site, read from Yahoo Finance on a GitHub server (run by
.github/workflows/saudi.yml): every main-market code that answers (####.SR), with Yahoo's names, sector, industry and market
cap, written to research/results/saudi_list.json. It also checks the Yahoo calls the Saudi pages rely on (the TASI index, daily
prices, quotes, the screener, news, search) and logs what came back (research/results/saudi_probe.txt).
"""
import json
import os
import sys
import time
import traceback
import warnings

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "research", "results")
os.makedirs(OUT, exist_ok=True)

import pandas as pd      # noqa: E402
import requests          # noqa: E402
import yfinance as yf    # noqa: E402

RANGES = [(1010, 1899), (2001, 2399), (3001, 3099), (4001, 4399), (5110, 5119), (6001, 6099), (7010, 7299), (8010, 8399)]


def log(*a):
    print(*a, flush=True)


def probe():
    """What the Saudi pages would get from Yahoo."""
    checks = []

    def t(name, fn):
        try:
            v = fn()
            checks.append((name, "ok", str(v)[:600]))
        except Exception as e:
            checks.append((name, "ERROR", f"{type(e).__name__}: {e}"[:600]))
        log(checks[-1][0], checks[-1][1], checks[-1][2][:300])

    def hist(sym, **kw):
        h = yf.Ticker(sym).history(**kw)
        return (len(h), str(h.index[0]) if len(h) else None, str(h.index[-1]) if len(h) else None)
    for idx in ("^TASI.SR", "^NOMUC.SR", "^MT30.SR", "KSA", "FLSA"):
        t(f"history {idx} 2y", lambda idx=idx: hist(idx, period="2y"))
    t("history ^TASI.SR max", lambda: hist("^TASI.SR", period="max"))
    t("history ^TASI.SR start 2024", lambda: hist("^TASI.SR", start="2024-01-01"))
    t("download ^TASI.SR 2y", lambda: (lambda d: (len(d), str(d.index[0]) if len(d) else None))(yf.download("^TASI.SR", period="2y", progress=False)))
    t("download ^TASI.SR 1wk", lambda: (lambda d: (len(d), str(d.index[0]) if len(d) else None))(yf.download("^TASI.SR", period="5y", interval="1wk", progress=False)))
    t("^TASI.SR info", lambda: {k: yf.Ticker("^TASI.SR").info.get(k) for k in ("shortName", "regularMarketPrice", "regularMarketChangePercent", "fiftyDayAverage")})

    def chart(sym, rng):
        from yfinance.data import YfData
        js = YfData().get_raw_json(f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}", params={"range": rng, "interval": "1d"})
        r = js["chart"]["result"][0]
        return len(r.get("timestamp") or []), r.get("meta", {}).get("dataGranularity"), r.get("meta", {}).get("validRanges")
    t("chart api ^TASI.SR 2y", lambda: chart("^TASI.SR", "2y"))
    t("chart api ^TASI.SR 1y", lambda: chart("^TASI.SR", "1y"))

    def quotes():
        from yfinance.data import YfData
        js = YfData().get_raw_json("https://query1.finance.yahoo.com/v7/finance/quote?",
                                   params={"symbols": "2222.SR,1120.SR,^TASI.SR,4264.SR", "formatted": "false", "lang": "en-US", "region": "US"})
        return [(q.get("symbol"), q.get("shortName"), q.get("regularMarketPrice"), q.get("regularMarketChangePercent"), q.get("marketCap"),
                 q.get("fiftyDayAverage"), q.get("trailingPE"), q.get("averageDailyVolume3Month")) for q in js["quoteResponse"]["result"]]
    t("v7 quotes .SR", quotes)
    return checks


def discover():
    """Every Saudi equity Yahoo's screener knows (region sa), with its names and market cap."""
    from yfinance import EquityQuery
    found, offset = {}, 0
    q = EquityQuery("eq", ["region", "sa"])
    while True:
        r = None
        for attempt in range(3):
            try:
                r = yf.screen(q, size=250, offset=offset, sortField="intradaymarketcap", sortAsc=False)
                break
            except Exception as e:
                log("screen retry", offset, e)
                time.sleep(5)
        qs = (r or {}).get("quotes") or []
        for x in qs:
            s = x.get("symbol")
            if s:
                found[s] = {"short": x.get("shortName"), "long": x.get("longName"), "cap": x.get("marketCap"), "exchange": x.get("exchange"),
                            "type": x.get("quoteType"), "price": x.get("regularMarketPrice"), "vol": x.get("averageDailyVolume3Month")}
        log(f"screen offset {offset}: {len(qs)} (total {(r or {}).get('total')})")
        offset += len(qs)
        if not qs or offset >= ((r or {}).get("total") or 0):
            break
        time.sleep(1)
    return found


def details(found):
    """Sector and industry for the main-market codes (4 digits, not 9xxx: Nomu)."""
    out = {}
    for n, s in enumerate(sorted(x for x in found if x.endswith(".SR") and x[:4].isdigit() and not x.startswith("9"))):
        info = {}
        for attempt in range(3):
            try:
                info = yf.Ticker(s).info or {}
                break
            except Exception as e:
                log("info retry", s, e)
                time.sleep(4 * (attempt + 1))
        out[s] = {**found[s], "sector": info.get("sector"), "industry": info.get("industry"), "long": info.get("longName") or found[s].get("long"),
                  "currency": info.get("currency")}
        if n % 25 == 0:
            log(f"details {n}/{len(found)} {s} {out[s]['short']} {out[s]['sector']}")
        time.sleep(0.4)
    return out


def main():
    t0 = time.time()
    lines = []
    try:
        for name, st, v in probe():
            lines.append(f"{st:5s} | {name} | {v}")
    except Exception:
        lines.append(traceback.format_exc())
    open(os.path.join(OUT, "saudi_probe.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    found = discover()
    log(f"found {len(found)} codes in {time.time() - t0:.0f} s")
    det = details(found)
    json.dump({"made": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M UTC"), "companies": det}, open(os.path.join(OUT, "saudi_list.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
    log(f"done: {len(det)} companies in {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
