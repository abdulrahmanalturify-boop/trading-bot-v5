# Opportunity Hunter 3.0 — historical evidence

Run on GitHub Actions on 2026-10-16 · 509 symbols (today's S&P 500 and the site's largest companies: survivorship bias, so compare methods with each other, never with zero) · daily bars from 2005 (Yahoo Finance, adjusted).

**These are simulations, not trading results.** Costs per side: commission bps 1.0 bps, half spread bps 5.0 bps, slippage bps 5.0 bps (22 bps a round trip). Fills at the next open; stops filled at the open when the day gaps through them; targets and time stops; no shorts, no leverage, no dividends in the stocks' returns (SPY's benchmark return is price-only too).

## 1. Ranking quality (rank IC of each score against the next month's return over SPY, among the stocks with a live long setup)

| Period | v1 | quant | adaptive | ml |
|---|---:|---:|---:|---:|
| 2008-2009 (dev, flagged) | -0.107 (t -2.17, 22 mo) | -0.106 (t -2.02, 22 mo) | -0.098 (t -1.89, 22 mo) | — |
| 2010-2015 (dev) | +0.003 (t 0.19, 72 mo) | +0.016 (t 0.66, 72 mo) | +0.023 (t 0.99, 72 mo) | — |
| 2016-2019 (validation) | -0.019 (t -0.86, 48 mo) | -0.023 (t -0.73, 48 mo) | -0.022 (t -0.74, 48 mo) | -0.001 (t -0.05, 48 mo) |
| 2020-2021 (test) | +0.041 (t 1.25, 23 mo) | +0.040 (t 1.11, 23 mo) | +0.047 (t 1.23, 23 mo) | -0.008 (t -0.21, 23 mo) |
| 2022 (test) | +0.056 (t 0.88, 11 mo) | +0.096 (t 1.19, 11 mo) | +0.104 (t 1.35, 11 mo) | +0.003 (t 0.06, 11 mo) |
| 2023-2024 (test) | +0.041 (t 1.34, 24 mo) | +0.009 (t 0.26, 24 mo) | +0.008 (t 0.24, 24 mo) | +0.028 (t 1.06, 24 mo) |
| 2025-2026 (final test) | -0.015 (t -0.38, 20 mo) | -0.059 (t -1.2, 20 mo) | -0.052 (t -1.15, 20 mo) | +0.011 (t 0.19, 20 mo) |

IC by market regime (all periods):

| Regime | v1 | quant | adaptive | ml |
|---|---:|---:|---:|---:|
| bull | -0.007 (134 mo) | -0.014 (134 mo) | -0.010 (134 mo) | +0.005 (84 mo) |
| neutral | +0.039 (50 mo) | +0.035 (50 mo) | +0.048 (50 mo) | +0.015 (22 mo) |
| bear | -0.033 (23 mo) | -0.067 (23 mo) | -0.067 (23 mo) | +0.066 (11 mo) |
| stress | -0.027 (19 mo) | +0.019 (19 mo) | +0.019 (19 mo) | -0.086 (9 mo) |

## 2. Adaptive weights (fitted on 2010-2015 only)

| Regime | momentum | trend | volume | risk | setup | months |
|---|---:|---:|---:|---:|---:|---:|
| bull | 0.49 | 0.21 | 0.07 | 0.07 | 0.16 | 42 |
| neutral | 0.42 | 0.25 | 0.07 | 0.07 | 0.17 | 21 |
| bear | 0.30 | 0.20 | 0.15 | 0.15 | 0.20 | 5 |
| stress | 0.30 | 0.20 | 0.15 | 0.15 | 0.20 | 4 |

ML model: trained · walk-forward IC 2016-2024 0.0045 against adaptive 0.0131 · NOT USED (did not beat the adaptive score out of sample)

## Verdict

Rule: a new score replaces the old Hunter's only when it beats v1 on rank IC and Sharpe in most out-of-sample periods (2020 on).

- **quant**: not better (beats v1 on IC in 1 of 4 periods, on Sharpe in 3)
- **adaptive**: not better (beats v1 on IC in 2 of 4 periods, on Sharpe in 2)
- **ml**: rejected (walk-forward IC did not beat the adaptive score)

**The page ranks by `v1` by default**; every score stays selectable, with these numbers beside it.

## 3. Trading simulation by period (same portfolio rules for every method)

### 2008-2009 (dev, flagged)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 1.44% | 2.90% | 0.25 | 0.22 | -8.97% | 0.16 | 0.97 | -0.01 | 39% | 134 | 1.91% | 0.05 | 0.19 | 16.0 | 45% | -4.9% … +4.6% |
| quant | 1.77% | 3.58% | 0.29 | 0.26 | -8.12% | 0.22 | 0.95 | -0.02 | 48% | 145 | 2.26% | 0.06 | 0.20 | 19.0 | 57% | -4.4% … +4.0% |
| adaptive | 0.95% | 1.91% | 0.17 | 0.16 | -8.84% | 0.11 | 0.84 | -0.08 | 43% | 156 | 1.43% | 0.05 | 0.18 | 17.7 | 53% | -4.2% … +3.7% |
| random | 5.15% | 10.56% | 0.79 | 0.70 | -8.83% | 0.58 | 1.46 | 0.17 | 55% | 161 | 5.51% | 0.06 | 0.30 | 23.5 | 56% | -3.5% … +10.7% |
| SPY | -10.24% | -19.43% | -0.14 | -0.19 | -51.87% | -0.20 | — | — | — | 0 | 0.00% | 1.00 | — | 0.0 | 100% | -37.2% … +22.9% |

### 2010-2015 (dev)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 2.58% | 16.49% | 0.30 | 0.35 | -18.40% | 0.14 | 1.02 | 0.01 | 44% | 764 | -2.16% | 0.40 | -0.79 | 16.0 | 45% | -4.0% … +10.5% |
| quant | 3.35% | 21.81% | 0.38 | 0.48 | -15.41% | 0.22 | 1.20 | 0.10 | 46% | 710 | -1.10% | 0.37 | -0.74 | 19.0 | 57% | -1.3% … +9.5% |
| adaptive | 3.13% | 20.30% | 0.33 | 0.44 | -15.59% | 0.20 | 1.14 | 0.07 | 46% | 746 | -1.91% | 0.43 | -0.74 | 17.7 | 53% | -2.1% … +10.4% |
| random | 4.64% | 31.22% | 0.48 | 0.61 | -13.51% | 0.34 | 1.20 | 0.09 | 52% | 924 | -0.73% | 0.45 | -0.68 | 23.5 | 56% | -1.2% … +11.6% |
| SPY | 12.57% | 103.21% | 0.83 | 1.07 | -18.61% | 0.68 | — | — | — | 0 | -0.00% | 1.00 | — | 0.0 | 100% | +5.2% … +22.0% |

### 2016-2019 (validation)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 2.26% | 9.33% | 0.31 | 0.35 | -16.03% | 0.14 | 1.03 | 0.02 | 44% | 472 | -1.93% | 0.31 | -1.04 | 16.0 | 45% | -4.6% … +10.4% |
| quant | 5.88% | 25.61% | 0.63 | 0.69 | -12.90% | 0.46 | 1.19 | 0.10 | 49% | 445 | 0.44% | 0.40 | -0.73 | 19.0 | 57% | -2.1% … +14.2% |
| adaptive | 6.52% | 28.63% | 0.68 | 0.74 | -15.34% | 0.42 | 1.33 | 0.16 | 49% | 440 | 1.02% | 0.40 | -0.67 | 17.7 | 53% | -2.1% … +17.1% |
| ml | 11.64% | 55.13% | 1.18 | 1.30 | -11.82% | 0.98 | 1.40 | 0.18 | 55% | 600 | 5.54% | 0.41 | -0.28 | 14.7 | 25% | +3.9% … +20.5% |
| random | 4.76% | 20.39% | 0.52 | 0.69 | -13.94% | 0.34 | 1.20 | 0.09 | 51% | 521 | 0.31% | 0.33 | -0.76 | 23.5 | 56% | -1.9% … +13.6% |
| SPY | 14.75% | 73.12% | 1.13 | 1.35 | -19.35% | 0.76 | — | — | — | 0 | -0.00% | 1.00 | — | 0.0 | 100% | +6.4% … +23.7% |

### 2020-2021 (test)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 5.09% | 10.45% | 0.53 | 0.65 | -8.58% | 0.59 | 1.02 | 0.01 | 42% | 230 | 1.87% | 0.15 | -0.78 | 16.0 | 45% | -1.5% … +11.7% |
| quant | 7.26% | 15.04% | 0.67 | 0.72 | -15.85% | 0.46 | 1.05 | 0.03 | 46% | 252 | 3.38% | 0.18 | -0.69 | 19.0 | 57% | -4.3% … +19.4% |
| adaptive | 7.91% | 16.44% | 0.71 | 0.82 | -15.48% | 0.51 | 1.11 | 0.06 | 44% | 242 | 4.07% | 0.18 | -0.66 | 17.7 | 53% | -3.2% … +19.3% |
| ml | -0.26% | -0.52% | 0.03 | 0.03 | -16.96% | -0.02 | 0.95 | -0.03 | 46% | 423 | -3.71% | 0.17 | -1.02 | 14.7 | 25% | -9.4% … +12.6% |
| random | 10.04% | 21.10% | 1.00 | 1.27 | -11.09% | 0.91 | 1.18 | 0.09 | 50% | 292 | 5.96% | 0.17 | -0.60 | 23.5 | 56% | +0.7% … +20.5% |
| SPY | 22.85% | 50.92% | 0.94 | 1.04 | -33.72% | 0.68 | — | — | — | 0 | -0.00% | 1.00 | — | 0.0 | 100% | +4.2% … +49.0% |

### 2022 (test)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | -11.32% | -11.23% | -2.24 | -2.07 | -11.36% | -1.00 | 0.43 | -0.33 | 34% | 96 | -10.74% | 0.06 | 0.26 | 16.0 | 45% | -17.4% … +1.5% |
| quant | -11.70% | -11.61% | -1.92 | -1.91 | -11.97% | -0.98 | 0.36 | -0.33 | 34% | 85 | -10.81% | 0.08 | 0.24 | 19.0 | 57% | -18.2% … +3.0% |
| adaptive | -7.00% | -6.94% | -1.51 | -1.32 | -7.41% | -0.94 | 0.53 | -0.22 | 35% | 71 | -6.08% | 0.06 | 0.46 | 17.7 | 53% | -11.1% … +1.9% |
| ml | -8.72% | -8.65% | -1.63 | -1.50 | -9.01% | -0.97 | 0.73 | -0.14 | 35% | 119 | -7.41% | 0.09 | 0.39 | 14.7 | 25% | -11.5% … +3.7% |
| random | -14.70% | -14.59% | -2.60 | -2.32 | -14.85% | -0.99 | 0.43 | -0.34 | 31% | 111 | -14.05% | 0.09 | 0.09 | 23.5 | 56% | -18.8% … -0.0% |
| SPY | -18.78% | -18.65% | -0.74 | -1.18 | -24.50% | -0.77 | — | — | — | 0 | 0.00% | 1.00 | — | 0.0 | 100% | -31.0% … +4.7% |

### 2023-2024 (test)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 14.48% | 30.86% | 1.33 | 1.78 | -8.41% | 1.72 | 1.46 | 0.23 | 50% | 245 | 0.72% | 0.56 | -1.02 | 16.0 | 45% | +6.1% … +29.2% |
| quant | 4.25% | 8.63% | 0.51 | 0.63 | -6.53% | 0.65 | 1.18 | 0.09 | 46% | 250 | -3.88% | 0.35 | -1.70 | 19.0 | 57% | -3.1% … +17.3% |
| adaptive | 6.58% | 13.50% | 0.68 | 0.87 | -9.47% | 0.69 | 1.25 | 0.12 | 49% | 245 | -3.02% | 0.41 | -1.49 | 17.7 | 53% | -1.4% … +17.7% |
| ml | 4.99% | 10.15% | 0.52 | 0.68 | -13.68% | 0.36 | 1.09 | 0.05 | 49% | 419 | -7.85% | 0.55 | -1.97 | 14.7 | 25% | -4.9% … +18.2% |
| random | 6.62% | 13.60% | 0.88 | 1.11 | -5.66% | 1.17 | 1.34 | 0.16 | 51% | 343 | -2.28% | 0.38 | -1.73 | 23.5 | 56% | +0.6% … +17.0% |
| SPY | 25.97% | 58.24% | 1.87 | 2.73 | -9.97% | 2.60 | — | — | — | 0 | 0.00% | 1.00 | — | 0.0 | 100% | +11.1% … +40.1% |

### 2025-2026 (final test)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 7.42% | 13.54% | 0.82 | 1.17 | -6.89% | 1.08 | 1.27 | 0.13 | 45% | 199 | 3.78% | 0.21 | -0.67 | 16.0 | 45% | -1.4% … +20.4% |
| quant | 10.23% | 18.86% | 1.06 | 1.62 | -7.29% | 1.40 | 1.34 | 0.15 | 51% | 187 | 7.11% | 0.17 | -0.48 | 19.0 | 57% | -1.0% … +19.3% |
| adaptive | 3.65% | 6.57% | 0.39 | 0.55 | -9.32% | 0.39 | 1.14 | 0.07 | 44% | 208 | -0.25% | 0.24 | -0.87 | 17.7 | 53% | -7.3% … +11.9% |
| ml | 0.26% | 0.47% | 0.07 | 0.10 | -12.52% | 0.02 | 1.04 | 0.02 | 47% | 370 | -3.39% | 0.22 | -1.12 | 14.7 | 25% | -11.4% … +16.3% |
| random | -2.50% | -4.39% | -0.25 | -0.34 | -11.53% | -0.22 | 1.28 | 0.14 | 44% | 287 | -4.98% | 0.15 | -1.24 | 23.5 | 56% | -11.0% … +5.2% |
| SPY | 18.24% | 34.60% | 1.07 | 1.45 | -18.76% | 0.97 | — | — | — | 0 | -0.00% | 1.00 | — | 0.0 | 100% | +3.4% … +36.5% |

## 4. Returns by market regime (annualised, all periods, adaptive method against SPY on the same days)

| Regime | Days | Adaptive | SPY |
|---|---:|---:|---:|
| bull | 2768 | 19.46% | 34.82% |
| neutral | 1065 | -25.90% | -27.28% |
| bear | 419 | -6.05% | -21.03% |
| stress | 474 | -7.16% | 3.05% |

## 5. Ablations (adaptive method, 2016-2026, one rule removed at a time)

| Variant | CAGR | Sharpe | Max DD | Trades | Exposure |
|---|---:|---:|---:|---:|---:|
| no_regime_cap | 3.46% | 0.39 | -20.26% | 1206 | 52% |
| no_corr_filter | 2.71% | 0.33 | -19.27% | 1197 | 49% |
| no_vol_sizing | 6.22% | 0.55 | -23.46% | 1210 | 59% |
| no_dd_brake | 3.75% | 0.40 | -21.52% | 1246 | 58% |
| no_regime_exit | 3.00% | 0.35 | -18.66% | 1366 | 53% |
| adaptive (all rules) | 4.90% | 0.52 | -17.74% | 1206 | 53% |

## 6. What this does and does not show

- Survivorship: today's constituents; delisted and acquired companies are missing, which flatters every method (the control and SPY-relative comparisons still hold).
- 2008-2009 has few survivors with full history and is shown for context only.
- Earnings dates are not in the history: the live page penalises a report within 5 sessions, the simulation cannot.
- Fundamentals are today's snapshot (no point-in-time history), so they take no part in the scores here or on the page's ranking.
- Adjusted prices from Yahoo can be revised; SPY is price-only in both the benchmark and the excess-return labels.
- A score is a rank, never a probability. The ML model's output is used as a rank too.
- The adaptive weights were fitted on 2010-2015; 2016-2019 was the validation window; nothing after 2019 touched any setting.
