"""
robobot.py - The Robo Advisor's Opportunity Bot: at risk levels 9 and 10 a slice of the portfolio (10% and 20%) hunts young,
fast-growing companies and explosive price moves, long when a breakout starts and short when a breakdown starts.

Its hunting ground is a list of emerging companies (recent listings and young growth names: AI, chips, quantum computing,
space, nuclear and new energy, electric vehicles and air taxis, fintech, cloud and cybersecurity, consumer internet,
biotech). Everything it does is read from daily prices and volume, so the same rules replay the same way on every visit:

- every week (the first trading day of the week) it ranks the list on the previous close. A LONG signal: a close above the
  55-day high (or within 3% of it), volume running above its 50-day average, strong 1- and 3-month momentum, an uptrend
  (price over its 20 and 50-day averages), a volatility squeeze that just released, extra weight for a young company.
  A SHORT signal: the mirror image, a close under the 55-day low on heavy volume, falling momentum, a downtrend;
  only stocks of $5 or more with enough trading (brokers lend those);
- free slots are filled with the best signals (score 55 or more) at that day's close, each slot an equal share of the
  slice (level 9: 4 long + 2 short, level 10: 6 long + 3 short);
- each position has a stop 2.5 ATR away that trails the best close by 3 ATR; one that has not gained 10% after 60 trading
  days leaves (a winner stays with its trailing stop); a short pays a borrow fee (5% a year). A stopped stock waits 10 days
  before it can come back.
- extended hours (from EXT_FROM on, with Yahoo's pre-market and after-hours prices): the scan reads the scan day's own close
  and its trades are filled in that evening's after-hours session (the close of its first hour, 0.1% worse) instead of at the
  next close; the stops are also checked on the last price of the pre-market and of the after-hours session. A day without
  these prices trades the regular way.

A Sharia-compliant portfolio is long only (no short selling) and hunts only the companies whose business passes a
business-activity screen (no lending, insurance, brokerage, crypto, gambling or weapons; financial ratios are not checked).
"""
import math

import numpy as np
import pandas as pd
import streamlit as st

import data

SAT = {9: 10.0, 10: 20.0}                       # the slice of the portfolio the bot runs (percent), by risk level
SLOTS = {9: (4, 2), 10: (6, 3)}                 # long, short positions
THRESHOLD = 55                                  # the score a signal needs to be bought
STOP_ATR, TRAIL_ATR = 2.5, 3.0
MAX_DAYS, COOLDOWN = 60, 10
KEEP_IF = 10.0                                  # % gained: past MAX_DAYS a position this far ahead stays (its trailing stop decides)
BORROW = 0.05                                   # a year, on the value shorted
MIN_PX_LONG, MIN_PX_SHORT = 3.0, 5.0
MIN_DV_LONG, MIN_DV_SHORT = 10e6, 20e6          # average dollar volume a day (20 days)
EXT_FROM = pd.Timestamp("2026-10-09")           # 21.9: the bot trades the extended hours from this session on (earlier days replay as before)
EXT_SLIP = 0.001                                # extended hours: thinner trading, fills 0.1% worse

THEMES = {"ai": ("AI & data", "الذكاء الاصطناعي والبيانات", "neurology"),
          "chips": ("AI chips & cloud", "رقائق وسحابة الذكاء الاصطناعي", "memory"),
          "quantum": ("Quantum computing", "الحوسبة الكمية", "blur_on"),
          "space": ("Space & defense tech", "الفضاء وتقنيات الدفاع", "rocket_launch"),
          "energy": ("Nuclear & new energy", "الطاقة النووية والجديدة", "bolt"),
          "mobility": ("EVs & air taxis", "السيارات الكهربائية والتاكسي الطائر", "electric_car"),
          "fintech": ("Fintech & crypto", "التقنية المالية والكريبتو", "currency_bitcoin"),
          "software": ("Cloud & cybersecurity", "السحابة والأمن السيبراني", "cloud"),
          "consumer": ("Consumer & internet", "المستهلك والإنترنت", "storefront"),
          "health": ("Health & biotech", "الصحة والتقنية الحيوية", "biotech")}
# ticker: (name, theme, passes the Sharia business screen)
UNIVERSE = {
    "PLTR": ("Palantir", "ai", True), "AI": ("C3.ai", "ai", True), "SOUN": ("SoundHound AI", "ai", True),
    "BBAI": ("BigBear.ai", "ai", True), "PATH": ("UiPath", "ai", True), "TEM": ("Tempus AI", "ai", True), "APP": ("AppLovin", "ai", True),
    "ARM": ("Arm Holdings", "chips", True), "SMCI": ("Super Micro Computer", "chips", True), "CRDO": ("Credo Technology", "chips", True),
    "ALAB": ("Astera Labs", "chips", True), "CRWV": ("CoreWeave", "chips", True), "NBIS": ("Nebius", "chips", True),
    "IONQ": ("IonQ", "quantum", True), "RGTI": ("Rigetti Computing", "quantum", True), "QBTS": ("D-Wave Quantum", "quantum", True),
    "QUBT": ("Quantum Computing Inc", "quantum", True),
    "RKLB": ("Rocket Lab", "space", True), "ASTS": ("AST SpaceMobile", "space", True), "LUNR": ("Intuitive Machines", "space", True),
    "RDW": ("Redwire", "space", True), "PL": ("Planet Labs", "space", True), "KTOS": ("Kratos Defense", "space", False),
    "AVAV": ("AeroVironment", "space", False),
    "OKLO": ("Oklo", "energy", True), "SMR": ("NuScale Power", "energy", True), "NNE": ("Nano Nuclear Energy", "energy", True),
    "LEU": ("Centrus Energy", "energy", True), "FLNC": ("Fluence Energy", "energy", True), "EOSE": ("Eos Energy", "energy", True),
    "RIVN": ("Rivian", "mobility", True), "LCID": ("Lucid", "mobility", True), "JOBY": ("Joby Aviation", "mobility", True),
    "ACHR": ("Archer Aviation", "mobility", True), "QS": ("QuantumScape", "mobility", True),
    "SOFI": ("SoFi", "fintech", False), "AFRM": ("Affirm", "fintech", False), "UPST": ("Upstart", "fintech", False),
    "HOOD": ("Robinhood", "fintech", False), "NU": ("Nu Holdings", "fintech", False), "COIN": ("Coinbase", "fintech", False),
    "TOST": ("Toast", "fintech", False), "CRCL": ("Circle", "fintech", False), "MARA": ("MARA Holdings", "fintech", False),
    "RIOT": ("Riot Platforms", "fintech", False), "IREN": ("IREN", "fintech", False),
    "NET": ("Cloudflare", "software", True), "DDOG": ("Datadog", "software", True), "S": ("SentinelOne", "software", True),
    "RBRK": ("Rubrik", "software", True), "GTLB": ("GitLab", "software", True), "MDB": ("MongoDB", "software", True),
    "SNOW": ("Snowflake", "software", True), "DUOL": ("Duolingo", "software", True),
    "RDDT": ("Reddit", "consumer", True), "RBLX": ("Roblox", "consumer", True), "DASH": ("DoorDash", "consumer", True),
    "ABNB": ("Airbnb", "consumer", True), "CAVA": ("CAVA", "consumer", True), "ONON": ("On Holding", "consumer", True),
    "BIRK": ("Birkenstock", "consumer", True), "CART": ("Instacart", "consumer", True), "CELH": ("Celsius", "consumer", True),
    "HIMS": ("Hims & Hers", "health", True), "VKTX": ("Viking Therapeutics", "health", True), "RXRX": ("Recursion", "health", True),
}

# the signals a position was opened on (key -> en, ar), shown as chips
WHY = {"brk": ("55-day high breakout", "اختراق قمة 55 يوم"), "near": ("Near its 55-day high", "قريب من قمة 55 يوم"),
       "brkd": ("55-day low breakdown", "كسر قاع 55 يوم"), "neard": ("Near its 55-day low", "قريب من قاع 55 يوم"),
       "vol": ("Volume ×{v:.1f}", "حجم ×{v:.1f}"), "mom": ("3 months {r:+.0f}%", "3 أشهر {r:+.0f}%"),
       "up": ("Uptrend", "اتجاه صاعد"), "down": ("Downtrend", "اتجاه هابط"), "sq": ("Squeeze released", "انطلاق بعد انضغاط"),
       "young": ("Young company", "شركة ناشئة")}
EXIT = {"stop": ("Stop loss", "وقف الخسارة"), "trail": ("Trailing stop", "الوقف المتحرك"), "time": ("Time limit", "انتهاء المدة"),
        "plan": ("Plan change", "تغيير الخطة")}


def universe(sharia=False):
    return [t for t, v in UNIVERSE.items() if v[2] or not sharia]


def slots(level, sharia=False):
    n_long, n_short = SLOTS.get(int(level), (0, 0))
    return (n_long + n_short, 0) if sharia else (n_long, n_short)


# ---------------------------------------------------------------- signals (pure, testable)
def features(df, first_listed=None, young_days=3 * 365):
    """Indicators and the two scores (0-100) for every day of one company's daily OHLCV. Uses only data up to each day."""
    if df is None or df.empty or "Close" not in df:
        return pd.DataFrame()
    d = df.copy()
    idx = pd.to_datetime(d.index)
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_localize(None)
    d.index = idx.normalize()
    d = d[~d.index.duplicated(keep="last")].sort_index()
    c = pd.to_numeric(d["Close"], errors="coerce")
    h = pd.to_numeric(d.get("High", c), errors="coerce").fillna(c)
    lo = pd.to_numeric(d.get("Low", c), errors="coerce").fillna(c)
    v = pd.to_numeric(d.get("Volume", pd.Series(0.0, index=d.index)), errors="coerce").fillna(0.0)
    f = pd.DataFrame(index=d.index)
    f["c"] = c
    f["sma20"] = c.rolling(20, min_periods=20).mean()
    f["sma50"] = c.rolling(50, min_periods=50).mean()
    f["sma200"] = c.rolling(200, min_periods=120).mean()
    f["hh"] = h.shift(1).rolling(55, min_periods=40).max()
    f["ll"] = lo.shift(1).rolling(55, min_periods=40).min()
    f["vr"] = v.rolling(5, min_periods=5).mean() / v.rolling(50, min_periods=30).mean().replace(0, np.nan)
    f["r5"], f["r21"], f["r63"] = c.pct_change(5, fill_method=None), c.pct_change(21, fill_method=None), c.pct_change(63, fill_method=None)
    tr = pd.concat([h - lo, (h - c.shift(1)).abs(), (lo - c.shift(1)).abs()], axis=1).max(axis=1)
    f["atr"] = tr.rolling(14, min_periods=10).mean()
    bw = c.rolling(20, min_periods=20).std() / c.rolling(20, min_periods=20).mean()
    f["bwp"] = bw.rolling(120, min_periods=60).rank(pct=True)
    f["sq"] = (f["bwp"].rolling(10, min_periods=1).min() <= 0.25) & (f["bwp"] > 0.5)
    f["dv"] = (c * v).rolling(20, min_periods=10).mean()
    f["n"] = np.arange(1, len(f) + 1)
    first = pd.Timestamp(first_listed) if first_listed is not None else None
    f["young"] = ((f.index - first).days < young_days) if first is not None else False
    num = lambda s: s.fillna(False).astype(float) if s.dtype == bool or s.dtype == object else s.astype(float)
    hh, ll = f["hh"], f["ll"]
    brk = (c > hh).astype(float) * 30 + ((c >= hh * 0.97) & (c <= hh)).astype(float) * 15
    vol = ((f["vr"] - 1).clip(0, 1) * 25).fillna(0)
    mom = (f["r63"].clip(0, 0.4) / 0.4 * 20).fillna(0) + (f["r21"] > 0).astype(float) * 5
    trend = ((c > f["sma20"]) & (f["sma20"] > f["sma50"])).astype(float) * 10 + (f["sma50"] > f["sma200"]).astype(float) * 5
    f["long"] = (brk + vol + mom + trend + num(f["sq"]) * 10 + num(f["young"]) * 5).clip(0, 100)
    f["ok_long"] = (brk > 0) & (c >= MIN_PX_LONG) & (f["dv"] >= MIN_DV_LONG) & (f["n"] >= 60) & f["atr"].notna()
    brkd = (c < ll).astype(float) * 30 + ((c <= ll * 1.03) & (c >= ll)).astype(float) * 15
    vold = ((f["vr"] - 1).clip(0, 1) * 25).fillna(0) * (f["r5"] < 0).astype(float)
    momd = ((-f["r63"]).clip(0, 0.4) / 0.4 * 20).fillna(0) + (f["r21"] < 0).astype(float) * 5
    trendd = ((c < f["sma20"]) & (f["sma20"] < f["sma50"])).astype(float) * 10 + (f["sma50"] < f["sma200"]).astype(float) * 5
    f["short"] = (brkd + vold + momd + trendd).clip(0, 100)
    f["ok_short"] = (brkd > 0) & (c >= MIN_PX_SHORT) & (f["dv"] >= MIN_DV_SHORT) & (f["n"] >= 60) & f["atr"].notna()
    return f


def reasons(row, side):
    """[(key, value)] of the signals behind a score (for the chips)."""
    out = []
    c = row["c"]
    if side == "long":
        if c > row["hh"]:
            out.append(("brk", None))
        elif row["hh"] and c >= row["hh"] * 0.97:
            out.append(("near", None))
        if row["vr"] == row["vr"] and row["vr"] >= 1.3:
            out.append(("vol", row["vr"]))
        if row["r63"] == row["r63"] and row["r63"] >= 0.15:
            out.append(("mom", row["r63"] * 100))
        if c > row["sma20"] > row["sma50"]:
            out.append(("up", None))
        if bool(row.get("sq")):
            out.append(("sq", None))
        if bool(row.get("young")):
            out.append(("young", None))
    else:
        if c < row["ll"]:
            out.append(("brkd", None))
        elif row["ll"] and c <= row["ll"] * 1.03:
            out.append(("neard", None))
        if row["vr"] == row["vr"] and row["vr"] >= 1.3 and row["r5"] < 0:
            out.append(("vol", row["vr"]))
        if row["r63"] == row["r63"] and row["r63"] <= -0.15:
            out.append(("mom", row["r63"] * 100))
        if c < row["sma20"] < row["sma50"]:
            out.append(("down", None))
    return out


def build(ohlcv, sharia=False):
    """{ticker: features} for the hunting list from {ticker: OHLCV}. A company whose data starts well after the others' is
    taken to have listed then (young for 3 years)."""
    tick = [t for t in universe(sharia) if t in ohlcv and ohlcv[t] is not None and not ohlcv[t].empty]
    if not tick:
        return {}
    def first(df):
        i = pd.to_datetime(df.index[:1])
        if getattr(i, "tz", None) is not None:
            i = i.tz_localize(None)
        return pd.Timestamp(i[0]).normalize()
    starts = {t: first(ohlcv[t]) for t in tick}
    earliest = min(starts.values())
    out = {}
    for t in tick:
        listed = starts[t] if starts[t] > earliest + pd.Timedelta(days=20) else None
        f = features(ohlcv[t], first_listed=listed)
        if len(f):
            out[t] = f
    return out


@st.cache_data(ttl=900, show_spinner=False)
def load(period="5y"):
    """The whole hunting list's features from Yahoo's daily bars (empty when nothing came back). A Sharia-compliant book and
    radar pick from it only the companies that pass the screen."""
    out = build(data.history_many(list(UNIVERSE), period))
    if not out:
        raise RuntimeError("no prices")        # not kept: the next visit tries again
    return out


def load_ext(feats):
    """The hunting list's pre-market and after-hours prices ({ticker: data.ext_summary}; {} when they can't be fetched)."""
    try:
        return data.extended_hours(list(feats)) if feats else {}
    except Exception:
        return {}


def radar(feats, sharia=False, n_long=6, n_short=4):
    """The best long and short candidates on the latest bar: [{t, side, score, signal (passes), why, c, theme}]."""
    longs, shorts = [], []
    for t, f in feats.items():
        if not len(f) or (sharia and not UNIVERSE[t][2]):
            continue
        row = f.iloc[-1]
        base = {"t": t, "c": float(row["c"]), "theme": UNIVERSE[t][1], "name": UNIVERSE[t][0], "r63": row["r63"]}
        if row["c"] >= MIN_PX_LONG and row["dv"] >= MIN_DV_LONG:
            longs.append({**base, "side": "long", "score": float(row["long"]), "signal": bool(row["ok_long"] and row["long"] >= THRESHOLD),
                          "why": reasons(row, "long")})
        if not sharia and row["c"] >= MIN_PX_SHORT and row["dv"] >= MIN_DV_SHORT:
            shorts.append({**base, "side": "short", "score": float(row["short"]), "signal": bool(row["ok_short"] and row["short"] >= THRESHOLD),
                           "why": reasons(row, "short")})
    longs.sort(key=lambda x: (not x["signal"], -x["score"]))
    shorts.sort(key=lambda x: (not x["signal"], -x["score"]))
    return longs[:n_long], shorts[:n_short]


def trade_plan(feats, value, level, sharia=False, held=(), cool=(), n_long_held=0, n_short_held=0, extra=2):
    """The trades the next weekly scan would open if the latest signals hold: for each free slot the best signal not held
    and not cooling down, with its entry (the latest close), its first stop, its size (the slice / the slots), the shares
    and the money at risk to the stop. Then `extra` runners-up per side, marked "next". -> (trades, summary)."""
    n_l, n_s = slots(level, sharia)
    total = n_l + n_s
    size = value / total if total else 0.0
    free = {"long": max(0, n_l - n_long_held), "short": max(0, n_s - n_short_held)}
    out = []
    for side in ("long", "short"):
        if (side == "long" and n_l == 0) or (side == "short" and n_s == 0):
            continue
        cands = []
        for t, f in feats.items():
            if not len(f) or t in held or t in cool or (sharia and not UNIVERSE[t][2]):
                continue
            row = f.iloc[-1]
            ok, sc = (row["ok_long"], row["long"]) if side == "long" else (row["ok_short"], row["short"])
            atr = row["atr"]
            if not bool(ok) or sc < THRESHOLD or atr != atr or atr <= 0:
                continue
            cands.append((float(sc), float(row["dv"]), t, row))
        cands.sort(key=lambda x: (-x[0], -x[1]))
        for i, (sc, _, t, row) in enumerate(cands[:free[side] + extra]):
            entry, atr = float(row["c"]), float(row["atr"])
            stop = entry - STOP_ATR * atr if side == "long" else entry + STOP_ATR * atr
            units = size / entry if entry else 0.0
            risk = units * abs(entry - stop)
            out.append({"t": t, "name": UNIVERSE[t][0], "theme": UNIVERSE[t][1], "side": side, "score": sc, "entry": entry, "stop": stop,
                        "dist": abs(entry - stop) / entry * 100, "trail": TRAIL_ATR * atr, "size": size, "units": units, "risk": risk,
                        "risk_pct": risk / value * 100 if value else 0.0, "why": reasons(row, side), "next": i >= free[side]})
    return out, {"size": size, "free_long": free["long"], "free_short": free["short"], "n_long": n_l, "n_short": n_s}


# ---------------------------------------------------------------- the bot's book (inside the robo replay)
class Book:
    """The bot's slice: cash and positions (units < 0 for a short), run day by day on the robo's trading days."""

    def __init__(self, feats, index, level=10, sharia=False, ext=None, now=None):
        """ext: {ticker: data.ext_summary} (the extended hours, see the module's notes); now: New York time (default: now)."""
        self.level, self.sharia = int(level), bool(sharia)
        self.n_long, self.n_short = slots(self.level, self.sharia)
        self.tick = [t for t in feats if len(feats[t])]
        self.index = index
        al = {t: feats[t].reindex(index) for t in self.tick}
        self.f = al
        self.C = pd.DataFrame({t: al[t]["c"] for t in self.tick}, index=index).ffill() if self.tick else pd.DataFrame(index=index)
        self.L = pd.DataFrame({t: al[t]["long"].where(al[t]["ok_long"].fillna(False).astype(bool)) for t in self.tick}, index=index)
        self.S = pd.DataFrame({t: al[t]["short"].where(al[t]["ok_short"].fillna(False).astype(bool)) for t in self.tick}, index=index)
        self.cash, self.cost = 0.0, 0.0
        self.pos = {}
        self.trades, self.opens = [], []
        self.cool = {}
        self.curve = []
        self.wait = None                     # a scan day whose trades wait for tonight's after-hours session
        self.now = pd.Timestamp(now) if now is not None else pd.Timestamp.now(tz="America/New_York").tz_localize(None)
        self.X = None
        if ext and self.tick:
            # each day's extended prices on the footing of the adjusted daily ones (x the adjusted close / the regular last price)
            days = pd.DatetimeIndex(index).normalize()
            if getattr(days, "tz", None) is not None:
                days = days.tz_localize(None)
            X = {c: {} for c in ("PMc", "AHf", "AHc")}
            for t in self.tick:
                xs = ext.get(t)
                if xs is None or not len(xs):
                    continue
                xs = xs[~xs.index.duplicated(keep="last")].reindex(days)
                f = al[t]["c"].to_numpy(float) / xs["RC"].to_numpy(float)
                f = np.where((f > 0.8) & (f < 1.25), f, np.nan)
                for c in X:
                    X[c][t] = xs[c].to_numpy(float) * f
            if X["AHf"]:
                self.X = {c: pd.DataFrame(v, index=index) for c, v in X.items()}
                ah = self.X["AHf"]
                self.xdays = set(ah.index[ah.notna().any(axis=1)])     # the days with after-hours prices at all

    def xpx(self, col, t, d):
        """An extended-hours price of ticker t on day d (None without one)."""
        try:
            v = self.X[col].at[d, t]
        except (KeyError, TypeError):
            return None
        return None if v != v else float(v)

    def _ext_on(self, d):
        """Day d trades the extended hours (prices loaded, from EXT_FROM on)."""
        if self.X is None:
            return False
        d = pd.Timestamp(d)
        return (d.tz_localize(None) if d.tz is not None else d) >= EXT_FROM

    def _after(self, d, minutes):
        """`minutes` after day d's close has passed (always, for a day before today)."""
        d = pd.Timestamp(d)
        d = d.tz_localize(None) if d.tz is not None else d
        if d.normalize() < self.now.normalize():
            return True
        import mcal
        close = 13 * 60 if mcal.day_status(d.date())[0] == "early" else 16 * 60
        return self.now >= d.normalize() + pd.Timedelta(minutes=close + minutes)

    def set_level(self, level, sharia, d=None):
        """A new plan: the slots of its level; turning Sharia-compliant closes the shorts and the companies off its list."""
        self.level, self.sharia = int(level), bool(sharia)
        self.n_long, self.n_short = slots(self.level, self.sharia)
        if self.sharia and d is not None:
            for t, p in list(self.pos.items()):
                if p["side"] == "short" or not UNIVERSE[t][2]:
                    self._close(t, d, "plan")

    def px(self, t, d):
        try:
            v = self.C.at[d, t]
        except KeyError:
            return None
        return None if v != v else float(v)

    def value(self, d):
        v = self.cash
        for t, p in self.pos.items():
            x = self.px(t, d)
            v += p["u"] * (x if x is not None else p["last"])
        return v

    def deposit(self, x):
        self.cash += x
        self.cost += x

    def withdraw(self, x, d, why="plan"):
        """Takes `x` out: every position and the cash cut by the same share (all of it: everything closed)."""
        v = self.value(d)
        if v <= 0:
            return
        k = max(0.0, 1 - x / v)
        if k <= 1e-9:
            for t in list(self.pos):
                self._close(t, d, why)
            self.cash, self.cost = 0.0, 0.0
            return
        for p in self.pos.values():
            p["u"] *= k
            p["size"] *= k
        self.cash *= k
        self.cost *= k

    def _close(self, t, d, why, price=None, x_=None):
        """price: an extended-hours fill (x_: 'pm' / 'ah'); else the day's close."""
        p = self.pos.pop(t)
        x = price if price is not None else (self.px(t, d) or p["last"])
        self.cash += p["u"] * x
        sign = 1 if p["side"] == "long" else -1
        ret = (x / p["entry"] - 1) * sign
        self.trades.append({"t": t, "side": p["side"], "d_in": p["d"], "px_in": p["entry"], "d_out": d, "px_out": x, "ret": ret * 100,
                            "pnl": p["u"] * (x - p["entry"]), "why": why, "days": p["held"], "reasons": p["why"],
                            **({"x_in": p["x"]} if p.get("x") else {}), **({"x_out": x_} if x_ else {})})
        if why in ("stop", "trail"):
            self.cool[t] = COOLDOWN

    def fees(self, d):
        """The day's borrow fee on the shorts (at its close)."""
        for t, p in self.pos.items():
            if p["side"] == "short":
                x = self.px(t, d)
                self.cash -= abs(p["u"]) * (x if x is not None else p["last"]) * BORROW / 252

    def _ext_stops(self, d, col, tag):
        """The stops on the last price of the pre-market (col PMc) or of the after-hours session (AHc)."""
        for t, p in list(self.pos.items()):
            x = self.xpx(col, t, d)
            if x is None:
                continue
            if (x <= p["stop"]) if p["side"] == "long" else (x >= p["stop"]):
                fill = x * (1 - EXT_SLIP) if p["side"] == "long" else x * (1 + EXT_SLIP)
                self._close(t, d, "trail" if p["stop"] != p["stop0"] else "stop", fill, tag)

    def step(self, d, prev_d, scan, fees=True):
        """One trading day at its close: the borrow fee (unless charged already), the exits, then (on a scan day) new positions
        from the previous close. With the extended hours: the stops also at the end of the pre-market and of the after-hours
        session, and the scan reads this close and fills in this evening's after-hours session."""
        ext = self._ext_on(d)
        if fees:
            self.fees(d)
        for t in list(self.cool):
            self.cool[t] -= 1
            if self.cool[t] <= 0:
                del self.cool[t]
        if ext:
            self._ext_stops(d, "PMc", "pm")
        for t, p in list(self.pos.items()):
            x = self.px(t, d)
            if x is None:
                continue
            p["last"] = x
            p["held"] += 1
            if p["side"] == "short":
                p["best"] = min(p["best"], x)
                p["stop"] = min(p["stop"], p["best"] + TRAIL_ATR * p["atr"])
                hit = x >= p["stop"]
            else:
                p["best"] = max(p["best"], x)
                p["stop"] = max(p["stop"], p["best"] - TRAIL_ATR * p["atr"])
                hit = x <= p["stop"]
            if hit:
                self._close(t, d, "trail" if p["stop"] != p["stop0"] else "stop")
            elif p["held"] >= MAX_DAYS and (x / p["entry"] - 1) * (1 if p["side"] == "long" else -1) * 100 < KEEP_IF:
                self._close(t, d, "time")
        self.wait = None
        if scan and ext and self.tick:
            if not self._after(d, 60):
                self.wait = d                        # tonight, once the after-hours session's first hour is over
            elif d in self.xdays:                    # filled at the close of that first hour
                self._scan(d, d, ah=True)
            elif prev_d is not None:                 # a day without after-hours prices: the regular way
                self._scan(d, prev_d)
        elif scan and prev_d is not None and self.tick:
            self._scan(d, prev_d)
        if ext and self._after(d, 240):              # the after-hours session is over: its last price
            self._ext_stops(d, "AHc", "ah")
        self.curve.append((d, self.value(d), self.cost))

    def _scan(self, d, prev_d, ah=False):
        """New positions for the free slots from the signals of the close of prev_d, at the close of d (ah: at d's after-hours
        price, prev_d = d)."""
        held = set(self.pos)
        n_l = sum(1 for p in self.pos.values() if p["side"] == "long")
        n_s = len(self.pos) - n_l
        total = self.n_long + self.n_short
        if total <= 0:
            return
        size = self.value(d) / total
        if size <= 1:
            return
        for side, free, M in (("long", self.n_long - n_l, self.L), ("short", self.n_short - n_s, self.S)):
            if free <= 0:
                continue
            row = M.loc[prev_d].dropna() if prev_d in M.index else pd.Series(dtype=float)
            row = row[row >= THRESHOLD].sort_values(ascending=False)
            for t in row.index:
                if free <= 0:
                    break
                if t in held or t in self.cool or (self.sharia and not UNIVERSE[t][2]):
                    continue
                x = self.px(t, d)
                if ah:                                 # no after-hours price for it: it waits for the next scan
                    x = self.xpx("AHf", t, d)
                    x = None if x is None else x * (1 + EXT_SLIP if side == "long" else 1 - EXT_SLIP)
                fr = self.f[t].loc[prev_d]
                atr = fr["atr"]
                if x is None or atr != atr or atr <= 0:
                    continue
                if side == "long":
                    amt = min(size, self.cash)
                    if amt < size * 0.5:
                        continue
                    u = amt / x
                    self.cash -= amt
                    stop = x - STOP_ATR * atr
                else:
                    amt = size
                    u = -amt / x
                    self.cash += amt
                    stop = x + STOP_ATR * atr
                why = reasons(fr, side)
                self.pos[t] = {"side": side, "u": u, "entry": x, "d": d, "atr": float(atr), "stop": stop, "stop0": stop, "best": x,
                               "held": 0, "last": x, "size": amt, "score": float(row[t]), "why": why, **({"x": "ah"} if ah else {})}
                self.opens.append({"t": t, "side": side, "d": d, "px": x, "score": float(row[t]), "why": why, **({"x": "ah"} if ah else {})})
                held.add(t)
                free -= 1

    def positions(self, d):
        """[{t, side, entry, d, px, ret, pnl, stop, held, value, why}] now."""
        out = []
        for t, p in self.pos.items():
            x = self.px(t, d) or p["last"]
            sign = 1 if p["side"] == "long" else -1
            out.append({"t": t, "side": p["side"], "entry": p["entry"], "d": p["d"], "px": x, "ret": (x / p["entry"] - 1) * sign * 100,
                        "pnl": p["u"] * (x - p["entry"]), "stop": p["stop"], "held": p["held"], "value": abs(p["u"]) * x, "why": p["why"],
                        "score": p["score"]})
        return sorted(out, key=lambda r: -r["ret"])


def stats(book):
    """{n, win, avg_win, avg_loss, best, worst} of the closed trades."""
    tr = book.trades if book is not None else []
    if not tr:
        return {"n": 0}
    rets = [x["ret"] for x in tr]
    wins = [r for r in rets if r > 0]
    loss = [r for r in rets if r <= 0]
    return {"n": len(tr), "win": len(wins) / len(tr) * 100, "avg_win": float(np.mean(wins)) if wins else None,
            "avg_loss": float(np.mean(loss)) if loss else None, "best": max(tr, key=lambda x: x["ret"]), "worst": min(tr, key=lambda x: x["ret"]),
            "longs": sum(1 for x in tr if x["side"] == "long"), "shorts": sum(1 for x in tr if x["side"] == "short")}


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "21.9"
