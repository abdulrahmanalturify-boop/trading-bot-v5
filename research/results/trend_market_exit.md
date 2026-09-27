# Lab results · trend_market_exit

Run 2026-09-27 23:43 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 2.6 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.6% | 0.83 | -10.9% | 0.23 | 2% | 3.6 | 35% | +10.6% | 0.81 | -20.3% | +15.0% · 1.09 · -19.5% | +13.7% · 1.09 · -18.8% |
| Moving Average Crossover | +4.4% | 0.84 | -9.1% | 0.33 | 6% | 2.4 | 38% | +9.3% | 0.75 | -20.3% | +13.6% · 1.08 · -18.4% | +14.1% · 1.17 · -18.0% |
| Momentum Strategy | +8.0% | 1.11 | -7.9% | 0.41 | 8% | 2.9 | 46% | +13.1% | 0.90 | -21.3% | +13.7% · 0.95 · -19.2% | +15.5% · 1.11 · -15.5% |
| Breakout Strategy | +5.2% | 0.92 | -8.3% | 0.28 | 3% | 2.5 | 43% | +10.9% | 0.81 | -20.1% | +17.4% · 1.11 · -15.7% | +14.8% · 1.10 · -14.7% |
| Volatility Breakout | +2.9% | 0.73 | -6.8% | 0.19 | 5% | 8.1 | 41% | +6.3% | 0.54 | -21.5% | +7.3% · 0.59 · -23.7% | +10.2% · 0.88 · -14.3% |
| Mean Reversion | +2.8% | 0.95 | -3.6% | 0.35 | 7% | 2.5 | 71% | +6.2% | 0.59 | -16.8% | +10.1% · 0.80 · -21.0% | +7.7% · 0.70 · -16.0% |
| VWAP Mean Reversion | +2.1% | 0.89 | -3.3% | 0.31 | 7% | 1.2 | 73% | +6.1% | 0.61 | -17.0% | +16.5% · 1.09 · -18.2% | +11.6% · 0.95 · -17.2% |
| VWAP Reclaim / Pullback | +4.7% | 0.91 | -7.1% | 0.31 | 2% | 4.2 | 34% | +10.2% | 0.78 | -21.0% | +18.0% · 1.25 · -13.4% | +14.9% · 1.18 · -12.8% |
| Relative Strength Strategy | +4.8% | 0.99 | -5.7% | 0.33 | 6% | 2.3 | 47% | +12.6% | 0.89 | -18.2% | +23.0% · 1.33 · -18.0% | +21.8% · 1.39 · -16.5% |
| Pairs Trading | +2.5% | 1.16 | -2.8% | 0.36 | 5% | 1.1 | 73% | +7.0% | 0.63 | -19.6% | +13.5% · 1.06 · -18.7% | +11.4% · 1.00 · -14.6% |
| Statistical Arbitrage | +0.7% | 0.70 | -1.9% | 0.15 | 2% | 1.6 | 60% | +3.0% | 0.38 | -16.7% | +11.2% · 0.91 · -15.2% | +8.4% · 0.85 · -15.2% |
| Multi-Factor Strategy | +4.4% | 0.86 | -9.7% | 0.30 | 5% | 1.4 | 43% | +11.7% | 0.83 | -19.7% | +19.3% · 1.31 · -14.9% | +17.5% · 1.32 · -13.7% |
| Regime-Based Strategy | +2.7% | 0.89 | -5.0% | 0.24 | 4% | 6.1 | 55% | +8.1% | 0.64 | -22.2% | +9.5% · 0.68 · -25.7% | +12.6% · 0.96 · -17.8% |
| Machine Learning Signal Combination | +5.5% | 0.93 | -6.7% | 0.34 | 2% | 6.1 | 36% | +9.3% | 0.70 | -21.3% | +14.6% · 1.04 · -17.8% | +13.3% · 1.04 · -16.5% |
| Portfolio-Level Strategy | +11.7% | 1.12 | -15.2% | 0.49 | 12% | 1.4 | 44% | +16.4% | 0.94 | -26.2% | +27.0% · 1.29 · -23.4% | +25.4% · 1.36 · -18.2% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +6.1% | 0.91 | -7.4% | 0.25 | 15% | 2.9 | 37% | +7.7% | 0.48 | -26.9% | +7.0% · 0.45 · -31.7% | +8.7% · 0.57 · -29.9% |
| Moving Average Crossover | +5.0% | 0.80 | -8.6% | 0.17 | 12% | 2.0 | 35% | +8.2% | 0.50 | -26.2% | +5.7% · 0.43 · -24.5% | +10.1% · 0.74 · -17.2% |
| Momentum Strategy | +7.3% | 0.86 | -9.6% | 0.28 | 15% | 3.0 | 42% | +9.0% | 0.52 | -28.9% | +12.6% · 0.74 · -25.7% | +14.1% · 0.82 · -24.0% |
| Breakout Strategy | +8.1% | 1.01 | -9.2% | 0.35 | 15% | 2.3 | 46% | +11.5% | 0.59 | -27.5% | +39.1% · 1.33 · -22.8% | +32.4% · 1.32 · -22.1% |
| Volatility Breakout | +4.8% | 0.92 | -7.1% | 0.23 | 12% | 6.8 | 38% | +9.2% | 0.50 | -27.5% | +28.0% · 1.23 · -21.3% | +18.7% · 1.03 · -18.2% |
| Mean Reversion | +2.1% | 0.72 | -4.6% | 0.21 | 15% | 1.9 | 66% | +3.2% | 0.28 | -23.3% | +5.6% · 0.42 · -28.3% | +7.6% · 0.60 · -24.2% |
| VWAP Mean Reversion | +1.9% | 0.57 | -5.5% | 0.22 | 14% | 1.6 | 64% | +5.5% | 0.46 | -25.1% | +11.7% · 0.67 · -28.7% | +13.0% · 0.82 · -27.0% |
| VWAP Reclaim / Pullback | +6.7% | 1.03 | -6.3% | 0.25 | 9% | 4.0 | 32% | +9.1% | 0.52 | -27.1% | +19.2% · 0.97 · -26.1% | +16.4% · 0.97 · -21.3% |
| Relative Strength Strategy | +6.4% | 0.99 | -7.9% | 0.28 | 10% | 2.0 | 45% | +9.1% | 0.48 | -29.1% | +33.8% · 1.16 · -27.8% | +29.4% · 1.17 · -25.7% |
| Pairs Trading | +1.8% | 0.71 | -3.4% | 0.19 | 20% | 1.0 | 66% | +3.9% | 0.36 | -24.6% | +7.3% · 0.57 · -24.7% | +5.9% · 0.50 · -20.3% |
| Statistical Arbitrage | +0.6% | 0.55 | -2.0% | 0.13 | 9% | 1.4 | 59% | +1.8% | 0.20 | -19.3% | +8.2% · 0.58 · -34.5% | +4.5% · 0.42 · -20.7% |
| Multi-Factor Strategy | +5.4% | 0.89 | -5.9% | 0.28 | 20% | 1.1 | 49% | +8.7% | 0.50 | -27.7% | +6.1% · 0.44 · -28.5% | +11.9% · 0.76 · -19.9% |
| Regime-Based Strategy | +2.4% | 0.68 | -4.9% | 0.12 | 11% | 5.1 | 53% | +5.9% | 0.42 | -27.1% | +16.2% · 0.77 · -32.1% | +12.9% · 0.76 · -23.9% |
| Machine Learning Signal Combination | +4.0% | 0.64 | -8.7% | 0.21 | 11% | 5.3 | 34% | +7.8% | 0.47 | -27.6% | +18.7% · 0.91 · -23.2% | +15.5% · 0.90 · -21.4% |
| Portfolio-Level Strategy | +10.6% | 0.87 | -18.9% | 0.35 | 17% | 1.5 | 43% | +9.8% | 0.46 | -38.9% | +33.8% · 1.06 · -39.6% | +22.3% · 0.85 · -38.0% |
| **Buy & hold (same stocks)** | +24.2% | 1.03 | -33.6% | | | | | | | | | |

