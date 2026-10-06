"""
portfolio.py - The paper portfolio: a margin account traded by hand with virtual money on real prices.

What it does, like a real broker account:
  * orders: market, limit, stop and trailing stop; good for the day or until cancelled (90 days); a bracket (stop loss +
    take profit, one cancels the other) can be attached to any new position;
  * long and SHORT positions: a short sells borrowed shares (the money comes in, the shares are owed), pays a daily borrow
    fee and the dividends of the shares it owes, and is closed by buying them back (cover);
  * margin (Reg T / FINRA): buying power, initial requirement (longs 100% or 50% with 2x, shorts 150%), maintenance
    (longs 25%, shorts 30%) and a margin call when equity falls below it; interest on a debit balance;
  * dividends (paid to longs, charged to shorts) and stock splits on the real dates, commissions and slippage.

How it stays right without a server running all day: the account is an event log (orders, fills, deposits). Every page
view replays it: open orders are checked against the real 5-minute bars since they were placed (daily bars for older
days), so a stop that was hit at 11:05 fills at 11:05's price even if nobody looked; then the whole account (cash,
positions, dividends, splits, fees, the equity curve) is rebuilt day by day from the fills and the real closing prices.
Prices are Yahoo's raw prices (not adjusted), the ones the trades really happened at.

Storage: rows of the paper bots' table, so nothing new has to be set up in Supabase. Every visitor has a portfolio of their
own, the row "__portfolio__:<their code>", where the code is a random key kept in their browser (see p_portfolio). The row
"__portfolio__" is the site owner's own portfolio: it opens on the owner's devices (owner_code), never for visitors.
"""
import hashlib
import copy
import json
import math
import os
import tempfile
import threading
from datetime import date, datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import streamlit as st

import mcal

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")
KEY = "__portfolio__"                      # the owner's row in the paper_bots table; a visitor's is KEY + ":" + their code


def visitor_key(code):
    return f"{KEY}:{code}"


def owner_code():
    """The site owner's device code: a fingerprint of BOTS_PASSWORD (kept nowhere, not in the repository). A device that has
    it in its cookie opens the owner's own portfolio directly, with nothing to type. None when no password is set."""
    import hmac
    pw = _pb()._secret("BOTS_PASSWORD")
    if not pw:
        return None
    return hmac.new(pw.encode(), b"alturaifi-paper-portfolio-owner-v1", hashlib.sha256).hexdigest()[:40]
DEFAULTS = {"start_cash": 100000.0, "leverage": 1.0, "commission": 0.0, "per_share": 0.0, "min_fee": 0.0, "slippage_bps": 2.0,
            "borrow_rate": 0.3, "margin_rate": 8.0, "allow_short": True}
LONG_MAINT, SHORT_INIT, SHORT_MAINT = 0.25, 0.50, 0.30     # FINRA / Reg T
MIN_SHORT_PRICE = 5.0                      # brokers do not lend shares under $5
GTC_DAYS = 90
SIDES = ("buy", "sell", "short", "cover")
TYPES = ("market", "limit", "stop", "trail")
ENTRY = ("buy", "short")
BUYISH = ("buy", "cover")


class Empty(Exception):
    pass


# ---------------------------------------------------------------- time
def utcnow():
    return datetime.now(UTC)


def iso(dt):
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(s):
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=UTC)
    return datetime.strptime(str(s)[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)


def et_date(dt):
    return parse(dt).astimezone(ET).date()


def session(d):
    """(open, close) of a trading day as aware ET datetimes, None when the market is closed that day."""
    if not mcal.is_trading_day(d):
        return None
    kind, _ = mcal.day_status(d)
    close = dtime(13, 0) if kind == "early" else dtime(16, 0)
    return datetime.combine(d, dtime(9, 30), ET), datetime.combine(d, close, ET)


def is_open(now=None):
    now = (now or utcnow()).astimezone(ET)
    s = session(now.date())
    return bool(s) and s[0] <= now < s[1]


def order_session(placed):
    """The trading day an order placed at this time belongs to (the current session, else the next one)."""
    t = parse(placed).astimezone(ET)
    d = t.date()
    s = session(d)
    if s and t < s[1]:
        return d
    return mcal.next_trading_day(d)


def last_session_day(now=None):
    """The last trading day whose session has started (today during or after the session, else the one before)."""
    t = (now or utcnow()).astimezone(ET)
    s = session(t.date())
    if s and t >= s[0]:
        return t.date()
    return mcal.prev_trading_day(t.date())


# ---------------------------------------------------------------- prices (raw, from Yahoo)
def _tidy_daily(df):
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    idx = pd.to_datetime(df.index)
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_convert(ET).tz_localize(None)
    df.index = idx.normalize()
    for c in ("Dividends", "Stock Splits"):
        if c not in df:
            df[c] = 0.0
    df = df[["Open", "High", "Low", "Close", "Dividends", "Stock Splits"]].astype(float)
    return df[~df.index.duplicated(keep="last")].dropna(subset=["Close"])


@st.cache_data(ttl=600, show_spinner=False)
def _daily(sym, start):
    import yfinance as yf
    df = _tidy_daily(yf.Ticker(sym).history(start=start, auto_adjust=False, actions=True))
    if df.empty:
        raise Empty(sym)
    return df


@st.cache_data(ttl=60, show_spinner=False)
def _intraday(sym):
    import yfinance as yf
    df = yf.Ticker(sym).history(period="5d", interval="5m", prepost=False, auto_adjust=False)
    if df is None or df.empty:
        raise Empty(sym)
    idx = pd.to_datetime(df.index)
    df.index = idx.tz_convert(ET) if getattr(idx, "tz", None) is not None else idx.tz_localize(ET)
    return df[["Open", "High", "Low", "Close"]].astype(float).dropna()


class Market:
    """Where the prices come from (tests give their own)."""

    def quotes(self, syms):
        """{sym: (price, previous close)} right now."""
        import data
        syms = [s for s in dict.fromkeys(syms) if s]
        if not syms:
            return {}
        out = {}
        df = data.quotes_df(syms)
        if not df.empty:
            for s, p, c in zip(df["Symbol"], df["Price"], df["Chg %"]):
                if pd.notna(p) and p > 0:
                    out[s] = (float(p), float(p) / (1 + float(c) / 100) if pd.notna(c) and c > -100 else float(p))
        for s in syms:                                       # the last two daily closes when the quote is missing
            if s not in out:
                d = self.daily(s, (date.today() - timedelta(days=10)).isoformat())
                if len(d) >= 2:
                    out[s] = (float(d["Close"].iloc[-1]), float(d["Close"].iloc[-2]))
        return out

    def daily(self, sym, start):
        try:
            return _daily(sym, str(start)[:10])
        except Exception:
            return pd.DataFrame()

    def intraday(self, sym):
        try:
            return _intraday(sym)
        except Exception:
            return pd.DataFrame()

    def info(self, sym):
        import data
        try:
            return data.info(sym) or {}
        except Exception:
            return {}


# ---------------------------------------------------------------- the account
def new_state(start_cash=None, settings=None, name="Paper Portfolio", now=None):
    st_ = dict(DEFAULTS)
    st_.update({k: v for k, v in (settings or {}).items() if k in DEFAULTS})
    if start_cash:
        st_["start_cash"] = float(start_cash)
    return {"v": 1, "name": name, "created": iso(now or utcnow()), "start_cash": float(st_["start_cash"]), "settings": st_,
            "orders": [], "fills": [], "flows": [], "seq": 1}


def clean(state):
    """A stored account -> a usable one (missing keys filled in); None when it is not an account."""
    if not isinstance(state, dict) or "orders" not in state:
        return None
    s = copy.deepcopy(state)
    s.setdefault("v", 1)
    s.setdefault("name", "Paper Portfolio")
    s.setdefault("created", iso(utcnow()))
    s["settings"] = {**DEFAULTS, **(s.get("settings") or {})}
    s.setdefault("start_cash", float(s["settings"]["start_cash"]))
    for k in ("orders", "fills", "flows"):
        s[k] = list(s.get(k) or [])
    s["seq"] = max([int(s.get("seq") or 1)] + [int(o.get("id", 0)) + 1 for o in s["orders"]] + [int(f.get("id", 0)) + 1 for f in s["fills"]])
    return s


def _next_id(state):
    i = int(state.get("seq") or 1)
    state["seq"] = i + 1
    return i


def fee_of(settings, qty):
    c = float(settings.get("commission") or 0) + float(settings.get("per_share") or 0) * abs(qty)
    return max(c, float(settings.get("min_fee") or 0)) if c > 0 or float(settings.get("min_fee") or 0) > 0 else 0.0


def slip(settings):
    return float(settings.get("slippage_bps") or 0) / 10000.0


def borrow_rate_for(settings, info):
    """Yearly borrow fee (%) for a new short: the account's general rate, more for heavily shorted stocks (an estimate:
    stocks with a big part of their float sold short are 'hard to borrow')."""
    base = float(settings.get("borrow_rate") or 0)
    try:
        sp = float((info or {}).get("shortPercentOfFloat") or 0) * 100
    except (TypeError, ValueError):
        sp = 0.0
    if sp >= 30:
        return max(base, 25.0)
    if sp >= 20:
        return max(base, 10.0)
    if sp >= 10:
        return max(base, 3.0)
    return base


# ---------------------------------------------------------------- positions from the fills (with the splits)
def _split_events(mkt, syms, start):
    out = {}
    for s in syms:
        d = mkt.daily(s, start)
        if not d.empty and "Stock Splits" in d:
            sp = d["Stock Splits"]
            out[s] = {ix.date(): float(v) for ix, v in sp[(sp > 0) & (sp != 1)].items()}
    return out


def positions_now(state, mkt, until=None):
    """{sym: qty} from the fills (+ the splits since), the quick version used to check orders."""
    until = until or utcnow()
    fills = sorted(state["fills"], key=lambda f: (f["time"], f["id"]))
    if not fills:
        return {}
    start = (et_date(fills[0]["time"]) - timedelta(days=3)).isoformat()
    splits = _split_events(mkt, {f["sym"] for f in fills}, start)
    q, last = {}, {}
    for f in fills:
        t = parse(f["time"])
        if t > until:
            break
        s = f["sym"]
        for d, r in sorted((splits.get(s) or {}).items()):
            if last.get(s) and last[s] < d <= et_date(t) and q.get(s):
                q[s] *= r
        last[s] = et_date(t)
        q[s] = q.get(s, 0) + (f["qty"] if f["side"] in BUYISH else -f["qty"])
    today = et_date(until)
    for s in list(q):
        for d, r in sorted((splits.get(s) or {}).items()):
            if last.get(s) and last[s] < d <= today and q[s]:
                q[s] *= r
        q[s] = round(q[s], 6)
    return {s: v for s, v in q.items() if abs(v) > 1e-9}


# ---------------------------------------------------------------- open orders against the real bars
def _bars(mkt, sym, since, now):
    """[(start, end, O, H, L, C)] of the regular session after `since` (aware datetimes): the 5-minute bars of the last days,
    daily bars before them (a day that began before `since` only gives its close)."""
    out = []
    intr = mkt.intraday(sym)
    covered = set()
    if not intr.empty:
        for ts, r in intr.iterrows():
            t0 = ts.to_pydatetime()
            t1 = t0 + timedelta(minutes=5)
            covered.add(t0.date())
            if t0 >= since and t1 <= now:
                out.append((t0, t1, float(r["Open"]), float(r["High"]), float(r["Low"]), float(r["Close"])))
    d0 = since.astimezone(ET).date()
    daily = mkt.daily(sym, (d0 - timedelta(days=7)).isoformat())
    if not daily.empty:
        for ix, r in daily.iterrows():
            d = ix.date()
            if d < d0 or d in covered:
                continue
            s = session(d)
            if not s or s[1] > now or s[1] <= since:
                continue
            if s[0] >= since:
                out.append((s[0], s[1], float(r["Open"]), float(r["High"]), float(r["Low"]), float(r["Close"])))
            else:
                c = float(r["Close"])
                out.append((s[1], s[1], c, c, c, c))
    out.sort(key=lambda b: b[0])
    return out


def _trigger(o, bar, sl):
    """The fill price of an order on one bar, None when it does not fill (stops and market orders pay the slippage)."""
    _, _, O, H, L, C = bar
    buy = o["side"] in BUYISH
    t = o["type"]
    if t == "market":
        return O * (1 + sl) if buy else O * (1 - sl)
    if t == "limit":
        lim = float(o["limit"])
        if buy and L <= lim:
            return min(O, lim)
        if not buy and H >= lim:
            return max(O, lim)
        return None
    if t == "stop":
        s = float(o["stop"])
        if buy and H >= s:
            return max(O, s) * (1 + sl)
        if not buy and L <= s:
            return min(O, s) * (1 - sl)
        return None
    if t == "trail":
        pct = float(o["trail"]) / 100
        pk = float(o.get("peak") or O)
        if buy:                                    # protects a short: follows the lowest price, fires on a bounce
            stop = pk * (1 + pct)
            if H >= stop:
                return max(O, stop) * (1 + sl)
            o["peak"] = min(pk, L)
        else:
            stop = pk * (1 - pct)
            if L <= stop:
                return min(O, stop) * (1 - sl)
            o["peak"] = max(pk, H)
    return None


def _expiry(o):
    if o.get("tif") == "gtc":
        return parse(o["placed"]) + timedelta(days=GTC_DAYS)
    d = date.fromisoformat(o.get("session") or order_session(o["placed"]).isoformat())
    s = session(d)
    return s[1].astimezone(UTC) if s else parse(o["placed"]) + timedelta(days=1)


def _cancel_children(state, o, why):
    for c in state["orders"]:
        if c.get("parent") == o["id"] and c["status"] in ("open", "held"):
            c["status"], c["note"] = "cancelled", why


def _record_fill(state, o, qty, px, when, pos, after=None):
    """Adds the fill, updates the running positions, starts the bracket (its legs work from `after`, the end of the fill's
    bar), closes the other leg (OCO). Returns (fill, new orders)."""
    s = state["settings"]
    fee = fee_of(s, qty)
    f = {"id": _next_id(state), "order": o["id"], "sym": o["sym"], "side": o["side"], "qty": qty, "px": round(float(px), 4),
         "time": iso(when), "fee": round(fee, 2)}
    if o["side"] == "short":
        f["borrow"] = float(o.get("borrow") if o.get("borrow") is not None else s.get("borrow_rate") or 0)
    state["fills"].append(f)
    o.update(status="filled", fill_px=f["px"], filled_at=f["time"], filled_qty=qty)
    pos[o["sym"]] = round(pos.get(o["sym"], 0) + (qty if o["side"] in BUYISH else -qty), 6)
    born = []
    if o["side"] in ENTRY and (o.get("sl") or o.get("tp")):
        exit_side = "sell" if o["side"] == "buy" else "cover"
        for kind, price in (("stop", o.get("sl")), ("limit", o.get("tp"))):
            if price:
                c = {"id": _next_id(state), "sym": o["sym"], "side": exit_side, "qty": qty, "type": kind, "tif": "gtc",
                     "placed": iso(after or (when + timedelta(seconds=1))), "status": "open", "parent": o["id"], "oco": o["id"],
                     "stop" if kind == "stop" else "limit": float(price), "ref": f["px"]}
                state["orders"].append(c)
                born.append(c)
    if o.get("oco"):
        for c in state["orders"]:
            if c is not o and c.get("oco") == o["oco"] and c["status"] == "open":
                c["status"], c["note"] = "cancelled", "oco"
    if abs(pos.get(o["sym"], 0)) < 1e-9:           # the position is closed: its other exit orders go
        for c in state["orders"]:
            if c is not o and c["sym"] == o["sym"] and c["status"] == "open" and c["side"] in ("sell", "cover"):
                c["status"], c["note"] = "cancelled", "closed"
    return f, born


def _fill_qty(o, pos):
    """How much of an order can fill against the position at that moment (None: it is rejected / cancelled)."""
    q = int(o["qty"])
    have = pos.get(o["sym"], 0)
    if o["side"] == "sell":
        return (min(q, int(have)), "closed") if have > 0 else (None, "no_long")
    if o["side"] == "cover":
        return (min(q, int(-have)), "closed") if have < 0 else (None, "no_short")
    if o["side"] == "buy" and have < 0:
        return None, "is_short"
    if o["side"] == "short" and have > 0:
        return None, "is_long"
    return q, ""


def process(state, mkt, now=None):
    """Fills, expires and cancels the open orders against the real bars since they were placed, in time order across all
    orders. True when anything changed."""
    import heapq
    now = now or utcnow()
    live = [o for o in state["orders"] if o["status"] == "open"]
    if not live:
        return False
    changed = False
    pos = positions_now(state, mkt, now)
    sl = slip(state["settings"])
    bars, q = {}, []

    def since_of(o):
        return max(parse(o["placed"]), parse(o["checked"])) if o.get("checked") else parse(o["placed"])

    def queue(o):
        if o["sym"] not in bars:
            first = min([since_of(x) for x in state["orders"] if x["status"] == "open" and x["sym"] == o["sym"]] + [since_of(o)])
            bars[o["sym"]] = _bars(mkt, o["sym"], first, now)
        t = since_of(o)
        for i, b in enumerate(bars[o["sym"]]):
            if b[0] >= t:
                heapq.heappush(q, (b[0], o["id"], i))
                return

    for o in live:
        queue(o)
    by_id = {o["id"]: o for o in state["orders"]}
    while q:
        t0, oid, i = heapq.heappop(q)
        o = by_id[oid]
        if o["status"] != "open":
            continue
        b = bars[o["sym"]][i]
        if t0 >= _expiry(o):
            o["status"], o["note"] = "expired", "tif"
            _cancel_children(state, o, "parent")
            changed = True
            continue
        px = _trigger(o, b, sl)
        o["checked"] = iso(b[1])
        changed = True
        if px is None:
            if i + 1 < len(bars[o["sym"]]):
                heapq.heappush(q, (bars[o["sym"]][i + 1][0], oid, i + 1))
            continue
        n, why = _fill_qty(o, pos)
        if not n:
            o["status"], o["note"] = ("cancelled" if why in ("no_long", "no_short") else "rejected"), why or "zero"
            continue
        _, born = _record_fill(state, o, n, px, b[0], pos, after=b[1] if b[1] > b[0] else b[0] + timedelta(seconds=1))
        for c in born:
            by_id[c["id"]] = c
            queue(c)
    for o in state["orders"]:
        if o["status"] == "open" and now >= _expiry(o):
            o["status"], o["note"] = "expired", "tif"
            changed = True
    return changed


# ---------------------------------------------------------------- the whole account, day by day
def _f(x, default=0.0):
    try:
        x = float(x)
        return x if math.isfinite(x) else default
    except (TypeError, ValueError):
        return default


def rebuild(state, mkt, now=None):
    """Replays the account: cash, positions, dividends, splits, fees, borrow fees, margin interest and the daily equity."""
    now = now or utcnow()
    s = state["settings"]
    start_day = et_date(state["created"])
    end_day = last_session_day(now)
    fills = sorted(state["fills"], key=lambda f: (f["time"], f["id"]))
    flows = sorted(state.get("flows") or [], key=lambda x: x["time"])
    syms = sorted({f["sym"] for f in fills})
    first = min([start_day] + [et_date(f["time"]) for f in fills])
    daily = {x: mkt.daily(x, (first - timedelta(days=7)).isoformat()) for x in syms}
    held_now = [x for x, q in positions_now(state, mkt, now).items() if q]
    quotes = mkt.quotes(held_now) if held_now else {}
    cash = float(state["start_cash"])
    pos = {}
    trades, ledger, rows = [], [], []
    tot = {"fees": 0.0, "borrow": 0.0, "interest": 0.0, "divs": 0.0, "realized": 0.0}
    fi = li = 0
    month_cost = {}
    last_px = {}
    days = []
    d = start_day if mcal.is_trading_day(start_day) else mcal.next_trading_day(start_day)
    while d <= end_day:
        days.append(d)
        d = mcal.next_trading_day(d)
    if not days:
        days = [end_day]

    def bar(sym, day):
        df = daily.get(sym)
        if df is None or df.empty:
            return None
        ts = pd.Timestamp(day)
        return df.loc[ts] if ts in df.index else None

    def close_part(p, sym, qty, px, when, fee):
        """A closing fill: realized P&L of this part, net of its share of the fees, borrow and dividends."""
        share = qty / abs(p["qty"]) if p["qty"] else 1.0
        entry_fees, borrow, divs = p["fees"] * share, p["borrow"] * share, p["divs"] * share
        gross = (px - p["avg"]) * qty if p["qty"] > 0 else (p["avg"] - px) * qty
        net = gross - entry_fees - fee - borrow + divs
        p["fees"] -= entry_fees
        p["borrow"] -= borrow
        p["divs"] -= divs
        opened = parse(p["opened"])
        trades.append({"sym": sym, "dir": "long" if p["qty"] > 0 else "short", "qty": qty, "entry": round(p["avg"], 4), "exit": round(px, 4),
                       "opened": p["opened"], "closed": iso(when), "gross": round(gross, 2), "fees": round(entry_fees + fee, 2),
                       "borrow": round(borrow, 2), "divs": round(divs, 2), "pnl": round(net, 2),
                       "ret": round(net / (p["avg"] * qty) * 100, 3) if p["avg"] and qty else 0.0,
                       "days": round((when - opened).total_seconds() / 86400, 2)})
        tot["realized"] += net
        return net

    for i, day in enumerate(days):
        # corporate actions at the open: splits change the shares, dividends are paid to longs and charged to shorts
        for sym, p in pos.items():
            if not p["qty"]:
                continue
            b = bar(sym, day)
            if b is None:
                continue
            sp = _f(b.get("Stock Splits"))
            if sp > 0 and sp != 1:
                p["qty"] = round(p["qty"] * sp, 6)
                p["avg"] = p["avg"] / sp
                ledger.append({"time": day.isoformat(), "kind": "split", "sym": sym, "amount": 0.0, "note": f"{sp:g}:1"})
            dv = _f(b.get("Dividends"))
            if dv > 0:
                amt = p["qty"] * dv
                cash += amt
                p["divs"] += amt
                tot["divs"] += amt
                ledger.append({"time": day.isoformat(), "kind": "dividend" if amt > 0 else "dividend_short", "sym": sym,
                               "amount": round(amt, 2), "note": f"{dv:g}/sh"})
        flow_today = 0.0
        while li < len(flows) and et_date(flows[li]["time"]) <= day:
            x = flows[li]
            amt = _f(x["amount"]) * (1 if x["kind"] == "deposit" else -1)
            cash += amt
            flow_today += amt
            ledger.append({"time": x["time"], "kind": x["kind"], "sym": "", "amount": round(amt, 2), "note": x.get("note", "")})
            li += 1
        while fi < len(fills) and et_date(fills[fi]["time"]) <= day:
            f = fills[fi]
            fi += 1
            sym, q, px, fee, when = f["sym"], float(f["qty"]), float(f["px"]), _f(f.get("fee")), parse(f["time"])
            p = pos.setdefault(sym, {"qty": 0.0, "avg": 0.0, "opened": None, "fees": 0.0, "borrow": 0.0, "divs": 0.0, "rate": 0.0})
            tot["fees"] += fee
            last_px[sym] = px
            if f["side"] == "buy":
                cash -= q * px + fee
                p["avg"] = (p["avg"] * p["qty"] + px * q) / (p["qty"] + q) if p["qty"] > 0 else px
                p["opened"] = p["opened"] or f["time"]
                p["qty"] += q
                p["fees"] += fee
            elif f["side"] == "short":
                cash += q * px - fee
                n = -p["qty"]
                p["avg"] = (p["avg"] * n + px * q) / (n + q) if n > 0 else px
                p["rate"] = (p["rate"] * n + _f(f.get("borrow"), s["borrow_rate"]) * q) / (n + q) if n > 0 else _f(f.get("borrow"), s["borrow_rate"])
                p["opened"] = p["opened"] or f["time"]
                p["qty"] -= q
                p["fees"] += fee
            elif f["side"] == "sell":
                q = min(q, max(p["qty"], 0))
                if q <= 0:
                    continue
                cash += q * px - fee
                close_part(p, sym, q, px, when, fee)
                p["qty"] -= q
            else:                                   # cover
                q = min(q, max(-p["qty"], 0))
                if q <= 0:
                    continue
                cash -= q * px + fee
                close_part(p, sym, q, px, when, fee)
                p["qty"] += q
            if abs(p["qty"]) < 1e-9:
                pos[sym] = {"qty": 0.0, "avg": 0.0, "opened": None, "fees": 0.0, "borrow": 0.0, "divs": 0.0, "rate": 0.0}
        # marks at the close (now, for a session still running)
        lmv = smv = 0.0
        for sym, p in pos.items():
            if not p["qty"]:
                continue
            b = bar(sym, day)
            px = _f(b["Close"]) if b is not None else last_px.get(sym, p["avg"])
            if day == end_day and sym in quotes:
                px = quotes[sym][0]
            last_px[sym] = px
            mv = p["qty"] * px
            if mv > 0:
                lmv += mv
            else:
                smv += -mv
        eq = cash + lmv - smv
        borrow = interest = 0.0
        if i + 1 < len(days):                       # the nights until the next session: borrow fees and margin interest
            nights = (days[i + 1] - day).days
            for sym, p in pos.items():
                if p["qty"] < 0:
                    fee_ = -p["qty"] * last_px.get(sym, p["avg"]) * p["rate"] / 100 / 360 * nights
                    p["borrow"] += fee_
                    borrow += fee_
            if cash < 0 and s.get("margin_rate"):
                interest = -cash * float(s["margin_rate"]) / 100 / 360 * nights
            cash -= borrow + interest
            tot["borrow"] += borrow
            tot["interest"] += interest
            if borrow or interest:
                m = day.strftime("%Y-%m")
                mc = month_cost.setdefault(m, {"borrow": 0.0, "interest": 0.0, "last": day})
                mc["borrow"] += borrow
                mc["interest"] += interest
                mc["last"] = day
        rows.append({"date": pd.Timestamp(day), "equity": eq, "cash": cash, "lmv": lmv, "smv": smv, "flow": flow_today,
                     "borrow": borrow, "interest": interest})
    while li < len(flows):                          # money moved after the last session (a weekend, before the open)
        x = flows[li]
        amt = _f(x["amount"]) * (1 if x["kind"] == "deposit" else -1)
        cash += amt
        if rows:
            rows[-1]["equity"] += amt
            rows[-1]["cash"] += amt
            rows[-1]["flow"] += amt
        ledger.append({"time": x["time"], "kind": x["kind"], "sym": "", "amount": round(amt, 2), "note": x.get("note", "")})
        li += 1
    for m, mc in sorted(month_cost.items()):
        for k in ("borrow", "interest"):
            if mc[k] > 0.005:
                ledger.append({"time": mc["last"].isoformat(), "kind": k, "sym": "", "amount": round(-mc[k], 2), "note": m})
    curve = pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame(columns=["equity", "cash", "lmv", "smv", "flow"])
    # positions now
    eq_now = float(curve["equity"].iloc[-1]) if len(curve) else cash
    out_pos = []
    for sym, p in pos.items():
        if not p["qty"]:
            continue
        last = quotes.get(sym, (last_px.get(sym, p["avg"]), None))[0]
        prev = quotes.get(sym, (None, None))[1]
        if prev is None:
            df = daily.get(sym)
            prev = float(df["Close"].iloc[-2]) if df is not None and len(df) >= 2 else last
        q = p["qty"]
        mv = q * last
        cost = q * p["avg"]
        upnl = mv - cost
        opened_today = p["opened"] and et_date(p["opened"]) == end_day
        day_pnl = q * (last - (p["avg"] if opened_today else prev))
        out_pos.append({"sym": sym, "qty": q, "side": "long" if q > 0 else "short", "avg": p["avg"], "last": last, "prev": prev,
                        "mv": mv, "cost": cost, "upnl": upnl, "upnl_pct": upnl / abs(cost) * 100 if cost else 0.0,
                        "day_pnl": day_pnl, "day_pct": (last / prev - 1) * 100 if prev else 0.0, "weight": abs(mv) / eq_now * 100 if eq_now > 0 else 0.0,
                        "opened": p["opened"], "borrow": p["borrow"], "rate": p["rate"], "divs": p["divs"], "fees": p["fees"]})
    out_pos.sort(key=lambda r: -abs(r["mv"]))
    lmv = sum(r["mv"] for r in out_pos if r["qty"] > 0)
    smv = -sum(r["mv"] for r in out_pos if r["qty"] < 0)
    flows_total = sum(_f(x["amount"]) * (1 if x["kind"] == "deposit" else -1) for x in flows)
    invested = float(state["start_cash"]) + flows_total
    prev_eq = float(curve["equity"].iloc[-2]) if len(curve) >= 2 else float(state["start_cash"])
    today_flow = float(curve["flow"].iloc[-1]) if len(curve) else 0.0
    day_pnl = eq_now - prev_eq - today_flow if len(curve) >= 2 else eq_now - float(state["start_cash"]) - today_flow
    ledger.sort(key=lambda r: r["time"], reverse=True)
    return {"curve": curve, "positions": out_pos, "cash": cash, "equity": eq_now, "lmv": lmv, "smv": smv, "trades": trades,
            "ledger": ledger, "totals": tot, "invested": invested, "pnl": eq_now - invested,
            "ret": (eq_now / invested - 1) * 100 if invested > 0 else 0.0, "day_pnl": day_pnl,
            "day_pct": day_pnl / prev_eq * 100 if prev_eq > 0 else 0.0, "unrealized": sum(r["upnl"] for r in out_pos),
            "asof": iso(now), "end_day": end_day.isoformat()}


# ---------------------------------------------------------------- margin and buying power
def account(view, settings):
    """Reg T / FINRA numbers of the account now."""
    eq, lmv, smv = view["equity"], view["lmv"], view["smv"]
    r_long = 1.0 / max(float(settings.get("leverage") or 1), 1.0)
    init = r_long * lmv + SHORT_INIT * smv
    maint = LONG_MAINT * lmv + SHORT_MAINT * smv
    excess = eq - init
    gross = lmv + smv
    return {"equity": eq, "cash": view["cash"], "lmv": lmv, "smv": smv, "gross": gross, "net": lmv - smv,
            "leverage": gross / eq if eq > 0 else 0.0, "init": init, "maint": maint, "excess": excess,
            "bp_long": max(excess, 0) / r_long, "bp_short": max(excess, 0) / SHORT_INIT if settings.get("allow_short", True) else 0.0,
            "margin_call": eq < maint and gross > 0, "cushion": (eq - maint) / eq * 100 if eq > 0 else -100.0,
            "used": init / eq * 100 if eq > 0 else 100.0, "r_long": r_long}


# ---------------------------------------------------------------- placing and cancelling
class OrderError(Exception):
    """code: one of the reasons the order page explains (bad_symbol, qty, no_long, no_short, is_short, is_long, short_off,
    short_price, bp, bracket, price, margin_call)"""

    def __init__(self, code, **info):
        super().__init__(code)
        self.code, self.info = code, info


def preview(state, view, mkt, spec, now=None):
    """What an order would do before it is sent: reference price, value, fees, margin it needs, buying power left, the
    loss at its stop and the reward at its target. Raises OrderError when it would be refused."""
    now = now or utcnow()
    s = state["settings"]
    sym = str(spec.get("sym") or "").strip().upper()
    side, typ = spec.get("side"), spec.get("type", "market")
    if side not in SIDES or typ not in TYPES:
        raise OrderError("bad")
    q = mkt.quotes([sym]).get(sym) if sym and not any(c in sym for c in "^=") else None
    if not q:
        raise OrderError("bad_symbol")
    info = mkt.info(sym) or {}
    if info.get("quoteType") and str(info["quoteType"]).upper() not in ("EQUITY", "ETF"):
        raise OrderError("bad_symbol")                 # US stocks and ETFs only (their sessions are the ones the fills follow)
    price, prev = q
    try:
        qty = int(spec.get("qty") or 0)
    except (TypeError, ValueError):
        qty = 0
    if qty <= 0:
        raise OrderError("qty")
    held = {p["sym"]: p["qty"] for p in view["positions"]}.get(sym, 0)
    if side == "sell" and held <= 0:
        raise OrderError("no_long")
    if side == "cover" and held >= 0:
        raise OrderError("no_short")
    if side == "sell" and qty > held:
        raise OrderError("too_many", have=int(held))
    if side == "cover" and qty > -held:
        raise OrderError("too_many", have=int(-held))
    if side == "buy" and held < 0:
        raise OrderError("is_short")
    if side == "short" and held > 0:
        raise OrderError("is_long")
    if side == "short" and not s.get("allow_short", True):
        raise OrderError("short_off")
    if side == "short" and price < MIN_SHORT_PRICE:
        raise OrderError("short_price", price=price)
    lim, stp, trail = spec.get("limit"), spec.get("stop"), spec.get("trail")
    if typ == "limit" and not (lim and lim > 0):
        raise OrderError("price")
    if typ == "stop" and not (stp and stp > 0):
        raise OrderError("price")
    if typ == "trail" and not (trail and 0 < trail < 50):
        raise OrderError("price")
    if typ == "stop" and (stp <= price if side in BUYISH else stp >= price):
        raise OrderError("stop_side", price=price)
    if typ == "trail" and side in ENTRY:
        raise OrderError("trail_entry")
    ref = float(lim) if typ == "limit" else float(stp) if typ == "stop" else price
    value = qty * ref
    fee = fee_of(s, qty)
    acct = account(view, s)
    held_for = reserved(state, acct)                 # buying power already promised to open orders
    room = max(acct["excess"] - held_for, 0)
    need = 0.0
    if side in ENTRY:
        r = acct["r_long"] if side == "buy" else SHORT_INIT
        need = r * value + fee
        if acct["margin_call"]:
            raise OrderError("margin_call")
        if need > room + 1e-6:
            raise OrderError("bp", max_qty=int(max(room - fee, 0) / (r * ref)) if ref else 0, need=need, room=room)
    sl_, tp_ = spec.get("sl"), spec.get("tp")
    if side in ENTRY and (sl_ or tp_):
        long_ = side == "buy"
        if sl_ and (sl_ >= ref if long_ else sl_ <= ref):
            raise OrderError("bracket", which="sl")
        if tp_ and (tp_ <= ref if long_ else tp_ >= ref):
            raise OrderError("bracket", which="tp")
    risk = reward = None
    if side in ENTRY:
        if sl_:
            risk = abs(ref - sl_) * qty + 2 * fee
        if tp_:
            reward = abs(tp_ - ref) * qty - 2 * fee
    rate = borrow_rate_for(s, info) if side == "short" else None
    eq = acct["equity"]
    after_w = (abs(held) + qty) * price / eq * 100 if side in ENTRY and eq > 0 else None
    return {"sym": sym, "side": side, "type": typ, "qty": qty, "price": price, "prev": prev, "ref": ref, "value": value, "fee": fee,
            "need": need, "room": room, "bp_after": max(room - need, 0) / (acct["r_long"] if side == "buy" else SHORT_INIT if side == "short" else 1),
            "risk": risk, "reward": reward, "rr": (reward / risk) if risk and reward else None,
            "risk_pct": risk / eq * 100 if risk and eq > 0 else None, "borrow": rate,
            "borrow_day": value * rate / 100 / 360 if rate else None, "weight_after": after_w, "held": held, "info": info,
            "open": is_open(now)}


def reserved(state, acct):
    """Margin promised to the open entry orders (a broker holds buying power for them until they fill or are cancelled)."""
    tot = 0.0
    for o in state["orders"]:
        if o["status"] == "open" and o["side"] in ENTRY:
            ref = o.get("limit") or o.get("stop") or o.get("ref") or 0
            tot += (acct["r_long"] if o["side"] == "buy" else SHORT_INIT) * float(o["qty"]) * float(ref)
    return tot


def place(state, view, mkt, spec, now=None):
    """Checks and adds an order; a market order fills at once while the market is open. Returns the order."""
    now = now or utcnow()
    pv = preview(state, view, mkt, spec, now)
    o = {"id": _next_id(state), "sym": pv["sym"], "side": pv["side"], "qty": pv["qty"], "type": pv["type"],
         "tif": "gtc" if spec.get("tif") == "gtc" else "day", "placed": iso(now), "status": "open", "ref": round(pv["price"], 4)}
    o["session"] = order_session(o["placed"]).isoformat()
    if pv["type"] == "limit":
        o["limit"] = float(spec["limit"])
    if pv["type"] == "stop":
        o["stop"] = float(spec["stop"])
    if pv["type"] == "trail":
        o["trail"] = float(spec["trail"])
        o["peak"] = pv["price"]
    if pv["side"] in ENTRY:
        for k in ("sl", "tp"):
            if spec.get(k):
                o[k] = round(float(spec[k]), 4)
    if pv["side"] == "short":
        o["borrow"] = pv["borrow"]
    if spec.get("note"):
        o["note_user"] = str(spec["note"])[:120]
    state["orders"].append(o)
    marketable = o["type"] == "limit" and (o["limit"] >= pv["price"] if o["side"] in BUYISH else o["limit"] <= pv["price"])
    if (o["type"] == "market" or marketable) and is_open(now):
        sl = slip(state["settings"])
        px = pv["price"] if marketable else pv["price"] * (1 + sl) if o["side"] in BUYISH else pv["price"] * (1 - sl)
        pos = positions_now(state, mkt, now)
        q, why = _fill_qty(o, pos)
        if q:
            _record_fill(state, o, q, px, now, pos)
        else:
            o["status"], o["note"] = "rejected", why
    return o


def cancel(state, order_id):
    for o in state["orders"]:
        if o["id"] == order_id and o["status"] in ("open", "held"):
            o["status"], o["note"] = "cancelled", "user"
            _cancel_children(state, o, "parent")
            return True
    return False


def close_position(state, view, mkt, sym, now=None, qty=None):
    """A market order that closes (part of) a position: sell a long, cover a short."""
    p = next((x for x in view["positions"] if x["sym"] == sym), None)
    if not p:
        raise OrderError("no_long")
    q = int(abs(p["qty"])) if qty is None else int(qty)
    return place(state, view, mkt, {"sym": sym, "side": "sell" if p["qty"] > 0 else "cover", "qty": q, "type": "market"}, now)


def flow(state, kind, amount, now=None, note=""):
    if kind not in ("deposit", "withdraw") or not amount or amount <= 0:
        raise OrderError("qty")
    state["flows"].append({"time": iso(now or utcnow()), "kind": kind, "amount": float(amount), "note": note})


# ---------------------------------------------------------------- performance
def daily_returns(curve):
    """Time-weighted daily returns (deposits and withdrawals are not gains)."""
    if curve is None or len(curve) < 2:
        return pd.Series(dtype=float)
    e = curve["equity"]
    r = (e - curve["flow"]) / e.shift(1) - 1
    return r.iloc[1:].replace([np.inf, -np.inf], np.nan).dropna()


def stats(view, bench=None):
    """Return, risk and trading statistics of the account."""
    r = daily_returns(view["curve"])
    n = len(r)
    out = {"days": n}
    if n:
        growth = float((1 + r).prod())
        out["twr"] = (growth - 1) * 100
        yrs = n / 252
        out["cagr"] = (growth ** (1 / yrs) - 1) * 100 if yrs >= 0.5 and growth > 0 else None      # a yearly rate from less is a guess
        sd = float(r.std(ddof=1)) if n > 1 else 0.0
        out["vol"] = sd * math.sqrt(252) * 100
        out["sharpe"] = float(r.mean()) / sd * math.sqrt(252) if sd > 0 else None
        dn = r[r < 0]
        dsd = float(np.sqrt((dn ** 2).sum() / n)) if len(dn) else 0.0
        out["sortino"] = float(r.mean()) / dsd * math.sqrt(252) if dsd > 0 else None
        idx = (1 + r).cumprod()
        dd = idx / idx.cummax() - 1
        out["maxdd"] = float(dd.min()) * 100
        out["dd_now"] = float(dd.iloc[-1]) * 100
        under = (dd < 0).astype(int)
        run = best = 0
        for u in under:
            run = run + 1 if u else 0
            best = max(best, run)
        out["dd_days"] = best
        out["calmar"] = (out["cagr"] / abs(out["maxdd"])) if out.get("cagr") is not None and out["maxdd"] < 0 else None
        out["best_day"], out["worst_day"] = float(r.max()) * 100, float(r.min()) * 100
        out["pos_days"] = float((r > 0).mean()) * 100
        out["var95"] = float(-np.percentile(r, 5)) * 100 if n >= 20 else None
        if bench is not None and len(bench) > 2:
            b = bench.pct_change().reindex(r.index).dropna()
            j = r.reindex(b.index).dropna()
            b = b.reindex(j.index)
            if len(j) > 5 and float(b.var()) > 0:
                beta = float(np.cov(j, b)[0, 1] / b.var())
                out["beta"] = beta
                out["alpha"] = (float(j.mean()) - beta * float(b.mean())) * 252 * 100
                out["corr"] = float(np.corrcoef(j, b)[0, 1])
                out["bench_ret"] = (float((1 + b).prod()) - 1) * 100
    t = pd.DataFrame(view["trades"])
    if len(t):
        wins, losses = t[t["pnl"] > 0], t[t["pnl"] <= 0]
        gw, gl = float(wins["pnl"].sum()), float(-losses["pnl"].sum())
        out.update({"n_trades": len(t), "win_rate": len(wins) / len(t) * 100, "profit_factor": gw / gl if gl > 0 else None,
                    "avg_win": float(wins["pnl"].mean()) if len(wins) else 0.0, "avg_loss": float(losses["pnl"].mean()) if len(losses) else 0.0,
                    "expectancy": float(t["pnl"].mean()), "best_trade": float(t["pnl"].max()), "worst_trade": float(t["pnl"].min()),
                    "avg_days": float(t["days"].mean()), "realized": float(t["pnl"].sum())})
        out["payoff"] = abs(out["avg_win"] / out["avg_loss"]) if out["avg_loss"] else None
        for side in ("long", "short"):
            x = t[t["dir"] == side]
            out[side] = {"n": len(x), "win": float((x["pnl"] > 0).mean() * 100) if len(x) else None, "pnl": float(x["pnl"].sum()),
                         "avg_ret": float(x["ret"].mean()) if len(x) else None}
    return out


# ---------------------------------------------------------------- storage (one row of the paper bots' table)
_LOCK = threading.Lock()
_LOCAL = os.path.join(tempfile.gettempdir(), "alturaifi_paper_portfolio.json")
_REV = {"n": 0}


def _pb():
    import paperbots
    return paperbots


def _local_path(key):
    if key == KEY:
        return _LOCAL
    return os.path.join(tempfile.gettempdir(), f"alturaifi_paper_portfolio_{hashlib.sha256(key.encode()).hexdigest()[:20]}.json")


@st.cache_data(ttl=30, show_spinner=False)
def _load_raw(kind, rev, key=KEY):
    PB = _pb()
    if kind == "supabase":
        url, h = PB._sb()
        r = PB._request("GET", url, headers=h, params={"select": "id,params", "strategy": f"eq.{key}", "order": "id.asc", "limit": "1"})
        PB._check(r)
        rows = r.json()
        if rows:
            p = rows[0].get("params") or {}
            if isinstance(p, str):
                p = json.loads(p)
            return {"id": rows[0]["id"], "state": p.get("pf")}
        return None
    with _LOCK:
        try:
            with open(_local_path(key), encoding="utf-8") as f:
                return {"id": 0, "state": json.load(f)}
        except (OSError, ValueError):
            return None


def load(key=KEY):
    """(state, row id) of a portfolio (the owner's by default, or a visitor's: key=visitor_key(code)); a new account when
    there is none yet (nothing is written until the first order or setting). Raises paperbots.StoreError."""
    raw = _load_raw(_pb().backend(), _REV["n"], key)
    st_ = clean(raw["state"]) if raw else None
    return (st_ or new_state()), (raw or {}).get("id")


class Conflict(Exception):
    """The saved portfolio changed since it was read (another page saved first)."""


def save(state, row_id=None, expect="any", key=KEY):
    """Keeps the account. `expect`: the revision it was read at; the save is refused (Conflict) when the stored one has moved
    on, so a page that read an older copy can never overwrite a newer order."""
    PB = _pb()
    prev = state.get("rev")
    state["rev"] = int(prev or 0) + 1
    body = json.loads(json.dumps(state, default=float))
    try:
        if PB.backend() == "supabase":
            url, h = PB._sb()
            rec = {"name": body.get("name") or ("Paper Portfolio" if key == KEY else "Visitor portfolio"), "symbol": "PORTFOLIO",
                   "strategy": key, "params": {"pf": body}, "capital": float(body.get("start_cash") or 0), "start_date": body["created"][:10]}
            if row_id:
                q = {"id": f"eq.{int(row_id)}", "select": "id"}
                if expect != "any":
                    q["params->pf->>rev"] = "is.null" if expect is None else f"eq.{int(expect)}"
                r = PB._request("PATCH", url, headers={**h, "Prefer": "return=representation"}, params=q, data=json.dumps(rec))
                PB._check(r)
                if expect != "any" and not r.json():
                    raise Conflict()
            else:
                r = PB._request("POST", url, headers={**h, "Prefer": "return=minimal"}, data=json.dumps(rec))
                PB._check(r)
        else:
            path = _local_path(key)
            with _LOCK:
                if expect != "any":
                    try:
                        with open(path, encoding="utf-8") as f:
                            cur = json.load(f).get("rev")
                    except (OSError, ValueError):
                        cur = None
                    if cur != expect:
                        raise Conflict()
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(body, f)
                os.replace(tmp, path)
    except Exception:
        state["rev"] = prev
        raise
    _REV["n"] += 1
    _load_raw.clear()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "20.1"
