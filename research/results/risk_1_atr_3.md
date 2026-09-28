# Lab results · risk_1_atr_3

Run 2026-09-28 20:14 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 2.2 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +0.7% | 0.73 | -2.2% | 0.25 | 2% | 3.7 | 34% | +9.0% | 0.83 | -17.7% | +14.7% · 1.04 · -15.7% | +15.9% · 1.18 · -16.0% |
| Moving Average Crossover | +0.9% | 0.89 | -2.0% | 0.32 | 7% | 2.5 | 38% | +8.7% | 0.82 | -17.8% | +18.8% · 1.34 · -16.7% | +16.6% · 1.28 · -16.7% |
| Momentum Strategy | +1.4% | 1.07 | -1.8% | 0.42 | 5% | 3.0 | 44% | +10.7% | 0.87 | -19.4% | +21.3% · 1.26 · -24.6% | +20.2% · 1.30 · -20.4% |
| Breakout Strategy | +0.9% | 0.87 | -1.8% | 0.30 | 3% | 2.5 | 42% | +8.5% | 0.78 | -15.7% | +16.0% · 1.07 · -17.4% | +16.9% · 1.21 · -18.3% |
| Volatility Breakout | +0.7% | 0.89 | -1.4% | 0.33 | 3% | 10.3 | 41% | +6.7% | 0.66 | -17.5% | +7.8% · 0.61 · -24.5% | +10.1% · 0.81 · -16.8% |
| Mean Reversion | +0.4% | 0.91 | -0.5% | 0.34 | 4% | 2.8 | 70% | +5.5% | 0.68 | -12.1% | +8.4% · 0.66 · -24.5% | +8.8% · 0.73 · -17.1% |
| VWAP Mean Reversion | +0.2% | 0.86 | -0.4% | 0.24 | 6% | 1.3 | 73% | +4.2% | 0.70 | -10.0% | +16.1% · 1.09 · -22.9% | +14.9% · 1.10 · -17.7% |
| VWAP Reclaim / Pullback | +0.9% | 0.89 | -1.6% | 0.31 | 1% | 5.0 | 33% | +9.3% | 0.82 | -17.2% | +15.6% · 1.09 · -19.2% | +17.3% · 1.27 · -15.8% |
| Relative Strength Strategy | +0.8% | 1.03 | -1.1% | 0.32 | 7% | 2.4 | 46% | +10.5% | 0.89 | -18.5% | +21.1% · 1.20 · -27.5% | +21.5% · 1.31 · -21.9% |
| Pairs Trading | +0.6% | 1.36 | -0.7% | 0.41 | 6% | 2.2 | 64% | +7.1% | 0.70 | -20.0% | +18.3% · 1.22 · -27.0% | +17.5% · 1.20 · -23.6% |
| Statistical Arbitrage | +0.1% | 0.61 | -0.3% | 0.09 | 3% | 1.8 | 60% | +1.7% | 0.31 | -13.6% | +12.4% · 0.97 · -15.1% | +8.7% · 0.85 · -13.4% |
| Multi-Factor Strategy | +0.9% | 0.95 | -1.7% | 0.36 | 6% | 1.5 | 39% | +11.2% | 0.97 | -17.0% | +20.3% · 1.38 · -17.7% | +19.4% · 1.41 · -14.1% |
| Regime-Based Strategy | +0.3% | 0.63 | -0.8% | 0.15 | 2% | 6.7 | 55% | +5.9% | 0.58 | -19.8% | +10.3% · 0.71 · -28.7% | +10.8% · 0.79 · -25.8% |
| Machine Learning Signal Combination | +1.1% | 0.98 | -1.6% | 0.36 | 5% | 8.0 | 36% | +9.1% | 0.80 | -17.1% | +14.2% · 1.00 · -23.6% | +17.0% · 1.24 · -16.5% |
| Portfolio-Level Strategy | +2.5% | 1.14 | -3.0% | 0.56 | 6% | 1.2 | 42% | +12.8% | 0.92 | -21.4% | +24.1% · 1.12 · -31.6% | +21.3% · 1.10 · -32.6% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +0.7% | 0.89 | -0.9% | 0.27 | 13% | 3.2 | 36% | +5.5% | 0.46 | -20.8% | +8.4% · 0.51 · -31.6% | +8.5% · 0.50 · -30.5% |
| Moving Average Crossover | +0.6% | 0.79 | -0.9% | 0.17 | 11% | 2.2 | 34% | +4.6% | 0.40 | -23.0% | +9.3% · 0.57 · -26.0% | +13.1% · 0.78 · -21.6% |
| Momentum Strategy | +1.0% | 0.88 | -1.3% | 0.26 | 14% | 3.5 | 41% | +8.4% | 0.54 | -24.9% | +15.5% · 0.73 · -32.7% | +18.3% · 0.83 · -29.9% |
| Breakout Strategy | +0.8% | 0.86 | -1.4% | 0.25 | 11% | 2.3 | 43% | +6.6% | 0.46 | -24.4% | +24.0% · 0.97 · -27.4% | +24.7% · 1.02 · -27.3% |
| Volatility Breakout | +0.5% | 0.63 | -1.8% | 0.21 | 12% | 10.1 | 39% | +2.8% | 0.26 | -20.9% | +17.9% · 0.92 · -29.4% | +16.1% · 0.82 · -30.1% |
| Mean Reversion | +0.2% | 0.73 | -0.5% | 0.25 | 19% | 2.2 | 67% | +1.9% | 0.26 | -16.7% | +7.9% · 0.56 · -24.4% | +7.3% · 0.50 · -26.4% |
| VWAP Mean Reversion | +0.2% | 0.66 | -0.6% | 0.23 | 18% | 1.9 | 67% | +3.1% | 0.46 | -12.1% | +8.0% · 0.55 · -28.0% | +10.5% · 0.62 · -29.6% |
| VWAP Reclaim / Pullback | +0.7% | 0.79 | -1.3% | 0.22 | 8% | 5.4 | 31% | +4.5% | 0.39 | -24.6% | +14.8% · 0.81 · -28.6% | +12.7% · 0.71 · -26.6% |
| Relative Strength Strategy | +0.6% | 0.84 | -1.4% | 0.21 | 9% | 2.3 | 43% | +4.8% | 0.38 | -24.2% | +37.0% · 1.20 · -31.1% | +33.0% · 1.14 · -38.2% |
| Pairs Trading | +0.4% | 0.80 | -0.7% | 0.25 | 13% | 2.4 | 58% | +4.7% | 0.46 | -21.4% | +8.7% · 0.53 · -35.7% | +11.6% · 0.60 · -43.6% |
| Statistical Arbitrage | +0.1% | 0.66 | -0.2% | 0.12 | 13% | 1.6 | 60% | +1.0% | 0.20 | -12.0% | +7.1% · 0.53 · -25.0% | +6.7% · 0.55 · -21.2% |
| Multi-Factor Strategy | +0.8% | 0.93 | -1.0% | 0.32 | 16% | 1.4 | 41% | +5.3% | 0.42 | -23.7% | +4.9% · 0.36 · -27.1% | +15.5% · 0.83 · -27.1% |
| Regime-Based Strategy | +0.3% | 0.68 | -0.7% | 0.17 | 11% | 5.8 | 53% | +3.1% | 0.34 | -20.7% | +14.1% · 0.72 · -33.9% | +13.8% · 0.74 · -30.3% |
| Machine Learning Signal Combination | +0.8% | 0.82 | -1.6% | 0.24 | 13% | 8.1 | 35% | +5.6% | 0.43 | -24.0% | +14.8% · 0.80 · -28.5% | +17.9% · 0.89 · -31.4% |
| Portfolio-Level Strategy | +1.8% | 0.97 | -3.3% | 0.33 | 13% | 1.4 | 32% | +10.5% | 0.58 | -26.8% | +46.5% · 1.19 · -37.7% | +48.6% · 1.25 · -39.0% |
| **Buy & hold (same stocks)** | +24.1% | 1.03 | -33.6% | | | | | | | | | |

