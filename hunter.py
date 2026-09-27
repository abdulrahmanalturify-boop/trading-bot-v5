"""
hunter.py - the Opportunity Hunter's engine (the Scanner page, p_scanner.py).

For every stock of a universe (daily candles, about two years):
  * SETUPS: exact, numeric patterns. Each one is a vector rule on the whole history (a signal on a bar's close, a stop and
    a target fixed on that bar, a time limit), so the same rule that finds today's opportunity can be backtested on the
    stock's own past (backtest()). The four daily combined strategies of the Paper Bots (playbooks.py) are setups too.
      events  : fire on one bar; an opportunity while it is at most 2 bars old (3 for the playbooks) and the price is still
                between its stop and its target,
      states  : hold for many bars (a leader near its 52-week high); an opportunity while they hold,
      watch   : a squeeze that is building and hasn't broken out yet (a trigger level to watch).
  * a SCORE from 0 to 100 and a grade (A+ .. D): trend 25%, relative strength 25% (RS rating 1-99 against the whole
    universe, or against SPY for small lists), accumulation 15% (volume on up days vs down days, relative volume), the
    setup 20% (fresh / active / watch) and risk 15% (reward-to-risk to the target, not stretched far above its averages);
    earnings within 5 days and thin trading cost points and are flagged,
  * the MARKET REGIME (SPY's trend, the share of stocks above their 50 / 200-day averages, new highs vs new lows, VIX)
    and the sectors ranked by strength.
All numbers are computed on the daily close; nothing looks ahead: a signal on a bar only uses that bar and the ones before.
"""
import numpy as np
import pandas as pd

import playbooks as PB
import ta
import universe as U

# key -> (en, ar, icon, kind, side, max_bars, what it is en, ar)
SETUPS = {
    "pullback": (PB.TREND_PULLBACK, PB.AR[PB.TREND_PULLBACK], "trending_up", "event", 1, None,
                 "An uptrend pulled back to its 20-day EMA or old resistance, and turned up again today.",
                 "اتجاه صاعد تراجع لمتوسط 20 الأسي أو لمقاومة قديمة، ورجع يصعد."),
    "retest": (PB.BREAKOUT_RETEST, PB.AR[PB.BREAKOUT_RETEST], "north_east", "event", 1, None,
               "Broke out over resistance on volume, came back to test it and held.",
               "اخترق المقاومة بحجم، ورجع يختبرها وثبت فوقها."),
    "squeeze": (PB.SQUEEZE, PB.AR[PB.SQUEEZE], "compress", "event", 1, None,
                "Volatility shrank to its lowest levels, then the price broke out of the bands with volume.",
                "التذبذب انكمش لأقل مستوياته، بعدها اخترق السعر النطاق بحجم."),
    "range": (PB.RANGE, PB.AR[PB.RANGE], "swap_vert", "event", 1, None,
              "A flat range: the price dipped to its floor with RSI low and turned up.",
              "نطاق عرضي: نزل السعر لأرضيته مع RSI منخفض ورجع يصعد."),
    "breakout": ("20-day breakout on volume", "اختراق قمة 20 يوم بحجم", "rocket_launch", "event", 1, 20,
                 "Closed above its 20-day high for the first time, with volume at least 1.5x its 50-day average, above its 50-day average.",
                 "أغلق فوق قمة 20 يوم لأول مرة، بحجم 1.5 ضعف متوسط 50 يوم على الأقل، وفوق متوسط 50."),
    "leader": ("Leader near its 52-week high", "قائد قرب قمته السنوية", "emoji_events", "state", 1, 30,
               "In an uptrend (above its 50 and 200-day averages) and within 3% of its 52-week high.",
               "في اتجاه صاعد (فوق متوسط 50 و200) وعلى بعد 3% أو أقل من قمته السنوية."),
    "golden": ("Golden cross 50/200", "التقاطع الذهبي 50/200", "auto_awesome", "event", 1, 40,
               "The 50-day average crossed above the 200-day average.", "متوسط 50 يوم قطع فوق متوسط 200 يوم."),
    "dip": ("Oversold dip in an uptrend", "تشبع بيعي داخل اتجاه صاعد", "water_drop", "event", 1, 7,
            "A short, sharp dip (RSI 2 under 10) while the stock stays above its 200-day average: a quick bounce setup.",
            "نزول سريع وحاد (RSI 2 تحت 10) والسهم فوق متوسط 200: فرصة ارتداد قصيرة."),
    "volume": ("Accumulation day", "يوم تجميع", "equalizer", "event", 1, 20,
               "Volume at least 2.5x its 50-day average on a green day that closed near its high, above its 50-day average.",
               "حجم 2.5 ضعف متوسط 50 يوم على الأقل في يوم أخضر أغلق قرب قمته، وفوق متوسط 50."),
    "gap": ("Gap and go", "فجوة صاعدة ثابتة", "bolt", "event", 1, 15,
            "Opened at least 3% above yesterday's close and held it (closed at or above the open) on 1.5x volume.",
            "افتتح أعلى من إغلاق أمس بـ 3% أو أكثر وحافظ عليها (أغلق عند الافتتاح أو فوقه) بحجم 1.5 ضعف."),
    "coil": ("Squeeze building", "انضغاط يتكوّن", "hourglass_top", "watch", 1, None,
             "Its Bollinger bands are the narrowest of the last 6 months and it is above its 50-day average: watch for a break over the trigger.",
             "نطاق بولنجر في أضيق مستوى له خلال 6 أشهر والسهم فوق متوسط 50: راقب الاختراق فوق مستوى الإشارة."),
    "breakdown": ("Breakdown (bearish)", "كسر هابط (سلبي)", "trending_down", "event", -1, 20,
                  "Closed under its 20-day low for the first time, below a falling 200-day average: avoid, or a short setup.",
                  "أغلق تحت قاع 20 يوم لأول مرة، تحت متوسط 200 الهابط: تجنّب، أو فرصة بيع على المكشوف."),
}
PLAYBOOK_OF = {"pullback": PB.TREND_PULLBACK, "retest": PB.BREAKOUT_RETEST, "squeeze": PB.SQUEEZE, "range": PB.RANGE}
ORDER = ["pullback", "retest", "squeeze", "breakout", "range", "volume", "gap", "golden", "leader", "dip", "coil", "breakdown"]
STATUS = {"fresh": ("New today", "جديدة اليوم", "up"), "active": ("Active", "نشطة", "acc"), "watch": ("Watch", "مراقبة", "gold")}
GRADES = [(85, "A+"), (75, "A"), (65, "B"), (50, "C"), (0, "D")]
WEIGHTS = {"trend": 0.25, "rs": 0.25, "volume": 0.15, "setup": 0.20, "risk": 0.15}
PARTS = {"trend": ("Trend", "الاتجاه"), "rs": ("Relative strength", "القوة النسبية"), "volume": ("Accumulation", "التجميع"),
         "setup": ("Setup", "الفرصة"), "risk": ("Reward / risk", "العائد / المخاطرة")}
MIN_BARS = 130


def grade(score):
    return next(g for lo, g in GRADES if score >= lo)


def _clean(df):
    if df is None or df.empty or not {"Open", "High", "Low", "Close"}.issubset(df.columns):
        return None
    df = df.dropna(subset=["Open", "High", "Low", "Close"]).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    if "Volume" not in df:
        df = df.assign(Volume=np.nan)
    return df if len(df) >= MIN_BARS else None


def indicators(df):
    """The indicators the hunter reads (the same formulas as ta.add_all, only the ones it needs, built in one go)."""
    c = df["Close"]
    adx, dip, dim = ta.adx(df)
    mid, up, low, width = ta.bollinger(c)
    cols = {"SMA20": ta.sma(c, 20), "SMA50": ta.sma(c, 50), "SMA200": ta.sma(c, 200), "RSI": ta.rsi(c), "ATR": ta.atr(df),
            "ADX": adx, "DI_plus": dip, "DI_minus": dim, "BB_mid": mid, "BB_up": up, "BB_low": low, "BB_width": width}
    return pd.concat([df, pd.DataFrame(cols, index=df.index)], axis=1)


# ---------------------------------------------------------------- the setups as vector rules
def _series(d, market=None, ind=None):
    """{key: (signal bool array, stop array, target array, max_bars)} for every setup except the 'watch' one. Stops and
    targets are fixed on the signal bar."""
    c, h, lo, o = (d[k].to_numpy(float) for k in ("Close", "High", "Low", "Open"))
    v = d["Volume"].to_numpy(float)
    a = d["ATR"].to_numpy(float)
    s20, s50, s200 = (d[k].to_numpy(float) for k in ("SMA20", "SMA50", "SMA200"))
    prev = lambda x, k=1: np.r_[np.full(k, np.nan), x[:-k]]
    vavg50 = prev(pd.Series(v).rolling(50, min_periods=30).mean().to_numpy())
    with np.errstate(invalid="ignore", divide="ignore"):
        out = {}
        # the four combined strategies of the Paper Bots, with their own stops, targets and time stops
        ind = ind or PB.Ind(d[["Open", "High", "Low", "Close", "Volume"]], market)
        for key, name in PLAYBOOK_OF.items():
            e, _, plan = PB.signals(name, d[["Open", "High", "Low", "Close", "Volume"]], {}, market=market, ind=ind)
            sig = e.fillna(False).to_numpy(bool)
            stop = plan["stop"].to_numpy(float)
            if plan["target"] is not None:
                tgt = plan["target"].to_numpy(float)
            else:
                tgt = c + float(plan["target_r"] or 2.0) * (c - stop)
            out[key] = (sig, stop, tgt, int(plan["max_bars"] or 20))
        lvl = prev(pd.Series(h).rolling(20).max().to_numpy())
        brk = (c > lvl) & (v >= 1.5 * vavg50) & (c > s50)
        brk &= ~np.r_[False, (c[:-1] > lvl[:-1])]                         # the first close above it
        stop = np.fmin(lo, lvl) - 0.5 * a
        out["breakout"] = (brk, stop, c + 2.5 * (c - stop), 20)
        hi252 = pd.Series(h).rolling(252, min_periods=120).max().to_numpy()
        lead = (c > s50) & (s50 > s200) & (c >= 0.97 * hi252) & (c > s20)
        stop = np.fmax(s50 - 0.25 * a, c - 3 * a)
        out["leader"] = (lead & ~np.r_[False, lead[:-1]], stop, c + 2.5 * (c - stop), 30)
        out["_leader_state"] = lead
        gold = (s50 > s200) & np.r_[False, s50[:-1] <= s200[:-1]]
        stop = c - 2 * a
        out["golden"] = (gold, stop, c + 3 * (c - stop), 40)
        r2 = ta.rsi(d["Close"], 2).to_numpy(float)
        dip = (r2 < 10) & (c > s200) & (s50 > s200)
        out["dip"] = (dip, c - 1.5 * a, c + 1.5 * a, 7)
        rng = h - lo
        acc = (v >= 2.5 * vavg50) & (c > o) & (c - lo >= 0.7 * rng) & (c > s50)
        stop = lo - 0.25 * a
        out["volume"] = (acc, stop, c + 2.5 * (c - stop), 20)
        pc = prev(c)
        gap = (o / pc - 1 >= 0.03) & (c >= o) & (v >= 1.5 * vavg50)
        stop = pc - 0.25 * a
        out["gap"] = (gap, stop, c + 2 * (c - stop), 15)
        low20 = prev(pd.Series(lo).rolling(20).min().to_numpy())
        s200_up = s200 > prev(s200, 20)
        bd = (c < low20) & (c < s200) & (s50 < s200) & ~s200_up
        bd &= ~np.r_[False, (c[:-1] < low20[:-1])]
        stop = np.fmax(h, low20) + 0.5 * a
        out["breakdown"] = (bd, stop, c - 2 * (stop - c), 20)
    for k in list(out):
        if not k.startswith("_"):
            s_, st_, tg_, mb = out[k]
            out[k] = (np.nan_to_num(np.asarray(s_, bool), nan=False), np.asarray(st_, float), np.asarray(tg_, float), mb)
    return out


def backtest(d, key, series=None, market=None):
    """The setup's past trades on this stock: enter at the next open (no trade if it opens beyond the stop or the target),
    exit on the stop or the target during the day (the stop first when a candle touches both), or at the close of the last
    allowed bar. One trade at a time. Returns a DataFrame (Signal, Entry Date, Entry, Stop, Target, Exit Date, Exit, R, Ret %,
    Bars, Reason)."""
    series = series or _series(d, market)
    if key not in series:
        return pd.DataFrame()
    sig, stop, tgt, mb = series[key]
    side = SETUPS[key][4]
    o, h, lo, c = (d[k].to_numpy(float) for k in ("Open", "High", "Low", "Close"))
    idx = d.index
    n, i, rows = len(c), 0, []
    hits = np.flatnonzero(sig)
    for j in hits:
        if j < i or j + 1 >= n:
            continue
        s_, t_ = stop[j], tgt[j]
        e = o[j + 1]
        if not (np.isfinite(s_) and np.isfinite(t_) and np.isfinite(e)):
            continue
        if side > 0 and not (s_ < e < t_) or side < 0 and not (t_ < e < s_):
            continue
        risk = abs(e - s_)
        ex, why, k = None, None, j + 1
        last = min(n - 1, j + mb)
        for k in range(j + 1, last + 1):
            if side > 0:
                if lo[k] <= s_:
                    ex, why = (s_ if k == j + 1 else min(o[k], s_)), "Stop"
                elif h[k] >= t_:
                    ex, why = (t_ if k == j + 1 else max(o[k], t_)), "Target"
            else:
                if h[k] >= s_:
                    ex, why = (s_ if k == j + 1 else max(o[k], s_)), "Stop"
                elif lo[k] <= t_:
                    ex, why = (t_ if k == j + 1 else min(o[k], t_)), "Target"
            if ex is not None:
                break
        if ex is None:
            if j + mb > n - 1:                                  # still open at the end of the data: not counted
                break
            ex, why, k = c[last], "Time", last
        r = (ex - e) / risk * side
        rows.append({"Signal": idx[j], "Entry Date": idx[j + 1], "Entry": e, "Stop": s_, "Target": t_, "Exit Date": idx[k], "Exit": ex,
                     "R": r, "Ret %": (ex / e - 1) * 100 * side, "Bars": k - j, "Reason": why})
        i = k + 1
    return pd.DataFrame(rows)


def edge(trades):
    """Win rate, average R, profit factor and number of trades of a backtest (None when it has no trades)."""
    if trades is None or trades.empty:
        return None
    r = trades["R"].to_numpy(float)
    wins, losses = r[r > 0].sum(), -r[r < 0].sum()
    return {"n": len(r), "win": float((r > 0).mean() * 100), "avg_r": float(r.mean()), "avg_ret": float(trades["Ret %"].mean()),
            "pf": float(wins / losses) if losses > 0 else (np.inf if wins > 0 else 0.0), "total_r": float(r.sum())}


# ---------------------------------------------------------------- one stock
def analyze(df, market=None):
    """Everything the hunter needs about one stock (df: daily OHLCV). None when there isn't enough history."""
    df = _clean(df)
    if df is None:
        return None
    d = indicators(df)
    c, h, lo, v = (d[k].to_numpy(float) for k in ("Close", "High", "Low", "Volume"))
    n = len(c)
    i = n - 1
    last = d.iloc[-1]
    price, a = float(c[i]), float(last["ATR"])
    if not (np.isfinite(price) and price > 0 and np.isfinite(a) and a > 0):
        return None
    s20, s50, s200 = float(last["SMA20"]), float(last["SMA50"]), float(last["SMA200"])
    has200 = np.isfinite(s200)
    ret = lambda k: float(c[i] / c[i - k] - 1) * 100 if n > k and c[i - k] > 0 else np.nan
    r1, r3, r6, r9, r12 = ret(21), ret(63), ret(126), ret(189), ret(252 if n > 252 else n - 1)
    parts = [(0.4, r3), (0.2, r6), (0.2, r9), (0.2, r12)]
    wsum = sum(w for w, x in parts if np.isfinite(x))
    rs_raw = sum(w * x for w, x in parts if np.isfinite(x)) / wsum if wsum else np.nan
    hi52, lo52 = float(np.nanmax(h[-252:])), float(np.nanmin(lo[-252:]))
    vol50 = float(np.nanmean(v[-51:-1])) if n > 51 else np.nan
    rvol = float(v[i] / vol50) if vol50 and np.isfinite(vol50) and vol50 > 0 else np.nan
    dollar = float(np.nanmean((c * v)[-20:]))
    up = np.r_[False, c[1:] > c[:-1]][-50:]
    dn = np.r_[False, c[1:] < c[:-1]][-50:]
    vv = v[-50:]
    ud = float(np.nansum(vv[up]) / np.nansum(vv[dn])) if np.nansum(vv[dn]) > 0 else 2.0
    s200_prev = float(d["SMA200"].iloc[-21]) if n > 21 else np.nan
    adx, dip_, dim_ = float(last["ADX"]), float(last["DI_plus"]), float(last["DI_minus"])
    bw = d["BB_width"].tail(126).dropna()
    bw_pct = float((bw <= bw.iloc[-1]).mean()) if len(bw) > 60 else np.nan
    ext = (price - s20) / a if np.isfinite(s20) else 0.0

    # ---- setups found now
    try:
        series = _series(d, market)
    except Exception:
        series = {}
    found = []
    for key in ORDER:
        en, ar, icon, kind, side, _, _, _ = SETUPS[key]
        if kind == "watch":
            if np.isfinite(bw_pct) and bw_pct <= 0.10 and price > s50 and not (has200 and s50 < s200):
                trig = max(float(last["BB_up"]), float(d["High"].iloc[-21:-1].max()))
                stop = min(float(last["BB_low"]), trig - 1.5 * a)
                if trig > price and stop < price:
                    found.append({"key": key, "status": "watch", "age": None, "entry": trig * 1.001, "stop": stop,
                                  "target": trig * 1.001 + 2.5 * (trig * 1.001 - stop), "side": side})
            continue
        if key not in series:
            continue
        sig, stop, tgt, _ = series[key]
        window = 3 if key in PLAYBOOK_OF else 2
        if kind == "state":
            if not series["_leader_state"][i]:
                continue
            j = i - int(np.argmax(~series["_leader_state"][::-1])) + 1 if not series["_leader_state"].all() else 0
            age = i - j
            st_, tg_ = float(stop[i]), float(tgt[i])               # a state keeps today's levels
        else:
            hits = np.flatnonzero(sig[max(0, i - window):]) + max(0, i - window)
            if not len(hits):
                continue
            j = int(hits[-1])
            age = i - j
            st_, tg_ = float(stop[j]), float(tgt[j])
        if not (np.isfinite(st_) and np.isfinite(tg_)):
            continue
        if side > 0 and not (st_ < price < tg_) or side < 0 and not (tg_ < price < st_):
            continue                                          # already stopped out or at its target
        found.append({"key": key, "status": "fresh" if age == 0 else "active", "age": age, "entry": price, "stop": st_, "target": tg_,
                      "side": side})

    rank = {"fresh": 0, "active": 1, "watch": 2}
    longs = sorted((f for f in found if f["side"] > 0), key=lambda f: (rank[f["status"]], SETUPS[f["key"]][3] == "state", ORDER.index(f["key"])))
    best = longs[0] if longs else (found[0] if found else None)

    # ---- the parts of the score (0-100 each; relative strength is filled in by hunt())
    tr_pts = 0.0
    tr_pts += 20 if has200 and price > s200 else 0
    tr_pts += 20 if has200 and s50 > s200 else 0
    tr_pts += 20 if price > s50 else 0
    tr_pts += 15 if has200 and np.isfinite(s200_prev) and s200 > s200_prev else 0
    tr_pts += 10 if price > s20 else 0
    tr_pts += 15 if np.isfinite(adx) and adx >= 20 and dip_ > dim_ else 0
    vol_pts = float(np.clip((ud - 0.6) / 1.0 * 100, 0, 100)) * 0.8
    if np.isfinite(rvol) and c[i] >= c[i - 1]:
        vol_pts += float(np.clip((rvol - 1) * 20, 0, 20))
    setup_pts = 0.0
    rr = np.nan
    if best is not None and best["side"] > 0:
        setup_pts = {"fresh": 100.0, "active": 78.0, "watch": 55.0}[best["status"]]
        if SETUPS[best["key"]][3] == "state" and best["status"] == "active":
            setup_pts = 68.0                                 # a leader in play, but no fresh trigger
        if best["key"] in PLAYBOOK_OF and best["status"] != "watch":
            setup_pts = min(100.0, setup_pts + 8)
        risk_ = best["entry"] - best["stop"]
        rr = (best["target"] - best["entry"]) / risk_ if risk_ > 0 else np.nan
    risk_pts = 0.0
    if np.isfinite(rr):
        risk_pts = float(np.interp(rr, [0.8, 1.5, 2.0, 3.0], [15, 50, 75, 100]))
        if best and (best["entry"] - best["stop"]) / a > 3.5:
            risk_pts -= 20
    if ext > 3:
        risk_pts -= 30
    risk_pts = float(np.clip(risk_pts, 0, 100))

    return {"price": price, "chg": float((c[i] / c[i - 1] - 1) * 100), "r1": r1, "r3": r3, "r6": r6, "r12": r12, "rs_raw": rs_raw,
            "hi52": hi52, "lo52": lo52, "dist_hi": (price / hi52 - 1) * 100, "rvol": rvol, "dollar": dollar, "ud": ud,
            "rsi": float(last["RSI"]), "adx": adx, "atr": a, "atr_pct": a / price * 100, "ext": ext, "bw_pct": bw_pct,
            "above50": bool(price > s50), "above200": bool(has200 and price > s200), "new_high": bool(h[i] >= hi52 * 0.999),
            "new_low": bool(lo[i] <= lo52 * 1.001), "sma20": s20, "sma50": s50, "sma200": s200,
            "setups": found, "best": best, "rr": rr, "p_trend": tr_pts, "p_volume": min(vol_pts, 100.0), "p_setup": setup_pts,
            "p_risk": risk_pts, "spark": [float(x) for x in c[-66:]]}


# ---------------------------------------------------------------- a whole universe
def _rs_from_spy(rs_raw, spy_raw):
    """A 1-99 strength rating from the lead over SPY, for lists too small to rank against each other."""
    if not (np.isfinite(rs_raw) and np.isfinite(spy_raw)):
        return 50.0
    return float(np.clip(50 + 49 * np.tanh((rs_raw - spy_raw) / 25), 1, 99))


def spy_strength(spy):
    df = _clean(spy)
    if df is None:
        return np.nan
    c = df["Close"].to_numpy(float)
    i = len(c) - 1
    parts = [(0.4, 63), (0.2, 126), (0.2, 189), (0.2, min(252, i))]
    vals = [(w, (c[i] / c[i - k] - 1) * 100) for w, k in parts if i >= k > 0]
    return sum(w * x for w, x in vals) / sum(w for w, _ in vals) if vals else np.nan


def hunt(data_by_symbol, market=None, earnings=None, today=None, names=None, sectors=None):
    """Every stock analysed and scored. earnings: {symbol: date} of upcoming reports; today: a date.
    Returns a DataFrame (one row per stock, best first) and a dict of the per-stock details (setups, sparkline)."""
    rows, detail = [], {}
    for sym, df in data_by_symbol.items():
        if sym in ("SPY", "^VIX"):
            continue
        try:
            r = analyze(df, market)
        except Exception:
            r = None
        if r:
            rows.append((sym, r))
    if not rows:
        return pd.DataFrame(), {}
    raw = np.array([r["rs_raw"] for _, r in rows], float)
    spy_raw = spy_strength(market) if market is not None else np.nan
    if len(rows) >= 60 and np.isfinite(raw).sum() >= 30:
        order = pd.Series(raw).rank(pct=True).to_numpy()
        rs = np.where(np.isfinite(raw), np.clip(np.round(order * 98 + 1), 1, 99), 50.0)
    else:
        rs = np.array([_rs_from_spy(x, spy_raw) for x in raw])
    out = []
    for (sym, r), rsv in zip(rows, rs):
        flags = []
        edays = None
        ed = (earnings or {}).get(sym)
        if ed is not None and today is not None:
            edays = int(np.busday_count(pd.Timestamp(today).date(), pd.Timestamp(ed).date()))
            if 0 <= edays <= 5:
                flags.append("earnings")
        if r["dollar"] < 20e6:
            flags.append("thin")
        if r["ext"] > 3:
            flags.append("extended")
        b = r["best"]
        total = (WEIGHTS["trend"] * r["p_trend"] + WEIGHTS["rs"] * rsv + WEIGHTS["volume"] * r["p_volume"]
                 + WEIGHTS["setup"] * r["p_setup"] + WEIGHTS["risk"] * r["p_risk"])
        total -= 8 if "earnings" in flags else 0
        total -= 5 if "thin" in flags else 0
        if b is None or b["side"] < 0:
            total = min(total, 49.0)                           # no long setup: not an opportunity, however strong
        total = float(np.clip(total, 0, 100))
        keys = [s["key"] for s in r["setups"]]
        row = {"Symbol": sym, "Name": (names or {}).get(sym) or U.name_of(sym), "Sector": (sectors or {}).get(sym) or U.sector_of(sym),
               "Score": round(total, 1), "Grade": grade(total), "Setup": b["key"] if b else None,
               "Status": b["status"] if b else None, "Age": b["age"] if b else None, "Setups": ",".join(keys),
               "Side": b["side"] if b else 0, "Price": r["price"], "Chg %": r["chg"], "1M %": r["r1"], "3M %": r["r3"], "6M %": r["r6"],
               "RS": int(rsv), "RVOL": r["rvol"], "RSI": r["rsi"], "ADX": r["adx"], "From high %": r["dist_hi"], "ATR %": r["atr_pct"],
               "$Vol": r["dollar"], "Entry": b["entry"] if b else np.nan, "Stop": b["stop"] if b else np.nan,
               "Target": b["target"] if b else np.nan, "R:R": r["rr"], "Earnings": edays, "Flags": ",".join(flags),
               "Trend": r["p_trend"], "Accum": r["p_volume"], "SetupPts": r["p_setup"], "RiskPts": r["p_risk"],
               "Above50": r["above50"], "Above200": r["above200"], "NewHigh": r["new_high"], "NewLow": r["new_low"]}
        out.append(row)
        detail[sym] = {"setups": r["setups"], "spark": r["spark"], "sma20": r["sma20"], "sma50": r["sma50"], "sma200": r["sma200"],
                       "hi52": r["hi52"], "lo52": r["lo52"], "ud": r["ud"], "ext": r["ext"], "bw_pct": r["bw_pct"]}
    res = pd.DataFrame(out).sort_values(["Score", "RS"], ascending=False).reset_index(drop=True)
    return res, detail


def regime(res, spy=None, vix=None):
    """The market's mood from SPY, the scanned stocks and the VIX: {'mood': on / mixed / off, ...}."""
    out = {"pct50": np.nan, "pct200": np.nan, "highs": 0, "lows": 0, "spy_trend": None, "vix": np.nan, "spy_chg": np.nan}
    if res is not None and len(res):
        out["pct50"] = float(res["Above50"].mean() * 100)
        out["pct200"] = float(res["Above200"].mean() * 100)
        out["highs"], out["lows"] = int(res["NewHigh"].sum()), int(res["NewLow"].sum())
    s = _clean(spy)
    if s is not None:
        c = s["Close"]
        s50, s200 = c.rolling(50).mean().iloc[-1], c.rolling(200).mean().iloc[-1]
        last = float(c.iloc[-1])
        out["spy_chg"] = float((c.iloc[-1] / c.iloc[-2] - 1) * 100)
        out["spy_trend"] = "up" if last > s50 > s200 else ("down" if last < s200 else "mixed")
        out["spy_vs50"], out["spy_vs200"] = float((last / s50 - 1) * 100), float((last / s200 - 1) * 100) if np.isfinite(s200) else np.nan
    if vix is not None and len(vix):
        out["vix"] = float(pd.Series(vix["Close"]).dropna().iloc[-1])
    p50 = out["pct50"]
    if out["spy_trend"] == "down" or (np.isfinite(p50) and p50 < 35) or (np.isfinite(out["vix"]) and out["vix"] >= 30):
        out["mood"] = "off"
    elif out["spy_trend"] == "up" and (not np.isfinite(p50) or p50 >= 55) and not (np.isfinite(out["vix"]) and out["vix"] >= 22):
        out["mood"] = "on"
    else:
        out["mood"] = "mixed"
    return out


def sectors(res):
    """Sectors ranked by the average RS rating of their stocks, with the share above their 50-day average and the count of
    opportunities (grade B or better)."""
    if res is None or res.empty:
        return pd.DataFrame()
    g = res.groupby("Sector").agg(rs=("RS", "mean"), above=("Above50", "mean"), n=("Symbol", "size"),
                                  opp=("Score", lambda s: int((s >= 65).sum())))
    g["above"] *= 100
    return g[g["n"] >= 2].sort_values("rs", ascending=False)


def size(entry, stop, account, risk_pct):
    """Shares to buy so that a stop-out loses risk_pct of the account (never more than the account)."""
    risk = entry - stop
    if not (np.isfinite(risk) and risk > 0 and entry > 0):
        return 0
    return int(max(0, min(account * risk_pct / 100 / risk, account / entry)))


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "9.9"
