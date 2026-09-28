# Lab results · baseline

Run 2026-09-28 19:52 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 1.8 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +5.1% | 0.86 | -10.2% | 0.29 | 3% | 3.7 | 34% | +11.3% | 0.83 | -22.0% | +15.2% · 1.05 · -17.6% | +17.1% · 1.24 · -16.1% |
| Moving Average Crossover | +5.2% | 0.90 | -10.3% | 0.33 | 6% | 2.5 | 38% | +11.5% | 0.84 | -22.4% | +20.0% · 1.38 · -18.1% | +18.6% · 1.41 · -16.0% |
| Momentum Strategy | +8.8% | 1.17 | -8.5% | 0.46 | 7% | 2.9 | 46% | +14.9% | 0.94 | -25.3% | +22.8% · 1.34 · -19.2% | +18.7% · 1.21 · -20.3% |
| Breakout Strategy | +5.7% | 0.97 | -8.0% | 0.27 | 5% | 2.4 | 44% | +11.9% | 0.84 | -20.2% | +19.4% · 1.19 · -19.6% | +18.1% · 1.25 · -16.5% |
| Volatility Breakout | +4.8% | 0.89 | -8.6% | 0.34 | 6% | 10.2 | 41% | +9.5% | 0.70 | -22.7% | +9.2% · 0.67 · -24.2% | +11.0% · 0.87 · -16.4% |
| Mean Reversion | +3.8% | 1.06 | -3.6% | 0.40 | 11% | 2.7 | 74% | +9.3% | 0.78 | -16.8% | +13.9% · 0.96 · -21.1% | +11.3% · 0.89 · -16.1% |
| VWAP Mean Reversion | +2.9% | 1.04 | -3.8% | 0.34 | 7% | 1.3 | 77% | +9.2% | 0.80 | -17.0% | +22.1% · 1.25 · -24.8% | +17.5% · 1.21 · -17.4% |
| VWAP Reclaim / Pullback | +5.6% | 0.97 | -7.5% | 0.38 | 2% | 5.0 | 33% | +12.1% | 0.85 | -22.4% | +16.7% · 1.12 · -20.0% | +16.8% · 1.23 · -16.5% |
| Relative Strength Strategy | +5.8% | 1.07 | -7.8% | 0.33 | 7% | 2.3 | 49% | +15.4% | 0.98 | -22.5% | +24.1% · 1.27 · -25.3% | +22.5% · 1.34 · -21.5% |
| Pairs Trading | +6.1% | 1.43 | -5.4% | 0.53 | 12% | 1.7 | 78% | +12.3% | 0.81 | -25.3% | +16.4% · 1.09 · -19.6% | +18.4% · 1.27 · -19.2% |
| Statistical Arbitrage | +0.9% | 0.87 | -1.3% | 0.16 | 4% | 1.7 | 61% | +3.7% | 0.47 | -16.6% | +14.3% · 1.03 · -17.1% | +10.9% · 1.00 · -14.5% |
| Multi-Factor Strategy | +6.7% | 1.09 | -10.1% | 0.40 | 5% | 1.3 | 46% | +15.3% | 1.01 | -21.9% | +23.7% · 1.49 · -20.3% | +23.4% · 1.61 · -17.2% |
| Regime-Based Strategy | +2.6% | 0.81 | -5.4% | 0.23 | 5% | 6.5 | 55% | +8.7% | 0.65 | -25.4% | +10.1% · 0.67 · -30.8% | +12.2% · 0.86 · -25.3% |
| Machine Learning Signal Combination | +8.3% | 1.10 | -9.8% | 0.46 | 5% | 8.0 | 37% | +13.6% | 0.89 | -21.6% | +14.9% · 1.01 · -22.9% | +16.8% · 1.22 · -16.0% |
| Portfolio-Level Strategy | +14.6% | 1.27 | -14.3% | 0.59 | 14% | 0.9 | 52% | +18.2% | 0.97 | -29.3% | +24.4% · 1.04 · -32.6% | +24.6% · 1.21 · -32.0% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +6.9% | 0.93 | -8.4% | 0.27 | 14% | 3.2 | 36% | +9.1% | 0.46 | -31.7% | +14.7% · 0.72 · -31.9% | +11.1% · 0.62 · -27.4% |
| Moving Average Crossover | +6.4% | 0.89 | -10.7% | 0.19 | 11% | 2.2 | 34% | +9.4% | 0.47 | -35.1% | +17.8% · 0.85 · -29.2% | +16.5% · 0.91 · -21.6% |
| Momentum Strategy | +9.8% | 0.99 | -12.5% | 0.26 | 17% | 3.3 | 42% | +13.9% | 0.59 | -36.9% | +18.7% · 0.79 · -41.6% | +22.2% · 0.93 · -34.2% |
| Breakout Strategy | +8.1% | 0.97 | -11.0% | 0.27 | 15% | 2.3 | 44% | +11.2% | 0.52 | -33.9% | +33.6% · 1.12 · -29.2% | +29.1% · 1.14 · -28.3% |
| Volatility Breakout | +4.9% | 0.51 | -21.6% | 0.17 | 9% | 10.0 | 39% | +6.2% | 0.32 | -36.7% | +26.3% · 1.02 · -34.9% | +16.7% · 0.80 · -36.7% |
| Mean Reversion | +3.1% | 0.51 | -14.6% | 0.20 | 15% | 2.2 | 70% | +3.8% | 0.27 | -39.1% | +7.5% · 0.45 · -36.9% | +8.9% · 0.54 · -36.0% |
| VWAP Mean Reversion | +3.2% | 0.51 | -14.0% | 0.24 | 21% | 1.9 | 70% | +7.4% | 0.44 | -35.7% | +17.1% · 0.75 · -31.1% | +16.3% · 0.78 · -35.5% |
| VWAP Reclaim / Pullback | +7.1% | 0.91 | -11.8% | 0.24 | 9% | 5.3 | 31% | +7.9% | 0.41 | -37.3% | +19.7% · 0.88 · -29.9% | +14.3% · 0.78 · -25.9% |
| Relative Strength Strategy | +7.3% | 0.94 | -11.7% | 0.27 | 7% | 2.2 | 47% | +10.3% | 0.47 | -37.3% | +40.1% · 1.16 · -32.5% | +38.3% · 1.24 · -35.1% |
| Pairs Trading | +5.4% | 0.75 | -11.9% | 0.36 | 20% | 1.9 | 69% | +11.1% | 0.54 | -42.1% | +13.4% · 0.66 · -36.8% | +15.4% · 0.73 · -39.2% |
| Statistical Arbitrage | +1.1% | 0.86 | -2.0% | 0.17 | 13% | 1.6 | 60% | +3.0% | 0.27 | -20.3% | +12.8% · 0.71 · -25.8% | +7.7% · 0.58 · -18.8% |
| Multi-Factor Strategy | +8.7% | 1.07 | -7.9% | 0.36 | 28% | 1.1 | 50% | +10.2% | 0.51 | -34.2% | +17.4% · 0.84 · -29.8% | +16.6% · 0.84 · -28.3% |
| Regime-Based Strategy | +3.0% | 0.76 | -6.6% | 0.17 | 10% | 5.7 | 54% | +6.6% | 0.42 | -31.0% | +19.0% · 0.78 · -38.5% | +14.7% · 0.76 · -28.2% |
| Machine Learning Signal Combination | +8.9% | 0.89 | -16.3% | 0.30 | 18% | 8.1 | 36% | +11.0% | 0.51 | -35.9% | +22.7% · 0.94 · -34.5% | +20.2% · 0.95 · -29.3% |
| Portfolio-Level Strategy | +15.4% | 1.00 | -21.3% | 0.40 | 20% | 1.0 | 44% | +20.2% | 0.66 | -43.1% | +59.6% · 1.25 · -45.2% | +52.9% · 1.28 · -39.7% |
| **Buy & hold (same stocks)** | +24.1% | 1.03 | -33.6% | | | | | | | | | |

