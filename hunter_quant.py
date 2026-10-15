"""Transparent, point-in-time quantitative overlays for the TURA Opportunity Hunter.

No paid AI API or fitted model is required. Factors are *heuristics*, NOT
calibrated win probabilities. Every component uses information observable
as of the last bar of the provided history, and is neutral when unavailable.

The 63-session window is deliberate: it keeps the default full-universe scan
inexpensive while measuring realized downside, path efficiency, relative
returns and volatility shock. Raw inputs may still contain vendor revisions,
adjustments and survivorship bias; validate any strategy out-of-sample.
"""
import numpy as np
import pandas as pd


WINDOW = 63
PARTS = ("risk_adj", "consistency", "efficiency", "drawdown", "relative")
LABELS = {
    "risk_adj": ("Risk-adjusted momentum", "الزخم المعدل بالمخاطرة"),
    "consistency": ("Return persistence", "استمرارية العائد"),
    "efficiency": ("Price path efficiency", "كفاءة المسار السعري"),
    "drawdown": ("Drawdown resilience", "مقاومة التراجع"),
    "relative": ("Benchmark-relative strength", "التفوق على المؤشر"),
}
FACTOR_WEIGHTS = {"risk_adj": .30, "consistency": .20, "efficiency": .15,
                  "drawdown": .20, "relative": .15}


def _clip100(v):
    return float(np.clip(v, 0.0, 100.0)) if np.isfinite(v) else 50.0


def _benchmark_close(market, index):
    """Align to the stock's calendar using only benchmark observations <= date."""
    if market is None or not isinstance(market, pd.DataFrame) or "Close" not in market:
        return None
    s = pd.to_numeric(market["Close"], errors="coerce").dropna()
    if s.empty:
        return None
    try:
        dates = pd.to_datetime(s.index)
        if dates.tz is not None:
            dates = dates.tz_convert("UTC").tz_localize(None)
        ix = pd.to_datetime(index)
        if ix.tz is not None:
            ix = ix.tz_convert("UTC").tz_localize(None)
        s.index = dates
        s = s[~s.index.duplicated(keep="last")].sort_index()
        # Limit stale quotes; never backward-fill from future benchmark values.
        aligned = s.reindex(ix, method="ffill", limit=3)
        return pd.Series(aligned.to_numpy(dtype=float), index=index)
    except (TypeError, ValueError, KeyError):
        return None


def assess(df, benchmark=None):
    """Calculate the last-date quant overlay from daily adjusted OHLCV.

    A 50/100 fallback is deliberately neutral; a missing series never earns
    a 100. Returns the overall score, component scores, and diagnostics.
    IR is diagnostic (annualised information ratio), not the score itself.
    """
    empty = {
        "score": 50.0, "quality": "insufficient", "bars": 0,
        "volatility_pct": np.nan, "downside_vol_pct": np.nan,
        "max_drawdown_pct": np.nan, "beta": np.nan,
        "excess_return_pct": np.nan, "information_ratio": np.nan,
        "efficiency_pct": np.nan, "positive_weeks_pct": np.nan,
        "volatility_shock": False,
        "parts": {p: 50.0 for p in PARTS},
    }
    if df is None or not isinstance(df, pd.DataFrame) or "Close" not in df:
        return empty
    price = pd.to_numeric(df["Close"], errors="coerce")
    price = price.replace([np.inf, -np.inf], np.nan)
    if len(price) < WINDOW + 1:
        return empty
    close = price.iloc[-(WINDOW + 1):].to_numpy(dtype=float)
    if not np.isfinite(close).all() or (close <= 0).any():
        return empty
    daily = close[1:] / close[:-1] - 1.0
    if not np.isfinite(daily).all():
        return empty
    std = float(daily.std(ddof=1))
    ann_vol = std * np.sqrt(252.0)
    neg = np.minimum(daily, 0.0)
    downside = float(np.sqrt(np.mean(neg ** 2) * 252.0))
    cum = close / close[0]
    dd = float(np.min(cum / np.maximum.accumulate(cum) - 1.0))
    move = abs(close[-1] - close[0])
    path = float(np.abs(np.diff(close)).sum())
    eff = move / path if path > 0 else 0.0
    # 12 disjoint five-day returns, evaluated only at the window endpoint.
    weeks = np.array([close[k] / close[k - 5] - 1 for k in range(5, 61, 5)], dtype=float)
    positive = float((weeks > 0).mean())
    three_month = float(close[-1] / close[0] - 1.0)
    # Realized 63-day Sharpe-style ratio (risk free excluded), saturating to avoid domination.
    realized_ratio = (three_month / (ann_vol * np.sqrt(WINDOW / 252.0))) if ann_vol > 1e-8 else 0.0
    risk_adj_pts = _clip100(50 + 25 * realized_ratio)
    consistency_pts = _clip100(100 * positive)
    efficiency_pts = _clip100(100 * eff / 0.45)
    drawdown_pts = _clip100(100 * (1 + dd / 0.30))

    beta = np.nan
    excess_pct = np.nan
    ir = np.nan
    relative_pts = 50.0
    aligned = _benchmark_close(benchmark, price.iloc[-(WINDOW + 1):].index)
    if aligned is not None:
        b = aligned.to_numpy(dtype=float)
        if np.isfinite(b).all() and (b > 0).all():
            br = b[1:] / b[:-1] - 1.0
            bvar = float(np.var(br, ddof=1))
            beta = float(np.cov(daily, br, ddof=1)[0, 1] / bvar) if bvar > 1e-12 else np.nan
            excess_pct = 100 * (three_month - (b[-1] / b[0] - 1))
            active = daily - br
            tracking = float(active.std(ddof=1))
            ir = float(active.mean() / tracking * np.sqrt(252)) if tracking > 1e-9 else np.nan
            # Includes the relative return and IR; neither is a success probability.
            relative_pts = _clip100(50 + 1.5 * excess_pct + (10 * np.clip(ir, -2, 2) if np.isfinite(ir) else 0))

    components = {"risk_adj": risk_adj_pts, "consistency": consistency_pts,
                  "efficiency": efficiency_pts, "drawdown": drawdown_pts,
                  "relative": relative_pts}
    score = sum(FACTOR_WEIGHTS[p] * components[p] for p in PARTS)
    recent_vol = float(daily[-20:].std(ddof=1))
    shock = bool(std > 1e-8 and recent_vol > 1.8 * std and ann_vol > 0.25)
    if shock:
        score = max(0, score - 8)
    return {
        "score": round(_clip100(score), 2), "quality": "ok",
        "bars": int(WINDOW + 1), "volatility_pct": round(ann_vol * 100, 2),
        "downside_vol_pct": round(downside * 100, 2),
        "max_drawdown_pct": round(dd * 100, 2),
        "beta": round(beta, 3) if np.isfinite(beta) else np.nan,
        "excess_return_pct": round(excess_pct, 2) if np.isfinite(excess_pct) else np.nan,
        "information_ratio": round(ir, 3) if np.isfinite(ir) else np.nan,
        "efficiency_pct": round(eff * 100, 2),
        "positive_weeks_pct": round(positive * 100, 2),
        "volatility_shock": shock, "parts": {p: round(v, 2) for p, v in components.items()},
    }


def sector_scores(entries, min_sector_size=3):
    """Rank sectors on observable 3-month performance and 50d breadth.

    A sector-only/custom scan returns neutral (50) because it has no meaningful
    cross-sector comparison. Treat a sector with fewer than 3 stocks as neutral.
    entries: iterable of (symbol, sector, three_month_return_percent, above50).
    """
    groups = {}
    symbols = []
    for symbol, sector, ret, above in entries:
        sector = str(sector or "")
        symbols.append((symbol, sector))
        if sector and np.isfinite(ret):
            groups.setdefault(sector, []).append((float(ret), bool(above)))
    good = {k: v for k, v in groups.items() if len(v) >= min_sector_size}
    if len(good) < 3:
        return {sym: 50.0 for sym, _ in symbols}
    raw = {k: .75 * float(np.median([x[0] for x in v])) +
              25 * float(np.mean([x[1] for x in v])) for k, v in good.items()}
    ranked = pd.Series(raw).rank(method="average", pct=True) * 100
    return {sym: round(float(ranked[sector]), 1) if sector in ranked else 50.0
            for sym, sector in symbols}
