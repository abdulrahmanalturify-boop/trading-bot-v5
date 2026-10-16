# Opportunity Hunter 3.0 — historical evidence

Run on GitHub Actions on 2026-10-16 · 509 symbols (today's S&P 500 and the site's largest companies: survivorship bias, so compare methods with each other, never with zero) · daily bars from 2005 (Yahoo Finance, adjusted).

**These are simulations, not trading results.** Costs per side: commission bps 1.0 bps, half spread bps 5.0 bps, slippage bps 5.0 bps (22 bps a round trip). Fills at the next open; stops filled at the open when the day gaps through them; targets and time stops; no shorts, no leverage, no dividends in the stocks' returns (SPY's benchmark return is price-only too).

## 1. Ranking quality (rank IC of each score against the next month's return over SPY, among the stocks with a live long setup)

| Period | v1 | quant | adaptive | ml |
|---|---:|---:|---:|---:|
| 2008-2009 (dev, flagged) | -0.107 (t -2.17, 22 mo) | -0.106 (t -2.02, 22 mo) | -0.098 (t -1.89, 22 mo) | — |
| 2010-2015 (dev) | +0.003 (t 0.19, 72 mo) | +0.016 (t 0.66, 72 mo) | +0.023 (t 0.99, 72 mo) | — |
| 2016-2019 (validation) | -0.019 (t -0.86, 48 mo) | -0.022 (t -0.73, 48 mo) | -0.022 (t -0.74, 48 mo) | +0.003 (t 0.13, 48 mo) |
| 2020-2021 (test) | +0.041 (t 1.25, 23 mo) | +0.040 (t 1.11, 23 mo) | +0.047 (t 1.23, 23 mo) | -0.013 (t -0.35, 23 mo) |
| 2022 (test) | +0.056 (t 0.88, 11 mo) | +0.096 (t 1.19, 11 mo) | +0.104 (t 1.35, 11 mo) | +0.011 (t 0.25, 11 mo) |
| 2023-2024 (test) | +0.041 (t 1.34, 24 mo) | +0.009 (t 0.26, 24 mo) | +0.008 (t 0.24, 24 mo) | +0.033 (t 1.18, 24 mo) |
| 2025-2026 (final test) | -0.015 (t -0.38, 20 mo) | -0.059 (t -1.2, 20 mo) | -0.052 (t -1.15, 20 mo) | +0.041 (t 0.73, 20 mo) |

IC by market regime (all periods):

| Regime | v1 | quant | adaptive | ml |
|---|---:|---:|---:|---:|
| bull | -0.007 (134 mo) | -0.014 (134 mo) | -0.010 (134 mo) | +0.011 (84 mo) |
| neutral | +0.039 (50 mo) | +0.035 (50 mo) | +0.048 (50 mo) | +0.021 (22 mo) |
| bear | -0.033 (23 mo) | -0.067 (23 mo) | -0.067 (23 mo) | +0.051 (11 mo) |
| stress | -0.027 (19 mo) | +0.019 (19 mo) | +0.019 (19 mo) | -0.046 (9 mo) |

## 2. Adaptive weights (fitted on 2010-2015 only)

| Regime | momentum | trend | volume | risk | setup | months |
|---|---:|---:|---:|---:|---:|---:|
| bull | 0.49 | 0.21 | 0.07 | 0.07 | 0.16 | 42 |
| neutral | 0.42 | 0.25 | 0.07 | 0.07 | 0.17 | 21 |
| bear | 0.30 | 0.20 | 0.15 | 0.15 | 0.20 | 5 |
| stress | 0.30 | 0.20 | 0.15 | 0.15 | 0.20 | 4 |

ML model: trained · walk-forward IC 2016-2024 0.007 against adaptive 0.0131 · NOT USED (did not beat the adaptive score out of sample)

## 3. Trading simulation by period (same portfolio rules for every method)

### 2008-2009 (dev, flagged)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 1.48% | 2.97% | 0.25 | 0.23 | -8.97% | 0.16 | 0.99 | -0.01 | 39% | 135 | 1.95% | 0.05 | 0.19 | 17.1 | 47% | -4.8% … +4.7% |
| quant | 1.64% | 3.30% | 0.27 | 0.24 | -8.16% | 0.20 | 0.87 | -0.06 | 47% | 146 | 2.13% | 0.06 | 0.20 | 18.4 | 55% | -4.5% … +3.6% |
| adaptive | 0.82% | 1.64% | 0.15 | 0.14 | -8.88% | 0.09 | 0.83 | -0.08 | 42% | 156 | 1.30% | 0.05 | 0.17 | 17.3 | 53% | -4.3% … +3.5% |
| random | 4.83% | 9.90% | 0.73 | 0.64 | -8.27% | 0.58 | 1.31 | 0.13 | 54% | 169 | 5.23% | 0.06 | 0.29 | 22.3 | 53% | -3.1% … +10.7% |
| SPY | -10.24% | -19.43% | -0.14 | -0.19 | -51.87% | -0.20 | — | — | — | 0 | 0.00% | 1.00 | — | 0.0 | 100% | -37.2% … +22.9% |

### 2010-2015 (dev)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 2.28% | 14.46% | 0.27 | 0.31 | -17.56% | 0.13 | 0.94 | -0.04 | 43% | 769 | -2.37% | 0.39 | -0.82 | 17.1 | 47% | -3.9% … +9.7% |
| quant | 2.26% | 14.34% | 0.29 | 0.36 | -15.06% | 0.15 | 1.01 | 0.01 | 45% | 706 | -1.77% | 0.34 | -0.81 | 18.4 | 55% | -2.3% … +9.2% |
| adaptive | 4.21% | 27.99% | 0.43 | 0.55 | -15.63% | 0.27 | 0.58 | -0.43 | 46% | 736 | -0.88% | 0.43 | -0.66 | 17.3 | 53% | -0.9% … +11.5% |
| random | 5.68% | 39.24% | 0.58 | 0.75 | -13.78% | 0.41 | 1.19 | 0.09 | 51% | 911 | 0.33% | 0.44 | -0.59 | 22.3 | 53% | +0.2% … +12.9% |
| SPY | 12.57% | 103.21% | 0.83 | 1.07 | -18.61% | 0.68 | — | — | — | 0 | -0.00% | 1.00 | — | 0.0 | 100% | +5.2% … +22.0% |

### 2016-2019 (validation)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 4.16% | 17.64% | 0.53 | 0.60 | -15.07% | 0.28 | 0.89 | -0.08 | 46% | 471 | -0.39% | 0.33 | -0.91 | 17.1 | 47% | -3.0% … +10.7% |
| quant | 6.75% | 29.74% | 0.72 | 0.79 | -12.39% | 0.54 | 1.23 | 0.12 | 48% | 438 | 1.12% | 0.40 | -0.68 | 18.4 | 55% | -0.4% … +14.3% |
| adaptive | 5.70% | 24.73% | 0.62 | 0.69 | -15.51% | 0.37 | 0.74 | -0.23 | 50% | 429 | 0.46% | 0.38 | -0.75 | 17.3 | 53% | -2.9% … +15.4% |
| ml | 11.08% | 52.07% | 1.15 | 1.35 | -12.55% | 0.88 | 1.41 | 0.19 | 53% | 600 | 4.93% | 0.41 | -0.33 | 14.6 | 26% | +2.9% … +20.2% |
| random | 4.67% | 19.98% | 0.51 | 0.67 | -16.94% | 0.28 | 0.95 | -0.04 | 48% | 554 | 0.08% | 0.34 | -0.78 | 22.3 | 53% | -3.0% … +15.0% |
| SPY | 14.75% | 73.12% | 1.13 | 1.35 | -19.35% | 0.76 | — | — | — | 0 | -0.00% | 1.00 | — | 0.0 | 100% | +6.4% … +23.7% |

### 2020-2021 (test)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 2.30% | 4.65% | 0.26 | 0.28 | -13.28% | 0.17 | 0.87 | -0.09 | 39% | 250 | -1.12% | 0.17 | -0.89 | 17.1 | 47% | -3.6% … +11.6% |
| quant | 5.77% | 11.88% | 0.55 | 0.59 | -14.80% | 0.39 | 1.09 | 0.05 | 45% | 248 | 2.00% | 0.18 | -0.75 | 18.4 | 55% | -5.0% … +18.8% |
| adaptive | 3.85% | 7.86% | 0.38 | 0.43 | -15.84% | 0.24 | 1.18 | 0.10 | 41% | 242 | 0.20% | 0.18 | -0.82 | 17.3 | 53% | -5.8% … +16.2% |
| ml | 0.87% | 1.75% | 0.13 | 0.15 | -14.38% | 0.06 | 0.99 | -0.01 | 48% | 427 | -2.65% | 0.17 | -0.96 | 14.6 | 26% | -6.1% … +14.1% |
| random | 14.45% | 30.99% | 1.44 | 1.70 | -7.76% | 1.86 | 1.18 | 0.09 | 53% | 297 | 10.12% | 0.16 | -0.43 | 22.3 | 53% | +4.5% … +24.6% |
| SPY | 22.85% | 50.92% | 0.94 | 1.04 | -33.72% | 0.68 | — | — | — | 0 | -0.00% | 1.00 | — | 0.0 | 100% | +4.2% … +49.0% |

### 2022 (test)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | -11.11% | -11.03% | -1.81 | -1.63 | -11.17% | -0.99 | 0.44 | -0.38 | 30% | 98 | -10.07% | 0.08 | 0.27 | 17.1 | 47% | -16.2% … +4.1% |
| quant | -8.12% | -8.06% | -1.34 | -1.30 | -8.44% | -0.96 | 0.52 | -0.25 | 33% | 82 | -6.88% | 0.08 | 0.41 | 18.4 | 55% | -11.6% … +1.6% |
| adaptive | -9.54% | -9.47% | -2.28 | -2.23 | -9.92% | -0.96 | 0.46 | -0.30 | 33% | 84 | -9.05% | 0.05 | 0.34 | 17.3 | 53% | -13.9% … +1.7% |
| ml | -7.37% | -7.31% | -1.28 | -1.16 | -8.11% | -0.91 | 0.62 | -0.19 | 38% | 112 | -5.81% | 0.09 | 0.46 | 14.6 | 26% | -10.4% … +2.9% |
| random | -12.82% | -12.72% | -2.11 | -2.06 | -12.97% | -0.99 | 0.41 | -0.37 | 32% | 115 | -11.65% | 0.10 | 0.19 | 22.3 | 53% | -16.9% … +0.1% |
| SPY | -18.78% | -18.65% | -0.74 | -1.18 | -24.50% | -0.77 | — | — | — | 0 | 0.00% | 1.00 | — | 0.0 | 100% | -31.0% … +4.7% |

### 2023-2024 (test)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 13.64% | 28.95% | 1.21 | 1.55 | -10.06% | 1.36 | 0.09 | -8.58 | 43% | 272 | -0.21% | 0.57 | -1.05 | 17.1 | 47% | +6.2% … +27.1% |
| quant | 10.42% | 21.78% | 1.10 | 1.43 | -6.57% | 1.59 | 1.09 | 0.06 | 50% | 246 | 1.66% | 0.36 | -1.17 | 18.4 | 55% | +2.2% … +26.0% |
| adaptive | 9.48% | 19.73% | 0.94 | 1.28 | -8.68% | 1.09 | 1.00 | -0.00 | 48% | 237 | -0.47% | 0.42 | -1.26 | 17.3 | 53% | +0.5% … +22.1% |
| ml | 1.19% | 2.38% | 0.18 | 0.23 | -9.33% | 0.13 | 0.97 | -0.02 | 49% | 403 | -9.86% | 0.48 | -2.35 | 14.6 | 26% | -6.3% … +11.6% |
| random | 1.03% | 2.06% | 0.18 | 0.24 | -8.52% | 0.12 | 1.20 | 0.10 | 48% | 323 | -7.55% | 0.37 | -2.36 | 22.3 | 53% | -4.9% … +8.9% |
| SPY | 25.97% | 58.24% | 1.87 | 2.73 | -9.97% | 2.60 | — | — | — | 0 | 0.00% | 1.00 | — | 0.0 | 100% | +11.1% … +40.1% |

### 2025-2026 (final test)

| Method | CAGR | Total | Sharpe | Sortino | Max DD | Calmar | PF | Expect. (R) | Win | Trades | Alpha | Beta | IR | Turnover | Exposure | CAGR 90% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 7.60% | 13.87% | 0.83 | 1.15 | -6.82% | 1.11 | 1.24 | 0.12 | 44% | 206 | 3.92% | 0.21 | -0.65 | 17.1 | 47% | -1.9% … +20.3% |
| quant | 12.13% | 22.51% | 1.22 | 1.81 | -6.90% | 1.76 | 1.35 | 0.16 | 52% | 188 | 8.96% | 0.16 | -0.37 | 18.4 | 55% | +0.6% … +19.9% |
| adaptive | 4.03% | 7.27% | 0.44 | 0.63 | -9.05% | 0.45 | 1.15 | 0.07 | 44% | 204 | 0.28% | 0.23 | -0.85 | 17.3 | 53% | -6.5% … +12.1% |
| ml | 0.83% | 1.47% | 0.14 | 0.18 | -12.49% | 0.07 | 0.85 | -0.09 | 46% | 356 | -3.08% | 0.24 | -1.10 | 14.6 | 26% | -8.1% … +15.0% |
| random | -4.32% | -7.53% | -0.63 | -0.88 | -10.76% | -0.40 | 0.93 | -0.04 | 44% | 291 | -6.76% | 0.14 | -1.42 | 22.3 | 53% | -9.5% … +0.0% |
| SPY | 18.24% | 34.60% | 1.07 | 1.45 | -18.76% | 0.97 | — | — | — | 0 | -0.00% | 1.00 | — | 0.0 | 100% | +3.4% … +36.5% |

## 4. Returns by market regime (annualised, all periods, adaptive method against SPY on the same days)

| Regime | Days | Adaptive | SPY |
|---|---:|---:|---:|
| bull | 2768 | 19.65% | 34.82% |
| neutral | 1065 | -26.53% | -27.28% |
| bear | 419 | -5.67% | -21.03% |
| stress | 474 | -8.11% | 3.05% |

## 5. Ablations (adaptive method, 2016-2026, one rule removed at a time)

| Variant | CAGR | Sharpe | Max DD | Trades | Exposure |
|---|---:|---:|---:|---:|---:|
| no_regime_cap | 1.81% | 0.24 | -23.89% | 1253 | 50% |
| no_corr_filter | 2.82% | 0.34 | -21.65% | 1223 | 48% |
| no_vol_sizing | 7.18% | 0.59 | -17.33% | 1210 | 63% |
| no_dd_brake | 4.92% | 0.51 | -22.32% | 1264 | 58% |
| no_regime_exit | 3.99% | 0.44 | -22.39% | 1386 | 56% |
| adaptive (all rules) | 4.17% | 0.46 | -21.43% | 1196 | 53% |

## 6. What this does and does not show

- Survivorship: today's constituents; delisted and acquired companies are missing, which flatters every method (the control and SPY-relative comparisons still hold).
- 2008-2009 has few survivors with full history and is shown for context only.
- Earnings dates are not in the history: the live page penalises a report within 5 sessions, the simulation cannot.
- Fundamentals are today's snapshot (no point-in-time history), so they take no part in the scores here or on the page's ranking.
- Adjusted prices from Yahoo can be revised; SPY is price-only in both the benchmark and the excess-return labels.
- A score is a rank, never a probability. The ML model's output is used as a rank too.
- The adaptive weights were fitted on 2010-2015; 2016-2019 was the validation window; nothing after 2019 touched any setting.
