"""TURA Hunter V3 Alpha Lab — isolated research engine, no live trading.

This module does not mutate hunter.py or paperbots.py. The candidate AI-free
ridge forecaster is trained only on realized outcomes whose exit dates precede
the scan date. Its validation samples are purged and chronologically later than
training samples. No probability claims are made. A negative validation
information coefficient disables its influence on live ranks.

The rank is fully quantitative and statistical: four factors (momentum, trend,
low risk, short-term reversal) ranked as percentiles across the scanned stocks,
blended with the validated forecast's percentile. The hunter's technical score,
setups and levels are kept as information only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import hunter as H
import universe as U


BUILD = "23.4.57"
HORIZON = 20
FEATURES = ("excess_21", "excess_63", "trend_100", "vol_20",
            "drawdown_63", "ema_diff", "rvol_20", "reversal_5", "market_trend")
COLUMNS = ("Symbol", "Name", "Sector", "Score", "V1 Score", "Alpha %",
           "Rank", "Setup", "Status", "Entry", "Stop", "Target", "R:R",
           "ATR %", "$Vol", "Risk Flag", "Model Active", "Exposure", "Side")
MIN_HISTORY = 260
# The rank is fully quantitative: statistical factors ranked across the scanned stocks, plus the validated forecast.
# Each factor: (column, the features it averages, +1 = higher is better / -1 = lower is better). Fixed weights, not fitted.
FACTORS = (("Q Momentum", (("excess_63", 1), ("excess_21", 1)), .35),
           ("Q Trend", (("trend_100", 1), ("ema_diff", 1)), .25),
           ("Q Low Risk", (("vol_20", -1), ("drawdown_63", 1)), .25),
           ("Q Reversal", (("reversal_5", 1),), .15))
FORECAST_WEIGHT = .5                                 # a validated model's share of the rank (see forecast_weight)


def _clean(df, cutoff=None):
    """Historical OHLCV with a strictly past-only cutoff."""
    if not isinstance(df, pd.DataFrame) or not {"Close", "Open", "High", "Low", "Volume"}.issubset(df):
        return None
    d = df.copy()
    d.index = pd.to_datetime(d.index)
    if d.index.tz is not None:
        d.index = d.index.tz_convert("UTC").tz_localize(None)
    d = d[~d.index.duplicated(keep="last")].sort_index()
    d = d.apply(pd.to_numeric, errors="coerce")
    d = d.dropna(subset=["Close", "Open", "High", "Low"])
    d = d[(d[["Close", "Open", "High", "Low"]] > 0).all(axis=1)]
    if cutoff is not None:
        d = d.loc[:pd.Timestamp(cutoff)]
    return d if len(d) >= MIN_HISTORY else None


def features_for(df, benchmark):
    """Daily features from current or past closes; never centered windows."""
    c, b = df["Close"].astype(float), benchmark["Close"].astype(float)
    # Reindex with forward fill only: missing future benchmark bars cannot leak.
    b = b.reindex(c.index, method="ffill", limit=3)
    b = b.where(b > 0)
    r = c.pct_change(fill_method=None)
    bm = b.pct_change(fill_method=None)
    vol = r.rolling(20, min_periods=20).std() * np.sqrt(252)
    v = df["Volume"].astype(float)
    out = pd.DataFrame(index=c.index)
    out["excess_21"] = c.pct_change(21, fill_method=None) - b.pct_change(21, fill_method=None)
    out["excess_63"] = c.pct_change(63, fill_method=None) - b.pct_change(63, fill_method=None)
    out["trend_100"] = c / c.rolling(100, min_periods=100).mean() - 1
    out["vol_20"] = vol
    out["drawdown_63"] = c / c.rolling(63, min_periods=63).max() - 1
    out["ema_diff"] = c.ewm(span=20, adjust=False).mean() / c.ewm(span=50, adjust=False).mean() - 1
    out["rvol_20"] = v / v.shift(1).rolling(20, min_periods=20).mean().replace(0, np.nan) - 1
    out["reversal_5"] = -c.pct_change(5, fill_method=None)
    out["market_trend"] = b / b.rolling(200, min_periods=200).mean() - 1
    # End of the forward 20-session holding period is known ONLY after 20 sessions.
    forward_stock = c.shift(-HORIZON) / c - 1
    forward_index = b.shift(-HORIZON) / b - 1
    label = forward_stock - forward_index
    return out.replace([np.inf, -np.inf], np.nan), label


MODEL_FEATURES = tuple(f for f in FEATURES if f != "market_trend")   # the same for every stock on a day: no use across stocks
MIN_CROSS = 8                                        # stocks a day needs to be ranked against each other
MODEL_STRIDE = 5                                     # a sample every 5 sessions (overlapping 20-session outcomes)
RIDGE_ALPHA = 10.0
# the forecast's weight in the rank by its measured accuracy: "by_accuracy" (validated: half; weak: a quarter; rejected: shown
# but unweighted), "always" (half whatever it measured), "show_only" (never in the rank)
FORECAST_MODE = "by_accuracy"
FORECAST_WEIGHTS = {"active": FORECAST_WEIGHT, "weak": .25, "rejected": 0.0}


def _cs_rank(df, cols):
    """Each column as a centred percentile within its day (-0.5 = the lowest of that day, +0.5 = the highest): the model ranks
    stocks against each other, so a feature's level across time (a bull year, a crash) never enters it."""
    out = df.copy()
    g = out.groupby("date")
    for c in cols:
        out[c] = g[c].rank(pct=True) - 0.5
    return out


def _fit(train, y, alpha=RIDGE_ALPHA):
    """Ridge on centred rank features (already comparable, so no scaling); the intercept is unpenalised."""
    med = np.zeros(train.shape[1])
    scale = np.ones(train.shape[1])
    z = np.asarray(train, float)
    zm = z.mean(axis=0)
    ym = float(np.mean(y))
    x = z - zm
    coef = np.linalg.solve(x.T @ x + alpha * np.eye(x.shape[1]), x.T @ (np.asarray(y, float) - ym))
    return {"med": med, "scale": scale, "zm": zm, "coef": coef, "ym": ym}


def _predict(model, data):
    z = (np.asarray(data, float) - model["med"]) / model["scale"]
    return model["ym"] + (z - model["zm"]) @ model["coef"]


def _panel(prices, market, cutoff, stride):
    """One row per stock and sample day: the model's features, the day, and the outcome (the 20-session excess return and
    its rank within the day). Only days where the outcome is already known by the cutoff."""
    rows = []
    for sym, raw in prices.items():
        d = _clean(raw, cutoff)
        if d is None:
            continue
        x, y = features_for(d, market)
        x = x[list(MODEL_FEATURES)]
        good = np.flatnonzero(x.notna().all(axis=1).to_numpy() & y.notna().to_numpy())
        for i in good[::max(1, int(stride))]:
            rows.append((sym, x.index[i], *x.iloc[i].to_numpy(dtype=float), float(np.clip(y.iloc[i], -0.75, 0.75))))
    if not rows:
        return pd.DataFrame(columns=["sym", "date", *MODEL_FEATURES, "y"])
    df = pd.DataFrame(rows, columns=["sym", "date", *MODEL_FEATURES, "y"])
    n = df.groupby("date")["sym"].transform("size")
    df = df[n >= MIN_CROSS].reset_index(drop=True)
    if df.empty:
        return df
    df = _cs_rank(df, list(MODEL_FEATURES))
    df["y_rank"] = df.groupby("date")["y"].rank(pct=True) - 0.5
    return df


def _ic_series(pred, truth, dates):
    """The rank correlation between the forecast and the outcome within each day."""
    f = pd.DataFrame({"p": pred, "t": truth, "d": dates})
    out = []
    for _, g in f.groupby("d"):
        if len(g) >= MIN_CROSS and g["p"].std() > 1e-9 and g["t"].std() > 1e-9:
            out.append(float(np.corrcoef(g["p"].rank(), g["t"].rank())[0, 1]))      # Spearman, without scipy
    return np.asarray(out, float)


def train(prices, benchmark, cutoff=None, min_training=150, stride=MODEL_STRIDE, folds=3):
    """A cross-sectional model: each day the scanned stocks are ranked against each other on every feature, and ridge regression
    learns which of those ranks go with a better rank of the next 20 sessions' excess return. Validated walking forward: the
    later part of the history is cut into `folds` blocks, each forecast by a model fitted on the days before it (with 20
    sessions purged at the boundary), and the day-by-day rank correlation (IC) of those forecasts is measured. The status says
    how much the forecast earned: "active" (mean IC >= .02 with t >= 2), "weak" (positive but unproven) or "rejected"; the
    forecast is shown in every case, and its weight in the rank follows the status (FORECAST_MODE)."""
    market = _clean(benchmark, cutoff)
    if market is None:
        return None, {"status": "no_benchmark", "n": 0}
    panel = _panel(prices, market, cutoff, stride)
    if len(panel) < min_training + 60:
        return None, {"status": "insufficient_training_data", "n": int(len(panel))}
    x = panel[list(MODEL_FEATURES)].to_numpy(float)
    y = panel["y_rank"].to_numpy(float)
    ds = pd.DatetimeIndex(panel["date"])
    unique = ds.unique().sort_values()
    if len(unique) < 24:
        return None, {"status": "insufficient_validation_data", "n": int(len(x))}
    # walk forward over the later 60% of the days, in blocks
    first = unique[int(len(unique) * 0.4)]
    blocks = np.array_split(unique[unique >= first], max(1, int(folds)))
    ics, val_n, fit_n = [], 0, 0
    for b in blocks:
        if len(b) == 0:
            continue
        purge = b[0] - pd.offsets.BDay(HORIZON)
        fit_mask = ds < purge
        val_mask = (ds >= b[0]) & (ds <= b[-1])
        if fit_mask.sum() < min_training or val_mask.sum() < MIN_CROSS * 2:
            continue
        m = _fit(x[fit_mask], y[fit_mask])
        ics.extend(_ic_series(_predict(m, x[val_mask]), y[val_mask], ds[val_mask]))
        val_n += int(val_mask.sum())
        fit_n = max(fit_n, int(fit_mask.sum()))
    ics = np.asarray(ics, float)
    if len(ics) < 12:
        return None, {"status": "insufficient_validation_data", "n": int(len(x))}
    ic = float(np.mean(ics))
    # the samples overlap (a 20-session outcome every `stride` sessions): the t-statistic counts only the independent ones
    n_eff = max(2.0, len(ics) * min(1.0, stride / HORIZON))
    t = float(ic / (np.std(ics, ddof=1) / np.sqrt(n_eff))) if np.std(ics, ddof=1) > 1e-9 else 0.0
    hit = float(np.mean(ics > 0))
    status = "active" if (ic >= .02 and t >= 2) else ("weak" if ic > 0 else "rejected")
    deployed = _fit(x, y)                            # fitted on every day whose outcome is known by the cutoff
    # the expected excess return behind a forecast rank: the slope of the realised outcome on the model's own forecast
    pred_all = _predict(deployed, x)
    yr = panel["y"].to_numpy(float)
    if pred_all.std() > 1e-9:
        slope = float(np.cov(pred_all, yr)[0, 1] / np.var(pred_all))
        inter = float(yr.mean() - slope * pred_all.mean())
    else:
        slope, inter = 0.0, float(yr.mean())
    deployed["cal"] = (inter, slope)
    stats = {"status": status, "n": int(len(x)), "fit_n": fit_n, "validation_n": val_n, "validation_days": int(len(ics)),
             "holdout_ic": round(ic, 4), "ic_t": round(t, 2), "ic_hit": round(hit, 3),
             "forecast_weight": forecast_weight(status),
             "horizon_sessions": HORIZON, "purge_sessions": HORIZON, "folds": int(folds), "stride": int(stride),
             "calibration": "No calibrated probabilities. 20-session benchmark-excess return, from the forecast rank's slope."}
    return deployed, stats


def forecast_weight(status):
    """The forecast's share of the rank for a model status (see FORECAST_MODE)."""
    if status not in FORECAST_WEIGHTS:
        return 0.0
    if FORECAST_MODE == "always":
        return FORECAST_WEIGHT
    if FORECAST_MODE == "show_only":
        return 0.0
    return FORECAST_WEIGHTS[status]


def forecast(model, feats):
    """The model's forecast for the stocks scanned today ({symbol: features} rows): each feature ranked across them, the ridge
    forecast of the outcome's rank, and the expected 20-session excess return (%) behind it. NaN without a model, for a stock
    missing a feature, or when fewer than MIN_CROSS stocks can be ranked against each other."""
    out = pd.Series(np.nan, index=feats.index, dtype=float)
    if model is None or feats.empty:
        return out
    f = feats[list(MODEL_FEATURES)].astype(float)
    ok = f.notna().all(axis=1)
    if ok.sum() < MIN_CROSS:
        return out
    f = f[ok].copy()
    f["date"] = 0
    z = _cs_rank(f, list(MODEL_FEATURES))[list(MODEL_FEATURES)].to_numpy(float)
    inter, slope = model.get("cal", (0.0, 1.0))
    out[ok] = np.clip(100 * (inter + slope * _predict(model, z)), -15, 15)
    return out


def _technical_quality(row, market_mood):
    """Independent rank overlay: avoid rewarding price spikes as free alpha."""
    atr = float(row.get("ATR %", np.nan))
    rr = float(row.get("R:R", np.nan))
    dist = float(row.get("From high %", np.nan))
    score = 50.0
    if np.isfinite(rr):
        score += np.clip((rr - 1.5) * 8, -16, 16)
    if np.isfinite(atr):
        score += (8 if atr <= 3 else 0) - (16 if atr >= 9 else 0)
    if np.isfinite(dist):
        score += 8 if -12 <= dist <= -1 else (-8 if dist < -40 else 0)
    if market_mood == "off":
        score -= 10
    return float(np.clip(score, 0, 100))


def _pctl(values, sign=1):
    """Cross-sectional percentile, 0-100 (the middle of each rank, so one stock alone sits at 50); NaN stays NaN."""
    v = pd.Series(values, dtype=float) * sign
    n = int(v.notna().sum())
    return (v.rank(method="average") - .5) / n * 100 if n else v


def quant_scores(feats):
    """feats: one row of FEATURES per stock (index = symbol). Returns each factor (0-100) and their weighted blend,
    'Quant Score'; a factor whose inputs are all missing for a stock counts as neutral (50)."""
    out = pd.DataFrame(index=feats.index)
    for name, cols, _ in FACTORS:
        out[name] = pd.concat([_pctl(feats[c], sg) for c, sg in cols], axis=1).mean(axis=1, skipna=True).fillna(50.0)
    out["Quant Score"] = sum(w * out[name] for name, _, w in FACTORS) / sum(w for *_, w in FACTORS)
    return out


def scan(prices, benchmark, cutoff=None, sectors=None, earnings=None, thin=20e6):
    """Full isolated V3 scan. Existing V1 scanning rules are READ only: they give each stock its setup, levels and flags,
    shown for information. The rank itself is fully quantitative: with a validated forecast, half its cross-sectional
    percentile and half the factor blend (Quant Score); without one, the factor blend alone."""
    market = _clean(benchmark, cutoff)
    if market is None:
        return pd.DataFrame(), {"status": "no_benchmark", "n": 0}, {"mood": "unknown"}
    clean = {k: d for k, raw in prices.items() if (d := _clean(raw, cutoff)) is not None}
    if not clean:
        return pd.DataFrame(), {"status": "no_stocks", "n": 0}, {"mood": "unknown"}
    candidate, _ = H.hunt(clean, market, sectors=sectors or {}, earnings=earnings,
                          today=pd.Timestamp(market.index.max()), thin=thin)
    if candidate.empty:
        return pd.DataFrame(), {"status": "no_setups", "n": 0}, {"mood": "unknown"}
    mood = H.regime(candidate, market)["mood"]
    model, info = train(clean, market, cutoff=cutoff)
    out = candidate.copy()
    out["V1 Score"] = out["Score"]
    out["Alpha %"] = np.nan
    out["Model Active"] = bool(model is not None)
    out["Risk Flag"] = ""
    out["Exposure"] = 1.0 if mood == "on" else 0.65 if mood == "mixed" else 0.25
    feats = pd.DataFrame({sym: features_for(clean[sym], market)[0].iloc[-1] for sym in out["Symbol"]}).T
    quant = quant_scores(feats)
    rank = []
    for row in out.itertuples(index=False):
        d = clean[row.Symbol]
        staleness = (market.index.max() - d.index.max()).days
        rowdata = candidate.loc[candidate["Symbol"] == row.Symbol].iloc[0]
        flags = str(rowdata["Flags"]).strip(",")
        if staleness > 5:
            flags = (flags + ",stale_data").strip(",")
        if np.isfinite(rowdata["ATR %"]) and rowdata["ATR %"] > 12:
            flags = (flags + ",extreme_volatility").strip(",")
        if float(rowdata["$Vol"]) < thin:
            flags = (flags + ",illiquid").strip(",")
        rank.append((row.Symbol, flags))
    ranks = pd.DataFrame(rank, columns=["Symbol", "Risk Flag"]).set_index("Symbol")
    ranks = ranks.join(quant)
    ranks["Alpha %"] = forecast(model, feats.loc[ranks.index])
    ranks["Forecast Pctl"] = _pctl(ranks["Alpha %"])
    w = float(info.get("forecast_weight", 0.0) or 0.0) if model is not None else 0.0
    has = ranks["Forecast Pctl"].notna()
    ranks["Rank"] = ranks["Quant Score"]
    ranks.loc[has, "Rank"] = w * ranks.loc[has, "Forecast Pctl"] + (1 - w) * ranks.loc[has, "Quant Score"]
    # Data you cannot trust (stale, extreme volatility, illiquid) caps the rank under the eligibility line.
    capped = ranks["Risk Flag"].str.contains("stale_data|extreme_volatility|illiquid", na=False)
    ranks.loc[capped, "Rank"] = ranks.loc[capped, "Rank"].clip(upper=49.0)
    ranks["Rank"] = ranks["Rank"].clip(0, 100)
    ranks = ranks.reset_index()
    out = out.drop(columns=["Alpha %", "Risk Flag"]).merge(ranks, on="Symbol", validate="one_to_one")
    out = out.sort_values(["Rank", "Quant Score"], ascending=False).reset_index(drop=True)
    return out, info, {"mood": mood, "date": str(market.index[-1].date()),
                        "universe": int(len(clean)), "eligible_longs": int((out["Rank"] >= 50).sum())}


def allocate(ranked, capital=100_000, risk_per_trade_pct=.5, max_positions=5,
             max_position_pct=25., sector_limit=2, mode="mixed", profile="risk_controlled"):
    """Research-only unlevered allocation respecting absolute cash/exposure caps.

    A protective stop is a sizing input, not a guarantee of a fill or capped loss.
    No trades are sent to a brokerage.
    """
    if not np.isfinite(capital) or capital <= 0 or not (0 < risk_per_trade_pct <= 5):
        raise ValueError("capital and risk_per_trade_pct must be positive, risk <=5%")
    if not (1 <= int(max_positions) <= 50) or not (0 < max_position_pct <= 100):
        raise ValueError("invalid position limits")
    if profile not in ("risk_controlled", "return_seeking"):
        raise ValueError("profile must be risk_controlled or return_seeking")
    exposure = (1.0 if mode == "on" else .65 if mode == "mixed" else .25)
    if profile == "return_seeking":
        # Return-seeking != safe. No margin, but can stay 70% exposed in a
        # market risk-off environment and 100% exposed in mixed conditions.
        exposure = 1.0 if mode in ("on", "mixed") else .70
    cash = capital
    sector_count = {}
    rows = []
    for _, row in ranked.iterrows():
        if len(rows) >= int(max_positions):
            break
        if row["Side"] <= 0 or row["Rank"] < 50 or row["Risk Flag"]:
            continue
        sector = str(row["Sector"] or "Unknown")
        if sector_count.get(sector, 0) >= sector_limit:
            continue
        entry = float(row["Entry"])
        stop = float(row["Stop"])
        if not (np.isfinite(entry) and np.isfinite(stop) and 0 < stop < entry):
            continue
        atr = float(row["ATR %"]) if np.isfinite(row["ATR %"]) else 0
        # More volatile stocks: smaller risk fraction; stop already comes from signal.
        adjusted_risk = risk_per_trade_pct * np.clip(3.0 / max(atr, 1.0), .3, 1.0)
        risk_budget = capital * adjusted_risk / 100
        shares = int(min(risk_budget / (entry - stop),
                         capital * max_position_pct / 100 / entry,
                         (capital * exposure - (capital - cash)) / entry,
                         cash / entry))
        if shares <= 0:
            continue
        cost = shares * entry
        rows.append({"Symbol": row["Symbol"], "Sector": sector, "Shares": shares,
                     "Entry": round(entry, 3), "Stop": round(stop, 3),
                     "Notional": round(cost, 2), "Weight %": round(100 * cost / capital, 2),
                     "Stop Risk $": round(shares * (entry - stop), 2),
                     "Alpha %": row["Alpha %"], "Rank": round(float(row["Rank"]), 1)})
        cash -= cost
        sector_count[sector] = sector_count.get(sector, 0) + 1
    return pd.DataFrame(rows), {
        "invested_pct": round(100 * (capital - cash) / capital, 2),
        "remaining_cash": round(cash, 2),
        "market_exposure_cap_pct": round(exposure * 100, 1),
        "positions": len(rows), "mode": mode, "profile": profile,
        "live_orders": False,
    }
