"""
research/hunter3_backtest.py - Opportunity Hunter 3.0: the historical evidence (runs in GitHub Actions, where Yahoo Finance
can be reached; .github/workflows/hunter3.yml).

What it measures, on today's S&P 500 and the site's largest companies (about 600 names, daily bars from 2005; the survivors
of today, so every number carries survivorship bias - compare methods with each other, never with zero):

  1. RANKING QUALITY  at every month end, the Spearman rank correlation (IC) between each score and the next 21 sessions'
                      return over SPY, among the stocks with a live long setup (the ones the Hunter would show) and among all
                      stocks; by period and by market regime; the spread between the top and bottom quintile.
  2. ADAPTIVE WEIGHTS the factor groups' IC by regime on the DEVELOPMENT period only (2010-2015) -> hunter3_weights.json.
  3. THE ML MODEL     a gradient-boosted classifier (top half of the month's excess returns), walk-forward: for every year from
                      2016 the model is trained on month ends up to the previous year minus a 21-session embargo and judged on
                      that year; the final model (trained through the last full year) is saved to models/hunter3_rank.json
                      with status "active" only when its walk-forward IC on 2016-2024 beat the adaptive score's.
  4. TRADING          a daily simulation of the whole book for every method and policy: signals at the close, fills at the
                      next open with costs (commission, half spread, slippage), stops checked against the day's low with a gap
                      filled at the open (worse), targets, time stops, a regime exposure cap, sector and correlation limits,
                      risk- and volatility-based sizing and a drawdown brake; equity marked at every close. A random-rank
                      control picks among the same candidates by chance. SPY buy-and-hold is the benchmark.
  5. PERIODS          development 2008-2015 (2008-2009 flagged: thin survivor data), validation 2016-2019, then the untouched
                      test periods 2020-2021, 2022, 2023-2024 and 2025-2026 (to the last completed session).
  6. METRICS          CAGR, Sharpe, Sortino, max drawdown, Calmar, profit factor, expectancy (R), win rate, average gain and
                      loss, alpha and beta, information ratio, turnover, exposure, returns by regime, block-bootstrap 90%
                      confidence intervals for CAGR and Sharpe; ablations of every policy on the adaptive method.

Nothing here is a live-trading result; the report says so on every table.
"""
import json
import os
import pickle
import sys
import time
import warnings
from datetime import date

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")

import hunter as H          # noqa: E402
import hunter3 as H3        # noqa: E402
import universe as U        # noqa: E402
from sp500 import SP500     # noqa: E402

CACHE = os.path.join(HERE, ".cache")
OUT = os.path.join(HERE, "results")
START = "2005-01-01"
DEV = ("2010-01-01", "2015-12-31")               # the only period that tunes anything (the adaptive weights)
PERIODS = {"2008-2009 (dev, flagged)": ("2008-01-01", "2009-12-31"), "2010-2015 (dev)": ("2010-01-01", "2015-12-31"),
           "2016-2019 (validation)": ("2016-01-01", "2019-12-31"), "2020-2021 (test)": ("2020-01-01", "2021-12-31"),
           "2022 (test)": ("2022-01-01", "2022-12-31"), "2023-2024 (test)": ("2023-01-01", "2024-12-31"),
           "2025-2026 (final test)": ("2025-01-01", None)}
COST = {"commission_bps": 1.0, "half_spread_bps": 5.0, "slippage_bps": 5.0}      # per side
SIDE_COST = sum(COST.values()) / 1e4
CAPITAL = 100_000.0
MIN_SCORE = 60.0
POLICY = {"risk_pct": 0.75, "max_pos": 8, "sector_cap": 2, "max_corr": 0.75, "target_vol": 18.0, "max_weight": 20.0,
          "regime_cap": True, "dd_brake": True, "corr_filter": True, "vol_size": True, "regime_exit": True}
ABLATIONS = {"no_regime_cap": {"regime_cap": False}, "no_corr_filter": {"corr_filter": False}, "no_vol_sizing": {"vol_size": False},
             "no_dd_brake": {"dd_brake": False}, "no_regime_exit": {"regime_exit": False}}
SEED = 7


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------- data
def symbols():
    syms = list(dict.fromkeys(list(SP500) + list(U.STOCKS)))
    return [s for s in syms if s.isupper() and "." not in s or s in ("BRK-B", "BF-B")]


def synthetic(syms, n=5300, seed=3):
    """Random walks in place of Yahoo (H3_SYNTH=1): a dry run of the whole pipeline on a laptop, nothing to learn from."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2005-01-03", periods=n)
    mkt = 0.0002 + 0.01 * rng.normal(size=n)
    out = {}
    for i, s in enumerate(["SPY", "^VIX"] + list(syms)):
        beta = 1.0 if s == "SPY" else rng.uniform(0.5, 1.5)
        r = mkt * beta + (0 if s == "SPY" else 0.012 * rng.normal(size=n)) + rng.uniform(-0.0001, 0.0004)
        if s == "^VIX":
            r = -2 * mkt + 0.03 * rng.normal(size=n)
        c = (20 if s == "^VIX" else 50) * np.exp(np.cumsum(np.clip(r, -0.2, 0.2)))
        o = c * (1 + 0.003 * rng.normal(size=n))
        out[s] = pd.DataFrame({"Open": o, "High": np.maximum(o, c) * (1 + 0.01 * rng.random(n)), "Low": np.minimum(o, c) * (1 - 0.01 * rng.random(n)),
                               "Close": c, "Volume": 3e6 * (1 + 0.5 * rng.random(n))}, index=idx)
    return out


def download(syms):
    if os.environ.get("H3_SYNTH"):
        return synthetic(syms[:int(os.environ.get("H3_SYNTH_N", "80"))])
    import yfinance as yf
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "hunter3_prices.pkl")
    stock = {}
    if os.path.exists(path):
        with open(path, "rb") as f:
            stock = pickle.load(f)
        log("cache", len(stock), "symbols")
    need = [s for s in syms + ["SPY", "^VIX"] if s not in stock]
    for i in range(0, len(need), 60):
        batch = need[i:i + 60]
        for attempt in range(3):
            try:
                raw = yf.download(batch, start=START, auto_adjust=True, group_by="ticker", threads=True, progress=False, timeout=40)
                break
            except Exception as e:
                log("retry", attempt, str(e)[:100])
                time.sleep(5 * (attempt + 1))
                raw = None
        if raw is None or raw.empty:
            continue
        for s in batch:
            try:
                df = raw[s] if isinstance(raw.columns, pd.MultiIndex) else raw
                df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
                if len(df) >= 300:
                    stock[s] = df
            except Exception:
                pass
        log("downloaded", i + len(batch), "/", len(need), "kept", len(stock))
    with open(path, "wb") as f:
        pickle.dump(stock, f)
    return stock


# ---------------------------------------------------------------- 1) ranking quality
def month_ends(index):
    s = pd.Series(index, index=index)
    return pd.DatetimeIndex(s.groupby(s.dt.to_period("M")).max().to_list())[:-1]


def rank_ic(score, label, mask=None):
    """Spearman IC of score against label on every row (NaN when fewer than 10 pairs)."""
    out = []
    for t in score.index:
        a, b = score.loc[t], label.loc[t]
        if mask is not None:
            m = mask.loc[t].fillna(False)
            a, b = a[m], b[m]
        ok = a.notna() & b.notna()
        if ok.sum() < 10:
            out.append(np.nan)
            continue
        out.append(a[ok].rank().corr(b[ok].rank()))
    return pd.Series(out, index=score.index)


def spread(score, label, mask=None):
    """Top quintile minus bottom quintile forward excess return (pct points) on every row."""
    out = []
    for t in score.index:
        a, b = score.loc[t], label.loc[t]
        if mask is not None:
            m = mask.loc[t].fillna(False)
            a, b = a[m], b[m]
        ok = a.notna() & b.notna()
        if ok.sum() < 20:
            out.append(np.nan)
            continue
        a, b = a[ok], b[ok]
        q = a.rank(pct=True)
        out.append(float(b[q >= 0.8].mean() - b[q <= 0.2].mean()))
    return pd.Series(out, index=score.index)


def in_period(idx, p):
    a, b = PERIODS[p] if p in PERIODS else p
    m = idx >= pd.Timestamp(a)
    if b:
        m &= idx <= pd.Timestamp(b)
    return m


def ic_tables(scores, label, cands, regime, ends):
    """{method: {period: {ic_mean, ic_t, n, spread}}, by regime} on the month ends."""
    out = {"candidates": {}, "all": {}, "by_regime": {}}
    reg = regime.reindex(ends)
    for m, frame in scores.items():
        sc = frame.reindex(ends)
        lb = label.reindex(ends)
        ic_c, ic_a = rank_ic(sc, lb, cands.reindex(ends)), rank_ic(sc, lb)
        sp_c = spread(sc, lb, cands.reindex(ends))
        out["candidates"][m], out["all"][m], out["by_regime"][m] = {}, {}, {}
        for p in PERIODS:
            pm = in_period(ends, p)
            for key, ic in (("candidates", ic_c), ("all", ic_a)):
                x = ic[pm].dropna()
                out[key][m][p] = {"ic_mean": round(float(x.mean()), 4) if len(x) else None,
                                  "ic_t": round(float(x.mean() / x.std() * np.sqrt(len(x))), 2) if len(x) > 2 and x.std() > 0 else None,
                                  "months": int(len(x)), "hit_rate": round(float((x > 0).mean()), 3) if len(x) else None}
            x = sp_c[pm].dropna()
            out["candidates"][m][p]["spread_pp"] = round(float(x.mean()), 3) if len(x) else None
        for r in H3.REGIMES:
            x = ic_c[(reg == r).to_numpy()].dropna()
            out["by_regime"][m][r] = {"ic_mean": round(float(x.mean()), 4) if len(x) else None, "months": int(len(x))}
    return out


# ---------------------------------------------------------------- 2) the adaptive weights from the development period
def fit_weights(groups, label, cands, regime, ends):
    dev = ends[in_period(ends, DEV)]
    reg = regime.reindex(dev)
    weights, evidence = {}, {}
    for r in H3.REGIMES:
        rows = dev[(reg == r).to_numpy()]
        ics = {}
        for g, frame in groups.items():
            ic = rank_ic(frame.reindex(rows), label.reindex(rows), cands.reindex(rows)).dropna()
            ics[g] = float(ic.mean()) if len(ic) >= 6 else np.nan
        evidence[r] = {"months": int(len(rows)), "ic": {g: (round(v, 4) if np.isfinite(v) else None) for g, v in ics.items()}}
        if sum(np.isfinite(v) for v in ics.values()) < 3 or len(rows) < 12:
            weights[r] = dict(H3.DEFAULT_WEIGHTS)                    # too few months of this regime in the dev period
            evidence[r]["note"] = "too few months: default weights"
            continue
        # the setup group keeps a floor (the Hunter is a setup scanner first); the others share by positive IC, blended half
        # with the defaults so a single regime's noise cannot zero a group
        pos = {g: max(v, 0.0) if np.isfinite(v) else 0.0 for g, v in ics.items()}
        tot = sum(pos.values())
        fitted = {g: (pos[g] / tot if tot > 0 else H3.DEFAULT_WEIGHTS[g]) for g in groups}
        w = {g: 0.5 * fitted[g] + 0.5 * H3.DEFAULT_WEIGHTS[g] for g in groups}
        w["setup"] = max(w["setup"], 0.15)
        tot = sum(w.values())
        weights[r] = {g: round(v / tot, 4) for g, v in w.items()}
    return weights, evidence


# ---------------------------------------------------------------- 3) the ML model, walk-forward
def ml_walk_forward(panel, groups, state, label, cands, ends):
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
    except Exception as e:
        return None, {"status": "sklearn_unavailable", "error": str(e)}
    cols = panel.ml_features(groups, state)
    feats = H3.ML_FEATURES
    X = np.stack([cols[f].reindex(ends).to_numpy(float).reshape(-1) for f in feats], axis=1)
    y_raw = label.reindex(ends)
    med = y_raw.median(axis=1)
    y = (y_raw.gt(med, axis=0)).to_numpy().reshape(-1)
    ok = np.isfinite(y_raw.to_numpy().reshape(-1)) & np.isfinite(X).any(axis=1)
    dates = np.repeat(ends.to_numpy(), len(panel.syms))
    cand = cands.reindex(ends).fillna(False).to_numpy().reshape(-1)
    years = sorted({d.year for d in ends if d.year >= 2016})
    pf = np.full(len(ends) * len(panel.syms), np.nan)
    per_year = {}
    for yr in years:
        train_end = pd.Timestamp(f"{yr - 1}-12-31") - pd.offsets.BDay(H3.HORIZON)      # embargo: labels must have resolved
        tr = ok & (dates <= np.datetime64(train_end)) & (dates >= np.datetime64("2007-01-01"))
        te = ok & (dates > np.datetime64(f"{yr - 1}-12-31")) & (dates <= np.datetime64(f"{yr}-12-31"))
        if tr.sum() < 2000 or te.sum() < 100:
            continue
        clf = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, max_depth=4, min_samples_leaf=200, l2_regularization=1.0,
                                             max_leaf_nodes=15, random_state=SEED)
        clf.fit(X[tr], y[tr])
        pf[te] = clf.predict_proba(X[te])[:, 1]
        per_year[yr] = {"train_rows": int(tr.sum()), "test_rows": int(te.sum())}
        log("ml year", yr, per_year[yr])
    if not per_year:
        return None, {"status": "insufficient_data"}
    pred_frame = pd.DataFrame(pf.reshape(len(ends), -1), index=ends, columns=panel.syms)
    ic = rank_ic(pred_frame, label.reindex(ends), cands.reindex(ends))
    # importance of the final model (permutation on the last validation year is costly; use the gain-free split counts)
    final_end = pd.Timestamp(f"{years[-1] - 1}-12-31") - pd.offsets.BDay(H3.HORIZON)
    tr = ok & (dates <= np.datetime64(final_end)) & (dates >= np.datetime64("2007-01-01"))
    clf = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, max_depth=4, min_samples_leaf=200, l2_regularization=1.0,
                                         max_leaf_nodes=15, random_state=SEED)
    clf.fit(X[tr], y[tr])
    model = H3.export_hgb(clf, feats, trained_through=str(final_end.date()), horizon=H3.HORIZON, label="top half of the month's excess return over SPY",
                          n_train=int(tr.sum()), walk_forward_years=per_year)
    # a check that the exported trees reproduce scikit-learn
    chk = X[tr][:500]
    raw = H3.predict_raw({**model, "trees": _as_arrays(model["trees"])}, chk)
    assert np.abs(1 / (1 + np.exp(-raw)) - clf.predict_proba(chk)[:, 1]).max() < 1e-6, "exported model disagrees with scikit-learn"
    return model, {"status": "trained", "ic": ic, "pred": pred_frame, "years": per_year}


def _as_arrays(trees):
    out = []
    for tr in trees:
        out.append({"feature": np.asarray(tr["feature"], int), "thr": np.asarray(tr["thr"], float), "left": np.asarray(tr["left"], int),
                    "right": np.asarray(tr["right"], int), "leaf": np.asarray(tr["leaf"], bool), "miss_left": np.asarray(tr["miss_left"], bool),
                    "value": np.asarray(tr["value"], float), "depth": tr["depth"]})
    return out


# ---------------------------------------------------------------- 4) the trading simulation
class Book:
    """The daily simulation of one method under one policy, on the panel's matrices."""

    def __init__(self, panel, score, state, policy, start, end, seed=None):
        self.p = panel
        self.idx = panel.index
        self.syms = panel.syms
        self.N = len(self.syms)
        g = lambda name, src="frames": panel.col(name, src).to_numpy(float)
        self.O, self.Hh, self.Lw, self.C = g("Open"), g("High"), g("Low"), g("Close")
        self.score = score.reindex(self.idx).to_numpy(float)
        if seed is not None:                                  # the random control: a random rank among the same candidates
            rng = np.random.default_rng(seed)
            self.score = np.where(np.isfinite(self.score), rng.random(self.score.shape) * 100, np.nan)
        self.side = g("side", "setups")
        self.status = panel.col("status", "setups").to_numpy(object)
        self.key = panel.col("key", "setups").to_numpy(object)
        self.stop = g("stop", "setups")
        self.tgt = g("target", "setups")
        self.vol = g("vol_63", "feats")
        self.dollar = g("dollar_20", "feats")
        self.regime = state["regime"].reindex(self.idx).fillna("neutral").to_numpy(object)
        self.sector = np.array([panel.sectors.get(s) or "?" for s in self.syms], dtype=object)
        self.hold = np.array([0] * self.N)
        self.pol = policy
        self.t0 = int(np.searchsorted(self.idx, pd.Timestamp(start)))
        self.t1 = int(np.searchsorted(self.idx, pd.Timestamp(end), side="right")) if end else len(self.idx)
        self.ret = np.vstack([np.full(self.N, np.nan), self.C[1:] / self.C[:-1] - 1])

    def run(self):
        pol = self.pol
        cash = CAPITAL
        pos = {}                                                 # j -> dict(shares, entry, stop, target, expiry, t_in, cost)
        equity = np.full(self.t1 - self.t0, np.nan)
        trades, traded, invested = [], 0.0, []
        peak = CAPITAL
        for t in range(self.t0, self.t1):
            # ---- exits on today's bar
            for j in list(pos):
                q = pos[j]
                o, hi, lo, c = self.O[t, j], self.Hh[t, j], self.Lw[t, j], self.C[t, j]
                if not np.isfinite(c):
                    continue
                ex, why = None, None
                if pol["regime_exit"] and self.regime[t - 1] in ("bear", "stress") and np.isfinite(o):
                    ex, why = o * (1 - SIDE_COST), "regime"
                elif np.isfinite(o) and o <= q["stop"]:
                    ex, why = o * (1 - SIDE_COST), "gap"
                elif np.isfinite(lo) and lo <= q["stop"]:
                    ex, why = q["stop"] * (1 - SIDE_COST), "stop"
                elif np.isfinite(o) and o >= q["target"]:
                    ex, why = o * (1 - SIDE_COST), "target"
                elif np.isfinite(hi) and hi >= q["target"]:
                    ex, why = q["target"] * (1 - SIDE_COST), "target"
                elif t >= q["expiry"]:
                    ex, why = c * (1 - SIDE_COST), "time"
                if ex is not None:
                    cash += q["shares"] * ex
                    traded += q["shares"] * ex
                    r = (ex - q["entry"]) / (q["entry"] - q["stop"])
                    trades.append({"sym": self.syms[j], "in": str(self.idx[q["t_in"]].date()), "out": str(self.idx[t].date()), "ret": ex / q["entry"] - 1,
                                   "R": r, "bars": t - q["t_in"], "why": why, "key": q["key"], "regime": q["regime"]})
                    del pos[j]
            # ---- entries decided at yesterday's close, filled at today's open
            eq_prev = cash + sum(q["shares"] * self.C[t - 1, j] for j, q in pos.items() if np.isfinite(self.C[t - 1, j]))
            peak = max(peak, eq_prev)
            dd = eq_prev / peak - 1
            reg = self.regime[t - 1]
            cap = (H3.EXPOSURE.get(reg, 0.5) if pol["regime_cap"] else 1.0) * (0.5 if pol["dd_brake"] and dd <= -0.10 else 1.0)
            if not (pol["regime_exit"] and reg in ("bear", "stress")) and len(pos) < pol["max_pos"]:
                s = self.score[t - 1]
                live = (self.side[t - 1] > 0) & np.isin(self.status[t - 1], ["fresh", "active"]) & (s >= MIN_SCORE) & np.isfinite(self.stop[t - 1]) \
                    & np.isfinite(self.tgt[t - 1]) & (self.dollar[t - 1] >= 20e6) & np.isfinite(self.O[t])
                live[list(pos)] = False
                order = np.argsort(-np.where(live, s, -np.inf))
                secs = {}
                for j in pos:
                    secs[self.sector[j]] = secs.get(self.sector[j], 0) + 1
                held_value = sum(q["shares"] * self.C[t - 1, jj] for jj, q in pos.items() if np.isfinite(self.C[t - 1, jj]))
                budget = eq_prev * cap - held_value
                for j in order:
                    if not live[j] or len(pos) >= pol["max_pos"] or budget <= 0:
                        break
                    o = self.O[t, j] * (1 + SIDE_COST)
                    st, tg = self.stop[t - 1, j], self.tgt[t - 1, j]
                    if not (st < o < tg):
                        continue                                   # opened beyond the stop or the target: no trade
                    if secs.get(self.sector[j], 0) >= pol["sector_cap"]:
                        continue
                    if pol["corr_filter"] and pos:
                        seg = self.ret[max(0, t - 63):t]
                        rj = seg[:, j]
                        mx = 0.0
                        for jj in pos:
                            rr = seg[:, jj]
                            ok = np.isfinite(rj) & np.isfinite(rr)
                            if ok.sum() > 30:
                                cc = np.corrcoef(rj[ok], rr[ok])[0, 1]
                                mx = max(mx, cc if np.isfinite(cc) else 0.0)
                        if mx > pol["max_corr"]:
                            continue
                    per_risk = eq_prev * pol["risk_pct"] / 100 / (o - st)
                    v = self.vol[t - 1, j]
                    per_vol = eq_prev * (pol["target_vol"] / pol["max_pos"]) / v / o if pol["vol_size"] and np.isfinite(v) and v > 0 else np.inf
                    per_w = eq_prev * pol["max_weight"] / 100 / o
                    shares = int(max(0, min(per_risk, per_vol, per_w, budget / o, cash / o)))
                    if shares <= 0:
                        continue
                    k = self.key[t - 1, j]
                    mb = H.SETUPS[k][5] if isinstance(k, str) and H.SETUPS[k][5] else 20
                    pos[j] = {"shares": shares, "entry": o, "stop": st, "target": tg, "expiry": t + mb, "t_in": t, "key": k, "regime": reg}
                    cash -= shares * o
                    traded += shares * o
                    budget -= shares * o
                    secs[self.sector[j]] = secs.get(self.sector[j], 0) + 1
            held = sum(q["shares"] * self.C[t, j] for j, q in pos.items() if np.isfinite(self.C[t, j]))
            equity[t - self.t0] = cash + held
            invested.append(held / (cash + held) if cash + held > 0 else 0.0)
        eq = pd.Series(equity, index=self.idx[self.t0:self.t1]).ffill()
        return eq, pd.DataFrame(trades), {"turnover": traded / max(1e-9, eq.mean()) / max(1, len(eq) / 252), "exposure": float(np.mean(invested)) if invested else 0.0}


# ---------------------------------------------------------------- 6) the metrics
def metrics(eq, bench, trades, extra, regime):
    r = eq.pct_change().dropna()
    b = bench.reindex(eq.index).ffill().pct_change().dropna().reindex(r.index).fillna(0)
    years = len(r) / 252
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1 if years > 0 and eq.iloc[0] > 0 else np.nan
    sharpe = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else np.nan
    dn = r[r < 0].std()
    sortino = r.mean() / dn * np.sqrt(252) if dn and dn > 0 else np.nan
    dd = (eq / eq.cummax() - 1)
    mdd = float(dd.min())
    calmar = cagr / abs(mdd) if mdd < 0 else np.nan
    ex = r - b
    ir = ex.mean() / ex.std() * np.sqrt(252) if ex.std() > 0 else np.nan
    if b.std() > 0:
        beta = float(np.cov(r, b)[0, 1] / b.var())
        alpha = float((r.mean() - beta * b.mean()) * 252)
    else:
        beta, alpha = np.nan, np.nan
    out = {"cagr": cagr, "total_return": eq.iloc[-1] / eq.iloc[0] - 1, "sharpe": sharpe, "sortino": sortino, "max_drawdown": mdd, "calmar": calmar,
           "alpha_annual": alpha, "beta": beta, "information_ratio": ir, "turnover_per_year": extra["turnover"], "exposure": extra["exposure"],
           "days": int(len(r)), "bench_total_return": float(bench.reindex(eq.index).ffill().iloc[-1] / bench.reindex(eq.index).ffill().iloc[0] - 1)}
    if len(trades):
        R = trades["R"].to_numpy(float)
        wins, losses = R[R > 0], R[R <= 0]
        out.update({"trades": int(len(R)), "win_rate": float((R > 0).mean()), "expectancy_R": float(R.mean()),
                    "avg_gain_pct": float(trades.loc[trades["ret"] > 0, "ret"].mean() * 100) if (trades["ret"] > 0).any() else 0.0,
                    "avg_loss_pct": float(trades.loc[trades["ret"] <= 0, "ret"].mean() * 100) if (trades["ret"] <= 0).any() else 0.0,
                    "profit_factor": float(wins.sum() / -losses.sum()) if losses.sum() < 0 else np.inf, "avg_bars": float(trades["bars"].mean()),
                    "exits": trades["why"].value_counts().to_dict()})
    else:
        out.update({"trades": 0})
    # by regime: the strategy's and the benchmark's daily returns on the days of each regime, annualised
    reg = regime.reindex(r.index).fillna("neutral")
    out["by_regime"] = {}
    for g in H3.REGIMES:
        m = (reg == g).to_numpy()
        if m.sum() >= 20:
            out["by_regime"][g] = {"days": int(m.sum()), "ann_return": float(r[m].mean() * 252), "bench_ann_return": float(b[m].mean() * 252),
                                   "sharpe": float(r[m].mean() / r[m].std() * np.sqrt(252)) if r[m].std() > 0 else None}
    # block bootstrap of monthly returns (3-month blocks), 90% interval for CAGR and Sharpe
    mo = (1 + r).resample("ME").prod() - 1
    if len(mo) >= 12:
        rng = np.random.default_rng(SEED)
        cs, ss = [], []
        x = mo.to_numpy()
        n, blk = len(x), 3
        for _ in range(1000):
            starts = rng.integers(0, n - blk + 1, size=n // blk + 1)
            samp = np.concatenate([x[s:s + blk] for s in starts])[:n]
            cs.append((np.prod(1 + samp)) ** (12 / n) - 1)
            ss.append(samp.mean() / samp.std() * np.sqrt(12) if samp.std() > 0 else 0.0)
        out["ci90"] = {"cagr": [float(np.percentile(cs, 5)), float(np.percentile(cs, 95))], "sharpe": [float(np.percentile(ss, 5)), float(np.percentile(ss, 95))]}
    return out


def _clean_json(o):
    if isinstance(o, dict):
        return {str(k): _clean_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean_json(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else round(float(o), 6)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp,)):
        return str(o.date())
    return o


# ---------------------------------------------------------------- the report
def fmt(v, pct=False, d=2):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    return f"{v * 100:.{d}f}%" if pct else f"{v:.{d}f}"


def report(res):
    L = ["# Opportunity Hunter 3.0 — historical evidence", "",
         f"Run on GitHub Actions on {res['run']['date']} · {res['run']['symbols']} symbols (today's S&P 500 and the site's largest companies: "
         "survivorship bias, so compare methods with each other, never with zero) · daily bars from 2005 (Yahoo Finance, adjusted).",
         "", "**These are simulations, not trading results.** Costs per side: " + ", ".join(f"{k.replace('_', ' ')} {v} bps" for k, v in COST.items())
         + f" ({SIDE_COST * 2e4:.0f} bps a round trip). Fills at the next open; stops filled at the open when the day gaps through them; "
         "targets and time stops; no shorts, no leverage, no dividends in the stocks' returns (SPY's benchmark return is price-only too).", ""]
    scored = [m for m in res["methods"] if m != "random"]
    L += ["## 1. Ranking quality (rank IC of each score against the next month's return over SPY, among the stocks with a live long setup)", "",
          "| Period | " + " | ".join(scored) + " |", "|---|" + "---:|" * len(scored)]
    for p in PERIODS:
        cells = []
        for m in scored:
            x = res["ic"]["candidates"].get(m, {}).get(p)
            cells.append("—" if not x or x["ic_mean"] is None else f"{x['ic_mean']:+.3f} (t {x['ic_t']}, {x['months']} mo)")
        L.append(f"| {p} | " + " | ".join(cells) + " |")
    L += ["", "IC by market regime (all periods):", "", "| Regime | " + " | ".join(scored) + " |", "|---|" + "---:|" * len(scored)]
    for r in H3.REGIMES:
        L.append(f"| {r} | " + " | ".join(("—" if res["ic"]["by_regime"].get(m, {}).get(r, {}).get("ic_mean") is None
                                           else f"{res['ic']['by_regime'][m][r]['ic_mean']:+.3f} ({res['ic']['by_regime'][m][r]['months']} mo)") for m in scored) + " |")
    L += ["", "## 2. Adaptive weights (fitted on 2010-2015 only)", "", "| Regime | " + " | ".join(H3.GROUPS) + " | months |", "|---|" + "---:|" * (len(H3.GROUPS) + 1)]
    for r, w in res["weights"]["weights"].items():
        ev = res["weights"]["evidence"].get(r, {})
        L.append(f"| {r} | " + " | ".join(f"{w[g]:.2f}" for g in H3.GROUPS) + f" | {ev.get('months', '—')} |")
    L += ["", f"ML model: {res['ml']['status']}" + (f" · walk-forward IC 2016-2024 {res['ml'].get('ic_2016_2024', '—')} against adaptive {res['ml'].get('adaptive_ic_2016_2024', '—')}"
                                                   f" · {'ACTIVE' if res['ml'].get('active') else 'NOT USED (did not beat the adaptive score out of sample)'}" if res['ml'].get('status') == 'trained' else ""), ""]
    L += ["## 3. Trading simulation by period (same portfolio rules for every method)", ""]
    for p in PERIODS:
        L += [f"### {p}", "", "| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |",
              "|---|" + "---:|" * 16]
        for m, d in res["sim"].get(p, {}).items():
            ci = d.get("ci90", {}).get("cagr")
            L.append(f"| {m} | {fmt(d.get('cagr'), True)} | {fmt(d.get('total_return'), True)} | {fmt(d.get('sharpe'))} | {fmt(d.get('sortino'))} | {fmt(d.get('max_drawdown'), True)} | "
                     f"{fmt(d.get('calmar'))} | {fmt(d.get('profit_factor'))} | {fmt(d.get('expectancy_R'))} | {fmt(d.get('win_rate'), True, 0)} | {d.get('trades', 0)} | "
                     f"{fmt(d.get('alpha_annual'), True)} | {fmt(d.get('beta'))} | {fmt(d.get('information_ratio'))} | {fmt(d.get('turnover_per_year'), False, 1)} | "
                     f"{fmt(d.get('exposure'), True, 0)} | {('—' if not ci else f'{ci[0] * 100:+.1f}% … {ci[1] * 100:+.1f}%')} |")
        L.append("")
    L += ["## 4. Returns by market regime (annualised, all periods, adaptive method against SPY on the same days)", "",
          "| Regime | Days | Adaptive | SPY |", "|---|---:|---:|---:|"]
    for r, d in res["sim_all"].get("adaptive", {}).get("by_regime", {}).items():
        L.append(f"| {r} | {d['days']} | {fmt(d['ann_return'], True)} | {fmt(d['bench_ann_return'], True)} |")
    L += ["", "## 5. Ablations (adaptive method, 2016-2026, one rule removed at a time)", "", "| Variant | CAGR | Sharpe | Max DD | Trades | Exposure |", "|---|---:|---:|---:|---:|---:|"]
    for m, d in res["ablation"].items():
        L.append(f"| {m} | {fmt(d.get('cagr'), True)} | {fmt(d.get('sharpe'))} | {fmt(d.get('max_drawdown'), True)} | {d.get('trades', 0)} | {fmt(d.get('exposure'), True, 0)} |")
    L += ["", "## 6. What this does and does not show", "",
          "- Survivorship: today's constituents; delisted and acquired companies are missing, which flatters every method (the control and SPY-relative comparisons still hold).",
          "- 2008-2009 has few survivors with full history and is shown for context only.",
          "- Earnings dates are not in the history: the live page penalises a report within 5 sessions, the simulation cannot.",
          "- Fundamentals are today's snapshot (no point-in-time history), so they take no part in the scores here or on the page's ranking.",
          "- Adjusted prices from Yahoo can be revised; SPY is price-only in both the benchmark and the excess-return labels.",
          "- A score is a rank, never a probability. The ML model's output is used as a rank too.",
          "- The adaptive weights were fitted on 2010-2015; 2016-2019 was the validation window; nothing after 2019 touched any setting.",
          ""]
    return "\n".join(L)


# ---------------------------------------------------------------- main
def main():
    t0 = time.time()
    syms = symbols()
    prices = download(syms)
    spy, vix = prices.pop("SPY"), prices.pop("^VIX", None)
    sectors = {s: U.sector_of(s) for s in prices}
    log("panel on", len(prices), "stocks")
    panel = H3.Panel(prices, spy, vix, sectors)
    log("panel built", len(panel.syms), "stocks", f"{time.time() - t0:.0f}s")
    state = panel.market_state()
    label = panel.col("fwd_excess")
    cands = (panel.col("side", "setups") > 0) & panel.col("status", "setups").isin(["fresh", "active"])
    ends = month_ends(panel.index)
    ends = ends[ends >= pd.Timestamp("2007-06-30")]
    groups = panel.group_ranks()
    weights, evidence = fit_weights(groups, label, cands, state["regime"], ends)
    with open(os.path.join(ROOT, "hunter3_weights.json"), "w", encoding="utf-8") as f:
        json.dump({"fitted_on": list(DEV), "weights": weights, "evidence": evidence, "built": date.today().isoformat()}, f, ensure_ascii=False, indent=1)
    log("weights", weights)
    scores, _ = panel.scores(("v1", "quant", "adaptive"), weights=weights, state=state)
    model, ml = ml_walk_forward(panel, groups, state, label, cands, ends)
    ml_info = {"status": ml.get("status")}
    if model is not None:
        ic = ml["ic"]
        win = (ic.index >= pd.Timestamp("2016-01-01")) & (ic.index <= pd.Timestamp("2024-12-31"))
        ic_ml = float(ic[win].mean())
        ic_ad = float(rank_ic(scores["adaptive"].reindex(ends), label.reindex(ends), cands.reindex(ends))[win].mean())
        active = bool(np.isfinite(ic_ml) and ic_ml > 0 and ic_ml > ic_ad)        # it must rank better than the adaptive score, out of sample
        model["status"] = "active" if active else "rejected"
        model["validation"] = {"ic_2016_2024": round(ic_ml, 4), "adaptive_ic_2016_2024": round(ic_ad, 4), "years": ml["years"]}
        os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)
        with open(H3.MODEL_FILE, "w", encoding="utf-8") as f:
            json.dump(model, f)
        ml_info.update({"ic_2016_2024": round(ic_ml, 4), "adaptive_ic_2016_2024": round(ic_ad, 4), "active": active, "years": ml["years"]})
        # the walk-forward predictions are the honest ML score in the simulation (the final model never sees its own test years)
        pred = ml["pred"].reindex(panel.index).ffill(limit=25)
        ml_rank = pred.rank(axis=1, pct=True) * 100
        scores["ml"] = ml_rank.where(panel.col("side", "setups") > 0, ml_rank.clip(upper=49))
        log("ml", ml_info)
    methods = list(scores)
    ic = ic_tables(scores, label, cands, state["regime"], ends)
    log("ic done", f"{time.time() - t0:.0f}s")
    bench = spy["Close"].astype(float)
    bench.index = H3._naive(bench.index)
    sim, sim_all, ablation = {}, {}, {}
    full = ("2008-01-01", None)
    eqs = {}
    for m in methods + ["random"]:
        sc = scores["adaptive"] if m == "random" else scores[m]
        book = Book(panel, sc, state, POLICY, *full, seed=SEED if m == "random" else None)
        eq, trades, extra = book.run()
        eqs[m] = (eq, trades, extra)
        sim_all[m] = metrics(eq, bench, trades, extra, state["regime"])
        log("sim", m, f"{time.time() - t0:.0f}s", {k: round(v, 3) for k, v in sim_all[m].items() if isinstance(v, float)})
    for p, (a, b) in PERIODS.items():
        sim[p] = {}
        for m, (eq, trades, extra) in eqs.items():
            e = eq.loc[a:b] if b else eq.loc[a:]
            if len(e) < 40 or (m == "ml" and a < "2016"):           # the ML score exists only from 2016 (walk-forward)
                continue
            tr = trades[(trades["in"] >= a) & ((trades["in"] <= b) if b else True)] if len(trades) else trades
            sim[p][m] = metrics(e, bench, tr, extra, state["regime"])
        spy_eq = bench.reindex(eq.index).ffill()
        e = spy_eq.loc[a:b] if b else spy_eq.loc[a:]
        sim[p]["SPY"] = metrics(e, bench, pd.DataFrame(), {"turnover": 0.0, "exposure": 1.0}, state["regime"])
    for name, change in ABLATIONS.items():
        book = Book(panel, scores["adaptive"], state, {**POLICY, **change}, "2016-01-01", None)
        eq, trades, extra = book.run()
        ablation[name] = metrics(eq, bench, trades, extra, state["regime"])
        log("ablation", name, f"{time.time() - t0:.0f}s")
    eq, trades, extra = eqs["adaptive"]
    ablation["adaptive (all rules)"] = metrics(eq.loc["2016-01-01":], bench, trades[trades["in"] >= "2016-01-01"], extra, state["regime"])
    res = {"run": {"date": date.today().isoformat(), "symbols": len(panel.syms), "seconds": int(time.time() - t0), "cost": COST, "policy": POLICY,
                   "min_score": MIN_SCORE, "capital": CAPITAL},
           "methods": methods + ["random"], "ic": ic, "weights": {"weights": weights, "evidence": evidence}, "ml": ml_info, "sim": sim, "sim_all": sim_all,
           "ablation": ablation,
           "equity_monthly": {m: {str(k.date()): round(float(v), 2) for k, v in eq.resample("ME").last().items()} for m, (eq, _, _) in eqs.items()},
           "spy_monthly": {str(k.date()): round(float(v), 2) for k, v in bench.loc["2008-01-01":].resample("ME").last().items()}}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "hunter3_backtest.json"), "w", encoding="utf-8") as f:
        json.dump(_clean_json(res), f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "hunter3_report.md"), "w", encoding="utf-8") as f:
        f.write(report(_clean_json(res)))
    trades_all = pd.concat([t.assign(method=m) for m, (_, t, _) in eqs.items() if len(t)])
    trades_all.to_csv(os.path.join(OUT, "hunter3_trades.csv.gz"), index=False, compression="gzip")
    log("done", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
