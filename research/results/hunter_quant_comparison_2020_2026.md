# TURA Opportunity Hunter — Historical Ranking Comparison

**Research date:** 2026-10-15 · **Status:** preliminary, not production validation.

**Finding:** The old five-factor Hunter was stronger than the candidate seven-factor quant Hunter in this particular 81-month, 29-stock, 9-sector ranking test. The candidate quant weights do **not** merit replacement of the old scorer yet.

## Independent calendar-year results

| Year | V1 (old) | V2 (quant) | SPY | V2 − V1 (percentage points) | Months |
|---|---:|---:|---:|---:|---:|
| 2020 | 39.55% | 37.21% | 18.17% | -2.34 | 12 |
| 2021 | 35.16% | 41.08% | 28.60% | 5.92 | 12 |
| 2022 | -16.72% | -21.30% | -17.99% | -4.58 | 12 |
| 2023 | -1.81% | -2.39% | 24.71% | -0.58 | 12 |
| 2024 | 30.40% | 26.51% | 26.43% | -3.89 | 12 |
| 2025 | 1.95% | 2.39% | 17.71% | 0.44 | 12 |
| 2026 YTD | -4.69% | -5.56% | 12.34% | -0.87 | 9 |

## Full sample January 2020–September 2026 (81 complete rebalances)

- Old V1 cumulative, approximately: **95.5%**.
- Candidate quant V2 cumulative, approximately: **81.9%**.
- SPY benchmark cumulative, approximately: **159.8%**.
- Maximum **month-end** drawdown, respectively: -21.4%, -26.1%, -23.3%.
- Monthly outcome changes when ranked: V2 better in **11**, V1 better in **13**, approximately tied to two decimals in **57** months.
- Scores are deterministic hand-set factor weights, not predictive probabilities. The fact that monthly selections differ infrequently suggests the added factors add limited independent rank information in this universe.

## Separate regimes

| Period | Old | Quant | SPY | Months |
|---|---:|---:|---:|---:|
| 2020-2021_bull_and_pandemic | 88.62% | 93.59% | 51.96% | 24 |
| 2022_bear | -16.72% | -21.30% | -17.99% | 12 |
| 2023-2024_recovery | 28.05% | 23.48% | 57.67% | 24 |
| 2025-2026_recent | -2.83% | -3.31% | 32.23% | 21 |

## Reproduction and major limitations

- Runner: `research/test_hunter_periods.py`, executed by GitHub Actions run **38782609605**.
- Raw run artifact: `hunter-quant-periods` containing detailed full-precision monthly records.
- Same 29 present-day large US stocks, same original 12 opportunity setups, same 5 positions, same benchmark, and **20 basis points estimated round-trip trading costs** applied to each filled stock position for both methods.
- Scores computed at **month-end close** from the price history available up to that date; entries at **next session's open**, exits at the **next month's first session's open**.
- Idle position slots earn no return. This checks **monthly ranking efficiency**, not stop losses or actual setup exit strategies.
- SPY benchmark excludes a trading fee drag; its monthly marks are not an intraday drawdown.
- **Survivorship bias:** stocks were selected using today's survivors, including earlier crisis periods. Adjusted historical data from Yahoo may be revised. Sector labels may also reflect current classifications. Absence of delisted companies is especially serious.
- **Selection/model risk:** V2 factor weights are hand-chosen, uncalibrated, and tested retrospectively. Periods are nonoverlapping but not formally blind, pre-registered out-of-sample tests.
- Uncertainty: only 81 monthly observations, with 57 near-ties. Apparent differences should not be treated as stable future performance.
- A production trading decision requires point-in-time historical constituents, realistic spread/slippage by asset, actual next-day fills and setup stop/target mechanics, proper daily mark-to-market, and walk-forward tests on entirely unseen dates.

**Decision:** Keep V2 on the draft feature branch. Do not merge as the default scoring engine on the evidence from this test.
