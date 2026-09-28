# Lab results · trailing_10

Run 2026-09-28 20:15 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 1.8 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +3.5% | 0.70 | -12.3% | 0.26 | 2% | 3.8 | 34% | +10.6% | 0.80 | -22.5% | +14.1% · 1.00 · -16.5% | +14.4% · 1.12 · -14.1% |
| Moving Average Crossover | +3.7% | 0.81 | -9.7% | 0.28 | 5% | 2.5 | 37% | +9.4% | 0.75 | -23.8% | +16.1% · 1.22 · -16.3% | +14.7% · 1.22 · -15.2% |
| Momentum Strategy | +6.1% | 1.01 | -8.4% | 0.41 | 4% | 3.3 | 46% | +12.1% | 0.86 | -21.5% | +14.4% · 1.05 · -15.5% | +15.1% · 1.15 · -15.8% |
| Breakout Strategy | +4.0% | 0.79 | -8.8% | 0.23 | 3% | 2.6 | 43% | +10.2% | 0.78 | -20.0% | +12.7% · 0.91 · -19.8% | +13.4% · 1.06 · -17.0% |
| Volatility Breakout | +4.2% | 0.81 | -10.0% | 0.28 | 4% | 10.3 | 41% | +9.1% | 0.68 | -22.5% | +5.8% · 0.47 · -30.0% | +9.4% · 0.77 · -18.1% |
| Mean Reversion | +2.5% | 0.86 | -3.4% | 0.32 | 9% | 2.7 | 70% | +7.0% | 0.66 | -17.2% | +7.0% · 0.55 · -27.1% | +7.1% · 0.62 · -18.7% |
| VWAP Mean Reversion | +1.6% | 0.77 | -2.5% | 0.23 | 4% | 1.4 | 72% | +6.1% | 0.63 | -15.5% | +15.1% · 0.98 · -26.9% | +11.3% · 0.90 · -15.7% |
| VWAP Reclaim / Pullback | +5.0% | 0.90 | -8.1% | 0.34 | 2% | 5.1 | 33% | +11.3% | 0.81 | -22.0% | +15.6% · 1.10 · -19.9% | +15.2% · 1.16 · -16.1% |
| Relative Strength Strategy | +4.1% | 0.90 | -7.8% | 0.28 | 6% | 2.5 | 47% | +11.7% | 0.84 | -21.6% | +15.4% · 0.99 · -20.7% | +16.6% · 1.14 · -16.5% |
| Pairs Trading | +4.3% | 1.41 | -5.3% | 0.45 | 11% | 2.3 | 64% | +9.5% | 0.69 | -28.5% | +13.9% · 0.97 · -26.2% | +15.5% · 1.11 · -24.3% |
| Statistical Arbitrage | +0.7% | 0.72 | -1.5% | 0.15 | 4% | 1.7 | 60% | +3.1% | 0.40 | -16.3% | +12.7% · 0.97 · -16.5% | +9.0% · 0.87 · -13.9% |
| Multi-Factor Strategy | +3.8% | 0.82 | -7.8% | 0.34 | 4% | 1.6 | 43% | +11.0% | 0.84 | -20.7% | +16.2% · 1.17 · -14.7% | +16.0% · 1.28 · -12.3% |
| Regime-Based Strategy | +2.1% | 0.69 | -4.8% | 0.20 | 4% | 6.7 | 55% | +7.9% | 0.62 | -24.7% | +9.9% · 0.69 · -26.2% | +9.9% · 0.74 · -23.4% |
| Machine Learning Signal Combination | +6.4% | 0.98 | -10.3% | 0.40 | 4% | 8.1 | 37% | +12.4% | 0.84 | -20.7% | +14.6% · 1.04 · -18.3% | +16.2% · 1.22 · -15.6% |
| Portfolio-Level Strategy | +10.3% | 1.20 | -10.6% | 0.52 | 9% | 2.2 | 49% | +12.5% | 0.89 | -21.4% | +14.8% · 1.03 · -18.7% | +12.9% · 1.05 · -17.3% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +3.9% | 0.80 | -4.9% | 0.24 | 10% | 3.3 | 36% | +5.8% | 0.39 | -27.5% | +8.3% · 0.52 · -31.5% | +3.7% · 0.31 · -27.2% |
| Moving Average Crossover | +2.1% | 0.57 | -5.1% | 0.12 | 8% | 2.2 | 33% | +4.4% | 0.33 | -30.4% | +5.6% · 0.40 · -25.4% | +6.8% · 0.51 · -20.1% |
| Momentum Strategy | +4.2% | 0.70 | -7.4% | 0.20 | 13% | 4.3 | 41% | +8.5% | 0.48 | -28.8% | +8.2% · 0.52 · -30.3% | +11.0% · 0.72 · -25.2% |
| Breakout Strategy | +5.2% | 0.92 | -8.2% | 0.24 | 13% | 2.7 | 42% | +6.8% | 0.41 | -31.6% | +21.7% · 1.12 · -24.5% | +14.0% · 0.87 · -23.3% |
| Volatility Breakout | +3.2% | 0.46 | -15.1% | 0.15 | 6% | 10.3 | 38% | +3.2% | 0.22 | -34.1% | +10.5% · 0.57 · -36.1% | +10.2% · 0.61 · -27.8% |
| Mean Reversion | +2.0% | 0.80 | -4.7% | 0.23 | 18% | 2.3 | 64% | +2.3% | 0.21 | -25.5% | +4.9% · 0.37 · -28.0% | +5.7% · 0.44 · -26.0% |
| VWAP Mean Reversion | +1.8% | 0.65 | -4.9% | 0.19 | 19% | 2.0 | 64% | +4.4% | 0.38 | -24.7% | +11.2% · 0.62 · -28.7% | +7.3% · 0.49 · -24.8% |
| VWAP Reclaim / Pullback | +5.6% | 0.87 | -10.9% | 0.21 | 9% | 5.6 | 31% | +7.8% | 0.42 | -34.8% | +7.9% · 0.50 · -31.9% | +10.2% · 0.67 · -27.6% |
| Relative Strength Strategy | +4.2% | 0.86 | -8.6% | 0.20 | 11% | 2.7 | 43% | +7.2% | 0.41 | -30.4% | +14.2% · 0.73 · -36.4% | +17.7% · 0.95 · -30.4% |
| Pairs Trading | +2.7% | 0.75 | -5.9% | 0.22 | 12% | 2.7 | 51% | +8.6% | 0.50 | -35.4% | +8.8% · 0.50 · -41.0% | +11.3% · 0.61 · -41.2% |
| Statistical Arbitrage | +0.9% | 0.75 | -1.7% | 0.15 | 13% | 1.6 | 60% | +2.3% | 0.25 | -19.9% | +10.7% · 0.69 · -29.8% | +5.8% · 0.50 · -20.6% |
| Multi-Factor Strategy | +3.0% | 0.68 | -5.4% | 0.17 | 15% | 1.8 | 41% | +4.1% | 0.30 | -30.8% | +9.2% · 0.61 · -27.3% | +6.3% · 0.50 · -22.7% |
| Regime-Based Strategy | +2.2% | 0.68 | -5.4% | 0.16 | 12% | 5.9 | 53% | +4.4% | 0.35 | -29.5% | +5.3% · 0.35 · -32.4% | +8.7% · 0.56 · -28.9% |
| Machine Learning Signal Combination | +4.7% | 0.66 | -12.7% | 0.19 | 10% | 8.3 | 35% | +6.5% | 0.38 | -35.0% | +7.6% · 0.47 · -31.0% | +5.4% · 0.38 · -25.9% |
| Portfolio-Level Strategy | +7.5% | 0.89 | -13.4% | 0.28 | 16% | 3.4 | 39% | +8.7% | 0.50 | -30.7% | +17.3% · 0.92 · -18.8% | +14.9% · 0.93 · -20.2% |
| **Buy & hold (same stocks)** | +24.1% | 1.03 | -33.6% | | | | | | | | | |

