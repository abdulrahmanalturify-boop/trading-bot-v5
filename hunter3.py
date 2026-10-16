"""
hunter3.py - Opportunity Hunter 3.0: the quantitative engine behind the Hunter 3.0 page (p_hunter3.py) and its research
(research/hunter3_backtest.py). It reuses the Opportunity Hunter's exact setups (hunter._series) and the smart bots' market
regime (brain.regime) and adds, on top of them:

  1. a FACTOR PANEL   for every stock, on every session, from that session's close and before (never a centred window):
                      momentum and trend (risk-adjusted momentum over 3 horizons, acceleration, relative and residual momentum,
                      trend efficiency and stability), volatility and risk (realised and downside volatility, ATR, drawdown,
                      beta, correlation, VaR / CVaR, volatility shock, skew), volume and liquidity (relative volume, up/down
                      volume, accumulation slope, dollar-volume trend, volume imbalance) and statistical behaviour
                      (autocorrelation, z-score, breakout strength, distance from the high);
  2. the SETUP PANEL  which setup (if any) is live on every session, its status (fresh / active / watch), entry, stop and target,
                      exactly as the Opportunity Hunter decides it on the last bar - so the same rule can be scored in the past;
  3. the MARKET STATE regime (bull / sideways / bear / stress, brain.regime), trends over 1, 3 and 12 months, breadth, new highs
                      and lows, volatility against its own year, dispersion, average correlation, risk-on / risk-off (cyclical
                      against defensive sectors), liquidity and leadership concentration - all as daily series;
  4. four SCORES      v1 (the Opportunity Hunter's own formula, replicated on every session), quant (ranked factor groups with
                      fixed weights), adaptive (the same groups weighted by the market regime, weights measured in the research
                      on 2010-2015 only: hunter3_weights.json) and ml (a gradient-boosted ranking model from the research,
                      models/hunter3_rank.json, used only where its walk-forward validation held) - each with its explanation;
  5. a PORTFOLIO      correlation-aware selection, sector caps, risk- and volatility-based sizing, a regime exposure cap, a
                      drawdown brake and a stress scenario.

A score is a rank out of 100, never a probability of success. Everything here is pandas / numpy; no UI, no data download.
"""
import json
import os

import numpy as np
import pandas as pd

import brain
import hunter as H
import playbooks as PB

BUILD = "23.4.41"
HERE = os.path.dirname(os.path.abspath(__file__))
WEIGHTS_FILE = os.path.join(HERE, "hunter3_weights.json")
MODEL_FILE = os.path.join(HERE, "models", "hunter3_rank.json")

MIN_BARS = 260
HORIZON = 21                  # sessions: the forward window the research ranks against (one month)
REGIMES = brain.REGIMES       # bull, neutral, bear, stress

# the factor groups: (en, ar, [(factor, +1 higher is better / -1 lower is better), ...])
GROUPS = {
    "momentum": ("Momentum", "الزخم", [("ramom_126", 1), ("ramom_252", 1), ("rs_126", 1), ("resid_126", 1), ("accel", 1)]),
    "trend": ("Trend quality", "جودة الاتجاه", [("trend_bits", 1), ("er_63", 1), ("stab_63", 1), ("dist_hi", 1)]),
    "volume": ("Volume & liquidity", "الحجم والسيولة", [("ud_50", 1), ("ad_slope", 1), ("dvol_trend", 1), ("imb_20", 1), ("rvol_20", 1)]),
    "risk": ("Risk", "المخاطر", [("vol_63", -1), ("mdd_126", 1), ("cvar_95", 1), ("vol_shock", -1), ("beta_252", -1)]),
    "setup": ("Setup", "الفرصة", [("setup_pts", 1), ("rr_pts", 1)]),
}
FACTOR_LABEL = {
    "ramom_126": ("6-month return per unit of volatility", "عائد 6 أشهر لكل وحدة تذبذب"),
    "ramom_252": ("12-month return per unit of volatility", "عائد 12 شهر لكل وحدة تذبذب"),
    "rs_126": ("6-month lead over the market", "التفوق على السوق في 6 أشهر"),
    "resid_126": ("Return left after the market's share (beta)", "العائد المتبقي بعد نصيب السوق (بيتا)"),
    "accel": ("Momentum acceleration (last 3 months against the 3 before)", "تسارع الزخم (آخر 3 أشهر مقابل الـ 3 قبلها)"),
    "trend_bits": ("Above its 20, 50 and 200-day averages, rising", "فوق متوسطات 20 و50 و200 وصاعد"),
    "er_63": ("Trend efficiency (straight-line move / path)", "كفاءة الاتجاه (الحركة الصافية / المسار)"),
    "stab_63": ("Share of the last 3 months above the 50-day average", "نسبة آخر 3 أشهر فوق متوسط 50"),
    "dist_hi": ("Distance from the 52-week high", "البعد عن القمة السنوية"),
    "ud_50": ("Volume on up days against down days", "الحجم في الأيام الصاعدة مقابل الهابطة"),
    "ad_slope": ("Accumulation / distribution slope", "ميل خط التجميع / التوزيع"),
    "dvol_trend": ("Dollar volume, last month against 6 months", "قيمة التداول، آخر شهر مقابل 6 أشهر"),
    "imb_20": ("Volume imbalance (up minus down volume)", "اختلال الحجم (صاعد ناقص هابط)"),
    "rvol_20": ("Relative volume today", "الحجم النسبي اليوم"),
    "vol_63": ("Realised volatility (3 months)", "التذبذب الفعلي (3 أشهر)"),
    "mdd_126": ("Deepest fall in 6 months", "أعمق هبوط في 6 أشهر"),
    "cvar_95": ("Average of the worst 5% of days (CVaR)", "متوسط أسوأ 5% من الأيام (CVaR)"),
    "vol_shock": ("Volatility shock (3 weeks against 6 months)", "صدمة التذبذب (3 أسابيع مقابل 6 أشهر)"),
    "beta_252": ("Beta to the market", "بيتا مقابل السوق"),
    "setup_pts": ("Setup status (new / active / watch)", "حالة الفرصة (جديدة / نشطة / مراقبة)"),
    "rr_pts": ("Reward to risk of the trade plan", "العائد مقابل المخاطرة في خطة الصفقة"),
}
DEFAULT_WEIGHTS = {"momentum": 0.30, "trend": 0.20, "volume": 0.15, "risk": 0.15, "setup": 0.20}
# the exposure the portfolio may take in each regime (share of the capital), measured in the research as a policy to test
EXPOSURE = {"bull": 1.0, "neutral": 0.7, "bear": 0.35, "stress": 0.2}
# how a found setup is classified for the reader
TIER = {"fresh": ("Actionable signal", "إشارة قابلة للتنفيذ"), "active": ("Developing setup", "فرصة تتكوّن"),
        "watch": ("Watchlist candidate", "مرشح للمراقبة")}
CYCLICAL = {"Technology", "Consumer Cyclical", "Industrials", "Financial Services", "Basic Materials", "Communication Services", "Energy"}
DEFENSIVE = {"Utilities", "Consumer Defensive", "Healthcare", "Real Estate"}


# ---------------------------------------------------------------- helpers
def _naive(ix):
    ix = pd.DatetimeIndex(ix)
    return ix.tz_localize(None) if ix.tz is not None else ix


def clean(df, cutoff=None, min_bars=MIN_BARS):
    """Daily OHLCV sorted, deduplicated, positive, and cut at `cutoff` (nothing after it is kept). None if too short."""
    if not isinstance(df, pd.DataFrame) or df.empty or not {"Open", "High", "Low", "Close"}.issubset(df.columns):
        return None
    d = df.copy()
    d.index = _naive(d.index)
    d = d[~d.index.duplicated(keep="last")].sort_index()
    d = d.apply(pd.to_numeric, errors="coerce")
    if "Volume" not in d:
        d["Volume"] = np.nan
    d = d.dropna(subset=["Open", "High", "Low", "Close"])
    d = d[(d[["Open", "High", "Low", "Close"]] > 0).all(axis=1)]
    if cutoff is not None:
        d = d.loc[:pd.Timestamp(cutoff)]
    return d if len(d) >= min_bars else None


def _rolling_cvar(x, window, q):
    """The mean of the worst q share of the last `window` values, on every position (NaN until the window is full)."""
    n = len(x)
    out = np.full(n, np.nan)
    if n < window:
        return out
    win = np.lib.stride_tricks.sliding_window_view(x, window)
    k = max(1, int(np.floor(window * q)))
    part = np.partition(np.nan_to_num(win, nan=0.0), k - 1, axis=1)[:, :k]
    out[window - 1:] = part.mean(axis=1)
    return out


def _rolling_pct_of_last(x, window, min_periods):
    """The share of the last `window` values at or under the current one (hunter.analyze's bw_pct), on every position."""
    n = len(x)
    out = np.full(n, np.nan)
    if n >= window:
        win = np.lib.stride_tricks.sliding_window_view(x, window)
        with np.errstate(invalid="ignore"):
            out[window - 1:] = (win <= win[:, -1:]).sum(axis=1) / np.isfinite(win).sum(axis=1)
    # the first positions (fewer than `window` values but at least min_periods)
    for i in range(min_periods - 1, min(window - 1, n)):
        seg = x[:i + 1]
        seg = seg[np.isfinite(seg)]
        if len(seg) >= min_periods:
            out[i] = (seg <= x[i]).mean()
    return out


def _pct_rank(frame):
    """Cross-sectional percentile rank (0-100) of every row of a (date x stock) frame; NaN stays NaN."""
    return frame.rank(axis=1, pct=True) * 100


# ---------------------------------------------------------------- 1) the factor panel of one stock
def stock_features(df, bench=None):
    """Every factor of one stock on every session (a DataFrame on df's index), from that session's close and before.
    bench: the benchmark's OHLCV (for relative and residual momentum, beta and correlation); without it those are NaN."""
    c, h, lo, o = (df[k].astype(float) for k in ("Close", "High", "Low", "Open"))
    v = df["Volume"].astype(float)
    r = c.pct_change(fill_method=None)
    out = pd.DataFrame(index=df.index)
    sma20, sma50, sma200 = c.rolling(20).mean(), c.rolling(50).mean(), c.rolling(200, min_periods=200).mean()
    out["sma20"], out["sma50"], out["sma200"] = sma20, sma50, sma200
    atr = H.ta.atr(df).astype(float)
    out["atr"] = atr
    out["atr_pct"] = atr / c * 100
    # momentum
    for n in (21, 63, 126, 252):
        out[f"ret_{n}"] = (c / c.shift(n) - 1) * 100
    for n in (63, 126, 252):
        vol = r.rolling(n, min_periods=int(n * 0.8)).std() * np.sqrt(252)
        out[f"ramom_{n}"] = (c / c.shift(n) - 1) / vol.replace(0, np.nan)
    out["accel"] = out["ret_63"] - (out["ret_126"] - out["ret_63"])
    # trend
    out["trend_bits"] = ((c > sma20).astype(float) + (c > sma50) + (c > sma200) + (sma50 > sma200) + (sma200 > sma200.shift(20))) / 5 * 100
    out.loc[sma200.isna(), "trend_bits"] = ((c > sma20).astype(float) + (c > sma50))[sma200.isna()] / 5 * 100
    path = r.abs().rolling(63).sum()
    out["er_63"] = ((c / c.shift(63) - 1) / path.replace(0, np.nan)).clip(-1, 1)
    out["stab_63"] = (c > sma50).astype(float).rolling(63).mean() * 100
    hi252 = h.rolling(252, min_periods=120).max()
    out["dist_hi"] = (c / hi252 - 1) * 100
    out["z_50"] = (c - sma50) / c.rolling(50).std().replace(0, np.nan)
    out["ext_atr"] = (c - sma20) / atr.replace(0, np.nan)
    out["brk_str"] = (c - h.shift(1).rolling(20).max()) / atr.replace(0, np.nan)
    # volatility and risk
    out["vol_20"] = r.rolling(20).std() * np.sqrt(252) * 100
    out["vol_63"] = r.rolling(63).std() * np.sqrt(252) * 100
    out["vol_126"] = r.rolling(126).std() * np.sqrt(252) * 100
    out["dvol_63"] = r.clip(upper=0).rolling(63).std() * np.sqrt(252) * 100
    out["vol_shock"] = out["vol_20"] / out["vol_126"].replace(0, np.nan)
    out["mdd_126"] = (c / c.rolling(126).max() - 1) * 100
    q = r.rolling(252, min_periods=200)
    out["var_95"] = q.quantile(0.05) * 100
    out["cvar_95"] = _rolling_cvar(r.to_numpy(float), 252, 0.05) * 100
    out["skew_252"] = q.skew()
    out["autocorr_63"] = r.rolling(63).corr(r.shift(1))
    # volume and liquidity
    dollar = c * v
    out["dollar_20"] = dollar.rolling(20).mean()
    out["dvol_trend"] = out["dollar_20"] / dollar.rolling(126).mean().replace(0, np.nan)
    out["liq_det"] = (out["dollar_20"] / dollar.rolling(63).mean().replace(0, np.nan)) < 0.6
    out["rvol_20"] = v / v.shift(1).rolling(20).mean().replace(0, np.nan)
    upv = v.where(c > c.shift(1), 0.0)
    dnv = v.where(c < c.shift(1), 0.0)
    out["ud_50"] = (upv.rolling(50).sum() / dnv.rolling(50).sum().replace(0, np.nan)).clip(upper=5)
    out["imb_20"] = (upv.rolling(20).sum() - dnv.rolling(20).sum()) / v.rolling(20).sum().replace(0, np.nan)
    rng = (h - lo).replace(0, np.nan)
    ad = (((c - lo) - (h - c)) / rng * v).fillna(0).cumsum()
    out["ad_slope"] = (ad - ad.shift(20)) / v.rolling(20).sum().replace(0, np.nan)
    # against the benchmark
    if bench is not None and len(bench):
        b = bench["Close"].astype(float)
        b.index = _naive(b.index)
        b = b[~b.index.duplicated(keep="last")].sort_index().reindex(df.index, method="ffill", limit=5)
        br = b.pct_change(fill_method=None)
        for n in (63, 126):
            out[f"rs_{n}"] = (c / c.shift(n) - b / b.shift(n)) * 100
        cov = r.rolling(252, min_periods=200).cov(br)
        var = br.rolling(252, min_periods=200).var()
        beta = cov / var.replace(0, np.nan)
        out["beta_252"] = beta
        out["corr_63"] = r.rolling(63).corr(br)
        resid = (r - beta.shift(1) * br)
        out["resid_126"] = resid.rolling(126, min_periods=100).sum() * 100
        out["fwd_excess"] = ((c.shift(-HORIZON) / c - 1) - (b.shift(-HORIZON) / b - 1)) * 100   # research label: NaN at the end
    else:
        for k in ("rs_63", "rs_126", "beta_252", "corr_63", "resid_126", "fwd_excess"):
            out[k] = np.nan
    return out.replace([np.inf, -np.inf], np.nan)


# ---------------------------------------------------------------- 2) the setups on every session
SETUP_WINDOW = {k: (3 if k in H.PLAYBOOK_OF else 2) for k in H.ORDER}
_PRIO = {k: i for i, k in enumerate(H.ORDER)}


def setup_panel(df, bench=None, feats=None):
    """The Opportunity Hunter's best setup on every session: a DataFrame (key, status, entry, stop, target, side, age, n_setups,
    setups) following hunter.analyze's choice (fresh before active before watch, events before the leader state, then the
    hunter's order). The 'coil' watch setup needs the Bollinger width percentile: computed here too."""
    d = H.indicators(df)
    n = len(d)
    try:
        series = H._series(d, bench)
    except Exception:
        series = {}
    c = d["Close"].to_numpy(float)
    idx = np.arange(n)
    best_prio = np.full(n, np.inf)
    key = np.full(n, None, dtype=object)
    status = np.full(n, None, dtype=object)
    entry, stop, tgt, side, age = (np.full(n, np.nan) for _ in range(5))
    count = np.zeros(n, int)
    names = [[] for _ in range(n)]

    def take(mask, prio, k, st, e, s_, t_, sd, ag):
        better = mask & (prio < best_prio)
        count[mask] += 1
        for i in np.flatnonzero(mask):
            names[i].append(k)
        best_prio[better] = prio
        key[better], status[better] = k, st
        entry[better], stop[better], tgt[better], side[better], age[better] = e[better], s_[better], t_[better], sd, ag[better]

    for k in H.ORDER:
        en, ar, icon, kind, sd, _, _, _ = H.SETUPS[k]
        if kind == "watch":
            bw = d["BB_width"]
            pct = _rolling_pct_of_last(bw.to_numpy(float), 126, 61)
            s50, s200 = d["SMA50"].to_numpy(float), d["SMA200"].to_numpy(float)
            trig0 = np.fmax(d["BB_up"].to_numpy(float), pd.Series(d["High"]).shift(1).rolling(20).max().to_numpy(float))
            a = d["ATR"].to_numpy(float)
            st_ = np.fmin(d["BB_low"].to_numpy(float), trig0 - 1.5 * a)
            trig = trig0 * 1.001
            with np.errstate(invalid="ignore"):
                m = (pct <= 0.10) & (c > s50) & ~(np.isfinite(s200) & (s50 < s200)) & (trig0 > c) & (st_ < c)
            take(m, 2 * 100 + _PRIO[k], k, "watch", trig, st_, trig + 2.5 * (trig - st_), sd, np.full(n, np.nan))
            continue
        if k not in series:
            continue
        sig, st_, tg_, _ = series[k]
        if kind == "state":
            state = series.get("_leader_state", np.zeros(n, bool))
            # the age of the state: sessions since it began
            grp = np.cumsum(~state)
            first = pd.Series(idx).where(state).groupby(grp).transform("min").to_numpy(float)
            ag = idx - first
            m = state & np.isfinite(st_) & np.isfinite(tg_) & (st_ < c) & (c < tg_)
            take(m & (ag == 0), 0 * 100 + 50 + _PRIO[k], k, "fresh", c, st_, tg_, sd, ag)
            take(m & (ag > 0), 1 * 100 + 50 + _PRIO[k], k, "active", c, st_, tg_, sd, ag)
            continue
        last = pd.Series(np.where(sig, idx, np.nan)).ffill().to_numpy(float)
        ag = idx - last
        j = np.where(np.isfinite(last), last, 0).astype(int)
        s_at, t_at = st_[j], tg_[j]
        with np.errstate(invalid="ignore"):
            inside = (s_at < c) & (c < t_at) if sd > 0 else (t_at < c) & (c < s_at)
        live = np.isfinite(ag) & (ag <= SETUP_WINDOW[k]) & np.isfinite(s_at) & np.isfinite(t_at) & inside
        take(live & (ag == 0), 0 * 100 + _PRIO[k], k, "fresh", c, s_at, t_at, sd, ag)
        take(live & (ag > 0), 1 * 100 + _PRIO[k], k, "active", c, s_at, t_at, sd, ag)
    out = pd.DataFrame({"key": key, "status": status, "entry": entry, "stop": stop, "target": tgt, "side": side, "age": age,
                        "n_setups": count, "setups": [",".join(x) for x in names]}, index=d.index)
    # a bearish setup is the best only when no long one is live: hunter.analyze's rule ("longs first")
    return out


# ---------------------------------------------------------------- the v1 score on every session (hunter.hunt's formula)
def v1_parts(df, feats, setups):
    """The Opportunity Hunter's score parts on every session (trend, volume, setup, risk out of 100, and rs_raw to be ranked
    across the universe): the same arithmetic as hunter.analyze, vectorised over time."""
    c = df["Close"].astype(float)
    s20, s50, s200 = feats["sma20"], feats["sma50"], feats["sma200"]
    has200 = s200.notna()
    adx, dip, dim = H.ta.adx(df)
    tr = (20 * (has200 & (c > s200)) + 20 * (has200 & (s50 > s200)) + 20 * (c > s50) + 15 * (has200 & (s200 > s200.shift(20)))
          + 10 * (c > s20) + 15 * ((adx >= 20) & (dip > dim))).astype(float)
    r3, r6, r9, r12 = feats["ret_63"], feats["ret_126"], (c / c.shift(189) - 1) * 100, feats["ret_252"]
    parts = [(0.4, r3), (0.2, r6), (0.2, r9), (0.2, r12)]
    wsum = sum(w * x.notna() for w, x in parts)
    rs_raw = sum(w * x.fillna(0) for w, x in parts) / wsum.replace(0, np.nan)
    ud = feats["ud_50"].fillna(2.0)
    volp = ((ud - 0.6) / 1.0 * 100).clip(0, 100) * 0.8
    rvol = feats["rvol_20"]
    volp = volp + ((rvol - 1) * 20).clip(0, 20).where(rvol.notna() & (c >= c.shift(1)), 0)
    st = setups["status"]
    setup = pd.Series(np.select([st == "fresh", st == "active", st == "watch"], [100.0, 78.0, 55.0], 0.0), index=df.index)
    is_state = setups["key"].map(lambda k: isinstance(k, str) and H.SETUPS[k][3] == "state")
    setup = setup.where(~(is_state & (st == "active")), 68.0)
    in_pb = setups["key"].map(lambda k: isinstance(k, str) and k in H.PLAYBOOK_OF)
    setup = setup.where(~(in_pb & (st != "watch")), (setup + 8).clip(upper=100))
    setup = setup.where(setups["side"] > 0, 0.0)
    risk = (setups["entry"] - setups["stop"])
    rr = (setups["target"] - setups["entry"]) / risk.where(risk > 0)
    rr = rr.where(setups["side"] > 0)
    riskp = pd.Series(np.interp(rr.fillna(-1), [0.8, 1.5, 2.0, 3.0], [15, 50, 75, 100]), index=df.index).where(rr.notna(), 0.0)
    riskp = riskp - 20 * ((risk / feats["atr"]) > 3.5).where(rr.notna(), False)
    riskp = riskp - 30 * (feats["ext_atr"] > 3)
    return pd.DataFrame({"p_trend": tr, "p_volume": volp.clip(upper=100), "p_setup": setup, "p_risk": riskp.clip(0, 100),
                         "rs_raw": rs_raw, "rr": rr, "thin": feats["dollar_20"] < 20e6, "extended": feats["ext_atr"] > 3})


def v1_score(parts, rs):
    """hunter.hunt's total from the parts and the RS rating (1-99), without the earnings penalty (no calendar in the past)."""
    w = H.WEIGHTS
    total = (w["trend"] * parts["p_trend"] + w["rs"] * rs + w["volume"] * parts["p_volume"] + w["setup"] * parts["p_setup"]
             + w["risk"] * parts["p_risk"])
    total = total - 5 * parts["thin"].astype(float)
    return total.clip(0, 100)


# ---------------------------------------------------------------- 3) the whole universe as panels
class Panel:
    """Everything about a universe on every session: factor panels (date x stock), the setups, the v1 parts and the market."""

    def __init__(self, prices, bench, vix=None, sectors=None, cutoff=None, min_bars=MIN_BARS):
        self.bench = clean(bench, cutoff, 200)
        self.vix = clean(vix, cutoff, 5) if vix is not None else None
        self.sectors = sectors or {}
        self.frames, self.feats, self.setups, self.parts = {}, {}, {}, {}
        for sym, raw in prices.items():
            if sym in ("SPY", "^VIX", "KSA", "^TASI.SR"):
                continue
            d = clean(raw, cutoff, min_bars)
            if d is None:
                continue
            try:
                f = stock_features(d, self.bench)
                s = setup_panel(d, self.bench, f)
                p = v1_parts(d, f, s)
            except Exception:
                continue
            self.frames[sym], self.feats[sym], self.setups[sym], self.parts[sym] = d, f, s, p
        self.syms = list(self.frames)
        self.index = self.bench.index if self.bench is not None else pd.DatetimeIndex(sorted(set().union(*(d.index for d in self.frames.values()))))
        self._cols = {}

    def col(self, name, source="feats"):
        """A (date x stock) frame of one column, aligned on the panel's index (cached)."""
        k = (source, name)
        if k not in self._cols:
            src = getattr(self, source)
            self._cols[k] = pd.DataFrame({s: src[s][name] for s in self.syms}).reindex(self.index)
        return self._cols[k]

    def closes(self):
        return self.col("Close", "frames")

    # ---- the RS rating of every stock on every session (1-99 across the universe, or against the benchmark for small lists)
    def rs_rating(self):
        raw = self.col("rs_raw", "parts")
        if len(self.syms) >= 60:
            return (raw.rank(axis=1, pct=True) * 98 + 1).round().clip(1, 99).fillna(50.0)
        b = self.bench["Close"].astype(float)
        parts = [(0.4, 63), (0.2, 126), (0.2, 189), (0.2, 252)]
        spy = sum(w * (b / b.shift(k) - 1) * 100 for w, k in parts).reindex(self.index)
        return (50 + 49 * np.tanh(raw.sub(spy, axis=0) / 25)).clip(1, 99).fillna(50.0)

    # ---- the market state on every session
    def market_state(self):
        """A DataFrame on the panel's index: regime, trend_21/63/252 (%), vol_20, vol_pct (against its own year), breadth50,
        breadth200, highs, lows (shares), dispersion, avg_corr, risk_on (cyclical minus defensive 3-month return, pts),
        liquidity (aggregate dollar volume against its year), leadership (top-decile gap), concentration."""
        b = self.bench["Close"].astype(float).reindex(self.index)
        br = b.pct_change(fill_method=None)
        c = self.closes()
        above50 = (c > self.col("sma50")).astype(float).where(c.notna())
        codes, parts = brain.regime(self.bench, self.index, above50.to_numpy(float))
        out = pd.DataFrame(index=self.index)
        out["regime"] = [REGIMES[k] for k in codes]
        for n in (21, 63, 252):
            out[f"trend_{n}"] = (b / b.shift(n) - 1) * 100
        out["vs200"] = (b / b.rolling(200, min_periods=200).mean() - 1) * 100
        out["vol_20"] = br.rolling(20).std() * np.sqrt(252) * 100
        out["vol_pct"] = out["vol_20"].rolling(252, min_periods=60).rank(pct=True) * 100
        out["breadth50"] = above50.mean(axis=1) * 100
        out["breadth200"] = (c > self.col("sma200")).astype(float).where(c.notna()).mean(axis=1) * 100
        hi = self.col("High", "frames").rolling(252, min_periods=120).max()
        lo = self.col("Low", "frames").rolling(252, min_periods=120).min()
        out["highs"] = (self.col("High", "frames") >= hi * 0.999).mean(axis=1) * 100
        out["lows"] = (self.col("Low", "frames") <= lo * 1.001).mean(axis=1) * 100
        r21 = self.col("ret_21")
        out["dispersion"] = r21.std(axis=1)
        out["avg_corr"] = self.col("corr_63").mean(axis=1)
        r63 = self.col("ret_63")
        if self.sectors:
            sec = pd.Series({s: self.sectors.get(s) for s in self.syms})
            cyc = r63[[s for s in self.syms if sec[s] in CYCLICAL]].mean(axis=1) if any(sec.isin(CYCLICAL)) else np.nan
            dfn = r63[[s for s in self.syms if sec[s] in DEFENSIVE]].mean(axis=1) if any(sec.isin(DEFENSIVE)) else np.nan
            out["risk_on"] = cyc - dfn
        else:
            out["risk_on"] = np.nan
        dollar = self.col("dollar_20")
        agg = dollar.sum(axis=1)
        out["liquidity"] = agg / agg.rolling(252, min_periods=60).median()
        top = r63.apply(lambda row: row.nlargest(max(1, len(row.dropna()) // 10)).mean() if row.notna().sum() >= 10 else np.nan, axis=1)
        out["leadership"] = top - r63.mean(axis=1)
        out["concentration"] = (r63.rank(axis=1, pct=True) >= 0.9).mean(axis=1) * 100   # share of names in the top decile: constant by design, kept for the strip
        out["risk_off_flag"] = (out["regime"].isin(["bear", "stress"])) | (out["vol_pct"] >= 90)
        return out

    # ---- the factor groups ranked across the universe on every session: {group: (date x stock) 0-100}
    def group_ranks(self):
        setups = {"setup_pts": self.col("p_setup", "parts"), "rr_pts": self.col("p_risk", "parts")}
        groups = {}
        for g, (_, _, members) in GROUPS.items():
            acc, cnt = None, None
            for name, sign in members:
                frame = setups[name] if name in setups else self.col(name)
                rk = _pct_rank(frame * sign)
                acc = rk.fillna(0) if acc is None else acc + rk.fillna(0)
                cnt = rk.notna().astype(float) if cnt is None else cnt + rk.notna()
            groups[g] = acc / cnt.replace(0, np.nan)
        return groups

    # ---- the scores of every stock on every session (date x stock), {method: frame}, and the group ranks
    def scores(self, methods=("v1", "quant", "adaptive", "ml"), weights=None, model=None, state=None):
        groups = self.group_ranks()
        side = self.col("side", "setups")
        long_ok = side > 0                                   # the new scores: an actionable long setup, or at most 49
        v1_ok = side >= 0                                    # the old Hunter caps only a bearish setup or none (a watch passes)
        out = {}
        rs = self.rs_rating()
        parts = {k: self.col(k, "parts") for k in ("p_trend", "p_volume", "p_setup", "p_risk", "thin", "extended")}
        if "v1" in methods:
            w = H.WEIGHTS
            v1 = (w["trend"] * parts["p_trend"] + w["rs"] * rs + w["volume"] * parts["p_volume"] + w["setup"] * parts["p_setup"]
                  + w["risk"] * parts["p_risk"] - 5 * parts["thin"].astype(float))
            out["v1"] = v1.where(v1_ok, v1.clip(upper=49)).clip(0, 100)
        if "quant" in methods:
            out["quant"] = self._composite(groups, {g: DEFAULT_WEIGHTS for g in REGIMES}, None, long_ok)
        if "adaptive" in methods:
            state = state if state is not None else self.market_state()
            out["adaptive"] = self._composite(groups, weights or load_weights(), state["regime"], long_ok)
        if "ml" in methods:
            model = model if model is not None else load_model()
            if model and model.get("status") == "active":
                out["ml"] = self.ml_scores(model, groups, state).where(long_ok, lambda f: f.clip(upper=49))
        return out, groups

    def _composite(self, groups, weights, regime, long_ok):
        """Weighted average of the group ranks; the weights by regime (a Series on the index) or one set for all."""
        total = None
        for g, frame in groups.items():
            if regime is None:
                w = pd.Series(weights["bull"][g], index=self.index)
            else:
                w = regime.map(lambda r: weights.get(r, weights["bull"]).get(g, DEFAULT_WEIGHTS[g])).astype(float)
            term = frame.mul(w, axis=0)
            total = term if total is None else total + term
        total = total.where(long_ok, total.clip(upper=49))
        return total.clip(0, 100)

    def ml_features(self, groups, state):
        """The model's inputs on every (date, stock): the factors, the group ranks and the market state."""
        state = state if state is not None else self.market_state()
        cols = {}
        for name in ML_FEATURES:
            if name in groups:
                cols[name] = groups[name]
            elif name in ("trend_63", "vol_pct", "breadth50", "risk_on", "dispersion"):
                cols[name] = pd.DataFrame({s: state[name] for s in self.syms}, index=self.index)
            elif name == "regime_code":
                code = state["regime"].map({r: i for i, r in enumerate(REGIMES)}).astype(float)
                cols[name] = pd.DataFrame({s: code for s in self.syms}, index=self.index)
            elif name in ("setup_pts", "rr_pts"):
                cols[name] = self.col("p_setup" if name == "setup_pts" else "p_risk", "parts")
            else:
                cols[name] = _pct_rank(self.col(name))
        return cols

    def ml_scores(self, model, groups, state=None):
        cols = self.ml_features(groups, state)
        feats = model["features"]
        T, N = len(self.index), len(self.syms)
        X = np.stack([cols[f].to_numpy(float).reshape(-1) for f in feats], axis=1)
        raw = predict_raw(model, X).reshape(T, N)
        frame = pd.DataFrame(raw, index=self.index, columns=self.syms)
        return _pct_rank(frame)

    # ---- the explanation of one stock's score on one session
    def explain(self, sym, method, when=None, groups=None, weights=None, state=None):
        """[(group, rank 0-100, weight, contribution), ...] and the factors behind each group with their ranks, for the reader."""
        groups = groups or self.group_ranks()
        t = self.index[-1] if when is None else pd.Timestamp(when)
        regime = (state if state is not None else self.market_state())["regime"].get(t, "bull")
        w = DEFAULT_WEIGHTS if method == "quant" else (weights or load_weights()).get(regime, DEFAULT_WEIGHTS)
        rows = []
        for g, (en, ar, members) in GROUPS.items():
            rk = float(groups[g].at[t, sym]) if sym in groups[g] else np.nan
            facs = []
            for name, sign in members:
                src = self.col(name) if name not in ("setup_pts", "rr_pts") else self.col("p_setup" if name == "setup_pts" else "p_risk", "parts")
                val = float(src.at[t, sym]) if sym in src else np.nan
                pr = float(_pct_rank(src * sign).at[t, sym]) if sym in src else np.nan
                facs.append({"factor": name, "value": val, "rank": pr, "label": FACTOR_LABEL.get(name, (name, name))})
            rows.append({"group": g, "label": (en, ar), "rank": rk, "weight": float(w.get(g, 0)), "contribution": rk * float(w.get(g, 0)) if np.isfinite(rk) else np.nan,
                         "factors": facs})
        return rows


# ---------------------------------------------------------------- 4) the research's artefacts: weights and the model
ML_FEATURES = ["momentum", "trend", "volume", "risk", "setup", "ramom_126", "resid_126", "er_63", "vol_63", "mdd_126", "ud_50",
               "dvol_trend", "autocorr_63", "z_50", "brk_str", "trend_63", "vol_pct", "breadth50", "risk_on", "dispersion", "regime_code"]


def load_weights(path=WEIGHTS_FILE):
    """{regime: {group: weight}} measured in the research (hunter3_weights.json); the defaults for every regime without one."""
    try:
        with open(path, encoding="utf-8") as f:
            w = json.load(f)
        out = {r: dict(DEFAULT_WEIGHTS) for r in REGIMES}
        for r, d in (w.get("weights") or {}).items():
            if r in out and isinstance(d, dict):
                out[r].update({g: float(v) for g, v in d.items() if g in GROUPS})
        return out
    except Exception:
        return {r: dict(DEFAULT_WEIGHTS) for r in REGIMES}


def load_model(path=MODEL_FILE):
    try:
        with open(path, encoding="utf-8") as f:
            m = json.load(f)
        for tr in m.get("trees", []):
            for k in ("feature", "left", "right"):
                tr[k] = np.asarray(tr[k], int)
            tr["thr"], tr["value"] = np.asarray(tr["thr"], float), np.asarray(tr["value"], float)
            tr["leaf"], tr["miss_left"] = np.asarray(tr["leaf"], bool), np.asarray(tr["miss_left"], bool)
        return m
    except Exception:
        return None


def predict_raw(model, X):
    """The raw (pre-link) output of an exported gradient-boosting model for each row of X (mlbots' tree format)."""
    X = np.asarray(X, float)
    n = len(X)
    raw = np.full(n, float(model.get("baseline", 0.0)))
    if not n:
        return raw
    ar = np.arange(n)
    for tr in model["trees"]:
        node = np.zeros(n, int)
        for _ in range(int(tr["depth"]) + 1):
            leaf = tr["leaf"][node]
            if leaf.all():
                break
            x = X[ar, tr["feature"][node]]
            go_left = np.where(np.isnan(x), tr["miss_left"][node], x <= tr["thr"][node])
            node = np.where(leaf, node, np.where(go_left, tr["left"][node], tr["right"][node]))
        raw += tr["value"][node]
    return raw


def export_hgb(clf, features, **meta):
    """A fitted scikit-learn HistGradientBoosting model (classifier or regressor) -> the JSON model of this module."""
    trees = []
    for it in clf._predictors:
        nd = it[0].nodes
        trees.append({"feature": nd["feature_idx"].astype(int).tolist(), "thr": nd["num_threshold"].astype(float).tolist(),
                      "left": nd["left"].astype(int).tolist(), "right": nd["right"].astype(int).tolist(),
                      "leaf": nd["is_leaf"].astype(bool).tolist(), "miss_left": nd["missing_go_to_left"].astype(bool).tolist(),
                      "value": nd["value"].astype(float).tolist(), "depth": int(nd["depth"].max())})
    base = float(np.ravel(clf._baseline_prediction)[0])
    return {"features": list(features), "baseline": base, "trees": trees, **meta}


# ---------------------------------------------------------------- 5) the portfolio
def _corr_matrix(closes, syms, t, window=63):
    """Pairwise correlation of the daily returns of syms over the window ending at t."""
    c = closes[syms].loc[:t].tail(window + 1)
    r = c.pct_change(fill_method=None).dropna(how="all")
    return r.corr()


def build_portfolio(cands, panel, when=None, capital=100_000.0, risk_pct=0.75, max_pos=8, sector_cap=2, max_corr=0.75,
                    exposure=None, regime="bull", drawdown=0.0, target_vol=18.0, max_weight=20.0):
    """Which of the ranked candidates to hold and how much of each.
    cands: a DataFrame (Symbol, Score, Entry, Stop, Target, Sector, ATR %, vol_63, beta) best first.
    Each position is sized by the smaller of: the risk budget (risk_pct of the capital lost at the stop), the volatility budget
    (target_vol / N of annualised volatility per position) and max_weight; the whole book by the regime's exposure cap, cut in
    half after a drawdown over 10%. A candidate correlated over max_corr with one already chosen, or over the sector cap, is
    skipped (the same market exposure twice). Returns (positions DataFrame, summary dict)."""
    t = panel.index[-1] if when is None else pd.Timestamp(when)
    cap = EXPOSURE.get(regime, 0.5) if exposure is None else exposure
    brake = 0.5 if drawdown <= -10 else 1.0
    cap *= brake
    budget = capital * cap
    chosen, rows, secs, skipped = [], [], {}, []
    closes = panel.closes()
    for _, r in cands.iterrows():
        if len(rows) >= max_pos or budget <= 0:
            break
        sym, sec = r["Symbol"], r.get("Sector") or "?"
        entry, stop = float(r["Entry"]), float(r["Stop"])
        if not (np.isfinite(entry) and np.isfinite(stop) and 0 < stop < entry):
            continue
        if secs.get(sec, 0) >= sector_cap:
            skipped.append((sym, "sector"))
            continue
        if chosen and sym in closes:
            cm = _corr_matrix(closes, chosen + [sym], t)
            mx = float(cm.loc[sym, chosen].max()) if sym in cm else 0.0
            if np.isfinite(mx) and mx > max_corr:
                skipped.append((sym, f"corr {mx:.2f}"))
                continue
        vol = float(r.get("vol_63", np.nan))
        per_risk = capital * risk_pct / 100 / (entry - stop)
        per_vol = (capital * (target_vol / max_pos) / vol / entry) if np.isfinite(vol) and vol > 0 else np.inf
        per_w = capital * max_weight / 100 / entry
        shares = int(max(0, min(per_risk, per_vol, per_w, budget / entry)))
        if shares <= 0:
            continue
        cost = shares * entry
        rows.append({"Symbol": sym, "Sector": sec, "Shares": shares, "Entry": entry, "Stop": stop, "Target": float(r.get("Target", np.nan)),
                     "Notional": cost, "Weight %": cost / capital * 100, "Risk $": shares * (entry - stop),
                     "Risk %": shares * (entry - stop) / capital * 100, "Vol %": vol, "Beta": float(r.get("beta", np.nan)),
                     "Score": float(r["Score"])})
        chosen.append(sym)
        secs[sec] = secs.get(sec, 0) + 1
        budget -= cost
    pos = pd.DataFrame(rows)
    inv = float(pos["Notional"].sum()) if len(pos) else 0.0
    beta = float((pos["Beta"].fillna(1.0) * pos["Weight %"]).sum() / 100) if len(pos) else 0.0
    risk_sum = float(pos["Risk %"].sum()) if len(pos) else 0.0
    stress = {f"spy_{s}": round(-beta * s, 2) for s in (5, 10, 20)}     # a market fall of s% -> the book's modelled move (%)
    summary = {"invested_pct": inv / capital * 100, "cash": capital - inv, "exposure_cap_pct": cap * 100, "regime": regime,
               "drawdown_brake": brake < 1, "positions": len(pos), "book_beta": beta, "risk_at_stops_pct": risk_sum,
               "stress": stress, "skipped": skipped, "live_orders": False}
    return pos, summary


# ---------------------------------------------------------------- the scan of today (the page)
def scan(prices, bench, vix=None, sectors=None, names=None, earnings=None, today=None, methods=("v1", "quant", "adaptive", "ml"),
         weights=None, model=None, thin=20e6):
    """Today's opportunities: a DataFrame (one row per stock with a live long setup, the chosen method's score first), the
    market state (last row and the whole series), the group ranks and the panel itself (for the detail views).
    earnings: {symbol: date} within the next days; today: the date for the earnings count."""
    panel = Panel(prices, bench, vix, sectors)
    if not panel.syms:
        return pd.DataFrame(), None, {}, panel
    state = panel.market_state()
    scores, groups = panel.scores(methods, weights, model, state)
    t = panel.index[-1]
    rows = []
    for sym in panel.syms:
        f, s, p = panel.feats[sym], panel.setups[sym], panel.parts[sym]
        if t not in s.index:
            continue
        st = s.loc[t]
        key = st["key"] if isinstance(st["key"], str) else None
        d = panel.frames[sym]
        last = d.index[-1]
        stale = (t - last).days > 5
        flags = []
        edays = None
        ed = (earnings or {}).get(sym)
        if ed is not None and today is not None:
            edays = int(np.busday_count(pd.Timestamp(today).date(), pd.Timestamp(ed).date()))
            if 0 <= edays <= 5:
                flags.append("earnings")
        fl = f.loc[t] if t in f.index else f.iloc[-1]
        if fl["dollar_20"] < thin:
            flags.append("thin")
        if fl["ext_atr"] > 3:
            flags.append("extended")
        if fl["atr_pct"] > 8:
            flags.append("volatile")
        if bool(fl["liq_det"]):
            flags.append("liquidity")
        if stale:
            flags.append("stale")
        row = {"Symbol": sym, "Name": (names or {}).get(sym) or H.U.name_of(sym), "Sector": (sectors or {}).get(sym) or H.U.sector_of(sym),
               "Setup": key, "Status": st["status"] if key else None, "Tier": st["status"] if key else None, "Age": st["age"], "Setups": st["setups"], "Side": st["side"] if key else 0,
               "Entry": st["entry"], "Stop": st["stop"], "Target": st["target"], "R:R": p.at[t, "rr"] if t in p.index else np.nan,
               "Price": float(d["Close"].iloc[-1]), "Chg %": float(d["Close"].iloc[-1] / d["Close"].iloc[-2] - 1) * 100,
               "ATR %": fl["atr_pct"], "$Vol": fl["dollar_20"], "vol_63": fl["vol_63"], "beta": fl["beta_252"], "mdd_126": fl["mdd_126"],
               "cvar_95": fl["cvar_95"], "var_95": fl["var_95"], "corr_63": fl["corr_63"], "ramom_126": fl["ramom_126"], "rs_126": fl["rs_126"],
               "resid_126": fl["resid_126"], "ret_21": fl["ret_21"], "ret_63": fl["ret_63"], "ret_252": fl["ret_252"], "dist_hi": fl["dist_hi"],
               "rvol_20": fl["rvol_20"], "ud_50": fl["ud_50"], "vol_shock": fl["vol_shock"], "er_63": fl["er_63"], "z_50": fl["z_50"],
               "Earnings": edays, "Flags": ",".join(flags), "RS": float(panel.rs_rating().at[t, sym]),
               "Hold": H.SETUPS[key][5] if key and H.SETUPS[key][5] else (20 if key else None)}
        for m, frame in scores.items():
            v = float(frame.at[t, sym]) if sym in frame else np.nan
            if "earnings" in flags:
                v -= 8
            row[f"score_{m}"] = v
        for g in GROUPS:
            row[f"g_{g}"] = float(groups[g].at[t, sym])
        rows.append(row)
    res = pd.DataFrame(rows)
    if res.empty:
        return res, state, groups, panel
    first = next((m for m in ("adaptive", "quant", "v1") if f"score_{m}" in res), None)
    if first:
        res = res.sort_values([f"score_{first}", "RS"], ascending=False).reset_index(drop=True)
    return res, state, groups, panel


def grade(score):
    return H.grade(score)


def why(row, panel, method, groups, state, ar=False):
    """A plain-words case for one opportunity: what the score stands on, what would invalidate it, what is uncertain."""
    sym = row["Symbol"]
    ex = panel.explain(sym, method if method in ("quant", "adaptive") else "quant", None, groups, None, state)
    strong = [e for e in ex if np.isfinite(e["rank"]) and e["rank"] >= 70]
    weak = [e for e in ex if np.isfinite(e["rank"]) and e["rank"] <= 35]
    lab = lambda e: e["label"][1 if ar else 0]
    L = lambda en, a: a if ar else en
    for_ = [lab(e) for e in sorted(strong, key=lambda e: -e["rank"])]
    against = [lab(e) for e in sorted(weak, key=lambda e: e["rank"])]
    inval = []
    if np.isfinite(row.get("Stop", np.nan)):
        inval.append(L(f"a close under the stop at {row['Stop']:.2f}", f"إغلاق تحت الوقف عند {row['Stop']:.2f}"))
    inval.append(L("the market regime turning to bear or stress", "تحول حالة السوق إلى هابطة أو مضطربة"))
    if row.get("Setup"):
        inval.append(L(f"the {H.SETUPS[row['Setup']][0].lower()} setup failing (price back inside its base)",
                       f"فشل فرصة {H.SETUPS[row['Setup']][1]} (رجوع السعر داخل قاعدته)"))
    unsure = []
    flags = str(row.get("Flags") or "").split(",")
    if "earnings" in flags:
        unsure.append(L("earnings within 5 sessions: a gap either way", "أرباح خلال 5 جلسات: فجوة محتملة في الاتجاهين"))
    if "thin" in flags or "liquidity" in flags:
        unsure.append(L("thin or fading liquidity: fills may slip", "سيولة ضعيفة أو متراجعة: التنفيذ قد ينزلق"))
    if "volatile" in flags:
        unsure.append(L("very wide daily range: the stop is far or the size small", "مدى يومي واسع جداً: الوقف بعيد أو الحجم صغير"))
    if not np.isfinite(row.get("beta", np.nan)):
        unsure.append(L("too little history for beta and correlation", "تاريخ أقصر من اللازم لبيتا والارتباط"))
    unsure.append(L("fundamentals are today's snapshot, not point-in-time", "الأساسيات لقطة اليوم وليست كما كانت تاريخياً"))
    return {"for": for_, "against": against, "invalidation": inval, "uncertain": unsure, "groups": ex}
