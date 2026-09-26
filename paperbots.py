"""
paperbots.py - Paper (virtual) trading bots: up to 5 bots that trade with virtual money on real daily prices, forward from
their start date.

Each bot chooses
  * WHAT it trades: one company, a whole sector, an industry (GICS sub-industry), or all companies
    (the S&P 500 + the site's largest companies), and
  * HOW it trades: one or more of the Strategy Lab strategies (any of them can open a trade; a trade closes on the exit
    signal of the strategy that opened it, or by the stop loss / take profit / trailing stop).
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

import data
import engine
import ta
import universe as U

MAX_BOTS = 5
MAX_POS_LIMIT = 20
TABLE = "paper_bots"
KINDS = ("company", "sector", "industry", "all")
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


def clean_params(strategy, params):
    """Strategy parameters clipped to the Strategy Lab ranges (missing ones get the defaults)."""
    out = {}
    for k, _, lo, hi, dflt, step in engine.STRATEGIES[strategy][1]:
        v = _num((params or {}).get(k, dflt), dflt)
        v = float(v) if isinstance(step, float) else int(round(v))
        out[k] = min(max(v, lo), hi)
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
        else:
            kind, value = "company", str(r["symbol"])
            raw, max_pos = {str(r["strategy"]): params}, 1
        if kind not in KINDS:
            kind, value = "company", str(r.get("symbol") or "")
        if kind == "company":
            value, max_pos = value.strip().upper(), 1
        if kind == "all":
            value = "all"
        strategies = {s: clean_params(s, raw[s]) for s in engine.STRATEGIES if s in raw}
        return {"id": r["id"], "name": str(r.get("name") or value)[:40], "kind": kind, "value": value,
                "symbol": value if kind == "company" else None, "strategies": strategies,
                "max_pos": min(max(max_pos, 1), MAX_POS_LIMIT),
                "capital": max(_num(r.get("capital"), 10000.0), 1.0), "fee": max(_num(r.get("fee")), 0.0),
                "stop_pct": max(_num(r.get("stop_pct")), 0.0), "atr_mult": max(_num(r.get("atr_mult")), 0.0),
                "tp_pct": max(_num(r.get("tp_pct")), 0.0), "trail_pct": max(_num(r.get("trail_pct")), 0.0),
                "start_date": str(r.get("start_date"))[:10], "created_at": str(r.get("created_at") or "")[:19],
                "valid": bool(strategies) and bool(members(kind, value))}
    except Exception:
        return None


def make_record(name, kind, value, strategies, max_pos, capital, fee, stop_pct, atr_mult, tp_pct, trail_pct, start_date):
    """Settings from the form -> a row for the table (FIELDS)."""
    strategies = {s: clean_params(s, p) for s, p in strategies.items() if s in engine.STRATEGIES}
    if kind == "company":
        value, max_pos, sym = str(value).strip().upper(), 1, str(value).strip().upper()
    else:
        sym = "ALL" if kind == "all" else f"{kind.upper()}:{value}"
        value = "all" if kind == "all" else value
    return {"name": str(name)[:40], "symbol": sym[:120], "strategy": " + ".join(strategies)[:250],
            "params": {"v": 2, "universe": {"kind": kind, "value": value}, "strategies": strategies,
                       "max_pos": int(min(max(int(max_pos), 1), MAX_POS_LIMIT))},
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


def load_prices(symbols, period):
    """{symbol: daily OHLC} in one batch download (cached by the data module); a missing single stock is retried alone."""
    symbols = tuple(dict.fromkeys(s for s in symbols if s))
    px = dict(data.history_many(symbols, period)) if symbols else {}
    missing = [s for s in symbols if s not in px or len(px[s]) < 2]
    if len(missing) <= 3:                  # a single company (or SPY) that the batch missed; big groups just skip gaps
        for s in missing:
            df = data.history(s, period)
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
TRADE_COLS = ["Symbol", "Strategy", "Entry Date", "Entry", "Exit Date", "Exit", "Shares", "P&L $", "P&L %", "Bars", "Exit Reason"]


def simulate(bot, px, spy=None):
    """Replay the bot from its start date on the prices in px ({symbol: daily OHLC}).
    Returns a dict; 'ok' is False with 'why' = strategy | data when it can't run; 'waiting' is True when no session has
    closed since the start date yet."""
    out = {"bot": bot, "ok": False, "why": None, "waiting": False}
    if not bot.get("valid"):
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
    names = [s for s in engine.STRATEGIES if s in bot["strategies"]]      # fixed order: the first one wins a tie
    S = len(names)
    atr_on = bool(bot["atr_mult"])

    # wide arrays (dates x stocks); each stock's indicators and signals come from its own history, exactly like the lab
    O, H, Lo, C = (np.full((T, N), np.nan) for _ in range(4))
    ATRP, K, MOM = (np.full((T, N), np.nan) for _ in range(3))
    ENT, EXT = np.zeros((S, T, N), bool), np.zeros((S, T, N), bool)
    for j, s in enumerate(syms):
        df = frames[s]
        p = idx.get_indexer(df.index)
        O[p, j], H[p, j], Lo[p, j], C[p, j] = (df[c].to_numpy(float) for c in ("Open", "High", "Low", "Close"))
        if atr_on:
            a = ta.atr(df).to_numpy(float)
            ATRP[p, j] = np.r_[a[:1], a[:-1]]                  # the ATR of the previous bar (engine: atr_v[i - 1])
        K[p, j] = np.arange(len(df))
        MOM[p, j] = df["Close"].pct_change(63).to_numpy(float)
        for k, name in enumerate(names):
            e, x = engine.STRATEGIES[name][0](df, **bot["strategies"][name])
            ENT[k, p, j] = e.fillna(False).astype(bool).to_numpy()
            EXT[k, p, j] = x.fillna(False).astype(bool).to_numpy()
    valid = ~np.isnan(C)
    CF = pd.DataFrame(C).ffill().to_numpy()                    # last known close, to value the portfolio every day
    ENT &= live[None, :, None]                                 # no new trades before the start date
    ENT &= valid[None, :, :]

    fee, cap = bot["fee"] / 100, float(bot["capital"])
    max_pos = 1 if bot["kind"] == "company" else int(bot["max_pos"])
    rk = risk_kwargs(bot)
    stop_pct, atr_mult, tp_pct, trail_pct = rk["stop_pct"], rk["atr_mult"], rk["tp_pct"], rk["trail_pct"]
    cash, eq_prev = cap, cap
    pos, pend, trades = {}, [], []
    equity, invested, npos = np.empty(T), np.empty(T), np.zeros(T, int)

    def close(j, t, price, reason):
        nonlocal cash
        q = pos.pop(j)
        proceeds = q["shares"] * price * (1 - fee)
        cost = q["shares"] * q["entry"] * (1 + fee)
        trades.append({"Symbol": syms[j], "Strategy": names[q["k"]], "Entry Date": idx[q["t"]], "Entry": q["entry"],
                       "Exit Date": idx[t], "Exit": price, "Shares": q["shares"], "P&L $": proceeds - cost,
                       "P&L %": (proceeds / cost - 1) * 100, "Bars": int(K[t, j] - q["kb"]), "Exit Reason": reason})
        cash += proceeds

    for t in range(T):
        # 1) yesterday's exit signals: sell at today's open
        for j in [j for j, q in pos.items() if q["exit"] and valid[t, j]]:
            close(j, t, O[t, j], "Signal")
        # 2) yesterday's entry signals: buy at today's open, best first, one equal slot each
        for j, k in pend:
            if j in pos or not valid[t, j] or len(pos) >= max_pos:
                continue
            alloc = min(cash, eq_prev / max_pos)
            if alloc <= 0:
                continue
            o = O[t, j]
            shares = alloc / (o * (1 + fee))
            cash -= shares * o * (1 + fee)
            stops = []
            if stop_pct:
                stops.append(o * (1 - stop_pct / 100))
            if atr_mult and not np.isnan(ATRP[t, j]):
                stops.append(o - atr_mult * ATRP[t, j])
            pos[j] = {"shares": shares, "entry": o, "t": t, "kb": K[t, j], "peak": o, "stop": max(stops) if stops else 0.0,
                      "target": o * (1 + tp_pct / 100) if tp_pct else np.inf, "k": k, "exit": False}
        pend = []
        # 3) stop loss / trailing stop / take profit during the day
        for j in list(pos):
            if not valid[t, j]:
                continue
            q = pos[j]
            q["peak"] = max(q["peak"], H[t, j])
            trail = q["peak"] * (1 - trail_pct / 100) if trail_pct else 0.0
            eff = max(q["stop"], trail)
            if Lo[t, j] <= eff:
                close(j, t, min(O[t, j], eff), "Trailing Stop" if trail >= q["stop"] and trail_pct else "Stop Loss")
            elif H[t, j] >= q["target"]:
                close(j, t, max(O[t, j], q["target"]), "Take Profit")
        # 4) signals at the close: the strategy that opened a trade decides its exit; new signals fill the free slots
        for j, q in pos.items():
            if valid[t, j] and EXT[q["k"], t, j]:
                q["exit"] = True
        free = max_pos - sum(1 for q in pos.values() if not q["exit"])
        if free > 0 and live[t]:
            row = ENT[:, t, :]
            cand = [j for j in np.flatnonzero(row.any(axis=0)) if j not in pos]
            if cand:
                cand.sort(key=lambda j: (-MOM[t, j] if not np.isnan(MOM[t, j]) else np.inf, syms[j]))
                pend = [(int(j), int(np.argmax(row[:, j]))) for j in cand[:free]]
        # 5) value at the close
        mv = float(sum(q["shares"] * CF[t, j] for j, q in pos.items()))
        equity[t] = cash + mv
        invested[t] = mv / equity[t] if equity[t] > 0 else 0.0
        npos[t] = len(pos)
        eq_prev = equity[t]

    open_rows = []
    for j, q in pos.items():
        tl = int(np.flatnonzero(valid[:, j])[-1])
        c_last, basis = C[tl, j], q["entry"] * (1 + fee)
        open_rows.append({"Symbol": syms[j], "Strategy": names[q["k"]], "Entry Date": idx[q["t"]], "Entry": q["entry"],
                          "Exit Date": idx[tl], "Exit": c_last, "Shares": q["shares"], "P&L $": q["shares"] * (c_last - basis),
                          "P&L %": (c_last / basis - 1) * 100, "Bars": int(K[tl, j] - q["kb"]), "Exit Reason": "Open"})
    tr = pd.DataFrame(trades + open_rows, columns=TRADE_COLS)
    out.update(ok=True, start=start, symbols=syms, n_symbols=N, last_date=idx[-1], trades=tr, max_pos=max_pos,
               next_buys=[(syms[j], names[k]) for j, k in pend],
               next_sells=[(syms[j], names[q["k"]]) for j, q in pos.items() if q["exit"]],
               n_open=len(pos), in_pos=bool(pos))
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


@st.cache_data(ttl=600, show_spinner=False, max_entries=24)
def _run_cached(bot_json):
    bot = json.loads(bot_json)
    period = period_for(bot["start_date"])
    px = load_prices(members(bot["kind"], bot["value"]), period)
    spy = px.get("SPY")
    if spy is None or len(spy) < 2:
        spy = data.history("SPY", period)
    return simulate(bot, px, spy)


def run_all(bots):
    """Every bot replayed (each result cached for 10 minutes, like the prices) + SPY for the comparison chart."""
    sims = [_run_cached(json.dumps(b, sort_keys=True, default=str)) for b in bots]
    period = max((period_for(b["start_date"]) for b in bots), key=PERIODS.index) if bots else "2y"
    return sims, data.history("SPY", period)


def journal(sim):
    """Trades in the Trade Journal / Auto Trader format (for tdash.render and autotrader.stats)."""
    bot, tr = sim["bot"], sim["trades"]
    fee = bot["fee"] / 100
    return pd.DataFrame({"Symbol": tr["Symbol"].astype(str), "Type": "Stock", "Contract": tr["Symbol"].astype(str), "Setup": 0,
                         "Sector": [sector_of(s) for s in tr["Symbol"]],
                         "Entry Date": pd.to_datetime(tr["Entry Date"]), "Entry": tr["Entry"].astype(float),
                         "Exit Date": pd.to_datetime(tr["Exit Date"]), "Exit": tr["Exit"].astype(float), "Qty": tr["Shares"].astype(float),
                         "P&L $": tr["P&L $"].astype(float), "P&L %": tr["P&L %"].astype(float),
                         "Fees": ((tr["Entry"] + tr["Exit"]) * tr["Shares"] * fee).astype(float), "Days": tr["Bars"],
                         "Exit Reason": tr["Exit Reason"]})

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.1"
