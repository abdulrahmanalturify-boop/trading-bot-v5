"""research/factor_test.py - which statistical factors rank S&P 500 stocks for the next 20 sessions over SPY?

Run by .github/workflows/factor-test.yml (GitHub Actions reaches Yahoo and the SEC; the Claude container does not).

At every month-end from 2013, for each of today's S&P 500 members:
  * the four price factors Hunter V3 ranks by (momentum, trend, low risk, short-term reversal), from hunter_v3.features_for,
  * value (earnings, book and operating cash-flow yields) and financial quality (ROE, gross profitability, low leverage,
    low accruals) from the SEC company facts KNOWN ON THAT DAY (fundamentals.as_of: a fact counts from its filing date),
plus classic 12-1 momentum (the year's return over SPY, skipping the last month), each as a percentile among the stocks that
day; the outcome is the stock's return over SPY in the next 20, 60 and 120 sessions (20 is the label hunter_v3 trains on). Every factor and blend gets its monthly rank IC (Spearman), t-stat, hit rate, and the
top-fifth minus bottom-fifth spread, on 2013-2019 (training) and 2020 on (testing) separately.

The decision is fixed before the run (DECISION below): the weights come only from the training years, and the blend
the page uses is the one that does best in the testing years among the pre-declared candidates.

Known limits, printed with the results: today's members only (survivorship bias: it flatters every factor's absolute
returns, and may favour low risk and quality), no trading costs, monthly snapshots, Yahoo's adjusted prices.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import fundamentals as F
import hunter_v3 as V3
from sp500 import SP500

START, TRAIN_END, DOWNLOAD_FROM = "2013-01-01", "2019-12-31", "2011-06-01"
OUT_JSON = ROOT / "research" / "results" / "factor_test.json"
OUT_MD = ROOT / "research" / "results" / "factor_test.md"
MIN_NAMES = 50                                      # a month needs this many stocks with a value to count
HORIZONS = (20, 60, 120)                            # sessions ahead: about one, three and six months
PRICE_FEATURES = sorted({c for _, cols, _ in V3.FACTORS for c, _ in cols}) + ["mom_12_1"]
GROUPS = {name: cols for name, cols, _ in V3.FACTORS}
GROUPS["Momentum 12-1"] = (("mom_12_1", 1),)        # the classic one: the year's return over the index, skipping the last month
GROUPS["Value"] = tuple((c, 1) for c in F.VALUE)
GROUPS["Quality"] = tuple((c, 1) for c in F.QUALITY)
DECISION = ("For each horizon: candidates are the current V3 blend (four price factors, 35/25/25/15), all seven groups "
            "(the four, classic 12-1 momentum, value, quality) equally weighted, and an "
            "IC-weighted blend (weights proportional to each group's training-years mean IC, zero when it is not positive). "
            "Chosen: the candidate with the highest testing-years mean IC whose testing t-stat is at least 2; if none reaches 2, "
            "the highest testing IC, flagged as weak. A group whose training IC is not positive gets no weight.")


# ---------------------------------------------------------------- data
def load_prices(symbols):
    import yfinance as yf
    tick = {s: s.replace(".", "-") for s in symbols}
    raw = yf.download(list(tick.values()) + ["SPY"], start=DOWNLOAD_FROM, auto_adjust=False, actions=True,
                      group_by="ticker", threads=True, progress=False)
    out = {}
    for s, t in list(tick.items()) + [("SPY", "SPY")]:
        try:
            d = raw[t].dropna(subset=["Close", "Adj Close"])
        except KeyError:
            continue
        if len(d) < 300:
            continue
        k = (d["Adj Close"] / d["Close"]).astype(float)          # dividends too: total-return prices for the features
        out[s] = pd.DataFrame({"Open": d["Open"] * k, "High": d["High"] * k, "Low": d["Low"] * k, "Close": d["Adj Close"],
                               "Volume": d["Volume"], "Split Close": d["Close"],
                               "Splits": d.get("Stock Splits", pd.Series(0.0, index=d.index)).fillna(0.0)})
        out[s].index = pd.to_datetime(out[s].index).tz_localize(None)
    return out


def load_facts(symbols):
    ciks = F.cik_map()
    facts, missing = {}, []
    for i, s in enumerate(symbols):
        cik = ciks.get(s.replace(".", "-")) or ciks.get(s.replace("-", ""))
        if not cik:
            missing.append(s)
            continue
        for attempt in range(3):
            try:
                facts[s] = F.fetch(cik)
                break
            except Exception as exc:                 # noqa: BLE001 - one company never stops the run
                if attempt == 2:
                    missing.append(s)
                    print(f"  no facts for {s}: {exc}", flush=True)
                time.sleep(2 * (attempt + 1))
        if i % 50 == 0:
            print(f"  facts {i}/{len(symbols)}", flush=True)
    return facts, missing


def split_factor_after(splits, when):
    """How many of today's shares one share of `when` became (the product of the splits after it)."""
    s = splits[(splits.index > pd.Timestamp(when)) & (splits > 0)]
    return float(np.prod(s.to_numpy())) if len(s) else 1.0


# ---------------------------------------------------------------- the panel
def panel(prices, facts):
    spy = prices["SPY"]
    days = spy.index[spy.index >= pd.Timestamp(START)]
    ends = pd.Series(days, index=days).groupby([days.year, days.month]).last().tolist()
    ends = [d for d in ends if spy.index.get_loc(d) + min(HORIZONS) < len(spy)]     # an outcome must be known
    b = spy["Close"]
    rows = []
    for s, d in prices.items():
        if s == "SPY":
            continue
        x, y = V3.features_for(d, spy)
        c, bb = d["Close"], b.reindex(d.index, method="ffill", limit=3)
        x["mom_12_1"] = (c.shift(21) / c.shift(252) - 1) - (bb.shift(21) / bb.shift(252) - 1)
        fwd = {h: (c.shift(-h) / c - 1) - (bb.shift(-h) / bb - 1) for h in HORIZONS}     # known only h sessions later
        sector = SP500.get(s, ("", "", ""))[1]
        f = facts.get(s)
        fund = dict(zip(sorted(ends), F.known(f, sorted(ends)))) if f else {}
        for e in ends:
            if e not in x.index or not np.isfinite(y.get(e, np.nan)):
                continue
            r = {"date": e, "symbol": s, "sector": sector, "label": float(y[e])}
            r.update({f"label_{h}": float(fwd[h].get(e, np.nan)) for h in HORIZONS})
            r.update({c: float(x.at[e, c]) for c in PRICE_FEATURES})
            if f:
                m = fund[e]
                mcap = np.nan
                if np.isfinite(m["shares"]):
                    mcap = float(d.at[e, "Split Close"]) * m["shares"] * split_factor_after(d["Splits"], m["shares_end"])
                r.update(F.ratios(m, mcap))
            rows.append(r)
    p = pd.DataFrame(rows)
    for c in F.VALUE + F.QUALITY:
        if c not in p:
            p[c] = np.nan
    return p.replace([np.inf, -np.inf], np.nan)


def pctl(g, col, sign=1, by=None):
    v = g[col] * sign
    if by is None:
        return v.rank(pct=True) * 100
    return v.groupby(g[by]).rank(pct=True) * 100


def scores(p):
    """Group scores per month: each input a percentile that month (within the sector for the *_sn variants)."""
    out = []
    for _, g in p.groupby("date"):
        g = g.copy()
        for name, cols in GROUPS.items():
            g[name] = pd.concat([pctl(g, c, sg) for c, sg in cols], axis=1).mean(axis=1, skipna=True)
            if name in ("Value", "Quality"):
                g[name + " (in sector)"] = pd.concat([pctl(g, c, sg, "sector") for c, sg in cols], axis=1).mean(axis=1, skipna=True)
        for c in PRICE_FEATURES + list(F.VALUE + F.QUALITY):
            g["f:" + c] = pctl(g, c)
        out.append(g)
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------- the measures
def measure(s, col, label="label_20", h=20):
    """Monthly rank IC and spread. With an outcome longer than a month the monthly samples overlap, so the t-stat counts
    n * 21 / h independent months instead of n."""
    ics, spreads = [], []
    for _, g in s.groupby("date"):
        g = g[[col, label]].dropna().rename(columns={label: "label"})
        if len(g) < MIN_NAMES or g[col].nunique() < 5:
            continue
        ics.append(g[col].rank().corr(g["label"].rank()))
        q = g[col].rank(pct=True)
        spreads.append(g.loc[q > .8, "label"].mean() - g.loc[q <= .2, "label"].mean())
    ics, spreads = np.asarray(ics, float), np.asarray(spreads, float)
    n = len(ics)
    if n < 6:
        return {"months": n}
    sd, eff = ics.std(ddof=1), n * min(1.0, 21 / h)
    per_year = 252 / h                                # non-overlapping periods a year, for the spread's Sharpe
    return {"months": n, "ic": round(float(ics.mean()), 4), "t": round(float(ics.mean() / sd * np.sqrt(eff)), 2) if sd > 0 else None,
            "hit": round(float((ics > 0).mean()), 3), "spread_pct": round(100 * float(spreads.mean()), 3),
            "ls_sharpe": round(float(spreads.mean() / spreads.std(ddof=1) * np.sqrt(per_year)), 2) if spreads.std(ddof=1) > 0 else None}


def blend(s, weights):
    w = {k: v for k, v in weights.items() if v > 0}
    tot = sum(w.values())
    return sum(v * s[k].fillna(50.0) for k, v in w.items()) / tot


def evaluate(s, h):
    """Every factor and blend against the outcome h sessions ahead, and the pre-declared choice."""
    lab = f"label_{h}"
    train, test = s[s["date"] <= TRAIN_END], s[s["date"] > TRAIN_END]
    cols = list(GROUPS) + ["Value (in sector)", "Quality (in sector)"] + ["f:" + c for c in PRICE_FEATURES + list(F.VALUE + F.QUALITY)]
    single = {c: {"train": measure(train, c, lab, h), "test": measure(test, c, lab, h)} for c in cols}
    # value and quality: whichever form (raw or within the sector) did better in the training years
    use = {}
    for g in ("Value", "Quality"):
        a, b = single[g]["train"].get("ic", -1), single[g + " (in sector)"]["train"].get("ic", -1)
        use[g] = g + " (in sector)" if b > a else g
    seven = ["Q Momentum", "Q Trend", "Q Low Risk", "Q Reversal", "Momentum 12-1", use["Value"], use["Quality"]]
    ic_w = {k: max(single[k]["train"].get("ic", 0) or 0, 0) for k in seven}
    cands = {
        "current V3 (price only)": {name: w for name, _, w in V3.FACTORS},
        "seven groups, equal": {k: 1.0 for k in seven},
        "seven groups, IC-weighted": ic_w,
        "value + quality only": {use["Value"]: 1.0, use["Quality"]: 1.0},
    }
    blends = {}
    for name, w in cands.items():
        if sum(v for v in w.values() if v > 0) <= 0:
            continue
        s["blend"] = blend(s, w)
        tr, te = s[s["date"] <= TRAIN_END], s[s["date"] > TRAIN_END]
        tot = sum(v for v in w.values() if v > 0)
        blends[name] = {"weights": {k: round(v / tot, 3) for k, v in w.items() if v > 0},
                        "train": measure(tr, "blend", lab, h), "test": measure(te, "blend", lab, h)}
    eligible = [k for k in ("current V3 (price only)", "seven groups, equal", "seven groups, IC-weighted") if k in blends]
    strong = [k for k in eligible if (blends[k]["test"].get("t") or 0) >= 2]
    chosen = max(strong or eligible, key=lambda k: blends[k]["test"].get("ic", -9))
    return {"value_form": use["Value"], "quality_form": use["Quality"], "single": single, "blends": blends,
            "chosen": chosen, "chosen_weights": blends[chosen]["weights"], "chosen_is_weak": not strong}


def run():
    t0 = time.time()
    symbols = sorted(SP500)
    print(f"prices for {len(symbols)} stocks...", flush=True)
    prices = load_prices(symbols)
    print(f"  {len(prices) - 1} with prices ({time.time() - t0:.0f}s); facts from the SEC...", flush=True)
    facts, missing = load_facts([s for s in symbols if s in prices])
    print(f"  {len(facts)} with facts, {len(missing)} without ({time.time() - t0:.0f}s); the panel...", flush=True)
    p = panel(prices, facts)
    s = scores(p)
    per = {h: evaluate(s, h) for h in HORIZONS}
    cover = (p.assign(year=p["date"].dt.year).groupby("year")[["ep", "roe"]].apply(lambda g: g.notna().mean()).round(3)
             .reset_index().to_dict("records"))
    res = {"run": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "universe": len(prices) - 1, "with_facts": len(facts),
           "missing_facts": missing, "months": int(s["date"].nunique()), "rows": int(len(s)),
           "train": f"{START} .. {TRAIN_END}", "test": f"after {TRAIN_END} .. {str(s['date'].max().date())}",
           "decision_rule": DECISION, "horizons": per, "coverage_by_year": cover,
           "limits": "Today's S&P 500 members only (survivorship bias), no costs, monthly snapshots, Yahoo adjusted prices."}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(res, indent=1, default=str))
    OUT_MD.write_text(report(res))
    print(report(res))
    print(f"done in {time.time() - t0:.0f}s", flush=True)


def report(r):
    def row(name, m):
        f = lambda k: "—" if m.get(k) is None else m[k]
        return f"| {name} | {f('ic')} | {f('t')} | {f('hit')} | {f('spread_pct')} | {f('ls_sharpe')} | {m.get('months', 0)} |"
    out = [f"# Factor test, S&P 500 ({r['run']})", "",
           f"{r['universe']} stocks with prices, {r['with_facts']} with SEC facts, {r['months']} month-ends, {r['rows']:,} stock-months. "
           f"Training {r['train']}, testing {r['test']}.", "", f"**Decision rule (fixed before the run):** {r['decision_rule']}", ""]
    out += ["| horizon | chosen | weak? | testing IC | testing t | weights |", "|---|---|---|---|---|---|"]
    for h, v in r["horizons"].items():
        te = v["blends"][v["chosen"]]["test"]
        out.append(f"| {h} sessions | {v['chosen']} | {'yes' if v['chosen_is_weak'] else 'no'} | {te.get('ic')} | {te.get('t')} | {v['chosen_weights']} |")
    out.append("")
    for h, v in r["horizons"].items():
        head = (f"| | mean IC | t (overlap-adjusted) | IC > 0 | top-bottom fifth, % / {h} sessions | long-short Sharpe | months |\n"
                "|---|---|---|---|---|---|---|")
        out += [f"# Horizon: {h} sessions", "", f"Value as {v['value_form']}, quality as {v['quality_form']} (picked on the training years).", ""]
        for part in ("train", "test"):
            out += [f"## Blends · {part} · {h} sessions", "", head] + [row(k, x[part]) for k, x in v["blends"].items()] + [""]
        for part in ("train", "test"):
            out += [f"## Factors · {part} · {h} sessions", "", head] + [row(k, x[part]) for k, x in v["single"].items()] + [""]
    out += ["## Coverage of the SEC facts (share of stock-months with a value)", "", "| year | earnings yield | ROE |", "|---|---|---|"]
    out += [f"| {c['year']} | {c['ep']} | {c['roe']} |" for c in r["coverage_by_year"]]
    out += ["", "Rows starting f: are single inputs as raw percentiles (higher value = higher score), so a negative IC there "
            "means lower is better (vol_20: lower volatility).", "", f"**Limits:** {r['limits']}", ""]
    return "\n".join(out)


if __name__ == "__main__":
    run()
