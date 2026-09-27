"""
mlbots.py - The AI part of the Paper Bots. Each AI bot has its own model: it learned, from every buy signal its strategies
gave on 500+ US stocks in 2012-2019 and how each of those trades ended, which signals tend to end in a win. In a bot with a
model ('ml' = the model's id), a buy signal only counts when the model's chance of a win is at least the model's threshold,
and when more stocks signal than there are free slots, the highest chances are bought first (instead of the strongest 3
months).

The models are gradient-boosted decision trees trained with scikit-learn in the lab (research/train_ml.py) and saved as
plain JSON (models/<id>.json), so the site needs no machine-learning library: a prediction is a walk down each tree in
numpy. Every feature uses only what was known at the signal's close.
"""
import json
import os
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


def scores(model, frames, syms, idx, spy, ENT):
    """The model's chance of a win for every buy signal of ENT (strategies x dates x stocks); NaN where there is none."""
    S, T, N = ENT.shape
    out = np.full((S, T, N), np.nan)
    if not ENT.any():
        return out
    ks, ts, js = np.nonzero(ENT)
    out[ks, ts, js] = predict(model, features_at(frames, syms, idx, spy, ts, js, ks.astype(float)))
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
