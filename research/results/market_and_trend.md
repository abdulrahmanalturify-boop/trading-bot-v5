# Lab results · market_and_trend

Run 2026-09-27 23:34 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 2.7 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.9% | 0.84 | -10.1% | 0.22 | 2% | 3.5 | 35% | +10.6% | 0.79 | -21.5% | +15.1% · 1.08 · -21.5% | +17.5% · 1.31 · -16.7% |
| Moving Average Crossover | +5.0% | 0.90 | -9.3% | 0.34 | 7% | 2.4 | 39% | +9.4% | 0.74 | -22.4% | +16.2% · 1.21 · -19.6% | +15.9% · 1.27 · -13.6% |
| Momentum Strategy | +8.1% | 1.11 | -9.2% | 0.43 | 8% | 2.7 | 46% | +12.8% | 0.86 | -24.3% | +17.8% · 1.13 · -20.9% | +17.0% · 1.17 · -18.2% |
| Breakout Strategy | +5.3% | 0.92 | -7.9% | 0.25 | 3% | 2.4 | 43% | +10.8% | 0.79 | -21.6% | +18.2% · 1.11 · -20.4% | +16.2% · 1.15 · -18.2% |
| Volatility Breakout | +2.9% | 0.71 | -7.5% | 0.18 | 3% | 8.1 | 40% | +6.2% | 0.52 | -22.7% | +6.5% · 0.52 · -23.7% | +9.4% · 0.81 · -14.3% |
| Mean Reversion | +3.4% | 1.07 | -3.6% | 0.40 | 11% | 2.5 | 74% | +8.4% | 0.74 | -15.8% | +12.7% · 0.94 · -19.7% | +10.7% · 0.90 · -15.9% |
| VWAP Mean Reversion | +2.5% | 0.98 | -3.4% | 0.32 | 7% | 1.1 | 76% | +8.1% | 0.75 | -15.2% | +21.5% · 1.30 · -18.3% | +16.2% · 1.21 · -13.8% |
| VWAP Reclaim / Pullback | +4.7% | 0.90 | -7.5% | 0.31 | 2% | 4.2 | 34% | +9.6% | 0.74 | -23.1% | +15.4% · 1.08 · -20.1% | +14.9% · 1.15 · -14.7% |
| Relative Strength Strategy | +5.3% | 1.04 | -5.9% | 0.32 | 5% | 2.1 | 48% | +13.6% | 0.91 | -21.4% | +22.0% · 1.22 · -21.9% | +22.6% · 1.38 · -20.2% |
| Pairs Trading | +3.0% | 1.29 | -2.8% | 0.42 | 7% | 1.0 | 78% | +8.5% | 0.71 | -19.1% | +14.5% · 1.06 · -16.9% | +14.1% · 1.11 · -15.3% |
| Statistical Arbitrage | +0.7% | 0.75 | -1.7% | 0.15 | 2% | 1.6 | 60% | +3.1% | 0.40 | -17.0% | +12.0% · 0.96 · -15.3% | +8.8% · 0.88 · -15.3% |
| Multi-Factor Strategy | +5.1% | 0.93 | -9.7% | 0.37 | 6% | 1.3 | 45% | +13.0% | 0.89 | -21.7% | +17.5% · 1.19 · -16.8% | +18.8% · 1.35 · -15.6% |
| Regime-Based Strategy | +2.8% | 0.89 | -4.9% | 0.25 | 4% | 6.1 | 55% | +8.6% | 0.67 | -23.6% | +9.7% · 0.68 · -27.9% | +10.6% · 0.81 · -19.8% |
| Machine Learning Signal Combination | +5.5% | 0.92 | -7.0% | 0.36 | 2% | 6.1 | 36% | +9.6% | 0.72 | -22.0% | +14.0% · 0.99 · -23.2% | +14.2% · 1.10 · -17.7% |
| Portfolio-Level Strategy | +13.6% | 1.20 | -14.2% | 0.56 | 13% | 0.9 | 49% | +17.3% | 0.94 | -29.0% | +24.4% · 1.03 · -36.5% | +23.6% · 1.17 · -32.6% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +6.1% | 0.89 | -8.0% | 0.24 | 14% | 2.9 | 36% | +7.5% | 0.44 | -28.4% | +6.5% · 0.42 · -23.0% | +7.4% · 0.49 · -21.3% |
| Moving Average Crossover | +5.1% | 0.79 | -9.9% | 0.16 | 11% | 2.0 | 34% | +8.6% | 0.49 | -28.4% | +7.2% · 0.48 · -34.0% | +9.1% · 0.65 · -20.7% |
| Momentum Strategy | +8.4% | 0.91 | -11.4% | 0.30 | 15% | 2.8 | 43% | +8.8% | 0.48 | -34.2% | +5.4% · 0.35 · -34.4% | +15.9% · 0.77 · -30.3% |
| Breakout Strategy | +7.9% | 0.98 | -9.5% | 0.27 | 14% | 2.2 | 45% | +9.9% | 0.51 | -33.1% | +32.5% · 1.13 · -30.0% | +30.1% · 1.19 · -22.9% |
| Volatility Breakout | +4.4% | 0.82 | -9.5% | 0.18 | 9% | 6.7 | 38% | +7.9% | 0.42 | -28.8% | +24.2% · 1.08 · -26.6% | +17.3% · 0.95 · -21.3% |
| Mean Reversion | +2.6% | 0.55 | -11.4% | 0.19 | 15% | 1.9 | 70% | +2.8% | 0.22 | -38.8% | +6.2% · 0.41 · -33.3% | +8.8% · 0.58 · -33.1% |
| VWAP Mean Reversion | +2.5% | 0.51 | -10.7% | 0.22 | 16% | 1.6 | 70% | +5.6% | 0.38 | -35.1% | +13.9% · 0.70 · -27.3% | +14.3% · 0.79 · -30.3% |
| VWAP Reclaim / Pullback | +6.6% | 1.01 | -6.1% | 0.24 | 9% | 3.9 | 32% | +8.4% | 0.46 | -29.6% | +20.1% · 0.95 · -32.2% | +16.1% · 0.91 · -23.1% |
| Relative Strength Strategy | +6.5% | 0.92 | -11.5% | 0.27 | 10% | 1.9 | 46% | +8.3% | 0.40 | -35.3% | +39.0% · 1.19 · -34.8% | +33.8% · 1.19 · -30.5% |
| Pairs Trading | +2.1% | 0.69 | -5.7% | 0.20 | 15% | 1.0 | 68% | +4.9% | 0.37 | -30.4% | +7.8% · 0.50 · -35.0% | +7.0% · 0.46 · -36.8% |
| Statistical Arbitrage | +0.7% | 0.61 | -2.0% | 0.15 | 7% | 1.4 | 59% | +1.6% | 0.17 | -20.0% | +8.6% · 0.59 · -33.3% | +4.3% · 0.39 · -22.9% |
| Multi-Factor Strategy | +6.2% | 0.96 | -5.9% | 0.32 | 23% | 1.0 | 50% | +8.5% | 0.48 | -29.2% | +4.5% · 0.34 · -25.5% | +11.9% · 0.72 · -24.6% |
| Regime-Based Strategy | +2.4% | 0.68 | -5.2% | 0.15 | 11% | 5.1 | 54% | +5.9% | 0.41 | -27.9% | +15.8% · 0.74 · -33.4% | +12.3% · 0.71 · -25.0% |
| Machine Learning Signal Combination | +4.3% | 0.64 | -9.4% | 0.23 | 8% | 5.3 | 34% | +7.2% | 0.43 | -30.3% | +15.4% · 0.78 · -22.6% | +14.9% · 0.83 · -21.5% |
| Portfolio-Level Strategy | +14.9% | 0.98 | -21.3% | 0.36 | 20% | 1.0 | 43% | +18.3% | 0.62 | -42.7% | +61.5% · 1.28 · -44.8% | +50.1% · 1.23 · -40.3% |
| **Buy & hold (same stocks)** | +24.2% | 1.03 | -33.6% | | | | | | | | | |

