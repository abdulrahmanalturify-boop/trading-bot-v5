# Lab results · atr_stop_3

Run 2026-09-27 23:38 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 3.1 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.8% | 0.83 | -10.8% | 0.25 | 2% | 3.8 | 34% | +11.4% | 0.84 | -22.4% | +15.5% · 1.07 · -18.0% | +16.4% · 1.21 · -15.9% |
| Moving Average Crossover | +5.0% | 0.88 | -10.7% | 0.34 | 7% | 2.5 | 38% | +11.1% | 0.82 | -22.4% | +19.0% · 1.32 · -17.8% | +16.7% · 1.28 · -16.7% |
| Momentum Strategy | +8.7% | 1.19 | -7.5% | 0.42 | 7% | 3.0 | 44% | +14.3% | 0.92 | -24.8% | +21.8% · 1.27 · -24.9% | +20.4% · 1.31 · -20.1% |
| Breakout Strategy | +5.2% | 0.92 | -8.0% | 0.27 | 3% | 2.5 | 42% | +11.1% | 0.81 | -19.8% | +16.0% · 1.06 · -17.8% | +17.4% · 1.23 · -17.8% |
| Volatility Breakout | +4.4% | 0.83 | -9.1% | 0.34 | 6% | 10.3 | 41% | +9.1% | 0.67 | -22.6% | +7.8% · 0.58 · -24.5% | +10.1% · 0.81 · -16.7% |
| Mean Reversion | +2.5% | 0.96 | -3.1% | 0.33 | 6% | 2.8 | 70% | +7.4% | 0.69 | -16.9% | +9.3% · 0.67 · -26.0% | +8.9% · 0.74 · -17.6% |
| VWAP Mean Reversion | +2.1% | 0.90 | -2.9% | 0.28 | 4% | 1.3 | 73% | +6.9% | 0.68 | -17.2% | +18.1% · 1.08 · -24.6% | +15.1% · 1.11 · -18.5% |
| VWAP Reclaim / Pullback | +5.5% | 0.96 | -7.8% | 0.38 | 2% | 5.0 | 33% | +12.2% | 0.86 | -22.4% | +17.0% · 1.15 · -19.7% | +17.3% · 1.27 · -15.8% |
| Relative Strength Strategy | +5.1% | 1.03 | -6.8% | 0.29 | 7% | 2.4 | 46% | +13.6% | 0.91 | -23.1% | +20.5% · 1.15 · -27.5% | +21.6% · 1.31 · -21.9% |
| Pairs Trading | +4.5% | 1.35 | -5.6% | 0.46 | 7% | 2.2 | 64% | +10.5% | 0.72 | -28.3% | +19.0% · 1.22 · -27.8% | +17.7% · 1.20 · -23.6% |
| Statistical Arbitrage | +0.6% | 0.70 | -1.8% | 0.11 | 4% | 1.8 | 60% | +2.7% | 0.35 | -17.2% | +12.2% · 0.92 · -17.1% | +8.7% · 0.85 · -13.4% |
| Multi-Factor Strategy | +5.8% | 1.02 | -8.6% | 0.38 | 6% | 1.5 | 39% | +14.9% | 0.99 | -20.5% | +20.3% · 1.36 · -17.7% | +19.4% · 1.41 · -14.1% |
| Regime-Based Strategy | +2.4% | 0.74 | -5.2% | 0.16 | 4% | 6.7 | 55% | +7.8% | 0.61 | -25.9% | +11.1% · 0.73 · -33.1% | +10.8% · 0.79 · -26.1% |
| Machine Learning Signal Combination | +7.4% | 1.05 | -9.7% | 0.39 | 7% | 8.0 | 36% | +12.6% | 0.83 | -21.5% | +14.6% · 1.00 · -24.9% | +17.1% · 1.24 · -16.7% |
| Portfolio-Level Strategy | +14.1% | 1.29 | -12.7% | 0.64 | 13% | 1.2 | 42% | +16.6% | 0.93 | -27.4% | +22.8% · 1.02 · -33.8% | +24.3% · 1.21 · -33.2% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +6.5% | 0.92 | -7.6% | 0.28 | 15% | 3.2 | 36% | +9.4% | 0.48 | -30.8% | +11.4% · 0.59 · -32.2% | +9.4% · 0.54 · -29.1% |
| Moving Average Crossover | +6.5% | 0.91 | -10.5% | 0.21 | 12% | 2.2 | 34% | +9.1% | 0.46 | -34.7% | +12.6% · 0.66 · -29.6% | +13.1% · 0.77 · -21.5% |
| Momentum Strategy | +9.5% | 1.03 | -11.9% | 0.31 | 16% | 3.5 | 41% | +15.3% | 0.64 | -33.5% | +25.2% · 0.93 · -36.2% | +21.1% · 0.90 · -29.8% |
| Breakout Strategy | +8.0% | 0.99 | -10.0% | 0.31 | 13% | 2.3 | 43% | +11.9% | 0.54 | -33.7% | +27.0% · 0.97 · -28.6% | +25.8% · 1.06 · -27.3% |
| Volatility Breakout | +4.8% | 0.57 | -17.9% | 0.15 | 11% | 10.1 | 39% | +6.2% | 0.33 | -34.5% | +25.0% · 1.01 · -35.0% | +16.9% · 0.84 · -30.3% |
| Mean Reversion | +2.3% | 0.83 | -5.2% | 0.27 | 18% | 2.2 | 67% | +4.3% | 0.33 | -25.6% | +9.6% · 0.57 · -33.1% | +7.7% · 0.51 · -27.0% |
| VWAP Mean Reversion | +2.2% | 0.64 | -6.1% | 0.18 | 19% | 1.9 | 67% | +6.2% | 0.44 | -26.4% | +8.5% · 0.46 · -44.2% | +10.7% · 0.61 · -32.6% |
| VWAP Reclaim / Pullback | +7.1% | 0.91 | -11.8% | 0.23 | 9% | 5.4 | 31% | +7.9% | 0.41 | -37.2% | +18.2% · 0.84 · -31.6% | +12.8% · 0.71 · -27.1% |
| Relative Strength Strategy | +6.4% | 0.93 | -9.6% | 0.26 | 10% | 2.3 | 43% | +9.0% | 0.44 | -36.8% | +40.8% · 1.21 · -35.4% | +34.4% · 1.17 · -38.2% |
| Pairs Trading | +4.2% | 0.79 | -9.2% | 0.30 | 17% | 2.4 | 58% | +10.9% | 0.54 | -43.1% | +10.9% · 0.54 · -46.5% | +13.3% · 0.65 · -43.7% |
| Statistical Arbitrage | +1.0% | 0.80 | -1.9% | 0.12 | 14% | 1.6 | 60% | +3.1% | 0.30 | -19.4% | +12.3% · 0.72 · -26.9% | +7.8% · 0.61 · -21.2% |
| Multi-Factor Strategy | +7.3% | 1.00 | -7.2% | 0.38 | 24% | 1.4 | 41% | +11.5% | 0.55 | -34.4% | +9.6% · 0.54 · -26.9% | +16.1% · 0.84 · -27.0% |
| Regime-Based Strategy | +3.0% | 0.79 | -6.0% | 0.17 | 13% | 5.8 | 53% | +6.5% | 0.41 | -31.5% | +17.3% · 0.74 · -38.6% | +13.7% · 0.72 · -30.4% |
| Machine Learning Signal Combination | +7.6% | 0.81 | -15.9% | 0.27 | 10% | 8.1 | 35% | +9.7% | 0.45 | -37.5% | +18.0% · 0.82 · -36.4% | +18.4% · 0.90 · -31.7% |
| Portfolio-Level Strategy | +14.6% | 1.07 | -16.8% | 0.41 | 24% | 1.4 | 32% | +20.7% | 0.71 | -39.2% | +66.3% · 1.35 · -45.1% | +52.2% · 1.30 · -41.5% |
| **Buy & hold (same stocks)** | +24.2% | 1.03 | -33.6% | | | | | | | | | |

