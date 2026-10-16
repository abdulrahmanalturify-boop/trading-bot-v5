# Opportunity Hunter 3.0

Research notes, assumptions, measured results and the review record for the Hunter 3.0 branch
(`claude/project-thread-ncauu4`). Everything below is reproducible from the files named; no number here is a
projection. The numbers are copied from `research/results/hunter3_report.md`, which GitHub Actions rewrites on every
evidence run, so when the two disagree the report is the newer one.

## 1. What changed

| Area | Before (Hunter V3 "Alpha Lab") | After (Hunter 3.0) |
|---|---|---|
| Engine | `hunter_v3.py`: per-stock loop, its own score, its own setups | `hunter3.py`: one wide (date × stock) panel of 43 features, 21 of them scored in five factor groups, four selectable scores, market state, portfolio builder, explainability |
| Page | `p_hunter_v3.py` | `p_hunter3.py` at `/hunter-3`, bilingual (AR/EN), dark and light, mobile layout; the menu entry "Hunter 3.0 / الصياد 3.0" |
| Old Hunter | not comparable | kept as the explicitly selectable **v1** baseline (replicated inside the panel, tested to within 0.2 points of `hunter.hunt`) |
| Evidence | `research/test_hunter_v3_periods.py` | `research/hunter3_backtest.py`: 7 periods 2008–2026, rank IC, costed simulation, walk-forward ML, ablations, automatic verdict |
| Tests | `tests/test_hunter_v3.py` | `tests/test_hunter3.py` (9 tests) |
| CI | `hunter-v3-tests.yml` | `.github/workflows/hunter3.yml`: tests, then the evidence run on real prices committed back to the branch |

Removed: `hunter_v3.py`, `p_hunter_v3.py`, `tests/test_hunter_v3.py`, `research/test_hunter_v3_periods.py`,
`research/results/hunter_v3_summary_2020_2026.md`, `.github/workflows/hunter-v3-tests.yml`. `hunter.py` (the old Hunter
used by the scanner, the bots and the home card) is untouched; `p_scanner.py` helpers are reused, not changed.

The site's version number was deliberately not bumped on this branch: `main` bumps it many times a day and a bump here
would only create merge conflicts. Bump it when merging.

## 2. The engine (`hunter3.py`)

**Panel.** `wide()` turns the per-stock OHLCV frames into five date × stock frames (gaps of up to five sessions are
filled with flat bars so a single missing day does not drop a stock). `panel_features()` computes every factor
column-wise, so the cost is one pandas rolling operation per factor for the whole universe instead of one per stock.
Setups (breakout, pullback, retest, squeeze … from `hunter.SETUPS`) are still detected per stock by `setup_panel()`
because they are path dependent.

**Factors and groups** (each factor is ranked within the universe on each day, 0–100):

| Group | Factors |
|---|---|
| momentum | risk-adjusted 6 and 12 month momentum, 6 month relative strength over SPY, 6 month idiosyncratic residual, 20-day acceleration |
| trend | alignment of price with the 20/50/200 day averages, 63-day efficiency ratio, 63-day stability, distance from the 52-week high |
| volume | 50-day up/down volume ratio, accumulation/distribution slope, dollar-volume trend, 20-day volume imbalance, relative volume |
| risk | 63-day volatility (penalised), 126-day drawdown, 95% CVaR, volatility shock (penalised), beta (penalised) |
| setup | the old Hunter's setup points and reward-to-risk points |

**Scores** (all 0–100 ranks, all capped at 49 when the stock has no live long setup):

- `v1`: the old Hunter's score rebuilt on the panel (`v1_parts()`). This is the baseline and the default.
- `quant`: equal-weighted factor groups.
- `adaptive`: the groups weighted per market regime, weights fitted on 2010–2015 only and stored in
  `hunter3_weights.json` (bear and stress fall back to defaults: too few months to fit).
- `ml`: a histogram gradient-boosted classifier on the factors, exported to `models/hunter3_rank.json` without a
  scikit-learn dependency at run time. **Disabled** by the evidence (see §4).

**Market state** (`Panel.market_state`): regime (bull / neutral / bear / stress, the same labels as `brain.py`),
benchmark trend, realised volatility and its percentile, breadth (% above the 50 and 200 day averages), new highs and
lows, risk-on gauge, average pairwise correlation and dispersion, liquidity, sector leadership and concentration.

**Portfolio** (`build_portfolio`): risk-per-trade sizing from the setup's stop, a volatility cap, a maximum weight,
sector cap, pairwise-correlation skip, regime exposure caps (`EXPOSURE`), and a drawdown brake.

**Explainability** (`Panel.explain`, `why`): each score decomposes into its group contributions with the weights that
produced it; the "Why this opportunity?" case gives the thesis, the evidence, what invalidates it, and what is uncertain,
in Arabic and English.

A score is a **rank**, never a probability. The page and the report say so and never show a score as a percentage of
anything.

## 3. Research design and assumptions (`research/hunter3_backtest.py`)

- Universe: today's S&P 500 plus the site's largest companies, 509 symbols, daily bars from 2005 (Yahoo Finance,
  adjusted). **Survivorship bias**: companies that failed before today are not in it, so every method's absolute
  numbers are flattered and only comparisons between methods are meaningful.
- Periods: 2008–2009 (dev, flagged: the regime weights never saw it), 2010–2015 (dev, used to fit the adaptive
  weights), 2016–2019 (validation), 2020–2021, 2022, 2023–2024 (test), 2025–2026 (final test). Only the test periods
  decide the verdict.
- Ranking quality: Spearman rank IC between each score and the next 21 sessions' return over SPY, among stocks with a
  live long setup, each month; t-statistics over months.
- Simulation: entries decided at the close, filled at the next open; costs 1 bps commission, 5 bps half spread, 5 bps
  slippage per side (22 bps a round trip); stops filled at the open when the day gaps through them, else at the stop;
  targets and time stops from the setup; no shorts, no leverage, no dividends (SPY price-only as well). Policy: 0.75% risk
  per trade, 8 positions, sector cap 2, correlation cap 0.75, 18% target volatility, 20% max weight, regime caps, drawdown
  brake, regime exit. An entry is refused when the open already sits past the target, below the stop, or has consumed over
  half of the planned risk (that last rule was added after the first run showed a handful of one-day trades with
  near-zero planned risk distorting the expectancy in R).
- ML: trained walk-forward with purging and a 21-session embargo, from 2016 on, each year on the years before it.
- Random: a random ranking run through the same simulation, as the floor.
- Ablations: the adaptive policy with each risk rule removed in turn, 2016–2026.
- Verdict rule (`decide()`): a method is "recommended" only if it beats v1 on **both** rank IC and Sharpe in more than
  half of the test periods; ML only if its walk-forward IC beats the adaptive score. Otherwise v1 stays the default.

## 4. Measured results (run of 2026-10-16, 509 symbols, 88 s)

**Verdict: v1 (the old Hunter) stays the default.** `quant` is "not better" (beats v1 on IC in 1 of 4 test periods, on
Sharpe in 2 of 4). `adaptive` is "not better" (IC 2 of 4, Sharpe 0 of 4). `ml` is **rejected**: walk-forward IC
2016–2024 of 0.0045 against 0.0131 for the adaptive score.

Rank IC on the test periods (full table with t-stats in the report):

| Period | v1 | quant | adaptive |
|---|---:|---:|---:|
| 2020–2021 | +0.041 | +0.040 | +0.047 |
| 2022 | +0.056 | +0.096 | +0.104 |
| 2023–2024 | +0.041 | +0.009 | +0.008 |
| 2025–2026 | −0.015 | −0.059 | −0.052 |

No score has a t-statistic above 1.4 in any period. The honest reading is that none of the rankings, old or new, shows a
reliable edge at a one-month horizon on this universe; the differences between them are inside the noise.

Simulation 2025–2026 (final test): v1 CAGR 7.6% / Sharpe 0.83, quant 10.7% / 1.12, adaptive 4.0% / 0.44, ml 2.1% / 0.27,
random −4.3% / −0.63, SPY 18.2% / 1.07. Whole span 2008–2026: v1 2.6% / 0.32, quant 1.9% / 0.26, adaptive 3.8% / 0.42,
random 3.6% / 0.44. Every method trails buy-and-hold SPY over the long span; the random floor is not clearly below the
scored methods, which is the strongest argument against performance claims of any kind.

Ablations (adaptive, 2016–2026): removing volatility sizing raised CAGR from 4.2% to 7.2% and Sharpe from 0.46 to 0.60;
removing the drawdown brake or the regime exit also helped slightly; removing the regime cap or the correlation filter
hurt. The sizing rules are therefore kept selectable rather than hard-wired, and nothing is claimed for them.

Failures recorded, not hidden: the ML ranker, the adaptive weights (fitted on bull and neutral months only), the
2025–2026 IC of all scores, and the first run's expectancy-in-R distortion (fixed in the simulation, see §3).

## 5. Benchmarks

| What | Measured |
|---|---|
| Page scan, 175 stocks × 500 bars (the default US universe) | 23.4 s, 218 MB peak (vectorised); 48 s before vectorisation |
| Evidence run on GitHub Actions, 509 symbols from 2005 | 88–119 s wall |
| Evidence run peak memory | 3.6 GB with the per-stock engine; 12 GB with the first wide engine; the rolling CVaR is now computed in blocks of 16 columns to cut that (re-measured by the next workflow run, `research/results/hunter3_run.txt`) |
| Unit tests | 9 tests, about 25 s |

## 6. How to re-run

```
PYTHONPATH=. python -m unittest tests.test_hunter3 -v
python research/hunter3_backtest.py          # needs Yahoo Finance; writes research/results/hunter3_*
```

GitHub Actions: "hunter 3.0" runs on every push of the backtest to the branch, or by hand (workflow_dispatch), and commits
the results, weights and model back to the branch. Nothing on `main` is touched.

## 7. Limitations and what would change the verdict

- Survivorship bias and a single data vendor; no intraday data, so gap fills are approximations.
- The verdict uses four test periods with 11–24 months each: small samples, wide confidence intervals.
- No live-trading connection exists and none is proposed by this branch.
- A new method earns the default only by beating v1 on IC and Sharpe in most test periods in a fresh run of the same
  workflow, and the page then switches its default automatically (`p_hunter3.default_method`).
