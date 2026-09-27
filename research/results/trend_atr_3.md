# Lab results · trend_atr_3

Run 2026-09-27 23:41 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 3.2 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.8% | 0.83 | -10.8% | 0.25 | 2% | 3.8 | 34% | +11.4% | 0.84 | -22.4% | +15.5% · 1.07 · -18.0% | +16.4% · 1.21 · -15.9% |
| Moving Average Crossover | +4.9% | 0.87 | -10.4% | 0.35 | 7% | 2.5 | 38% | +10.9% | 0.82 | -22.0% | +18.3% · 1.32 · -17.7% | +16.8% · 1.29 · -16.9% |
| Momentum Strategy | +8.5% | 1.17 | -7.5% | 0.42 | 8% | 3.0 | 44% | +14.0% | 0.91 | -25.0% | +20.8% · 1.23 · -24.8% | +19.3% · 1.25 · -22.0% |
| Breakout Strategy | +5.2% | 0.92 | -8.0% | 0.27 | 3% | 2.5 | 42% | +11.1% | 0.81 | -19.8% | +16.0% · 1.06 · -17.8% | +17.4% · 1.23 · -17.8% |
| Volatility Breakout | +2.9% | 0.70 | -7.9% | 0.23 | 3% | 8.4 | 41% | +8.2% | 0.65 | -20.2% | +6.4% · 0.50 · -26.1% | +9.4% · 0.78 · -15.6% |
| Mean Reversion | +2.5% | 0.96 | -3.1% | 0.33 | 6% | 2.8 | 70% | +7.4% | 0.69 | -16.9% | +9.3% · 0.67 · -26.0% | +8.9% · 0.74 · -17.6% |
| VWAP Mean Reversion | +2.1% | 0.90 | -2.9% | 0.28 | 4% | 1.3 | 73% | +6.9% | 0.68 | -17.2% | +18.1% · 1.08 · -24.6% | +15.1% · 1.11 · -18.5% |
| VWAP Reclaim / Pullback | +4.9% | 0.92 | -7.0% | 0.34 | 2% | 4.3 | 33% | +11.2% | 0.81 | -22.2% | +17.9% · 1.20 · -17.1% | +16.4% · 1.21 · -15.2% |
| Relative Strength Strategy | +4.9% | 1.02 | -6.1% | 0.30 | 7% | 2.3 | 46% | +13.8% | 0.93 | -22.0% | +22.0% · 1.22 · -26.9% | +22.6% · 1.38 · -20.5% |
| Pairs Trading | +1.7% | 1.09 | -1.9% | 0.29 | 3% | 1.2 | 63% | +4.7% | 0.45 | -21.0% | +12.4% · 0.90 · -22.0% | +12.5% · 1.01 · -17.9% |
| Statistical Arbitrage | +0.6% | 0.70 | -1.8% | 0.11 | 4% | 1.8 | 60% | +2.7% | 0.35 | -17.2% | +12.2% · 0.92 · -17.1% | +8.7% · 0.85 · -13.4% |
| Multi-Factor Strategy | +4.6% | 0.92 | -7.7% | 0.37 | 7% | 1.5 | 39% | +13.9% | 0.96 | -19.6% | +20.5% · 1.38 · -18.0% | +19.5% · 1.42 · -15.3% |
| Regime-Based Strategy | +2.4% | 0.74 | -5.2% | 0.16 | 4% | 6.7 | 55% | +7.8% | 0.61 | -25.9% | +11.1% · 0.73 · -33.1% | +10.8% · 0.79 · -26.1% |
| Machine Learning Signal Combination | +5.3% | 0.90 | -7.1% | 0.33 | 4% | 6.4 | 36% | +9.9% | 0.73 | -20.7% | +13.0% · 0.91 · -23.8% | +15.1% · 1.12 · -15.8% |
| Portfolio-Level Strategy | +14.1% | 1.29 | -12.7% | 0.64 | 13% | 1.2 | 42% | +16.6% | 0.93 | -27.4% | +22.8% · 1.02 · -33.8% | +24.3% · 1.21 · -33.2% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +6.5% | 0.92 | -7.6% | 0.28 | 15% | 3.2 | 36% | +9.4% | 0.48 | -30.8% | +11.4% · 0.59 · -32.2% | +9.4% · 0.54 · -29.1% |
| Moving Average Crossover | +6.5% | 0.91 | -10.5% | 0.21 | 13% | 2.2 | 34% | +11.1% | 0.51 | -33.9% | +12.4% · 0.66 · -28.6% | +13.1% · 0.77 · -21.5% |
| Momentum Strategy | +8.8% | 0.98 | -10.9% | 0.28 | 16% | 3.4 | 41% | +14.7% | 0.62 | -33.9% | +20.7% · 0.85 · -36.2% | +21.5% · 0.90 · -29.9% |
| Breakout Strategy | +8.0% | 0.99 | -10.0% | 0.31 | 13% | 2.3 | 43% | +11.9% | 0.54 | -33.7% | +27.0% · 0.97 · -28.6% | +25.8% · 1.06 · -27.3% |
| Volatility Breakout | +4.7% | 0.83 | -10.1% | 0.18 | 11% | 7.5 | 38% | +8.6% | 0.43 | -30.7% | +26.6% · 1.06 · -43.5% | +17.9% · 0.89 · -30.4% |
| Mean Reversion | +2.3% | 0.83 | -5.2% | 0.27 | 18% | 2.2 | 67% | +4.3% | 0.33 | -25.6% | +9.6% · 0.57 · -33.1% | +7.7% · 0.51 · -27.0% |
| VWAP Mean Reversion | +2.2% | 0.64 | -6.1% | 0.18 | 19% | 1.9 | 67% | +6.2% | 0.44 | -26.4% | +8.5% · 0.46 · -44.2% | +10.7% · 0.61 · -32.6% |
| VWAP Reclaim / Pullback | +6.8% | 1.00 | -8.0% | 0.20 | 10% | 4.3 | 31% | +8.0% | 0.44 | -33.1% | +23.6% · 1.00 · -30.7% | +17.8% · 0.93 · -25.3% |
| Relative Strength Strategy | +6.6% | 0.98 | -9.1% | 0.28 | 12% | 2.2 | 44% | +9.3% | 0.44 | -36.4% | +37.3% · 1.13 · -35.7% | +32.8% · 1.13 · -36.4% |
| Pairs Trading | +1.1% | 0.54 | -3.3% | 0.09 | 13% | 1.1 | 56% | +3.7% | 0.37 | -20.9% | +8.4% · 0.54 · -24.9% | +8.0% · 0.58 · -23.3% |
| Statistical Arbitrage | +1.0% | 0.80 | -1.9% | 0.12 | 14% | 1.6 | 60% | +3.1% | 0.30 | -19.4% | +12.3% · 0.72 · -26.9% | +7.8% · 0.61 · -21.2% |
| Multi-Factor Strategy | +5.4% | 0.89 | -6.7% | 0.33 | 16% | 1.3 | 41% | +11.5% | 0.57 | -32.0% | +7.0% · 0.43 · -28.1% | +16.6% · 0.86 · -25.6% |
| Regime-Based Strategy | +3.0% | 0.79 | -6.0% | 0.17 | 13% | 5.8 | 53% | +6.5% | 0.41 | -31.5% | +17.3% · 0.74 · -38.6% | +13.7% · 0.72 · -30.4% |
| Machine Learning Signal Combination | +4.8% | 0.68 | -10.5% | 0.22 | 10% | 6.0 | 33% | +7.3% | 0.39 | -35.5% | +20.1% · 0.88 · -31.8% | +16.9% · 0.84 · -25.8% |
| Portfolio-Level Strategy | +14.6% | 1.07 | -16.8% | 0.41 | 24% | 1.4 | 32% | +20.7% | 0.71 | -39.2% | +66.3% · 1.35 · -45.1% | +52.2% · 1.30 · -41.5% |
| **Buy & hold (same stocks)** | +24.2% | 1.03 | -33.6% | | | | | | | | | |

