# Lab results · market_exit

Run 2026-09-28 19:58 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 1.8 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.6% | 0.82 | -11.0% | 0.23 | 3% | 3.6 | 35% | +10.3% | 0.80 | -20.3% | +14.7% · 1.07 · -17.6% | +13.6% · 1.09 · -18.3% |
| Moving Average Crossover | +4.6% | 0.85 | -9.4% | 0.33 | 6% | 2.4 | 38% | +9.5% | 0.76 | -20.4% | +13.8% · 1.07 · -19.0% | +14.2% · 1.17 · -18.7% |
| Momentum Strategy | +8.1% | 1.13 | -7.9% | 0.40 | 8% | 2.9 | 45% | +13.2% | 0.90 | -21.2% | +13.4% · 0.94 · -20.4% | +15.2% · 1.09 · -15.5% |
| Breakout Strategy | +5.2% | 0.92 | -8.3% | 0.28 | 3% | 2.5 | 43% | +10.9% | 0.81 | -19.9% | +18.1% · 1.16 · -15.7% | +14.8% · 1.09 · -14.7% |
| Volatility Breakout | +3.4% | 0.74 | -8.2% | 0.22 | 3% | 9.4 | 40% | +6.4% | 0.51 | -27.3% | +9.1% · 0.71 · -24.4% | +10.8% · 0.91 · -14.0% |
| Mean Reversion | +2.8% | 0.95 | -3.6% | 0.35 | 7% | 2.5 | 71% | +6.2% | 0.59 | -16.8% | +10.0% · 0.80 · -21.0% | +7.4% · 0.68 · -16.0% |
| VWAP Mean Reversion | +2.1% | 0.89 | -3.3% | 0.31 | 7% | 1.2 | 73% | +6.1% | 0.60 | -17.1% | +16.2% · 1.07 · -18.2% | +11.5% · 0.94 · -17.2% |
| VWAP Reclaim / Pullback | +5.2% | 0.93 | -7.8% | 0.31 | 2% | 4.8 | 33% | +10.8% | 0.80 | -22.4% | +17.1% · 1.20 · -15.2% | +15.1% · 1.19 · -14.9% |
| Relative Strength Strategy | +4.7% | 0.96 | -7.0% | 0.31 | 3% | 2.3 | 47% | +12.3% | 0.87 | -18.9% | +22.7% · 1.30 · -19.0% | +21.6% · 1.38 · -15.7% |
| Pairs Trading | +4.2% | 1.30 | -4.6% | 0.45 | 12% | 1.7 | 72% | +8.6% | 0.66 | -23.7% | +11.3% · 0.89 · -24.9% | +12.4% · 1.02 · -16.0% |
| Statistical Arbitrage | +0.7% | 0.70 | -1.9% | 0.15 | 2% | 1.6 | 60% | +3.0% | 0.38 | -16.7% | +11.2% · 0.91 · -15.2% | +8.4% · 0.85 · -15.2% |
| Multi-Factor Strategy | +4.9% | 0.90 | -10.1% | 0.33 | 3% | 1.4 | 43% | +12.2% | 0.87 | -20.3% | +20.8% · 1.43 · -15.0% | +19.1% · 1.42 · -11.6% |
| Regime-Based Strategy | +2.8% | 0.89 | -5.0% | 0.23 | 4% | 6.1 | 55% | +8.1% | 0.64 | -22.2% | +9.1% · 0.65 · -30.3% | +12.2% · 0.94 · -17.9% |
| Machine Learning Signal Combination | +6.4% | 0.96 | -7.8% | 0.34 | 4% | 7.4 | 36% | +9.8% | 0.70 | -24.8% | +13.4% · 0.97 · -17.5% | +14.5% · 1.12 · -16.8% |
| Portfolio-Level Strategy | +11.7% | 1.12 | -15.2% | 0.49 | 12% | 1.4 | 44% | +16.4% | 0.94 | -26.2% | +27.0% · 1.29 · -23.4% | +25.4% · 1.36 · -18.2% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +6.1% | 0.90 | -7.3% | 0.25 | 15% | 2.9 | 37% | +7.6% | 0.47 | -27.1% | +6.8% · 0.44 · -31.9% | +8.2% · 0.55 · -30.2% |
| Moving Average Crossover | +4.9% | 0.79 | -8.6% | 0.16 | 11% | 2.0 | 34% | +7.8% | 0.49 | -26.2% | +4.5% · 0.35 · -24.9% | +10.1% · 0.74 · -17.1% |
| Momentum Strategy | +7.6% | 0.89 | -10.5% | 0.28 | 16% | 3.1 | 42% | +9.2% | 0.53 | -29.4% | +13.4% · 0.77 · -25.7% | +14.3% · 0.83 · -24.0% |
| Breakout Strategy | +8.0% | 1.00 | -9.2% | 0.34 | 15% | 2.3 | 46% | +11.4% | 0.58 | -27.7% | +39.7% · 1.35 · -22.7% | +32.4% · 1.32 · -22.1% |
| Volatility Breakout | +4.8% | 0.80 | -8.9% | 0.21 | 14% | 8.3 | 38% | +7.0% | 0.38 | -30.0% | +26.3% · 1.16 · -22.7% | +19.2% · 1.05 · -17.1% |
| Mean Reversion | +2.1% | 0.70 | -4.6% | 0.21 | 14% | 1.9 | 66% | +3.1% | 0.28 | -23.4% | +5.5% · 0.42 · -28.3% | +7.5% · 0.59 · -24.2% |
| VWAP Mean Reversion | +1.9% | 0.56 | -5.5% | 0.22 | 14% | 1.6 | 64% | +5.4% | 0.45 | -25.1% | +11.5% · 0.66 · -28.7% | +12.8% · 0.81 · -27.0% |
| VWAP Reclaim / Pullback | +7.6% | 1.05 | -7.2% | 0.27 | 8% | 4.7 | 32% | +9.5% | 0.49 | -30.0% | +16.3% · 0.84 · -24.7% | +13.0% · 0.80 · -23.4% |
| Relative Strength Strategy | +6.3% | 0.96 | -8.3% | 0.28 | 9% | 2.0 | 45% | +8.8% | 0.46 | -30.2% | +32.7% · 1.13 · -28.5% | +30.5% · 1.20 · -26.1% |
| Pairs Trading | +3.0% | 0.80 | -5.8% | 0.24 | 17% | 1.6 | 65% | +6.2% | 0.44 | -27.8% | +9.7% · 0.68 · -24.0% | +7.4% · 0.58 · -25.3% |
| Statistical Arbitrage | +0.6% | 0.54 | -2.0% | 0.13 | 9% | 1.4 | 59% | +1.8% | 0.20 | -19.3% | +8.0% · 0.57 · -34.5% | +4.4% · 0.41 · -20.7% |
| Multi-Factor Strategy | +5.6% | 0.87 | -6.4% | 0.29 | 21% | 1.1 | 48% | +8.0% | 0.45 | -31.9% | +5.5% · 0.40 · -30.6% | +11.0% · 0.72 · -22.1% |
| Regime-Based Strategy | +2.4% | 0.68 | -4.9% | 0.12 | 10% | 5.1 | 53% | +5.9% | 0.42 | -27.1% | +16.9% · 0.80 · -29.2% | +13.3% · 0.77 · -24.0% |
| Machine Learning Signal Combination | +4.9% | 0.68 | -10.4% | 0.23 | 12% | 6.7 | 34% | +9.6% | 0.53 | -28.4% | +22.1% · 1.05 · -22.7% | +17.1% · 0.96 · -21.6% |
| Portfolio-Level Strategy | +10.5% | 0.86 | -18.9% | 0.33 | 16% | 1.5 | 43% | +9.6% | 0.45 | -39.0% | +32.9% · 1.03 · -39.6% | +21.6% · 0.83 · -38.6% |
| **Buy & hold (same stocks)** | +24.1% | 1.03 | -33.6% | | | | | | | | | |

