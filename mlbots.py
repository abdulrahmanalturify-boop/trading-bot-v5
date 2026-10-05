"""
mlbots.py - The AI part of the Paper Bots. Each AI bot has its own model: it learned, from every buy signal its strategies
gave on 500+ US stocks in 2012-2019 and how each of those trades ended, which signals tend to end in a win. In a bot with a
model ('ml' = the model's id), a buy signal only counts when the model's chance of a win is at least the model's threshold.
A model with rank = true also fills the free slots with the highest chances first (otherwise the strongest 3 months go
first, as in every bot). A released model file never changes: a retrained model gets a new id, so a running forward test
always keeps the model it started with.

The models are gradient-boosted decision trees trained with scikit-learn in the lab (research/train_ml.py) and saved as
plain JSON (models/<id>.json), so the site needs no machine-learning library: a prediction is a walk down each tree in
numpy. Every feature uses only what was known at the signal's close.
"""
import json
import os
import warnings
from functools import lru_cache

import numpy as np
import pandas as pd

import ta

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "models")
FEATURES = ["r5", "r20", "r60", "r120", "d20", "d50", "d200", "rsi", "atrp", "vol20", "vr", "h252", "clv",
            "spy_d200", "spy_r20", "spy_vol", "rs60", "strat"]
STOCK = FEATURES[:13]
MARKET = ["spy_d200", "spy_r20", "spy_vol"]


# ---------------------------------------------------------------- features
def _naive(ix):
    return ix.tz_localize(None) if getattr(ix, "tz", None) is not None else ix


def stock_features(df):
    """The stock's own features on every day of df (OHLCV), from its own history up to that close."""
    c = df["Close"].astype(float)
    h, lo = df["High"].astype(float), df["Low"].astype(float)
    v = df["Volume"].astype(float) if "Volume" in df else pd.Series(np.nan, index=df.index)
    f = pd.DataFrame(index=df.index)
    for n in (5, 20, 60, 120):
        f[f"r{n}"] = c.pct_change(n)
    for n in (20, 50, 200):
        f[f"d{n}"] = c / c.rolling(n, min_periods=n).mean() - 1
    f["rsi"] = ta.rsi(c, 14) / 100
    f["atrp"] = ta.atr(df, 14) / c
    f["vol20"] = c.pct_change().rolling(20, min_periods=20).std()
    f["vr"] = v / v.rolling(20, min_periods=20).mean().replace(0, np.nan)
    f["h252"] = c / h.rolling(252, min_periods=60).max() - 1
    rng = (h - lo).replace(0, np.nan)
    f["clv"] = (c - lo) / rng
    return f.replace([np.inf, -np.inf], np.nan)


def market_features(spy, idx):
    """The market's features (SPY) on idx: distance from its 200-day average, its last month and its volatility."""
    out = pd.DataFrame(np.nan, index=idx, columns=MARKET)
    if spy is None or getattr(spy, "empty", True):
        return out
    c = spy["Close"].astype(float)
    c = c[~c.index.duplicated(keep="last")].sort_index()
    c.index = _naive(c.index)
    m = pd.DataFrame({"spy_d200": c / c.rolling(200, min_periods=200).mean() - 1, "spy_r20": c.pct_change(20),
                      "spy_vol": c.pct_change().rolling(20, min_periods=20).std()})
    m = m.reindex(_naive(idx), method="ffill")
    m.index = idx
    return m.replace([np.inf, -np.inf], np.nan)


def row_rank(a):
    """Each value's percentile among the stocks of its day (0 = weakest, 1 = strongest; NaN stays NaN)."""
    out = np.full(a.shape, np.nan)
    ok = ~np.isnan(a)
    r = pd.DataFrame(np.where(ok, a, np.nan)).rank(axis=1, pct=True).to_numpy()
    out[ok] = r[ok]
    return out


def features_at(frames, syms, idx, spy, t, j, strat):
    """The feature matrix (rows x FEATURES) for signals on day idx[t[i]] of stock syms[j[i]], by strategy strat[i].
    Only the stocks with a signal get their full features; every stock's 60-day return is needed for the ranking."""
    t, j = np.asarray(t, int), np.asarray(j, int)
    T, N = len(idx), len(syms)
    X = np.full((len(t), len(FEATURES)), np.nan)
    if not len(t):
        return X
    R60 = np.full((T, N), np.nan)
    need = set(j.tolist())
    col = {k: c for c, k in enumerate(FEATURES)}
    for jj, s in enumerate(syms):
        df = frames[s]
        p = idx.get_indexer(df.index)
        if jj not in need:
            R60[p, jj] = df["Close"].astype(float).pct_change(60).to_numpy(float)
            continue
        f = stock_features(df)
        R60[p, jj] = f["r60"].to_numpy(float)
        local = np.full(T, -1)
        local[p] = np.arange(len(p))
        sel = np.flatnonzero(j == jj)
        at = local[t[sel]]
        okr = at >= 0
        vals = f[STOCK].to_numpy(float)
        for c, k in enumerate(STOCK):
            X[sel[okr], col[k]] = vals[at[okr], c]
    m = market_features(spy, idx)[MARKET].to_numpy(float)
    for c, k in enumerate(MARKET):
        X[:, col[k]] = m[t, c]
    X[:, col["rs60"]] = row_rank(R60)[t, j]
    X[:, col["strat"]] = strat
    return X


# ---------------------------------------------------------------- the market model (kind "market")
# It looks at the whole market each day (the S&P 500 and the breadth of the bot's stocks) and gives the chance that the
# next month is good for stocks. Below its threshold the bot buys nothing and sells what it holds (like the 200-day
# market filter, but decided by the model).
MARKET2 = ["spy_d50", "spy_d200", "spy_r20", "spy_r60", "spy_vol20", "spy_volr", "spy_dd", "br50", "br200", "up20", "med_r20",
           "disp20", "hilo"]


def market_panel(frames, syms, idx, spy):
    """The market model's features on every day of idx (from SPY and the stocks of frames)."""
    T, N = len(idx), len(syms)
    A50, A200, U20, R20, HI, LO = (np.full((T, N), np.nan) for _ in range(6))
    for j, s in enumerate(syms):
        df = frames[s]
        p = idx.get_indexer(df.index)
        c = df["Close"].astype(float)
        s50, s200 = c.rolling(50, min_periods=50).mean(), c.rolling(200, min_periods=200).mean()
        r20 = c.pct_change(20)
        mx, mn = c.rolling(252, min_periods=252).max(), c.rolling(252, min_periods=252).min()
        A50[p, j] = np.where(s50.isna(), np.nan, (c > s50).astype(float))
        A200[p, j] = np.where(s200.isna(), np.nan, (c > s200).astype(float))
        R20[p, j] = r20.to_numpy(float)
        U20[p, j] = np.where(r20.isna(), np.nan, (r20 > 0).astype(float))
        HI[p, j] = np.where(mx.isna(), np.nan, (c >= mx).astype(float))
        LO[p, j] = np.where(mn.isna(), np.nan, (c <= mn).astype(float))
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore")                  # a day with no stock in a column gives NaN, not a warning
        f = pd.DataFrame({"br50": np.nanmean(A50, axis=1), "br200": np.nanmean(A200, axis=1), "up20": np.nanmean(U20, axis=1),
                          "med_r20": np.nanmedian(R20, axis=1), "disp20": np.nanstd(R20, axis=1),
                          "hilo": np.nanmean(HI, axis=1) - np.nanmean(LO, axis=1)}, index=idx)
    for k in ("br50", "br200", "up20", "med_r20", "disp20", "hilo"):          # too few stocks that day: unknown
        f.loc[(~np.isnan(R20)).sum(axis=1) < 20, k] = np.nan
    m = pd.DataFrame(np.nan, index=idx, columns=MARKET2[:7])
    if spy is not None and not getattr(spy, "empty", True):
        c = spy["Close"].astype(float)
        c = c[~c.index.duplicated(keep="last")].sort_index()
        c.index = _naive(c.index)
        r = c.pct_change()
        v20, v60 = r.rolling(20, min_periods=20).std(), r.rolling(60, min_periods=60).std()
        sm = pd.DataFrame({"spy_d50": c / c.rolling(50, min_periods=50).mean() - 1, "spy_d200": c / c.rolling(200, min_periods=200).mean() - 1,
                           "spy_r20": c.pct_change(20), "spy_r60": c.pct_change(60), "spy_vol20": v20, "spy_volr": v20 / v60,
                           "spy_dd": c / c.rolling(252, min_periods=60).max() - 1})
        m = sm.reindex(_naive(idx), method="ffill")
        m.index = idx
    out = pd.concat([m, f], axis=1)[MARKET2]
    return out.replace([np.inf, -np.inf], np.nan)


def market_gate(model, frames, syms, idx, spy):
    """(True on the days the market model allows the bot to hold stocks, the model's chance on each day)."""
    X = market_panel(frames, syms, idx, spy)[model["features"]].to_numpy(float)
    p = predict(model, X)
    return p >= float(model.get("threshold", 0.0)), p


# ---------------------------------------------------------------- models
@lru_cache(maxsize=16)
def _load(path, mtime):
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    m["_trees"] = [{k: np.asarray(v) for k, v in tr.items()} for tr in m["trees"]]
    return m


def load(model_id):
    """The model saved as models/<id>.json, or None."""
    if not model_id or not str(model_id).replace("_", "").replace("-", "").isalnum():
        return None
    path = os.path.join(MODELS, f"{model_id}.json")
    try:
        return _load(path, os.path.getmtime(path))
    except (OSError, ValueError, KeyError):
        return None


RESULTS = os.path.join(HERE, "ml_results.json")


@lru_cache(maxsize=4)
def _results(path, mtime):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def results():
    """The lab's report on the AI bots (research/train_ml.py): {'bots': {id: {...}}, ...}, or None before the first training."""
    try:
        return _results(RESULTS, os.path.getmtime(RESULTS))
    except (OSError, ValueError):
        return None


def verdict(r, margin=0.05):
    """'up' when the model raised the bot's 2020-now Sharpe by at least `margin`, 'down' when it lowered it, else 'flat'."""
    t = (r or {}).get("bot_test") or {}
    a, p = (t.get("ai") or {}).get("sharpe"), (t.get("plain") or {}).get("sharpe")
    if a is None or p is None:
        return None
    return "up" if a >= p + margin else "down" if a <= p - margin else "flat"


def available():
    try:
        return sorted(f[:-5] for f in os.listdir(MODELS) if f.endswith(".json"))
    except OSError:
        return []


def predict(model, X):
    """The chance of a winning trade for each row of X (columns = model['features'])."""
    X = np.asarray(X, float)
    n = len(X)
    raw = np.full(n, float(model["baseline"]))
    if not n:
        return raw
    ar = np.arange(n)
    for tr in model["_trees"]:
        node = np.zeros(n, int)
        for _ in range(int(tr["depth"]) + 1):
            leaf = tr["leaf"][node]
            if leaf.all():
                break
            x = X[ar, tr["feature"][node]]
            go_left = np.where(np.isnan(x), tr["miss_left"][node], x <= tr["thr"][node])
            node = np.where(leaf, node, np.where(go_left, tr["left"][node], tr["right"][node]))
        raw += tr["value"][node]
    return 1.0 / (1.0 + np.exp(-raw))


def strat_codes(model, labels):
    """The 'strat' feature of each of the bot's strategies: the model's own code for it (a model that learned from many
    strategies), or its place in the bot."""
    ids = model.get("strat_ids")
    return np.array([float(ids.get(n, -1)) if ids else float(k) for k, n in enumerate(labels)])


def scores(model, frames, syms, idx, spy, ENT, labels=None):
    """The model's chance of a win for every buy signal of ENT (strategies x dates x stocks); NaN where there is none."""
    S, T, N = ENT.shape
    out = np.full((S, T, N), np.nan)
    if not ENT.any():
        return out
    ks, ts, js = np.nonzero(ENT)
    codes = strat_codes(model, labels or [str(k) for k in range(S)])
    out[ks, ts, js] = predict(model, features_at(frames, syms, idx, spy, ts, js, codes[ks]))
    return out


# ---------------------------------------------------------------- training helpers (the lab)
def export_hgb(clf, features, **meta):
    """A fitted scikit-learn HistGradientBoostingClassifier (binary, numeric features) -> the JSON model of this module."""
    trees = []
    for it in clf._predictors:
        nd = it[0].nodes
        trees.append({"feature": nd["feature_idx"].astype(int).tolist(), "thr": nd["num_threshold"].astype(float).tolist(),
                      "left": nd["left"].astype(int).tolist(), "right": nd["right"].astype(int).tolist(),
                      "leaf": nd["is_leaf"].astype(bool).tolist(), "miss_left": nd["missing_go_to_left"].astype(bool).tolist(),
                      "value": nd["value"].astype(float).tolist(), "depth": int(nd["depth"].max())})
    base = float(np.ravel(clf._baseline_prediction)[0])
    return {"features": list(features), "baseline": base, "trees": trees, **meta}

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "17.9"
