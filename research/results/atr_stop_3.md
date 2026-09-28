# Lab results · atr_stop_3

Run 2026-09-28 20:04 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 2.2 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.8% | 0.83 | -10.8% | 0.25 | 3% | 3.7 | 34% | +11.4% | 0.84 | -22.3% | +14.9% · 1.04 · -15.7% | +15.9% · 1.18 · -16.0% |
| Moving Average Crossover | +5.0% | 0.88 | -10.7% | 0.34 | 7% | 2.5 | 38% | +11.1% | 0.82 | -22.4% | +19.0% · 1.32 · -17.8% | +16.7% · 1.28 · -16.7% |
| Momentum Strategy | +8.7% | 1.19 | -7.5% | 0.42 | 7% | 3.0 | 44% | +14.3% | 0.92 | -24.8% | +21.8% · 1.27 · -24.9% | +20.2% · 1.30 · -20.4% |
| Breakout Strategy | +5.2% | 0.92 | -8.0% | 0.27 | 3% | 2.5 | 42% | +11.1% | 0.81 | -19.8% | +16.0% · 1.06 · -17.8% | +16.9% · 1.21 · -18.3% |
| Volatility Breakout | +4.4% | 0.83 | -9.1% | 0.34 | 6% | 10.3 | 41% | +9.1% | 0.67 | -22.6% | +7.8% · 0.58 · -24.5% | +10.1% · 0.81 · -16.7% |
| Mean Reversion | +2.5% | 0.96 | -3.1% | 0.33 | 6% | 2.8 | 70% | +7.4% | 0.69 | -16.9% | +9.2% · 0.66 · -26.0% | +8.9% · 0.74 · -17.4% |
| VWAP Mean Reversion | +2.1% | 0.90 | -2.9% | 0.28 | 4% | 1.3 | 73% | +6.9% | 0.68 | -17.2% | +18.2% · 1.08 · -24.6% | +15.0% · 1.10 · -18.5% |
| VWAP Reclaim / Pullback | +5.5% | 0.96 | -7.8% | 0.38 | 2% | 5.0 | 33% | +12.2% | 0.86 | -22.4% | +17.0% · 1.15 · -19.7% | +17.3% · 1.27 · -15.8% |
| Relative Strength Strategy | +5.1% | 1.03 | -6.8% | 0.29 | 7% | 2.4 | 46% | +13.6% | 0.91 | -23.2% | +20.5% · 1.15 · -27.5% | +21.5% · 1.31 · -21.9% |
| Pairs Trading | +4.5% | 1.35 | -5.6% | 0.46 | 7% | 2.2 | 64% | +10.6% | 0.72 | -28.3% | +19.0% · 1.22 · -27.8% | +17.7% · 1.20 · -23.6% |
| Statistical Arbitrage | +0.6% | 0.70 | -1.8% | 0.11 | 4% | 1.8 | 60% | +2.7% | 0.35 | -17.2% | +12.2% · 0.92 · -17.1% | +8.7% · 0.85 · -13.4% |
| Multi-Factor Strategy | +5.8% | 1.02 | -8.6% | 0.38 | 6% | 1.5 | 39% | +14.9% | 0.99 | -20.5% | +20.3% · 1.36 · -17.7% | +19.4% · 1.41 · -14.1% |
| Regime-Based Strategy | +2.4% | 0.75 | -5.2% | 0.16 | 4% | 6.7 | 55% | +7.8% | 0.61 | -25.9% | +10.6% · 0.70 · -32.9% | +10.7% · 0.78 · -25.9% |
| Machine Learning Signal Combination | +7.4% | 1.05 | -9.7% | 0.39 | 7% | 8.0 | 36% | +12.6% | 0.83 | -21.5% | +14.6% · 1.00 · -24.9% | +17.0% · 1.24 · -16.5% |
| Portfolio-Level Strategy | +14.1% | 1.29 | -12.7% | 0.64 | 13% | 1.2 | 42% | +16.6% | 0.93 | -27.4% | +22.8% · 1.01 · -34.2% | +21.3% · 1.10 · -32.6% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +6.5% | 0.91 | -7.6% | 0.28 | 15% | 3.2 | 36% | +9.3% | 0.48 | -30.7% | +10.0% · 0.54 · -33.2% | +8.5% · 0.50 · -30.6% |
| Moving Average Crossover | +6.5% | 0.91 | -10.5% | 0.21 | 11% | 2.2 | 34% | +9.1% | 0.46 | -34.7% | +12.6% · 0.66 · -29.6% | +13.3% · 0.78 · -21.5% |
| Momentum Strategy | +9.5% | 1.03 | -11.9% | 0.31 | 17% | 3.5 | 41% | +15.2% | 0.64 | -33.5% | +25.4% · 0.93 · -36.2% | +21.1% · 0.90 · -29.8% |
| Breakout Strategy | +7.9% | 0.98 | -10.0% | 0.31 | 15% | 2.3 | 43% | +11.7% | 0.53 | -33.6% | +26.5% · 0.96 · -28.4% | +23.6% · 0.99 · -27.5% |
| Volatility Breakout | +4.7% | 0.56 | -17.9% | 0.15 | 12% | 10.1 | 39% | +6.1% | 0.33 | -34.5% | +25.0% · 1.01 · -35.0% | +16.7% · 0.83 · -30.3% |
| Mean Reversion | +2.3% | 0.82 | -5.2% | 0.27 | 17% | 2.2 | 67% | +4.2% | 0.32 | -25.7% | +9.3% · 0.55 · -33.1% | +7.5% · 0.50 · -27.0% |
| VWAP Mean Reversion | +2.2% | 0.63 | -6.1% | 0.17 | 18% | 1.9 | 67% | +6.1% | 0.43 | -26.4% | +8.4% · 0.46 · -44.2% | +10.5% · 0.60 · -32.6% |
| VWAP Reclaim / Pullback | +7.1% | 0.91 | -11.8% | 0.23 | 10% | 5.4 | 31% | +7.9% | 0.40 | -37.2% | +18.1% · 0.84 · -31.6% | +12.8% · 0.71 · -27.1% |
| Relative Strength Strategy | +6.4% | 0.93 | -9.6% | 0.26 | 12% | 2.3 | 43% | +8.9% | 0.44 | -36.8% | +40.6% · 1.20 · -35.4% | +33.8% · 1.15 · -38.2% |
| Pairs Trading | +4.1% | 0.78 | -9.2% | 0.31 | 17% | 2.4 | 58% | +10.7% | 0.53 | -43.1% | +10.6% · 0.53 · -46.5% | +13.1% · 0.64 · -43.7% |
| Statistical Arbitrage | +1.0% | 0.79 | -1.9% | 0.12 | 14% | 1.6 | 60% | +3.1% | 0.30 | -19.4% | +12.1% · 0.72 · -26.9% | +7.7% · 0.61 · -21.2% |
| Multi-Factor Strategy | +7.2% | 0.99 | -7.2% | 0.38 | 24% | 1.4 | 41% | +11.4% | 0.54 | -34.4% | +9.3% · 0.53 · -26.9% | +16.3% · 0.84 · -27.0% |
| Regime-Based Strategy | +3.0% | 0.79 | -6.0% | 0.17 | 13% | 5.8 | 53% | +6.4% | 0.40 | -31.5% | +16.7% · 0.72 · -40.5% | +13.9% · 0.73 · -30.4% |
| Machine Learning Signal Combination | +7.6% | 0.81 | -15.9% | 0.26 | 12% | 8.1 | 35% | +9.6% | 0.45 | -37.5% | +18.0% · 0.82 · -36.4% | +17.9% · 0.88 · -31.7% |
| Portfolio-Level Strategy | +14.5% | 1.06 | -16.8% | 0.41 | 24% | 1.4 | 32% | +20.4% | 0.70 | -39.2% | +67.3% · 1.35 · -45.0% | +50.3% · 1.27 · -40.9% |
| **Buy & hold (same stocks)** | +24.1% | 1.03 | -33.6% | | | | | | | | | |

