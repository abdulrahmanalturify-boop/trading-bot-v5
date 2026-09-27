# Lab results · baseline

Run 2026-09-27 23:21 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 2.6 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +5.1% | 0.86 | -10.2% | 0.28 | 2% | 3.7 | 34% | +11.5% | 0.84 | -22.1% | +16.1% · 1.09 · -19.4% | +16.7% · 1.22 · -16.1% |
| Moving Average Crossover | +5.2% | 0.90 | -10.3% | 0.33 | 6% | 2.5 | 38% | +11.5% | 0.84 | -22.4% | +20.0% · 1.38 · -18.1% | +18.6% · 1.41 · -16.0% |
| Momentum Strategy | +8.8% | 1.17 | -8.5% | 0.46 | 7% | 2.9 | 46% | +14.9% | 0.94 | -25.3% | +22.8% · 1.34 · -19.2% | +18.7% · 1.21 · -20.3% |
| Breakout Strategy | +5.7% | 0.97 | -8.0% | 0.27 | 5% | 2.4 | 44% | +11.7% | 0.83 | -20.2% | +19.4% · 1.19 · -19.6% | +18.1% · 1.25 · -16.5% |
| Volatility Breakout | +4.8% | 0.89 | -8.6% | 0.34 | 6% | 10.2 | 41% | +9.5% | 0.70 | -22.7% | +9.2% · 0.67 · -24.2% | +11.0% · 0.87 · -16.4% |
| Mean Reversion | +3.8% | 1.06 | -3.6% | 0.40 | 11% | 2.7 | 74% | +9.3% | 0.78 | -16.8% | +14.0% · 0.96 · -21.1% | +11.5% · 0.91 · -16.1% |
| VWAP Mean Reversion | +2.9% | 1.04 | -3.8% | 0.34 | 7% | 1.3 | 77% | +9.2% | 0.80 | -17.0% | +22.4% · 1.26 · -24.8% | +17.6% · 1.21 · -17.4% |
| VWAP Reclaim / Pullback | +5.6% | 0.97 | -7.5% | 0.38 | 2% | 5.0 | 33% | +12.1% | 0.85 | -22.4% | +16.7% · 1.12 · -20.0% | +16.8% · 1.23 · -16.5% |
| Relative Strength Strategy | +5.8% | 1.07 | -7.8% | 0.33 | 7% | 2.3 | 49% | +15.4% | 0.98 | -22.5% | +24.1% · 1.27 · -25.3% | +22.5% · 1.34 · -21.5% |
| Pairs Trading | +6.1% | 1.43 | -5.4% | 0.53 | 12% | 1.7 | 78% | +12.2% | 0.81 | -25.3% | +16.4% · 1.09 · -19.6% | +18.4% · 1.27 · -19.2% |
| Statistical Arbitrage | +0.9% | 0.87 | -1.3% | 0.16 | 4% | 1.7 | 61% | +3.7% | 0.47 | -16.6% | +14.3% · 1.03 · -17.1% | +10.9% · 1.00 · -14.5% |
| Multi-Factor Strategy | +6.7% | 1.09 | -10.1% | 0.40 | 5% | 1.3 | 46% | +15.3% | 1.01 | -21.9% | +23.7% · 1.49 · -20.3% | +23.4% · 1.61 · -17.2% |
| Regime-Based Strategy | +2.6% | 0.80 | -5.4% | 0.23 | 5% | 6.5 | 55% | +8.7% | 0.65 | -25.4% | +10.8% · 0.71 · -30.9% | +12.7% · 0.89 · -24.5% |
| Machine Learning Signal Combination | +8.3% | 1.10 | -9.8% | 0.46 | 5% | 8.0 | 37% | +13.7% | 0.89 | -21.6% | +14.9% · 1.01 · -22.9% | +16.9% · 1.23 · -16.0% |
| Portfolio-Level Strategy | +14.6% | 1.27 | -14.3% | 0.59 | 14% | 0.9 | 52% | +18.2% | 0.97 | -29.3% | +25.0% · 1.06 · -33.3% | +24.1% · 1.19 · -32.5% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +7.0% | 0.94 | -8.4% | 0.27 | 14% | 3.2 | 36% | +9.1% | 0.46 | -31.8% | +17.2% · 0.81 · -31.9% | +11.0% · 0.61 · -27.4% |
| Moving Average Crossover | +6.4% | 0.89 | -10.7% | 0.19 | 10% | 2.2 | 34% | +9.4% | 0.47 | -35.1% | +17.9% · 0.85 · -29.2% | +16.6% · 0.92 · -21.6% |
| Momentum Strategy | +9.8% | 0.99 | -12.5% | 0.27 | 17% | 3.3 | 42% | +14.1% | 0.59 | -36.9% | +18.7% · 0.79 · -41.6% | +22.4% · 0.93 · -34.2% |
| Breakout Strategy | +8.2% | 0.98 | -11.0% | 0.27 | 13% | 2.3 | 44% | +11.4% | 0.53 | -33.8% | +33.4% · 1.12 · -29.8% | +29.2% · 1.14 · -27.9% |
| Volatility Breakout | +5.0% | 0.51 | -21.6% | 0.17 | 9% | 10.0 | 39% | +6.3% | 0.32 | -36.7% | +26.2% · 1.02 · -34.9% | +16.7% · 0.80 · -36.7% |
| Mean Reversion | +3.2% | 0.52 | -14.6% | 0.23 | 13% | 2.2 | 70% | +3.9% | 0.27 | -39.1% | +7.6% · 0.45 · -36.9% | +9.0% · 0.54 · -36.0% |
| VWAP Mean Reversion | +3.3% | 0.52 | -14.0% | 0.24 | 21% | 1.9 | 70% | +7.5% | 0.44 | -35.7% | +17.2% · 0.75 · -31.1% | +16.5% · 0.78 · -35.5% |
| VWAP Reclaim / Pullback | +7.1% | 0.91 | -11.8% | 0.24 | 9% | 5.4 | 31% | +8.0% | 0.41 | -37.3% | +19.8% · 0.89 · -29.9% | +14.4% · 0.78 · -25.9% |
| Relative Strength Strategy | +7.3% | 0.94 | -11.7% | 0.27 | 8% | 2.2 | 47% | +10.4% | 0.47 | -37.3% | +40.2% · 1.16 · -32.5% | +38.0% · 1.23 · -35.1% |
| Pairs Trading | +5.4% | 0.76 | -11.9% | 0.36 | 19% | 1.9 | 69% | +11.0% | 0.54 | -42.7% | +13.6% · 0.67 · -36.8% | +15.5% · 0.74 · -39.2% |
| Statistical Arbitrage | +1.1% | 0.87 | -2.0% | 0.17 | 13% | 1.6 | 60% | +3.0% | 0.28 | -20.3% | +13.0% · 0.72 · -25.8% | +7.9% · 0.59 · -18.8% |
| Multi-Factor Strategy | +8.7% | 1.08 | -7.9% | 0.37 | 28% | 1.1 | 50% | +10.3% | 0.52 | -34.2% | +17.7% · 0.85 · -29.8% | +16.9% · 0.85 · -28.3% |
| Regime-Based Strategy | +3.0% | 0.77 | -6.6% | 0.17 | 10% | 5.7 | 54% | +6.7% | 0.42 | -31.0% | +18.6% · 0.77 · -40.0% | +14.5% · 0.75 · -27.9% |
| Machine Learning Signal Combination | +9.0% | 0.90 | -16.3% | 0.30 | 16% | 8.1 | 36% | +11.0% | 0.52 | -35.9% | +22.8% · 0.95 · -34.5% | +20.2% · 0.95 · -29.3% |
| Portfolio-Level Strategy | +15.5% | 1.01 | -21.3% | 0.39 | 20% | 1.0 | 44% | +20.5% | 0.67 | -43.1% | +60.4% · 1.26 · -45.2% | +53.7% · 1.29 · -39.5% |
| **Buy & hold (same stocks)** | +24.2% | 1.03 | -33.6% | | | | | | | | | |

