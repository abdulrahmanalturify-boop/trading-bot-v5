"""
research/train_market.py - Round 3 of the AI bots: one model of the whole market (mlbots.market_panel: the S&P 500 and the
breadth of the 500+ stocks), trained on 2012-2019. Each day it gives the chance that the next month is good for stocks (the
equal-weighted return of the stocks over the next 21 sessions above zero). Under its threshold the bot buys nothing and
sells what it holds; in the AI bots it takes the place of the 200-day market filter.

How many days to call risky (none, 10, 20 or 30 % of them) is chosen on 2017-2019 with a model trained on 2012-2016 only:
the share that gave the best Sharpe to holding the stocks only on the allowed days, and only when it clearly beats always
holding them. Then the model is trained again on 2012-2019 (labels that would reach into 2020 are left out) and saved as
models/<MODEL_ID>.json. The test: 2020 to now, years the model never saw: the stocks held with and without the model, and
the five AI bots (research/train_ml.AI_BOTS) with the model against the same bots as they are.
Results: ml_results.json at the top (for the site) and research/results/ml_market_summary.md.
"""
import json
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from datetime import date

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [ROOT, HERE]
warnings.filterwarnings("ignore")
os.environ.setdefault("STREAMLIT_LOG_LEVEL", "error")

import run as R                 # noqa: E402
import train_ml as TM           # noqa: E402  (the five AI bots and their settings)
import paperbots as PB          # noqa: E402
import mlbots as MLB            # noqa: E402

MODEL_ID = "ai_market_1"        # a released model never changes: a retrained one gets a new id
HORIZON = 21
GATE = (0.0, 0.1, 0.2, 0.3)
HGBM = dict(learning_rate=0.03, max_iter=150, max_depth=2, min_samples_leaf=120, l2_regularization=2.0, early_stopping=False,
            random_state=0)
TRAIN0, FIT_END, TRAIN_END, TEST = "2012-01-03", "2016-12-30", "2019-12-31", "2020-01-02"


def sharpe(r):
    r = pd.Series(r).dropna()
    return float(r.mean() / r.std() * np.sqrt(252)) if len(r) > 30 and r.std() > 0 else 0.0


def curve(r):
    eq = (1 + pd.Series(r).fillna(0)).cumprod()
    yrs = len(eq) / 252
    return {"sharpe": sharpe(r), "cagr": float(eq.iloc[-1] ** (1 / yrs) - 1) if yrs > 0 else 0.0,
            "maxdd": float((eq / eq.cummax() - 1).min())}


def ai_settings(mid, gates):
    c = {k: v for k, v in TM.AI_BOTS[mid].items() if k != "name"}
    if gates:
        c["regime"] = 0              # the model takes the place of the 200-day market filter (when it calls any day risky)
    return c


def bot_job(job):
    """(bot id, 'train' | 'test', with the model?) -> the all-companies bot's numbers."""
    mid, part, ai = job
    px, spy = dict(TM._PX), TM._PX["SPY"]
    start = TRAIN0 if part == "train" else TEST
    if part == "train":
        px = {s: df[df.index <= pd.Timestamp(TRAIN_END)] for s, df in px.items()}
        spy = px["SPY"]
    b = TM.make_bot(mid, "all", "all", start, MODEL_ID if ai else None)
    if ai and (MLB.load(MODEL_ID) or {}).get("risky", 0) > 0:
        b["regime"] = 0
    try:
        out = PB.simulate(b, px, spy)
    except Exception as e:
        return job, {"error": repr(e)[:300]}
    if not out.get("ok") or out.get("waiting"):
        return job, None
    st_ = R.stats(out["equity"], out["trades"], out.get("group"))
    if ai and out.get("ml_last"):
        st_["risky_share"] = out["ml_last"]["risky_days"] / max(out["ml_last"]["days"], 1)
    return job, st_


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
    import sklearn
    t0 = time.time()
    syms = sorted(set(PB.members("all", "all")) | {"SPY"})
    px = R.load_prices(syms)
    uni = [s for s in syms if s in px and s != "SPY"]
    frames = {s: PB._prep(px[s]) for s in uni}
    idx = frames[uni[0]].index
    for s in uni[1:]:
        idx = idx.union(frames[s].index)
    F = MLB.market_panel(frames, uni, idx, px["SPY"])
    print(f"features: {F.shape} in {time.time() - t0:.0f} s", flush=True)
    ew = pd.concat({s: frames[s]["Close"].astype(float).pct_change() for s in uni}, axis=1).reindex(idx).mean(axis=1).fillna(0.0)
    level = (1 + ew).cumprod()
    fwd = level.shift(-HORIZON) / level - 1
    ends = pd.Series(idx, index=idx).shift(-HORIZON)                  # the day each label is known
    y = (fwd > 0).astype(int).to_numpy()
    X = F.to_numpy(float)
    ix = pd.Series(idx, index=idx)
    fit = ((ix >= pd.Timestamp(TRAIN0)) & (ends <= pd.Timestamp(FIT_END))).to_numpy()
    val = ((ix > pd.Timestamp(FIT_END)) & (ends <= pd.Timestamp(TRAIN_END))).to_numpy()
    trn = ((ix >= pd.Timestamp(TRAIN0)) & (ends <= pd.Timestamp(TRAIN_END))).to_numpy()
    tst = ((ix >= pd.Timestamp(TEST)) & ends.notna()).to_numpy()
    clf1 = HistGradientBoostingClassifier(**HGBM).fit(X[fit], y[fit])
    p_fit = clf1.predict_proba(X[fit])[:, 1]
    p_val = clf1.predict_proba(X[val])[:, 1]
    nxt = ew.shift(-1).to_numpy()                                      # decided at the close, held from the next session
    choice = []
    for q in GATE:
        thr = -np.inf if q <= 0 else float(np.quantile(p_fit, q))
        on = p_val >= thr
        choice.append({"risky": q, "sharpe": sharpe(np.where(on, nxt[val], 0.0)), "off_days": float(1 - on.mean())})
    best = max(choice, key=lambda c: (c["sharpe"], -c["risky"]))
    if best["sharpe"] < choice[0]["sharpe"] + 0.10:
        best = choice[0]
    clf = HistGradientBoostingClassifier(**HGBM).fit(X[trn], y[trn])
    p_trn = clf.predict_proba(X[trn])[:, 1]
    thr = 0.0 if best["risky"] <= 0 else float(np.quantile(p_trn, best["risky"]))
    model = MLB.export_hgb(clf, MLB.MARKET2, id=MODEL_ID, kind="market", threshold=thr, risky=best["risky"], choice=choice,
                           trained=f"{TRAIN0}..{TRAIN_END}", horizon=HORIZON, n_train=int(trn.sum()), sklearn=sklearn.__version__,
                           made=f"{date.today():%Y-%m-%d}")
    os.makedirs(MLB.MODELS, exist_ok=True)
    with open(os.path.join(MLB.MODELS, f"{MODEL_ID}.json"), "w", encoding="utf-8") as f:
        json.dump(model, f, separators=(",", ":"))
    m = MLB.load(MODEL_ID)
    p_all_np = MLB.predict(m, X)
    assert np.abs(p_all_np - clf.predict_proba(X)[:, 1]).max() < 1e-9, "numpy and scikit-learn disagree"
    gate_np, _ = MLB.market_gate(m, frames, uni, idx, px["SPY"])
    assert (gate_np == (p_all_np >= thr)).all(), "the site's gate differs"
    auc = lambda mask, mdl: float(roc_auc_score(y[mask], mdl.predict_proba(X[mask])[:, 1])) if len(set(y[mask])) == 2 else None
    ts = ((ix >= pd.Timestamp(TEST))).to_numpy()
    on_t = p_all_np[ts] >= thr
    info = {"id": MODEL_ID, "risky": best["risky"], "threshold": thr, "choice": choice, "auc_2017_2019": auc(val, clf1),
            "auc_test": auc(tst, clf), "n_train": int(trn.sum()),
            "stocks_test": {"hold": curve(nxt[ts]), "ai": curve(np.where(on_t, nxt[ts], 0.0)), "risky_share": float(1 - on_t.mean())}}
    print(f"market model: risky {best['risky']}, AUC 2017-2019 {info['auc_2017_2019']}, AUC 2020-now {info['auc_test']}", flush=True)
    jobs = [(mid, part, ai) for mid in TM.AI_BOTS for part in ("train", "test") for ai in (False, True)]
    bots = {mid: {"id": mid, "ml": MODEL_ID, "kind": "market", "name": TM.AI_BOTS[mid]["name"], "bot": ai_settings(mid, best["risky"] > 0),
                  "plain_bot": {k: v for k, v in TM.AI_BOTS[mid].items() if k != "name"}} for mid in TM.AI_BOTS}
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2, initializer=TM._init, initargs=(px,)) as ex:
        for (mid, part, ai), st_ in ex.map(bot_job, jobs):
            if st_ and "error" in st_:
                print("error", mid, part, ai, st_["error"], flush=True)
                st_ = None
            bots[mid].setdefault("bot_" + part, {})["ai" if ai else "plain"] = st_
    out = {"updated": f"{date.today():%Y-%m-%d}", "round": 3, "train": [TRAIN0, TRAIN_END], "test_from": TEST, "model": info, "bots": bots}
    with open(os.path.join(ROOT, "ml_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float, ensure_ascii=False)
    summary(out)
    print(f"done in {(time.time() - t0) / 60:.1f} min", flush=True)


def summary(out):
    f2 = lambda v: "—" if v is None else f"{v:.2f}"
    pc = lambda v: "—" if v is None else f"{v * 100:+.0f}%"
    cell = lambda x: f"{f2(x['sharpe'])} ({pc(x['cagr'])}, {pc(x['maxdd'])})" if x else "—"
    m = out["model"]
    lines = ["# AI bots, round 3 · the market model", "",
             f"Trained on {out['train'][0]}..{out['train'][1]}; tested from {out['test_from']} (never seen). Calls the "
             f"{m['risky'] * 100:.0f}% least promising days risky (chosen on 2017-2019). AUC 2017-2019 {f2(m['auc_2017_2019'])}, "
             f"2020-now {f2(m['auc_test'])} (0.5 = a coin flip).", "",
             "Choice on 2017-2019: " + ", ".join(f"{c['risky'] * 100:.0f}% risky -> Sharpe {c['sharpe']:.2f}" for c in m["choice"]), "",
             f"The stocks 2020-now, held always: {cell(m['stocks_test']['hold'])}; held only on the days the model allows: "
             f"{cell(m['stocks_test']['ai'])} (risky days {m['stocks_test']['risky_share'] * 100:.0f}%).", "",
             "| Bot | 2020-now as it is | 2020-now with the model | 2012-2019 as it is | 2012-2019 with the model (trained here) |",
             "|---|---|---|---|---|"]
    for mid, r in out["bots"].items():
        t, tr = r.get("bot_test", {}), r.get("bot_train", {})
        lines.append(f"| {mid} | {cell(t.get('plain'))} | {cell(t.get('ai'))} | {cell(tr.get('plain'))} | {cell(tr.get('ai'))} |")
    os.makedirs(R.OUT, exist_ok=True)
    with open(os.path.join(R.OUT, "ml_market_summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
