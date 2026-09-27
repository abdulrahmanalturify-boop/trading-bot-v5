# Lab results · market_exit

Run 2026-09-27 23:29 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 2.5 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.6% | 0.83 | -10.9% | 0.23 | 2% | 3.6 | 35% | +10.6% | 0.81 | -20.3% | +15.0% · 1.09 · -19.5% | +13.7% · 1.09 · -18.8% |
| Moving Average Crossover | +4.6% | 0.85 | -9.4% | 0.33 | 6% | 2.4 | 38% | +9.5% | 0.76 | -20.4% | +13.8% · 1.07 · -19.0% | +14.1% · 1.16 · -18.7% |
| Momentum Strategy | +8.1% | 1.13 | -7.9% | 0.40 | 8% | 2.9 | 45% | +13.2% | 0.90 | -21.2% | +13.4% · 0.94 · -20.4% | +15.2% · 1.09 · -15.5% |
| Breakout Strategy | +5.2% | 0.92 | -8.3% | 0.28 | 3% | 2.5 | 43% | +10.9% | 0.81 | -20.1% | +17.4% · 1.11 · -15.7% | +14.8% · 1.10 · -14.7% |
| Volatility Breakout | +3.4% | 0.74 | -8.2% | 0.22 | 3% | 9.4 | 40% | +6.4% | 0.51 | -27.2% | +9.1% · 0.71 · -24.4% | +10.8% · 0.91 · -14.0% |
| Mean Reversion | +2.8% | 0.95 | -3.6% | 0.35 | 7% | 2.5 | 71% | +6.2% | 0.59 | -16.8% | +10.1% · 0.80 · -21.0% | +7.7% · 0.70 · -16.0% |
| VWAP Mean Reversion | +2.1% | 0.89 | -3.3% | 0.31 | 7% | 1.2 | 73% | +6.1% | 0.61 | -17.0% | +16.5% · 1.09 · -18.2% | +11.6% · 0.95 · -17.2% |
| VWAP Reclaim / Pullback | +5.2% | 0.93 | -7.8% | 0.31 | 2% | 4.8 | 33% | +10.8% | 0.81 | -22.4% | +17.1% · 1.20 · -15.2% | +15.2% · 1.19 · -14.9% |
| Relative Strength Strategy | +4.7% | 0.96 | -7.0% | 0.31 | 3% | 2.3 | 47% | +12.3% | 0.87 | -18.9% | +22.7% · 1.30 · -19.0% | +21.4% · 1.37 · -16.8% |
| Pairs Trading | +4.2% | 1.30 | -4.6% | 0.45 | 12% | 1.7 | 72% | +8.5% | 0.66 | -23.7% | +11.3% · 0.89 · -24.9% | +12.4% · 1.02 · -16.0% |
| Statistical Arbitrage | +0.7% | 0.70 | -1.9% | 0.15 | 2% | 1.6 | 60% | +3.0% | 0.38 | -16.7% | +11.2% · 0.91 · -15.2% | +8.4% · 0.85 · -15.2% |
| Multi-Factor Strategy | +4.9% | 0.90 | -10.1% | 0.33 | 3% | 1.4 | 43% | +12.2% | 0.87 | -20.3% | +20.8% · 1.43 · -15.0% | +19.1% · 1.42 · -11.6% |
| Regime-Based Strategy | +2.7% | 0.89 | -5.0% | 0.24 | 4% | 6.1 | 55% | +8.1% | 0.64 | -22.2% | +9.5% · 0.68 · -25.7% | +12.6% · 0.96 · -17.8% |
| Machine Learning Signal Combination | +6.4% | 0.95 | -7.8% | 0.34 | 4% | 7.4 | 36% | +9.9% | 0.70 | -24.8% | +13.4% · 0.97 · -17.5% | +14.6% · 1.12 · -16.8% |
| Portfolio-Level Strategy | +11.7% | 1.12 | -15.2% | 0.49 | 12% | 1.4 | 44% | +16.4% | 0.94 | -26.2% | +27.0% · 1.29 · -23.4% | +25.4% · 1.36 · -18.2% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +6.1% | 0.91 | -7.4% | 0.25 | 15% | 2.9 | 37% | +7.7% | 0.48 | -26.9% | +7.0% · 0.45 · -31.7% | +8.7% · 0.57 · -29.9% |
| Moving Average Crossover | +4.9% | 0.80 | -8.6% | 0.16 | 11% | 2.0 | 34% | +7.8% | 0.49 | -26.2% | +4.5% · 0.36 · -24.9% | +10.2% · 0.74 · -17.1% |
| Momentum Strategy | +7.6% | 0.89 | -10.5% | 0.28 | 16% | 3.1 | 42% | +9.3% | 0.54 | -29.3% | +13.2% · 0.76 · -25.7% | +14.2% · 0.83 · -24.0% |
| Breakout Strategy | +8.1% | 1.01 | -9.2% | 0.35 | 15% | 2.3 | 46% | +11.5% | 0.59 | -27.5% | +39.1% · 1.33 · -22.8% | +32.4% · 1.32 · -22.1% |
| Volatility Breakout | +4.8% | 0.80 | -8.9% | 0.21 | 14% | 8.3 | 38% | +7.0% | 0.39 | -29.9% | +26.3% · 1.16 · -22.7% | +19.4% · 1.06 · -17.1% |
| Mean Reversion | +2.1% | 0.72 | -4.6% | 0.21 | 15% | 1.9 | 66% | +3.2% | 0.28 | -23.3% | +5.6% · 0.42 · -28.3% | +7.6% · 0.60 · -24.2% |
| VWAP Mean Reversion | +1.9% | 0.57 | -5.5% | 0.22 | 14% | 1.6 | 64% | +5.5% | 0.46 | -25.1% | +11.7% · 0.67 · -28.7% | +13.0% · 0.82 · -27.0% |
| VWAP Reclaim / Pullback | +7.6% | 1.05 | -7.2% | 0.27 | 8% | 4.7 | 32% | +9.6% | 0.50 | -30.0% | +16.7% · 0.86 · -24.7% | +13.0% · 0.80 · -23.4% |
| Relative Strength Strategy | +6.3% | 0.97 | -8.3% | 0.28 | 10% | 2.0 | 45% | +8.8% | 0.47 | -30.2% | +32.9% · 1.13 · -28.5% | +30.7% · 1.20 · -26.1% |
| Pairs Trading | +3.1% | 0.81 | -5.8% | 0.24 | 17% | 1.6 | 65% | +6.4% | 0.45 | -27.8% | +9.7% · 0.69 · -24.0% | +7.5% · 0.59 · -25.3% |
| Statistical Arbitrage | +0.6% | 0.55 | -2.0% | 0.13 | 9% | 1.4 | 59% | +1.8% | 0.20 | -19.3% | +8.2% · 0.58 · -34.5% | +4.5% · 0.42 · -20.7% |
| Multi-Factor Strategy | +5.6% | 0.88 | -6.4% | 0.28 | 21% | 1.1 | 48% | +8.1% | 0.46 | -31.9% | +5.6% · 0.41 · -30.6% | +11.2% · 0.73 · -22.1% |
| Regime-Based Strategy | +2.4% | 0.68 | -4.9% | 0.12 | 11% | 5.1 | 53% | +5.9% | 0.42 | -27.1% | +16.2% · 0.77 · -32.1% | +12.9% · 0.76 · -23.9% |
| Machine Learning Signal Combination | +4.9% | 0.69 | -10.4% | 0.24 | 12% | 6.7 | 34% | +9.6% | 0.53 | -28.4% | +22.2% · 1.05 · -22.7% | +17.4% · 0.98 · -21.6% |
| Portfolio-Level Strategy | +10.6% | 0.87 | -18.9% | 0.35 | 17% | 1.5 | 43% | +9.8% | 0.46 | -38.9% | +33.8% · 1.06 · -39.6% | +22.3% · 0.85 · -38.0% |
| **Buy & hold (same stocks)** | +24.2% | 1.03 | -33.6% | | | | | | | | | |

