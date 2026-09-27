"""
research/run.py - The bots' lab on real prices (runs in GitHub Actions, where Yahoo Finance can be reached).

Every strategy runs through the site's own bot engine (paperbots.simulate), on real daily prices, in two separate periods:
  in-sample     2012-01-03 .. 2019-12-31   (where ideas may be tuned)
  out-of-sample 2020-01-02 .. today        (never used for tuning: an idea is kept only if it also helps here)
Two kinds of bot per strategy:
  company bots  one bot per stock on the site's largest US companies; their equity curves averaged = "all stocks"
  sector bots   one bot per sector (up to max_pos open trades)
An experiment is a set of bot settings (see VARIANTS); config.json says which experiments run. Results go to
research/results/<experiment>.md and .json. Note: the stock lists are today's large companies (survivorship bias), so
compare a variant with the baseline, not with zero.
"""
import json
import os
import pickle
import sys
import time
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

import paperbots as PB          # noqa: E402  (the site's bot engine)
import universe as U            # noqa: E402

CACHE = os.path.join(HERE, ".cache")
OUT = os.path.join(HERE, "results")
PERIODS = {"in-sample 2012-2019": ("2012-01-03", "2019-12-31"), "out-of-sample 2020-now": ("2020-01-02", None)}
CAP = 10000.0
ALL_MAX = (10, 20)              # the all-companies bot with up to 10 / 20 open trades
FEE = 0.05                      # % per side, the site's default

# ---------------------------------------------------------------- experiments: bot settings on top of each strategy's defaults
VARIANTS = {
    "baseline": {},
    "market_filter": {"regime": 1},                        # no new buys while SPY is under its 200-day average
    "market_exit": {"regime": 2},                          # ... and sell when it drops under it
    "trend_filter": {"trend_filter": 1},                   # no new buys while the stock is under its own 200-day average
    "market_and_trend": {"regime": 1, "trend_filter": 1},
    "atr_stop_3": {"atr_mult": 3.0},                       # a stop 3 ATR under the entry
    "trailing_10": {"trail_pct": 10.0},                    # a 10% trailing stop
    "stop_8": {"stop_pct": 8.0},
    "risk_1_atr_3": {"atr_mult": 3.0, "risk_pct": 1.0},    # size each trade so the 3-ATR stop loses 1% of the balance
    "site_default": {"stop_pct": 2.0},                     # what the bot form gives when nothing is changed
    "stop_5": {"stop_pct": 5.0},
    "trend_market_exit": {"trend_filter": 1, "regime": 2},
    "trend_atr_3": {"trend_filter": 1, "atr_mult": 3.0},
}


def strategies():
    return [s for s in PB.ALL_STRATEGIES if s != PB.PB.ORB]


def bot(strategy, kind, value, start, **extra):
    max_pos = 1 if kind == "company" else 5
    if kind == "all":                                      # value "all:10" = the all-companies bot with up to 10 trades
        max_pos, value = int(str(value).split(":")[1]), "all"
    b = {"id": 0, "name": "lab", "kind": kind, "value": value, "symbol": value if kind == "company" else None,
         "strategies": {strategy: PB.clean_params(strategy, {})}, "combine": {"mode": "any"}, "instrument": "stock",
         "options": PB.clean_options(None), "max_pos": max_pos, "capital": CAP, "fee": FEE,
         "stop_pct": 0.0, "atr_mult": 0.0, "tp_pct": 0.0, "trail_pct": 0.0, "start_date": start, "valid": True,
         "risk_pct": 0.0, "fwd": None, "fwd_prev": []}
    b.update(extra)
    return b


# ---------------------------------------------------------------- prices
def load_prices(symbols):
    """Daily prices from 2009 (the indicators need a year before 2012), cached for the day."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"prices_{date.today():%Y%m%d}.pkl")
    have = {}
    if os.path.exists(path):
        have = pickle.load(open(path, "rb"))
    todo = [s for s in symbols if s not in have]
    if todo:
        import yfinance as yf
        import data
        for i in range(0, len(todo), 80):
            batch = todo[i:i + 80]
            for attempt in range(4):
                try:
                    raw = yf.download(batch, start="2009-01-01", auto_adjust=True, progress=False, threads=True, group_by="column")
                    got = data._split(raw, batch)
                    have.update({s: df[["Open", "High", "Low", "Close", "Volume"]] for s, df in got.items()})
                    break
                except Exception as e:                       # rate limits: wait and try again
                    print("download retry", attempt, e, flush=True)
                    time.sleep(20 * (attempt + 1))
            time.sleep(2)
        pickle.dump(have, open(path, "wb"))
    return have


# ---------------------------------------------------------------- one run and its numbers
def stats(eq, trades, grp, cap=CAP):
    eq = eq.dropna()
    if len(eq) < 30:
        return None
    r = eq.pct_change().dropna()
    yrs = len(eq) / 252
    g = grp.dropna() if grp is not None else None
    closed = trades[trades["Exit Reason"] != "Open"] if trades is not None and len(trades) else pd.DataFrame(columns=["P&L $"])
    wins, losses = closed.loc[closed["P&L $"] > 0, "P&L $"].sum(), -closed.loc[closed["P&L $"] < 0, "P&L $"].sum()
    out = {"cagr": (eq.iloc[-1] / cap) ** (1 / yrs) - 1 if eq.iloc[-1] > 0 else -1.0,
           "sharpe": float(r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else 0.0,
           "maxdd": float((eq / eq.cummax() - 1).min()),
           "trades_yr": len(closed) / yrs, "win": float((closed["P&L $"] > 0).mean()) if len(closed) else np.nan,
           "pf": float(wins / losses) if losses > 0 else (np.inf if wins > 0 else np.nan)}
    if g is not None and len(g) > 30:
        gr = g.pct_change().dropna()
        out.update(bh_cagr=(g.iloc[-1] / g.iloc[0]) ** (1 / yrs) - 1, bh_sharpe=float(gr.mean() / gr.std() * np.sqrt(252)) if gr.std() > 0 else 0.0,
                   bh_maxdd=float((g / g.cummax() - 1).min()))
    return out


_PX = {}


def _init(px):
    global _PX
    _PX = px


def run_one(job):
    """job = (variant, strategy, kind, value, period) -> (job, stats, equity normalised to 1)"""
    variant, strategy, kind, value, period = job
    a, b = PERIODS[period]
    px = {s: (df if b is None else df[df.index <= pd.Timestamp(b)]) for s, df in _PX.items() if s in _members(kind, value)}
    spy = _PX.get("SPY")
    if spy is not None and b is not None:
        spy = spy[spy.index <= pd.Timestamp(b)]
    try:
        out = PB.simulate(bot(strategy, kind, value, a, **VARIANTS[variant]), px, spy)
    except Exception as e:
        return job, {"error": repr(e)[:200]}, None
    if not out.get("ok") or out.get("waiting"):
        return job, None, None
    st_ = stats(out["equity"], out["trades"], out.get("group"))
    return job, st_, (out["equity"] / CAP).astype(float)


_MEM = {}


def _members(kind, value):
    key = (kind, value)
    if key not in _MEM:
        _MEM[key] = set(PB.members(kind, "all" if kind == "all" else value))
    return _MEM[key]


# ---------------------------------------------------------------- the report
def pct(v, d=1):
    return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v * 100:+.{d}f}%"


def num(v, d=2):
    return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{d}f}"


def curve_stats(curves):
    """The company bots of one strategy as one portfolio: their equity curves (each starting at 1) averaged."""
    if not curves:
        return None
    df = pd.concat(curves, axis=1).ffill()
    avg = df.mean(axis=1) * CAP
    return stats(avg, None, None)


def report(variant, rows, curves, bh_curves, n_company, sectors, secs_took):
    lines = [f"# Lab results · {variant}", "",
             f"Run {pd.Timestamp.now(tz='UTC'):%Y-%m-%d %H:%M} UTC · {n_company} company bots per strategy · sectors: {', '.join(sectors)} · "
             f"fee {FEE}% per side · took {secs_took / 60:.1f} min", "",
             "All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's "
             "Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.", ""]
    js = {"variant": variant, "settings": VARIANTS[variant], "periods": {}}
    for period in PERIODS:
        lines += [f"## {period}", "",
                  "| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD |"
                  + "".join(f" All-companies bot, {m} trades: CAGR · Sharpe · Max DD |" for m in ALL_MAX),
                  "|---|---|---|---|---|---|---|---|---|---|---|" + "---|" * len(ALL_MAX)]
        bh = curve_stats(bh_curves.get(period, []))
        per = {}
        for s in strategies():
            comp = [r for (v, st_, k, val, p), r in rows.items() if v == variant and st_ == s and k == "company" and p == period and r]
            sect = [r for (v, st_, k, val, p), r in rows.items() if v == variant and st_ == s and k == "sector" and p == period and r]
            cs = curve_stats(curves.get((s, period), []))
            if not comp or cs is None:
                continue
            med_sh = float(np.median([r["sharpe"] for r in comp]))
            beat = float(np.mean([r["sharpe"] > r.get("bh_sharpe", np.inf) for r in comp]))
            tpy = float(np.mean([r["trades_yr"] for r in comp]))
            win = float(np.nanmean([r["win"] for r in comp]))
            sc = {k: float(np.mean([r[k] for r in sect])) for k in ("cagr", "sharpe", "maxdd")} if sect else {}
            allb = {m: rows.get((variant, s, "all", f"all:{m}", period)) for m in ALL_MAX}
            per[s] = {"all": cs, "median_sharpe": med_sh, "beat_bh": beat, "trades_yr": tpy, "win": win, "sector": sc,
                      "all_bot": {str(m): v for m, v in allb.items() if v}}
            lines.append(f"| {s} | {pct(cs['cagr'])} | {num(cs['sharpe'])} | {pct(cs['maxdd'])} | {num(med_sh)} | {beat * 100:.0f}% | "
                         f"{tpy:.1f} | {win * 100:.0f}% | {pct(sc.get('cagr'))} | {num(sc.get('sharpe'))} | {pct(sc.get('maxdd'))} |"
                         + "".join(f" {pct(v['cagr'])} · {num(v['sharpe'])} · {pct(v['maxdd'])} |" if v else " — |" for v in allb.values()))
        if bh:
            lines.append(f"| **Buy & hold (same stocks)** | {pct(bh['cagr'])} | {num(bh['sharpe'])} | {pct(bh['maxdd'])} | | | | | | | |" + " |" * len(ALL_MAX))
        lines.append("")
        js["periods"][period] = {"strategies": per, "buy_hold": bh}
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, f"{variant}.md"), "w").write("\n".join(lines) + "\n")
    json.dump(js, open(os.path.join(OUT, f"{variant}.json"), "w"), indent=1, default=float)


def main():
    cfg = json.load(open(os.path.join(HERE, "config.json")))
    n = int(cfg.get("company_bots", 100))
    companies = [s for s, _ in sorted(U.STOCKS.items(), key=lambda kv: -kv[1][3])][:n]
    sectors = cfg.get("sectors", [])
    if sectors == "all":
        sectors = list(PB.sector_members())
    need = set(companies) | {"SPY"}
    for sec in sectors:
        need |= set(PB.members("sector", sec))
    if cfg.get("all_bots", True):
        need |= set(PB.members("all", "all"))
    t0 = time.time()
    px = load_prices(sorted(need))
    print(f"prices: {len(px)} of {len(need)} symbols in {time.time() - t0:.0f} s", flush=True)
    companies = [s for s in companies if s in px]
    for variant in cfg.get("experiments", ["baseline"]):
        t1 = time.time()
        jobs = [(variant, s, "company", c, p) for s in strategies() for c in companies for p in PERIODS]
        jobs += [(variant, s, "sector", sec, p) for s in strategies() for sec in sectors for p in PERIODS]
        if cfg.get("all_bots", True):
            jobs = [(variant, s, "all", f"all:{m}", p) for s in strategies() for m in ALL_MAX for p in PERIODS] + jobs
        rows, curves, bh = {}, {}, {}
        with ProcessPoolExecutor(max_workers=os.cpu_count() or 2, initializer=_init, initargs=(px,)) as ex:
            for job, st_, eq in ex.map(run_one, jobs, chunksize=8):
                rows[job] = st_
                if st_ and "error" in st_:
                    print("error", job, st_["error"], flush=True)
                    rows[job] = None
                if eq is not None and job[2] == "company":
                    curves.setdefault((job[1], job[4]), []).append(eq.rename(job[3]))
        for p, (a, b) in PERIODS.items():                           # buy and hold of the same stocks, equally weighted
            cur = []
            for c in companies:
                cl = px[c]["Close"]
                cl = cl[(cl.index >= pd.Timestamp(a)) & ((cl.index <= pd.Timestamp(b)) if b else True)]
                if len(cl) > 30:
                    cur.append((cl / cl.iloc[0]).rename(c))
            bh[p] = cur
        report(variant, rows, curves, bh, len(companies), sectors, time.time() - t1)
        print(f"{variant}: {len(jobs)} runs in {time.time() - t1:.0f} s", flush=True)


def summary():
    """One table per period: each experiment against the baseline, for the three views of every strategy."""
    runs = {}
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".json") and f != "summary.json":
            j = json.load(open(os.path.join(OUT, f)))
            runs[j["variant"]] = j
    if "baseline" not in runs:
        return
    order = ["baseline"] + [v for v in VARIANTS if v in runs and v != "baseline"]
    lines = ["# Lab summary · every experiment against the baseline", "",
             "Each cell: Sharpe (CAGR, max drawdown). Views: **stocks** = the 100 company bots averaged, **all-20** = one "
             "all-companies bot with up to 20 trades. Decide on out-of-sample; in-sample is where ideas were found.", ""]
    for period in PERIODS:
        lines += [f"## {period}", "", "| Strategy | View | " + " | ".join(order) + " |", "|---|---|" + "---|" * len(order)]
        base = runs["baseline"]["periods"].get(period, {}).get("strategies", {})
        for s in base:
            for view in ("stocks", "all-20"):
                cells = []
                for v in order:
                    st_ = runs[v]["periods"].get(period, {}).get("strategies", {}).get(s)
                    x = (st_ or {}).get("all") if view == "stocks" else ((st_ or {}).get("all_bot") or {}).get("20")
                    cells.append(f"{x['sharpe']:.2f} ({x['cagr'] * 100:+.0f}%, {x['maxdd'] * 100:.0f}%)" if x else "—")
                lines.append(f"| {s} | {view} | " + " | ".join(cells) + " |")
        bh = runs["baseline"]["periods"].get(period, {}).get("buy_hold")
        if bh:
            lines.append(f"| Buy & hold | stocks | {bh['sharpe']:.2f} ({bh['cagr'] * 100:+.0f}%, {bh['maxdd'] * 100:.0f}%) |" + " |" * (len(order) - 1))
        lines.append("")
    open(os.path.join(OUT, "summary.md"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
    summary()
