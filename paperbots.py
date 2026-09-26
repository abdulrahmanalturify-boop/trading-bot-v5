"""
paperbots.py - Paper (virtual) trading bots: up to 5 bots, each one = one symbol + one Strategy Lab strategy + virtual money.
A bot trades FORWARD from its start date on real daily prices, with the same engine as the Strategy Lab: signals on the
daily close, orders at the next open, stop loss / take profit / trailing stop checked during the day.

Only each bot's settings are saved. Its trades are replayed from the start date every time the page opens, so no server
has to stay on all day and everyone sees the same results.

Storage (Streamlit > Settings > Secrets):
    SUPABASE_URL = "https://xxxx.supabase.co"
    SUPABASE_KEY = "sb_secret_..."     # the SECRET key (Supabase > Settings > API Keys); it never leaves the server
    BOTS_PASSWORD = "..."              # needed to add or delete bots, so visitors can only watch them
Without Supabase the bots live in a temporary file that is lost when the app restarts (good for trying it out).
"""
import hmac
import json
import os
import tempfile
import threading

import numpy as np
import pandas as pd
import requests
import streamlit as st

import data
import engine

MAX_BOTS = 5
TABLE = "paper_bots"
FIELDS = ["name", "symbol", "strategy", "params", "capital", "fee", "stop_pct", "atr_mult", "tp_pct", "trail_pct", "start_date"]
SETUP_SQL = """create table if not exists paper_bots (
  id bigint generated always as identity primary key,
  name text not null,
  symbol text not null,
  strategy text not null,
  params jsonb not null default '{}'::jsonb,
  capital double precision not null default 10000,
  fee double precision not null default 0.05,
  stop_pct double precision not null default 0,
  atr_mult double precision not null default 0,
  tp_pct double precision not null default 0,
  trail_pct double precision not null default 0,
  start_date date not null default current_date,
  created_at timestamptz not null default now()
);
alter table paper_bots enable row level security;"""


class StoreError(Exception):
    """kind: no_table · auth · network · full · other"""

    def __init__(self, kind, detail=""):
        super().__init__(f"{kind}: {detail}")
        self.kind, self.detail = kind, str(detail)


# ---------------------------------------------------------------- settings from Secrets
def _secret(name):
    try:
        v = st.secrets.get(name)
    except Exception:                      # no secrets file at all (local run)
        v = None
    v = str(v).strip() if v else os.environ.get(name, "").strip()
    return v or None


def backend():
    """'supabase' when both keys are in Secrets, otherwise 'local' (temporary file)."""
    return "supabase" if _secret("SUPABASE_URL") and _secret("SUPABASE_KEY") else "local"


def admin_mode():
    """'password': a password unlocks editing · 'open': anyone can edit (trial mode, no password set) ·
    'locked': Supabase is connected but BOTS_PASSWORD is missing, so nobody can edit from the site."""
    if _secret("BOTS_PASSWORD"):
        return "password"
    return "open" if backend() == "local" else "locked"


def check_password(text):
    pw = _secret("BOTS_PASSWORD") or ""
    return bool(pw) and hmac.compare_digest(str(text or "").encode(), pw.encode())


# ---------------------------------------------------------------- Supabase (REST, no extra package needed)
def _sb():
    url = _secret("SUPABASE_URL").rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[: -len("/rest/v1")]
    key = _secret("SUPABASE_KEY")
    h = {"apikey": key, "Content-Type": "application/json"}
    if key.startswith("eyJ"):              # older "service_role" keys are JWTs and also go in Authorization
        h["Authorization"] = f"Bearer {key}"
    return f"{url}/rest/v1/{TABLE}", h


def _check(r):
    if r.status_code < 300:
        return
    try:
        j = r.json()
    except ValueError:
        j = {}
    code = str(j.get("code", "")) if isinstance(j, dict) else ""
    msg = (j.get("message") if isinstance(j, dict) else None) or r.text[:300]
    if code in ("PGRST205", "42P01") or "does not exist" in msg or "Could not find the table" in msg:
        raise StoreError("no_table", msg)
    if r.status_code in (401, 403) or code == "42501":
        raise StoreError("auth", msg)
    raise StoreError("other", f"HTTP {r.status_code}: {msg}")


def _request(method, url, **kw):
    try:
        return requests.request(method, url, timeout=15, **kw)
    except requests.RequestException as e:
        raise StoreError("network", e) from e


# ---------------------------------------------------------------- temporary local file (trial mode)
_LOCK = threading.Lock()
_LOCAL = os.path.join(tempfile.gettempdir(), "alturaifi_paper_bots.json")


def _local_read():
    try:
        with open(_LOCAL, encoding="utf-8") as f:
            rows = json.load(f)
        return rows if isinstance(rows, list) else []
    except (OSError, ValueError):
        return []


def _local_write(rows):
    tmp = _LOCAL + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    os.replace(tmp, _LOCAL)


# ---------------------------------------------------------------- saved bots
@st.cache_data(ttl=60, show_spinner=False)
def _list_raw(kind):
    if kind == "supabase":
        url, h = _sb()
        r = _request("GET", url, headers=h, params={"select": "*", "order": "id.asc"})
        _check(r)
        rows = r.json()
        return rows if isinstance(rows, list) else []
    with _LOCK:
        return _local_read()


def _num(v, default=0.0):
    try:
        v = float(v)
        return v if np.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def _norm(r):
    """A stored row -> clean bot dict (parameters clipped to the Strategy Lab ranges). None if the row is unusable."""
    try:
        strat = str(r["strategy"])
        params = r.get("params") or {}
        if isinstance(params, str):
            params = json.loads(params)
        clean = {}
        for k, _, lo, hi, dflt, step in engine.STRATEGIES.get(strat, (None, []))[1]:
            v = _num(params.get(k, dflt), dflt)
            v = float(v) if isinstance(step, float) else int(round(v))
            clean[k] = min(max(v, lo), hi)
        sym = str(r["symbol"]).strip().upper()
        return {"id": r["id"], "name": str(r.get("name") or sym)[:40], "symbol": sym, "strategy": strat, "params": clean,
                "capital": max(_num(r.get("capital"), 10000.0), 1.0), "fee": max(_num(r.get("fee")), 0.0),
                "stop_pct": max(_num(r.get("stop_pct")), 0.0), "atr_mult": max(_num(r.get("atr_mult")), 0.0),
                "tp_pct": max(_num(r.get("tp_pct")), 0.0), "trail_pct": max(_num(r.get("trail_pct")), 0.0),
                "start_date": str(r.get("start_date"))[:10], "created_at": str(r.get("created_at") or "")[:19],
                "valid": strat in engine.STRATEGIES and bool(sym)}
    except Exception:
        return None


def list_bots():
    """Saved bots, oldest first. Raises StoreError when Supabase is set up but can't be used."""
    return [b for b in (_norm(r) for r in _list_raw(backend())) if b]


def create_bot(bot):
    """Save a new bot (dict with FIELDS). Raises StoreError('full') at MAX_BOTS."""
    _list_raw.clear()
    if len(list_bots()) >= MAX_BOTS:
        raise StoreError("full")
    rec = {k: bot[k] for k in FIELDS}
    rec["params"] = {k: (float(v) if isinstance(v, float) else int(v)) for k, v in rec["params"].items()}
    if backend() == "supabase":
        url, h = _sb()
        r = _request("POST", url, headers={**h, "Prefer": "return=minimal"}, data=json.dumps(rec))
        _check(r)
    else:
        with _LOCK:
            rows = _local_read()
            rec["id"] = max([int(x.get("id", 0)) for x in rows] + [0]) + 1
            rec["created_at"] = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%S")
            rows.append(rec)
            _local_write(rows)
    _list_raw.clear()


def delete_bot(bot_id):
    if backend() == "supabase":
        url, h = _sb()
        r = _request("DELETE", url, headers=h, params={"id": f"eq.{int(bot_id)}"})
        _check(r)
    else:
        with _LOCK:
            _local_write([x for x in _local_read() if str(x.get("id")) != str(bot_id)])
    _list_raw.clear()


# ---------------------------------------------------------------- simulation
PERIODS = ["2y", "5y", "10y", "max"]


def today_ny():
    """Today's date on Wall Street (a bot created today starts with today's session)."""
    return pd.Timestamp.now(tz="America/New_York").date()


def _period_for(start):
    days = (pd.Timestamp(today_ny()) - pd.Timestamp(start)).days + 450      # + ~300 sessions so SMA 200 etc. are ready
    for p, d in (("2y", 730), ("5y", 1826), ("10y", 3652)):
        if days <= d:
            return p
    return "max"


def load_prices(bots):
    """Daily prices for every bot's symbol + SPY, one batch download (cached by the data module)."""
    if not bots:
        return {}, pd.DataFrame()
    period = max((_period_for(b["start_date"]) for b in bots), key=PERIODS.index)
    syms = sorted({b["symbol"] for b in bots} | {"SPY"})
    px = dict(data.history_many(tuple(syms), period))
    for s in syms:
        if s not in px or len(px[s]) < 2:
            df = data.history(s, period)
            if not df.empty:
                px[s] = df
    return px, px.get("SPY", pd.DataFrame())


def risk_kwargs(bot):
    return {"stop_pct": bot["stop_pct"] or None, "atr_mult": bot["atr_mult"] or None, "tp_pct": bot["tp_pct"] or None,
            "trail_pct": bot["trail_pct"] or None}


def simulate(bot, df, spy=None):
    """Replay the bot from its start date. Returns a dict; 'ok' is False with 'why' = strategy | data when it can't run.
    'waiting' is True when no session has closed since the start date yet."""
    out = {"bot": bot, "ok": False, "why": None, "waiting": False}
    if not bot.get("valid"):
        out["why"] = "strategy"
        return out
    if df is None or df.empty:
        out["why"] = "data"
        return out
    df = df.dropna(subset=["Open", "High", "Low", "Close"]).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    if len(df) < 30:
        out["why"] = "data"
        return out
    start = pd.Timestamp(bot["start_date"])
    if getattr(df.index, "tz", None) is not None:
        start = start.tz_localize(df.index.tz)
    live = np.asarray(df.index >= start)
    cap = float(bot["capital"])

    entries, exits = engine.STRATEGIES[bot["strategy"]][0](df, **bot["params"])
    entries = entries.fillna(False).astype(bool) & live           # no trades before the start date
    exits = exits.fillna(False).astype(bool)
    res = engine.backtest(df, entries, exits, cap, bot["fee"] / 100, **risk_kwargs(bot))
    out.update(ok=True, start=start, full=df, last_date=df.index[-1], entries=entries, exits=exits)

    d = df[live]
    if d.empty:
        out.update(waiting=True, d=d, equity=pd.Series(dtype=float), position=pd.Series(dtype=float),
                   trades=res["trades"].iloc[0:0], metrics=None, bench=None, bench_ret=None, in_pos=False, open=None,
                   next=None, final=cap, ret=0.0, sessions=0)
        return out

    eq, pos = res["equity"][live], res["position"][live]
    tr = res["trades"].reset_index(drop=True)
    m = engine.metrics({"equity": eq, "position": pos, "trades": tr}, d, cap)

    bench = bench_ret = None
    if spy is not None and not spy.empty:
        s = spy["Close"].copy()
        if getattr(s.index, "tz", None) is not None and getattr(eq.index, "tz", None) is None:
            s.index = s.index.tz_localize(None)
        s = s.reindex(eq.index).ffill().bfill()
        if s.notna().all() and float(s.iloc[0]) > 0:
            bench = s / float(s.iloc[0]) * cap
            bench_ret = float((bench.iloc[-1] / cap - 1) * 100)

    in_pos = bool(res["position"].iloc[-1])
    op = tr[tr["Exit Reason"] == "Open"]
    nxt = None
    if in_pos and bool(exits.iloc[-1]):
        nxt = "sell"                        # exit signal on the latest close -> sells at the next open
    elif not in_pos and bool(entries.iloc[-1]):
        nxt = "buy"                         # entry signal on the latest close -> buys at the next open
    out.update(d=d, equity=eq, position=pos, trades=tr, metrics=m, bench=bench, bench_ret=bench_ret, in_pos=in_pos,
               open=op.iloc[0] if len(op) else None, next=nxt, final=float(eq.iloc[-1]),
               ret=float((eq.iloc[-1] / cap - 1) * 100), sessions=len(d))
    return out


def run_all(bots):
    px, spy = load_prices(bots)
    return [simulate(b, px.get(b["symbol"]), spy) for b in bots], spy


def journal(sim):
    """Trades in the Trade Journal / Auto Trader format (for tdash.render and autotrader.stats)."""
    bot, tr = sim["bot"], sim["trades"]
    fee = bot["fee"] / 100
    return pd.DataFrame({"Symbol": [bot["symbol"]] * len(tr), "Type": "Stock", "Contract": bot["symbol"], "Setup": 0, "Sector": "",
                         "Entry Date": pd.to_datetime(tr["Entry Date"]), "Entry": tr["Entry"].astype(float),
                         "Exit Date": pd.to_datetime(tr["Exit Date"]), "Exit": tr["Exit"].astype(float), "Qty": tr["Shares"].astype(float),
                         "P&L $": tr["P&L $"].astype(float), "P&L %": tr["P&L %"].astype(float),
                         "Fees": ((tr["Entry"] + tr["Exit"]) * tr["Shares"] * fee).astype(float), "Days": tr["Bars"],
                         "Exit Reason": tr["Exit Reason"]})

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.1"
