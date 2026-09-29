"""
research/combos.py - Which strategies work best together (runs in GitHub Actions, where Yahoo Finance can be reached).
Writes research/results/combos.json and combos.md.

Every strategy of the site gives, for each stock and each session, its buy state (from its own buy signal until its own
sell signal). A combination of k strategies with an agreement rule m-of-k is "in" a stock while at least m of them are in
their buy state. Each combination is judged as a portfolio: every session it holds, in equal parts, every stock where it
is "in" at the previous close (bought at the open, like the bots), and its daily return is compared with holding every
stock equally that day (the excess return). Numbers: the excess return a year, its information ratio (excess / its
volatility), the average number of stocks held and the entries a year.
  Screened: every strategy alone, every pair (2 of 2), every triple (2 of 3 and 3 of 3), and every group of 4 of the 12
  best single strategies (3 of 4 and 4 of 4).
  Judged on 2010-2019 (in-sample); 2020-now is only shown to check. Today's S&P 500 list (survivorship bias): the excess
  over holding the same stocks is the fair measure.
"""
import itertools
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
warnings.filterwarnings("ignore")
os.environ.setdefault("STREAMLIT_LOG_LEVEL", "error")

import engine                   # noqa: E402
import paperbots as PB          # noqa: E402
from smart import load_prices   # noqa: E402  (the same cached prices as the bots' test)

OUT = os.path.join(HERE, "results")
PERIODS = {"ins": ("2010-01-04", "2019-12-31"), "oos": ("2020-01-02", None), "full": ("2008-01-02", None)}
MIN_HELD, MIN_ENTRIES = 3.0, 40.0          # a combination must hold at least 3 stocks on average and enter 40 times a year


def states(px, syms, spy, idx):
    """{strategy: (T, N) bool buy state} for every strategy on every stock (NaN days = False)."""
    out = {}
    for name in engine.STRATEGIES:
        M = np.zeros((len(idx), len(syms)), bool)
        p0 = PB.clean_params(name, {})
        for j, s in enumerate(syms):
            df = px[s]
            try:
                e, x = engine.signals(name, df, p0, spy)
            except Exception:
                continue
            st_ = PB._state(e, x).reindex(idx).fillna(0.0).to_numpy() > 0.5
            M[:, j] = st_
        out[name] = M
        print("state", name, flush=True)
    return out


def judge(cond, R, mkt, masks):
    """cond (T, N): in at the close; R (T, N): open-to-open return of the next session (NaN unknown); mkt (T,): the
    average of R. -> {period: {ex, ir, held, entries}}"""
    held = np.zeros_like(cond)
    held[1:] = cond[:-1]                                   # in at the previous close -> holds this session
    fin = np.isfinite(R)
    h = held & fin
    n = h.sum(axis=1)
    port = np.where(n > 0, np.where(h, R, 0.0).sum(axis=1) / np.maximum(n, 1), np.nan)
    ex = port - mkt
    ent = cond & ~np.vstack([np.zeros((1, cond.shape[1]), bool), cond[:-1]])
    ent_n = ent.sum(axis=1)
    out = {}
    for pk, m in masks.items():
        e_ = ex[m]
        e_ = e_[np.isfinite(e_)]
        days = int(m.sum())
        if len(e_) < 60:
            out[pk] = None
            continue
        out[pk] = {"ex": float(e_.mean() * 252), "ir": float(e_.mean() / e_.std() * np.sqrt(252)) if e_.std() > 0 else 0.0,
                   "held": float(n[m].mean()), "entries": float(ent_n[m].sum() / days * 252), "in_days": float((n[m] > 0).mean())}
    return out


def main():
    t0 = time.time()
    syms = PB.members("all", "all")
    px = load_prices(sorted(set(syms) | {"SPY"}))
    syms = [s for s in syms if s in px and len(px[s]) > 300]
    spy = px["SPY"]
    idx = pd.DatetimeIndex(sorted(set().union(*[set(px[s].index) for s in syms])))
    idx = idx[idx >= pd.Timestamp("2006-01-01")]
    px = {s: PB._prep(px[s]) for s in syms}
    O = pd.concat({s: px[s]["Open"].astype(float) for s in syms}, axis=1).reindex(idx).to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        R = np.full(O.shape, np.nan)
        R[:-1] = O[1:] / O[:-1] - 1                        # bought at this open, valued at the next one
        R[~np.isfinite(R) | (np.abs(R) > 0.8)] = np.nan     # data errors
    fin = np.isfinite(R)
    mkt = np.where(fin.sum(axis=1) > 0, np.where(fin, R, 0.0).sum(axis=1) / np.maximum(fin.sum(axis=1), 1), np.nan)
    ixn = idx.tz_localize(None) if idx.tz is not None else idx
    masks = {pk: np.asarray((ixn >= pd.Timestamp(a)) & ((ixn <= pd.Timestamp(b)) if b else True)) for pk, (a, b) in PERIODS.items()}
    ST = states(px, syms, spy, idx)
    print(f"states in {time.time() - t0:.0f} s", flush=True)
    names = list(ST)
    rows = []

    def add(members, m):
        cnt = sum(ST[x].astype(np.int8) for x in members)
        res = judge(cnt >= m, R, mkt, masks)
        rows.append({"of": list(members), "min": m, "k": len(members), **res})

    for s in names:
        add([s], 1)
    single = sorted((r for r in rows if r["ins"]), key=lambda r: -r["ins"]["ir"])
    top12 = [r["of"][0] for r in single[:12]]
    for a, b in itertools.combinations(names, 2):
        add([a, b], 2)
    print(f"pairs done {time.time() - t0:.0f} s", flush=True)
    for trio in itertools.combinations(names, 3):
        add(list(trio), 2)
        add(list(trio), 3)
    print(f"triples done {time.time() - t0:.0f} s", flush=True)
    for quad in itertools.combinations(top12, 4):
        add(list(quad), 3)
        add(list(quad), 4)
    print(f"quads done {time.time() - t0:.0f} s, {len(rows)} combinations", flush=True)

    ok = [r for r in rows if r["ins"] and r["ins"]["held"] >= MIN_HELD and r["ins"]["entries"] >= MIN_ENTRIES]
    ok.sort(key=lambda r: -r["ins"]["ir"])
    os.makedirs(OUT, exist_ok=True)
    json.dump({"run": f"{pd.Timestamp.now(tz='UTC'):%Y-%m-%d %H:%M} UTC", "n_stocks": len(syms), "n_combos": len(rows),
               "singles": single, "top": ok[:300]}, open(os.path.join(OUT, "combos.json"), "w"), indent=0, default=float)
    pct = lambda v: "—" if v is None else f"{v * 100:+.1f}%"
    L = [f"# Strategy combinations · screening", "", f"Run {pd.Timestamp.now(tz='UTC'):%Y-%m-%d %H:%M} UTC · {len(syms)} stocks · "
         f"{len(rows)} combinations · took {(time.time() - t0) / 60:.0f} min", "",
         "Excess = the combination's equal-weight portfolio (stocks where the rule is in) minus holding every stock equally, a year. "
         "IR = excess / its volatility. Ranked on 2010-2019; 2020-now only to check. "
         f"Kept: at least {MIN_HELD:g} stocks held on average and {MIN_ENTRIES:g} entries a year.", "",
         "| # | Combination | Rule | IS excess | IS IR | IS held | IS entries/yr | OOS excess | OOS IR | Full excess | Full IR |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(ok[:120]):
        a, b, c = r["ins"], r["oos"] or {}, r["full"] or {}
        L.append(f"| {i + 1} | {' + '.join(r['of'])} | {r['min']} of {r['k']} | {pct(a['ex'])} | {a['ir']:.2f} | {a['held']:.0f} | {a['entries']:.0f} | "
                 f"{pct(b.get('ex'))} | {b.get('ir', 0):.2f} | {pct(c.get('ex'))} | {c.get('ir', 0):.2f} |")
    L += ["", "## Every strategy alone", "", "| Strategy | IS excess | IS IR | IS held | OOS excess | OOS IR |", "|---|---|---|---|---|---|"]
    for r in single:
        a, b = r["ins"], r["oos"] or {}
        L.append(f"| {r['of'][0]} | {pct(a['ex'])} | {a['ir']:.2f} | {a['held']:.0f} | {pct(b.get('ex'))} | {b.get('ir', 0):.2f} |")
    open(os.path.join(OUT, "combos.md"), "w").write("\n".join(L) + "\n")
    print(f"done in {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
