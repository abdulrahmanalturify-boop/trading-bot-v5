# Lab results · trend_atr_3

Run 2026-09-28 20:06 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 2.2 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.8% | 0.83 | -10.8% | 0.25 | 3% | 3.7 | 34% | +11.4% | 0.84 | -22.3% | +14.9% · 1.04 · -15.7% | +15.9% · 1.18 · -16.0% |
| Moving Average Crossover | +4.9% | 0.87 | -10.4% | 0.35 | 7% | 2.5 | 38% | +10.9% | 0.82 | -22.0% | +18.3% · 1.32 · -17.7% | +16.8% · 1.29 · -16.9% |
| Momentum Strategy | +8.5% | 1.17 | -7.5% | 0.42 | 8% | 3.0 | 44% | +14.0% | 0.91 | -25.0% | +20.8% · 1.23 · -24.8% | +19.7% · 1.27 · -20.6% |
| Breakout Strategy | +5.2% | 0.92 | -8.0% | 0.27 | 3% | 2.5 | 42% | +11.1% | 0.81 | -19.8% | +16.0% · 1.06 · -17.8% | +16.9% · 1.21 · -18.3% |
| Volatility Breakout | +2.9% | 0.70 | -7.9% | 0.23 | 3% | 8.4 | 41% | +8.1% | 0.65 | -20.2% | +6.4% · 0.50 · -26.1% | +9.4% · 0.78 · -15.6% |
| Mean Reversion | +2.5% | 0.96 | -3.1% | 0.33 | 6% | 2.8 | 70% | +7.4% | 0.69 | -16.9% | +9.2% · 0.66 · -26.0% | +8.9% · 0.74 · -17.4% |
| VWAP Mean Reversion | +2.1% | 0.90 | -2.9% | 0.28 | 4% | 1.3 | 73% | +6.9% | 0.68 | -17.2% | +18.2% · 1.08 · -24.6% | +15.0% · 1.10 · -18.5% |
| VWAP Reclaim / Pullback | +4.9% | 0.92 | -7.0% | 0.34 | 2% | 4.3 | 33% | +11.2% | 0.81 | -22.2% | +17.9% · 1.20 · -17.1% | +16.4% · 1.22 · -15.2% |
| Relative Strength Strategy | +4.9% | 1.02 | -6.1% | 0.30 | 7% | 2.3 | 46% | +13.8% | 0.92 | -22.1% | +22.0% · 1.22 · -26.9% | +22.7% · 1.39 · -20.5% |
| Pairs Trading | +1.7% | 1.09 | -1.9% | 0.29 | 3% | 1.2 | 63% | +4.7% | 0.45 | -21.0% | +12.4% · 0.90 · -22.0% | +12.5% · 1.01 · -17.9% |
| Statistical Arbitrage | +0.6% | 0.70 | -1.8% | 0.11 | 4% | 1.8 | 60% | +2.7% | 0.35 | -17.2% | +12.2% · 0.92 · -17.1% | +8.7% · 0.85 · -13.4% |
| Multi-Factor Strategy | +4.6% | 0.92 | -7.7% | 0.37 | 7% | 1.5 | 39% | +13.9% | 0.96 | -19.6% | +20.5% · 1.38 · -18.0% | +19.5% · 1.42 · -15.3% |
| Regime-Based Strategy | +2.4% | 0.75 | -5.2% | 0.16 | 4% | 6.7 | 55% | +7.8% | 0.61 | -25.9% | +10.6% · 0.70 · -32.9% | +10.7% · 0.78 · -25.9% |
| Machine Learning Signal Combination | +5.3% | 0.90 | -7.1% | 0.33 | 4% | 6.4 | 36% | +9.9% | 0.73 | -20.7% | +12.8% · 0.89 · -23.8% | +15.1% · 1.13 · -15.8% |
| Portfolio-Level Strategy | +14.1% | 1.29 | -12.7% | 0.64 | 13% | 1.2 | 42% | +16.6% | 0.93 | -27.4% | +22.8% · 1.01 · -34.2% | +21.3% · 1.10 · -32.6% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +6.5% | 0.91 | -7.6% | 0.28 | 15% | 3.2 | 36% | +9.3% | 0.48 | -30.7% | +10.0% · 0.54 · -33.2% | +8.5% · 0.50 · -30.6% |
| Moving Average Crossover | +6.5% | 0.91 | -10.5% | 0.21 | 12% | 2.2 | 34% | +11.1% | 0.51 | -33.9% | +12.3% · 0.66 · -28.6% | +13.6% · 0.79 · -21.5% |
| Momentum Strategy | +8.8% | 0.98 | -10.9% | 0.28 | 16% | 3.4 | 41% | +14.6% | 0.62 | -33.9% | +20.7% · 0.85 · -36.2% | +21.6% · 0.90 · -29.9% |
| Breakout Strategy | +7.9% | 0.98 | -10.0% | 0.31 | 15% | 2.3 | 43% | +11.7% | 0.53 | -33.6% | +26.5% · 0.96 · -28.4% | +23.6% · 0.99 · -27.5% |
| Volatility Breakout | +4.7% | 0.82 | -10.1% | 0.18 | 12% | 7.5 | 38% | +8.6% | 0.43 | -30.7% | +26.7% · 1.06 · -43.5% | +17.5% · 0.87 · -30.4% |
| Mean Reversion | +2.3% | 0.82 | -5.2% | 0.27 | 17% | 2.2 | 67% | +4.2% | 0.32 | -25.7% | +9.3% · 0.55 · -33.1% | +7.5% · 0.50 · -27.0% |
| VWAP Mean Reversion | +2.2% | 0.63 | -6.1% | 0.17 | 18% | 1.9 | 67% | +6.1% | 0.43 | -26.4% | +8.4% · 0.46 · -44.2% | +10.5% · 0.60 · -32.6% |
| VWAP Reclaim / Pullback | +6.8% | 1.00 | -8.0% | 0.20 | 10% | 4.3 | 31% | +7.9% | 0.43 | -33.1% | +23.4% · 1.00 · -30.7% | +17.7% · 0.92 · -25.3% |
| Relative Strength Strategy | +6.6% | 0.98 | -9.1% | 0.28 | 12% | 2.2 | 44% | +9.2% | 0.44 | -36.4% | +36.1% · 1.10 · -35.7% | +33.1% · 1.14 · -36.4% |
| Pairs Trading | +1.0% | 0.54 | -3.3% | 0.08 | 13% | 1.1 | 56% | +3.7% | 0.37 | -20.9% | +8.2% · 0.54 · -24.9% | +8.0% · 0.58 · -23.3% |
| Statistical Arbitrage | +1.0% | 0.79 | -1.9% | 0.12 | 14% | 1.6 | 60% | +3.1% | 0.30 | -19.4% | +12.1% · 0.72 · -26.9% | +7.7% · 0.61 · -21.2% |
| Multi-Factor Strategy | +5.4% | 0.88 | -6.7% | 0.32 | 16% | 1.3 | 41% | +11.5% | 0.56 | -32.0% | +6.8% · 0.42 · -28.1% | +16.4% · 0.85 · -25.6% |
| Regime-Based Strategy | +3.0% | 0.79 | -6.0% | 0.17 | 13% | 5.8 | 53% | +6.4% | 0.40 | -31.5% | +16.7% · 0.72 · -40.5% | +13.9% · 0.73 · -30.4% |
| Machine Learning Signal Combination | +4.8% | 0.68 | -10.5% | 0.22 | 10% | 6.0 | 33% | +7.3% | 0.39 | -35.6% | +20.1% · 0.89 · -31.8% | +16.9% · 0.85 · -25.8% |
| Portfolio-Level Strategy | +14.5% | 1.06 | -16.8% | 0.41 | 24% | 1.4 | 32% | +20.4% | 0.70 | -39.2% | +67.3% · 1.35 · -45.0% | +50.3% · 1.27 · -40.9% |
| **Buy & hold (same stocks)** | +24.1% | 1.03 | -33.6% | | | | | | | | | |

