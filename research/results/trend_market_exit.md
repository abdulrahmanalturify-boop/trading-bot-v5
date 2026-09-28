# Lab results · trend_market_exit

Run 2026-09-28 20:08 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 1.9 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.6% | 0.82 | -11.0% | 0.23 | 3% | 3.6 | 35% | +10.3% | 0.80 | -20.3% | +14.7% · 1.07 · -17.6% | +13.6% · 1.09 · -18.3% |
| Moving Average Crossover | +4.4% | 0.84 | -9.1% | 0.33 | 6% | 2.4 | 38% | +9.3% | 0.75 | -20.3% | +13.6% · 1.08 · -18.4% | +14.1% · 1.17 · -18.0% |
| Momentum Strategy | +8.0% | 1.11 | -7.9% | 0.41 | 8% | 2.9 | 46% | +13.1% | 0.90 | -21.3% | +13.7% · 0.95 · -19.2% | +15.5% · 1.11 · -15.5% |
| Breakout Strategy | +5.2% | 0.92 | -8.3% | 0.28 | 3% | 2.5 | 43% | +10.9% | 0.81 | -19.9% | +18.1% · 1.16 · -15.7% | +14.8% · 1.09 · -14.7% |
| Volatility Breakout | +2.9% | 0.73 | -6.8% | 0.19 | 5% | 8.1 | 41% | +6.3% | 0.53 | -21.5% | +7.3% · 0.59 · -23.7% | +10.2% · 0.88 · -14.3% |
| Mean Reversion | +2.8% | 0.95 | -3.6% | 0.35 | 7% | 2.5 | 71% | +6.2% | 0.59 | -16.8% | +10.0% · 0.80 · -21.0% | +7.4% · 0.68 · -16.0% |
| VWAP Mean Reversion | +2.1% | 0.89 | -3.3% | 0.31 | 7% | 1.2 | 73% | +6.1% | 0.60 | -17.1% | +16.2% · 1.07 · -18.2% | +11.5% · 0.94 · -17.2% |
| VWAP Reclaim / Pullback | +4.7% | 0.91 | -7.1% | 0.31 | 2% | 4.2 | 34% | +10.2% | 0.78 | -21.0% | +18.0% · 1.25 · -13.4% | +14.9% · 1.18 · -12.8% |
| Relative Strength Strategy | +4.8% | 0.99 | -5.7% | 0.33 | 6% | 2.3 | 47% | +12.6% | 0.89 | -18.2% | +23.0% · 1.33 · -18.0% | +21.9% · 1.40 · -15.5% |
| Pairs Trading | +2.5% | 1.16 | -2.8% | 0.36 | 5% | 1.1 | 73% | +7.0% | 0.63 | -19.6% | +13.5% · 1.06 · -18.7% | +11.4% · 1.00 · -14.6% |
| Statistical Arbitrage | +0.7% | 0.70 | -1.9% | 0.15 | 2% | 1.6 | 60% | +3.0% | 0.38 | -16.7% | +11.2% · 0.91 · -15.2% | +8.4% · 0.85 · -15.2% |
| Multi-Factor Strategy | +4.4% | 0.86 | -9.7% | 0.30 | 5% | 1.4 | 43% | +11.7% | 0.83 | -19.7% | +19.3% · 1.31 · -14.9% | +17.5% · 1.32 · -13.7% |
| Regime-Based Strategy | +2.8% | 0.89 | -5.0% | 0.23 | 4% | 6.1 | 55% | +8.1% | 0.64 | -22.2% | +9.1% · 0.65 · -30.3% | +12.2% · 0.94 · -17.9% |
| Machine Learning Signal Combination | +5.5% | 0.93 | -6.8% | 0.34 | 2% | 6.1 | 36% | +9.3% | 0.70 | -21.3% | +14.4% · 1.02 · -17.8% | +13.3% · 1.05 · -16.5% |
| Portfolio-Level Strategy | +11.7% | 1.12 | -15.2% | 0.49 | 12% | 1.4 | 44% | +16.4% | 0.94 | -26.2% | +27.0% · 1.29 · -23.4% | +25.4% · 1.36 · -18.2% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +6.1% | 0.90 | -7.3% | 0.25 | 15% | 2.9 | 37% | +7.6% | 0.47 | -27.1% | +6.8% · 0.44 · -31.9% | +8.2% · 0.55 · -30.2% |
| Moving Average Crossover | +4.9% | 0.79 | -8.6% | 0.16 | 12% | 2.0 | 35% | +8.2% | 0.50 | -26.2% | +5.7% · 0.43 · -24.5% | +10.1% · 0.74 · -17.2% |
| Momentum Strategy | +7.2% | 0.86 | -9.6% | 0.28 | 15% | 3.0 | 42% | +8.9% | 0.52 | -28.9% | +12.8% · 0.75 · -25.7% | +14.2% · 0.82 · -24.0% |
| Breakout Strategy | +8.0% | 1.00 | -9.2% | 0.34 | 15% | 2.3 | 46% | +11.4% | 0.58 | -27.7% | +39.7% · 1.35 · -22.7% | +32.4% · 1.32 · -22.1% |
| Volatility Breakout | +4.8% | 0.91 | -7.1% | 0.23 | 12% | 6.8 | 38% | +9.2% | 0.50 | -27.5% | +28.0% · 1.23 · -21.3% | +18.7% · 1.03 · -18.2% |
| Mean Reversion | +2.1% | 0.70 | -4.6% | 0.21 | 14% | 1.9 | 66% | +3.1% | 0.28 | -23.4% | +5.5% · 0.42 · -28.3% | +7.5% · 0.59 · -24.2% |
| VWAP Mean Reversion | +1.9% | 0.56 | -5.5% | 0.22 | 14% | 1.6 | 64% | +5.4% | 0.45 | -25.1% | +11.5% · 0.66 · -28.7% | +12.8% · 0.81 · -27.0% |
| VWAP Reclaim / Pullback | +6.7% | 1.02 | -6.3% | 0.25 | 11% | 4.0 | 32% | +9.0% | 0.51 | -27.1% | +19.1% · 0.96 · -26.1% | +16.4% · 0.97 · -21.3% |
| Relative Strength Strategy | +6.4% | 0.99 | -7.9% | 0.28 | 9% | 2.0 | 45% | +9.0% | 0.48 | -29.1% | +33.7% · 1.15 · -27.8% | +29.3% · 1.16 · -25.7% |
| Pairs Trading | +1.8% | 0.70 | -3.4% | 0.19 | 20% | 1.0 | 66% | +4.0% | 0.36 | -24.6% | +7.2% · 0.56 · -24.7% | +5.8% · 0.49 · -20.3% |
| Statistical Arbitrage | +0.6% | 0.54 | -2.0% | 0.13 | 9% | 1.4 | 59% | +1.8% | 0.20 | -19.3% | +8.0% · 0.57 · -34.5% | +4.4% · 0.41 · -20.7% |
| Multi-Factor Strategy | +5.4% | 0.88 | -5.9% | 0.28 | 20% | 1.1 | 49% | +8.6% | 0.49 | -27.7% | +6.0% · 0.44 · -28.5% | +11.8% · 0.76 · -19.9% |
| Regime-Based Strategy | +2.4% | 0.68 | -4.9% | 0.12 | 10% | 5.1 | 53% | +5.9% | 0.42 | -27.1% | +16.9% · 0.80 · -29.2% | +13.3% · 0.77 · -24.0% |
| Machine Learning Signal Combination | +4.0% | 0.63 | -8.7% | 0.22 | 11% | 5.3 | 34% | +7.7% | 0.47 | -27.6% | +18.8% · 0.92 · -23.2% | +15.5% · 0.90 · -21.4% |
| Portfolio-Level Strategy | +10.5% | 0.86 | -18.9% | 0.33 | 16% | 1.5 | 43% | +9.6% | 0.45 | -39.0% | +32.9% · 1.03 · -39.6% | +21.6% · 0.83 · -38.6% |
| **Buy & hold (same stocks)** | +24.1% | 1.03 | -33.6% | | | | | | | | | |

