"""
playbooks.py - "Combined strategies": five trading playbooks written as exact numeric rules (nothing is read off a chart),
for the Paper Bots.

Four run on daily candles like every other strategy on the site: the rules are checked on a session's close and the order
is filled at the next open; stops and targets are watched during the day. The Opening Range Breakout runs on 5-minute
candles (paperbots.simulate_orb).

A daily playbook returns (entries, exits, plan):
  entries          bool Series - the entry rule is met on that bar's close (the bot buys at the next open)
  exits            bool Series - the early-exit condition holds on that bar's close (the bot sells at the next open);
                   it can never be true on an entry bar, so a new trade is not closed by an old condition
  plan             "stop"     Series - the stop price fixed on the signal bar
                   "target"   Series of absolute target prices, or None
                   "target_r" target = entry + target_r x (entry - stop) when there is no absolute target
                   "max_bars" time stop: sell at the next open once the trade has been held this many sessions
                   "floor"    optional Series: the trade is sold at the next open after a close under this price (fixed on
                              the signal bar, so every trade keeps its own line)
A daily trade is skipped when the next open is already at or under its stop (or at or over an absolute target).

Shared definitions (daily candles, t = the signal bar):
  SMA(n) / EMA(n)  simple / exponential average of the close
  ATR, RSI, ADX    14 sessions, Wilder smoothing
  RVOL             volume(t) / average volume of the 20 sessions before t
  Bollinger        20-session SMA +/- 2 standard deviations; band width BBW = (upper - lower) / middle
  swing high / low a bar whose high (low) is above (below) the 3 bars before it and at least as high (low) as the 3 bars
                   after it; it is only known 3 bars later, so no rule ever uses a future bar (of two equal highs the
                   first one counts)
  market trend     SPY close > SPY SMA(200)
"""
import numpy as np
import pandas as pd

import mcal
import ta

SWING = 3                    # bars on each side of a swing point
TREND_PULLBACK, BREAKOUT_RETEST = "Trend Pullback", "Breakout & Retest"
SQUEEZE, RANGE, ORB = "Squeeze Breakout", "Range Reversion", "Opening Range Breakout"


# ---------------------------------------------------------------- building blocks
def rvol(df, n=20):
    """Relative volume: today's volume against the average of the n sessions before it."""
    v = df["Volume"].astype(float) if "Volume" in df else pd.Series(np.nan, index=df.index)
    return v / v.shift(1).rolling(n).mean().replace(0, np.nan)


def _ffill(x):
    return np.array(pd.Series(x).ffill(), dtype=float)


def _roll(x, n, fn):
    """Rolling max / min / mean of the n values ending at each bar (NaN until there are n)."""
    return getattr(pd.Series(x).rolling(int(n)), fn)().to_numpy(float)


def _shift(x, k=1):
    out = np.full(len(x), np.nan)
    if k < len(x):
        out[k:] = x[:len(x) - k]
    return out


def _ewm(x, alpha):
    return pd.Series(x).ewm(alpha=alpha, adjust=False).mean().to_numpy(float)


def _swings_of(s, k, high):
    """(last, previous) swing value known at every bar for one price array (see swings)."""
    n = len(s)
    last = np.full(n, np.nan)
    prev = np.full(n, np.nan)
    if n < 2 * k + 1:
        return last, prev
    win = np.lib.stride_tricks.sliding_window_view(s, k)
    w = win.max(axis=1) if high else win.min(axis=1)                  # w[j] = extreme of s[j .. j+k-1]
    i = np.arange(k, n - k)                                            # bars with k bars on both sides
    left, right = w[i - k], w[i + 1]
    ext = (s[i] > left) & (s[i] >= right) if high else (s[i] < left) & (s[i] <= right)
    at = i[ext] + k                                                    # known k bars after the swing bar
    ev = np.full(n, np.nan)
    ev[at] = s[i[ext]]
    pv = np.full(n, np.nan)
    pv[at[1:]] = s[i[ext]][:-1]                                        # at each swing, the one before it
    return _ffill(ev), _ffill(pv)


def swings(df, k=SWING):
    """(last swing high, previous swing high, last swing low, previous swing low) as known at every bar."""
    h, l = df["High"].to_numpy(float), df["Low"].to_numpy(float)
    return tuple(pd.Series(x, index=df.index) for x in (*_swings_of(h, k, True), *_swings_of(l, k, False)))


def _argmin_pos(x, n):
    """For every bar t: the position of the lowest value among the n bars ending at t (the first one on a tie), -1 before
    there are n bars."""
    out = np.full(len(x), -1, dtype=int)
    if len(x) < n:
        return out
    win = np.lib.stride_tricks.sliding_window_view(np.where(np.isnan(x), np.inf, x), n)
    out[n - 1:] = np.arange(len(win)) + np.argmin(win, axis=1)
    return out


def _naive(idx):
    idx = pd.DatetimeIndex(idx)
    return idx.tz_localize(None) if idx.tz is not None else idx


def market_up(df, market, n=200):
    """True while SPY closes above its n-session average (always True when SPY is not available)."""
    if market is None or len(market) < n:
        return pd.Series(True, index=df.index)
    c = market["Close"].astype(float).copy()
    c.index = _naive(c.index)
    c = c[~c.index.duplicated(keep="last")].sort_index()
    ok = (c > c.rolling(n).mean()).astype(float)
    target = _naive(df.index)
    aligned = ok.reindex(ok.index.union(target)).ffill().reindex(target)
    return pd.Series(aligned.fillna(0).to_numpy() > 0, index=df.index)


def first_bar(cond):
    """The first bar of a condition (False -> True)."""
    cond = cond.fillna(False).astype(bool)
    return cond & ~cond.shift(1, fill_value=False)


class Ind:
    """One stock's indicators, computed once and shared by the playbooks (numpy arrays, the same formulas as ta.py)."""

    def __init__(self, df, market=None):
        self.df, self.spy, self.memo = df, market, {}
        self.o, self.h, self.l, self.c = (df[k].to_numpy(float) for k in ("Open", "High", "Low", "Close"))
        self.v = df["Volume"].to_numpy(float) if "Volume" in df else np.full(len(df), np.nan)

    def _get(self, key, fn):
        if key not in self.memo:
            self.memo[key] = fn()
        return self.memo[key]

    def tr(self):
        def f():
            pc = _shift(self.c)
            return np.fmax(self.h - self.l, np.fmax(np.abs(self.h - pc), np.abs(self.l - pc)))
        return self._get("tr", f)

    def atr(self, n=14):
        return self._get(("atr", n), lambda: _ewm(self.tr(), 1 / n))

    def rsi(self, n=14):
        def f():
            d = np.r_[np.nan, np.diff(self.c)]
            gain = _ewm(np.where(np.isnan(d), np.nan, np.maximum(d, 0.0)), 1 / n)
            loss = _ewm(np.where(np.isnan(d), np.nan, np.maximum(-d, 0.0)), 1 / n)
            with np.errstate(divide="ignore", invalid="ignore"):
                rs = gain / np.where(loss == 0, np.nan, loss)
                out = 100 - 100 / (1 + rs)
            return np.where(np.isnan(out), 100.0, out)
        return self._get(("rsi", n), f)

    def adx(self, n=14):
        def f():
            up, down = np.r_[np.nan, np.diff(self.h)], -np.r_[np.nan, np.diff(self.l)]
            with np.errstate(invalid="ignore"):
                plus_dm = np.where((up > down) & (up > 0), up, 0.0)
                minus_dm = np.where((down > up) & (down > 0), down, 0.0)
            tr = _ewm(self.tr(), 1 / n)
            with np.errstate(divide="ignore", invalid="ignore"):
                p_di = 100 * _ewm(plus_dm, 1 / n) / tr
                m_di = 100 * _ewm(minus_dm, 1 / n) / tr
                tot = p_di + m_di
                dx = 100 * np.abs(p_di - m_di) / np.where(tot == 0, np.nan, tot)
            return _ewm(dx, 1 / n)
        return self._get(("adx", n), f)

    def sma(self, n):
        return self._get(("sma", n), lambda: _roll(self.c, n, "mean"))

    def ema(self, n):
        return self._get(("ema", n), lambda: pd.Series(self.c).ewm(span=n, adjust=False).mean().to_numpy(float))

    def boll(self, n=20, k=2.0):
        def f():
            mid = self.sma(n)
            sd = pd.Series(self.c).rolling(int(n)).std().to_numpy(float)
            up, low = mid + k * sd, mid - k * sd
            return mid, up, low, (up - low) / mid
        return self._get(("boll", n, k), f)

    def rvol(self, n=20):
        def f():
            base = _roll(_shift(self.v), n, "mean")
            with np.errstate(divide="ignore", invalid="ignore"):
                return self.v / np.where(base == 0, np.nan, base)
        return self._get(("rvol", n), f)

    def swings(self):
        return self._get("swings", lambda: (*_swings_of(self.h, SWING, True), *_swings_of(self.l, SWING, False)))

    def market(self):
        return self._get("market", lambda: market_up(self.df, self.spy).to_numpy(bool))


def _out(df, entries, exits, plan):
    idx = df.index
    s = lambda x: None if x is None else pd.Series(x, index=idx)
    return (pd.Series(entries, index=idx), pd.Series(exits, index=idx),
            {**plan, "stop": s(plan["stop"]), "target": s(plan["target"]), **({"floor": s(plan["floor"])} if "floor" in plan else {})})


# ---------------------------------------------------------------- 1) trend pullback
def trend_pullback(df, market=None, trend_ma=200, mid_ma=50, pull_ema=20, adx_min=20, rsi_dip=50, lookback=5, target_r=2.0,
                   max_bars=20, ind=None):
    ind = ind or Ind(df, market)
    c, h, l, o = ind.c, ind.h, ind.l, ind.o
    a, r = ind.atr(), ind.rsi()
    slow, mid, e = ind.sma(int(trend_ma)), ind.sma(int(mid_ma)), ind.ema(int(pull_ema))
    sh1, sh0, sl1, sl0 = ind.swings()
    lb = int(lookback)
    with np.errstate(invalid="ignore"):
        trend = (c > slow) & (mid > slow) & (mid > _shift(mid, 10)) & (sh1 > sh0) & (sl1 > sl0) & (ind.adx() >= adx_min)
        # pullback: a low reached the EMA zone, or the previous swing high (old resistance, now support), in the last `lookback` bars
        touch = (l <= e + 0.25 * a) | ((l <= sh0 + 0.25 * a) & (c >= sh0 - 0.25 * a))
        touched = _roll(touch.astype(float), lb, "max") > 0
        low_w = _roll(l, lb, "min")
        # the drop into the pullback: the highest high of the 10 sessions up to the pullback low, minus that low
        lo_pos = _argmin_pos(l, lb)
        hh10 = _roll(h, 10, "max")
        drop = np.full(len(c), np.nan)
        ok = lo_pos >= 0
        drop[ok] = hh10[lo_pos[ok]] - l[lo_pos[ok]]
        deep = drop >= a                                               # at least 1 ATR
        held = low_w >= mid - 0.5 * a                                  # did not break the medium average
        dipped = _roll(r, lb, "min") <= rsi_dip
        resume = (c > _shift(h)) & (c > e) & (c > mid) & (c > o) & (r > _shift(r))
        entries = trend & touched & deep & held & dipped & resume
        stop = np.maximum(low_w - 0.25 * a, c - 3 * a)                 # under the pullback low, never more than 3 ATR away
        exits = c < mid
    return _out(df, entries, exits, {"stop": np.where(entries, stop, np.nan), "target": None, "target_r": float(target_r),
                                     "max_bars": int(max_bars)})


# ---------------------------------------------------------------- 2) breakout and retest
def breakout_retest(df, market=None, level_days=20, rvol_min=1.5, break_pct=0.2, window=5, tol_pct=0.5, max_break_pct=1.0,
                    target_r=2.0, max_bars=15, ind=None):
    ind = ind or Ind(df, market)
    c, h, l = ind.c, ind.h, ind.l
    a = ind.atr()
    lvl = _roll(_shift(h), int(level_days), "max")                    # resistance = highest high of the prior N bars
    rv = ind.rvol()
    n = len(c)
    ent, stop, level = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    up_k, tol_k, dip_k = 1 + break_pct / 100, 1 + tol_pct / 100, 1 - max_break_pct / 100
    x, b = np.nan, -1
    for t in range(n):
        if lvl[t] == lvl[t] and c[t] >= lvl[t] * up_k and rv[t] >= rvol_min:
            x, b = lvl[t], t                                       # a new breakout replaces any older setup
            continue
        if b < 0:
            continue
        if t - b > window or c[t] < x * dip_k:
            x, b = np.nan, -1                                      # too late, or it closed back inside: setup cancelled
            continue
        if l[t] <= x * tol_k and l[t] >= x * dip_k and c[t] >= x and c[t] >= (h[t] + l[t]) / 2:
            ent[t], stop[t], level[t] = True, min(l[t], x) - 0.25 * a[t], x
            x, b = np.nan, -1                                      # one trade per breakout
    # each trade's own failure line (a close under it sells at the next open): the level it retested, minus the allowed dip
    return _out(df, ent, np.zeros(n, bool), {"stop": stop, "target": None, "target_r": float(target_r), "max_bars": int(max_bars),
                                              "floor": level * dip_k})


# ---------------------------------------------------------------- 3) volatility squeeze, then breakout
def squeeze_breakout(df, market=None, bb_period=20, bb_std=2.0, rank_days=126, squeeze_pct=20, recent=5, rvol_min=1.5, target_r=3.0,
                     max_bars=30, ind=None):
    ind = ind or Ind(df, market)
    c = ind.c
    mid, up, _, bbw = ind.boll(int(bb_period), float(bb_std))
    with np.errstate(invalid="ignore"):
        tight = bbw <= pd.Series(bbw).rolling(int(rank_days)).quantile(squeeze_pct / 100).to_numpy(float)
        squeezed = _roll(_shift(tight.astype(float)), int(recent), "max") > 0   # a squeeze in the `recent` bars before t
        brk = (c > up) & (_shift(c) <= _shift(up))                              # first close above the upper band
        entries = squeezed & brk & (ind.rvol() >= rvol_min) & ind.market() & (c > ind.sma(50))
        stop = np.minimum(mid, c - ind.atr())                                   # middle band, at least 1 ATR below
        exits = c < mid
    return _out(df, entries, exits, {"stop": np.where(entries, stop, np.nan), "target": None, "target_r": float(target_r),
                                     "max_bars": int(max_bars)})


# ---------------------------------------------------------------- 4) range reversion
def range_reversion(df, market=None, range_days=40, adx_max=20, slope_max=2.0, width_min=5, width_max=20, zone_pct=15, rsi_max=35,
                    max_bars=15, ind=None):
    ind = ind or Ind(df, market)
    c, h, l, o = ind.c, ind.h, ind.l, ind.o
    hi, lo = _roll(_shift(h), int(range_days), "max"), _roll(_shift(l), int(range_days), "min")
    z = zone_pct / 100
    with np.errstate(invalid="ignore", divide="ignore"):
        height = hi - lo
        width = height / lo * 100
        s50 = ind.sma(50)
        flat = (ind.adx() < adx_max) & (np.abs(s50 / _shift(s50, 20) - 1) * 100 <= slope_max) & (width >= width_min) & (width <= width_max)
        bb_low = ind.boll(20, 2.0)[2]
        near = (l <= lo + z * height) & (l <= bb_low * 1.01)
        r = ind.rsi()
        turn = (_roll(r, 3, "min") <= rsi_max) & (r > _shift(r))
        candle = (c > o) & (c >= l + 0.6 * (h - l)) & (c > lo)
        entries = flat & near & turn & candle
        a = ind.atr()
        exits = r >= 65
    return _out(df, entries, exits, {"stop": np.where(entries, lo - 0.5 * a, np.nan), "target": np.where(entries, hi - z * height, np.nan),
                                     "target_r": None, "max_bars": int(max_bars)})


# ---------------------------------------------------------------- 5) opening range breakout (5-minute candles)
NY = "America/New_York"
OPEN_MIN = 9 * 60 + 30            # 9:30 New York
SESSION_BARS = 78                 # 9:30 .. 15:55
BASE_DAYS, BASE_MIN = 10, 5       # relative volume: the same minutes of the last 10 sessions (at least 5)
ORB_COLS = ["Day", "Side", "Signal", "Entry Time", "Entry", "Stop", "Target", "Exit Bar", "Exit Time", "Exit", "Reason", "Bars",
            "RVOL", "ORH", "ORL", "Open", "Pending"]


def session_close(day):
    """Minutes after midnight when the session closes (13:00 on the early-close days, else 16:00)."""
    return 13 * 60 if mcal.day_status(pd.Timestamp(day).date())[0] == "early" else 16 * 60


def last_entry_of(or_minutes, last_entry):
    """The last entry is at least 15 minutes after the opening range, so the settings can always trade."""
    return max(int(last_entry), int(or_minutes) + 15)


def ny_bars(df):
    """Regular-session 5-minute candles (9:30-16:00) with naive New York timestamps."""
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"], index=pd.DatetimeIndex([]), dtype=float)
    df = df.dropna(subset=["Open", "High", "Low", "Close"]).sort_index()
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_convert(NY).tz_localize(None)
    elif len(idx) and int((idx.hour * 60 + idx.minute).min()) >= 13 * 60:     # naive UTC stamps (no bar before 13:00)
        idx = idx.tz_localize("UTC").tz_convert(NY).tz_localize(None)
    df = df.set_axis(idx)
    df = df[~df.index.duplicated(keep="last")]
    m = df.index.hour * 60 + df.index.minute - OPEN_MIN
    df = df[(m >= 0) & (m < SESSION_BARS * 5)].copy()
    if "Volume" not in df:
        df["Volume"] = np.nan
    return df


def _prev_atr(daily, days):
    """Daily ATR 14 of the session before each day (NaN when there is not enough history)."""
    out = np.full(len(days), np.nan)
    if daily is None or len(daily) < 16:
        return out
    d = daily.dropna(subset=["High", "Low", "Close"]).sort_index()
    di = pd.DatetimeIndex(d.index)
    if di.tz is not None:
        di = di.tz_localize(None)
    d = d.set_axis(di.normalize())
    d = d[~d.index.duplicated(keep="last")]
    a = ta.atr(d).to_numpy(float)
    pos = d.index.searchsorted(pd.DatetimeIndex(days)) - 1           # the last daily candle before the session
    ok = pos >= 14
    out[ok] = a[pos[ok]]
    return out


def orb_trades(bars, daily, or_minutes=15, rvol_min=1.5, width_min=0.15, width_max=1.0, stop_frac=0.5, target_r=2.0, last_entry=120,
               shorts=1, now=None):
    """Every opening-range-breakout trade of one stock, one row per session at most (ORB_COLS), before any portfolio limits.
    bars: ny_bars() output. daily: daily candles (for the ATR). now: naive New York time; a session that has not closed yet
    keeps its trade open ('Open'), and a signal on its last candle waits for the next open ('Pending')."""
    now = pd.Timestamp(now) if now is not None else pd.Timestamp.now(tz=NY).tz_localize(None)
    if bars is not None and len(bars):
        bars = bars[bars.index + pd.Timedelta(minutes=5) <= now]          # a candle counts once it has closed
    if bars is None or len(bars) == 0:
        return pd.DataFrame(columns=ORB_COLS)
    last_entry = last_entry_of(or_minutes, last_entry)
    k_or, last_slot = int(or_minutes) // 5, (int(last_entry) - 5) // 5
    O, H, L, C = (bars[c].to_numpy(float) for c in ("Open", "High", "Low", "Close"))
    vol = np.nan_to_num(bars["Volume"].to_numpy(float))
    tp = (H + L + C) / 3
    stamp = bars.index
    slot = ((stamp.hour * 60 + stamp.minute - OPEN_MIN) // 5).to_numpy()
    day = stamp.normalize()
    days = day.unique()
    di = days.get_indexer(day)
    D = len(days)
    cum = np.zeros((D, SESSION_BARS))
    np.add.at(cum, (di, slot), vol)
    cum = cum.cumsum(axis=1)                                           # volume since the open, by 5-minute slot
    base = np.full((D, SESSION_BARS), np.nan)
    for d in range(BASE_MIN, D):
        base[d] = cum[max(0, d - BASE_DAYS):d].mean(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        rv = cum / np.where(base > 0, base, np.nan)
    atr_prev = _prev_atr(daily, days)
    starts = np.r_[0, np.flatnonzero(np.diff(di)) + 1]
    ends = np.r_[starts[1:], len(bars)]
    rows = []
    for d in range(D):
        s, e = int(starts[d]), int(ends[d])
        live = days[d] == now.normalize() and now < days[d] + pd.Timedelta(minutes=session_close(days[d]))
        if e - s <= k_or or not np.array_equal(slot[s:s + k_or], np.arange(k_or)):
            continue                                                   # the opening range is incomplete
        orh, orl = H[s:s + k_or].max(), L[s:s + k_or].min()
        w, a = orh - orl, atr_prev[d]
        if not (np.isfinite(a) and a > 0 and width_min * a <= w <= width_max * a):
            continue
        cv = np.cumsum(vol[s:e])
        with np.errstate(divide="ignore", invalid="ignore"):
            vw = np.cumsum(tp[s:e] * vol[s:e]) / np.where(cv > 0, cv, np.nan)
        sig = None
        for i in range(s + k_or, e):
            if slot[i] > last_slot:
                break
            r_ = rv[d, slot[i]]
            if not r_ >= rvol_min or not np.isfinite(vw[i - s]):
                continue
            if C[i] > orh and C[i] > vw[i - s]:
                sig = (i, 1, r_)
                break
            if shorts and C[i] < orl and C[i] < vw[i - s]:
                sig = (i, -1, r_)
                break
        if sig is None:
            continue
        i, side, r_ = sig
        row = {"Day": days[d], "Side": "Long" if side > 0 else "Short", "Signal": stamp[i], "RVOL": float(r_), "ORH": orh, "ORL": orl,
               "Open": False, "Pending": False}
        j = i + 1
        if j >= e:                                                     # no candle after the signal yet
            if live:
                rows.append({**row, "Pending": True})
            continue
        entry = O[j]
        stop = orh - stop_frac * w if side > 0 else orl + stop_frac * w
        if (entry - stop) * side <= 0:                                 # opened beyond the stop: no trade today
            continue
        target = entry + side * target_r * abs(entry - stop)
        ex = None
        for k in range(j, e):
            if side > 0:
                if L[k] <= stop:
                    ex = (k, min(O[k], stop), "Stop Loss")
                elif H[k] >= target:
                    ex = (k, max(O[k], target), "Take Profit")
            else:
                if H[k] >= stop:
                    ex = (k, max(O[k], stop), "Stop Loss")
                elif L[k] <= target:
                    ex = (k, min(O[k], target), "Take Profit")
            if ex:
                break
        row.update({"Entry Time": stamp[j], "Entry": entry, "Stop": stop, "Target": target})
        if ex:
            k, px, why = ex
            rows.append({**row, "Exit Bar": stamp[k], "Exit Time": stamp[k], "Exit": px, "Reason": why, "Bars": k - j + 1})
        elif live:                                                     # the session is still trading
            rows.append({**row, "Exit Bar": pd.Timestamp.max, "Exit Time": stamp[e - 1], "Exit": C[e - 1], "Reason": "Open",
                         "Bars": e - j, "Open": True})
        else:
            rows.append({**row, "Exit Bar": stamp[e - 1], "Exit Time": stamp[e - 1] + pd.Timedelta(minutes=5), "Exit": C[e - 1],
                         "Reason": "Close of Day", "Bars": e - j})
    return pd.DataFrame(rows, columns=ORB_COLS)


def with_vwap(bars):
    """A session's candles with its VWAP (for the day chart)."""
    b = bars.copy()
    tp = (b["High"] + b["Low"] + b["Close"]) / 3
    v = b["Volume"].fillna(0)
    day = b.index.normalize()
    b["VWAP"] = (tp * v).groupby(day).cumsum() / v.groupby(day).cumsum().replace(0, np.nan)
    return b


# ---------------------------------------------------------------- registry
# (key, label, min, max, default, step) - the same format as engine.STRATEGIES
PLAYBOOKS = {
    TREND_PULLBACK: (trend_pullback, [("trend_ma", "Long average (SMA)", 100, 300, 200, 1), ("mid_ma", "Medium average (SMA)", 20, 100, 50, 1),
                                      ("pull_ema", "Pullback average (EMA)", 10, 50, 20, 1), ("adx_min", "ADX at least", 10, 40, 20, 1),
                                      ("rsi_dip", "RSI dipped to", 30, 60, 50, 1), ("lookback", "Pullback window (bars)", 3, 10, 5, 1),
                                      ("target_r", "Target (x risk)", 1.0, 5.0, 2.0, 0.5), ("max_bars", "Time stop (bars)", 5, 60, 20, 1)]),
    BREAKOUT_RETEST: (breakout_retest, [("level_days", "Resistance (prior bars)", 10, 100, 20, 1), ("rvol_min", "Relative volume at least", 1.0, 5.0, 1.5, 0.1),
                                        ("break_pct", "Close above level (%)", 0.0, 2.0, 0.2, 0.1), ("window", "Retest within (bars)", 2, 15, 5, 1),
                                        ("tol_pct", "Retest distance (%)", 0.1, 2.0, 0.5, 0.1), ("max_break_pct", "Max dip under level (%)", 0.2, 3.0, 1.0, 0.1),
                                        ("target_r", "Target (x risk)", 1.0, 5.0, 2.0, 0.5), ("max_bars", "Time stop (bars)", 5, 60, 15, 1)]),
    SQUEEZE: (squeeze_breakout, [("bb_period", "Bollinger period", 10, 50, 20, 1), ("bb_std", "Bollinger std dev", 1.5, 3.0, 2.0, 0.1),
                                 ("rank_days", "Width history (bars)", 60, 252, 126, 1), ("squeeze_pct", "Width percentile at most", 5, 40, 20, 1),
                                 ("recent", "Squeeze within (bars)", 1, 20, 5, 1), ("rvol_min", "Relative volume at least", 1.0, 5.0, 1.5, 0.1),
                                 ("target_r", "Target (x risk)", 1.0, 6.0, 3.0, 0.5), ("max_bars", "Time stop (bars)", 5, 90, 30, 1)]),
    RANGE: (range_reversion, [("range_days", "Range (prior bars)", 20, 120, 40, 1), ("adx_max", "ADX below", 10, 30, 20, 1),
                              ("slope_max", "SMA 50 slope at most (%)", 0.5, 5.0, 2.0, 0.5), ("width_min", "Range height from (%)", 2, 15, 5, 1),
                              ("width_max", "Range height to (%)", 8, 40, 20, 1), ("zone_pct", "Edge zone (% of range)", 5, 30, 15, 1),
                              ("rsi_max", "RSI dipped to", 20, 45, 35, 1), ("max_bars", "Time stop (bars)", 3, 60, 15, 1)]),
    ORB: (None, [("or_minutes", "Opening range (minutes)", 15, 30, 15, 15), ("rvol_min", "Relative volume at least", 1.0, 5.0, 1.5, 0.1),
                 ("width_min", "Range at least (x ATR)", 0.05, 1.0, 0.15, 0.05), ("width_max", "Range at most (x ATR)", 0.5, 3.0, 1.0, 0.1),
                 ("stop_frac", "Stop (0.5 = middle, 1 = far side)", 0.25, 1.0, 0.5, 0.05), ("target_r", "Target (x risk)", 1.0, 5.0, 2.0, 0.5),
                 ("last_entry", "Last entry (minutes after the open)", 30, 240, 120, 15), ("shorts", "Short breakdowns (1 = yes)", 0, 1, 1, 1)]),
}
DAILY = [TREND_PULLBACK, BREAKOUT_RETEST, SQUEEZE, RANGE]
INTRADAY = {ORB}
AR = {TREND_PULLBACK: "التراجع مع الاتجاه", BREAKOUT_RETEST: "الاختراق وإعادة الاختبار", SQUEEZE: "انكماش التذبذب ثم الاختراق",
      RANGE: "الارتداد داخل النطاق", ORB: "اختراق نطاق الافتتاح"}
PARAM_AR = {"Long average (SMA)": "المتوسط الطويل (SMA)", "Medium average (SMA)": "المتوسط المتوسط (SMA)", "Pullback average (EMA)": "متوسط التراجع (EMA)",
            "ADX at least": "ADX على الأقل", "RSI dipped to": "نزل RSI إلى", "Pullback window (bars)": "نافذة التراجع (شموع)",
            "Target (x risk)": "الهدف (× المخاطرة)", "Time stop (bars)": "وقف زمني (شموع)", "Resistance (prior bars)": "المقاومة (شموع سابقة)",
            "Relative volume at least": "الحجم النسبي على الأقل", "Close above level (%)": "الإغلاق فوق المستوى (%)",
            "Retest within (bars)": "إعادة الاختبار خلال (شموع)", "Retest distance (%)": "مسافة إعادة الاختبار (%)",
            "Max dip under level (%)": "أقصى نزول تحت المستوى (%)", "Bollinger period": "فترة بولنجر", "Bollinger std dev": "انحراف بولنجر",
            "Width history (bars)": "تاريخ العرض (شموع)", "Width percentile at most": "مئين العرض بحد أقصى",
            "Squeeze within (bars)": "الانكماش خلال (شموع)", "Range (prior bars)": "النطاق (شموع سابقة)", "ADX below": "ADX أقل من",
            "SMA 50 slope at most (%)": "ميل متوسط 50 بحد أقصى (%)", "Range height from (%)": "ارتفاع النطاق من (%)",
            "Range height to (%)": "ارتفاع النطاق إلى (%)", "Edge zone (% of range)": "منطقة الحافة (% من النطاق)",
            "Opening range (minutes)": "نطاق الافتتاح (دقائق)", "Range at least (x ATR)": "النطاق على الأقل (× ATR)",
            "Range at most (x ATR)": "النطاق بحد أقصى (× ATR)", "Stop (0.5 = middle, 1 = far side)": "الوقف (0.5 = المنتصف، 1 = الطرف الآخر)",
            "Last entry (minutes after the open)": "آخر دخول (دقائق بعد الافتتاح)", "Short breakdowns (1 = yes)": "البيع على المكشوف عند الكسر (1 = نعم)"}
TIMEFRAME = {ORB: ("5-minute candles", "شموع 5 دقائق")}


def defaults(name):
    return {k: d for k, _, _, _, d, _ in PLAYBOOKS[name][1]}


def signals(name, df, params, market=None, ind=None):
    """(entries, exits, plan) of a daily playbook; ind: the stock's Ind, to share indicators between playbooks."""
    fn = PLAYBOOKS[name][0]
    return fn(df, market=market, ind=ind, **{**defaults(name), **(params or {})})


# ---------------------------------------------------------------- the rules, in words (numbers filled in from the settings)
def _i(x):
    """A formula kept left-to-right inside Arabic text."""
    return f"⁦{x}⁩"


def rules(name, params=None):
    """[(group_en, group_ar, [(rule_en, rule_ar), ...]), ...] for a playbook with its settings."""
    p = {**defaults(name), **(params or {})}
    f = lambda v: f"{v:g}"
    if name == TREND_PULLBACK:
        return [("Trend", "الاتجاه", [
                    (f"Close > SMA {f(p['trend_ma'])}, and SMA {f(p['mid_ma'])} > SMA {f(p['trend_ma'])}",
                     f"الإغلاق فوق {_i('SMA ' + f(p['trend_ma']))}، و{_i('SMA ' + f(p['mid_ma']))} فوق {_i('SMA ' + f(p['trend_ma']))}"),
                    (f"SMA {f(p['mid_ma'])} higher than 10 sessions ago", f"{_i('SMA ' + f(p['mid_ma']))} أعلى من قيمته قبل 10 جلسات"),
                    ("Last swing high > the one before it, and last swing low > the one before it (higher highs and higher lows)",
                     "آخر قمة أعلى من اللي قبلها، وآخر قاع أعلى من اللي قبله (قمم وقيعان صاعدة)"),
                    (f"ADX 14 >= {f(p['adx_min'])}", f"{_i('ADX 14 ≥ ' + f(p['adx_min']))}")]),
                ("Pullback", "التراجع", [
                    (f"In the last {f(p['lookback'])} bars a low reached EMA {f(p['pull_ema'])} + 0.25 ATR, or the previous swing high (old resistance) +/- 0.25 ATR",
                     f"خلال آخر {f(p['lookback'])} شموع لمس القاع {_i('EMA ' + f(p['pull_ema']) + ' + 0.25 ATR')} أو القمة السابقة (مقاومة صارت دعم) ± {_i('0.25 ATR')}"),
                    ("The drop into the pullback low (from the highest high of the 10 sessions up to it) is at least 1 ATR",
                     "النزول إلى قاع التراجع (من أعلى قمة في الـ 10 جلسات لين القاع) لا يقل عن 1 ATR"),
                    (f"The pullback low stays above SMA {f(p['mid_ma'])} - 0.5 ATR", f"قاع التراجع يبقى فوق {_i('SMA ' + f(p['mid_ma']) + ' - 0.5 ATR')}"),
                    (f"RSI 14 dipped to {f(p['rsi_dip'])} or lower in that window", f"نزل {_i('RSI 14')} إلى {f(p['rsi_dip'])} أو أقل خلال النافذة")]),
                ("Trigger (on the close)", "إشارة الاستئناف (عند الإغلاق)", [
                    (f"Close > yesterday's high, close > EMA {f(p['pull_ema'])} and SMA {f(p['mid_ma'])}, a green candle, and RSI rising",
                     f"الإغلاق فوق قمة أمس، وفوق {_i('EMA ' + f(p['pull_ema']))} و{_i('SMA ' + f(p['mid_ma']))}، وشمعة خضراء، و{_i('RSI')} صاعد")]),
                ("Trade", "الصفقة", [
                    ("Buy at the next open (no trade if it opens at or under the stop)",
                     "شراء عند الافتتاح التالي (ما فيه صفقة إذا افتتح عند الوقف أو تحته)"),
                    ("Stop: pullback low - 0.25 ATR (never more than 3 ATR below the signal close)",
                     "الوقف: قاع التراجع ناقص 0.25 ATR (وبحد أقصى 3 ATR تحت إغلاق الإشارة)"),
                    (f"Target: entry + {f(p['target_r'])} x risk", f"الهدف: الدخول + {f(p['target_r'])} × المخاطرة"),
                    (f"Exit early: a close under SMA {f(p['mid_ma'])}, or after {f(p['max_bars'])} sessions",
                     f"خروج مبكر: إغلاق تحت {_i('SMA ' + f(p['mid_ma']))}، أو بعد {f(p['max_bars'])} جلسة")])]
    if name == BREAKOUT_RETEST:
        return [("Breakout", "الاختراق", [
                    (f"Level = highest high of the {f(p['level_days'])} bars before", f"المستوى = أعلى قمة في آخر {f(p['level_days'])} شمعة قبلها"),
                    (f"Close >= level x (1 + {f(p['break_pct'])}%)", f"الإغلاق ≥ المستوى × {_i('(1 + ' + f(p['break_pct']) + '%)')}"),
                    (f"Relative volume (vs the 20 sessions before) >= {f(p['rvol_min'])}", f"الحجم النسبي (مقابل آخر 20 جلسة) ≥ {f(p['rvol_min'])}")]),
                ("Retest", "إعادة الاختبار", [
                    (f"Within {f(p['window'])} bars the low comes back to the level: low <= level x (1 + {f(p['tol_pct'])}%)",
                     f"خلال {f(p['window'])} شموع يرجع القاع للمستوى: القاع ≤ المستوى × {_i('(1 + ' + f(p['tol_pct']) + '%)')}"),
                    (f"It holds: low >= level x (1 - {f(p['max_break_pct'])}%), close >= level, close in the upper half of the candle",
                     f"ويصمد: القاع ≥ المستوى × {_i('(1 - ' + f(p['max_break_pct']) + '%)')}، والإغلاق ≥ المستوى وفي النصف العلوي من الشمعة"),
                    (f"Cancelled if a close falls under level x (1 - {f(p['max_break_pct'])}%) or the window passes",
                     f"يُلغى إذا أغلق تحت المستوى × {_i('(1 - ' + f(p['max_break_pct']) + '%)')} أو انتهت النافذة")]),
                ("Trade", "الصفقة", [
                    ("Buy at the next open after the retest bar (no trade if it opens at or under the stop)",
                     "شراء عند الافتتاح التالي لشمعة إعادة الاختبار (ما فيه صفقة إذا افتتح عند الوقف أو تحته)"),
                    ("Stop: lower of (retest low, level) - 0.25 ATR", "الوقف: الأقل بين (قاع إعادة الاختبار، المستوى) ناقص 0.25 ATR"),
                    (f"Target: entry + {f(p['target_r'])} x risk", f"الهدف: الدخول + {f(p['target_r'])} × المخاطرة"),
                    (f"Exit early: a close under level x (1 - {f(p['max_break_pct'])}%), or after {f(p['max_bars'])} sessions",
                     f"خروج مبكر: إغلاق تحت المستوى × {_i('(1 - ' + f(p['max_break_pct']) + '%)')}، أو بعد {f(p['max_bars'])} جلسة")])]
    if name == SQUEEZE:
        return [("Squeeze", "الانكماش", [
                    (f"Band width = (upper - lower) / middle of Bollinger {f(p['bb_period'])} / {f(p['bb_std'])}",
                     f"عرض النطاق = {_i('(upper - lower) / middle')} لبولنجر {_i(f(p['bb_period']) + ' / ' + f(p['bb_std']))}"),
                    (f"In the {f(p['recent'])} bars before the breakout the width was at or under its {f(p['squeeze_pct'])}th percentile of the last {f(p['rank_days'])} bars",
                     f"خلال الـ {f(p['recent'])} شموع اللي قبل الاختراق كان العرض عند أو تحت المئين {f(p['squeeze_pct'])} لآخر {f(p['rank_days'])} شمعة")]),
                ("Breakout", "الاختراق", [
                    ("First close above the upper band", "أول إغلاق فوق النطاق العلوي"),
                    (f"Relative volume >= {f(p['rvol_min'])}", f"الحجم النسبي ≥ {f(p['rvol_min'])}"),
                    ("Market: SPY close > SPY SMA 200, and the stock's close > its SMA 50",
                     f"السوق: إغلاق {_i('SPY')} فوق {_i('SMA 200')} له، وإغلاق السهم فوق {_i('SMA 50')}")]),
                ("Trade", "الصفقة", [
                    ("Buy at the next open (no trade if it opens at or under the stop)",
                     "شراء عند الافتتاح التالي (ما فيه صفقة إذا افتتح عند الوقف أو تحته)"),
                    ("Stop: the middle band, and at least 1 ATR under the signal close", "الوقف: الخط الأوسط، وعلى الأقل 1 ATR تحت إغلاق الإشارة"),
                    (f"Target: entry + {f(p['target_r'])} x risk", f"الهدف: الدخول + {f(p['target_r'])} × المخاطرة"),
                    (f"Exit early: a close under the middle band, or after {f(p['max_bars'])} sessions",
                     f"خروج مبكر: إغلاق تحت الخط الأوسط، أو بعد {f(p['max_bars'])} جلسة")])]
    if name == RANGE:
        return [("Sideways market", "سوق عرضي", [
                    (f"Range = highest high and lowest low of the {f(p['range_days'])} bars before; height between {f(p['width_min'])}% and {f(p['width_max'])}% of the low",
                     f"النطاق = أعلى قمة وأدنى قاع في آخر {f(p['range_days'])} شمعة قبلها؛ ارتفاعه بين {f(p['width_min'])}% و{f(p['width_max'])}% من القاع"),
                    (f"ADX 14 < {f(p['adx_max'])}, and SMA 50 moved less than {f(p['slope_max'])}% in 20 sessions",
                     f"{_i('ADX 14 < ' + f(p['adx_max']))}، و{_i('SMA 50')} تحرك أقل من {f(p['slope_max'])}% خلال 20 جلسة")]),
                ("At the bottom edge", "عند الحافة السفلية", [
                    (f"Low within the bottom {f(p['zone_pct'])}% of the range, and low <= lower Bollinger band x 1.01",
                     f"القاع داخل أسفل {f(p['zone_pct'])}% من النطاق، والقاع ≤ نطاق بولنجر السفلي × 1.01"),
                    (f"RSI 14 was {f(p['rsi_max'])} or lower in the last 3 bars and is now rising",
                     f"{_i('RSI 14')} كان {f(p['rsi_max'])} أو أقل خلال آخر 3 شموع والحين صاعد"),
                    ("A green candle closing in the top 40% of its range, above the range low",
                     "شمعة خضراء تغلق في أعلى 40% من مداها، وفوق قاع النطاق")]),
                ("Trade", "الصفقة", [
                    ("Buy at the next open (no trade if it opens at or under the stop, or at or over the target)",
                     "شراء عند الافتتاح التالي (ما فيه صفقة إذا افتتح عند الوقف أو تحته، أو عند الهدف أو فوقه)"),
                    ("Stop: range low - 0.5 ATR", "الوقف: قاع النطاق ناقص 0.5 ATR"),
                    (f"Target: the top {f(p['zone_pct'])}% zone (range high - {f(p['zone_pct'])}% of the height)",
                     f"الهدف: منطقة أعلى {f(p['zone_pct'])}% (قمة النطاق ناقص {f(p['zone_pct'])}% من الارتفاع)"),
                    (f"Exit early: RSI reaches 65, or after {f(p['max_bars'])} sessions", f"خروج مبكر: وصول {_i('RSI')} إلى 65، أو بعد {f(p['max_bars'])} جلسة")])]
    if name == ORB:
        m = int(p["or_minutes"])
        end = f"9:{30 + m:02d}" if m < 30 else "10:00"
        last = 9 * 60 + 30 + last_entry_of(m, p["last_entry"])
        last_txt = f"{last // 60}:{last % 60:02d}"
        return [("Opening range", "نطاق الافتتاح", [
                    (f"High and low of the first {m} minutes (9:30 to {end} New York, 5-minute candles)",
                     f"أعلى وأدنى سعر في أول {m} دقيقة ({_i('9:30')} إلى {_i(end)} بتوقيت نيويورك، شموع 5 دقائق)"),
                    (f"Range height between {f(p['width_min'])} and {f(p['width_max'])} x the daily ATR 14",
                     f"ارتفاع النطاق بين {f(p['width_min'])} و{f(p['width_max'])} × {_i('ATR 14')} اليومي")]),
                ("Breakout (on a 5-minute close)", "الاختراق (عند إغلاق شمعة 5 دقائق)", [
                    ("Long: close above the range high and above the session VWAP", "شراء: إغلاق فوق قمة النطاق وفوق VWAP الجلسة"),
                    ("Short: close below the range low and below VWAP" if p["shorts"] else "Shorts are off",
                     "بيع مكشوف: إغلاق تحت قاع النطاق وتحت VWAP" if p["shorts"] else "البيع المكشوف مقفل"),
                    (f"Relative volume >= {f(p['rvol_min'])}: volume since the open against the average of the same minutes over the last 10 sessions (at least 5)",
                     f"الحجم النسبي ≥ {f(p['rvol_min'])}: حجم الجلسة من الافتتاح مقابل متوسط نفس الدقائق في آخر 10 جلسات (5 على الأقل)"),
                    (f"One trade per stock per day: the first 5-minute close that meets all of these, entered by {last_txt} at the latest",
                     f"صفقة وحدة لكل سهم في اليوم: أول إغلاق 5 دقائق يحقق كل هذي الشروط، والدخول بحد أقصى {_i(last_txt)}")]),
                ("Trade", "الصفقة", [
                    ("Enter at the next 5-minute candle's open (if it opens beyond the stop, no trade that day)",
                     "الدخول عند افتتاح شمعة الـ 5 دقائق التالية (إذا افتتحت بعد الوقف، ما فيه صفقة ذاك اليوم)"),
                    (f"Stop: {f(p['stop_frac'])} of the range back from the broken side (0.5 = the middle)",
                     f"الوقف: {f(p['stop_frac'])} من النطاق رجوعاً من الطرف المكسور (0.5 = المنتصف)"),
                    (f"Target: entry +/- {f(p['target_r'])} x risk", f"الهدف: الدخول ± {f(p['target_r'])} × المخاطرة"),
                    ("Everything is closed at the day's last candle (no overnight positions; 13:00 on early-close days)",
                     "كل الصفقات تتقفل مع آخر شمعة في اليوم (ما تبات مفتوحة؛ والإغلاق 13:00 في أيام الإغلاق المبكر)")])]
    return []

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.9"
