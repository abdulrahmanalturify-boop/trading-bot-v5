"""
holders.py - Who owns a company: the share held by institutions, by insiders and by everyone else, the largest institutional
holders, and how the institutions' and insiders' shares moved over the last month.

Yahoo Finance gives the shares as they stand now (majorHoldersBreakdown, from the latest 13F and insider filings), the top
institutional and fund holders, and the insiders' net buying of the last six months. It keeps no history, so the change over
a month comes from holders.json: a weekly snapshot of every company in the site's lists (scripts/build_holders.py, run by
.github/workflows/holders.yml), kept for about a year. A company outside the lists is read live, in the background.
"""
import json
import math
import os
import threading
import time
from datetime import date, timedelta

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(HERE, "holders.json")
KEEP_DAYS = 400                     # the snapshots kept per company


class Missing(Exception):
    pass


# ---------------------------------------------------------------- reading Yahoo's tables (pure, testable)
def _f(v):
    """A number from Yahoo's cells: 0.6213, '62.13%', 1.2e9, None."""
    try:
        if isinstance(v, str):
            s = v.strip().replace(",", "")
            return float(s[:-1]) / 100 if s.endswith("%") else float(s)
        v = float(v)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def parse_major(df):
    """{'inst', 'ins', 'instf', 'n'} as percentages (0-100) and a count, from Ticker.major_holders (the 1.x layout: a
    'Value' column indexed by insidersPercentHeld ...; or the older two columns: value, description)."""
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {}
    vals = {}
    if "Value" in df.columns:
        for k, v in df["Value"].items():
            vals[str(k)] = _f(v)
    elif df.shape[1] >= 2:
        for _, row in df.iterrows():
            d = str(row.iloc[1]).lower()
            v = _f(row.iloc[0])
            if "insider" in d:
                vals["insidersPercentHeld"] = v
            elif "float" in d:
                vals["institutionsFloatPercentHeld"] = v
            elif "number of institutions" in d:
                vals["institutionsCount"] = v
            elif "institution" in d:
                vals["institutionsPercentHeld"] = v
    pct = lambda k: None if vals.get(k) is None else round(vals[k] * 100, 3)
    out = {"inst": pct("institutionsPercentHeld"), "ins": pct("insidersPercentHeld"), "instf": pct("institutionsFloatPercentHeld"),
           "n": int(vals["institutionsCount"]) if vals.get("institutionsCount") else None}
    return {k: v for k, v in out.items() if v is not None}


def parse_holders(df, limit=10):
    """[[holder, pct of shares (0-100), shares, value, change in the holder's shares since its last report (%), date]] from
    Ticker.institutional_holders / mutualfund_holders, largest first."""
    if not isinstance(df, pd.DataFrame) or df.empty or "Holder" not in df.columns:
        return []
    rows = []
    for _, r in df.iterrows():
        pct = _f(r.get("pctHeld", r.get("% Out")))
        chg = _f(r.get("pctChange"))
        dt = r.get("Date Reported")
        try:
            dt = pd.Timestamp(dt).strftime("%Y-%m-%d") if dt is not None and not pd.isna(dt) else None
        except (TypeError, ValueError):
            dt = None
        rows.append([str(r.get("Holder") or "").strip(), None if pct is None else round(pct * 100, 3), _f(r.get("Shares")),
                     _f(r.get("Value")), None if chg is None else round(chg * 100, 2), dt])
    rows = [r for r in rows if r[0]]
    rows.sort(key=lambda r: -(r[1] or 0))
    return rows[:limit]


def parse_insider_6m(df):
    """{'net_pct', 'buys', 'sells'}: the insiders' net buying (+) or selling (-) of the last 6 months as a share of what they
    hold, and how many purchases and sales, from Ticker.insider_purchases."""
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {}
    first = df.columns[0]
    out = {}
    for _, r in df.iterrows():
        name = str(r.get(first, "")).lower()
        shares, trans = _f(r.get("Shares")), _f(r.get("Trans"))
        if name.startswith("% net"):
            out["net_pct"] = None if shares is None else round(shares * 100, 2)
        elif name.startswith("purchases"):
            out["buys"] = int(trans) if trans is not None else None
        elif name.startswith("sales"):
            out["sells"] = int(trans) if trans is not None else None
    return {k: v for k, v in out.items() if v is not None}


def snapshot(t):
    """Everything for one company from a yfinance Ticker (raises Missing when Yahoo sent no ownership at all)."""
    def grab(attr):
        try:
            return getattr(t, attr)
        except Exception:
            return None
    major = parse_major(grab("major_holders"))
    if "inst" not in major and "ins" not in major:
        raise Missing("no ownership")
    top = parse_holders(grab("institutional_holders"))
    funds = parse_holders(grab("mutualfund_holders"), 5)
    out = {"d": date.today().isoformat(), **major, "top": top, "funds": funds, "ins6m": parse_insider_6m(grab("insider_purchases"))}
    reps = [r[5] for r in top if r[5]]
    if reps:
        out["rep"] = max(reps)
    return out


def fetch(sym):
    import yfinance as yf
    return snapshot(yf.Ticker(sym))


def add_history(prev, cur):
    """The company's weekly history with today's shares added (one point per day, the last KEEP_DAYS days)."""
    hist = [h for h in (prev or {}).get("hist", []) if isinstance(h, list) and len(h) == 3]
    point = [cur["d"], cur.get("inst"), cur.get("ins")]
    hist = [h for h in hist if h[0] != cur["d"]] + [point]
    cut = (date.fromisoformat(cur["d"]) - timedelta(days=KEEP_DAYS)).isoformat()
    return sorted(h for h in hist if h[0] >= cut)


def change(item, key, days=30):
    """How much the share (inst or ins, in points) moved since about `days` ago: the snapshot 0.8x-1.5x that old, nearest to
    it. None when the history does not reach that far yet."""
    hist = item.get("hist") or []
    cur = item.get(key)
    if cur is None or not hist:
        return None
    try:
        now = date.fromisoformat(item.get("d") or hist[-1][0])
    except ValueError:
        return None
    col = 1 if key == "inst" else 2
    best = None
    for h in hist:
        try:
            age = (now - date.fromisoformat(h[0])).days
        except ValueError:
            continue
        if days * 0.8 <= age <= days * 1.5 and h[col] is not None:
            if best is None or abs(age - days) < abs(best[0] - days):
                best = (age, h[col])
    return None if best is None else round(cur - best[1], 3)


def split(item):
    """[(key, value)] of the donut: institutions, insiders and everyone else, adding up to 100. Yahoo's institutions can
    pass 100% (shares lent out and bought again are counted twice): then they are shown as what is left beside the insiders."""
    ins = max(0.0, min(100.0, item.get("ins") or 0.0))
    inst = max(0.0, item.get("inst") or 0.0)
    over = inst + ins > 100
    inst = min(inst, 100 - ins)
    rest = max(0.0, 100 - inst - ins)
    return [("inst", inst), ("ins", ins), ("other", rest)], over


# ---------------------------------------------------------------- for the page
_FILE_CACHE = {"mtime": None, "data": {}}
_LIVE, _LOCK = {}, threading.Lock()


def _file():
    try:
        m = os.path.getmtime(FILE)
    except OSError:
        return {}
    if _FILE_CACHE["mtime"] != m:
        try:
            with open(FILE, encoding="utf-8") as f:
                _FILE_CACHE["data"] = json.load(f).get("items", {})
            _FILE_CACHE["mtime"] = m
        except (OSError, ValueError):
            return {}
    return _FILE_CACHE["data"]


def _work(sym):
    try:
        r = fetch(sym)
    except Exception as e:                          # Yahoo busy: tried again in an hour
        r = {"why": f"error {type(e).__name__}", "retry": True}
    _LIVE[sym] = (time.time(), r)


def get(sym):
    """A company's ownership for the page, or None: from holders.json (with its history), else read from Yahoo in the
    background (the page never waits; it shows on the next refresh) and kept 12 hours."""
    sym = sym.upper()
    hit = _file().get(sym)
    if hit and ("inst" in hit or "ins" in hit):
        return hit
    with _LOCK:
        got = _LIVE.get(sym)
        stale = got is not None and got[0] and time.time() - got[0] > (3600 if got[1].get("retry") else 12 * 3600)
        if got is None or stale:
            _LIVE[sym] = (0.0, {})
            threading.Thread(target=_work, args=(sym,), daemon=True).start()
            return None
    r = got[1]
    return r if ("inst" in r or "ins" in r) else None


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "21.8"
