# Lab results · trend_filter

Run 2026-09-27 23:27 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 2.7 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +5.1% | 0.86 | -10.2% | 0.28 | 2% | 3.7 | 34% | +11.5% | 0.84 | -22.1% | +16.1% · 1.09 · -19.4% | +16.7% · 1.22 · -16.1% |
| Moving Average Crossover | +5.1% | 0.90 | -10.0% | 0.34 | 6% | 2.5 | 38% | +11.2% | 0.83 | -22.0% | +18.0% · 1.29 · -18.0% | +18.5% · 1.41 · -16.2% |
| Momentum Strategy | +8.6% | 1.15 | -8.4% | 0.45 | 9% | 2.8 | 46% | +14.6% | 0.93 | -25.7% | +21.1% · 1.25 · -21.6% | +18.9% · 1.23 · -20.0% |
| Breakout Strategy | +5.7% | 0.97 | -8.0% | 0.27 | 5% | 2.4 | 44% | +11.7% | 0.83 | -20.2% | +19.4% · 1.19 · -19.6% | +18.1% · 1.25 · -16.5% |
| Volatility Breakout | +3.1% | 0.75 | -7.6% | 0.22 | 3% | 8.4 | 41% | +8.3% | 0.66 | -19.9% | +7.2% · 0.56 · -25.0% | +10.2% · 0.83 · -16.1% |
| Mean Reversion | +3.8% | 1.06 | -3.6% | 0.40 | 11% | 2.7 | 74% | +9.3% | 0.78 | -16.8% | +14.0% · 0.96 · -21.1% | +11.5% · 0.91 · -16.1% |
| VWAP Mean Reversion | +2.9% | 1.04 | -3.8% | 0.34 | 7% | 1.3 | 77% | +9.2% | 0.80 | -17.0% | +22.4% · 1.26 · -24.8% | +17.6% · 1.21 · -17.4% |
| VWAP Reclaim / Pullback | +5.0% | 0.94 | -6.9% | 0.35 | 2% | 4.3 | 34% | +11.2% | 0.81 | -22.2% | +17.1% · 1.15 · -17.3% | +17.3% · 1.26 · -15.4% |
| Relative Strength Strategy | +5.6% | 1.07 | -7.1% | 0.33 | 7% | 2.2 | 49% | +15.4% | 0.99 | -21.5% | +24.2% · 1.31 · -26.2% | +25.5% · 1.50 · -20.4% |
| Pairs Trading | +3.1% | 1.33 | -2.8% | 0.42 | 7% | 1.0 | 78% | +8.9% | 0.72 | -18.6% | +16.9% · 1.16 · -17.3% | +15.0% · 1.13 · -15.8% |
| Statistical Arbitrage | +0.9% | 0.87 | -1.3% | 0.16 | 4% | 1.7 | 61% | +3.7% | 0.47 | -16.6% | +14.3% · 1.03 · -17.1% | +10.9% · 1.00 · -14.5% |
| Multi-Factor Strategy | +5.2% | 0.94 | -9.7% | 0.40 | 6% | 1.3 | 46% | +14.9% | 0.99 | -21.3% | +22.9% · 1.44 · -18.9% | +23.3% · 1.62 · -14.8% |
| Regime-Based Strategy | +2.6% | 0.80 | -5.4% | 0.23 | 5% | 6.5 | 55% | +8.7% | 0.65 | -25.4% | +10.8% · 0.71 · -30.9% | +12.7% · 0.89 · -24.5% |
| Machine Learning Signal Combination | +5.7% | 0.92 | -7.8% | 0.37 | 2% | 6.4 | 37% | +11.0% | 0.78 | -20.0% | +15.0% · 1.03 · -21.1% | +14.9% · 1.10 · -16.1% |
| Portfolio-Level Strategy | +14.6% | 1.27 | -14.3% | 0.59 | 14% | 0.9 | 52% | +18.2% | 0.97 | -29.3% | +25.0% · 1.06 · -33.3% | +24.1% · 1.19 · -32.5% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +7.0% | 0.94 | -8.4% | 0.27 | 14% | 3.2 | 36% | +9.1% | 0.46 | -31.8% | +17.2% · 0.81 · -31.9% | +11.0% · 0.61 · -27.4% |
| Moving Average Crossover | +6.5% | 0.89 | -10.7% | 0.19 | 11% | 2.2 | 35% | +11.5% | 0.53 | -34.3% | +16.9% · 0.82 · -28.2% | +16.8% · 0.93 · -21.6% |
| Momentum Strategy | +9.2% | 0.95 | -11.5% | 0.26 | 16% | 3.2 | 42% | +13.7% | 0.58 | -36.6% | +21.4% · 0.86 · -41.6% | +22.0% · 0.92 · -34.2% |
| Breakout Strategy | +8.2% | 0.98 | -11.0% | 0.27 | 13% | 2.3 | 44% | +11.4% | 0.53 | -33.8% | +33.4% · 1.12 · -29.8% | +29.2% · 1.14 · -27.9% |
| Volatility Breakout | +4.8% | 0.77 | -11.8% | 0.18 | 9% | 7.4 | 38% | +9.1% | 0.43 | -32.2% | +27.5% · 1.06 · -38.7% | +18.9% · 0.91 · -32.1% |
| Mean Reversion | +3.2% | 0.52 | -14.6% | 0.23 | 13% | 2.2 | 70% | +3.9% | 0.27 | -39.1% | +7.6% · 0.45 · -36.9% | +9.0% · 0.54 · -36.0% |
| VWAP Mean Reversion | +3.3% | 0.52 | -14.0% | 0.24 | 21% | 1.9 | 70% | +7.5% | 0.44 | -35.7% | +17.2% · 0.75 · -31.1% | +16.5% · 0.78 · -35.5% |
| VWAP Reclaim / Pullback | +6.9% | 1.00 | -8.0% | 0.21 | 10% | 4.3 | 31% | +8.1% | 0.44 | -33.2% | +25.1% · 1.05 · -28.7% | +19.3% · 0.98 · -24.0% |
| Relative Strength Strategy | +7.1% | 0.96 | -11.7% | 0.27 | 12% | 2.1 | 47% | +9.9% | 0.46 | -37.3% | +46.4% · 1.28 · -32.0% | +33.4% · 1.13 · -34.8% |
| Pairs Trading | +2.3% | 0.69 | -5.4% | 0.20 | 15% | 1.0 | 68% | +5.4% | 0.40 | -30.6% | +10.0% · 0.57 · -33.0% | +7.8% · 0.48 · -36.5% |
| Statistical Arbitrage | +1.1% | 0.87 | -2.0% | 0.17 | 13% | 1.6 | 60% | +3.0% | 0.28 | -20.3% | +13.0% · 0.72 · -25.8% | +7.9% · 0.59 · -18.8% |
| Multi-Factor Strategy | +6.7% | 0.96 | -6.6% | 0.31 | 20% | 1.1 | 49% | +10.7% | 0.55 | -32.3% | +10.5% · 0.58 · -29.9% | +15.4% · 0.81 · -27.7% |
| Regime-Based Strategy | +3.0% | 0.77 | -6.6% | 0.17 | 10% | 5.7 | 54% | +6.7% | 0.42 | -31.0% | +18.6% · 0.77 · -40.0% | +14.5% · 0.75 · -27.9% |
| Machine Learning Signal Combination | +5.5% | 0.74 | -11.3% | 0.27 | 9% | 5.9 | 34% | +8.8% | 0.46 | -34.7% | +19.2% · 0.85 · -29.7% | +18.2% · 0.90 · -26.2% |
| Portfolio-Level Strategy | +15.5% | 1.01 | -21.3% | 0.39 | 20% | 1.0 | 44% | +20.5% | 0.67 | -43.1% | +60.4% · 1.26 · -45.2% | +53.7% · 1.29 · -39.5% |
| **Buy & hold (same stocks)** | +24.2% | 1.03 | -33.6% | | | | | | | | | |

