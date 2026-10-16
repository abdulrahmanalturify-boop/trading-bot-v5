"""TURA Hunter V3 Alpha Lab — isolated research engine, no live trading.

This module does not mutate hunter.py or paperbots.py. The candidate AI-free
ridge forecaster is trained only on realized outcomes whose exit dates precede
the scan date. Its validation samples are purged and chronologically later than
training samples. No probability claims are made. A negative validation
information coefficient disables its influence on live ranks.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import hunter as H
import universe as U


BUILD = "v3-alpha-20261016"
HORIZON = 20
FEATURES = ("excess_21", "excess_63", "trend_100", "vol_20",
            "drawdown_63", "ema_diff", "rvol_20", "reversal_5", "market_trend")
COLUMNS = ("Symbol", "Name", "Sector", "Score", "V1 Score", "Alpha %",
           "Rank", "Setup", "Status", "Entry", "Stop", "Target", "R:R",
           "ATR %", "$Vol", "Risk Flag", "Model Active", "Exposure", "Side")
MIN_HISTORY = 260


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


def _fit(train, y, alpha=80.0):
    med = np.median(train, axis=0)
    scale = np.std(train, axis=0)
    scale = np.where(scale < 1e-6, 1.0, scale)
    z = np.clip((train - med) / scale, -5, 5)
    # Intercept is unpenalized. All numeric features are trained on past data.
    zm = z.mean(axis=0)
    ym = y.mean()
    x = z - zm
    coef = np.linalg.solve(x.T @ x + alpha * np.eye(x.shape[1]), x.T @ (y - ym))
    return {"med": med, "scale": scale, "zm": zm, "coef": coef, "ym": float(ym)}


def _predict(model, data):
    z = np.clip((data - model["med"]) / model["scale"], -5, 5)
    return model["ym"] + (z - model["zm"]) @ model["coef"]


def train(prices, benchmark, cutoff=None, min_training=150, stride=10):
    """Fit pooled stock returns and hold out the most recent 25% by time.

    Only use labels whose horizon has fully expired by \`cutoff\`. Purge 20
    sessions around the train/validation boundary to prevent overlap.
    A negative or meaningless holdout IC disables the predictive overlay;
    the model is still returned for transparent diagnostics.
    """
    market = _clean(benchmark, cutoff)
    if market is None:
        return None, {"status": "no_benchmark", "n": 0}
    rows, labels, dates = [], [], []
    for sym, raw in prices.items():
        d = _clean(raw, cutoff)
        if d is None:
            continue
        x, y = features_for(d, market)
        good = np.flatnonzero(x.notna().all(axis=1).to_numpy() & y.notna().to_numpy())
        for i in good[::max(1, int(stride))]:
            rows.append(x.iloc[i].to_numpy(dtype=float))
            labels.append(float(np.clip(y.iloc[i], -0.75, 0.75)))
            dates.append(x.index[i])
    if len(rows) < min_training + 60:
        return None, {"status": "insufficient_training_data", "n": len(rows)}
    x = np.asarray(rows, float)
    y = np.asarray(labels, float)
    ds = pd.DatetimeIndex(dates)
    # The split is by distinct date, NOT random stock rows.
    unique = ds.unique().sort_values()
    boundary = unique[max(1, int(len(unique) * 0.75))]
    cutoff_training = boundary - pd.offsets.BDay(HORIZON)
    fit_mask = (ds < cutoff_training)
    val_mask = (ds >= boundary)
    if fit_mask.sum() < min_training or val_mask.sum() < 40:
        return None, {"status": "insufficient_validation_data", "n": int(len(x))}
    fitted = _fit(x[fit_mask], y[fit_mask])
    pred = _predict(fitted, x[val_mask])
    truth = y[val_mask]
    ic = float(np.corrcoef(pred, truth)[0, 1]) if pred.std() > 1e-8 and truth.std() > 1e-8 else np.nan
    mae = float(np.mean(np.abs(pred - truth)))
    benchmark_mae = float(np.mean(np.abs(truth - np.mean(y[fit_mask]))))
    # Simple baseline must be beaten on chronological held-out outcomes.
    reliable = bool(np.isfinite(ic) and ic > .03 and mae < benchmark_mae and val_mask.sum() >= 60)
    # Fit after validation ONLY with outcomes available by scan cutoff.
    deployed = _fit(x, y) if reliable else None
    stats = {"status": "active" if reliable else "rejected_by_validation",
             "n": int(len(x)), "fit_n": int(fit_mask.sum()), "validation_n": int(val_mask.sum()),
             "holdout_ic": round(ic, 4) if np.isfinite(ic) else None,
             "holdout_mae_pct": round(100 * mae, 2),
             "naive_mae_pct": round(100 * benchmark_mae, 2),
             "horizon_sessions": HORIZON, "purge_sessions": HORIZON,
             "calibration": "No calibrated probabilities. 20-session benchmark-excess return."}
    return deployed, stats


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


def scan(prices, benchmark, cutoff=None, sectors=None, earnings=None, thin=20e6):
    """Full isolated V3 scan. Existing V1 scanning rules are READ only."""
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
    rank = []
    for row in out.itertuples(index=False):
        d = clean[row.Symbol]
        last = d.index.max()
        staleness = (market.index.max() - last).days
        rowdata = candidate.loc[candidate["Symbol"] == row.Symbol].iloc[0]
        q = _technical_quality(rowdata, mood)
        flags = str(rowdata["Flags"]).strip(",")
        if staleness > 5:
            flags = (flags + ",stale_data").strip(",")
        if np.isfinite(rowdata["ATR %"]) and rowdata["ATR %"] > 12:
            flags = (flags + ",extreme_volatility").strip(",")
        if float(rowdata["$Vol"]) < thin:
            flags = (flags + ",illiquid").strip(",")
        alpha = np.nan
        if model is not None:
            feat = features_for(d, market)[0].iloc[-1]
            if feat.notna().all():
                alpha = float(np.clip(100 * _predict(model, feat.to_numpy(float)[None, :])[0], -15, 15))
        score = .75 * float(rowdata["Score"]) + .25 * q
        if np.isfinite(alpha):
            score = .55 * float(rowdata["Score"]) + .20 * q + .25 * np.clip(50 + 3 * alpha, 0, 100)
        if "stale_data" in flags or "extreme_volatility" in flags or "illiquid" in flags:
            score = min(score, 49.0)
        if rowdata["Side"] <= 0:
            score = min(score, 49.0)
        # Penalties already reflected in baseline V1 score; do not double count.
        rank.append((row.Symbol, score, alpha, flags))
    ranks = pd.DataFrame(rank, columns=["Symbol", "Rank", "Alpha %", "Risk Flag"])
    out = out.drop(columns=["Alpha %", "Risk Flag"]).merge(ranks, on="Symbol", validate="one_to_one")
    out = out.sort_values(["Rank", "V1 Score"], ascending=False).reset_index(drop=True)
    return out, info, {"mood": mood, "date": str(market.index[-1].date()),
                        "universe": int(len(clean)), "eligible_longs": int(((out["Side"] > 0) & (out["Rank"] >= 50)).sum())}


def allocate(ranked, capital=100_000, risk_per_trade_pct=.5, max_positions=5,
             max_position_pct=25., sector_limit=2, mode="mixed"):
    """Research-only unlevered allocation respecting absolute cash/exposure caps.

    A protective stop is a sizing input, not a guarantee of a fill or capped loss.
    No trades are sent to a brokerage.
    """
    if not np.isfinite(capital) or capital <= 0 or not (0 < risk_per_trade_pct <= 5):
        raise ValueError("capital and risk_per_trade_pct must be positive, risk <=5%")
    if not (1 <= int(max_positions) <= 50) or not (0 < max_position_pct <= 100):
        raise ValueError("invalid position limits")
    exposure = 1.0 if mode == "on" else .65 if mode == "mixed" else .25
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
        "positions": len(rows), "mode": mode,
        "live_orders": False,
    }
