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

    for idx in ("^TASI.SR", "^TASI", "TASI.SR", "^NOMUC.SR"):
        t(f"index history {idx}", lambda idx=idx: (lambda h: (len(h), str(h.index[-1]) if len(h) else None, float(h["Close"].iloc[-1]) if len(h) else None))(yf.Ticker(idx).history(period="1mo")))
    t("2222.SR daily (tz, last rows)", lambda: (lambda h: (len(h), str(h.index.tz), h.tail(3)[["Open", "Close"]].round(2).to_dict()))(yf.Ticker("2222.SR").history(period="1mo")))
    def dl():
        df = yf.download(["2222.SR", "1120.SR", "2010.SR"], period="2y", progress=False, group_by="ticker")
        return {k: int(df[k]["Close"].notna().sum()) for k in ("2222.SR", "1120.SR", "2010.SR")}, str(df.index[-1])
    t("download 2222/1120/2010 2y", dl)
    t("2222.SR info keys", lambda: {k: yf.Ticker("2222.SR").info.get(k) for k in ("longName", "shortName", "sector", "industry", "marketCap", "currency", "exchange",
                                                                                   "trailingPE", "dividendYield", "fullExchangeName", "quoteType")})
    t("2222.SR fast_info", lambda: dict(yf.Ticker("2222.SR").fast_info))
    t("2222.SR news", lambda: [(n.get("content", n).get("title"), n.get("content", n).get("pubDate")) for n in (yf.Ticker("2222.SR").news or [])[:5]])
    t("search Al Rajhi", lambda: [(q.get("symbol"), q.get("shortname"), q.get("exchange")) for q in yf.Search("Al Rajhi Bank", max_results=8).quotes])
    t("search الراجحي", lambda: [(q.get("symbol"), q.get("shortname"), q.get("exchange")) for q in yf.Search("الراجحي", max_results=8).quotes])
    t("search 2222", lambda: [(q.get("symbol"), q.get("shortname"), q.get("exchange")) for q in yf.Search("2222", max_results=8).quotes])

    def screen():
        from yfinance import EquityQuery
        q = EquityQuery("and", [EquityQuery("eq", ["region", "sa"]), EquityQuery("gt", ["intradaymarketcap", 1e9])])
        r = yf.screen(q, size=100, sortField="intradaymarketcap", sortAsc=False)
        qs = r.get("quotes", [])
        return {"total": r.get("total"), "n": len(qs), "first": [(x.get("symbol"), x.get("shortName"), x.get("marketCap"), x.get("trailingPE")) for x in qs[:6]],
                "fields": sorted(qs[0].keys())[:80] if qs else []}
    t("screener region sa", screen)

    def rss(q, hl="ar", gl="SA"):
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl={hl}&gl={gl}&ceid={gl}:{hl}"
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        import re
        titles = re.findall(r"<title>(.*?)</title>", r.text)[1:6]
        return (r.status_code, len(re.findall(r"<item>", r.text)), titles)
    t("google news ar السوق السعودية", lambda: rss("السوق السعودية أسهم"))
    t("google news en Saudi stocks", lambda: rss("Saudi stocks Tadawul", "en", "SA"))
    t("argaam rss", lambda: (lambda r: (r.status_code, r.headers.get("content-type"), r.text[:300]))(requests.get("https://www.argaam.com/ar/rss/ho-main-news?sectionid=1524", timeout=20, headers={"User-Agent": "Mozilla/5.0"})))
    t("hourly prepost 2222", lambda: len(yf.download("2222.SR", period="5d", interval="1h", progress=False)))
    return checks


def discover():
    """Every main-market code Yahoo has daily prices for (the last 10 days)."""
    cands = [f"{c}.SR" for a, b in RANGES for c in range(a, b + 1)]
    found = {}
    for i in range(0, len(cands), 80):
        chunk = cands[i:i + 80]
        for attempt in range(3):
            try:
                df = yf.download(chunk, period="10d", progress=False, group_by="ticker", threads=True)
                break
            except Exception as e:
                log("retry", i, e)
                time.sleep(5)
        else:
            continue
        for s in chunk:
            try:
                sub = df[s] if s in df.columns.get_level_values(0) else None
            except Exception:
                sub = None
            if sub is not None and sub["Close"].notna().sum() >= 1:
                found[s] = {"last": float(sub["Close"].dropna().iloc[-1]), "days": int(sub["Close"].notna().sum()),
                            "vol": float(sub["Volume"].fillna(0).mean())}
        log(f"{i + len(chunk)}/{len(cands)} checked, {len(found)} found")
        time.sleep(1)
    return found


def details(found):
    out = {}
    for n, s in enumerate(sorted(found)):
        info = {}
        for attempt in range(3):
            try:
                info = yf.Ticker(s).info or {}
                break
            except Exception as e:
                log("info retry", s, e)
                time.sleep(4 * (attempt + 1))
        out[s] = {"long": info.get("longName"), "short": info.get("shortName"), "sector": info.get("sector"), "industry": info.get("industry"),
                  "cap": info.get("marketCap"), "currency": info.get("currency"), "type": info.get("quoteType"), "exchange": info.get("exchange"),
                  **found[s]}
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
