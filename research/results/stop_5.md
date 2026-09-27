# Lab results · stop_5

Run 2026-09-27 23:46 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 2.6 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +3.5% | 0.66 | -12.8% | 0.25 | 1% | 3.8 | 33% | +10.4% | 0.79 | -22.4% | +13.5% · 0.96 · -16.2% | +14.4% · 1.10 · -15.2% |
| Moving Average Crossover | +4.6% | 0.88 | -10.7% | 0.32 | 6% | 2.5 | 36% | +10.5% | 0.80 | -21.9% | +16.9% · 1.25 · -15.9% | +17.1% · 1.35 · -14.5% |
| Momentum Strategy | +7.6% | 1.11 | -7.0% | 0.42 | 6% | 3.1 | 43% | +14.1% | 0.93 | -22.8% | +16.5% · 1.07 · -24.4% | +17.8% · 1.21 · -19.0% |
| Breakout Strategy | +4.7% | 0.88 | -7.9% | 0.24 | 4% | 2.6 | 40% | +10.2% | 0.77 | -19.8% | +19.4% · 1.23 · -19.1% | +15.7% · 1.13 · -18.6% |
| Volatility Breakout | +4.1% | 0.82 | -9.8% | 0.28 | 4% | 10.3 | 40% | +8.7% | 0.66 | -21.8% | +8.4% · 0.64 · -24.1% | +9.1% · 0.76 · -19.0% |
| Mean Reversion | +2.1% | 0.87 | -2.8% | 0.24 | 7% | 2.8 | 65% | +6.3% | 0.63 | -16.7% | +6.6% · 0.53 · -26.3% | +7.4% · 0.67 · -15.5% |
| VWAP Mean Reversion | +1.3% | 0.72 | -2.3% | 0.17 | 6% | 1.5 | 62% | +5.0% | 0.57 | -14.7% | +14.0% · 0.95 · -16.0% | +10.8% · 0.90 · -13.7% |
| VWAP Reclaim / Pullback | +5.1% | 0.91 | -8.2% | 0.33 | 2% | 5.1 | 32% | +11.3% | 0.82 | -22.1% | +16.6% · 1.14 · -23.1% | +15.7% · 1.18 · -16.8% |
| Relative Strength Strategy | +4.7% | 1.01 | -6.1% | 0.28 | 5% | 2.5 | 43% | +13.3% | 0.92 | -22.3% | +19.1% · 1.14 · -22.7% | +21.1% · 1.34 · -21.1% |
| Pairs Trading | +3.7% | 1.36 | -4.0% | 0.37 | 11% | 2.5 | 55% | +8.6% | 0.64 | -28.3% | +11.9% · 0.85 · -32.5% | +15.1% · 1.09 · -25.6% |
| Statistical Arbitrage | +0.5% | 0.61 | -1.8% | 0.06 | 2% | 1.8 | 58% | +2.4% | 0.33 | -15.6% | +11.9% · 0.95 · -15.9% | +7.6% · 0.80 · -13.4% |
| Multi-Factor Strategy | +5.9% | 1.09 | -7.3% | 0.38 | 6% | 1.6 | 37% | +13.0% | 0.91 | -20.2% | +20.3% · 1.36 · -17.6% | +17.8% · 1.33 · -16.3% |
| Regime-Based Strategy | +1.7% | 0.56 | -4.9% | 0.16 | 4% | 6.9 | 53% | +7.3% | 0.58 | -24.7% | +8.3% · 0.59 · -31.0% | +9.8% · 0.74 · -23.3% |
| Machine Learning Signal Combination | +7.1% | 1.04 | -8.8% | 0.36 | 6% | 8.1 | 36% | +12.6% | 0.84 | -20.2% | +15.1% · 1.05 · -21.6% | +17.7% · 1.31 · -14.8% |
| Portfolio-Level Strategy | +14.4% | 1.32 | -12.3% | 0.62 | 12% | 1.3 | 40% | +15.6% | 0.93 | -25.6% | +27.9% · 1.22 · -26.7% | +23.4% · 1.20 · -29.7% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.6% | 0.78 | -6.2% | 0.23 | 11% | 3.3 | 32% | +6.5% | 0.40 | -28.6% | +6.2% · 0.39 · -32.6% | +4.6% · 0.33 · -27.2% |
| Moving Average Crossover | +4.4% | 0.79 | -8.3% | 0.18 | 12% | 2.2 | 31% | +6.0% | 0.38 | -31.9% | +6.3% · 0.43 · -22.5% | +6.2% · 0.46 · -22.8% |
| Momentum Strategy | +7.6% | 0.93 | -10.1% | 0.34 | 16% | 3.8 | 37% | +13.7% | 0.56 | -34.3% | +14.0% · 0.67 · -31.4% | +10.9% · 0.62 · -28.0% |
| Breakout Strategy | +6.6% | 0.92 | -8.4% | 0.25 | 14% | 2.6 | 37% | +9.7% | 0.48 | -32.3% | +28.5% · 1.10 · -31.2% | +28.0% · 1.16 · -24.9% |
| Volatility Breakout | +3.7% | 0.53 | -13.7% | 0.12 | 7% | 10.4 | 37% | +3.6% | 0.22 | -33.9% | +18.5% · 0.86 · -30.9% | +14.5% · 0.79 · -24.7% |
| Mean Reversion | +1.5% | 0.73 | -3.5% | 0.16 | 18% | 2.4 | 56% | +2.3% | 0.23 | -23.6% | +5.1% · 0.38 · -25.9% | +2.4% · 0.23 · -27.4% |
| VWAP Mean Reversion | +1.5% | 0.66 | -3.8% | 0.20 | 17% | 2.2 | 56% | +3.1% | 0.30 | -22.3% | +2.5% · 0.23 · -29.0% | +2.8% · 0.25 · -22.6% |
| VWAP Reclaim / Pullback | +6.9% | 0.92 | -11.3% | 0.22 | 9% | 5.5 | 29% | +6.8% | 0.37 | -36.9% | +11.2% · 0.62 · -30.6% | +15.0% · 0.85 · -24.3% |
| Relative Strength Strategy | +6.2% | 0.99 | -8.3% | 0.24 | 12% | 2.6 | 38% | +8.4% | 0.42 | -34.6% | +30.2% · 1.03 · -38.1% | +27.9% · 1.06 · -33.3% |
| Pairs Trading | +2.3% | 0.67 | -6.2% | 0.16 | 14% | 2.9 | 40% | +8.0% | 0.48 | -33.0% | +9.8% · 0.54 · -41.5% | +9.8% · 0.56 · -41.4% |
| Statistical Arbitrage | +0.6% | 0.65 | -1.7% | 0.11 | 13% | 1.7 | 56% | +1.2% | 0.16 | -18.5% | +6.2% · 0.46 · -28.3% | +3.5% · 0.35 · -22.8% |
| Multi-Factor Strategy | +6.2% | 0.97 | -6.6% | 0.27 | 24% | 1.6 | 32% | +10.4% | 0.55 | -32.5% | +14.9% · 0.81 · -30.2% | +9.6% · 0.59 · -27.5% |
| Regime-Based Strategy | +2.5% | 0.75 | -5.3% | 0.18 | 13% | 6.1 | 51% | +5.3% | 0.37 | -30.1% | +9.3% · 0.50 · -39.1% | +10.5% · 0.63 · -27.2% |
| Machine Learning Signal Combination | +6.4% | 0.77 | -12.1% | 0.20 | 13% | 8.2 | 33% | +7.0% | 0.37 | -36.9% | +24.4% · 1.07 · -35.5% | +15.6% · 0.82 · -29.1% |
| Portfolio-Level Strategy | +14.7% | 1.11 | -16.5% | 0.38 | 24% | 1.6 | 27% | +19.4% | 0.73 | -35.5% | +43.8% · 1.17 · -40.4% | +38.2% · 1.15 · -35.6% |
| **Buy & hold (same stocks)** | +24.2% | 1.03 | -33.6% | | | | | | | | | |

