"""
research/train_ml.py - Trains the AI bots' models (mlbots.py) on real prices, and tests them on years they never saw.

For each AI bot (AI_BOTS):
 1. Labelled signals. Every stock of the all-companies list runs the bot's strategies on its own (a one-company bot with the
    same exits and filters) over 2012-2019. Each closed trade is one example: the features on its signal day (the close
    before the entry, mlbots.FEATURES) and whether it ended in a win.
 2. The model. Gradient-boosted trees (scikit-learn HistGradientBoostingClassifier, small and regularised). How many of the
    signals to keep (all of them, or the best 80 / 60 / 50 / 40 %) is chosen by training on 2012-2016 and looking at
    2017-2019 only. Then the model is trained again on all of 2012-2019 and saved as models/<id>.json; the site predicts
    with numpy (mlbots.predict), checked here to give the same numbers as scikit-learn.
 3. The test: 2020 to today. The signals of every stock are scored (win rate and average trade of the signals the model
    keeps and of those it drops, AUC), and the whole bot (all companies, the site's portfolio engine) runs with and
    without its model.
Results: research/results/ml_<id>.json, research/results/ml_summary.md, and ml_results.json at the top (for the site).
The stock list is today's large companies (survivorship bias): compare the bot with and without its model, not with zero.
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

import run as R                 # noqa: E402  (prices, stats, the lab's bot)
import paperbots as PB          # noqa: E402
import mlbots as MLB            # noqa: E402

TRAIN = ("2012-01-03", "2019-12-31")
FIT_END = "2016-12-31"          # the model that picks how many signals to keep learns up to here and is checked on 2017-2019
TEST = "2020-01-02"
KEEP = (1.0, 0.8, 0.6, 0.5, 0.4)
HGB = dict(learning_rate=0.05, max_iter=200, max_depth=3, min_samples_leaf=100, l2_regularization=1.0, early_stopping=False,
           random_state=0)
AI_BOTS = {
    "ai_sma": {"name": ["AI · SMA Crossover", "ذكاء · تقاطع المتوسطات البسيطة"], "strategies": ["SMA Crossover"],
               "max_pos": 10, "atr_mult": 3.0},
    "ai_donchian": {"name": ["AI · Donchian Breakout", "ذكاء · اختراق دونشيان"], "strategies": ["Donchian Breakout (Turtle)"],
                    "max_pos": 10, "regime": 2},
    "ai_volume": {"name": ["AI · Volume Breakout", "ذكاء · اختراق بحجم عالي"], "strategies": ["Volume Breakout"],
                  "max_pos": 20, "trend_filter": 1, "atr_mult": 3.0},
    "ai_vwma": {"name": ["AI · VWMA Crossover", "ذكاء · المتوسط المرجّح بالحجم"], "strategies": ["VWMA Crossover (Volume)"],
                "max_pos": 10, "trend_filter": 1, "regime": 2},
    "ai_setups": {"name": ["AI · Combined setups", "ذكاء · الإعدادات المركّبة"],
                  "strategies": ["Trend Pullback", "Squeeze Breakout", "Breakout & Retest"], "max_pos": 20, "regime": 2},
}
SETTINGS = ("stop_pct", "atr_mult", "tp_pct", "trail_pct", "risk_pct", "regime", "trend_filter")


def make_bot(mid, kind, value, start, ml=None):
    c = AI_BOTS[mid]
    b = {"id": 0, "name": mid, "kind": kind, "value": value, "symbol": value if kind == "company" else None,
         "strategies": {s: PB.clean_params(s, {}) for s in c["strategies"]}, "combine": {"mode": "any"}, "instrument": "stock",
         "options": PB.clean_options(None), "max_pos": 1 if kind == "company" else c["max_pos"], "capital": R.CAP, "fee": R.FEE,
         "start_date": start, "valid": True, "fwd": None, "fwd_prev": [], "ml": ml}
    b.update({k: c.get(k, 0.0) for k in SETTINGS})
    return b


_PX = {}


def _init(px):
    global _PX
    _PX = px


def label_job(job):
    """(bot id, symbol, 'train' | 'test') -> the stock's closed trades as examples: its own features on the signal day."""
    mid, sym, part = job
    df, spy = _PX.get(sym), _PX.get("SPY")
    if df is None or spy is None:
        return job, None
    if part == "train":
        df, spy, start = df[df.index <= pd.Timestamp(TRAIN[1])], spy[spy.index <= pd.Timestamp(TRAIN[1])], TRAIN[0]
    else:
        start = TEST
    try:
        b = make_bot(mid, "company", sym, start)
        out = PB.simulate(b, {sym: df}, spy)
    except Exception as e:
        return job, {"error": repr(e)[:200]}
    if not out.get("ok") or out.get("waiting") or not len(out["trades"]):
        return job, None
    tr = out["trades"]
    tr = tr[tr["Exit Reason"] != "Open"]
    if not len(tr):
        return job, None
    d = PB._prep(df)
    names = [s for s in PB.ALL_STRATEGIES if s in b["strategies"]]
    f = MLB.stock_features(d)
    pos = [d.index.get_loc(pd.Timestamp(x)) - 1 for x in tr["Entry Date"]]
    keep = [i for i, p in enumerate(pos) if p >= 0]
    rows = f.iloc[[pos[i] for i in keep]][MLB.STOCK].reset_index(drop=True)
    rows["date"] = [d.index[pos[i]] for i in keep]
    rows["sym"] = sym
    rows["strat"] = [float(names.index(tr["Strategy"].iloc[i])) if tr["Strategy"].iloc[i] in names else 0.0 for i in keep]
    rows["pnl"] = tr["P&L %"].to_numpy(float)[keep]
    rows["y"] = (rows["pnl"] > 0).astype(int)
    return job, rows


def market_and_rank(px, syms):
    """The market features and every stock's 60-day-return rank, on the dates of all the stocks (as in an all-companies bot)."""
    r60 = pd.concat({s: PB._prep(px[s])["Close"].astype(float).pct_change(60) for s in syms if s in px}, axis=1).sort_index()
    rank = r60.rank(axis=1, pct=True)
    mk = MLB.market_features(px["SPY"], r60.index)
    return rank, mk


def assemble(rows, rank, mk):
    rows = rows.copy()
    rows["rs60"] = [rank.at[d, s] if d in rank.index else np.nan for d, s in zip(rows["date"], rows["sym"])]
    m = mk.reindex(pd.DatetimeIndex(rows["date"]))
    for k in MLB.MARKET:
        rows[k] = m[k].to_numpy(float)
    return rows


def sig_stats(pnl, kept):
    pnl = np.asarray(pnl, float)
    out = {}
    for name, m in (("all", np.ones(len(pnl), bool)), ("kept", kept), ("dropped", ~kept)):
        x = pnl[m]
        out[name] = {"n": int(len(x)), "win": float((x > 0).mean()) if len(x) else None, "avg": float(x.mean()) if len(x) else None}
    return out


def tstat(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 30 and x.std(ddof=1) > 0 else -np.inf


def train(mid, D):
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
    import sklearn
    X, y, pnl = D[MLB.FEATURES].to_numpy(float), D["y"].to_numpy(int), D["pnl"].to_numpy(float)
    fit = (D["date"] <= pd.Timestamp(FIT_END)).to_numpy()
    val = ~fit
    clf1 = HistGradientBoostingClassifier(**HGB).fit(X[fit], y[fit])
    p_fit, p_val = clf1.predict_proba(X[fit])[:, 1], clf1.predict_proba(X[val])[:, 1]
    choice = []
    for q in KEEP:
        thr = -np.inf if q >= 1 else float(np.quantile(p_fit, 1 - q))
        k = p_val >= thr
        choice.append({"keep": q, "n": int(k.sum()), "win": float(y[val][k].mean()) if k.any() else None,
                       "avg": float(pnl[val][k].mean()) if k.any() else None, "t": tstat(pnl[val][k])})
    best = max(choice, key=lambda c: (c["t"], c["keep"]))
    clf = HistGradientBoostingClassifier(**HGB).fit(X, y)
    p_all = clf.predict_proba(X)[:, 1]
    thr = 0.0 if best["keep"] >= 1 else float(np.quantile(p_all, 1 - best["keep"]))
    auc_val = float(roc_auc_score(y[val], p_val)) if len(set(y[val])) == 2 else None
    c = AI_BOTS[mid]
    model = MLB.export_hgb(clf, MLB.FEATURES, id=mid, name=c["name"], threshold=thr, keep=best["keep"],
                           bot={k: v for k, v in c.items() if k != "name"}, trained=f"{TRAIN[0]}..{TRAIN[1]}",
                           n_train=int(len(y)), win_train=float(y.mean()), auc_2017_2019=auc_val, choice=choice,
                           sklearn=sklearn.__version__, made=f"{date.today():%Y-%m-%d}")
    return clf, model


def run_bot(job):
    """(bot id, 'train' | 'test', ml or None) -> the all-companies bot's numbers."""
    mid, part, ml = job
    px, spy = dict(_PX), _PX["SPY"]
    start = TRAIN[0] if part == "train" else TEST
    if part == "train":
        px = {s: df[df.index <= pd.Timestamp(TRAIN[1])] for s, df in px.items()}
        spy = px["SPY"]
    try:
        out = PB.simulate(make_bot(mid, "all", "all", start, ml), px, spy)
    except Exception as e:
        return job, {"error": repr(e)[:300]}
    if not out.get("ok") or out.get("waiting"):
        return job, None
    return job, R.stats(out["equity"], out["trades"], out.get("group"))


def main():
    t0 = time.time()
    syms = sorted(set(PB.members("all", "all")) | {"SPY"})
    px = R.load_prices(syms)
    print(f"prices: {len(px)} of {len(syms)} in {time.time() - t0:.0f} s", flush=True)
    uni = [s for s in syms if s in px and s != "SPY"]
    rank, mk = market_and_rank(px, uni)
    os.makedirs(MLB.MODELS, exist_ok=True)
    jobs = [(mid, s, part) for mid in AI_BOTS for s in uni for part in ("train", "test")]
    ex_rows = {}
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2, initializer=_init, initargs=(px,)) as ex:
        for (mid, s, part), rows in ex.map(label_job, jobs, chunksize=16):
            if isinstance(rows, dict):
                print("error", mid, s, part, rows["error"], flush=True)
            elif rows is not None and len(rows):
                ex_rows.setdefault((mid, part), []).append(rows)
    print(f"labelled signals in {time.time() - t0:.0f} s", flush=True)
    results = {}
    for mid in list(AI_BOTS):
        if len(ex_rows.get((mid, "train"), [])) == 0 or sum(map(len, ex_rows[(mid, "train")])) < 300 or not ex_rows.get((mid, "test")):
            print(f"{mid}: too few signals to learn from, skipped", flush=True)
            continue
        tr_ = assemble(pd.concat(ex_rows[(mid, "train")], ignore_index=True), rank, mk)
        te_ = assemble(pd.concat(ex_rows[(mid, "test")], ignore_index=True), rank, mk)
        clf, model = train(mid, tr_)
        path = os.path.join(MLB.MODELS, f"{mid}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(model, f, separators=(",", ":"))
        m = MLB.load(mid)
        Xte = te_[MLB.FEATURES].to_numpy(float)
        p_np, p_sk = MLB.predict(m, Xte), clf.predict_proba(Xte)[:, 1]
        assert np.abs(p_np - p_sk).max() < 1e-9, "numpy and scikit-learn disagree"
        # the site computes the same features (a sample, through mlbots.features_at on the whole list)
        smp = te_.sample(min(40, len(te_)), random_state=1)
        frames = {s: PB._prep(px[s]) for s in uni}
        idx = rank.index
        pos = {s: j for j, s in enumerate(uni)}
        Xs = MLB.features_at(frames, uni, idx, px["SPY"], [idx.get_loc(d) for d in smp["date"]], [pos[s] for s in smp["sym"]],
                             smp["strat"].to_numpy(float))
        assert np.allclose(Xs, smp[MLB.FEATURES].to_numpy(float), equal_nan=True, atol=1e-10), "training and site features differ"
        from sklearn.metrics import roc_auc_score
        kept = p_np >= m["threshold"]
        results[mid] = {"id": mid, "name": model["name"], "bot": model["bot"], "keep": model["keep"], "threshold": model["threshold"],
                        "n_train": model["n_train"], "win_train": model["win_train"], "auc_2017_2019": model["auc_2017_2019"],
                        "choice": model["choice"],
                        "signals_test": sig_stats(te_["pnl"], kept),
                        "auc_test": float(roc_auc_score(te_["y"], p_np)) if te_["y"].nunique() == 2 else None}
        print(f"{mid}: {len(tr_)} train / {len(te_)} test signals, keep {model['keep']}, test AUC {results[mid]['auc_test']}", flush=True)
    jobs = [(mid, part, ml) for mid in results for part in ("train", "test") for ml in (None, mid)]
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2, initializer=_init, initargs=(px,)) as ex:
        for (mid, part, ml), st_ in ex.map(run_bot, jobs):
            if st_ and "error" in st_:
                print("error", mid, part, ml, st_["error"], flush=True)
                st_ = None
            results[mid].setdefault("bot_" + part, {})["ai" if ml else "plain"] = st_
    out = {"updated": f"{date.today():%Y-%m-%d}", "train": list(TRAIN), "test_from": TEST, "bots": results}
    os.makedirs(R.OUT, exist_ok=True)
    with open(os.path.join(ROOT, "ml_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float, ensure_ascii=False)
    summary(out)
    print(f"done in {(time.time() - t0) / 60:.1f} min", flush=True)


def summary(out):
    f2 = lambda v: "—" if v is None else f"{v:.2f}"
    pc = lambda v: "—" if v is None else f"{v * 100:+.0f}%"
    wp = lambda v: "—" if v is None else f"{v * 100:.0f}%"
    lines = ["# AI bots · with and without the model", "",
             f"Trained on signals of {out['train'][0]}..{out['train'][1]}; tested from {out['test_from']} (never seen).", "",
             "| Bot | Keeps | Test AUC | Test win % kept / dropped | Test avg trade kept / dropped | Bot 2020-now plain: Sharpe (CAGR, max DD) | Bot 2020-now AI |",
             "|---|---|---|---|---|---|---|"]
    for mid, r in out["bots"].items():
        s = r["signals_test"]
        bt = r.get("bot_test", {})
        cell = lambda x: f"{f2(x['sharpe'])} ({pc(x['cagr'])}, {pc(x['maxdd'])})" if x else "—"
        lines.append(f"| {mid} | {r['keep'] * 100:.0f}% | {f2(r['auc_test'])} | "
                     f"{wp(s['kept']['win'])} / {wp(s['dropped']['win'])} | {f2(s['kept']['avg'])}% / {f2(s['dropped']['avg'])}% | "
                     f"{cell(bt.get('plain'))} | {cell(bt.get('ai'))} |")
    lines += ["", "In-sample (2012-2019, the model was trained here, so the AI numbers are optimistic):", "",
              "| Bot | plain | AI |", "|---|---|---|"]
    for mid, r in out["bots"].items():
        b = r.get("bot_train", {})
        cell = lambda x: f"{f2(x['sharpe'])} ({pc(x['cagr'])}, {pc(x['maxdd'])})" if x else "—"
        lines.append(f"| {mid} | {cell(b.get('plain'))} | {cell(b.get('ai'))} |")
    with open(os.path.join(R.OUT, "ml_summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
