"""Compare TURA Hunter v1 scoring against v2 quant scoring on separate calendar years.

Research-only monthly ranking test: at each previous month-end, compute scores
using historical bars available THEN, buy up to 5 ranked long setups at the next
session's OPEN, hold until the following month's first session OPEN, rebalance.
Same preselected stock universe and ~20 basis points round-trip assumed friction
for each selected stock, per month, for both methods.

This is NOT a test of Hunter's actual stop/target execution. It tests the
INCREMENTAL RANKING value of v2 given the same eligible setup candidates.
Importantly: TODAY'S stock universe creates survivorship bias. Yahoo-adjusted
historical OHLCV may also be revised. Monthly marks hide intramonth drawdowns.
Never interpret this as a trade recommendation or calibrated accuracy.
"""
from __future__ import annotations
import json
import os
import sys
import time
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import hunter as H
import yfinance as yf

# Ex-ante fixed for THIS experiment, but surviving as of now: survivorship bias.
SECTORS = {
    "Technology": ["AAPL", "MSFT", "NVDA", "AMD"],
    "Communication": ["GOOGL", "META", "DIS"],
    "Financials": ["JPM", "BAC", "WFC"],
    "Energy": ["XOM", "CVX", "SLB"],
    "Health Care": ["UNH", "JNJ", "MRK"],
    "Consumer Discretionary": ["AMZN", "HD", "MCD", "NKE"],
    "Consumer Staples": ["WMT", "PG", "KO"],
    "Industrials": ["CAT", "DE", "UPS"],
    "Utilities": ["NEE", "DUK", "SO"],
}
SYMS = [x for group in SECTORS.values() for x in group]
SECTOR_OF = {ticker: sector for sector, tickers in SECTORS.items() for ticker in tickers}
START = "2017-01-01"
ROUND_TRIP_BPS = 20.
TOP = 5
EPOCH = 2020
PERIOD_LAST = 2026
COST = ROUND_TRIP_BPS / 10000.
YEARLY = list(range(EPOCH, PERIOD_LAST + 1))


def _read_batch(symbols):
    for attempt in range(3):
        try:
            raw = yf.download(symbols, start=START,
                              end=(pd.Timestamp.today().normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                              auto_adjust=True, group_by="ticker", threads=True, progress=False,
                              timeout=25)
            if raw is not None and not raw.empty:
                return raw
        except Exception as exc:
            print(f"DOWNLOAD_RETRY attempt={attempt} error={str(exc)[:160]}", flush=True)
        time.sleep(4 * (attempt + 1))
    return pd.DataFrame()


def download_prices():
    stock = {}
    groups = [SYMS[i:i + 7] for i in range(0, len(SYMS), 7)] + [["SPY"]]
    for batch in groups:
        raw = _read_batch(batch)
        if raw.empty:
            print("DOWNLOAD_FAILED", batch, flush=True)
            continue
        for symbol in batch:
            try:
                if isinstance(raw.columns, pd.MultiIndex):
                    if symbol in raw.columns.get_level_values(0):
                        df = raw[symbol].copy()
                    elif symbol in raw.columns.get_level_values(1):
                        df = raw.xs(symbol, axis=1, level=1).copy()
                    else:
                        continue
                else:
                    if len(batch) != 1:
                        continue
                    df = raw.copy()
                need = ["Open", "High", "Low", "Close", "Volume"]
                if not set(need).issubset(df.columns):
                    continue
                df = df[need].apply(pd.to_numeric, errors="coerce").dropna(subset=["Open", "High", "Low", "Close"])
                df = df[(df[["Open", "High", "Low", "Close"]] > 0).all(axis=1)]
                df = df[~df.index.duplicated(keep="last")].sort_index()
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                if len(df) >= 260:
                    stock[symbol] = df
            except Exception as exc:
                print("PARSE_ERROR", symbol, str(exc)[:120], flush=True)
        print("DOWNLOADED", ",".join(batch), ",".join(x for x in batch if x in stock), flush=True)
    return stock


def score_original(row):
    s = (.25 * row["Trend"] + .25 * row["RS"] + .15 * row["Accum"] +
         .20 * row["SetupPts"] + .15 * row["RiskPts"])
    flags = str(row["Flags"]).split(",")
    if "earnings" in flags: s -= 8
    if "thin" in flags: s -= 5
    if row["Side"] <= 0: s = min(s, 49.0)
    return float(np.clip(s, 0, 100))


def month_ends(idx):
    # Include previous December to get January returns; omit incomplete month.
    ix = idx.to_series(index=idx)
    ends = ix.groupby(ix.dt.to_period("M")).max().to_list()
    return [pd.Timestamp(x) for x in ends]


def port_stats(arr):
    x = np.asarray(arr, float)
    e = np.r_[1.0, np.cumprod(1 + x)]
    peaks = np.maximum.accumulate(e)
    return {
        "return_pct": round(float((e[-1] - 1) * 100), 2),
        "annualized_pct": round(float((e[-1]**(12/len(x))-1) * 100), 2) if len(x) else 0,
        "max_month_end_drawdown_pct": round(float(np.min(e / peaks - 1) * 100), 2),
        "positive_months": int((x > 0).sum()),
        "months": int(len(x)),
        "mean_month_pct": round(float(x.mean() * 100), 2),
    }


def run(prices):
    if "SPY" not in prices:
        raise RuntimeError("Missing SPY market reference; cannot compare.")
    spy = prices["SPY"]
    dates = month_ends(spy.index)
    limit = pd.Timestamp.today().normalize()
    # A complete month requires an entry open and exit open at the NEXT
    # month's start. No partial intervals in either method.
    records = []
    skipped = 0
    for j in range(len(dates) - 2):
        prev_end, next_end = dates[j], dates[j + 1]
        entry_day = spy.index[spy.index.get_loc(prev_end) + 1]
        exit_day = spy.index[spy.index.get_loc(next_end) + 1]
        if entry_day.year not in YEARLY or exit_day > limit:
            continue
        if (exit_day - entry_day).days < 15:
            continue
        samples = {}
        for symbol, df in prices.items():
            if symbol == "SPY" or prev_end not in df.index:
                continue
            # No future bars or future-identified exits are accessed by the
            # scorer. Entry/exit prices are read only after ranking.
            past = df.loc[:prev_end].tail(505)
            if len(past) < 260:
                continue
            samples[symbol] = past
        if len(samples) < 12:
            skipped += 1
            print("SKIP_UNIVERSE", str(prev_end.date()), len(samples))
            continue
        market = spy.loc[:prev_end].tail(505)
        res, _ = H.hunt(samples, market, earnings=None, today=prev_end,
                         sectors=SECTOR_OF, thin=20e6)
        if res.empty:
            skipped += 1
            continue
        res = res[(res["Side"] > 0) & res["Entry"].notna() & (res["$Vol"] >= 20e6)].copy()
        if len(res) == 0:
            res = res.copy()
        else:
            res["OldScore"] = res.apply(score_original, axis=1)
        picks = {}
        vals = {}
        for method, col in [("v1", "OldScore"), ("v2", "Score")]:
            chosen = res.sort_values([col,"RS","Symbol"], ascending=[False, False, True]).head(TOP)
            gains = []
            picked = []
            for symbol in chosen["Symbol"]:
                df = prices[symbol]
                if entry_day not in df.index or exit_day not in df.index:
                    continue
                a = float(df.at[entry_day, "Open"])
                b = float(df.at[exit_day, "Open"])
                if a <= 0 or b <= 0: continue
                gains.append(b / a - 1 - COST)
                picked.append(symbol)
            picks[method] = picked
            # If fewer than TOP setups found, deploy equally to found stocks
            # and hold idle slots as cash (no interest).
            vals[method] = float(sum(gains) / TOP)
        ar = float(spy.at[entry_day, "Open"])
        br = float(spy.at[exit_day, "Open"])
        records.append({
            "snapshot": prev_end.date().isoformat(),
            "entry": entry_day.date().isoformat(),
            "exit": exit_day.date().isoformat(),
            "year": int(entry_day.year),
            "candidates": int(len(res)), "scanned": int(len(samples)),
            "v1": vals["v1"], "v2": vals["v2"], "SPY": br/ar - 1,
            "v1_picks": picks["v1"], "v2_picks": picks["v2"],
        })
        print(f"MONTH {entry_day.date()} candidates={len(res)} "
              f"v1={vals['v1']*100:.2f}% v2={vals['v2']*100:.2f}% SPY={(br/ar-1)*100:.2f}%", flush=True)
    if not records:
        raise RuntimeError("No evaluable monthly rebalances; downloaded history is insufficient.")
    out = {"methodology": {
        "data_source": "Yahoo Finance adjusted daily OHLCV via yfinance",
        "universe": "29 present-day large listed US stocks, sectors fixed in the research script (survivorship bias)",
        "selection": "Top five eligible long Hunter setups, rebalanced monthly after previous month close.",
        "fill": "Next trading session open; exit at next rebalance open; equal 20% slots, unused slots in cash",
        "cost_per_trade_round_trip_bps": ROUND_TRIP_BPS,
        "benchmark": "SPY next-open to next-open buy-and-hold (no trading-cost drag)",
        "not_tested": "Actual setup stops/targets, options, intraday liquidity, delisting returns, point-in-time constituents",
        "note": "No AI API or future-price information in the ranking step; this is ranking evidence, not a trading P&L audit."
    }, "tickers_downloaded": list(prices), "skipped_months": skipped, "years": {}, "periods": {},
    "monthly": records}
    for year in YEARLY:
        chunk = [rec for rec in records if rec["year"] == year]
        if not chunk: continue
        out["years"][str(year)] = {
            **{m: port_stats([r[m] for r in chunk]) for m in ("v1", "v2", "SPY")},
            "v2_minus_v1_pct_points": round(port_stats([r["v2"] for r in chunk])["return_pct"] -
                                              port_stats([r["v1"] for r in chunk])["return_pct"], 2),
            "average_eligible": round(float(np.mean([r["candidates"] for r in chunk])), 1),
            "different_top5_pct": round(100 * float(np.mean([set(r["v1_picks"]) != set(r["v2_picks"]) for r in chunk])), 1)
        }
    periods = {"2020-2021_bull_and_pandemic": [2020,2021], "2022_bear": [2022],
               "2023-2024_recovery": [2023,2024], "2025-2026_recent": [2025,2026]}
    for label, years in periods.items():
        chunk = [r for r in records if r["year"] in years]
        if chunk:
            out["periods"][label] = {m: port_stats([r[m] for r in chunk]) for m in ("v1","v2","SPY")}
    Path("research/results").mkdir(parents=True,exist_ok=True)
    dest = Path("research/results/hunter_quant_periods.json")
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2), encoding="utf-8")
    print("BEGIN_HUNTER_RESULTS_JSON")
    print(json.dumps({"tickers_downloaded":out["tickers_downloaded"],"skipped_months":skipped,
                      "years":out["years"],"periods":out["periods"],
                      "tested_months":len(records)},ensure_ascii=False))
    print("END_HUNTER_RESULTS_JSON")
    print("REPORT_FILE",str(dest.resolve()),flush=True)


if __name__ == "__main__":
    run(download_prices())
