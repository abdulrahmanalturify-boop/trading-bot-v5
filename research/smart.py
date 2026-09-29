"""
research/smart.py - The five smart bots (smartbots.py) on real prices, period by period (runs in GitHub Actions, where
Yahoo Finance can be reached). Writes smart_results.json (read by the Paper Bots page) and research/results/smart.md.

Each bot runs ONCE through the site's own engine (paperbots.simulate) from 2007-01-03 to today on all companies, with
100,000 of virtual money and 0.10% per side for the fee and the slippage. Its balance is then read period by period:
  2008-2009 financial crisis · 2010-2014 · 2015-2019 · 2020 (COVID crash and rebound) · 2021 · 2022 bear market · 2023-now,
  in-sample 2010-2019 (where the ideas behind the settings come from) and out-of-sample 2020-now (never looked at while
  the settings were fixed), and the whole 2008-now.
Each period is compared with the S&P 500 (SPY) and with holding all the same stocks equally (bought at the period's start).
Variants of every bot show what each part adds and how sensitive it is: the same strategies without the brain, the brain
without the regimes / the score / the self-check, and the minimum score and the ATR stop moved up and down.
Note: the stock list is today's S&P 500 (survivorship bias): every number back in time is on the high side, so compare a
bot with holding the same stocks, not with zero.
"""
import json
import os
import pickle
import sys
import time
import traceback
import warnings
from concurrent.futures import ProcessPoolExecutor
from datetime import date

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")
os.environ.setdefault("STREAMLIT_LOG_LEVEL", "error")

import brain as BR              # noqa: E402
import paperbots as PB          # noqa: E402
import smartbots as SB          # noqa: E402

CACHE = os.path.join(HERE, ".cache")
OUT = os.path.join(HERE, "results")
START = "2007-01-03"
CAP = 100000.0
PERIODS = [("crisis", "2008-2009 crisis", "2008-01-02", "2009-12-31"), ("y10", "2010-2014", "2010-01-04", "2014-12-31"),
           ("y15", "2015-2019", "2015-01-02", "2019-12-31"), ("y20", "2020 COVID", "2020-01-02", "2020-12-31"),
           ("y21", "2021", "2021-01-04", "2021-12-31"), ("y22", "2022 bear market", "2022-01-03", "2022-12-30"),
           ("y23", "2023-now", "2023-01-03", None),
           ("ins", "In-sample 2010-2019", "2010-01-04", "2019-12-31"), ("oos", "Out-of-sample 2020-now", "2020-01-02", None),
           ("full", "Whole test 2008-now", "2008-01-02", None)]


def variants(key):
    """name -> (strategies, max_pos, brain or None, atr) for one bot."""
    b = SB.BOTS[key]
    br = BR.clean(b["brain"])
    v = {"smart": br,
         "plain": None,
         "no_regime": {**br, "allow": {r: list(BR.FAMILIES) for r in BR.REGIMES}, "exit": [],
                       "size": {r: 1.0 for r in BR.REGIMES}, "exposure": {r: 1.0 for r in BR.REGIMES}},
         "no_score": {**br, "min_score": 0.0},
         "no_selfcheck": {**br, "decay": 0, "streak": 0, "pause": 0, "day_loss": 0.0},
         "score_m10": {**br, "min_score": max(br["min_score"] - 10, 0)},
         "score_p10": {**br, "min_score": min(br["min_score"] + 10, 100)},
         "atr_m": {**br, "atr": br["atr"] - 0.5},
         "atr_p": {**br, "atr": br["atr"] + 0.5}}
    return {n: (b["strategies"], b["max_pos"], (BR.clean(x) if x else None), (x or br)["atr"]) for n, x in v.items()}


def make_bot(strategies, max_pos, brain, atr):
    return {"id": 0, "name": "smart", "kind": "all", "value": "all", "symbol": None,
            "strategies": {s: PB.clean_params(s, p) for s, p in strategies.items()}, "combine": {"mode": "any"},
            "instrument": "stock", "options": PB.clean_options(None), "max_pos": max_pos, "capital": CAP, "fee": SB.FEE,
            "stop_pct": 0.0, "atr_mult": float(atr), "tp_pct": 0.0, "trail_pct": 0.0, "start_date": START, "valid": True,
            "risk_pct": 0.0, "regime": 0, "trend_filter": 0, "ml": None, "brain": brain, "fwd": None, "fwd_prev": []}


# ---------------------------------------------------------------- prices
def load_prices(symbols):
    """Daily prices from 2005 (the indicators need two years before the test starts), cached for the day."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"smart_prices_{date.today():%Y%m%d}.pkl")
    have = pickle.load(open(path, "rb")) if os.path.exists(path) else {}
    todo = [s for s in symbols if s not in have]
    if todo:
        import yfinance as yf
        import data
        for i in range(0, len(todo), 80):
            batch = todo[i:i + 80]
            for attempt in range(4):
                try:
                    raw = yf.download(batch, start="2005-01-01", auto_adjust=True, progress=False, threads=True, group_by="column")
                    got = data._split(raw, batch)
                    have.update({s: df[["Open", "High", "Low", "Close", "Volume"]] for s, df in got.items()})
                    break
                except Exception as e:
                    print("download retry", attempt, e, flush=True)
                    time.sleep(20 * (attempt + 1))
            time.sleep(2)
        pickle.dump(have, open(path, "wb"))
    return have


# ---------------------------------------------------------------- numbers
def window(s, a, b):
    s = s.dropna()
    return s[(s.index >= pd.Timestamp(a)) & ((s.index <= pd.Timestamp(b)) if b else True)]


def curve_stats(eq):
    """Return, yearly return, Sharpe and max drop of a balance curve (None when too short)."""
    if eq is None or len(eq) < 20:
        return None
    r = eq.pct_change().dropna()
    yrs = max(len(eq) / 252, 1 / 252)
    tot = float(eq.iloc[-1] / eq.iloc[0] - 1)
    return {"ret": tot, "cagr": float((1 + tot) ** (1 / yrs) - 1) if tot > -1 else -1.0,
            "sharpe": float(r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else 0.0,
            "maxdd": float((eq / eq.cummax() - 1).min())}


def trade_stats(tr, a, b):
    """The trades closed in the period: how many a year, share of winners, profit factor."""
    if tr is None or not len(tr):
        return {"n": 0}
    x = tr[tr["Exit Reason"] != "Open"]
    ed = pd.to_datetime(x["Exit Date"])
    ed = ed.dt.tz_localize(None) if getattr(ed.dt, "tz", None) is not None else ed
    x = x[(ed >= pd.Timestamp(a)) & ((ed <= pd.Timestamp(b)) if b else True)]
    if not len(x):
        return {"n": 0}
    w, l_ = x.loc[x["P&L $"] > 0, "P&L $"].sum(), -x.loc[x["P&L $"] < 0, "P&L $"].sum()
    return {"n": int(len(x)), "win": float((x["P&L $"] > 0).mean()), "pf": float(w / l_) if l_ > 0 else None,
            "avg": float(x["P&L %"].mean())}


def ew_hold(px, syms, a, b):
    """All the stocks bought equally at the period's first session and held (the stocks with prices by then)."""
    cur = []
    for s in syms:
        df = px.get(s)
        if df is None:
            continue
        c = window(df["Close"].astype(float), a, b)
        if len(c) > 20 and c.index[0] <= pd.Timestamp(a) + pd.Timedelta(days=10):
            cur.append(c / c.iloc[0])
    if not cur:
        return None
    return pd.concat(cur, axis=1).ffill().mean(axis=1) * CAP


_PX = {}


def _init(px):
    global _PX
    _PX = px


def run_one(job):
    key, var = job
    strategies, max_pos, brain, atr = variants(key)[var]
    t0 = time.time()
    try:
        px = {s: _PX[s] for s in PB.members("all", "all") if s in _PX}
        out = PB.simulate(make_bot(strategies, max_pos, brain, atr), px, _PX.get("SPY"))
    except Exception:
        return job, {"error": traceback.format_exc()[-1500:]}
    if not out.get("ok") or out.get("waiting"):
        return job, {"error": f"not run: {out.get('why')}"}
    eq, tr = out["equity"], out["trades"]
    eq.index = pd.DatetimeIndex(eq.index).tz_localize(None) if pd.DatetimeIndex(eq.index).tz is not None else eq.index
    res = {"periods": {}, "secs": round(time.time() - t0, 1), "trades_total": int((tr["Exit Reason"] != "Open").sum())}
    for pk, _, a, b in PERIODS:
        st_ = curve_stats(window(eq, a, b))
        if st_:
            inv = window(out["invested"].set_axis(eq.index), a, b)
            res["periods"][pk] = {**st_, **{"t_" + k: v for k, v in trade_stats(tr, a, b).items()}, "invested": float(inv.mean())}
    if var == "smart":
        bb = out.get("brain") or {}
        codes = pd.Series(bb.get("series") or [], index=eq.index[:len(bb.get("series") or [])])
        r = eq.pct_change()
        prev = codes.shift(1)
        by_reg = {}
        for i, nm in enumerate(BR.REGIMES):                    # the bot's daily return by the regime of the session before
            rr = r[prev == i].dropna()
            if len(rr) > 10:
                by_reg[nm] = {"days": int(len(rr)), "ann": float(rr.mean() * 252), "sharpe": float(rr.mean() / rr.std() * np.sqrt(252)) if rr.std() > 0 else 0.0}
        closed = tr[tr["Exit Reason"] != "Open"]
        by_str = {s: {"n": int(len(g)), "pnl": float(g["P&L $"].sum()), "win": float((g["P&L $"] > 0).mean())}
                  for s, g in closed.groupby("Strategy")}
        exits = {k: int(v) for k, v in closed["Exit Reason"].value_counts().items()}
        monthly = (eq.resample("ME").last() / CAP).round(4)
        res.update(by_regime=by_reg, by_strategy=by_str, exits=exits, blocked=bb.get("blocked"), pauses=bb.get("pauses"),
                   regime_days=bb.get("regime_days"), regime_now=bb.get("regime"),
                   curve={"d": [f"{d:%Y-%m}" for d in monthly.index], "v": monthly.tolist()})
    return job, res


def pct(v, d=0):
    return "—" if v is None else f"{v * 100:+.{d}f}%"


def main():
    t0 = time.time()
    syms = PB.members("all", "all")
    px = load_prices(sorted(set(syms) | {"SPY"}))
    print(f"prices: {len(px)} of {len(syms) + 1} symbols in {time.time() - t0:.0f} s", flush=True)
    spy = px["SPY"]
    jobs = [(k, v) for k in SB.ORDER for v in variants(k)]
    rows = {}
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2, initializer=_init, initargs=(px,)) as ex:
        for job, res in ex.map(run_one, jobs):
            rows[job] = res
            print(job, "error" if "error" in res else f"{res['secs']} s", res.get("error", ""), flush=True)
    bench = {}
    for pk, _, a, b in PERIODS:
        sc = spy["Close"].astype(float)
        sc.index = pd.DatetimeIndex(sc.index).tz_localize(None) if pd.DatetimeIndex(sc.index).tz is not None else sc.index
        bench[pk] = {"spy": curve_stats(window(sc, a, b)), "hold": curve_stats(ew_hold(px, syms, a, b))}
    spy_m = window(sc, "2007-01-03", None)
    spy_m = (spy_m.resample("ME").last() / float(spy_m.iloc[0])).round(4)
    js = {"run": f"{pd.Timestamp.now(tz='UTC'):%Y-%m-%d %H:%M} UTC", "start": START, "capital": CAP, "fee": SB.FEE,
          "n_stocks": len([s for s in syms if s in px]), "periods": [{"key": k, "name": n, "from": a, "to": b} for k, n, a, b in PERIODS],
          "bench": bench, "spy_curve": {"d": [f"{d:%Y-%m}" for d in spy_m.index], "v": spy_m.tolist()},
          "bots": {k: {v: rows[(k, v)] for v in variants(k)} for k in SB.ORDER}}
    json.dump(js, open(os.path.join(ROOT, "smart_results.json"), "w"), indent=0, default=float)
    # the report
    L = [f"# Smart bots · period test", "", f"Run {js['run']} · {js['n_stocks']} stocks · from {START} · fee+slippage {SB.FEE}% per side · "
         f"took {(time.time() - t0) / 60:.0f} min", "",
         "Each cell: return of the period (yearly for multi-year periods), Sharpe, max drop. Hold = all the same stocks bought "
         "equally at the start of the period. Survivorship bias: today's S&P 500 list, so compare with Hold.", ""]
    head = "| Bot · variant | " + " | ".join(n for _, n, _, _ in PERIODS) + " |"
    L += [head, "|---|" + "---|" * len(PERIODS)]

    def cell(x):
        if not x:
            return "—"
        main_ = x["ret"] if x.get("cagr") is None or abs(x["ret"] - x["cagr"]) < 1e-9 else x["cagr"]
        return f"{pct(main_)} · {x['sharpe']:.2f} · {pct(x['maxdd'])}"
    for k in SB.ORDER:
        for v in variants(k):
            r = rows[(k, v)]
            if "error" in r:
                L.append(f"| {k} · {v} | error |" + " |" * (len(PERIODS) - 1))
                continue
            L.append(f"| {'**' + k + '**' if v == 'smart' else k} · {v} | " + " | ".join(cell(r["periods"].get(pk)) for pk, _, _, _ in PERIODS) + " |")
        L.append("| | " + " |" * len(PERIODS))
    L.append("| S&P 500 (SPY) | " + " | ".join(cell(bench[pk]["spy"]) for pk, _, _, _ in PERIODS) + " |")
    L.append("| Hold all the stocks | " + " | ".join(cell(bench[pk]["hold"]) for pk, _, _, _ in PERIODS) + " |")
    L += ["", "## Inside each smart bot", ""]
    for k in SB.ORDER:
        r = rows[(k, "smart")]
        if "error" in r:
            L += [f"### {k}: error", "", "```", r["error"], "```", ""]
            continue
        L += [f"### {SB.BOTS[k]['name'][0]}", "", f"Closed trades {r['trades_total']} · exits {r.get('exits')} · sessions blocked {r.get('blocked')} · "
              f"pauses {r.get('pauses')} · regime days {r.get('regime_days')} · regime now {r.get('regime_now')}", "",
              "By regime (the session before): " + ", ".join(f"{n} {x['days']} days {pct(x['ann'])}/yr Sharpe {x['sharpe']:.2f}"
                                                              for n, x in (r.get("by_regime") or {}).items()), "",
              "By strategy: " + ", ".join(f"{s} {x['n']} trades {x['pnl']:+,.0f} win {x['win'] * 100:.0f}%" for s, x in (r.get("by_strategy") or {}).items()), ""]
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "smart.md"), "w").write("\n".join(L) + "\n")
    print(f"done in {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
