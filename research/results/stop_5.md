# Lab results · stop_5

Run 2026-09-28 20:10 UTC · 100 company bots per strategy · sectors: Basic Materials, Communication Services, Consumer Cyclical, Consumer Defensive, Energy, Financial Services, Healthcare, Industrials, Real Estate, Technology, Utilities · fee 0.05% per side · took 1.8 min

All stocks = the company bots of a strategy averaged as one portfolio. Beat B&H = share of stocks where the bot's Sharpe is higher than buying and holding that stock. Sector = one bot per sector (up to 5 trades), averaged.

## in-sample 2012-2019

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +3.4% | 0.65 | -13.0% | 0.25 | 2% | 3.8 | 33% | +10.4% | 0.79 | -22.4% | +14.0% · 0.99 · -16.2% | +14.4% · 1.10 · -15.2% |
| Moving Average Crossover | +4.6% | 0.88 | -10.7% | 0.32 | 6% | 2.5 | 36% | +10.4% | 0.80 | -21.9% | +16.9% · 1.25 · -15.9% | +17.2% · 1.35 · -14.5% |
| Momentum Strategy | +7.6% | 1.11 | -7.0% | 0.42 | 6% | 3.1 | 43% | +14.1% | 0.93 | -22.8% | +16.5% · 1.07 · -24.4% | +17.9% · 1.21 · -19.6% |
| Breakout Strategy | +4.7% | 0.88 | -7.9% | 0.24 | 4% | 2.6 | 40% | +9.9% | 0.76 | -19.8% | +19.7% · 1.25 · -19.0% | +16.2% · 1.17 · -18.6% |
| Volatility Breakout | +4.1% | 0.82 | -9.8% | 0.28 | 4% | 10.3 | 40% | +8.7% | 0.66 | -21.9% | +8.4% · 0.64 · -24.1% | +9.1% · 0.76 · -19.0% |
| Mean Reversion | +2.1% | 0.87 | -2.8% | 0.24 | 7% | 2.8 | 65% | +6.3% | 0.63 | -16.7% | +7.1% · 0.57 · -26.3% | +7.6% · 0.69 · -15.5% |
| VWAP Mean Reversion | +1.3% | 0.72 | -2.3% | 0.17 | 6% | 1.5 | 62% | +5.0% | 0.57 | -14.7% | +13.9% · 0.94 · -16.0% | +10.7% · 0.90 · -13.7% |
| VWAP Reclaim / Pullback | +5.1% | 0.91 | -8.2% | 0.33 | 2% | 5.1 | 32% | +11.3% | 0.82 | -22.1% | +16.6% · 1.14 · -23.1% | +15.7% · 1.18 · -16.8% |
| Relative Strength Strategy | +4.7% | 1.01 | -6.1% | 0.28 | 5% | 2.5 | 43% | +13.3% | 0.92 | -22.3% | +19.1% · 1.14 · -22.7% | +21.1% · 1.33 · -21.1% |
| Pairs Trading | +3.7% | 1.36 | -4.0% | 0.37 | 11% | 2.5 | 55% | +8.6% | 0.64 | -28.3% | +11.9% · 0.85 · -32.5% | +15.1% · 1.09 · -25.6% |
| Statistical Arbitrage | +0.5% | 0.61 | -1.8% | 0.06 | 2% | 1.8 | 58% | +2.4% | 0.33 | -15.6% | +11.9% · 0.95 · -15.9% | +7.6% · 0.80 · -13.4% |
| Multi-Factor Strategy | +5.9% | 1.09 | -7.3% | 0.38 | 6% | 1.6 | 37% | +13.0% | 0.91 | -20.2% | +20.3% · 1.36 · -17.6% | +17.9% · 1.33 · -16.3% |
| Regime-Based Strategy | +1.7% | 0.57 | -4.9% | 0.16 | 4% | 6.9 | 53% | +7.3% | 0.58 | -24.8% | +7.8% · 0.56 · -31.8% | +9.4% · 0.72 · -23.2% |
| Machine Learning Signal Combination | +7.1% | 1.05 | -8.8% | 0.36 | 6% | 8.1 | 36% | +12.6% | 0.84 | -20.2% | +15.1% · 1.05 · -21.6% | +17.8% · 1.31 · -14.8% |
| Portfolio-Level Strategy | +14.4% | 1.32 | -12.3% | 0.62 | 12% | 1.3 | 40% | +15.6% | 0.93 | -25.6% | +27.8% · 1.21 · -30.5% | +23.5% · 1.20 · -31.6% |
| **Buy & hold (same stocks)** | +22.9% | 1.39 | -23.1% | | | | | | | | | |

## out-of-sample 2020-now

| Strategy | All stocks CAGR | Sharpe | Max DD | Median stock Sharpe | Beat B&H | Trades / yr / stock | Win % | Sector CAGR | Sector Sharpe | Sector Max DD | All-companies bot, 10 trades: CAGR · Sharpe · Max DD | All-companies bot, 20 trades: CAGR · Sharpe · Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trend Following | +4.6% | 0.77 | -6.2% | 0.24 | 11% | 3.3 | 32% | +6.3% | 0.39 | -29.0% | +5.6% · 0.36 · -32.6% | +3.9% · 0.30 · -28.5% |
| Moving Average Crossover | +4.4% | 0.78 | -8.3% | 0.18 | 12% | 2.2 | 31% | +6.0% | 0.38 | -31.9% | +6.6% · 0.45 · -22.5% | +6.2% · 0.46 · -22.8% |
| Momentum Strategy | +7.5% | 0.93 | -10.1% | 0.34 | 17% | 3.8 | 37% | +13.6% | 0.56 | -34.3% | +13.9% · 0.66 · -31.4% | +11.1% · 0.62 · -28.0% |
| Breakout Strategy | +6.5% | 0.91 | -8.4% | 0.25 | 14% | 2.6 | 37% | +9.6% | 0.47 | -32.3% | +29.5% · 1.13 · -31.2% | +27.4% · 1.13 · -25.8% |
| Volatility Breakout | +3.7% | 0.53 | -13.7% | 0.12 | 7% | 10.4 | 37% | +3.6% | 0.22 | -33.9% | +18.7% · 0.87 · -30.9% | +14.6% · 0.79 · -24.7% |
| Mean Reversion | +1.5% | 0.72 | -3.5% | 0.16 | 17% | 2.4 | 56% | +2.2% | 0.22 | -23.6% | +5.0% · 0.38 · -25.9% | +2.2% · 0.23 · -27.4% |
| VWAP Mean Reversion | +1.5% | 0.65 | -3.8% | 0.18 | 18% | 2.2 | 56% | +3.0% | 0.30 | -22.3% | +2.2% · 0.21 · -29.0% | +2.6% · 0.24 · -22.6% |
| VWAP Reclaim / Pullback | +6.9% | 0.92 | -11.3% | 0.23 | 9% | 5.5 | 29% | +6.7% | 0.37 | -36.9% | +11.1% · 0.62 · -30.6% | +15.0% · 0.85 · -24.3% |
| Relative Strength Strategy | +6.2% | 0.99 | -8.3% | 0.24 | 12% | 2.6 | 38% | +8.3% | 0.42 | -34.6% | +30.1% · 1.02 · -38.1% | +27.5% · 1.05 · -33.3% |
| Pairs Trading | +2.3% | 0.66 | -6.2% | 0.14 | 14% | 2.9 | 40% | +7.9% | 0.47 | -33.0% | +9.6% · 0.54 · -41.5% | +9.6% · 0.55 · -41.4% |
| Statistical Arbitrage | +0.6% | 0.64 | -1.7% | 0.11 | 13% | 1.7 | 56% | +1.2% | 0.16 | -18.6% | +6.1% · 0.45 · -28.3% | +3.4% · 0.35 · -22.8% |
| Multi-Factor Strategy | +6.1% | 0.96 | -6.6% | 0.27 | 23% | 1.6 | 32% | +10.4% | 0.54 | -32.5% | +14.6% · 0.79 · -30.2% | +11.1% · 0.67 · -26.8% |
| Regime-Based Strategy | +2.5% | 0.74 | -5.3% | 0.18 | 13% | 6.1 | 51% | +5.2% | 0.37 | -30.0% | +9.5% · 0.51 · -40.1% | +10.7% · 0.63 · -27.2% |
| Machine Learning Signal Combination | +6.3% | 0.77 | -12.1% | 0.20 | 13% | 8.2 | 33% | +7.0% | 0.37 | -36.9% | +24.4% · 1.07 · -35.5% | +15.6% · 0.82 · -29.1% |
| Portfolio-Level Strategy | +14.7% | 1.11 | -16.5% | 0.38 | 24% | 1.6 | 27% | +19.2% | 0.73 | -35.8% | +42.9% · 1.15 · -40.3% | +39.0% · 1.16 · -34.9% |
| **Buy & hold (same stocks)** | +24.1% | 1.03 | -33.6% | | | | | | | | | |

