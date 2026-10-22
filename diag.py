"""
diag.py - How the server the site runs on is doing (?diag=1): its processor, memory and load, and how long the data sources take
to answer from it (Yahoo Finance's quotes, history, screeners, a news feed). Nothing secret is shown. Run at most once a minute
per server process (a visit in between gets the last result), so it can't be used to load the server.
"""
import os
import threading
import time

BUILD = "23.4.60"
_LOCK = threading.Lock()
_LAST = {"t": 0.0, "res": None}


def _timed(fn):
    t0 = time.time()
    try:
        out = fn()
        ok = out if isinstance(out, (int, float, str, bool)) or out is None else type(out).__name__
    except Exception as e:
        ok = f"error: {type(e).__name__}: {str(e)[:120]}"
    return {"s": round(time.time() - t0, 2), "got": ok}


def _machine():
    m = {"cpus": os.cpu_count()}
    try:
        m["load"] = os.getloadavg()
    except Exception:
        pass
    try:
        info = {}
        for line in open("/proc/meminfo"):
            k, v = line.split(":", 1)
            if k in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
                info[k] = int(v.split()[0]) // 1024
        m["mem_mb"] = info
    except Exception:
        pass
    try:
        for line in open("/proc/self/status"):
            if line.startswith("VmRSS"):
                m["site_rss_mb"] = int(line.split()[1]) // 1024
    except Exception:
        pass
    try:
        m["arch"] = os.uname().machine
    except Exception:
        pass
    t0 = time.time()
    s = 0
    for i in range(3_000_000):
        s += i * i
    m["cpu_bench_s"] = round(time.time() - t0, 2)          # the same loop takes about 0.2 s on a fast machine
    return m


def _sources():
    import requests
    import yfinance as yf
    out = {}
    out["google"] = _timed(lambda: requests.get("https://www.google.com/generate_204", timeout=20).status_code)
    out["yahoo_chart"] = _timed(lambda: requests.get("https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=5d&interval=1d",
                                                     headers={"User-Agent": "Mozilla/5.0"}, timeout=20).status_code)
    out["yf_history_1"] = _timed(lambda: len(yf.Ticker("MSFT").history(period="5d")))
    out["yf_download_30"] = _timed(lambda: yf.download(["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "JPM", "V",
                                                        "XOM", "UNH", "LLY", "MA", "HD", "PG", "COST", "JNJ", "ABBV", "WMT", "NFLX",
                                                        "CRM", "BAC", "KO", "PEP", "ORCL", "AMD", "CVX", "MRK", "ADBE"],
                                                       period="5d", progress=False, threads=True).shape[0])
    def scr():
        r = yf.screen("day_gainers", count=10)
        return len(r.get("quotes", [])) if isinstance(r, dict) else 0
    out["yf_screen"] = _timed(scr)
    out["news_feed"] = _timed(lambda: len(requests.get("https://feeds.content.dowjones.io/public/rss/mw_topstories", timeout=20).content))
    return out


def run(force=False):
    with _LOCK:
        if not force and _LAST["res"] is not None and time.time() - _LAST["t"] < 60:
            return dict(_LAST["res"], cached=True)
        res = {"at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "machine": _machine()}
        try:
            res["sources"] = _sources()
        except Exception as e:
            res["sources"] = {"error": str(e)[:200]}
        try:
            import warm
            res["warm"] = warm.status()              # the home page's data kept ready: {piece: (age s, seconds it took)}
        except Exception:
            pass
        _LAST.update(t=time.time(), res=res)
        return res
