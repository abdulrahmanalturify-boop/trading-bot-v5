"""
brain.py - The smart bots' layer on top of the bot engine (paperbots.simulate).

A plain bot buys whenever one of its strategies signals. A smart bot adds the five parts that separate a trained bot from a
plain one:
  1. MARKET REGIME  every session it reads the market: bull, neutral (sideways), bear, or stress (panic volatility), from the
                    S&P 500's trend and volatility and the share of the bot's stocks above their 50-day average (breadth);
  2. STRATEGY CHOICE only the strategy families that suit that regime may open trades (trend and breakouts in a bull market,
                    buying dips in a sideways one, nothing in a panic), and a regime can also sell everything;
  3. SIGNAL SCORE   every buy signal gets a score out of 100 (trend 20, momentum 20, volume 15, volatility 10, structure 15,
                    reward/risk 20); only signals over the bot's minimum are taken, the best first;
  4. DYNAMIC RISK   each trade is sized so that its ATR stop loses a set % of the balance, smaller when the score is lower, the
                    regime worse or the bot in a drawdown; a sector cap, fewer open trades in a weaker regime, a stop that
                    moves to break-even and then trails the highest high, and a time stop for trades that go nowhere;
  5. SELF-CHECK     a circuit breaker (no buys for a while after a deep drawdown, after a losing streak, or after a bad day),
                    and a strategy whose signals of the last year did clearly worse than the market is muted until they
                    recover.
Everything is decided at a session's close from what was known at that close (no look-ahead); the orders fill at the next
open, like every other bot. Pure numpy / pandas: no UI.
"""
import numpy as np
import pandas as pd

import ta

REGIMES = ("bull", "neutral", "bear", "stress")
BULL, NEUTRAL, BEAR, STRESS = range(4)
REGIME_LABEL = {"bull": ("Bull market", "سوق صاعد"), "neutral": ("Sideways market", "سوق عرضي"),
                "bear": ("Bear market", "سوق هابط"), "stress": ("Panic volatility", "تذبذب حاد")}

# the family of every strategy: what kind of market it is made for
FAMILIES = ("trend", "breakout", "momentum", "reversion")
FAMILY_LABEL = {"trend": ("Trend", "اتجاه"), "breakout": ("Breakout", "اختراق"), "momentum": ("Momentum", "زخم"),
                "reversion": ("Buying dips", "شراء التصحيحات")}
FAMILY = {
    "SMA Crossover": "trend", "EMA Crossover": "trend", "Golden Cross (50/200)": "trend", "MACD Crossover": "trend",
    "OBV Trend (Volume)": "trend", "VWMA Crossover (Volume)": "trend", "Trend Following": "trend",
    "Moving Average Crossover": "trend", "Regime-Based Strategy": "trend", "Machine Learning Signal Combination": "trend",
    "Multi-Factor Strategy": "momentum",
    "Bollinger Breakout": "breakout", "Donchian Breakout (Turtle)": "breakout", "Volume Breakout": "breakout",
    "Breakout Strategy": "breakout", "Volatility Breakout": "breakout",
    "Momentum Strategy": "momentum", "Relative Strength Strategy": "momentum", "Portfolio-Level Strategy": "momentum",
    "RSI Mean Reversion": "reversion", "MFI Money Flow (Volume)": "reversion", "Mean Reversion": "reversion",
    "VWAP Mean Reversion": "reversion", "VWAP Reclaim / Pullback": "reversion", "Pairs Trading": "reversion",
    "Statistical Arbitrage": "reversion",
    # the combined strategies (playbooks.py)
    "Trend Pullback": "reversion", "Range Reversion": "reversion", "Breakout & Retest": "breakout", "Squeeze Breakout": "breakout",
    "Opening Range Breakout": "breakout",
}

# the score: six parts, each worth its weight (the weights add up to 100)
PARTS = ("trend", "mom", "vol", "volat", "struct", "rr")
PART_LABEL = {"trend": ("Trend", "الاتجاه"), "mom": ("Momentum", "الزخم"), "vol": ("Volume", "الحجم"),
              "volat": ("Volatility", "التذبذب"), "struct": ("Structure", "بنية السعر"), "rr": ("Reward/risk", "العائد/المخاطرة")}
WEIGHTS = {"trend": 20, "mom": 20, "vol": 15, "volat": 10, "struct": 15, "rr": 20}

DEFAULTS = {
    "min_score": 60,                  # buy only signals scoring at least this (out of 100)
    "weights": WEIGHTS,
    "allow": {"bull": ["trend", "breakout", "momentum", "reversion"], "neutral": ["reversion"], "bear": [], "stress": []},
    "size": {"bull": 1.0, "neutral": 0.6, "bear": 0.3, "stress": 0.0},       # risk of a new trade, x the base risk
    "exposure": {"bull": 1.0, "neutral": 0.6, "bear": 0.3, "stress": 0.0},   # share of the open-trade slots usable
    "exit": ["stress"],               # regimes that sell every open trade at the next open
    "risk": 1.0,                      # % of the balance a full-size trade loses at its stop
    "size_floor": 0.5,                # the weakest signal that passes gets this share of the full size (the best gets all)
    "atr": 3.0,                       # the stop: this many ATR under the entry
    "sector_cap": 3,                  # open trades in one sector at most (0 = no cap)
    "be_r": 1.5,                      # the stop moves to the entry once the trade has been up this many R (0 = off)
    "trail_atr": 3.5,                 # then trails: highest high - this x the entry ATR (0 = off)
    "time_bars": 0,                   # time stop: after this many sessions (0 = off) ...
    "time_r": 0.5,                    # ... sell unless the trade is up at least this many R
    "dd_half": 10.0,                  # drawdown % from the peak where new trades are halved
    "dd_stop": 20.0,                  # drawdown % where the bot stops buying for `pause` sessions, then starts a new peak
    "pause": 20,
    "streak": 5,                      # after this many losing trades in a row ...
    "cool": 5,                        # ... no buys for this many sessions
    "day_loss": 3.0,                  # a session that loses this % of the balance: no buys at its close
    "decay": 1,                       # mute a strategy whose signals of the last year did clearly worse than the market
    "stress_vol": 30.0,               # panic: the S&P 500's 20-day volatility at least this % a year ...
    "stress_x": 2.0,                  # ... or this many times its median of the last year (and at least 20%)
    "prefer": [],                     # the bot's style: signals of these families get `bonus` points on their score
    "bonus": 0.0,
    "choose": "first",                # when several strategies signal on one stock: "edge" = the one whose signals did best
                                      # lately (its style first), "first" = the first in the list
    "multi": [],                      # besides each strategy alone, "m strategies agree" rules (buy when at least m of them
                                      # are in their buy state, sell when fewer are): the bot may trade on one or on several
    "combos": [],                     # combined strategies: [{"of": [strategies], "min": m}] - each is "in" a stock while at
                                      # least m of its strategies are in their buy state (one strategy alone trades on its own
                                      # signals); with combos the bot trades only them
    "sector_rank": 0,                 # trade only the sector ranked this by the growth of its stocks over `sector_days`
    "sector_days": 252,               # sessions (re-ranked at the start of every month; 0 = every sector)
}
EDGE_H, EDGE_WIN, EDGE_MIN, EDGE_CUT = 10, 250, 30, -0.01   # 10-session return after each signal, over the last year


def _f(v, lo, hi, dflt):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return float(dflt)
    return float(min(max(v, lo), hi)) if np.isfinite(v) else float(dflt)


def clean(b):
    """A brain's settings with every value in its range and every missing one at its default (None when b is empty)."""
    if not isinstance(b, dict) or not b:
        return None
    d = DEFAULTS
    w = b.get("weights") if isinstance(b.get("weights"), dict) else {}
    w = {p: round(_f(w.get(p, WEIGHTS[p]), 0, 100, WEIGHTS[p]), 4) for p in PARTS}
    tot = sum(w.values())
    if tot <= 0:
        w, tot = dict(WEIGHTS), 100.0
    if abs(tot - 100) >= 0.01:                     # scaled to 100 (a second clean leaves it as it is)
        w = {p: round(v * 100 / tot, 4) for p, v in w.items()}
    allow = b.get("allow") if isinstance(b.get("allow"), dict) else d["allow"]
    lists = {r: allow.get(r, d["allow"][r]) for r in REGIMES}
    allow = {r: [f for f in FAMILIES if isinstance(lists[r], (list, tuple)) and f in lists[r]] for r in REGIMES}

    def per_regime(key):
        x = b.get(key) if isinstance(b.get(key), dict) else {}
        return {r: _f(x.get(r, d[key][r]), 0, 1, d[key][r]) for r in REGIMES}
    ints = lambda k, lo, hi: int(round(_f(b.get(k, d[k]), lo, hi, d[k])))
    return {"min_score": _f(b.get("min_score", d["min_score"]), 0, 100, d["min_score"]), "weights": w, "allow": allow,
            "size": per_regime("size"), "exposure": per_regime("exposure"),
            "exit": [r for r in REGIMES if r in (b.get("exit") if isinstance(b.get("exit"), (list, tuple)) else d["exit"])],
            "risk": _f(b.get("risk", d["risk"]), 0.1, 5, d["risk"]), "atr": _f(b.get("atr", d["atr"]), 0.5, 10, d["atr"]),
            "size_floor": _f(b.get("size_floor", d["size_floor"]), 0, 1, d["size_floor"]),
            "stress_vol": _f(b.get("stress_vol", d["stress_vol"]), 10, 200, d["stress_vol"]),
            "stress_x": _f(b.get("stress_x", d["stress_x"]), 1, 10, d["stress_x"]),
            "prefer": [f for f in FAMILIES if f in (b.get("prefer") if isinstance(b.get("prefer"), (list, tuple)) else [])],
            "bonus": _f(b.get("bonus", d["bonus"]), 0, 50, d["bonus"]),
            "choose": "edge" if b.get("choose") == "edge" else "first",
            "multi": sorted({int(m) for m in (b.get("multi") if isinstance(b.get("multi"), (list, tuple)) else [])
                             if isinstance(m, (int, float)) and 2 <= m <= 20}),
            "sector_rank": ints("sector_rank", 0, 11), "sector_days": ints("sector_days", 21, 504),
            "combos": _combos(b.get("combos")),
            "sector_cap": ints("sector_cap", 0, 20), "be_r": _f(b.get("be_r", d["be_r"]), 0, 10, d["be_r"]),
            "trail_atr": _f(b.get("trail_atr", d["trail_atr"]), 0, 20, d["trail_atr"]),
            "time_bars": ints("time_bars", 0, 250), "time_r": _f(b.get("time_r", d["time_r"]), -5, 10, d["time_r"]),
            "dd_half": _f(b.get("dd_half", d["dd_half"]), 1, 90, d["dd_half"]),
            "dd_stop": _f(b.get("dd_stop", d["dd_stop"]), 1, 95, d["dd_stop"]), "pause": ints("pause", 0, 250),
            "streak": ints("streak", 0, 50), "cool": ints("cool", 0, 250),
            "day_loss": _f(b.get("day_loss", d["day_loss"]), 0, 50, d["day_loss"]), "decay": int(bool(b.get("decay", d["decay"])))}


def _combos(v):
    """Combined strategies, cleaned: up to 6, each of 1..6 different strategies with an agreement of 1..all (one strategy
    alone is that strategy trading on its own signals, next to the combinations)."""
    out = []
    for c in (v if isinstance(v, (list, tuple)) else [])[:6]:
        if not isinstance(c, dict) or not isinstance(c.get("of"), (list, tuple)):
            continue
        of = list(dict.fromkeys(str(x) for x in c["of"] if isinstance(x, str) and x))[:6]
        if not of:
            continue
        m = int(round(_f(c.get("min", len(of)), 1, len(of), len(of))))
        out.append({"of": of, "min": m})
    return out


def combo_label(c):
    """The name a combined strategy trades under: its strategies joined by ' & ', with its agreement: 'A & B (2/2)'; one
    strategy alone trades under its own name."""
    if len(c["of"]) == 1:
        return c["of"][0]
    return " & ".join(c["of"]) + f" ({c['min']}/{len(c['of'])})"


def combo_parts(label):
    """([strategies], m) of a combined-strategy label, else None."""
    if not isinstance(label, str) or " & " not in label or not label.endswith(")"):
        return None
    head, _, tail = label.rpartition(" (")
    try:
        m, n = (int(x) for x in tail[:-1].split("/"))
    except ValueError:
        return None
    of = head.split(" & ")
    return (of, m) if len(of) == n else None


def family_of(strategy):
    return FAMILY.get(strategy, "trend")


AGREE = "__agree{}__"                 # the label of an "m strategies agree" rule


def agree_level(label):
    """m for an "m strategies agree" label, else None."""
    if isinstance(label, str) and label.startswith("__agree") and label.endswith("__"):
        try:
            return int(label[7:-2])
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------- the sector of a sector bot
def sector_by_rank(CF, sectors, idx, rank, days=252, min_stocks=5):
    """(T,) the sector a bot trades at each session: the one ranked `rank` by the average growth of its stocks over the
    last `days` sessions, ranked again on the first session of every month from the closes up to the session before
    (no look-ahead). '' until there is enough history. Also returns [(first day, sector)] for every change."""
    T = len(CF)
    names = sorted({s for s in sectors if s})
    cols = {s: [j for j, x in enumerate(sectors) if x == s] for s in names}
    cols = {s: c for s, c in cols.items() if len(c) >= min_stocks}
    ix = _naive(idx)
    out = np.array([""] * T, dtype=object)
    cur, changes = "", []
    for t in range(1, T):
        if ix[t].month != ix[t - 1].month or t == 1:
            if t - 1 - days >= 0:
                with np.errstate(invalid="ignore", divide="ignore"):
                    g = CF[t - 1] / CF[t - 1 - days] - 1
                ranked = sorted(((float(np.nanmean(g[c])) if np.isfinite(g[c]).any() else -np.inf, s) for s, c in cols.items()),
                                reverse=True)
                new = ranked[rank - 1][1] if len(ranked) >= rank and np.isfinite(ranked[rank - 1][0]) else ""
                if new != cur:
                    cur = new
                    changes.append((str(ix[t])[:10], cur))
        out[t] = cur
    return out, changes


# ---------------------------------------------------------------- 1) the market regime
MIN_CROSS = 5          # a day needs at least this many stocks with a value to compare a stock with the others


def _row_mean(a, min_n=1):
    """The mean of every row over its finite values (NaN for a row with fewer than min_n)."""
    fin = np.isfinite(a)
    cnt = fin.sum(axis=1)
    return np.where(cnt >= min_n, np.where(fin, a, 0.0).sum(axis=1) / np.maximum(cnt, 1), np.nan)


def _naive(ix):
    ix = pd.DatetimeIndex(ix)
    return ix.tz_localize(None) if ix.tz is not None else ix


def regime(spy, idx, above50, stress_vol=30.0, stress_x=2.0):
    """The regime code of every session of idx (BULL, NEUTRAL, BEAR, STRESS) and its inputs.
    above50: (T, N) 1.0 / 0.0 = the stock closed above / under its 50-day average, NaN = unknown.
      stress  the S&P 500's 20-day volatility is stress_vol % a year or more, or stress_x times its median of the last year
              and at least 20%
      bear    the S&P 500 under its 200-day average and its 50-day average falling (over 20 sessions)
      bull    the S&P 500 over its 200-day average, its 50-day average rising and at least half the stocks over their own
      neutral everything else (and whenever the S&P 500 is missing or too short to tell)"""
    T = len(idx)
    breadth = _row_mean(above50)
    codes = np.full(T, NEUTRAL, np.int8)
    parts = {"breadth": breadth, "trend": np.full(T, np.nan), "slope": np.full(T, np.nan), "vol": np.full(T, np.nan)}
    if spy is None or len(spy) < 2:
        return codes, parts
    sc = spy["Close"].astype(float)
    sc.index = _naive(sc.index)
    sc = sc[~sc.index.duplicated(keep="last")].sort_index()
    sma200 = sc.rolling(200, min_periods=200).mean()
    sma50 = sc.rolling(50, min_periods=50).mean()
    slope = sma50 / sma50.shift(20) - 1
    vol = sc.pct_change().rolling(20, min_periods=20).std() * np.sqrt(252)
    vmed = vol.rolling(252, min_periods=60).median()
    ix = _naive(idx)
    al = lambda s: s.reindex(ix, method="ffill").to_numpy(float)
    c, s200, sl, v, vm = al(sc), al(sma200), al(slope), al(vol), al(vmed)
    with np.errstate(invalid="ignore"):
        stress = (v >= stress_vol / 100) | ((v >= 0.20) & (v >= stress_x * vm))
        bear = (c < s200) & (sl < 0)
        bull = (c > s200) & (sl > 0) & (np.nan_to_num(breadth, nan=0.5) >= 0.5)
    codes[bull] = BULL
    codes[bear] = BEAR
    codes[stress] = STRESS
    parts.update(trend=c / s200 - 1, slope=sl, vol=v)
    return codes, parts


# ---------------------------------------------------------------- 3) the score of a buy signal
def _ramp(x, lo, hi):
    """0 at lo, 1 at hi, linear in between (NaN stays NaN)."""
    return np.clip((x - lo) / (hi - lo), 0.0, 1.0)


def stock_parts(df, atr_mult):
    """The per-stock inputs of the score on every bar of df (each from that bar's close and before):
    {'trend', 'volp', 'volat', 'struct', 'rr', 'mraw', 'above50'} as arrays (mraw is ranked across the stocks later)."""
    c, h, l = (df[k].astype(float) for k in ("Close", "High", "Low"))
    v = df["Volume"].astype(float) if "Volume" in df else pd.Series(np.nan, index=df.index)
    sma50, sma200 = c.rolling(50, min_periods=50).mean(), c.rolling(200, min_periods=200).mean()
    slope50 = sma50 / sma50.shift(20) - 1
    with np.errstate(invalid="ignore"):
        trend = (0.35 * (c > sma50) + 0.35 * (sma50 > sma200) + 0.30 * (slope50 > 0)).astype(float)
        trend[sma50.isna()] = np.nan
        mraw = 0.5 * (c / c.shift(126) - 1) + 0.5 * (c / c.shift(63) - 1)
        rv = v / v.shift(1).rolling(20, min_periods=10).mean()
        volp = _ramp(rv.to_numpy(float), 0.8, 2.0)
        a = ta.atr(df).astype(float)
        atrp = (a / c).to_numpy(float)
        # volatility: a normal daily range (1.2%..3.5% of the price) scores full, a very quiet or a wild stock less
        volat = np.where(atrp < 0.012, 0.5 + 0.5 * _ramp(atrp, 0.008, 0.012), 1.0 - _ramp(atrp, 0.035, 0.06))
        volat[~np.isfinite(atrp)] = np.nan
        hi252 = h.rolling(252, min_periods=60).max()
        near = _ramp((c / hi252).to_numpy(float), 0.75, 0.95)
        higher_lows = (l.rolling(10).min() > l.shift(10).rolling(10).min()).to_numpy(float)
        struct = 0.6 * near + 0.4 * higher_lows
        # reward / risk: the risk is the ATR stop; the reward is the way up to the 60-day high (a stock at a new high has
        # open sky: 3R)
        risk = atr_mult * a
        hi60 = h.rolling(60, min_periods=20).max()
        reward = np.where(c < 0.98 * hi60, hi60 - c, 3.0 * risk)
        rr = _ramp((reward / risk).to_numpy(float), 0.0, 3.0)
        above50 = np.where(sma50.isna(), np.nan, (c > sma50).astype(float))
    return {"trend": trend.to_numpy(float), "volp": volp, "volat": volat, "struct": struct, "rr": rr,
            "mraw": mraw.to_numpy(float), "above50": above50}


def score(P, weights):
    """The score (T, N) out of 100 and its parts {part: (T, N) points}, from the stacked stock_parts P."""
    with np.errstate(invalid="ignore"):
        mom = pd.DataFrame(P["mraw"]).rank(axis=1, pct=True).to_numpy(float, copy=True)   # momentum against the other stocks that day
    few = np.isfinite(P["mraw"]).sum(axis=1) < MIN_CROSS                          # too few stocks to rank: a neutral half
    mom[few] = np.where(np.isfinite(P["mraw"][few]), 0.5, np.nan)
    raw = {"trend": P["trend"], "mom": mom, "vol": P["volp"], "volat": P["volat"], "struct": P["struct"], "rr": P["rr"]}
    pts = {p: np.nan_to_num(raw[p], nan=0.0) * weights[p] for p in PARTS}
    total = sum(pts.values())
    total[np.isnan(P["trend"])] = np.nan                  # too little history to judge the stock
    return total, pts


# ---------------------------------------------------------------- 5) self-check: a strategy whose signals lost their edge
def excess(O, C, h=EDGE_H):
    """(T, N) what buying each stock at the next open and holding it h sessions made, minus the average stock that day
    (NaN where it isn't known; one stock alone: its raw return)."""
    T = len(C)
    fr = np.full(C.shape, np.nan)
    if T > h + 1:
        with np.errstate(invalid="ignore", divide="ignore"):
            fr[:T - h] = C[h:] / O[1:T - h + 1] - 1
    return fr - np.nan_to_num(_row_mean(fr, MIN_CROSS), nan=0.0)[:, None]


def edge(ent, ex, h=EDGE_H, window=EDGE_WIN, min_n=EDGE_MIN, cut=EDGE_CUT):
    """A strategy's edge at every session: the average of ex over its buy signals of the last `window` sessions, each
    counted only once its h sessions have passed (no look-ahead). Returns (ok, value): ok is False while that average is
    under `cut` with at least min_n signals; value is NaN with fewer than min_n."""
    T = len(ex)
    m = ent & np.isfinite(ex)
    s = np.where(m, ex, 0.0).sum(axis=1)
    n = m.sum(axis=1).astype(float)
    s = np.r_[np.zeros(h), s[:T - h]] if T > h else np.zeros(T)
    n = np.r_[np.zeros(h), n[:T - h]] if T > h else np.zeros(T)
    S = pd.Series(s).rolling(window, min_periods=1).sum().to_numpy()
    Nn = pd.Series(n).rolling(window, min_periods=1).sum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        val = np.where(Nn >= min_n, S / np.maximum(Nn, 1), np.nan)
    return (Nn < min_n) | (np.nan_to_num(val, nan=np.inf) > cut), val


def edge_ok(ent, O, C, h=EDGE_H, window=EDGE_WIN, min_n=EDGE_MIN, cut=EDGE_CUT):
    """(T,) True while the strategy may trade (see edge)."""
    return edge(ent, excess(O, C, h), h, window, min_n, cut)[0]


# ---------------------------------------------------------------- 4) sizing
def size_mult(sc, min_score, regime_size, dd, dd_half, floor=0.5):
    """The share of the full risk a new trade gets: floor..1 by its score, x the regime's size, halved in a drawdown."""
    s = 1.0 if min_score >= 100 else floor + (1 - floor) * float(np.clip((sc - min_score) / (100 - min_score), 0, 1))
    return s * regime_size * (0.5 if dd >= dd_half / 100 else 1.0)

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "18.0"
