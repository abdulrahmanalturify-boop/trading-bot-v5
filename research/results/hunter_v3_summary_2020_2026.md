# TURA Hunter V3 — Independent Historical Evaluation

**Tested:** 2026-10-16 on GitHub Actions [run 38875845256](https://github.com/abdulrahmanalturify-boop/trading-bot-v5/actions/runs/38875845256).
**Status:** research evidence only; neither V3 profile beats the older V1 in compounded historical return.

## Summary · 81 monthly intervals (Jan 2020–Sep 2026)

| Method | Cumulative modeled return | Maximum month-end drawdown |
|---|---:|---:|
| Old V1 | 104.45% | -21.36% |
| V3 risk-controlled | 49.45% | -15.20% |
| V3 return-seeking | 56.38% | -22.14% |
| SPY | 159.77% | -23.32% |

**Interpretation:** Lower regime exposure helped defensive V3 lower portfolio-level drawdown compared with V1, but substantially reduced upside. The more aggressive profile increased cumulative returns slightly while losing most of the drawdown advantage. Return-seeking *does not guarantee* higher returns: it underperformed defensive V3 in 2022 and 2023.

## Annual results

| Year | Old V1 | V3 risk-controlled | V3 return-seeking | SPY |
|---|---:|---:|---:|---:|
| 2020 | 39.55% | 21.87% | 28.05% | 18.17% |
| 2021 | 41.34% | 13.15% | 25.56% | 28.60% |
| 2022 | -16.72% | -11.34% | -17.53% | -17.99% |
| 2023 | -1.81% | 1.28% | -2.10% | 24.71% |
| 2024 | 30.40% | 22.74% | 28.26% | 26.43% |
| 2025 | 1.95% | 3.48% | 2.32% | 17.71% |
| 2026 (Jan–Sep) | -4.69% | -5.00% | -8.23% | 12.34% |

## Study setup and caveats

- **Not the real Hunter trading P&L.** Monthly ranks used 29 present-day US shares. At prior month-end, use only previously observed daily price data, then enter the top five eligible Hunter setups at next open, exit at next month open, 20 basis points estimated friction per round-trip.
- V3 still uses V1 setup detection, but adds a separately trained 20-session benchmark-excess regression filter; predictions are disabled if purged chronological validation fails.
- V3 risk-controlled deploys 100% / 65% / 25% depending on positive / mixed / negative market regime, compared with V3 return-seeking 100% / 100% / 70% and V1's unchanged fixed slot budget.
- Risk-controlled, return-seeking, and V1 return figures include months with no valid signals, with unused holdings as unremunerated cash. This test does not enforce V3 share-level stop sizing or simulate intraday execution.
- **Survivorship bias:** today's list omits historically delisted names, a major optimistic bias. Data vendor may revise adjusted prices and sector classifications.
- **Data-mining caution:** the V3 code and weights were created with knowledge of past markets; this is a chronological simulation, but **not a preregistered external blind test**. None of the reported numbers is a reliable live-return forecast. Comparing alternative modes post hoc also increases overfit risk.
- **Different V1 result versus an earlier V2 experiment** (104.45% here versus 95.5% earlier): preprocessing and ranking eligibility differ across research scripts. These figures should only be compared *within this exact test*, not conflated with prior ones.
- Maximum drawdowns are measured at month ends, missing deeper intramonth peak-to-trough losses. No leverage, short sales or broker execution were tested.
- Future research needed: survivorship-free point-in-time universe and cross-validation, daily mark-to-market stop/target execution, realistic liquidity/slippage, independent post-development periods, and asset allocation optimization with turnover constraints.

## Engineering quality checks

11 focused regression tests passed on the final branch, including no-lookahead training cutoff, chronological validation and risk exposure limits. Python compilation succeeded for `app.py`, `hunter_v3.py`, `p_hunter_v3.py`. GitHub Actions multi-period research completed successfully.

**Decision:** keep V3 isolated in a draft PR, evaluate further before merging or enabling real-money trades.
