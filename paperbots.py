"""
paperbots.py - Paper (virtual) trading bots: up to 5 bots that trade with virtual money on real daily prices, forward from
their start date.

Each bot chooses
  * WHAT it trades: one company, a whole sector, an industry (GICS sub-industry), or all companies
    (the S&P 500 + the site's largest companies), and
  * HOW it trades: one or more of the Strategy Lab strategies (any of them can open a trade; a trade closes on the exit
    signal of the strategy that opened it, or by the stop loss / take profit / trailing stop), or a custom rule where n of
    them must agree, or the "combined strategies" of playbooks.py (each brings its own stop, target and time stop; the
    Opening Range Breakout trades 5-minute candles in simulate_orb), and
  * WHAT it buys: stocks, options (calls on buy signals / puts on sell signals, priced with Black-Scholes), or both side by
    side (stocks and options each have their own `max_pos` slots; options are bought first at the open).
Same fills as the Strategy Lab: signals on the daily close, orders at the next open, stops checked during the day.
With a group of stocks the bot holds up to `max_pos` positions, each opened with an equal share of the balance; when more
stocks signal than there are free slots, the strongest over the last 3 months are bought first.
A bot on one company with one strategy gives exactly the Strategy Lab result from its start date.

Only each bot's settings are saved. Its trades are replayed from the start date whenever the page opens, so no server has
to stay on all day and everyone sees the same results.

Storage (Streamlit > Settings > Secrets):
    SUPABASE_URL = "https://xxxx.supabase.co"
    SUPABASE_KEY = "sb_secret_..."     # the SECRET key (Supabase > Settings > API Keys); it never leaves the server
    BOTS_PASSWORD = "..."              # needed to add or delete bots, so visitors can only watch them
Without Supabase the bots live in a temporary file that is lost when the app restarts (good for trying it out).
The table is the one from SETUP_SQL; what the bot trades and its strategies are kept inside the `params` JSON, so bots
saved by the first version of this page keep working.
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

from math import exp

import data
import engine
import playbooks as PB
import ta
import universe as U
from autotrader import bs_call, strike_for

MAX_BOTS = 5
MAX_POS_LIMIT = 20
TABLE = "paper_bots"
KINDS = ("company", "sector", "industry", "all")
COMBO = "__combo__"          # trades opened by a combined (custom) rule carry this strategy name
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
    if "://" not in url and "." not in url:  # only the Project ID was pasted
        url = f"https://{url}.supabase.co"
    elif "://" not in url:
        url = "https://" + url
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


# ---------------------------------------------------------------- what a bot can trade
def _sp500():
    from sp500 import SP500
    return SP500


def sector_members():
    """sector -> symbols (S&P 500 + the site's largest companies), sectors in alphabetical order.
    Each stock sits in one sector: the site's own (Yahoo) sector when it has one, otherwise the S&P 500 list's."""
    out = {}
    for s in all_members():
        out.setdefault(sector_of(s), []).append(s)
    return {k: sorted(out[k]) for k in sorted(out) if k}


def industry_members(sector=None):
    """GICS sub-industry -> S&P 500 symbols (optionally only the industries of one sector)."""
    out = {}
    for s, (_, sec, sub) in _sp500().items():
        if sub and (sector is None or sec == sector):
            out.setdefault(sub, []).append(s)
    return {k: sorted(out[k]) for k in sorted(out)}


def industry_sector(industry):
    for _, sec, sub in _sp500().values():
        if sub == industry:
            return sec
    return None


def all_members():
    return sorted(set(_sp500()) | set(U.STOCKS))


def members(kind, value):
    if kind == "company":
        v = str(value or "").strip().upper()
        return [v] if v else []
    if kind == "sector":
        return sector_members().get(value, [])
    if kind == "industry":
        return industry_members().get(value, [])
    if kind == "all":
        return all_members()
    return []


def sector_of(sym):
    if sym in U.STOCKS:
        return U.STOCKS[sym][1]
    sp = _sp500()
    if sym in sp:
        return sp[sym][1]
    return U.sector_of(sym) if U.known(sym) else ""


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


INSTRUMENTS = ("stock", "options", "both")   # both = stocks on buy signals + options by the option filters, side by side
OPTION_DEFAULTS = {"type": "call", "dte": 30, "strike": 0, "alloc": 5.0, "tp": 100.0, "sl": 50.0}
OPTION_TYPES = ("call", "put", "both")
STRIKES = (-10, -5, 0, 5, 10)            # % out of the money (negative = in the money)
OPT_FEE = 0.65                           # $ per contract, each side (same as the Auto Trader)
TIME_EXIT_DAYS = 5                       # options are sold when this few calendar days are left


def clean_options(o):
    o = {**OPTION_DEFAULTS, **(o or {})}
    return {"type": o["type"] if o["type"] in OPTION_TYPES else "call",
            "dte": int(min(max(_num(o["dte"], 30), 7), 180)),
            "strike": int(min(STRIKES, key=lambda k: abs(k - _num(o["strike"], 0)))),
            "alloc": float(min(max(_num(o["alloc"], 5.0), 0.5), 50.0)),
            "tp": float(min(max(_num(o["tp"], 100.0), 5.0), 2000.0)),
            "sl": float(min(max(_num(o["sl"], 50.0), 5.0), 95.0))}


ALL_STRATEGIES = list(engine.STRATEGIES) + list(PB.PLAYBOOKS)       # fixed order: the first one wins a tie


def is_playbook(name):
    return name in PB.PLAYBOOKS


def spec_of(name):
    """(signal function, [(key, label, min, max, default, step), ...]) of a Strategy Lab strategy or a playbook."""
    return engine.STRATEGIES.get(name) or PB.PLAYBOOKS[name]


def tidy(strategies, instrument, kind):
    """The rules every bot follows: a bot runs either Strategy Lab strategies or combined strategies (playbooks), the
    combined strategies trade shares (each one plans its own stop, target and time stop for them), and the Opening Range
    Breakout runs alone and not on all companies (5-minute prices for 500+ stocks are too much to download).
    Returns (strategies, instrument, ok)."""
    if PB.ORB in strategies:
        return {PB.ORB: strategies[PB.ORB]}, "stock", kind != "all"
    books = {k: v for k, v in strategies.items() if is_playbook(k)}
    if books:
        return books, "stock", True
    return strategies, instrument if instrument in INSTRUMENTS else "stock", True


def window_of(comb):
    """Combined strategies agree when their buy signals fall within this many sessions (1 = the same day)."""
    return int(min(max(_num((comb or {}).get("window"), 5), 1), 20))


def clean_params(strategy, params):
    """Strategy parameters clipped to their ranges (missing ones get the defaults)."""
    out = {}
    snap = is_playbook(strategy)                     # playbook settings also sit on their step grid (e.g. 15 or 30 minutes)
    for k, _, lo, hi, dflt, step in spec_of(strategy)[1]:
        v = _num((params or {}).get(k, dflt), dflt)
        if snap:
            v = lo + round((min(max(v, lo), hi) - lo) / step) * step
            v = round(v, 6)
        v = float(v) if isinstance(step, float) else int(round(v))
        out[k] = min(max(v, lo), hi)
    if strategy == PB.ORB:
        out["last_entry"] = min(PB.last_entry_of(out["or_minutes"], out["last_entry"]), 240)
    return out


def _norm(r):
    """A stored row -> clean bot dict. None if the row is unusable.
    Version 2 rows keep {'v': 2, 'universe': {...}, 'strategies': {...}, 'max_pos': n} in params;
    version 1 rows (first release) are one company + one strategy with flat params."""
    try:
        params = r.get("params") or {}
        if isinstance(params, str):
            params = json.loads(params)
        if isinstance(params, dict) and params.get("v") == 2:
            uni = params.get("universe") or {}
            kind, value = str(uni.get("kind") or "company"), str(uni.get("value") or "")
            raw, max_pos = params.get("strategies") or {}, int(_num(params.get("max_pos"), 5))
            comb = params.get("combine") or {}
            instrument, opts = params.get("instrument") or "stock", params.get("options")
        else:
            kind, value = "company", str(r["symbol"])
            raw, max_pos = {str(r["strategy"]): params}, 1
            comb, instrument, opts = {}, "stock", None
        if kind not in KINDS:
            kind, value = "company", str(r.get("symbol") or "")
        if kind == "company":
            value, max_pos = value.strip().upper(), 1
        if kind == "all":
            value = "all"
        strategies = {s: clean_params(s, raw[s]) for s in ALL_STRATEGIES if s in raw}
        strategies, instrument, allowed = tidy(strategies, instrument, kind)
        combo = comb.get("mode") == "combo" and len(strategies) > 1
        combine = {"mode": "combo" if combo else "any",
                   "min": min(max(int(_num(comb.get("min"), len(strategies))), 1), max(len(strategies), 1)) if combo else 1}
        if combo and all(map(is_playbook, strategies)):
            combine["window"] = window_of(comb)
        return {"id": r["id"], "name": str(r.get("name") or value)[:40], "kind": kind, "value": value,
                "symbol": value if kind == "company" else None, "strategies": strategies, "combine": combine,
                "instrument": instrument, "options": clean_options(opts),
                "max_pos": min(max(max_pos, 1), MAX_POS_LIMIT),
                "capital": max(_num(r.get("capital"), 10000.0), 1.0), "fee": max(_num(r.get("fee")), 0.0),
                "stop_pct": max(_num(r.get("stop_pct")), 0.0), "atr_mult": max(_num(r.get("atr_mult")), 0.0),
                "tp_pct": max(_num(r.get("tp_pct")), 0.0), "trail_pct": max(_num(r.get("trail_pct")), 0.0),
                "start_date": str(r.get("start_date"))[:10], "created_at": str(r.get("created_at") or "")[:19],
                "valid": bool(strategies) and allowed and bool(members(kind, value))}
    except Exception:
        return None


def make_record(name, kind, value, strategies, max_pos, capital, fee, stop_pct, atr_mult, tp_pct, trail_pct, start_date, combine=None,
                instrument="stock", options=None):
    """Settings from the form -> a row for the table (FIELDS).
    combine: None / {'mode': 'any'} = any strategy opens its own trades; {'mode': 'combo', 'min': n} = buy only when at least
    n of the strategies agree (see simulate)."""
    strategies = {s: clean_params(s, p) for s, p in strategies.items() if s in ALL_STRATEGIES}
    strategies, instrument, _ = tidy(strategies, instrument, kind)
    combine = combine or {}
    if combine.get("mode") == "combo" and len(strategies) > 1:
        books = all(map(is_playbook, strategies))
        combine = {"mode": "combo", "min": int(min(max(int(combine.get("min") or len(strategies)), 1), len(strategies))),
                   **({"window": window_of(combine)} if books else {})}
    else:
        combine = {"mode": "any"}
    if kind == "company":
        value, max_pos, sym = str(value).strip().upper(), 1, str(value).strip().upper()
    else:
        sym = "ALL" if kind == "all" else f"{kind.upper()}:{value}"
        value = "all" if kind == "all" else value
    joiner = " & " if combine["mode"] == "combo" else " + "
    return {"name": str(name)[:40], "symbol": sym[:120], "strategy": joiner.join(strategies)[:250],
            "params": {"v": 2, "universe": {"kind": kind, "value": value}, "strategies": strategies,
                       "max_pos": int(min(max(int(max_pos), 1), MAX_POS_LIMIT)), "combine": combine,
                       "instrument": instrument if instrument in INSTRUMENTS else "stock", "options": clean_options(options)},
            "capital": float(capital), "fee": float(fee), "stop_pct": float(stop_pct), "atr_mult": float(atr_mult),
            "tp_pct": float(tp_pct), "trail_pct": float(trail_pct), "start_date": str(start_date)[:10]}


def list_bots():
    """Saved bots, oldest first. Raises StoreError when Supabase is set up but can't be used."""
    return [b for b in (_norm(r) for r in _list_raw(backend())) if b]


def create_bot(rec):
    """Save a new bot (a row from make_record). Raises StoreError('full') at MAX_BOTS."""
    _list_raw.clear()
    if len(list_bots()) >= MAX_BOTS:
        raise StoreError("full")
    rec = json.loads(json.dumps({k: rec[k] for k in FIELDS}, default=float))
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


def update_bot(bot_id, rec):
    """Replace a bot's settings (a row from make_record); its history is replayed from its start date with the new settings."""
    rec = json.loads(json.dumps({k: rec[k] for k in FIELDS}, default=float))
    if backend() == "supabase":
        url, h = _sb()
        r = _request("PATCH", url, headers={**h, "Prefer": "return=minimal"}, params={"id": f"eq.{int(bot_id)}"}, data=json.dumps(rec))
        _check(r)
    else:
        with _LOCK:
            rows = _local_read()
            for x in rows:
                if str(x.get("id")) == str(bot_id):
                    x.update(rec)
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


# ---------------------------------------------------------------- prices
PERIODS = ["2y", "5y", "10y", "max"]


def today_ny():
    """Today's date on Wall Street (a bot created today starts with today's session)."""
    return pd.Timestamp.now(tz="America/New_York").date()


def period_for(start):
    days = (pd.Timestamp(today_ny()) - pd.Timestamp(start)).days + 450      # + ~300 sessions so SMA 200 etc. are ready
    for p, d in (("2y", 730), ("5y", 1826), ("10y", 3652)):
        if days <= d:
            return p
    return "max"


def load_prices(symbols, period, interval="1d"):
    """{symbol: OHLC} in one batch download (cached by the data module); a missing single stock is retried alone."""
    symbols = tuple(dict.fromkeys(s for s in symbols if s))
    px = dict(data.history_many(symbols, period, interval)) if symbols else {}
    missing = [s for s in symbols if s not in px or len(px[s]) < 2]
    if len(missing) <= 3:                  # a single company (or SPY) that the batch missed; big groups just skip gaps
        for s in missing:
            df = data.history(s, period, interval)
            if not df.empty:
                px[s] = df
    return px


def _prep(df):
    df = df.dropna(subset=["Open", "High", "Low", "Close"]).sort_index()
    return df[~df.index.duplicated(keep="last")]


def risk_kwargs(bot):
    return {"stop_pct": bot["stop_pct"] or None, "atr_mult": bot["atr_mult"] or None, "tp_pct": bot["tp_pct"] or None,
            "trail_pct": bot["trail_pct"] or None}


# ---------------------------------------------------------------- the portfolio engine
def _state(entries, exits):
    """1 while a strategy is in its buy state (from its buy signal until its sell signal), else 0. A sell wins a tie."""
    e = entries.fillna(False).astype(bool).to_numpy()
    x = exits.fillna(False).astype(bool).to_numpy()
    return pd.Series(np.where(x, 0.0, np.where(e, 1.0, np.nan)), index=entries.index).ffill().fillna(0.0)


TRADE_COLS = ["Symbol", "Strategy", "Entry Date", "Entry", "Exit Date", "Exit", "Shares", "P&L $", "P&L %", "Bars", "Exit Reason"]
EXTRA_COLS = ["Type", "Contract", "Stock Entry", "Stock Exit", "Fees", "Stop", "Target", "Expiry"]   # Type: Stock / Call / Put; option prices are per share


def _bs(kind, S, K, T, sigma):
    """Black-Scholes price of a call or put (the Auto Trader's model: the stock's own volatility, 4% rate)."""
    c = bs_call(S, K, T, sigma)
    if kind == "Call":
        return c
    return max(K - S, 0.0) if T <= 0 or sigma <= 0 else max(c - S + K * exp(-0.04 * T), 0.0)


def simulate(bot, px, spy=None):
    """Replay the bot from its start date on the prices in px ({symbol: daily OHLC}).
    Returns a dict; 'ok' is False with 'why' = strategy | data when it can't run; 'waiting' is True when no session has
    closed since the start date yet."""
    out = {"bot": bot, "ok": False, "why": None, "waiting": False}
    if not bot.get("valid") or PB.ORB in bot["strategies"]:           # the Opening Range Breakout runs in simulate_orb
        out["why"] = "strategy"
        return out
    frames = {}
    for s in dict.fromkeys(members(bot["kind"], bot["value"])):
        df = px.get(s)
        if df is not None and not df.empty:
            df = _prep(df)
            if len(df) >= 30:
                frames[s] = df
    if not frames:
        out["why"] = "data"
        return out
    syms = sorted(frames)
    idx = frames[syms[0]].index
    for s in syms[1:]:
        idx = idx.union(frames[s].index)
    T, N = len(idx), len(syms)
    start = pd.Timestamp(bot["start_date"])
    if getattr(idx, "tz", None) is not None:
        start = start.tz_localize(idx.tz)
    live = np.asarray(idx >= start)
    names = [s for s in ALL_STRATEGIES if s in bot["strategies"]]        # fixed order: the first one wins a tie
    comb = bot.get("combine") or {}
    books_only = bool(names) and all(map(is_playbook, names))
    combo = comb.get("mode") == "combo" and len(names) > 1 and (books_only or not any(map(is_playbook, names)))
    need = min(max(int(comb.get("min") or len(names)), 1), len(names)) if combo else 1
    # combined strategies that must agree: a buy signal counts only when at least `need` of them signalled within the last
    # `window` sessions; the trade then follows the plan of the strategy whose signal it is
    pb_combo = combo and books_only
    labels = [COMBO] if combo and not pb_combo else names      # what opens a trade: each strategy, or the combined rule
    S = len(labels)
    atr_on = bool(bot["atr_mult"])
    instrument = bot.get("instrument") if bot.get("instrument") in INSTRUMENTS else "stock"
    options = instrument in ("options", "both")
    oc = bot.get("options") or OPTION_DEFAULTS
    want_stock = instrument in ("stock", "both")                       # shares on buy signals
    want_call = options and oc["type"] in ("call", "both")             # calls on buy signals
    want_put = options and oc["type"] in ("put", "both")               # puts on sell signals

    # wide arrays (dates x stocks); each stock's indicators and signals come from its own history, exactly like the lab
    O, H, Lo, C = (np.full((T, N), np.nan) for _ in range(4))
    ATRP, K, MOM = (np.full((T, N), np.nan) for _ in range(3))
    HVP, HVC = (np.full((T, N), np.nan) for _ in range(2))
    ENT, EXT = np.zeros((S, T, N), bool), np.zeros((S, T, N), bool)
    PENT, PEXT = (np.zeros((S, T, N), bool) for _ in range(2)) if want_put else (None, None)
    # playbooks bring a trade plan fixed on the signal bar: stop price, target (absolute, or a multiple of the risk), time stop
    PIDX = [-1] * S
    books = [k for k, name in enumerate(labels) if is_playbook(name)]
    for i, k in enumerate(books):
        PIDX[k] = i
    PSTOP, PTGT, PFLOOR = (np.full((len(books), T, N), np.nan) for _ in range(3))
    TR, MB = np.full(len(books), np.nan), np.zeros(len(books), int)
    for j, s in enumerate(syms):
        df = frames[s]
        p = idx.get_indexer(df.index)
        O[p, j], H[p, j], Lo[p, j], C[p, j] = (df[c].to_numpy(float) for c in ("Open", "High", "Low", "Close"))
        if atr_on:
            a = ta.atr(df).to_numpy(float)
            ATRP[p, j] = np.r_[a[:1], a[:-1]]                  # the ATR of the previous bar (engine: atr_v[i - 1])
        if options:
            hv = (df["Close"].pct_change().rolling(20).std() * np.sqrt(252)).to_numpy(float)
            HVC[p, j], HVP[p, j] = hv, np.r_[np.nan, hv[:-1]]
        K[p, j] = np.arange(len(df))
        MOM[p, j] = df["Close"].pct_change(63).to_numpy(float)
        sig, ind = [], (PB.Ind(df, spy) if PIDX and max(PIDX) >= 0 else None)     # indicators shared by the playbooks
        for k, name in enumerate(names):
            if is_playbook(name):
                e, x, plan = PB.signals(name, df, bot["strategies"][name], market=spy, ind=ind)
                i = PIDX[k]
                PSTOP[i, p, j] = plan["stop"].to_numpy(float)
                if plan["target"] is not None:
                    PTGT[i, p, j] = plan["target"].to_numpy(float)
                if plan.get("floor") is not None:
                    PFLOOR[i, p, j] = plan["floor"].to_numpy(float)
                TR[i] = plan["target_r"] if plan["target_r"] else np.nan
                MB[i] = int(plan["max_bars"] or 0)
                sig.append((e, x))
            else:
                sig.append(engine.STRATEGIES[name][0](df, **bot["strategies"][name]))
        if pb_combo:
            win = window_of(comb)
            recent = [e.fillna(False).astype(bool).astype(float).rolling(win, min_periods=1).max() > 0 for e, _ in sig]
            agree = (sum(r_.astype(int) for r_ in recent) >= need).to_numpy()
            for k, (e, x) in enumerate(sig):
                ENT[k, p, j] = e.fillna(False).astype(bool).to_numpy() & agree
                EXT[k, p, j] = x.fillna(False).astype(bool).to_numpy()
        elif combo:
            # a strategy "agrees" while it is in its buy state (after its own buy signal, until its own sell signal);
            # the bot buys on the day at least `need` agree and sells when fewer than `need` agree
            cond = sum(_state(e, x) for e, x in sig) >= need
            ENT[0, p, j] = (cond & ~cond.shift(1, fill_value=False)).to_numpy()
            EXT[0, p, j] = (~cond).to_numpy()
            if want_put:                                   # puts: bought when the rule breaks, sold when it is met again
                PENT[0, p, j] = (~cond & cond.shift(1, fill_value=False)).to_numpy()
                PEXT[0, p, j] = cond.to_numpy()
        else:
            for k, (e, x) in enumerate(sig):
                ENT[k, p, j] = e.fillna(False).astype(bool).to_numpy()
                EXT[k, p, j] = x.fillna(False).astype(bool).to_numpy()
                if want_put:                               # puts: bought on the strategy's sell signal, sold on its buy signal
                    # (a playbook's exit is a condition that can last for days: its first day is the sell signal)
                    PENT[k, p, j] = PB.first_bar(x).to_numpy() if PIDX[k] >= 0 else EXT[k, p, j]
                    PEXT[k, p, j] = ENT[k, p, j]
    valid = ~np.isnan(C)
    CF = pd.DataFrame(C).ffill().to_numpy()                    # last known close, to value the portfolio every day
    ENT &= live[None, :, None]                                 # no new trades before the start date
    ENT &= valid[None, :, :]
    if want_put:
        PENT &= live[None, :, None]
        PENT &= valid[None, :, :]

    fee, cap = bot["fee"] / 100, float(bot["capital"])
    max_pos = 1 if bot["kind"] == "company" else int(bot["max_pos"])
    rk = risk_kwargs(bot)
    stop_pct, atr_mult, tp_pct, trail_pct = rk["stop_pct"], rk["atr_mult"], rk["tp_pct"], rk["trail_pct"]
    cash, eq_prev = cap, cap
    pos, pend, trades = {}, [], []
    equity, invested, npos = np.empty(T), np.empty(T), np.zeros(T, int)

    def sigma_of(hv, fallback=0.35):
        return float(np.clip((hv if np.isfinite(hv) else fallback) * 1.1, 0.15, 1.5))

    def close(key, t, price, reason, under=None):
        nonlocal cash
        j = key[0]
        q = pos.pop(key)
        if q["kind"] == "Stock":
            proceeds = q["shares"] * price * (1 - fee)
            cost = q["shares"] * q["entry"] * (1 + fee)
            fees = q["shares"] * (q["entry"] + price) * fee
            under = price
        else:
            proceeds = q["shares"] * 100 * price - q["shares"] * OPT_FEE
            cost = q["shares"] * 100 * q["entry"] + q["shares"] * OPT_FEE
            fees = 2 * q["shares"] * OPT_FEE
        plan = q.get("plan", False)                        # a playbook trade keeps its stop and target in the journal
        trades.append({"Symbol": syms[j], "Strategy": labels[q["k"]], "Entry Date": idx[q["t"]], "Entry": q["entry"],
                       "Exit Date": idx[t], "Exit": price, "Shares": q["shares"], "P&L $": proceeds - cost,
                       "P&L %": (proceeds / cost - 1) * 100, "Bars": int(K[t, j] - q["kb"]), "Exit Reason": reason,
                       "Type": q["kind"], "Contract": q["contract"], "Stock Entry": q["s0"], "Stock Exit": under, "Fees": fees,
                       "Stop": q["stop"] if plan and q["stop"] > 0 else np.nan,
                       "Target": q["target"] if plan and np.isfinite(q["target"]) else np.nan, "Expiry": q.get("expiry")})
        cash += proceeds

    def slots(group):
        return max_pos - sum(1 for key, q in pos.items() if key[1] == group and not q["exit"])

    for t in range(T):
        # 1) yesterday's exit signals: sell at today's open
        for key in [key for key, q in pos.items() if q["exit"] and valid[t, key[0]]]:
            q, j = pos[key], key[0]
            if q["kind"] == "Stock":
                close(key, t, O[t, j], q.get("why", "Signal"))
            else:
                t_left = max((q["expiry"] - idx[t]).days, 0)
                close(key, t, _bs(q["kind"], O[t, j], q["K"], t_left / 365, sigma_of(HVP[t, j], q["sigma"])), "Signal", O[t, j])
        # 2) yesterday's entry signals: buy at today's open, best first (options first, so shares get the rest of the cash)
        for j, k, kind, ts in sorted(pend, key=lambda x: x[2] == "Stock"):
            g = "S" if kind == "Stock" else "O"
            if (j, g) in pos or not valid[t, j] or sum(1 for key in pos if key[1] == g) >= max_pos:
                continue
            o = O[t, j]
            if kind == "Stock":                                # one equal slot of the balance
                i = PIDX[k]
                stops, target = [], np.inf
                if i >= 0:                                     # the playbook's plan, from the signal bar
                    ps, pt = PSTOP[i, ts, j], PTGT[i, ts, j]
                    if not np.isfinite(ps) or o <= ps or (np.isfinite(pt) and o >= pt):
                        continue                               # opened under the stop or over the target: no trade
                    stops.append(ps)
                    target = pt if np.isfinite(pt) else (o + TR[i] * (o - ps) if np.isfinite(TR[i]) else np.inf)
                alloc = min(cash, eq_prev / max_pos)
                if alloc <= 0:
                    continue
                shares = alloc / (o * (1 + fee))
                cash -= shares * o * (1 + fee)
                if stop_pct:
                    stops.append(o * (1 - stop_pct / 100))
                if atr_mult and not np.isnan(ATRP[t, j]):
                    stops.append(o - atr_mult * ATRP[t, j])
                if tp_pct:
                    target = min(target, o * (1 + tp_pct / 100))
                pos[(j, "S")] = {"kind": "Stock", "shares": shares, "entry": o, "t": t, "kb": K[t, j], "peak": o,
                                 "stop": max(stops) if stops else 0.0, "target": target,
                                 "k": k, "exit": False, "contract": syms[j], "s0": o}
                if i >= 0:
                    pos[(j, "S")].update(plan=True, mb=int(MB[i]), floor=PFLOOR[i, ts, j])
            else:                                              # options: a % of the balance, priced with Black-Scholes
                sigma = sigma_of(HVP[t, j])
                strike = strike_for(o * (1 + oc["strike"] / 100) if kind == "Call" else o * (1 - oc["strike"] / 100))
                prem = _bs(kind, o, strike, oc["dte"] / 365, sigma)
                if prem < 0.05:
                    continue
                n = int(min(cash, eq_prev * oc["alloc"] / 100) // (prem * 100 + OPT_FEE))
                if n < 1:
                    continue
                cash -= n * (prem * 100 + OPT_FEE)
                expiry = idx[t] + pd.Timedelta(days=oc["dte"])
                pos[(j, "O")] = {"kind": kind, "shares": n, "entry": prem, "t": t, "kb": K[t, j], "k": k, "exit": False, "K": strike,
                                 "expiry": expiry, "sigma": sigma, "value": prem, "s0": o,
                                 "contract": f"{syms[j]} {strike:g}{kind[0]} {expiry:%Y-%m-%d}"}
        pend = []
        # 3) shares: stop loss / trailing stop / take profit during the day · options: value at the close, take profit / stop / time
        for key in list(pos):
            j = key[0]
            if not valid[t, j]:
                continue
            q = pos[key]
            if q["kind"] == "Stock":
                q["peak"] = max(q["peak"], H[t, j])
                trail = q["peak"] * (1 - trail_pct / 100) if trail_pct else 0.0
                eff = max(q["stop"], trail)
                if Lo[t, j] <= eff:
                    close(key, t, min(O[t, j], eff), "Trailing Stop" if trail >= q["stop"] and trail_pct else "Stop Loss")
                elif H[t, j] >= q["target"]:
                    close(key, t, max(O[t, j], q["target"]), "Take Profit")
                continue
            t_left = (q["expiry"] - idx[t]).days
            q["value"] = _bs(q["kind"], C[t, j], q["K"], max(t_left, 0) / 365, sigma_of(HVC[t, j], q["sigma"]))
            why = None
            if q["value"] >= q["entry"] * (1 + oc["tp"] / 100):
                why = "Take Profit"
            elif q["value"] <= q["entry"] * (1 - oc["sl"] / 100):
                why = "Stop Loss"
            elif t_left <= TIME_EXIT_DAYS:
                why = "Time Exit"
            if why:
                close(key, t, q["value"], why, C[t, j])
        # 4) signals at the close: the rule that opened a trade decides its exit; new signals fill the free slots
        for (j, g), q in pos.items():
            if not valid[t, j]:
                continue
            if (PEXT if q["kind"] == "Put" else EXT)[q["k"], t, j]:
                q["exit"] = True
            elif q.get("plan") and C[t, j] < q["floor"]:
                q["exit"] = True                                # closed under the trade's own failure line (NaN = none)
            elif q.get("mb") and not q["exit"] and K[t, j] - q["kb"] >= q["mb"] - 1:
                q["exit"], q["why"] = True, "Time Stop"         # held max_bars sessions: sell at the next open
        if live[t]:
            cand = []
            if want_stock or want_call:
                row = ENT[:, t, :]
                for j in np.flatnonzero(row.any(axis=0)):
                    m_ = MOM[t, j]
                    rank_ = (-m_ if not np.isnan(m_) else np.inf, syms[j])
                    if want_stock and (j, "S") not in pos:
                        cand.append((rank_, int(j), int(np.argmax(row[:, j])), "Stock"))
                    if want_call and (j, "O") not in pos:
                        cand.append((rank_, int(j), int(np.argmax(row[:, j])), "Call"))
            if want_put:                                       # puts: the weakest of the last 3 months first
                row = PENT[:, t, :]
                taken = {c[1] for c in cand if c[3] != "Stock"}
                for j in np.flatnonzero(row.any(axis=0)):
                    if (j, "O") not in pos and j not in taken:
                        m_ = MOM[t, j]
                        cand.append(((m_ if not np.isnan(m_) else np.inf, syms[j]), int(j), int(np.argmax(row[:, j])), "Put"))
            cand.sort(key=lambda c: c[0])
            free = {"S": slots("S"), "O": slots("O")}
            for _, j, k, kind in cand:
                g = "S" if kind == "Stock" else "O"
                if free[g] > 0:
                    pend.append((j, k, kind, t))
                    free[g] -= 1
        # 5) value at the close
        mv = float(sum(q["shares"] * CF[t, key[0]] if q["kind"] == "Stock" else q["shares"] * 100 * q["value"] for key, q in pos.items()))
        equity[t] = cash + mv
        invested[t] = mv / equity[t] if equity[t] > 0 else 0.0
        npos[t] = len(pos)
        eq_prev = equity[t]

    open_rows = []
    for (j, g), q in pos.items():
        tl = int(np.flatnonzero(valid[:, j])[-1])
        c_last = C[tl, j]
        stop_lvl = target_lvl = np.nan
        if q["kind"] == "Stock":
            basis = q["entry"] * (1 + fee)
            pnl, pct, exit_px = q["shares"] * (c_last - basis), (c_last / basis - 1) * 100, c_last
            fees = q["shares"] * q["entry"] * fee
            eff = max(q["stop"], q["peak"] * (1 - trail_pct / 100) if trail_pct else 0.0)
            stop_lvl = eff if eff > 0 else np.nan
            target_lvl = q["target"] if np.isfinite(q["target"]) else np.nan
        else:
            cost = q["shares"] * 100 * q["entry"] + q["shares"] * OPT_FEE
            pnl = q["shares"] * 100 * q["value"] - cost
            pct, exit_px, fees = pnl / cost * 100, q["value"], q["shares"] * OPT_FEE
            stop_lvl, target_lvl = q["entry"] * (1 - oc["sl"] / 100), q["entry"] * (1 + oc["tp"] / 100)
        open_rows.append({"Symbol": syms[j], "Strategy": labels[q["k"]], "Entry Date": idx[q["t"]], "Entry": q["entry"],
                          "Exit Date": idx[tl], "Exit": exit_px, "Shares": q["shares"], "P&L $": pnl, "P&L %": pct,
                          "Bars": int(K[tl, j] - q["kb"]), "Exit Reason": "Open", "Type": q["kind"], "Contract": q["contract"],
                          "Stock Entry": q["s0"], "Stock Exit": c_last, "Fees": fees, "Stop": stop_lvl, "Target": target_lvl,
                          "Expiry": q.get("expiry")})
    tr = pd.DataFrame(trades + open_rows, columns=TRADE_COLS + EXTRA_COLS)
    out.update(ok=True, start=start, symbols=syms, n_symbols=N, last_date=idx[-1], trades=tr, max_pos=max_pos,
               next_buys=[(syms[j], labels[k], kind) for j, k, kind, _ in pend],
               next_sells=[(syms[j], labels[q["k"]], q["kind"]) for (j, g), q in pos.items() if q["exit"]],
               n_open=len(pos), in_pos=bool(pos), cash=float(cash))
    if bot["kind"] == "company":
        out["frame"] = frames[syms[0]]

    if not live.any():
        out.update(waiting=True, equity=pd.Series(dtype=float), invested=pd.Series(dtype=float), npos=pd.Series(dtype=float),
                   metrics=None, bench=None, bench_ret=None, group_ret=None, final=cap, ret=0.0, sessions=0)
        return out

    li = idx[live]
    eq = pd.Series(equity[live], index=li)
    inv = pd.Series(invested[live], index=li)
    t0 = int(np.flatnonzero(live)[0])
    cols = np.flatnonzero(~np.isnan(CF[t0]))
    grp = pd.Series(np.nanmean(CF[live][:, cols] / CF[t0, cols], axis=1) * cap, index=li)   # the group bought equally
    m = engine.metrics({"equity": eq, "position": inv, "trades": tr}, pd.DataFrame({"Close": grp}), cap)

    bench = bench_ret = None
    if spy is not None and not spy.empty:
        s = spy["Close"].copy()
        if getattr(s.index, "tz", None) is not None and getattr(li, "tz", None) is None:
            s.index = s.index.tz_localize(None)
        s = s[~s.index.duplicated(keep="last")].reindex(li).ffill().bfill()
        if s.notna().all() and float(s.iloc[0]) > 0:
            bench = s / float(s.iloc[0]) * cap
            bench_ret = float((bench.iloc[-1] / cap - 1) * 100)
    out.update(equity=eq, invested=inv, npos=pd.Series(npos[live], index=li), metrics=m, bench=bench, bench_ret=bench_ret,
               group=grp, group_ret=float((grp.iloc[-1] / cap - 1) * 100), final=float(eq.iloc[-1]),
               ret=float((eq.iloc[-1] / cap - 1) * 100), sessions=int(live.sum()))
    return out


def simulate_orb(bot, px5, pxd, spy=None, now=None):
    """The Opening Range Breakout bot on 5-minute candles (px5 {symbol: 5-minute OHLCV}, pxd {symbol: daily OHLC} for the
    ATR). Every trade opens and closes on the same day; when more stocks break out than there are free slots, the ones
    that broke out first are taken (a tie goes to the higher relative volume). Each trade gets an equal slot of the
    balance at the day's open. Yahoo keeps 5-minute prices for 60 days, so the bot shows the last 60 days at most (the
    first 5 sessions only build the relative volume). Same result dict as simulate(), plus 'intraday' and 'days5'."""
    out = {"bot": bot, "ok": False, "why": None, "waiting": False, "intraday": True}
    if not bot.get("valid") or PB.ORB not in bot["strategies"]:
        out["why"] = "strategy"
        return out
    prm = bot["strategies"][PB.ORB]
    now = pd.Timestamp(now) if now is not None else pd.Timestamp.now(tz=PB.NY).tz_localize(None)
    bars, sig = {}, {}
    for s in dict.fromkeys(members(bot["kind"], bot["value"])):
        b = PB.ny_bars(px5.get(s))
        if b.index.normalize().nunique() >= PB.BASE_MIN + 1:
            bars[s] = b
            sig[s] = PB.orb_trades(b, pxd.get(s), now=now, **prm)
    if not bars:
        out["why"] = "data"
        return out
    syms = sorted(bars)
    days = pd.DatetimeIndex(sorted(set().union(*(set(b.index.normalize()) for b in bars.values()))))
    start = max(pd.Timestamp(bot["start_date"]), days[min(PB.BASE_MIN, len(days) - 1)])
    live_days = days[days >= start]
    cap, fee = float(bot["capital"]), bot["fee"] / 100
    max_pos = 1 if bot["kind"] == "company" else int(bot["max_pos"])
    cand = [dict(r, Symbol=s) for s in syms for r in sig[s].to_dict("records") if r["Day"] >= start]
    five = pd.Timedelta(minutes=5)
    for r in cand:                                         # a pending order would enter at the next candle's open
        r["_at"] = r["Signal"] + five if r["Pending"] else r["Entry Time"]
    cand.sort(key=lambda r: (r["_at"], -r["RVOL"], r["Symbol"]))
    by_day = {}
    for r in cand:
        by_day.setdefault(r["Day"], []).append(r)
    # the day's last close of every stock (to value the group and the open trades)
    closes = pd.DataFrame({s: b["Close"].groupby(b.index.normalize()).last() for s, b in bars.items()}).reindex(days).ffill()
    last_bar = {s: (b.index[-1], float(b["Close"].iloc[-1])) for s, b in bars.items()}
    equity, trades, open_rows, next_buys, days5 = cap, [], [], [], {}
    eq, inv, npos = [], [], []
    cash = cap
    for d in live_days:
        alloc, busy, pnl_day, held_value, n_open, reserved = equity / max_pos, [], 0.0, 0.0, 0, 0
        for r in by_day.get(d, []):
            at = r["_at"]
            if sum(1 for x in busy if x >= at) + reserved >= max_pos:
                continue                                   # every slot is taken at that moment
            side = 1 if r["Side"] == "Long" else -1
            kind = "Stock" if side > 0 else "Short"
            if r["Pending"]:
                next_buys.append((r["Symbol"], PB.ORB, kind))
                reserved += 1                              # the order holds its slot until the next candle
                continue
            busy.append(r["Exit Bar"])
            entry = float(r["Entry"])
            shares = alloc / (entry * (1 + fee))
            cost = shares * entry * (1 + fee)
            days5.setdefault(f'{r["Symbol"]}|{d:%Y-%m-%d}', True)
            row = {"Symbol": r["Symbol"], "Strategy": PB.ORB, "Entry Date": r["Entry Time"], "Entry": entry, "Shares": shares,
                   "Bars": int(r["Bars"]), "Type": kind, "Contract": r["Symbol"], "Stock Entry": entry, "Stop": float(r["Stop"]),
                   "Target": float(r["Target"]), "Expiry": None}
            if r["Open"]:                                  # today's session is still trading
                last = float(r["Exit"])
                pnl = shares * (last - entry) * side - shares * entry * fee
                open_rows.append({**row, "Exit Date": r["Exit Time"], "Exit": last, "P&L $": pnl, "P&L %": pnl / cost * 100,
                                  "Exit Reason": "Open", "Stock Exit": last, "Fees": shares * entry * fee})
                held_value += cost + pnl
                n_open += 1
                pnl_day += pnl
                continue
            exit_px = float(r["Exit"])
            fees = shares * (entry + exit_px) * fee
            pnl = shares * (exit_px - entry) * side - fees
            trades.append({**row, "Exit Date": r["Exit Time"], "Exit": exit_px, "P&L $": pnl, "P&L %": pnl / cost * 100,
                           "Exit Reason": r["Reason"], "Stock Exit": exit_px, "Fees": fees})
            pnl_day += pnl
        value = equity + pnl_day                           # open trades (today only) are valued at their last price
        eq.append(value)
        inv.append(min(len(busy), max_pos) / max_pos)      # the share of the slots the day used
        npos.append(len(busy))                             # trades held during the day (all are closed by the end of it)
        cash = value - held_value
        if not n_open:
            equity = value
    tr = pd.DataFrame(trades + open_rows, columns=TRADE_COLS + EXTRA_COLS)
    if bot["kind"] == "company" or len(days5) <= 400:     # the traded days (and the last one) for the day chart
        keep = set(days5) | ({f"{syms[0]}|{days[-1]:%Y-%m-%d}"} if bot["kind"] == "company" else set())
        days5 = {}
        for key in sorted(keep):
            sym, day = key.split("|")
            b = bars[sym]
            day_b = b[b.index.normalize() == pd.Timestamp(day)]
            if len(day_b):
                days5[key] = PB.with_vwap(day_b)[["Open", "High", "Low", "Close", "Volume", "VWAP"]]
    else:
        days5 = {}
    out.update(ok=True, start=start, symbols=syms, n_symbols=len(syms), last_date=days[-1], trades=tr, max_pos=max_pos,
               next_buys=next_buys, next_sells=[], n_open=len(open_rows), in_pos=bool(open_rows), cash=float(cash),
               days5=days5, first_day=days[0], last_bar=max(t for t, _ in last_bar.values()))
    if bot["kind"] == "company":
        d0 = pxd.get(syms[0])
        out["frame"] = _prep(d0) if d0 is not None and len(d0) else None
    if not len(live_days):
        out.update(waiting=True, equity=pd.Series(dtype=float), invested=pd.Series(dtype=float), npos=pd.Series(dtype=float),
                   metrics=None, bench=None, bench_ret=None, group_ret=None, final=cap, ret=0.0, sessions=0)
        return out
    eqs = pd.Series(eq, index=live_days)
    invs = pd.Series(inv, index=live_days)
    cl = closes.loc[live_days]
    cols = [c for c in cl.columns if np.isfinite(cl[c].iloc[0]) and cl[c].iloc[0] > 0]
    grp = (cl[cols] / cl[cols].iloc[0]).mean(axis=1) * cap if cols else pd.Series(cap, index=live_days)
    m = engine.metrics({"equity": eqs, "position": invs, "trades": tr}, pd.DataFrame({"Close": grp}), cap)
    bench, bench_ret = _bench(spy, live_days, cap)
    out.update(equity=eqs, invested=invs, npos=pd.Series(npos, index=live_days, dtype=float), metrics=m, bench=bench,
               bench_ret=bench_ret, group=grp, group_ret=float((grp.iloc[-1] / cap - 1) * 100), final=float(eqs.iloc[-1]),
               ret=float((eqs.iloc[-1] / cap - 1) * 100), sessions=len(live_days))
    return out


def _bench(spy, li, cap):
    """SPY bought with the same capital on the first day (None when SPY is missing)."""
    if spy is None or spy.empty:
        return None, None
    s = spy["Close"].copy()
    if getattr(s.index, "tz", None) is not None and getattr(li, "tz", None) is None:
        s.index = s.index.tz_localize(None)
    s = s[~s.index.duplicated(keep="last")].reindex(li).ffill().bfill()
    if s.notna().all() and float(s.iloc[0]) > 0:
        bench = s / float(s.iloc[0]) * cap
        return bench, float((bench.iloc[-1] / cap - 1) * 100)
    return None, None


@st.cache_data(ttl=600, show_spinner=False, max_entries=24)
def _run_cached(bot_json, build=None):
    """build: the site version, so results cached by an older version of the engine are never reused."""
    bot = json.loads(bot_json)
    if PB.ORB in bot.get("strategies", {}):          # 5-minute candles (Yahoo keeps 60 days) + daily ones for the ATR
        syms = members(bot["kind"], bot["value"]) if bot.get("valid") else []
        px5 = load_prices(syms, "60d", "5m")
        pxd = load_prices(list(syms) + ["SPY"], "1y")
        return simulate_orb(bot, px5, pxd, pxd.get("SPY"))
    period = period_for(bot["start_date"])
    px = load_prices(members(bot["kind"], bot["value"]), period)
    spy = px.get("SPY")
    if spy is None or len(spy) < 2:
        spy = data.history("SPY", period)
    return simulate(bot, px, spy)


def run_all(bots):
    """Every bot replayed (each result cached for 10 minutes, like the prices) + SPY for the comparison chart."""
    sims = []
    for b in bots:
        sim = dict(_run_cached(json.dumps(b, sort_keys=True, default=str), BUILD))
        sim["bot"] = b                       # the saved settings as they are (the cache key sorts the JSON)
        sims.append(sim)
    period = max((period_for(b["start_date"]) for b in bots), key=PERIODS.index) if bots else "2y"
    return sims, data.history("SPY", period)


def journal(sim):
    """Trades in the Trade Journal / Auto Trader format (for tdash.render and autotrader.stats)."""
    tr = sim["trades"]
    return pd.DataFrame({"Symbol": tr["Symbol"].astype(str), "Type": tr["Type"].astype(str), "Contract": tr["Contract"].astype(str), "Setup": 0,
                         "Sector": [sector_of(s) for s in tr["Symbol"]],
                         "Entry Date": pd.to_datetime(tr["Entry Date"]), "Entry": tr["Entry"].astype(float),
                         "Exit Date": pd.to_datetime(tr["Exit Date"]), "Exit": tr["Exit"].astype(float), "Qty": tr["Shares"].astype(float),
                         "P&L $": tr["P&L $"].astype(float), "P&L %": tr["P&L %"].astype(float), "Fees": tr["Fees"].astype(float),
                         "Days": tr["Bars"], "Exit Reason": tr["Exit Reason"]})

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.8"
